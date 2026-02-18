"""
Serializers for user registration, profile updates, and account management.

This module provides DRF serializers for:
- ReadOnlyUserSerializer: Display user profile (all fields, read-only)
- RegisterSerializer: Create users with email, password, phone validation
- UpdateUserSerializer: Partial updates to user profile (names, phone)
- CustomTokenObtainPairSerializer: Login with custom tokens (session_version, email)
- Password Validation: Enforces Django's password validators

Serializer Responsibilities:
- Input Validation: Validates email uniqueness, phone format via phonenumbers library
- Data Normalization: Phone numbers converted to E.164 format for consistency
- Atomic Operations: User creation wrapped in transaction with password hashing
- Field Masking: Excludes password hashes, internal fields from responses

Phone Validation:
- Uses phonenumbers library to parse international formats
- Validates both "possible" and "valid" states (strict validation)
- Formats output to E.164 standard (e.g., "+15551234567")

Dependencies:
- rest_framework.serializers: Base serializer classes and validation
- rest_framework_simplejwt.serializers: JWT token serializers
- phonenumbers: International phone number handling
- django.contrib.auth: Password validators and User model
"""

from django.contrib.auth import password_validation, get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.utils.validators import validate_and_normalize_phone
from users.tokens import CustomRefreshToken

User = get_user_model()


def encode_uid(pk):
    """
    Encode a user PK to a URL-safe base64 string.

    Args:
        pk: User primary key (UUID or int).

    Returns:
        str: URL-safe base64 encoded string.

    Example:
        uid = encode_uid(user.user_id)  # -> "NjkwNGE2NWI..."
    """
    return urlsafe_base64_encode(force_bytes(str(pk)))


def decode_uid(uid_str):
    """
    Decode a URL-safe base64 UID back to a string.

    Args:
        uid_str (str): Base64 encoded UID from URL.

    Returns:
        str: Decoded user ID string.

    Raises:
        ValidationError: If uid_str is not valid base64.

    Example:
        user_id = decode_uid(uid)  # -> "6904a65b-565e-486b-af53-13beffb0b39b"
    """
    try:
        return force_str(urlsafe_base64_decode(uid_str))
    except Exception:
        raise serializers.ValidationError("Invalid UID.")


# -------------------------
# Read-only user profile
# -------------------------
class ReadOnlyUserSerializer(serializers.ModelSerializer):
    """Expose full user profile in read-only mode."""

    def __init__(self, *args, **kwargs):
        """
        Support optional field subsetting via 'fields' kwarg.

        Args:
            fields (list[str], optional): If provided, only these fields are included
                in the serialized output. Useful for lightweight responses.

        Example:
            ReadOnlyUserSerializer(user, fields=["user_id", "email"]).data
        """
        # Pop 'fields' before passing to super() to avoid unexpected kwarg error
        fields = kwargs.pop("fields", None)

        super().__init__(*args, **kwargs)

        # Drop unwanted fields if 'fields' specified
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = User
        fields = (
            "user_id",
            "email",
            "full_name",
            "telephone_number",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_soft_deleted",
            "soft_deleted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# -------------------------
# User update
# -------------------------
class UpdateUserSerializer(serializers.ModelSerializer):
    """Allow user to update email, name and phone number."""

    class Meta:
        model = User
        fields = ("email", "full_name", "telephone_number")

    def validate_telephone_number(self, value):
        """
        Normalize phone to E.164 or return None if blank.

        Args:
            value (str | None): Raw phone number input.

        Returns:
            str | None: E.164 formatted number or None.

        Raises:
            ValidationError: If number is not parseable or invalid.
        """
        if value in (None, ""):
            return None
        try:
            return validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_full_name(self, value):
        """Strip leading/trailing whitespace from full_name."""
        return value.strip()

    def update(self, instance, validated_data):
        """
        Apply validated fields to user and save atomically.

        Args:
            instance (User): Existing user to update.
            validated_data (dict): Fields to update (email, full_name, telephone_number).

        Returns:
            User: Updated user instance.

        Raises:
            ValidationError: On model validation failure or duplicate email.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()

                from config.logging import audit_log
                audit_log.info(
                    action="user.update",
                    message="User profile updated",
                    status="success",
                    source="users.serializers.UpdateUserSerializer",
                    target_user_id=str(instance.user_id),
                    extra={"updated_fields": list(validated_data.keys())}
                )
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except IntegrityError:
            raise serializers.ValidationError(
                {"email": "This email is already in use."}
            )

        return instance


# -------------------------
# Registration
# -------------------------
class RegisterSerializer(serializers.ModelSerializer):
    """Create a new user account with password and optional phone."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "full_name", "telephone_number", "password")

    def validate_email(self, value):
        """Strip whitespace from email input."""
        return value.strip()

    def validate_full_name(self, value):
        """Strip whitespace from full_name input."""
        return value.strip()

    def validate_telephone_number(self, value):
        """
        Normalize phone to E.164 or return None if blank.

        Args:
            value (str | None): Raw phone number input.

        Returns:
            str | None: E.164 formatted number or None.

        Raises:
            ValidationError: If number is not parseable or invalid.
        """
        if value in (None, ""):
            return None
        try:
            return validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_password(self, value):
        """
        Run Django's password validators against the provided password.

        Args:
            value (str): Plaintext password to validate.

        Returns:
            str: The validated password (unchanged).

        Raises:
            ValidationError: If password fails any validator (length, complexity, etc.).
        """
        try:
            password_validation.validate_password(value, self.instance)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        """
        Create a new user via UserManager.create_user.

        Args:
            validated_data (dict): Cleaned data from validate_* methods.

        Returns:
            User: Newly created user instance.

        Raises:
            ValidationError: On duplicate email/phone or model validation failure.

        Note:
            The post_save signal (assign_tokens_on_creation) fires after creation
            and attaches _auth_tokens to the user instance.
        """
        try:
            user = User.objects.create_user(**validated_data)

            from config.logging import audit_log
            audit_log.info(
                action="user.register",
                message="New user registered",
                status="success",
                source="users.serializers.RegisterSerializer",
                target_user_id=str(user.user_id),
            )
            return user

        except IntegrityError as e:
            # Inspect constraint name to return a field-specific error message
            err_msg = str(e).lower()
            if "telephone_number" in err_msg:
                raise serializers.ValidationError(
                    {
                        "telephone_number": "A user with this phone number already exists."
                    }
                )
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)


# -------------------------
# JWT Token Serializers
# -------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom login serializer that uses CustomRefreshToken.

    This ensures tokens include:
    - session_version: For forced logout on password change
    - email: For convenience (no DB lookup needed in frontend)

    Usage:
        Used by LoginView to generate tokens on login.
    """

    @classmethod
    def get_token(cls, user):
        """
        Override to use CustomRefreshToken instead of default RefreshToken.

        This method is called by TokenObtainPairSerializer.validate() when
        generating tokens during login.

        Args:
            user: User instance to generate tokens for

        Returns:
            CustomRefreshToken instance with custom claims
        """
        return CustomRefreshToken.for_user(user)


# -------------------------
# Admin usage
# -------------------------
class StaffUserActionSerializer(serializers.ModelSerializer):
    """
    Serializer for admin-only user actions (activation, deactivation, soft-delete).
    Should only be used with proper permission checks.
    """

    class Meta:
        model = User
        fields = ("is_active", "is_soft_deleted")

    def validate(self, attrs):
        """
        Guard against conflicting state: active + soft-deleted simultaneously.

        Raises:
            ValidationError: If is_active=True and is_soft_deleted=True are both set.
        """
        if attrs.get("is_active") and attrs.get("is_soft_deleted"):
            raise serializers.ValidationError(
                "Cannot activate a soft-deleted user. Restore first."
            )
        return attrs

    def update(self, instance, validated_data):
        """
        Apply is_active / is_soft_deleted changes atomically.

        The model's save() enforces soft-delete invariants (sets is_active=False,
        records soft_deleted_at) so no extra logic is needed here.

        Args:
            instance (User): User to update.
            validated_data (dict): Validated is_active / is_soft_deleted values.

        Returns:
            User: Updated user instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return instance


class AdminUserActionSerializer(serializers.ModelSerializer):
    """
    Serializer for superuser-only actions (modifying permissions, staff status).
    Should ONLY be used when request.user.is_superuser == True.
    """

    class Meta:
        model = User
        fields = ("is_staff", "is_superuser", "soft_deleted", "groups", "user_permissions")

    def validate(self, attrs):
        """
        Validation hook for admin actions.

        (Note: Last-superuser guard moved to UserManagementService).
        """
        return attrs

    def update(self, instance, validated_data):
        """
        Apply permission/staff/superuser changes atomically.

        Args:
            instance (User): User to update.
            validated_data (dict): Validated field values.

        Returns:
            User: Updated user instance.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return instance
