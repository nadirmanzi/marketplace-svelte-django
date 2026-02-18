"""
Custom JWT Authentication with session versioning and security checks.
Validates that the session_version in the token matches the user's
current session_version, invalidating tokens after password change.
Also checks for soft-deleted users.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from django.utils.translation import gettext_lazy as _
from config.logging import audit_log


class CustomJWTAuthentication(JWTAuthentication):
    """
    JWT authentication with enhanced security checks:
    - Session version validation (invalidates on password change)
    - Soft-delete check (blocks deleted users)
    - Comprehensive audit logging
    """
    
    def authenticate(self, request):
        """Override to capture request for logging."""
        self.request = request
        return super().authenticate(request)
    
    def get_user(self, validated_token):
        """
        Get user and perform security validations.
        
        Checks performed:
        1. User exists and is active (handled by parent)
        2. User is not soft-deleted
        3. Session version matches (token not invalidated)
        
        Args:
            validated_token: JWT token payload (already validated)
        
        Returns:
            User instance if all checks pass
        
        Raises:
            AuthenticationFailed: If any security check fails
        """
        # Get user from parent (handles existence and is_active check)
        try:
            user = super().get_user(validated_token)
        except (AuthenticationFailed, InvalidToken) as e:
            audit_log.warning(
                action="auth.token_validation_failed",
                message=f"Token validation failed: {e}",
                status="failed",
                source="users.authentication.CustomJWTAuthentication",
                extra={
                    "ip_address": self._get_client_ip(),
                    "path": getattr(self.request, 'path', None),
                },
            )
            raise
        
        # Check 1: Soft-delete status
        if user.is_soft_deleted:
            audit_log.warning(
                action="auth.soft_deleted_access_attempt",
                message="Soft-deleted user attempted authentication",
                status="blocked",
                source="users.authentication.CustomJWTAuthentication",
                extra={"ip_address": self._get_client_ip()},
            )
            raise AuthenticationFailed(
                _("User account has been deleted."),
                code="account_deleted",
            )
        
        # Check 2: Session version validation
        token_version = validated_token.get("session_version", 0)
        user_version = getattr(user, "session_version", 0)
        
        if token_version != user_version:
            audit_log.warning(
                action="auth.session_version_mismatch",
                message="Session invalidated - version mismatch",
                status="blocked",
                source="users.authentication.CustomJWTAuthentication",
                extra={
                    "token_version": token_version,
                    "user_version": user_version,
                    "ip_address": self._get_client_ip(),
                },
            )
            raise AuthenticationFailed(
                _("Your session has expired. Please log in again."),
                code="session_expired",
            )
        
        # All checks passed, update audit context with authenticated user
        from config.logging.audit import update_request_context
        # We only update the user_id, preserving existing IP and resource from middleware
        update_request_context(user_id=user.user_id)
        
        return user
    
    def _get_client_ip(self):
        """
        Extract client IP address from request.
        
        Returns:
            str: Client IP address or None if unavailable
        """
        if not hasattr(self, 'request'):
            return None
        
        # Check for proxy headers first
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take first IP in chain (client IP)
            return x_forwarded_for.split(',')[0].strip()
        
        # Fallback to direct connection IP
        return self.request.META.get('REMOTE_ADDR')