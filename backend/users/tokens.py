"""
Custom JWT token classes for minimal, efficient token payloads.

This module implements custom token classes extending SimpleJWT to provide:

- Minimal Claims: Only user_id and email in tokens (vs Django's default 50+ user fields)
- Zero DB Lookups: CustomAccessToken.for_user() and access_token property avoid DB queries
- Performance: Reduces token size, parsing overhead, and database pressure
- Security: Smaller payload surface area reduces data exposure

Token Classes:
- CustomAccessToken: Short-lived token (10min) with user_id + email claims only
- CustomRefreshToken: Long-lived token (1 day) with user_id + email + rotation support

Access Token Generation Flow:
1. On login: RefreshToken(user).access_token -> built from payload (no DB query)
2. On refresh: TokenRefreshSerializer -> builds new access token from refresh payload
3. Both paths use CustomAccessToken.for_user() which only adds minimal claims

Key Features:
- UUID Support: Converts UUID user_id to string for JSON serialization
- Email Caching: Refresh token stores email on payload so access tokens are created
  without database lookups (critical for performance with rotating refresh tokens)
- Inheritance: Extends SimpleJWT's AccessToken and RefreshToken for compatibility

Dependencies:
- rest_framework_simplejwt: Base token classes, JWT encoding/decoding
- User model: Must have email field and USER_ID_FIELD setting (typically 'user_id' for UUID)
"""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings

User = get_user_model()


class CustomAccessToken(AccessToken):
    """Short-lived JWT token with minimal claims for API request authentication.
    
    Design:
        - Payload contains only user_id and email (vs SimpleJWT default which adds 10+ fields)
        - Lifetime: 10 minutes (configurable via SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
        - Used in Authorization header: Authorization: Bearer <token>
        - Validated by JWTAuthentication backend on each request
    
    Attributes:
        user_id (str): UUID of authenticated user (converted to string for JSON)
        email (str): User's email address (for convenience in frontend)
        iat (int): Issued at timestamp (automatic)
        exp (int): Expiration timestamp (automatic)
        token_type (str): 'access' (automatic)
    
    Benefits:
        - Smaller payload = faster parsing and transmission
        - Less sensitive data in token (no full user object)
        - Reduced attack surface if token is intercepted
        - Better performance with large numbers of requests
    
    Usage:
        Created by CustomRefreshToken.access_token property (no DB lookup)
        Or created directly via CustomAccessToken.for_user(user)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def for_user(cls, user):
        """Create access token for user with minimal claims.
        
        Args:
            user: User object with user_id (UUID) and email fields
        
        Returns:
            CustomAccessToken instance with user_id and email in payload
        
        Notes:
            - Does NOT perform database lookup (safe to call in hot paths)
            - UUID user_id is converted to string for JSON serialization
            - Called by: login action, token_refresh action, access_token property
        """
        token = cls()
        # Convert UUID to string for JSON serialization
        user_id = getattr(user, jwt_settings.USER_ID_FIELD)
        token[jwt_settings.USER_ID_FIELD] = str(user_id)
        # Add email claim
        token["email"] = user.email
        # Add session version claim
        token["session_version"] = getattr(user, "session_version", 0)
        return token


class CustomRefreshToken(SimpleJWTRefreshToken):
    """Long-lived JWT token used to obtain new access tokens and refresh tokens.
    
    Design:
        - Payload contains user_id, email, and standard JWT claims
        - Lifetime: 1 day (configurable via SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])
        - Stored in OutstandingToken table for audit/revocation tracking
        - Can be rotated: old token blacklisted, new one issued on refresh
    
    Attributes:
        user_id (str): UUID of authenticated user
        email (str): User's email (cached from login for access_token generation)
        iat (int): Issued at timestamp
        exp (int): Expiration timestamp
        iss, aud, typ, jti: JWT metadata (automatic)
    
    Rotation Mechanism (if ROTATE_REFRESH_TOKENS enabled):
        - On token_refresh action, old token moved to BlacklistedToken table
        - New token returned to client
        - Prevents token reuse attacks (compromised old token can't be used)
    
    Key Feature - Zero DB Access:
        - access_token property builds AccessToken from payload without DB query
        - Email is cached on refresh token to enable this (avoids N+1 with rotation)
        - Critical performance improvement: token_refresh doesn't hit database
    
    Usage Flow:
        1. login action: CustomRefreshToken.for_user(user) -> stores email on payload
        2. Client uses refresh token in token_refresh action
        3. token_refresh builds new access token from refresh.access_token property
        4. access_token property creates CustomAccessToken from cached email (no DB)
    """
    @classmethod
    def for_user(cls, user):
        """Create refresh token for user, caching email on payload for access_token generation.

        Args:
            user: User object with user_id (UUID) and email fields
        
        Returns:
            CustomRefreshToken instance with user_id and email in payload
        
        Side Effect:
            Email is stored on payload to avoid DB lookup when creating access tokens
        
        Notes:
            - Does NOT perform database lookup (called during login)
            - Email caching is critical for performance with token rotation
            - Enables access_token property to work without DB access
        """
        token = super().for_user(user)
        # ensure email is included in refresh payload for later access-token creation
        token["email"] = user.email
        # Add session version claim
        token["session_version"] = getattr(user, "session_version", 0)
        return token

    @property
    def access_token(self):
        """Build new CustomAccessToken from refresh token payload (zero database lookups).
        
        Returns:
            CustomAccessToken instance with user_id and email from refresh token
        
        Raises:
            ValueError: If user_id missing from refresh payload (malformed token)
        
        Performance:
            - O(1) operation: reads payload, creates token, returns
            - No database queries (cached email on refresh payload)
            - Safe to call frequently during token_refresh action
        
        This is the key optimization: refresh token stores email on payload,
        allowing access token creation without fetching user from database.
        Critical for performance when refresh happens multiple times per session.
        """
        # Extract user_id and email from refresh token payload (already validated on issue).
        # These were stored on refresh token creation to avoid DB lookups here.
        user_id = self.payload.get(jwt_settings.USER_ID_FIELD)
        email = self.payload.get("email")
        session_version = self.payload.get("session_version", 0)
        
        # Defensive check: user_id must always be present (indicates valid token).
        if not user_id:
            raise ValueError("Refresh token does not contain user_id")

        # Create new access token with minimal claims (only user_id and email).
        # No database query needed: all data comes from refresh payload.
        access = CustomAccessToken()
        access[jwt_settings.USER_ID_FIELD] = user_id
        if email:
            access["email"] = email
        access["session_version"] = session_version
        
        return access
