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
    """Set request context for the current thread."""
    _request_context.ip_addr = ip_addr
    _request_context.user_id = str(user_id) if user_id else None
    _request_context.resource = resource


def get_request_context() -> Dict[str, Any]:
    """Get request context for the current thread."""
    return {
        "ip_addr": getattr(_request_context, "ip_addr", None),
        "user_id": getattr(_request_context, "user_id", None),
        "resource": getattr(_request_context, "resource", None),
    }


def clear_request_context() -> None:
    """Clear request context for the current thread."""
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
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Internal method to create structured log entry."""
        context = get_request_context()
        
        extra_fields = {
            "ip_addr": context.get("ip_addr"),
            "user_id": context.get("user_id"),
            "resource": context.get("resource"),
            "action": action,
            "status": status,
            "source": source,
            "extra": extra or {},
        }
        
        self.logger.log(level, message, extra=extra_fields, exc_info=exc_info)
    
    def debug(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a DEBUG level message."""
        self._log(logging.DEBUG, action, message, status, source, extra)
    
    def info(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an INFO level message."""
        self._log(logging.INFO, action, message, status, source, extra)
    
    def warning(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a WARNING level message."""
        self._log(logging.WARNING, action, message, status, source, extra)
    
    def error(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log an ERROR level message."""
        self._log(logging.ERROR, action, message, status, source, extra, exc_info)
    
    def critical(
        self,
        action: str,
        message: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False
    ) -> None:
        """Log a CRITICAL level message."""
        self._log(logging.CRITICAL, action, message, status, source, extra, exc_info)


# Global audit logger instance
audit_log = AuditLogger("audit")
