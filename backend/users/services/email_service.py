"""Email verification service with time-limited tokens.

This service generates signed, time-limited tokens for email verification
and provides methods for token validation and email sending.
"""

import logging
from typing import Tuple, Optional

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationService:
    """Service for email verification token generation and validation."""

    TOKEN_SALT = "email-verification"

    @classmethod
    def generate_token(cls, user) -> str:
        """Generate a signed, time-limited email verification token.

        Args:
            user: User instance to generate token for.

        Returns:
            Signed token string containing user_id.
        """
        return signing.dumps(
            {"user_id": str(user.user_id)},
            salt=cls.TOKEN_SALT,
        )

    @classmethod
    def verify_token(cls, token: str) -> Tuple[Optional[User], Optional[str]]:
        """Verify an email verification token.

        Args:
            token: The signed token string.

        Returns:
            (user, None) on success.
            (None, error_message) on failure.
        """
        max_age = getattr(settings, "EMAIL_VERIFICATION_TOKEN_EXPIRY", 5 * 60 * 60)

        try:
            data = signing.loads(token, salt=cls.TOKEN_SALT, max_age=max_age)
        except signing.SignatureExpired:
            logger.info("Email verification token expired")
            return None, "Verification link has expired. Please request a new one."
        except signing.BadSignature:
            logger.warning("Invalid email verification token")
            return None, "Invalid verification link."

        user_id = data.get("user_id")
        if not user_id:
            return None, "Invalid token data."

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return None, "User not found."

        return user, None

    @classmethod
    def send_verification_email(cls, user, verification_url: str) -> bool:
        """Send a verification email to the user.

        Args:
            user: User instance to send email to.
            verification_url: Full URL for verification (including token).

        Returns:
            True if email sent successfully, False otherwise.
        """
        subject = "Verify your email address"
        message = f"""
            Hello {user.first_name},

            Please verify your email address by clicking the link below:

            {verification_url}

            This link will expire in 5 hours.

            If you did not create an account, please ignore this email.

            Best regards,
            The Marketplace Team
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Verification email sent to %s", user.email)
            return True
        except Exception as e:
            logger.exception("Failed to send verification email to %s: %s", user.email, e)
            return False
