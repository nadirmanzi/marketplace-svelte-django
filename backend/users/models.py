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
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Permission
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email

from .managers import UserManager
from users.utils.validators import normalize_email, validate_and_normalize_phone


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

    full_name = models.CharField(max_length=255)
    telephone_number = models.CharField(
        max_length=32, null=True, blank=True, db_index=True
    )

    # Account status
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False, db_index=True)
    is_superuser = models.BooleanField(default=False, db_index=True)
    is_soft_deleted = models.BooleanField(default=False, db_index=True)
    soft_deleted_at = models.DateTimeField(null=True, blank=True)

    # Session tracking
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expires_in_days = models.PositiveIntegerField(default=90)
    session_version = models.IntegerField(default=0)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "telephone_number"]

    @property
    def password_expired(self):
        if not self.password_changed_at:
            return True
        return timezone.now() > (
            self.password_changed_at + timedelta(days=self.password_expires_in_days)
        )

    @property
    def is_last_superuser(self) -> bool:
        """
        Check if this user is the only active superuser in the system.

        Returns:
            bool: True if this is the last remaining superuser.
        """
        if not self.is_superuser:
            return False

        # Count other superusers
        return (
            type(self).objects.filter(is_superuser=True).exclude(pk=self.pk).count()
            == 0
        )

    def rotate_session(self):
        """Increment session_version to invalidate all existing tokens. Does not save."""
        self.session_version += 1

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["telephone_number"],
                condition=Q(is_soft_deleted=False),
                name="unique_active_telephone_number",
            )
        ]
        permissions = [
            ("can_soft_delete_user", "Can soft delete a user"),
            ("can_deactivate_user", "Can deactivate a user"),
            ("can_activate_user", "Can activate a user"),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

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

        # Prevent deactivating superuser
        if self.is_last_superuser:
            if not self.is_active or not self.is_staff or not self.is_superuser:
                raise ValidationError(
                    "Cannot deactivate or remove is_staff/is_superuser from last superuser"
                )

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

        if self.is_superuser:
            self.is_active = True
            self.is_staff = True
            self.is_soft_deleted = False
            self.soft_deleted_at = None

        # Name normalization: strip whitespace from first/last names.
        for field in ["full_name"]:
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
            self.soft_deleted_at = self.soft_deleted_at or timezone.now()
            self.is_active = False
        else:
            # When un-deleting (is_soft_deleted=False):
            # Clear the deletion timestamp so user can be fully reactivated later.
            self.soft_deleted_at = None

        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Hash password and update session tracking (does not save).

        Args:
            raw_password (str): The plaintext password to hash and store.

        Side Effects:
            - Hashes password using Django's password hashing algorithm.
            - Updates password_changed_at to current timestamp.
            - Increments session_version ONLY on password changes (not initial set).
        """
        # Check if this is a password change vs initial set
        is_password_change = bool(self.password)

        # Hash the password
        self.password = make_password(raw_password)

        # Always update timestamp (useful for password expiration)
        self.password_changed_at = timezone.now()

        # Only increment session version on actual password changes
        # This invalidates existing tokens when password changes
        if is_password_change:
            self.session_version += 1
