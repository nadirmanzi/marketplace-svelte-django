from config.logging import LOGGING
from pathlib import Path
import datetime
import os
import environ
from corsheaders.defaults import default_headers

# Initialize environ
env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# pointing to backend/ instead of backend/config/settings
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Auto-detect environment and load appropriate .env file
# Logic:
# 1. Trust DOTENV_FILE if valid.
# 2. If running production settings, load .env.production
# 3. If running local settings, load .env.local
# 4. Fallback to .env

LOGGING = LOGGING


def get_env_file(base_dir):
    """Determine which .env file to load."""
    # 1. Explicit override
    custom_env = os.environ.get("DOTENV_FILE")
    if custom_env:
        return Path(custom_env)

    # 2. Infer from Settings Module
    # Note: manage.py might set a default, but this is usually safe for file existence checks
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

    if "production" in settings_module:
        return base_dir / ".env.production"

    if "local" in settings_module:
        return base_dir / ".env.local"

    # 3. Generic Fallback
    return base_dir / ".env"


ENV_FILE = get_env_file(BASE_DIR)

# Read environment variables from the detected file
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))
    print(f"Loading environment from: {ENV_FILE.name}")
else:
    # If explicit file was expected but missing, specific environments might want to warn
    # but we'll just log generic warning for now.
    print(
        f"WARNING: Environment file {ENV_FILE.name} not found. Using environment variables only."
    )

# Logging configuration (imported from separate module)
# config.logging is now relative to backend root, which is in python path

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    # DRF apps
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    # Other apps
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "simple_history",
    # Core apps
    "users",
    "catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.logging.AuditLoggingMiddleware",
    "users.middleware.PasswordExpirationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# Using env.db() to respect DATABASE_URL

if env("ENVIRONMENT") == "production":
    DATABASES = {
        "default": env.db("DATABASE_URL"),
    }
elif env("ENVIRONMENT") == "local":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }
else:
    raise ValueError("Invalid environment")


# Redis Cache
# CACHES = {
#     "default": env.cache("REDIS_URL"),
# }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- Custom settings ----------


# CORS Configuration
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-session-token",
    "x-email-verification-key",
    "x-password-reset-key",
)

# Auth user model
AUTH_USER_MODEL = "users.User"

# DRF configurations
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": (
        "config.renderers.StandardizedJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.authentication.CustomJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "500/hour",
        "user": "5000/day",
        "login": "5/min",
        "register": "2/hour",
        "password_reset": "3/hour",
        "sensitive": "10/hour",
        "search": "30/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "user_id",  # DB field name
    "USER_ID_CLAIM": "user_id",  # JWT claim name
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "UPDATE_LAST_LOGIN": False,
}

# Spectacular configurations
SPECTACULAR_SETTINGS = {
    "TITLE": "Marketplace API",
    "DESCRIPTION": "API schema for the Marketplace project.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

PASSWORD_EXPIRATION_MIDDLEWARE = {
    "EXEMPT_URL_NAMES": [
        "user-login",
        "user-register",
        "user-logout",
        "user-token_refresh",
        "user-change-password",
        "user-password_reset",
        "user-password_reset_confirm",
    ],
    "EXEMPT_URL_PREFIXES": ["/admin/", "/schema/", "/static/", "/media/"],
    "EXEMPT_SUPERUSERS": True,  # Whether to exempt superusers
    "WARNING_DAYS": 7,  # Days before expiry to start warning
}
