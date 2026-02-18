"""
Audit logging utility for structured application logging.

Provides:
- Thread-local request context storage
- AuditLogger class for standardized audit entries
- Global audit_log instance for easy access

Usage:
    from config.logging import audit_log
    
    audit_log.info(
        action="user.login",
        message="User logged in",
        status="success",
        extra={"method": "email"}
    )
"""
import logging
import threading
from typing import Any, Dict, Optional


# Thread-local storage for request context
_request_context = threading.local()


def set_request_context(
    ip_addr: Optional[str] = None,
    user_id: Optional[str] = None,
    resource: Optional[str] = None
) -> None:
    """
    Set (overwrite) the full request context for the current thread.

    Called by AuditLoggingMiddleware at the start of each request to populate
    ip_addr, user_id, and resource for all subsequent log entries in this thread.

    Args:
        ip_addr: Client IP address (from X-Forwarded-For or REMOTE_ADDR).
        user_id: Authenticated user's UUID as string, or None for anonymous.
        resource: Request path (e.g. '/users/management/').
    """
    _request_context.ip_addr = ip_addr
    _request_context.user_id = str(user_id) if user_id else None
    _request_context.resource = resource


def update_request_context(
    ip_addr: Optional[str] = None,
    user_id: Optional[str] = None,
    resource: Optional[str] = None
) -> None:
    """
    Partially update the request context for the current thread.

    Unlike set_request_context, only non-None arguments are applied, so existing
    values are preserved. Used by CustomJWTAuthentication.get_user to inject
    user_id after DRF authentication resolves the user (which happens after
    AuditLoggingMiddleware has already set the initial context).

    Args:
        ip_addr: Client IP address to update, or None to leave unchanged.
        user_id: Authenticated user UUID to update, or None to leave unchanged.
        resource: Request path to update, or None to leave unchanged.

    Example:
        update_request_context(user_id=str(user.user_id))
    """
    if ip_addr is not None:
        _request_context.ip_addr = ip_addr
    if user_id is not None:
        _request_context.user_id = str(user_id)
    if resource is not None:
        _request_context.resource = resource


def get_request_context() -> Dict[str, Any]:
    """
    Retrieve the current thread's request context.

    Returns:
        dict with keys: ip_addr, user_id, resource (all may be None).
    """
    return {
        "ip_addr": getattr(_request_context, "ip_addr", None),
        "user_id": getattr(_request_context, "user_id", None),
        "resource": getattr(_request_context, "resource", None),
    }


def clear_request_context() -> None:
    """
    Reset all request context fields to None for the current thread.

    Called by AuditLoggingMiddleware after the response is sent to prevent
    context leakage between requests on the same thread (important for
    thread-pool servers like gunicorn/uwsgi).
    """
    _request_context.ip_addr = None
    _request_context.user_id = None
    _request_context.resource = None


class AuditLogger:
    """
    Structured audit logger with automatic request context.
    
    Automatically includes ip_addr, user_id, and resource from
    the current request context (set by AuditLoggingMiddleware).
    
    Args:
        name: Logger name (default: "audit")
    """
    
    def __init__(self, name: str = "audit"):
        self.logger = logging.getLogger(name)
    
    def _log(
        self,
        level: int,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """
        Build and emit a structured log entry.

        Merges the current thread's request context (ip_addr, user_id, resource)
        with the caller-supplied fields and passes them as `extra` to the
        underlying logger so AuditJsonFormatter can serialize them.

        Args:
            level: Python logging level constant (e.g. logging.INFO).
            action: Dot-namespaced action identifier (e.g. 'user.login').
            message: Human-readable description of the event.
            status: Outcome string ('success', 'failed', 'pending', etc.).
            source: Fully-qualified caller path (e.g. 'users.views.LoginView').
            resource_id: ID of the primary resource affected (e.g. product UUID).
            target_user_id: UUID of the user being acted upon (may differ from user_id).
            extra: Arbitrary additional data to include in the log entry.
            exc_info: If True, attach current exception traceback.
        """
        context = get_request_context()

        extra_fields = {
            "ip_addr": context.get("ip_addr"),
            "user_id": context.get("user_id"),
            "resource": context.get("resource"),
            "action": action,
            "status": status,
            "source": source,
            "resource_id": str(resource_id) if resource_id else None,
            "target_user_id": str(target_user_id) if target_user_id else None,
            "extra": extra or {},
        }

        self.logger.log(level, message, extra=extra_fields, exc_info=exc_info)
    
    def debug(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a DEBUG level message."""
        self._log(logging.DEBUG, action, message, status, source, resource_id, target_user_id, extra)
    
    def info(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an INFO level message."""
        self._log(logging.INFO, action, message, status, source, resource_id, target_user_id, extra)
    
    def warning(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a WARNING level message."""
        self._log(logging.WARNING, action, message, status, source, resource_id, target_user_id, extra)
    
    def error(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log an ERROR level message."""
        self._log(logging.ERROR, action, message, status, source, resource_id, target_user_id, extra, exc_info)
    
    def critical(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        resource_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log a CRITICAL level message."""
        self._log(logging.CRITICAL, action, message, status, source, resource_id, target_user_id, extra, exc_info)


# Global audit logger instance
audit_log = AuditLogger("audit")
