"""
Custom JWT token classes for minimal, efficient token payloads.

This module implements custom token classes extending SimpleJWT to provide:

- Minimal Claims: Only user_id and email in tokens (vs Django's default 50+ user fields)
- Zero DB Lookups: CustomAccessToken.for_user() and access_token property avoid DB queries
- Performance: Reduces token size, parsing overhead, and database pressure
- Security: Smaller payload surface area reduces data exposure

Token Classes:
- CustomAccessToken: Short-lived token (10min) with user_id + email claims only
- CustomRefreshToken: Long-lived token (1 day) with user_id + email + rotation support

Access Token Generation Flow:
1. On login: RefreshToken(user).access_token -> built from payload (no DB query)
2. On refresh: TokenRefreshSerializer -> builds new access token from refresh payload
3. Both paths use CustomAccessToken.for_user() which only adds minimal claims

Key Features:
- UUID Support: Converts UUID user_id to string for JSON serialization
- Email Caching: Refresh token stores email on payload so access tokens are created
  without database lookups (critical for performance with rotating refresh tokens)
- Inheritance: Extends SimpleJWT's AccessToken and RefreshToken for compatibility

Dependencies:
- rest_framework_simplejwt: Base token classes, JWT encoding/decoding
- User model: Must have email field and USER_ID_FIELD setting (typically 'user_id' for UUID)
"""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings

User = get_user_model()


class CustomAccessToken(AccessToken):
    """Short-lived JWT access token with minimal claims (user_id, email, session_version)."""

    @classmethod
    def for_user(cls, user):
        """
        Build an access token for the given user without a DB lookup.

        Args:
            user: User instance (must have email and session_version attributes).

        Returns:
            CustomAccessToken with user_id, email, and session_version claims.

        Example:
            token = CustomAccessToken.for_user(user)
            str(token)  # -> "eyJ..."
        """
        token = cls()

        # Core identity
        user_id = getattr(user, jwt_settings.USER_ID_FIELD)
        token[jwt_settings.USER_ID_FIELD] = str(user_id)
        token["email"] = user.email

        # Security: used by CustomJWTAuthentication to detect forced logouts
        token["session_version"] = getattr(user, "session_version", 0)

        return token


class CustomRefreshToken(SimpleJWTRefreshToken):
    """Long-lived JWT refresh token that caches email/session_version to avoid DB lookups on refresh."""

    @classmethod
    def for_user(cls, user):
        """
        Build a refresh token for the given user with cached email and session_version.

        Caching email on the refresh payload allows access tokens to be created
        during rotation without hitting the database.

        Args:
            user: User instance.

        Returns:
            CustomRefreshToken with user_id, email, and session_version claims.

        Example:
            refresh = CustomRefreshToken.for_user(user)
            access = refresh.access_token  # No DB query
        """
        token = super().for_user(user)

        # Cache for access token creation (avoids DB lookup on token rotation)
        token["email"] = user.email
        token["session_version"] = getattr(user, "session_version", 0)

        return token

    @property
    def access_token(self):
        """
        Generate a new access token from this refresh token's payload (no DB query).

        Reads user_id, email, and session_version directly from the refresh payload,
        so no database lookup is required. This is the key performance optimization
        for rotating refresh tokens.

        Returns:
            CustomAccessToken populated from refresh payload.

        Raises:
            ValueError: If refresh token payload is missing user_id.

        Example:
            refresh = CustomRefreshToken.for_user(user)
            access = refresh.access_token  # CustomAccessToken instance
            str(access)  # -> "eyJ..."
        """
        user_id = self.payload.get(jwt_settings.USER_ID_FIELD)
        email = self.payload.get("email")
        session_version = self.payload.get("session_version", 0)

        if not user_id:
            raise ValueError("Refresh token does not contain user_id")

        access = CustomAccessToken()
        access[jwt_settings.USER_ID_FIELD] = user_id
        if email:
            access["email"] = email
        access["session_version"] = session_version

        return access