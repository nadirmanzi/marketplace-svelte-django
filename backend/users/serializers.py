"""
Serializers for user registration, profile updates, and account management.

This module provides DRF serializers for:
- ReadOnlyUserSerializer: Display user profile (all fields, read-only)
- RegisterSerializer: Create users with email, password, phone validation
- UpdateUserSerializer: Partial updates to user profile (names, phone)
- CustomTokenObtainPairSerializer: Login with custom tokens (session_version, email)
- StaffUserActionSerializer: Base for staff-level actions
- AdminUserActionSerializer: Base for superuser-level actions
- ChangePasswordSerializer: Authenticated password changes
- Password Validation: Enforces Django's password validators
"""

from django.contrib.auth import password_validation, get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from users.utils.validators import validate_and_normalize_phone
from users.tokens import CustomRefreshToken

User = get_user_model()


def encode_uid(pk):
    """
    Encode a user PK to a URL-safe base64 string.
    """
    return urlsafe_base64_encode(force_bytes(str(pk)))


def decode_uid(uid_str):
    """
    Decode a URL-safe base64 UID back to a string.
    """
    try:
        return force_str(urlsafe_base64_decode(uid_str))
    except Exception:
        raise serializers.ValidationError("Invalid UID.")


class UserUpdateMixin:
    """
    Mixin to provide a standardized atomic update with full_clean validation.
    """
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        try:
            with transaction.atomic():
                instance.full_clean()
                instance.save()
        except DjangoValidationError as e:
            # Handle both dict and list style validation errors
            if hasattr(e, 'message_dict'):
                raise serializers.ValidationError(e.message_dict)
            raise serializers.ValidationError(str(e))
        return instance


# -------------------------
# Embedded user (for resources like products)
# -------------------------
class EmbeddedUserSerializer(serializers.ModelSerializer):
    """Minimal user representation embedded in resource responses (e.g. products)."""

    class Meta:
        model = User
        fields = ("user_id", "full_name", "email")
        read_only_fields = fields


# -------------------------
# /me endpoint (non-sensitive)
# -------------------------
class MeSerializer(serializers.ModelSerializer):
    """Non-sensitive user profile for the /me endpoint."""

    password_expires_in_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "email",
            "full_name",
            "telephone_number",
            "password_changed_at",
            "password_expires_in_days",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# -------------------------
# Full user object (staff/admin only, /management/{pk}/)
# -------------------------
class FullUserSerializer(serializers.ModelSerializer):
    """Complete user representation for staff/admin detail views."""

    password_expired = serializers.BooleanField(read_only=True)

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
            "password_changed_at",
            "password_expires_in_days",
            "password_expired",
            "session_version",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# -------------------------
# Read-only user profile (legacy — used for management action responses with dynamic fields)
# -------------------------
class ReadOnlyUserSerializer(serializers.ModelSerializer):
    """Expose user profile in read-only mode with optional dynamic field selection."""

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)

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
            "password_changed_at",
            "password_expired",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# -------------------------
# Registration serializer
# -------------------------
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "telephone_number", "password")

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required.")
        value = value.strip().lower()
        if User.objects.all_objects().filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_telephone_number(self, value):
        if not value:
            return None
        try:
            normalized_phone = validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.messages[0]))

        if User.objects.all_objects().filter(telephone_number=normalized_phone).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return normalized_phone

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
                return user
        except IntegrityError:
            raise serializers.ValidationError("Could not create user. Database integrity error.")


# -------------------------
# Profile update serializer
# -------------------------
class UpdateUserSerializer(UserUpdateMixin, serializers.ModelSerializer):
    """
    Serializer for updating existing user profiles.
    """
    class Meta:
        model = User
        fields = ("full_name", "telephone_number")

    def validate_telephone_number(self, value):
        if not value:
            return None
        try:
            normalized_phone = validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.messages[0]))

        if (
            User.objects.all_objects()
            .exclude(pk=self.instance.pk)
            .filter(telephone_number=normalized_phone)
            .exists()
        ):
            raise serializers.ValidationError("Another user already has this phone number.")
        
        return normalized_phone


# -------------------------
# JWT Login Serializer
# -------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom login serializer that uses CustomRefreshToken.
    """
    @classmethod
    def get_token(cls, user):
        return CustomRefreshToken.for_user(user)


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom refresh serializer that uses CustomRefreshToken to ensure 
    zero-DB access token generation and preserves custom claims.
    """
    def validate(self, attrs):
        from users.tokens import CustomRefreshToken
        from rest_framework_simplejwt.settings import api_settings

        refresh = CustomRefreshToken(attrs["refresh"])

        data = {"access": str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()
            refresh.set_iat()

            data["refresh"] = str(refresh)

        return data


# -------------------------
# Admin management serializers
# -------------------------
class StaffUserActionSerializer(serializers.ModelSerializer):
    """
    Serializer for staff-only actions (deactivate, activate, soft-delete).
    """
    class Meta:
        model = User
        fields = ("user_id", "email", "full_name", "is_active", "is_soft_deleted")
        read_only_fields = fields


class AdminUserActionSerializer(UserUpdateMixin, serializers.ModelSerializer):
    """
    Serializer for superuser-only actions (modifying permissions, staff status).
    """
    class Meta:
        model = User
        fields = ("is_staff", "is_superuser", "is_soft_deleted", "groups", "user_permissions")


# -------------------------
# Password Change Serializer
# -------------------------
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for authenticated password changes.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] == data['old_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old one."})
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        try:
            password_validation.validate_password(data['new_password'], self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return data
