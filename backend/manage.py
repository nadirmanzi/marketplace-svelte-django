#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Auto-detect which settings module to use based on .env file presence
    # This allows seamless switching between local and production environments
    backend_dir = Path(__file__).resolve().parent

    if (backend_dir / ".env.local").exists():
        settings_module = "config.settings.local"
    elif (backend_dir / ".env.production").exists():
        settings_module = "config.settings.production"
    else:
        # Fallback to base settings if no environment file found
        settings_module = "config.settings.base"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
