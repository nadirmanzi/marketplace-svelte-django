"""
Account lockout service for tracking and managing failed login attempts.

This service provides functionality to:
- Track failed login attempts per email address and IP address
- Lock accounts/IPs after threshold is reached
- Check lockout status before authentication
- Reset attempts on successful login
- Cleanup expired lockout records
"""

import logging
from typing import Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from ..models import FailedLoginAttempt
from config.logging import audit_log
from users.utils.network import get_client_ip
from django.db.models import F

logger = logging.getLogger(__name__)
User = get_user_model()


class AccountLockoutService:
    """Service for managing account lockout functionality."""

    @classmethod
    def _get_lockout_config(cls):
        """Get lockout configuration from settings."""
        return {
            "enabled": getattr(settings, "ACCOUNT_LOCKOUT_ENABLED", True),
            "threshold": getattr(settings, "ACCOUNT_LOCKOUT_THRESHOLD", 5),
            "duration_minutes": getattr(
                settings, "ACCOUNT_LOCKOUT_DURATION_MINUTES", 15
            ),
            "track_ip": getattr(settings, "ACCOUNT_LOCKOUT_TRACK_IP", True),
            "ip_threshold": getattr(settings, "ACCOUNT_LOCKOUT_IP_THRESHOLD", 10),
            "ip_duration_minutes": getattr(
                settings, "ACCOUNT_LOCKOUT_IP_DURATION_MINUTES", 30
            ),
        }

    @classmethod
    def check_account_locked(
        cls, email: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if an account is locked.

        Args:
            email: Email address to check

        Returns:
            (is_locked, locked_until_iso, retry_after_seconds)
            - is_locked: True if account is locked
            - locked_until_iso: ISO format datetime string or None
            - retry_after_seconds: Seconds until unlock or None
        """
        config = cls._get_lockout_config()
        if not config["enabled"]:
            return False, None, None

        try:
            user = User.objects.get(email__iexact=email)
            if user.is_locked:
                locked_until = user.locked_until
                retry_after = int((locked_until - timezone.now()).total_seconds())
                return True, locked_until.isoformat(), max(0, retry_after)
        except User.DoesNotExist:
            pass

        return False, None, None

    @classmethod
    def check_ip_locked(
        cls, ip_address: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if an IP address is locked.

        Args:
            ip_address: IP address to check

        Returns:
            (is_locked, locked_until_iso, retry_after_seconds)
        """
        config = cls._get_lockout_config()
        if not config["enabled"] or not config["track_ip"]:
            return False, None, None

        try:
            attempt = FailedLoginAttempt.objects.get(ip_address=ip_address)
            if attempt.is_locked:
                locked_until = attempt.locked_until
                retry_after = int((locked_until - timezone.now()).total_seconds())
                return True, locked_until.isoformat(), max(0, retry_after)
        except FailedLoginAttempt.DoesNotExist:
            pass

        return False, None, None

    @classmethod
    def record_failed_attempt(
        cls, email: str, ip_address: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Record a failed login attempt and lock account/IP if threshold reached.

        Args:
            email: Email address that failed
            ip_address: IP address of the failed attempt

        Returns:
            (was_locked, error_message)
            - was_locked: True if account/IP was just locked
            - error_message: Error message if locked, None otherwise
        """
        config = cls._get_lockout_config()
        if not config["enabled"]:
            return False, None

        was_locked = False
        error_message = None

        # Track per-email lockout
        try:
            user = User.objects.get(email__iexact=email)
            # Only increment if not already locked
            if not user.is_locked:
                # Use F() expression for atomic increment to prevent race conditions
                user.failed_login_attempts = F("failed_login_attempts") + 1
                user.save(update_fields=["failed_login_attempts"])

                # Refresh from DB to get the new value for threshold check
                user.refresh_from_db()

                # Check if threshold reached
                if user.failed_login_attempts >= config["threshold"]:
                    cls.lock_account(email, config["duration_minutes"])
                    was_locked = True
                    error_message = "Account is temporarily locked due to too many failed login attempts."

                    audit_log.warning(
                        action="account.locked",
                        message=f"Account locked after {user.failed_login_attempts} failed attempts",
                        status="locked",
                        source="users.services.account_lockout_service.AccountLockoutService",
                        extra={
                            "email": email,
                            "failed_attempts": user.failed_login_attempts,
                            "locked_until": user.locked_until.isoformat()
                            if user.locked_until
                            else None,
                        },
                    )
        except User.DoesNotExist:
            # User doesn't exist - still track IP
            pass

        # Track per-IP lockout
        if config["track_ip"]:
            attempt, created = FailedLoginAttempt.objects.get_or_create(
                ip_address=ip_address, defaults={"failed_attempts": 0}
            )

            # Only increment if not already locked
            if not attempt.is_locked:
                # Use F() expression for atomic increment
                attempt.failed_attempts = F("failed_attempts") + 1
                attempt.last_attempt_at = timezone.now()
                attempt.save(update_fields=["failed_attempts", "last_attempt_at"])

                # Refresh from DB to check threshold
                attempt.refresh_from_db()

                # Check if IP threshold reached
                if attempt.failed_attempts >= config["ip_threshold"]:
                    cls.lock_ip(ip_address, config["ip_duration_minutes"])
                    was_locked = True
                    if not error_message:
                        error_message = (
                            "Too many failed login attempts from this IP address."
                        )

                    audit_log.warning(
                        action="ip.locked",
                        message=f"IP locked after {attempt.failed_attempts} failed attempts",
                        status="locked",
                        source="users.services.account_lockout_service.AccountLockoutService",
                        extra={
                            "ip_address": ip_address,
                            "failed_attempts": attempt.failed_attempts,
                            "locked_until": attempt.locked_until.isoformat()
                            if attempt.locked_until
                            else None,
                        },
                    )

        return was_locked, error_message

    @classmethod
    def lock_account(cls, email: str, duration_minutes: int):
        """
        Lock an account for the specified duration.

        Args:
            email: Email address to lock
            duration_minutes: Lockout duration in minutes
        """
        try:
            user = User.objects.get(email__iexact=email)
            user.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
            user.locked_at = timezone.now()
            user.save(update_fields=["locked_until", "locked_at"])
            logger.info(f"Account locked: {email} until {user.locked_until}")
        except User.DoesNotExist:
            logger.warning(f"Attempted to lock non-existent account: {email}")

    @classmethod
    def lock_ip(cls, ip_address: str, duration_minutes: int):
        """
        Lock an IP address for the specified duration.

        Args:
            ip_address: IP address to lock
            duration_minutes: Lockout duration in minutes
        """
        attempt, created = FailedLoginAttempt.objects.get_or_create(
            ip_address=ip_address, defaults={"failed_attempts": 0}
        )
        attempt.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        attempt.last_attempt_at = timezone.now()
        attempt.save(update_fields=["locked_until", "last_attempt_at"])
        logger.info(f"IP locked: {ip_address} until {attempt.locked_until}")

    @classmethod
    def reset_account_attempts(cls, email: str):
        """
        Reset failed login attempts for an account (called on successful login).

        Args:
            email: Email address to reset
        """
        try:
            user = User.objects.get(email__iexact=email)
            if user.failed_login_attempts > 0 or user.is_locked:
                user.reset_failed_attempts()
                logger.info(f"Reset failed attempts for account: {email}")
        except User.DoesNotExist:
            pass

    @classmethod
    def reset_ip_attempts(cls, ip_address: str):
        """
        Reset failed login attempts for an IP address (called on successful login).

        Args:
            ip_address: IP address to reset
        """
        try:
            attempt = FailedLoginAttempt.objects.get(ip_address=ip_address)
            attempt.failed_attempts = 0
            attempt.locked_until = None
            attempt.last_attempt_at = timezone.now()
            attempt.save(
                update_fields=["failed_attempts", "locked_until", "last_attempt_at"]
            )
            logger.info(f"Reset failed attempts for IP: {ip_address}")
        except FailedLoginAttempt.DoesNotExist:
            pass

    @classmethod
    def unlock_account(cls, email: str) -> bool:
        """
        Manually unlock an account (admin action).

        Args:
            email: Email address to unlock

        Returns:
            True if account was unlocked, False if not found or not locked
        """
        try:
            user = User.objects.get(email__iexact=email)
            if user.is_locked:
                user.reset_failed_attempts()
                audit_log.info(
                    action="account.unlocked",
                    message="Account manually unlocked by admin",
                    status="unlocked",
                    source="users.services.account_lockout_service.AccountLockoutService",
                    extra={"email": email, "unlocked_by": "admin"},
                )
                return True
        except User.DoesNotExist:
            pass
        return False

    @classmethod
    def unlock_ip(cls, ip_address: str) -> bool:
        """
        Manually unlock an IP address (admin action).

        Args:
            ip_address: IP address to unlock

        Returns:
            True if IP was unlocked, False if not found or not locked
        """
        try:
            attempt = FailedLoginAttempt.objects.get(ip_address=ip_address)
            if attempt.is_locked:
                attempt.failed_attempts = 0
                attempt.locked_until = None
                attempt.save(update_fields=["failed_attempts", "locked_until"])
                audit_log.info(
                    action="ip.unlocked",
                    message="IP manually unlocked by admin",
                    status="unlocked",
                    source="users.services.account_lockout_service.AccountLockoutService",
                    extra={"ip_address": ip_address, "unlocked_by": "admin"},
                )
                return True
        except FailedLoginAttempt.DoesNotExist:
            pass
        return False

    @classmethod
    def cleanup_expired_locks(cls):
        """
        Cleanup expired lockout records (IP records older than 24 hours).

        This should be called periodically (e.g., via cron or Celery task).
        """
        # Cleanup expired IP lockout records (older than 24 hours)
        cutoff = timezone.now() - timedelta(hours=24)
        deleted_count = FailedLoginAttempt.objects.filter(
            last_attempt_at__lt=cutoff
        ).delete()[0]

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired IP lockout records")

        return deleted_count

    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Extract client IP address from request, handling proxy headers.

        Delegates to centralized network utility.

        Args:
            request: Django request object

        Returns:
            IP address string
        """
        return get_client_ip(request)
