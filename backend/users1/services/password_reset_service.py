"""Password reset service with time-limited tokens.

This service generates signed, time-limited tokens for password reset
and provides methods for token validation and email sending.
"""

import logging
from typing import Tuple, Optional

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class PasswordResetService:
    """Service for password reset token generation and validation."""

    TOKEN_SALT = "password-reset"
    # Default 1 hour expiry for password reset tokens
    DEFAULT_EXPIRY = 60 * 60

    @classmethod
    def generate_token(cls, user) -> str:
        """Generate a signed, time-limited password reset token.

        Args:
            user: User instance to generate token for.

        Returns:
            Signed token string containing user_id and session_version.
        """
        return signing.dumps(
            {
                "user_id": str(user.user_id),
                "session_version": getattr(user, "session_version", 0),
            },
            salt=cls.TOKEN_SALT,
        )

    @classmethod
    def verify_token(cls, token: str) -> Tuple[Optional[User], Optional[str]]:
        """Verify a password reset token.

        The token is validated for:
        - Signature integrity
        - Expiration (1 hour default)
        - Session version match (token invalid if password changed since issue)

        Args:
            token: The signed token string.

        Returns:
            (user, None) on success.
            (None, error_message) on failure.
        """
        max_age = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY", cls.DEFAULT_EXPIRY)

        try:
            data = signing.loads(token, salt=cls.TOKEN_SALT, max_age=max_age)
        except signing.SignatureExpired:
            logger.info("Password reset token expired")
            return None, "Password reset link has expired. Please request a new one."
        except signing.BadSignature:
            logger.warning("Invalid password reset token")
            return None, "Invalid password reset link."

        user_id = data.get("user_id")
        token_session_version = data.get("session_version", 0)

        if not user_id:
            return None, "Invalid token data."

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return None, "User not found."

        # Check session version - if password was changed since token issue, reject
        current_session_version = getattr(user, "session_version", 0)
        if token_session_version != current_session_version:
            logger.warning(
                "Password reset token session version mismatch: token=%s, current=%s",
                token_session_version,
                current_session_version,
            )
            return None, "This password reset link is no longer valid."

        return user, None

    @classmethod
    def send_reset_email(cls, user, reset_url: str) -> bool:
        """Send a password reset email to the user.

        Args:
            user: User instance to send email to.
            reset_url: Full URL for password reset (including token).

        Returns:
            True if email sent successfully, False otherwise.
        """
        subject = "Reset your password"
        message = f"""
Hello {user.first_name},

We received a request to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email. Your password will remain unchanged.

Best regards,
The Marketplace Team
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Password reset email sent to %s", user.email)
            return True
        except Exception as e:
            logger.exception("Failed to send password reset email to %s: %s", user.email, e)
            return False
