# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views.user_auth_views import (
    LoginView,
    LogoutView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
)

from users.views.user_management_views import UserManagementViewSet

router = DefaultRouter()
router.register(r"", UserManagementViewSet, basename="user")

urlpatterns = [
    # Authentication
    path("auth/login/", LoginView.as_view(), name="user-login"),
    path("auth/logout/", LogoutView.as_view(), name="user-logout"),
    path(
        "auth/token/refresh/",
        CustomTokenRefreshView.as_view(),
        name="user-token_refresh",
    ),
    path(
        "auth/token/verify/", CustomTokenVerifyView.as_view(), name="user-token_verify"
    ),
    # User CRUD (includes registration as POST /api/users/)
    path("management/", include(router.urls)),
]
