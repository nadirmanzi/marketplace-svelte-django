from .base import *

DEBUG = True

# Use console backend for development to avoid sending real emails
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relaxed security for local dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
