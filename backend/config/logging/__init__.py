"""
Custom logging package for the Marketplace project.

Provides:
- MonthlyRotatingFileHandler: File rotation by size (10MB) and month
- AuditJsonFormatter: JSON formatter for structured audit logs
- AuditLogger: High-level logging utility with request context
- AuditLoggingMiddleware: Middleware to capture request context

Usage:
    from config.logging import audit_log
    
    audit_log.info(
        action="user.login",
        message="User logged in",
        status="success"
    )
"""
from .config import LOGGING
from .audit import audit_log, set_request_context, clear_request_context
from .middleware import AuditLoggingMiddleware

__all__ = [
    "LOGGING",
    "audit_log",
    "set_request_context",
    "clear_request_context",
    "AuditLoggingMiddleware",
]
