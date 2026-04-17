"""
Authentication views for JWT token management.

Provides endpoints for:
- Login: Obtain JWT access + refresh tokens
- Token Refresh: Get new access token using refresh token
- Token Verify: Validate token is still valid
- Logout: Blacklist refresh token (if blacklist enabled)

All views use custom token classes that include session_version
for forced logout on password change.
"""

import json

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.contrib.auth import get_user_model

# Removed ScopedRateThrottle as we now use our custom specialized throttles

from config.logging import audit_log
from users.serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
)
from users.throttling import LoginRateThrottle, UserActionThrottle
from users.utils.cookies import set_auth_cookies, delete_auth_cookies


User = get_user_model()


class LoginView(TokenObtainPairView):
    """
    User login endpoint - returns access + refresh tokens.

    POST /api/users/auth/login/
    Body: {
        "email": "user@example.com",
        "password": "secure_password"
    }

    Returns: {
        "access": "eyJ...",
        "refresh": "eyJ..."
    }

    Tokens include:
    - user_id: UUID of the user
    - email: User's email address
    - session_version: For forced logout on password change
    """

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        summary="User Login",
        description="Authenticates user and returns JWT access + refresh tokens.",
        responses={
            200: CustomTokenObtainPairSerializer,
            403: OpenApiResponse(description="Password expired"),
        },
    )
    def post(self, request, *args, **kwargs):
        """Handle login request with custom token generation and audit logging."""
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log failed login attempt
            audit_log.warning(
                action="auth.login_failed",
                message=f"Login failed: {str(e)}",
                status="failed",
                source="users.views.LoginView",
            )
            raise

        user = serializer.user

        # Invalidate old sessions by incrementing version
        user.session_version += 1
        user.save(update_fields=["session_version"])

        # Re-generate tokens with new version
        from users.tokens import CustomRefreshToken

        refresh = CustomRefreshToken.for_user(user)

        # Check if password has expired AFTER generating tokens but BEFORE logging success
        if hasattr(user, "password_expired") and user.password_expired:
            audit_log.warning(
                action="auth.login_password_expired",
                message="User logged in with expired password",
                status="blocked",
                source="users.views.LoginView",
                target_user_id=str(user.user_id),
            )
            response = Response(
                {
                    "success": False,
                    "code": "password_expired",
                    "detail": "Your password has expired. Please change it to continue.",
                    "errors": {},
                },
                status=status.HTTP_403_FORBIDDEN,
            )
            return set_auth_cookies(response, str(refresh.access_token), str(refresh))

        audit_log.info(
            action="auth.login_success",
            message="User logged in successfully",
            status="success",
            source="users.views.LoginView",
            target_user_id=str(user.user_id),
        )

        response = Response(status=status.HTTP_200_OK)

        return set_auth_cookies(response, str(refresh.access_token), str(refresh))


class CustomTokenRefreshView(TokenRefreshView):
    """
    Token refresh endpoint - returns new access token (and optionally new refresh token).

    POST /api/users/auth/token/refresh/
    Body: {
        "refresh": "eyJ..."
    }

    Returns: {
        "detail": "Token successfully refreshed."
    }
    
    Sets new HttpOnly cookies for access and optionally refresh tokens.

    With ROTATE_REFRESH_TOKENS enabled:
    - Old refresh token is blacklisted
    - New refresh token is returned
    - This prevents token reuse attacks
    """

    serializer_class = CustomTokenRefreshSerializer
    permission_classes = [AllowAny]
    throttle_classes = [UserActionThrottle]
    # throttle_scope = 'user'  # No longer needed with UserActionThrottle

    @extend_schema(
        summary="Refresh Token",
        description="Provides a new access token using a valid refresh token.",
    )
    def post(self, request, *args, **kwargs):
        """Handle token refresh with audit logging."""
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if "refresh" not in data and "refresh_token" in request.COOKIES:
            data["refresh"] = request.COOKIES.get("refresh_token")

        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log failed refresh
            audit_log.warning(
                action="auth.token_refresh_failed",
                message=f"Token refresh failed: {str(e)}",
                status="failed",
                source="users.views.CustomTokenRefreshView",
            )
            raise

        # Log successful refresh (debug level - happens frequently)
        audit_log.debug(
            action="auth.token_refreshed",
            message="Access token refreshed successfully",
            status="success",
            source="users.views.CustomTokenRefreshView",
        )

        # Extract tokens from serializer data
        access_token = serializer.validated_data.get("access")
        refresh_token = serializer.validated_data.get("refresh")
        
        response = Response(status=status.HTTP_200_OK)

        response = set_auth_cookies(response, str(access_token), str(refresh_token))

        return response

class CustomTokenVerifyView(TokenVerifyView):
    """
    Token verification endpoint - checks if token is valid.

    POST /api/users/auth/token/verify/
    Body: {
        "token": "eyJ..."
    }

    Returns:
    - 200 OK if token is valid
    - 401 Unauthorized if token is invalid/expired

    Use this to check token validity before making API calls,
    or to implement "remember me" functionality.
    """

    permission_classes = [AllowAny]
    throttle_classes = [UserActionThrottle]
    # throttle_scope = 'user'  # No longer needed with UserActionThrottle

    @extend_schema(
        summary="Verify Token",
        description="Verifies the validity of a token (e.g. access or refresh).",
    )
    def post(self, request, *args, **kwargs):
        """Handle token verification with audit logging."""
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if "token" not in data and "access_token" in request.COOKIES:
            data["token"] = request.COOKIES.get("access_token")

        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log verification failure (debug level)
            # return Response(str(e))

            audit_log.debug(
                action="auth.token_verify_failed",
                message=f"Token verification failed: {str(e)}",
                status="failed",
                source="users.views.CustomTokenVerifyView",
            )
            raise

        return Response(status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout endpoint - blacklists refresh token.

    POST /api/users/auth/logout/
    Body: {} (No longer requires refresh token in body, relies on cookies)

    Returns: {
        "detail": "Successfully logged out."
    }

    This blacklists the refresh token, preventing it from being used
    to generate new access tokens. The current access token remains
    valid until it expires (10 minutes by default).

    For immediate logout, client should:
    1. Call this endpoint to blacklist refresh token
    2. Delete tokens from local storage
    3. Redirect to login page
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [UserActionThrottle]
    # throttle_scope = 'user'  # No longer needed with UserActionThrottle

    @extend_schema(
        summary="User Logout",
        description="Blacklists the refresh token and invalidates the session.",
        responses={
            200: OpenApiResponse(description="Successfully logged out."),
            400: OpenApiResponse(description="Refresh token is required."),
        },
    )
    def post(self, request):
        """Blacklist refresh token to logout user."""
        try:
            refresh_token = request.COOKIES.get("refresh_token")

            if refresh_token:
                # Blacklist the refresh token
                from rest_framework_simplejwt.tokens import RefreshToken

                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except TokenError:
                    # Token might already be blacklisted or invalid, proceed with logout anyway
                    pass

            # Increment session version to invalidate all current access tokens
            request.user.session_version += 1
            request.user.save(update_fields=["session_version"])

            # Log successful logout
            audit_log.info(
                action="auth.logout_success",
                message="User logged out successfully",
                status="success",
                source="users.views.LogoutView",
                target_user_id=str(request.user.user_id),
            )

            response = Response(
                {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
            )
            return delete_auth_cookies(response)

        except Exception as e:
            # Log logout failure
            audit_log.warning(
                action="auth.logout_failed",
                message=f"Logout failed: {str(e)}",
                status="failed",
                source="users.views.LogoutView",
                target_user_id=str(request.user.user_id)
                if request.user.is_authenticated
                else None,
            )
            raise
