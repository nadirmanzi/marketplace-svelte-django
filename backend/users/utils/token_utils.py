"""Token and datetime utility helpers.

Small helpers used by token cleanup and verification logic. Kept small
and timezone-aware to avoid datetime comparison bugs.
"""
from datetime import datetime, timezone as _timezone
from typing import Optional


def get_current_utc() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(_timezone.utc)


def make_datetime_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (assume UTC if naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_timezone.utc)
    return dt


def is_token_expired(expires_at: Optional[datetime]) -> bool:
    """Return True if `expires_at` is None or in the past relative to UTC."""
    if expires_at is None:
        return True
    aware = make_datetime_aware(expires_at)
    return aware <= get_current_utc()
