"""
Password expiration middleware.
Blocks access to protected endpoints when user's password has expired.
Users must change their password via the change_password endpoint.
"""
from datetime import timedelta
from django.http import JsonResponse
from django.urls import resolve
from django.utils import timezone
from django.conf import settings
from config.logging import audit_log


class PasswordExpirationMiddleware:
    """Middleware that enforces password expiration policy."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Load config from settings
        config = getattr(settings, 'PASSWORD_EXPIRATION_MIDDLEWARE', {})
        self.exempt_url_names = config.get('EXEMPT_URL_NAMES', [
            "user-login",
            "user-logout",
            "user-token_refresh",
            "user-change_password",
            "user-register",
            "user-password_reset",
            "user-password_reset_confirm",
        ])
        self.exempt_url_prefixes = config.get('EXEMPT_URL_PREFIXES', [
            "/admin/",
            "/schema/",
            "/static/",
            "/media/",
            "/api/docs/",
        ])
        self.exempt_superusers = config.get('EXEMPT_SUPERUSERS', True)
        self.warning_days = config.get('WARNING_DAYS', 7)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add expiry warning to response headers (non-blocking)
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._add_expiry_warning_header(request, response)
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Check password expiration before view execution."""
        # Skip if not authenticated
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None
        
        # Exempt superusers if configured
        if self.exempt_superusers and request.user.is_superuser:
            return None
        
        # Exempt specific URLs
        if self._is_exempt_url(request):
            return None
        
        # Block if password expired
        if hasattr(request.user, "password_expired") and request.user.password_expired:
            self._log_expiration_block(request)
            return JsonResponse(
                {
                    "error": "password_expired",
                    "detail": "Your password has expired. Please change your password.",
                    "change_password_url": "/api/users/change-password/",  # Helpful!
                },
                status=403,
            )
        
        return None
    
    def _is_exempt_url(self, request) -> bool:
        """Check if URL is exempt from expiration check."""
        # Check prefixes first (faster)
        for prefix in self.exempt_url_prefixes:
            if request.path.startswith(prefix):
                return True
        
        # Check URL names
        try:
            resolved = resolve(request.path)
            return resolved.url_name in self.exempt_url_names
        except Exception:
            return False
    
    def _add_expiry_warning_header(self, request, response):
        """Add warning header if password is expiring soon."""
        user = request.user
        
        if not hasattr(user, 'password_changed_at') or not user.password_changed_at:
            return
        
        expires_at = user.password_changed_at + timedelta(
            days=user.password_expires_in_days
        )
        days_until_expiry = (expires_at - timezone.now()).days
        
        if days_until_expiry > 0:
            response['X-Password-Expires-In-Days'] = str(days_until_expiry)
            
            # Add warning if within threshold
            if days_until_expiry <= self.warning_days:
                response['X-Password-Expiry-Warning'] = 'true'
    
    def _log_expiration_block(self, request):
        """Log when access is blocked due to expired password."""
        user = request.user
        days_since_change = None
        
        if user.password_changed_at:
            days_since_change = (timezone.now() - user.password_changed_at).days
        
        audit_log.warning(
            action="auth.password_expired",
            message="Access blocked - password expired",
            status="blocked",
            source="users.middleware.PasswordExpirationMiddleware",
            user_id=str(user.user_id),
            email=user.email,
            path=request.path,
            method=request.method,
            days_since_change=days_since_change,
            password_expires_in_days=user.password_expires_in_days,
        )