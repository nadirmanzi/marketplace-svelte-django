"""
Custom formatters for the logging system.

Provides:
- AuditJsonFormatter: JSON output with structured audit fields
- LevelRangeFilter: Filter logs by level range
"""
import json
import logging
from datetime import datetime
from typing import Optional


class AuditJsonFormatter(logging.Formatter):
    """
    JSON formatter for structured audit logs.
    
    Output format:
        {
            "timestamp": "2024-12-05T07:41:26+02:00",
            "level": "INFO",
            "ip_addr": "192.168.1.1",
            "user_id": "uuid",
            "action": "user.login",
            "message": "User logged in",
            "status": "success",
            "source": "users.views.UserViewSet.login",
            "resource": "/users/login/",
            "extra": {}
        }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "level": record.levelname,
            "ip_addr": getattr(record, "ip_addr", None),
            "user_id": getattr(record, "user_id", None),
            "action": getattr(record, "action", None),
            "message": record.getMessage(),
            "status": getattr(record, "status", None),
            "source": getattr(record, "source", record.name),
            "resource": getattr(record, "resource", None),
            "extra": getattr(record, "extra", {}),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class LevelRangeFilter(logging.Filter):
    """
    Filter that accepts logs within a specified level range.
    
    Args:
        min_level: Minimum log level to accept
        max_level: Maximum log level to accept
    """
    
    def __init__(
        self,
        min_level: int = logging.DEBUG,
        max_level: int = logging.CRITICAL
    ):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level
    
    def filter(self, record: logging.LogRecord) -> bool:
        return self.min_level <= record.levelno <= self.max_level
