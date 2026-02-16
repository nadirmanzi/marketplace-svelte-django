"""
Custom manager for User model with soft-delete filtering and creation helpers.

This module provides UserManager which extends BaseUserManager to implement:

- Soft-Delete Filtering: Default queryset excludes soft-deleted users; separate methods
  to access all_objects() and deleted() users
- Email Normalization: Converts domain to lowercase for case-insensitive matching
- Phone Validation: Validates via phonenumbers library and formats to E.164 standard
- User Creation: create_user() and create_superuser() with defaults for verification status

Default Queryset Behavior:
- objects.all(): Returns only active (not soft-deleted) users
- objects.all_objects(): Returns all users including soft-deleted
- objects.deleted(): Returns only soft-deleted users

This separation improves query safety by default-excluding deleted users, while providing
explicit access when needed for admin/audit purposes.

Creation Helpers:
- create_user(email, ...): Creates regular user with is_active=True, pending verification
- create_superuser(...): Creates admin with is_staff=is_superuser=True, verified status

Dependencies:
- phonenumbers: International phone number parsing and validation
- django.contrib.auth.BaseUserManager: Base manager class
"""
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from django.contrib.auth.base_user import BaseUserManager

from users.utils.validators import normalize_email, validate_and_normalize_phone


class UserManager(BaseUserManager):
    """Manager for User model with soft-delete filtering and creation helpers."""

    use_in_migrations = True

    def get_queryset(self):
        """Return default queryset excluding soft-deleted users.

        By default, soft-deleted users (is_soft_deleted=True) are filtered out.
        Use all_objects() to access all users including soft-deleted ones.

        Returns:
            QuerySet of active (non-soft-deleted) User objects

        Design:
            - Prevents accidental queries returning deleted users
            - Improves safety by hiding deleted accounts by default
            - Admin/staff can use all_objects() when needed

        Examples:
            User.objects.all()  # Returns only active users
            User.objects.all_objects()  # Returns all users including deleted
            User.objects.soft_deleted()  # Returns only soft-deleted users
        """
        return super().get_queryset().filter(is_soft_deleted=False)

    def all_objects(self):
        """Return queryset of ALL users including soft-deleted ones.

        Use when you need to access soft-deleted users for recovery, audit, or admin purposes.

        Returns:
            QuerySet of all User objects (deleted and active)

        Use Cases:
            - Admin recovery/restoration workflows
            - Data export/audit trails
            - Checking if email/phone was previously used
            - Finding soft-deleted users for reactivation

        Examples:
            User.objects.all_objects()  # All users
            User.objects.all_objects().filter(is_soft_deleted=True)  # Only deleted
            User.objects.all_objects().filter(email='john@example.com')  # By email, including deleted
        """
        return super().get_queryset()

    def soft_deleted(self):
        """Return queryset of only soft-deleted users.

        Convenience method for finding and auditing deleted accounts.

        Returns:
            QuerySet of soft-deleted User objects (is_soft_deleted=True)

        Use Cases:
            - Find recently deleted accounts
            - Recovery workflows
            - Audit and compliance reports
            - Verify deletion timestamp

        Examples:
            User.objects.deleted().count()  # Number of deleted users
            User.objects.deleted().filter(deleted_at__gte=cutoff_date)  # Recently deleted
        """
        return self.all_objects().filter(is_soft_deleted=True)

    def _create_user(
        self,
        email,
        full_name,
        password=None,
        telephone_number=None,
        **extra_fields,
    ):
        email = normalize_email(email)
        telephone_number = (
            validate_and_normalize_phone(telephone_number) if telephone_number else None
        )

        try:
            with transaction.atomic(using=self._db):
                user = self.model(
                    email=email,
                    full_name=full_name.strip(),
                    telephone_number=telephone_number,
                    **extra_fields,
                )
                if password:
                    user.set_password(password)
                
                # 1. Validate fields (Logic level)
                user.full_clean() 
                
                # 2. Persist (Database level)
                user.save(using=self._db)
                return user
                
        except (ValidationError, IntegrityError) as e:
            # Re-raise so the View/Serializer can catch it and return a 400
            raise e

    def create_user(
        self,
        email,
        full_name,
        password=None,
        telephone_number=None,
        **extra_fields,
    ):
        """Create a regular (non-staff) user with verification status defaults.

        Args:
            email (str): User's email (required, will be normalized and checked for uniqueness)
            full_name (str): User's full name (will be stripped)
            password (str, optional): Plaintext password (will be hashed via set_password)
            telephone_number (str, optional): Phone number (will be validated and normalized to E.164)
            **extra_fields: Additional fields to set on user object

        Returns:
            User: Created and saved user object with is_active=True, is_staff=False

        Default Attributes Set:
            is_active: True (user can login immediately)
            is_staff: False (not a staff member)
            is_superuser: False (not an admin)

        Raises:
            ValidationError: If email/phone invalid or violates constraints
            IntegrityError: If unique constraints violated (duplicate email/phone)

        Use Cases:
            - User registration via API (POST /users/)
            - Admin creates user account in Django admin
            - Bulk user imports during onboarding

        Example:
            user = User.objects.create_user(
                email='john@example.com',
                full_name='John',
                last_name='Doe',
                password='secure_password_123',
                telephone_number='+15551234567'
            )
        """
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(
            email, full_name, password, telephone_number, **extra_fields
        )

    def create_superuser(
        self,
        email,
        full_name,
        password=None,
        telephone_number=None,
        **extra_fields,
    ):
        """Create a superuser (admin) with full permissions and pre-verified status.

        Args:
            email (str): Admin's email (required, unique)
            full_name (str): Admin's full name
            password (str, optional): Plaintext password (will be hashed)
            telephone_number (str, optional): Phone number (optional for admin)
            **extra_fields: Additional fields to set on user object

        Returns:
            User: Created and saved superuser object with full permissions

        Default Attributes Set:
            is_staff: True (can access admin interface)
            is_superuser: True (has all permissions)
            is_active: True (can login immediately)

        Raises:
            ValueError: If is_staff or is_superuser not True (enforces admin permissions)
            ValidationError: If email/phone invalid
            IntegrityError: If unique constraints violated

        Use Cases:
            - Initial Django admin creation (./manage.py createsuperuser)
            - Administrative user provisioning
            - Trusted admin account setup

        Safety:
            - Requires explicit is_staff=True and is_superuser=True
            - Raises ValueError if permissions accidentally removed
            - Pre-verified status for admins (no verification workflow)

        Example:
            admin = User.objects.create_superuser(
                email='admin@example.com',
                full_name='Admin',
                last_name='User',
                password='strong_password_123'
            )
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields["is_staff"]:
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(
            email, full_name, password, telephone_number, **extra_fields
        )
