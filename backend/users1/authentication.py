"""
Custom JWT Authentication with session versioning.

Validates that the session_version in the token matches the user's
current session_version, invalidating tokens after password change.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from django.utils.translation import gettext_lazy as _
from config.logging import audit_log


class CustomJWTAuthentication(JWTAuthentication):
    """JWT authentication with session version validation."""
    
    def get_user(self, validated_token):
        """Get user and validate session version."""
        try:
            user = super().get_user(validated_token)
        except (AuthenticationFailed, InvalidToken) as e:
            audit_log.warning(
                action="auth.token_validation",
                message=f"Token validation failed: {e}",
                status="failed",
                source="users.authentication.CustomJWTAuthentication"
            )
            raise

        token_version = validated_token.get("session_version", 0)
        user_version = getattr(user, "session_version", 0)

        if token_version != user_version:
            audit_log.warning(
                action="auth.session_invalidation",
                message="Session invalidated - version mismatch",
                status="failed",
                source="users.authentication.CustomJWTAuthentication",
                extra={"token_version": token_version, "user_version": user_version}
            )
            raise AuthenticationFailed(
                _("Session is invalid or has expired. Please login again."),
                code="token_not_valid",
            )

        return user
