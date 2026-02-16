"""
Password expiration middleware.

Blocks access to protected endpoints when user's password has expired.
Users must change their password via the change_password endpoint.
"""

from django.http import JsonResponse
from django.urls import resolve
from config.logging import audit_log


class PasswordExpirationMiddleware:
    """Middleware that enforces password expiration policy."""

    EXEMPT_URL_NAMES = [
        "user-login",
        "user-logout",
        "user-token_refresh",
        "user-change_password",
    ]

    EXEMPT_URL_PREFIXES = ["/admin/", "/schema/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Check password expiration before view execution."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        if self._is_exempt_url(request):
            return None

        if hasattr(request.user, "password_expired") and request.user.password_expired:
            audit_log.warning(
                action="auth.password_expired",
                message="Access blocked - password expired",
                status="blocked",
                source="users.middleware.PasswordExpirationMiddleware",
            )
            return JsonResponse(
                {
                    "error": "password_expired",
                    "detail": "Your password has expired. Please change your password.",
                },
                status=403,
            )

        return None

    def _is_exempt_url(self, request) -> bool:
        """Check if URL is exempt from expiration check."""
        for prefix in self.EXEMPT_URL_PREFIXES:
            if request.path.startswith(prefix):
                return True

        try:
            resolved = resolve(request.path)
            return resolved.url_name in self.EXEMPT_URL_NAMES
        except Exception:
            return False
