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
    """Encode user ID for use in URLs."""
    return urlsafe_base64_encode(force_bytes(str(pk)))


def decode_uid(uid_str):
    """Decode UID from URL-safe base64."""
    try:
        return force_str(urlsafe_base64_decode(uid_str))
    except Exception:
        raise serializers.ValidationError("Invalid UID.")


# -------------------------
# Read-only user profile
# -------------------------
class ReadOnlyUserSerializer(serializers.ModelSerializer):
    """Expose full user profile in read-only mode."""

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
        if value in (None, ""):
            return None
        try:
            return validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_full_name(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        # 1. Apply the validated data to the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except IntegrityError:
            raise serializers.ValidationError({"email": "This email is already in use."})
            
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
        return value.strip()

    def validate_full_name(self, value):
        return value.strip()

    def validate_telephone_number(self, value):
        if value in (None, ""):
            return None
        try:
            return validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_password(self, value):
        try:
            password_validation.validate_password(value, self.instance)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        try:
            return User.objects.create_user(**validated_data)

        except IntegrityError as e:
            # Check which constraint failed
            err_msg = str(e).lower()
            if "telephone_number" in err_msg:
                raise serializers.ValidationError(
                    {"telephone_number": "A user with this phone number already exists."}
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
        fields = ('is_active', 'is_soft_deleted')
    
    def validate(self, attrs):
        # Prevent setting both to problematic states
        if attrs.get('is_active') and attrs.get('is_soft_deleted'):
            raise serializers.ValidationError(
                "Cannot activate a soft-deleted user. Restore first."
            )
        return attrs
    
    def update(self, instance, validated_data):
        # Let the model's save() method handle the soft-delete logic
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
        fields = (
            'is_staff', 
            'is_superuser', 
            'groups', 
            'user_permissions'
        )
    
    def validate(self, attrs):
        # Prevent removing superuser status from the last superuser
        if 'is_superuser' in attrs and attrs['is_superuser'] is False:
            instance = self.instance
            if instance and instance.is_superuser:
                # Count remaining superusers (excluding this one)
                remaining_superusers = User.objects.filter(
                    is_superuser=True
                ).exclude(user_id=instance.user_id).count()
                
                if remaining_superusers == 0:
                    raise serializers.ValidationError(
                        "Cannot remove superuser status from the last superuser account."
                    )
        
        return attrs
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        
        return instance