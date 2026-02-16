from config.logging import LOGGING  # noqa: F401
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
    # Allauth apps
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Other apps
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Core apps
    "users",
    "products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.logging.AuditLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    *default_headers,
    "x-session-token",
    "x-email-verification-key",
    "x-password-reset-key",
)

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.authentication.CustomJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/min",
        "user": "100/min",
        "login": "5/min",
        "register": "5/min",
        "email_verification": "100/hour",
        "password_reset": "2/hour",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Marketplace API",
    "DESCRIPTION": "API schema for the Marketplace project.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=1),
    # Token rotation: When enabled, old refresh tokens are blacklisted and new ones issued
    # on each refresh. This prevents token reuse attacks. The CustomHeadlessAdapter
    # ensures rotated refresh tokens are included in API responses.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "user_id",
}

# Enforce single active session per user
SINGLE_ACTIVE_SESSION = False

# Email Configuration
# Defaults; overridden in environment specific settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@marketplace.com")

# Email Verification Token Expiration (in seconds)
EMAIL_VERIFICATION_TOKEN_EXPIRY = 5 * 60 * 60  # 5 hours

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by email
    "allauth.account.auth_backends.AuthenticationBackend",
]

# AllAuth
HEADLESS_ONLY = True
REST_USE_JWT = True
JWT_AUTH_COOKIE = None
JWT_AUTH_REFRESH_COOKIE = None
SITE_ID = 1

# Allauth Headless Configuration
# Custom adapter supports token rotation by including rotated refresh tokens in responses
HEADLESS_ADAPTER = "users.adapters.CustomHeadlessAdapter"
HEADLESS_TOKEN_STRATEGY = "users.allauth_strategy.SimpleJWTTokenStrategy"
HEADLESS_SERVE_TOKEN_AS = "header"  # No cookies, header only
HEADLESS_CLIENTS = ('app',)  # 'app' or 'browser', 'app' typically implies no session cookies for auth state
# ALLAUTH_HEADLESS_CLIENTS = {
#     "app": {
#         "token_strategy": "users.allauth_strategy.SimpleJWTTokenStrategy",
#     }
# }

# Custom account adapter for account lockout integration with AllAuth
ACCOUNT_ADAPTER = "users.adapters.CustomAccountAdapter"

# Allauth account settings
# Authentication method: email-only (no username)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SIGNUP_FIELDS=['email*', 'first_name', 'last_name', 'telephone_number', 'password1*', 'password2*']

# Signup configuration
# Use custom signup form to handle phone number and name fields
# ACCOUNT_FORMS = {
#     "signup": "users.forms.CustomSignupForm",
# }

# Email verification: mandatory for security
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True

# Password requirements (Django validators handle complexity)
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Session management (for API/headless, no session cookies)
ACCOUNT_SESSION_REMEMBER = None  # Not applicable in headless mode
ACCOUNT_LOGOUT_ON_GET = False  # API should use POST for logout

HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{env('FRONTEND_URL')}/auth/v1/verify-email/{{key}}",
    "account_reset_password": f"{env('FRONTEND_URL')}/auth/v1/password/reset/{{key}}",
    "account_signup": f"{env('FRONTEND_URL')}/auth/v1/signup",
}

# Account Lockout Configuration
ACCOUNT_LOCKOUT_ENABLED = True
ACCOUNT_LOCKOUT_THRESHOLD = 5  # Failed attempts before lockout
ACCOUNT_LOCKOUT_DURATION_MINUTES = 15  # Lockout duration
ACCOUNT_LOCKOUT_TRACK_IP = True  # Enable IP tracking
ACCOUNT_LOCKOUT_IP_THRESHOLD = 10  # IP lockout threshold
ACCOUNT_LOCKOUT_IP_DURATION_MINUTES = 30  # IP lockout duration
