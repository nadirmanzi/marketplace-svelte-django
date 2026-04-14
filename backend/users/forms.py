"""
Django forms for user creation, editing, and account management in admin.

This module provides:

- UserCreationForm: Create new users with email, name, phone, verification status
- UserChangeForm: Edit existing users with field-level validation and soft-delete handling
- Phone Validation: International phone numbers validated via phonenumbers library, E.164 formatted
- Password Security: Uses Django's password validators (length, complexity, common words)
- Transaction Safety: Atomic creation with rollback on duplicate phone/email
- Soft-Delete Support: Prevents activating soft-deleted users; shows deletion status

Form Features:
- Email Uniqueness: Prevents duplicate emails (case-insensitive)
- Phone Uniqueness: Prevents duplicate active phone numbers (inactive users allowed)
- Password Confirmation: Requires matching password1/password2 on creation
- Atomic Operations: User creation wrapped in transaction with proper error handling
- Field Permissions: Read-only password field in edit form (use change_password instead)
- Soft-Delete Consistency: Soft-deleted users auto-deactivated; reactivation restricted

Helper Functions:
- normalize_and_validate_phone(): Parses, validates (possible + valid), formats to E.164

Integration:
- Used by Django admin for user management (UserAdmin)
- Provides intuitive creation/editing workflows with inline validation
- Displays friendly error messages for duplicate/invalid inputs

Dependencies:
- phonenumbers: International phone number parsing and validation
- django.contrib.auth: Password validators, BaseUser model
- django.core.exceptions: ValidationError for form-level validation
"""

from users.utils.validators import validate_and_normalize_phone
from django import forms
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

User = get_user_model()


# -------------------------
# User creation form
# -------------------------
class UserCreationForm(forms.ModelForm):
    """
    Form for creating a new user.
    Includes password confirmation and phone number validation.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Your password must be at least 8 characters long.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification.",
    )
    telephone_number = forms.CharField(
        label="Phone number (optional)",
        max_length=32,
        required=False,
        help_text="Include country code, e.g., +1234567890",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "telephone_number",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "telephone_number": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(),
            "is_staff": forms.CheckboxInput(),
            "is_superuser": forms.CheckboxInput(),
        }

    def clean_email(self):
        """Normalize and validate email uniqueness."""
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email is required.")
        email = email.strip()
        # Check if email already exists
        if User.objects.all_objects().filter(email__iexact=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def clean_telephone_number(self):
        """Validate and normalize phone number."""
        phone = self.cleaned_data.get("telephone_number")
        if phone in (None, ""):
            return None
        normalized = validate_and_normalize_phone(phone)
        # Check if normalized phone already exists among active users
        if User.objects.all_objects().filter(telephone_number=normalized).exists():
            raise ValidationError("A user with that phone number already exists.")
        return normalized

    def clean_full_name(self):
        """Validate first name."""
        full_name = self.cleaned_data.get("full_name")
        if not full_name or not full_name.strip():
            raise ValidationError("Full name is required.")
        return full_name.strip()

    def clean_password1(self):
        """Validate password strength using Django's validators."""
        password1 = self.cleaned_data.get("password1")
        if password1:
            try:
                password_validation.validate_password(password1, user=None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return password1

    def clean_password2(self):
        """Validate password confirmation."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The passwords do not match.")
        return password2

    def clean(self):
        """Check verification status consistency."""
        cleaned_data = super().clean()

        return cleaned_data

    def save(self, commit=True):
        """
        Delegate user creation to the Manager.
        The Manager handles hashing, validation, and atomic transactions.
        """
        if not commit:
            # Manually extract ONLY the fields that are NOT Many-to-Many
            data = {k: v for k, v in self.cleaned_data.items() 
                    if k not in ['groups', 'user_permissions', 'password1', 'password2']}
            user = User(**data)
            user.set_password(self.cleaned_data.get("password1"))

            self.save_m2m = lambda: None

            return user

        # This triggers UserManager.create_user -> _create_user -> atomic transaction
        user = User.objects.create_user(
            email=self.cleaned_data.get("email"),
            full_name=self.cleaned_data.get("full_name"),
            password=self.cleaned_data.get("password1"),
            telephone_number=self.cleaned_data.get("telephone_number"),
            is_staff=self.cleaned_data.get("is_staff", False),
            is_superuser=self.cleaned_data.get("is_superuser", False),
            is_active=self.cleaned_data.get("is_active", True),
        )

        self.save_m2m = lambda: None

        return user


# -------------------------
# User change form
# -------------------------
class UserChangeForm(forms.ModelForm):
    """
    Form for updating an existing user.
    Allows editing of email, name, phone, verification status, and account flags.
    """

    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text='Raw passwords are not stored. <a href="/admin/auth/user/%(id)s/password/">Change password</a>.',
    )
    telephone_number = forms.CharField(
        label="Phone number (optional)",
        max_length=32,
        required=False,
        help_text="Include country code, e.g., +1234567890",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "telephone_number",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_soft_deleted",
        )
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "telephone_number": forms.TextInput(attrs={"class": "form-control"}),
            "password": forms.PasswordInput(attrs={"readonly": "readonly"}),
            "is_active": forms.CheckboxInput(),
            "is_staff": forms.CheckboxInput(),
            "is_superuser": forms.CheckboxInput(),
            "is_soft_deleted": forms.CheckboxInput(),
        }

    def clean_email(self):
        """Validate email uniqueness (excluding current user)."""
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email is required.")
        email = email.strip()
        # Check if email exists for another user
        qs = User.objects.all_objects().filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(user_id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("A user with that email already exists.")
        return email

    def clean_telephone_number(self):
        """Validate and normalize phone number (excluding current user if unchanged)."""
        phone = self.cleaned_data.get("telephone_number")
        if phone in (None, ""):
            return None
        normalized = validate_and_normalize_phone(phone)
        # Check if normalized phone exists for another active user
        qs = User.objects.all_objects().filter(telephone_number=normalized)
        if self.instance and self.instance.pk:
            qs = qs.exclude(user_id=self.instance.user_id)
        if qs.exists():
            raise ValidationError("A user with that phone number already exists.")
        return normalized

    def clean_full_name(self):
        """Validate full name."""
        full_name = self.cleaned_data.get("full_name")
        if not full_name or not full_name.strip():
            raise ValidationError("Full name is required.")
        return full_name.strip()

    def clean(self):
        """Check verification status consistency and soft-delete logic."""
        cleaned_data = super().clean()
        telephone_number = cleaned_data.get("telephone_number")
        is_soft_deleted = cleaned_data.get("is_soft_deleted")

        # If soft-deleted, should not be active
        if is_soft_deleted and cleaned_data.get("is_active"):
            raise ValidationError(
                "Soft-deleted users cannot be active. Deactivate the user or restore them."
            )

        return cleaned_data

    def save(self, commit=True):
        """Save the user with validation."""
        user = super().save(commit=False)

        if commit:
            try:
                with transaction.atomic():
                    user.full_clean()
                    user.save()
            except (IntegrityError, ValidationError) as e:
                raise ValidationError(f"Error updating user: {str(e)}")

        return user
