"""Utility helpers for the `users` app.

Expose small helper functions and error classes used by services and views.
Keep utilities pure and testable (no HTTP imports).
"""

from .token_utils import is_token_expired, make_datetime_aware, get_current_utc
from .exception_handlers import (
    UserAuthError,
    InvalidCredentialsError,
    AccountDeactivatedError,
    AccountDeletedError,
)
from .permission_utils import can_access_user, can_reactivate_user

__all__ = [
    "is_token_expired",
    "make_datetime_aware",
    "get_current_utc",
    "UserAuthError",
    "InvalidCredentialsError",
    "AccountDeactivatedError",
    "AccountDeletedError",
    "can_access_user",
    "can_reactivate_user",
]
