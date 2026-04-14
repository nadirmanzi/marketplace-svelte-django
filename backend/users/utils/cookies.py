"""
Utility functions for setting and deleting secure HTTP-only cookies
for JWT authentication.
"""
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.settings import api_settings

def set_auth_cookies(response, access_token, refresh_token=None):
    """
    Sets JWT access and optionally refresh tokens in the response cookies.
    Forces HttpOnly, Lax SameSite, and Secure (if not in debug mode).
    
    Args:
        response (Response): The DRF response object to modify.
        access_token (str): The raw string value of the JWT access token.
        refresh_token (str, optional): The raw string value of the JWT refresh token.
        
    Returns:
        Response: The modified response object.
    """
    # Max age matches the JWT token lifetimes configured in settings
    access_max_age = int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_max_age,
        secure=not settings.DEBUG,
        httponly=True,
        samesite="Lax",
        path="/"
    )

    # Set a non-HttpOnly cookie for the frontend to track expiration
    # Unix timestamp in seconds
    expires_at = int((timezone.now() + api_settings.ACCESS_TOKEN_LIFETIME).timestamp())
    response.set_cookie(
        key="access_token_expires",
        value=str(expires_at),
        max_age=access_max_age,
        secure=not settings.DEBUG,
        httponly=False,  # Allow frontend JS to read this
        samesite="Lax",
        path="/"
    )

    if refresh_token:
        refresh_max_age = int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_max_age,
            secure=not settings.DEBUG,
            httponly=True,
            samesite="Lax",
            path="/"
        )
        
    return response


def delete_auth_cookies(response):
    """
    Deletes JWT access and refresh tokens from the response cookies.
    
    Args:
        response (Response): The DRF response object to modify.
        
    Returns:
        Response: The modified response object.
    """
    response.delete_cookie("access_token", path="/", samesite="Lax")
    response.delete_cookie("access_token_expires", path="/", samesite="Lax")
    response.delete_cookie("refresh_token", path="/", samesite="Lax")
    response.delete_cookie("refresh_token", path="/api/users/auth/token/refresh/", samesite="Lax")
    return response
