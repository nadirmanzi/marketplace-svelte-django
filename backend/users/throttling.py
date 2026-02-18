"""
Rate throttling classes for the users app.

Provides:
- UserThrottle: Mixin that exempts superusers from rate limits.
- LoginRateThrottle: Anonymous rate limit for login attempts (scope: 'login').
- RegistrationRateThrottle: Anonymous rate limit for registration (scope: 'register').
- UserActionThrottle: Per-user rate limit for general actions (scope: 'user').

Rates are configured in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']:
    'login': '5/min'
    'register': '3/hour'
    'user': '100/day'
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class UserThrottle:
    """
    Mixin that bypasses throttling for superusers.

    Superusers are exempt from all rate limits to avoid blocking admin operations.
    Must be placed before the throttle base class in MRO so allow_request is called first.

    Example:
        class MyThrottle(UserThrottle, AnonRateThrottle):
            scope = 'my_scope'
    """

    def allow_request(self, request, view):
        """
        Allow request unconditionally for authenticated superusers.

        Args:
            request: DRF request object.
            view: The view being accessed.

        Returns:
            True if user is a superuser, otherwise delegates to parent throttle logic.
        """
        if request.user and request.user.is_authenticated and request.user.is_superuser:
            return True
        return super().allow_request(request, view)


class LoginRateThrottle(UserThrottle, AnonRateThrottle):
    """
    Rate limit for login attempts (anonymous).

    Scope: 'login' — configure rate in DEFAULT_THROTTLE_RATES.
    Superusers are exempt via UserThrottle mixin.
    """
    scope = 'login'


class RegistrationRateThrottle(UserThrottle, AnonRateThrottle):
    """
    Rate limit for user registration (anonymous).

    Scope: 'register' — configure rate in DEFAULT_THROTTLE_RATES.
    Superusers are exempt via UserThrottle mixin.
    """
    scope = 'register'


class UserActionThrottle(UserThrottle, UserRateThrottle):
    """
    Per-user rate limit for general authenticated actions.

    Scope: 'user' — configure rate in DEFAULT_THROTTLE_RATES.
    Superusers are exempt via UserThrottle mixin.
    """
    scope = 'user'