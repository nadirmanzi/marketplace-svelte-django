"""
Django logging configuration.

Defines the LOGGING dict used by Django with:
- Console handler (development-friendly format)
- File handlers (JSON format for audit)
- Separate files for default and error logs
"""
import logging
from pathlib import Path

# Logs directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


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
            "()": "config.logging.formatters.AuditJsonFormatter",
        },
    },
    
    "filters": {
        "default_levels": {
            "()": "config.logging.formatters.LevelRangeFilter",
            "min_level": logging.DEBUG,
            "max_level": logging.WARNING,
        },
        "error_levels": {
            "()": "config.logging.formatters.LevelRangeFilter",
            "min_level": logging.ERROR,
            "max_level": logging.CRITICAL,
        },
    },
    
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "default_file": {
            "level": "DEBUG",
            "class": "config.logging.handlers.MonthlyRotatingFileHandler",
            "prefix": "default",
            "formatter": "audit_json",
            "filters": ["default_levels"],
        },
        "error_file": {
            "level": "ERROR",
            "class": "config.logging.handlers.MonthlyRotatingFileHandler",
            "prefix": "error",
            "formatter": "audit_json",
            "filters": ["error_levels"],
        },
    },
    
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
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
