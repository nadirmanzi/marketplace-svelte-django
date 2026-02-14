from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class UserThrottle:
    """
    Mixin to exempt superusers from throttling.
    """
    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated and request.user.is_superuser:
            return True
        return super().allow_request(request, view)

class LoginRateThrottle(UserThrottle, AnonRateThrottle):
    scope = 'login'

class RegistrationRateThrottle(UserThrottle, AnonRateThrottle):
    scope = 'register'

class UserActionThrottle(UserThrottle, UserRateThrottle):
    scope = 'user'

class EmailVerificationRateThrottle(UserThrottle, UserRateThrottle):
    """Rate limit for email verification requests: 3/hour."""
    scope = 'email_verification'

class PasswordResetRateThrottle(UserThrottle, AnonRateThrottle):
    """Rate limit for password reset requests: 3/hour."""
    scope = 'password_reset'
