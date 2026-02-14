"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Auto-detect which settings module to use based on .env file presence
# For production deployments, ensure .env.production exists
backend_dir = Path(__file__).resolve().parent.parent

if (backend_dir / ".env.local").exists():
    settings_module = "config.settings.local"
elif (backend_dir / ".env.production").exists():
    settings_module = "config.settings.production"
else:
    # Default to production if no environment file found (safer for deployments)
    settings_module = "config.settings.production"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
