"""
Serializers for user registration, profile updates, and account management.

This module provides DRF serializers for:
- ReadOnlyUserSerializer: Display user profile (all fields, read-only)
- RegisterSerializer: Create users with email, password, phone validation
- UpdateUserSerializer: Partial updates to user profile (names, phone)
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

Helper Functions:
- normalize_phone(): Parses, validates, formats phone to E.164; raises ValidationError on failure

Dependencies:
- rest_framework.serializers: Base serializer classes and validation
- phonenumbers: International phone number handling
- django.contrib.auth: Password validators and User model
"""

from django.contrib.auth import password_validation, get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import serializers


from users1.utils.validators import validate_and_normalize_phone

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

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "email",
            "first_name",
            "last_name",
            "telephone_number",
            "email_verification_status",
            "telephone_verification_status",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_soft_deleted",
            "deleted_at",
            "created_at",
            "updated_at",
            "full_name",
        )
        read_only_fields = fields


# -------------------------
# User update
# -------------------------
class UpdateUserSerializer(serializers.ModelSerializer):
    """Allow user to update email, name and phone number."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "telephone_number")

    def validate_telephone_number(self, value):
        if value in (None, ""):
            return None
        try:
            return validate_and_normalize_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages[0])

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def update(self, instance, validated_data):
        # Check if email is being changed
        old_email = instance.email
        new_email = validated_data.get("email", old_email)
        email_changed = old_email.lower() != new_email.lower()

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        # If email changed, reset verification status
        if email_changed:
            instance.email_verification_status = "pending"

        instance.full_clean()
        instance.save()

        # Send new verification email if email changed
        if email_changed:
            try:
                from .services.email_service import EmailVerificationService

                token = EmailVerificationService.generate_token(instance)
                request = self.context.get("request")
                if request:
                    base_url = request.build_absolute_uri("/")
                else:
                    from django.conf import settings as django_settings

                    base_url = getattr(
                        django_settings, "FRONTEND_URL", "http://localhost:5173/"
                    )
                verification_url = f"{base_url.rstrip('/')}/verify-email?token={token}"
                EmailVerificationService.send_verification_email(
                    instance, verification_url
                )
            except Exception:
                import logging

                logging.getLogger(__name__).warning(
                    "Failed to send verification email to %s after email change",
                    instance.email,
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
        fields = ("email", "first_name", "last_name", "telephone_number", "password")

    def validate_email(self, value):
        return value.strip()

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
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
        password = validated_data.pop("password")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data.get("email"),
                    first_name=validated_data.get("first_name"),
                    last_name=validated_data.get("last_name"),
                    password=password,
                    telephone_number=validated_data.get("telephone_number"),
                )

                # Create Allauth EmailAddress to allow login
                from allauth.account.models import EmailAddress

                # Check if email is already verified (e.g. by superuser creation logic, though this is regular create)
                # But here we default to False unless we want to auto-verify admin created users.
                # Since this is an admin API, let's auto-verify to avoid friction,
                # or better, follow the verification status of the user model.
                verified = user.email_verification_status == "verified"

                EmailAddress.objects.create(
                    user=user, email=user.email, primary=True, verified=verified
                )

                # If not verified, we should ideally send a confirmation email.
                # However, since this is an admin creation endpoint, maybe we skip sending email
                # and assume the admin communicates with the user or verifies them manually?
                # For now, ensuring the EmailAddress record exists prevents the "no email address" error.

        except IntegrityError:
            raise serializers.ValidationError(
                {"email": "A user with that email already exists."}
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return user
