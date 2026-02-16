from types import SimpleNamespace
from allauth.headless.account import views as allauth_views
from users1.throttling import (
    LoginRateThrottle,
    RegistrationRateThrottle,
    PasswordResetRateThrottle,
)

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(allauth_views.LoginView):
    client_id = "app"
    throttle_classes = [LoginRateThrottle]


@method_decorator(csrf_exempt, name="dispatch")
class SignupView(allauth_views.SignupView):
    client_id = "app"
    throttle_classes = [RegistrationRateThrottle]


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetView(allauth_views.RequestPasswordResetView):
    client_id = "app"
    throttle_classes = [PasswordResetRateThrottle]
