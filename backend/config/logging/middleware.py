"""
Logging middleware for capturing request context.

Provides AuditLoggingMiddleware which extracts:
- Client IP address (with proxy support)
- Authenticated user ID
- Request resource (path + query string)
"""
from .audit import set_request_context, clear_request_context


class AuditLoggingMiddleware:
    """
    Middleware that captures request context for audit logging.
    
    Must be placed after AuthenticationMiddleware to access request.user.
    Stores context in thread-local storage for access by AuditLogger.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        self._set_context(request)
        
        try:
            return self.get_response(request)
        finally:
            clear_request_context()
    
    def _set_context(self, request) -> None:
        """Extract and set request context."""
        ip_addr = self._get_client_ip(request)
        
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = getattr(request.user, "user_id", None) or getattr(request.user, "pk", None)
        
        resource = request.path
        if request.META.get("QUERY_STRING"):
            resource = f"{resource}?{request.META['QUERY_STRING']}"
        
        set_request_context(ip_addr=ip_addr, user_id=user_id, resource=resource)
    
    def _get_client_ip(self, request) -> str:
        """Get client IP, handling proxy headers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
