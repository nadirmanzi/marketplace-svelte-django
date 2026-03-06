"""
Rate throttling classes for the users app.

Provides:
- UserThrottle: Mixin that exempts superusers from rate limits.
- LoginRateThrottle: Anonymous rate limit for login attempts (scope: 'login').
- RegistrationRateThrottle: Anonymous rate limit for registration (scope: 'register').
- UserActionThrottle: Per-user rate limit for general actions (scope: 'user').
- PasswordResetRateThrottle: Anonymous rate limit for password reset requests (scope: 'password_reset').
- SensitiveActionRateThrottle: Per-user rate limit for sensitive actions (scope: 'sensitive').
- SearchRateThrottle: Per-user rate limit for searching/listing (scope: 'search').

Rates are configured in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class UserThrottle:
    """
    Mixin that bypasses throttling for superusers.

    Superusers are exempt from all rate limits to avoid blocking admin operations.
    Must be placed before the throttle base class in MRO so allow_request is called first.
    """

    def allow_request(self, request, view):
        """
        Allow request unconditionally for authenticated superusers.
        """
        if request.user and request.user.is_authenticated and request.user.is_superuser:
            return True
        return super().allow_request(request, view)


class LoginRateThrottle(UserThrottle, AnonRateThrottle):
    """
    Rate limit for login attempts (anonymous).
    Scope: 'login'
    """
    scope = 'login'


class RegistrationRateThrottle(UserThrottle, AnonRateThrottle):
    """
    Rate limit for user registration (anonymous).
    Scope: 'register'
    """
    scope = 'register'


class UserActionThrottle(UserThrottle, UserRateThrottle):
    """
    Per-user rate limit for general authenticated actions.
    Scope: 'user'
    """
    scope = 'user'


class PasswordResetRateThrottle(UserThrottle, AnonRateThrottle):
    """
    Rate limit for password reset requests (anonymous).
    Scope: 'password_reset' — prevents email spamming.
    """
    scope = 'password_reset'


class SensitiveActionRateThrottle(UserThrottle, UserRateThrottle):
    """
    Rate limit for sensitive user actions (authenticated).
    Scope: 'sensitive' — for password changes, email updates, etc.
    """
    scope = 'sensitive'


class SearchRateThrottle(UserThrottle, UserRateThrottle):
    """
    Rate limit for searching/listing users (authenticated).
    Scope: 'search' — prevents aggressive scraping of user data.
    """
    scope = 'search'