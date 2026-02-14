"""
Custom AllAuth Headless Adapter for Token Rotation Support and Account Lockout.

This module extends AllAuth's DefaultHeadlessAdapter to properly handle token
rotation when ROTATE_REFRESH_TOKENS is enabled in SimpleJWT settings, and
integrates account lockout checking for AllAuth headless login attempts.

Token Rotation Integration:
---------------------------
When a refresh token is rotated during token refresh:
1. SimpleJWTTokenStrategy.refresh_access_token() stores the new refresh token
   in request._allauth_rotated_refresh_token
2. This adapter's respond_to_token_refresh() method reads that stored token
3. The new refresh token is included in the response body for the client
4. Client must update their stored refresh token to continue using the API

Account Lockout Integration:
----------------------------
The adapter intercepts AllAuth headless login attempts to:
1. Check account lockout status before authentication
2. Check IP lockout status
3. Track failed login attempts
4. Reset attempts on successful login

Usage:
------
Set in settings.py:
    HEADLESS_ADAPTER = "users.adapters.CustomHeadlessAdapter"
"""

from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import JsonResponse
from users.services.account_lockout_service import AccountLockoutService


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom Account Adapter that adds account lockout checking.

    Extends DefaultAccountAdapter to check account lockout status before
    authentication attempts in AllAuth flows.
    """

    def authenticate(self, request, **credentials):
        """
        Authenticate user with lockout checking.

        Checks account and IP lockout status before attempting authentication.
        Raises ImmediateHttpResponse if account/IP is locked.
        """
        email = credentials.get("email") or credentials.get("username")
        if email:
            ip_address = AccountLockoutService.get_client_ip(request)

            # Check IP lockout
            ip_locked, ip_locked_until, ip_retry_after = (
                AccountLockoutService.check_ip_locked(ip_address)
            )
            if ip_locked:
                raise ImmediateHttpResponse(
                    JsonResponse(
                        {
                            "error": "ip_locked",
                            "detail": "Too many failed login attempts from this IP address.",
                            "locked_until": ip_locked_until,
                            "retry_after_seconds": ip_retry_after,
                        },
                        status=423,  # 423 Locked
                    )
                )

            # Check account lockout
            account_locked, account_locked_until, account_retry_after = (
                AccountLockoutService.check_account_locked(email)
            )
            if account_locked:
                raise ImmediateHttpResponse(
                    JsonResponse(
                        {
                            "error": "account_locked",
                            "detail": "Account is temporarily locked due to too many failed login attempts.",
                            "locked_until": account_locked_until,
                            "retry_after_seconds": account_retry_after,
                        },
                        status=423,  # 423 Locked
                    )
                )

        # Call parent authenticate
        user = super().authenticate(request, **credentials)

        # Track failed attempts if authentication failed
        if not user and email:
            ip_address = AccountLockoutService.get_client_ip(request)
            AccountLockoutService.record_failed_attempt(email, ip_address)
        # Reset attempts on successful authentication
        elif user and email:
            ip_address = AccountLockoutService.get_client_ip(request)
            AccountLockoutService.reset_account_attempts(email)
            AccountLockoutService.reset_ip_attempts(ip_address)

        return user


class CustomHeadlessAdapter(DefaultHeadlessAdapter):
    """
    Custom AllAuth Headless Adapter that supports token rotation and account lockout.

    Extends DefaultHeadlessAdapter to include rotated refresh tokens in the
    response when token rotation is enabled. This ensures clients can continue
    refreshing tokens after rotation occurs.

    Key Features:
    - Includes rotated refresh token in token refresh responses
    - Maintains compatibility with AllAuth's standard response format
    - Works seamlessly with SimpleJWTTokenStrategy
    - Handles both rotation-enabled and rotation-disabled scenarios
    - Account lockout is handled by CustomAccountAdapter
    """

    def respond_to_token_refresh(self, request, access_token):
        """
        Respond to token refresh request, including rotated refresh token if available.

        When token rotation is enabled, the SimpleJWTTokenStrategy stores the new
        refresh token in request._allauth_rotated_refresh_token. This method reads
        that token and includes it in the response body.

        Response Format:
        - access_token: Included in Authorization header (via parent class)
        - refresh_token: Included in response body (if rotation occurred)

        Args:
            request: Django request object (may contain _allauth_rotated_refresh_token)
            access_token: str - The new access token from token strategy

        Returns:
            Response: HTTP response with access token in header and refresh token in body

        Note:
            Clients must check for 'refresh' in the response body and update their
            stored refresh token when present. If rotation is disabled, only the
            access token is returned and the client continues using the same refresh token.
        """
        # Call parent to get standard response with access token in header
        response = super().respond_to_token_refresh(request, access_token)

        # Check if token rotation occurred (new refresh token was created)
        rotated_refresh_token = getattr(request, "_allauth_rotated_refresh_token", None)

        if rotated_refresh_token:
            # Include rotated refresh token in response body
            # Client must read this and update their stored refresh token
            if hasattr(response, "data"):
                # DRF Response object (most common with AllAuth headless)
                # Add refresh token to response data
                if not isinstance(response.data, dict):
                    # If response.data is not a dict, convert it
                    response.data = {"access": access_token}
                response.data["refresh"] = rotated_refresh_token
            elif hasattr(response, "content"):
                # Standard HttpResponse - parse JSON, add refresh token, re-encode
                import json
                import logging

                logger = logging.getLogger(__name__)
                try:
                    content_str = response.content.decode("utf-8")
                    if content_str:
                        data = json.loads(content_str)
                    else:
                        data = {}
                    data["refresh"] = rotated_refresh_token
                    response.content = json.dumps(data).encode("utf-8")
                    # Update content type if not already set
                    if "Content-Type" not in response:
                        response["Content-Type"] = "application/json"
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    # If response isn't JSON, log warning but don't break
                    logger.warning(
                        "Could not add rotated refresh token to non-JSON response: %s",
                        e,
                    )

        return response