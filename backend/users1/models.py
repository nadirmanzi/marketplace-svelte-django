"""
User models for marketplace authentication and account management.

Defines a custom User model with UUID primary key, email-based authentication,
phone number support with validation, verification status tracking, soft-delete capability,
and session/password change audit trails. Extends Django's AbstractBaseUser and PermissionsMixin
for full authentication support.

Key features:
- Email is case-insensitive and unique.
- Phone numbers are normalized to E.164 format and unique among active users.
- Soft-delete support preserves data while marking users as deleted.
- Session versioning enables forced logouts on password change.
- Verification status tracked separately for email and phone.
"""

import uuid
from datetime import timedelta
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email

from .managers import UserManager
from users1.utils.validators import normalize_email, validate_and_normalize_phone


EMAIL_VERIFICATION_PENDING = "pending"
EMAIL_VERIFICATION_VERIFIED = "verified"

EMAIL_VERIFICATION_CHOICES = [
    (EMAIL_VERIFICATION_PENDING, "Pending"),
    (EMAIL_VERIFICATION_VERIFIED, "Verified"),
]

TELEPHONE_VERIFICATION_PENDING = "pending"
TELEPHONE_VERIFICATION_VERIFIED = "verified"
TELEPHONE_VERIFICATION_NONE = "no_number"

TELEPHONE_VERIFICATION_CHOICES = [
    (TELEPHONE_VERIFICATION_PENDING, "Pending"),
    (TELEPHONE_VERIFICATION_VERIFIED, "Verified"),
    (TELEPHONE_VERIFICATION_NONE, "No number"),
]


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model:
    - Email is case-insensitive and unique.
    - Phone is normalized and unique among active users.
    - Soft-delete support via is_soft_deleted and deleted_at.
    - Tracks password changes and session versioning.
    """

    # Identity
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        db_index=True,
        max_length=254,
    )

    first_name = models.CharField(max_length=75)
    last_name = models.CharField(max_length=75)
    telephone_number = models.CharField(
        max_length=32, unique=True, null=True, blank=True, db_index=True
    )

    # Verification status
    email_verification_status = models.CharField(
        max_length=16,
        choices=EMAIL_VERIFICATION_CHOICES,
        default=EMAIL_VERIFICATION_PENDING,
        db_index=True,
    )
    telephone_verification_status = models.CharField(
        max_length=16,
        choices=TELEPHONE_VERIFICATION_CHOICES,
        default=TELEPHONE_VERIFICATION_NONE,
        db_index=True,
    )

    # Account status
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_superuser = models.BooleanField(default=False, db_index=True)
    is_soft_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Preferences
    locale = models.CharField(max_length=10, null=True, blank=True)

    # Session tracking
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expires_in_days = models.PositiveIntegerField(default=90)
    session_version = models.IntegerField(default=0)

    # Account lockout tracking
    failed_login_attempts = models.PositiveIntegerField(default=0, db_index=True)
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "telephone_number"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def password_expired(self):
        if not self.password_changed_at:
            return True
        return timezone.now() > (
            self.password_changed_at + timedelta(days=self.password_expires_in_days)
        )

    @property
    def is_locked(self):
        """Check if account is currently locked due to failed login attempts."""
        if not self.locked_until:
            return False
        return timezone.now() < self.locked_until

    def reset_failed_attempts(self):
        """Reset failed login attempts and clear lockout status."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.locked_at = None
        self.save(update_fields=["failed_login_attempts", "locked_until", "locked_at"])

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["telephone_number"],
                condition=Q(is_soft_deleted=False),
                name="unique_active_telephone_number",
            )
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    def clean(self):
        """Validate email and phone format.

        Raises:
            ValidationError: If email is missing, invalid format, or phone number invalid.
        """
        # Email validation: check presence and format compliance
        if not self.email:
            raise ValidationError({"email": "Email is required."})
        validate_email(self.email)

        # Phone validation: parse and validate using phonenumbers library
        # for international format support and RFC compliance.
        # Ensures phone can be dialed internationally and matches actual number database.
        for field in ["telephone_number"]:
            number = getattr(self, field)
            # Call validate_and_normalize_phone purely for validation side-effect
            if number:
                try:
                    validate_and_normalize_phone(number)
                except ValidationError as e:
                    raise ValidationError({field: e.messages[0]})

    def save(self, *args, **kwargs):
        """Normalize fields and enforce soft-delete behavior.

        Performs:
        - Email domain lowercasing for case-insensitive matching.
        - Name whitespace stripping.
        - Phone number E.164 format normalization.
        - Soft-delete enforcement (deactivates user, sets deleted_at).
        """
        # Email normalization: convert domain to lowercase for case-insensitive matching.
        if self.email:
            self.email = normalize_email(self.email)

        # Name normalization: strip whitespace from first/last names.
        for field in ["first_name", "last_name"]:
            value = getattr(self, field)
            if value:
                setattr(self, field, value.strip())

        # Phone normalization: format to E.164 standard (+15551234567) for consistency.
        # E.164 is the international standard for phone storage and comparison.
        for field in ["telephone_number"]:
            number = getattr(self, field)
            if number:
                try:
                    normalized = validate_and_normalize_phone(number)
                    setattr(self, field, normalized)
                except ValidationError:
                    # If we can't parse it, leave it as-is (clean() will catch it later)
                    pass

        # Soft-delete enforcement: maintain invariants between is_soft_deleted and deleted_at/is_active.
        # This ensures soft-deleted users cannot login and maintains data consistency.
        if self.is_soft_deleted:
            # When marking user as soft-deleted:
            # 1. Record deletion timestamp (preserve audit trail of when deletion occurred)
            # 2. Set is_active=False (prevents login, excluded from active user queries)
            self.deleted_at = self.deleted_at or timezone.now()
            self.is_active = False
        else:
            # When un-deleting (is_soft_deleted=False):
            # Clear the deletion timestamp so user can be fully reactivated later.
            self.deleted_at = None

        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Hash password and update session tracking (does not save).

        Args:
            raw_password (str): The plaintext password to hash and store.

        Side Effects:
            - Hashes password using Django's password hashing algorithm.
            - Updates password_changed_at to current timestamp (forces re-authentication).
            - Increments session_version (invalidates all existing sessions for forced logout).
        """
        # Hash the password using Django's make_password utility for consistent hashing.
        self.password = make_password(raw_password)
        # Record timestamp to track when user changed password (useful for security audits).
        self.password_changed_at = timezone.now()
        # Increment session version to invalidate all active sessions, forcing re-login
        # when passwords change or suspicious activity is detected.
        self.session_version += 1


class FailedLoginAttempt(models.Model):
    """
    Track failed login attempts per IP address for account lockout protection.

    This model stores IP-based lockout information separately from user accounts
    to prevent brute force attacks from specific IP addresses across multiple accounts.
    """

    ip_address = models.CharField(
        max_length=45, unique=True, db_index=True
    )  # IPv6 max length
    failed_attempts = models.PositiveIntegerField(default=0, db_index=True)
    locked_until = models.DateTimeField(null=True, blank=True, db_index=True)
    last_attempt_at = models.DateTimeField(auto_now=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-last_attempt_at"]
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["locked_until"]),
            models.Index(fields=["last_attempt_at"]),
        ]

    def __str__(self):
        return (
            f"FailedLoginAttempt: {self.ip_address} ({self.failed_attempts} attempts)"
        )

    @property
    def is_locked(self):
        """Check if IP is currently locked."""
        if not self.locked_until:
            return False
        return timezone.now() < self.locked_until
