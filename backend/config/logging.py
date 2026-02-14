"""
Custom logging configuration for the Marketplace project.

Features:
- Monthly rotating file handlers with 10MB size limit
- Separate files for default (INFO, WARNING) and error (ERROR, CRITICAL) logs
- JSON format for file logs, standard format for console
- Naming: default-Dec-2024.log, error-Dec-2024.log with .1, .2 suffixes for overflow
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# Base directory for logs
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Size limit: 10MB
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5  # Keep up to 5 backup files per month


class AuditJsonFormatter(logging.Formatter):
    """
    JSON formatter for audit logs with structured fields.
    
    Output format:
    {
        "timestamp": "2024-12-05T07:41:26+02:00",
        "level": "INFO",
        "ip_addr": "192.168.1.1",
        "user_id": "uuid-here",
        "action": "user.login",
        "message": "User logged in successfully",
        "status": "success",
        "source": "users.views.UserViewSet.login",
        "resource": "/users/login/",
        "extra": {}
    }
    """
    
    def format(self, record):
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
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class MonthlyRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Custom rotating file handler that:
    1. Rotates when file exceeds 10MB
    2. Uses monthly naming convention: <prefix>-<Mon-YYYY>.log
    3. Handles name collisions with .1, .2 suffixes
    """
    
    def __init__(self, prefix, logs_dir=LOGS_DIR, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT):
        self.prefix = prefix
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Generate initial filename
        self.current_month = self._get_month_str()
        filename = self._get_filename()
        
        super().__init__(
            filename=filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding="utf-8"
        )
    
    def _get_month_str(self):
        """Get current month string like 'Dec-2024'."""
        return datetime.now().strftime("%b-%Y")
    
    def _get_filename(self):
        """Generate filename for current month."""
        return str(self.logs_dir / f"{self.prefix}-{self.current_month}.log")
    
    def shouldRollover(self, record):
        """Check if we need to rollover (size or month change)."""
        # Check for month change
        new_month = self._get_month_str()
        if new_month != self.current_month:
            self.current_month = new_month
            self.baseFilename = self._get_filename()
            # Close current stream and open new file
            if self.stream:
                self.stream.close()
                self.stream = None
            return False  # New file, no rollover needed
        
        # Check size limit
        return super().shouldRollover(record)
    
    def doRollover(self):
        """
        Perform rollover with numbered suffixes.
        Creates: prefix-Dec-2024.log.1, prefix-Dec-2024.log.2, etc.
        """
        super().doRollover()


class LevelRangeFilter(logging.Filter):
    """Filter that accepts logs within a level range."""
    
    def __init__(self, min_level=logging.DEBUG, max_level=logging.CRITICAL):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level
    
    def filter(self, record):
        return self.min_level <= record.levelno <= self.max_level


# Logging configuration dictionary
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "audit_json": {
            "()": AuditJsonFormatter,
        },
    },
    
    "filters": {
        "default_levels": {
            "()": LevelRangeFilter,
            "min_level": logging.DEBUG,
            "max_level": logging.WARNING,
        },
        "error_levels": {
            "()": LevelRangeFilter,
            "min_level": logging.ERROR,
            "max_level": logging.CRITICAL,
        },
    },
    
    "handlers": {
        # Console handler for development (standard format)
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        
        # Default log file (DEBUG, INFO, WARNING)
        "default_file": {
            "level": "DEBUG",
            "class": "config.logging.MonthlyRotatingFileHandler",
            "prefix": "default",
            "formatter": "audit_json",
            "filters": ["default_levels"],
        },
        
        # Error log file (ERROR, CRITICAL)
        "error_file": {
            "level": "ERROR",
            "class": "config.logging.MonthlyRotatingFileHandler",
            "prefix": "error",
            "formatter": "audit_json",
            "filters": ["error_levels"],
        },
    },
    
    "loggers": {
        # Root logger
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
        
        # Django loggers
        "django": {
            "handlers": ["console", "default_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "default_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        
        # Application loggers
        "users": {
            "handlers": ["console", "default_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "audit": {
            "handlers": ["console", "default_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
