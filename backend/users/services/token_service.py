"""Token lifecycle and management services.

This module centralizes token creation, verification, refresh, invalidation,
and previous-token cleanup (single-session enforcement). It uses the
custom token classes defined in `users.tokens` and integrates safely
with SimpleJWT's OutstandingToken/BlacklistedToken models when available.

All methods are HTTP-agnostic and return simple values or raise only
well-documented exceptions.
"""

from typing import Dict, Optional, Tuple
import logging

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken as SimpleAccessToken

from ..tokens import CustomRefreshToken

logger = logging.getLogger(__name__)

# Try to import token blacklist/outstanding models if the project has them installed.
try:
    from rest_framework_simplejwt.token_blacklist.models import (
        OutstandingToken,
        BlacklistedToken,
    )  # type: ignore

    BLACKLIST_AVAILABLE = True
except Exception:
    OutstandingToken = None  # type: ignore
    BlacklistedToken = None  # type: ignore
    BLACKLIST_AVAILABLE = False


class TokenService:
    """Service responsible for JWT token operations.

    Methods are written defensively so the service works whether or not the
    token-blacklist app is enabled in the project settings.
    """

    @classmethod
    def create_login_tokens(cls, user) -> Dict[str, str]:
        """Create access and refresh tokens for `user`.

        Returns a dict with `access` and `refresh` string tokens.
        """
        refresh = CustomRefreshToken.for_user(user)
        access = refresh.access_token

        logger.debug(
            "Created new login tokens for user_id=%s", getattr(user, "user_id", None)
        )
        return {"access": str(access), "refresh": str(refresh)}

    @classmethod
    def cleanup_previous_tokens(cls, user, keep_last: int = 1) -> int:
        """Attempt to cleanup/blacklist previous tokens for `user`.

        If the `token_blacklist` app is installed this will blacklist older
        OutstandingTokens for the user, leaving only the most recent
        `keep_last` tokens. Returns number of tokens affected.

        If blacklist models are not present this is a no-op (returns 0).
        """
        if not BLACKLIST_AVAILABLE:
            logger.debug(
                "Token blacklist not available; skipping cleanup for user=%s",
                getattr(user, "id", None),
            )
            return 0

        # Query all outstanding tokens for this user ordered by created timestamp
        tokens_qs = OutstandingToken.objects.filter(user_id=user.pk).order_by(
            "created_at"
        )
        total = tokens_qs.count()
        if total <= keep_last:
            return 0

        # tokens to remove (all except last `keep_last`)
        tokens_to_blacklist = list(tokens_qs[: max(0, total - keep_last)])

        affected = 0
        for ot in tokens_to_blacklist:
            # Blacklist if not already blacklisted
            try:
                BlacklistedToken.objects.get_or_create(token=ot)
                affected += 1
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(
                    "Failed to blacklist token jti=%s: %s",
                    getattr(ot, "jti", None),
                    exc,
                )

        logger.info("Blacklisted %d previous tokens for user_id=%s", affected, user.pk)
        return affected

    @classmethod
    def verify_token(cls, token: str) -> Tuple[bool, Optional[str]]:
        """Verify validity of a token string.

        Returns (True, None) on success, or (False, error_message) on failure.
        """
        try:
            # Use SimpleJWT's AccessToken wrapper for verification
            SimpleAccessToken(token)
            return True, None
        except TokenError as exc:
            logger.info("Token verification failed: %s", exc)
            return False, str(exc)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected error verifying token: %s", exc)
            return False, "Invalid token"

    @classmethod
    def refresh_token(
        cls, refresh_token: str
    ) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
        """Refresh access/refresh tokens using a refresh token string.

        If ROTATE_REFRESH_TOKENS is enabled in settings, the old refresh token
        is blacklisted and a new one is issued.

        Returns (tokens_dict, None) on success, or (None, error_message) on failure.
        """
        try:
            refresh = CustomRefreshToken(refresh_token)
        except TokenError as exc:
            logger.info("Invalid refresh token provided: %s", exc)
            return None, "Invalid refresh token"

        if BLACKLIST_AVAILABLE:
            try:
                # The verify() method forces a check against the BlacklistedToken model.
                refresh.verify()
            except TokenError as exc:
                # If blacklisted, this will raise a TokenError.
                logger.info("Blacklisted token used for refresh: %s", exc)
                return None, str(exc)

        try:
            # Get new access token from current refresh
            access = refresh.access_token

            # Check if rotation is enabled and blacklist is available
            from django.conf import settings as django_settings

            rotate_enabled = getattr(django_settings, "SIMPLE_JWT", {}).get(
                "ROTATE_REFRESH_TOKENS", False
            )

            if rotate_enabled and BLACKLIST_AVAILABLE:
                # Blacklist the current refresh token
                try:
                    refresh.blacklist()
                    logger.debug("Blacklisted old refresh token during rotation")
                except Exception as blacklist_exc:
                    logger.warning(
                        "Failed to blacklist token during rotation: %s", blacklist_exc
                    )

                # Create new refresh token with same user data
                user_id = refresh.payload.get("user_id")
                email = refresh.payload.get("email")
                session_version = refresh.payload.get("session_version", 0)

                new_refresh = CustomRefreshToken()
                new_refresh["user_id"] = user_id
                new_refresh["email"] = email
                new_refresh["session_version"] = session_version

                logger.info("Rotated refresh token for user_id=%s", user_id)
                return {"access": str(access), "refresh": str(new_refresh)}, None
            else:
                # No rotation - return same refresh token
                return {"access": str(access), "refresh": str(refresh)}, None

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to refresh token: %s", exc)
            return None, "Failed to refresh token"

    @classmethod
    def invalidate_token(cls, token: str) -> Tuple[bool, Optional[str]]:
        """Invalidate a refresh token by blacklisting it (if supported).

        Returns (True, None) on success, (False, error_message) on failure.
        """
        if not BLACKLIST_AVAILABLE:
            # If blacklist not enabled we cannot reliably invalidate server-side
            logger.warning("Token blacklist not available; cannot invalidate token")
            return False, "Token blacklisting not enabled"

        try:
            refresh = CustomRefreshToken(token)
        except TokenError as exc:
            logger.info("Invalid token provided for invalidation: %s", exc)
            return False, "Invalid token"

        # Find corresponding OutstandingToken and blacklist it
        try:
            ot = OutstandingToken.objects.get(jti=refresh["jti"])  # type: ignore
            BlacklistedToken.objects.get_or_create(token=ot)
            logger.info("Blacklisted token jti=%s", refresh["jti"])  # type: ignore
            return True, None
        except OutstandingToken.DoesNotExist:  # pragma: no cover - defensive
            logger.warning("OutstandingToken not found for jti=%s", refresh.get("jti"))
            return False, "Outstanding token not found"
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Error blacklisting token: %s", exc)
            return False, "Failed to blacklist token"
