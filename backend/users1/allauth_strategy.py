"""
AllAuth Headless Token Strategy for SimpleJWT Integration.

This module implements a custom token strategy that integrates django-allauth's
headless authentication with SimpleJWT tokens. It handles token creation, refresh,
and rotation according to AllAuth's AbstractTokenStrategy interface.

Token Rotation Behavior:
-------------------------
When ROTATE_REFRESH_TOKENS is enabled in SIMPLE_JWT settings, token rotation occurs
during refresh operations. The strategy handles this as follows:

1. refresh_access_token() calls TokenService.refresh_token() which:
   - Validates the provided refresh token
   - Blacklists the old refresh token (if rotation enabled)
   - Creates a new access token and new refresh token
   - Returns both tokens in a dict: {"access": "...", "refresh": "..."}

2. AllAuth's interface requires refresh_access_token() to return only the access
   token string. To handle rotation properly:
   - The new refresh token is stored in request._allauth_rotated_refresh_token
   - The access token is returned as required by the interface
   - A custom adapter (see users.adapters) reads the rotated refresh token and
     includes it in the API response body

3. Client behavior:
   - Client receives access token in Authorization header (via HEADLESS_SERVE_TOKEN_AS)
   - Client receives new refresh token in response body (via custom adapter)
   - Client must update stored refresh token when rotation occurs

Security Considerations:
-----------------------
- Token rotation prevents token reuse attacks by invalidating old refresh tokens
- Session versioning ensures tokens are invalidated on password change
- Blacklisted tokens cannot be used for refresh operations
- Access tokens are short-lived (10 min) to limit exposure window

Integration Points:
--------------------
- AllAuth Headless: Uses this strategy via HEADLESS_TOKEN_STRATEGY setting
- SimpleJWT: Uses CustomRefreshToken and CustomAccessToken classes
- TokenService: Handles token lifecycle and blacklist management
- Custom Adapter: Reads rotated refresh token from request and includes in response
"""

from allauth.headless.tokens.strategies.base import AbstractTokenStrategy
from users1.tokens import CustomAccessToken, CustomRefreshToken
from users1.services.token_service import TokenService

from django.conf import settings


class SimpleJWTTokenStrategy(AbstractTokenStrategy):
    """
    Token strategy that uses SimpleJWT (via CustomRefreshToken) to generate tokens.

    Implements the AllAuth Headless AbstractTokenStrategy interface for headless
    API authentication. Integrates with SimpleJWT's token rotation and blacklist
    features for enhanced security.

    Key Features:
    - Email-based authentication (no username)
    - JWT tokens with minimal claims (user_id, email, session_version)
    - Token rotation support (configurable via SIMPLE_JWT settings)
    - Session versioning for forced logout on password change
    - Zero-database token refresh (email cached in refresh token payload)

    Token Flow:
    1. Login: create_refresh_token() -> returns refresh token string
    2. API Requests: Client sends access token in Authorization header
    3. Token Refresh: refresh_access_token() -> returns new access token
    4. Token Rotation: New refresh token stored in request for adapter to include
    """

    def create_access_token(self, request):
        """
        Create a new access token for the authenticated user.

        Used when logic only demands an access token (less common in full flow).
        Typically, access tokens are created via create_refresh_token() which
        generates both tokens together.

        Args:
            request: Django request object with authenticated user

        Returns:
            str: JWT access token string (short-lived, ~10 minutes)
        """
        refresh = CustomRefreshToken.for_user(request.user)
        return str(refresh.access_token)

    def create_access_token_payload(self, request):
        return {
            "access_token": str(CustomAccessToken.for_user(request.user)),
            "refresh_token": str(CustomRefreshToken.for_user(request.user)),
            "expires_in": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        }

    def create_refresh_token(self, request):
        """
        Create a refresh token (and implicitly an access token).

        This is the primary method used during login/signup flows. It creates
        both refresh and access tokens, but returns only the refresh token string
        as required by AllAuth's interface.

        The access token can be obtained via refresh.access_token property.
        AllAuth's adapter handles including both tokens in the response.

        Args:
            request: Django request object with authenticated user

        Returns:
            str: JWT refresh token string (long-lived, ~1 day)
        """
        user = request.user
        refresh = CustomRefreshToken.for_user(user)
        return str(refresh)

    def create_refresh_token_payload(self, request):
        """
        Create payload for refresh token (not used in SimpleJWT flow).

        SimpleJWT handles token payload creation internally via CustomRefreshToken.
        This method is required by AbstractTokenStrategy but returns empty dict
        as we use the token class directly rather than building payloads manually.

        Args:
            request: Django request object

        Returns:
            dict: Empty dict (payload handled by CustomRefreshToken)
        """
        return {}

    def refresh_access_token(self, request, refresh_token):
        """
        Refresh the access token using the provided refresh token.

        This method is called by AllAuth's refresh endpoint when a client requests
        a new access token. It handles token validation, rotation (if enabled),
        and returns the new access token.

        Token Rotation Handling:
        ------------------------
        When ROTATE_REFRESH_TOKENS is enabled in SIMPLE_JWT settings:
        1. TokenService.refresh_token() blacklists the old refresh token
        2. TokenService.refresh_token() creates a new refresh token
        3. Both new tokens are returned: {"access": "...", "refresh": "..."}
        4. This method stores the new refresh token in request._allauth_rotated_refresh_token
        5. This method returns only the access token (as required by interface)
        6. A custom adapter (users.adapters.CustomHeadlessAdapter) reads the stored
           refresh token and includes it in the API response body

        When rotation is disabled:
        1. TokenService.refresh_token() returns the same refresh token
        2. Only a new access token is created
        3. No special handling needed

        Args:
            request: Django request object
            refresh_token: str - The refresh token string to use for refresh

        Returns:
            str: New JWT access token string, or None if refresh token is invalid

        Side Effects:
            - If rotation enabled: Stores new refresh token in request._allauth_rotated_refresh_token
            - Blacklists old refresh token (if rotation enabled)
            - Creates OutstandingToken entry for new refresh token (if blacklist enabled)
        """
        tokens, error = TokenService.refresh_token(refresh_token)
        if error or not tokens:
            return None

        # AllAuth's refresh_access_token() interface requires returning only the access token.
        # However, when token rotation is enabled, we also need to provide the new refresh
        # token to the client. We store it in the request object so the adapter can access it.
        new_refresh_token = tokens.get("refresh")
        if new_refresh_token:
            # Store rotated refresh token for adapter to include in response
            # The adapter (users.adapters.CustomHeadlessAdapter) will read this and
            # include it in the response body so the client can update their stored token.
            request._allauth_rotated_refresh_token = new_refresh_token

        # Return access token as required by AbstractTokenStrategy interface
        # AllAuth's adapter will include this in the Authorization header response
        return tokens.get("access")

    def get_session_key(self, request):
        """
        Get session key for token storage (not used for stateless JWT).

        JWT tokens are stateless and don't require session storage. This method
        returns None to indicate that session-based token storage is not used.

        Args:
            request: Django request object

        Returns:
            None: JWT tokens are stateless, no session key needed
        """
        return None

    def create_session_token(self, request):
        return None

    def lookup_session(self, session_token):
        return None
