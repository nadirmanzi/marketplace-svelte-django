"""Exception types and helpers for user/auth errors.

These small exceptions provide semantic error types services can raise and
views can catch to produce consistent HTTP responses.
"""
from typing import Optional


class UserAuthError(Exception):
    """Base class for authentication-related errors."""


class InvalidCredentialsError(UserAuthError):
    """Raised when email/password do not match any user."""


class AccountDeactivatedError(UserAuthError):
    """Raised when an account is deactivated and cannot login."""


class AccountDeletedError(UserAuthError):
    """Raised when an account has been soft-deleted."""
