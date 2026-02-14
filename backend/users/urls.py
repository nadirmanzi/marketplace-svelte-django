from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AccountViewSet
from allauth.headless.account import views as allauth_views

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")
router.register(r"", AccountViewSet, basename="account")

urlpatterns = [
    path("", include(router.urls)),
    path("", include("allauth.headless.urls")),
]
