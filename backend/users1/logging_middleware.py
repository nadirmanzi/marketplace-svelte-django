"""
Logging middleware to capture request context for audit logging.

Captures:
- Client IP address (handles proxies via X-Forwarded-For)
- Authenticated user ID
- Request resource (path + query string)
"""

from .utils.audit import set_request_context, clear_request_context


class AuditLoggingMiddleware:
    """
    Middleware that captures request context for structured audit logging.

    Must be placed after AuthenticationMiddleware to access request.user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture request context before view execution
        self._set_context(request)

        try:
            response = self.get_response(request)
            return response
        finally:
            # Always clear context after request
            clear_request_context()

    def _set_context(self, request):
        """Extract and set request context for logging."""
        # Get client IP (handle proxies)
        ip_addr = self._get_client_ip(request)

        # Get user ID if authenticated
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = getattr(request.user, "user_id", None) or getattr(
                request.user, "pk", None
            )

        # Get resource (path + query string)
        resource = request.path
        if request.META.get("QUERY_STRING"):
            resource = f"{resource}?{request.META['QUERY_STRING']}"

        set_request_context(ip_addr=ip_addr, user_id=user_id, resource=resource)

    def _get_client_ip(self, request):
        """Get client IP address, handling proxy headers."""
        from .utils.network import get_client_ip

        return get_client_ip(request)
