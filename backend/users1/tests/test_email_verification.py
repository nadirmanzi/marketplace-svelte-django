"""Tests for email verification flow."""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users1.services.email_service import EmailVerificationService


User = get_user_model()


class EmailVerificationServiceTests(TestCase):
    """Unit tests for EmailVerificationService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )

    def test_generate_token_returns_string(self):
        """Token generation returns a non-empty string."""
        token = EmailVerificationService.generate_token(self.user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_verify_valid_token(self):
        """Valid token returns user without error."""
        token = EmailVerificationService.generate_token(self.user)
        user, error = EmailVerificationService.verify_token(token)
        self.assertEqual(user.user_id, self.user.user_id)
        self.assertIsNone(error)

    def test_verify_invalid_token(self):
        """Invalid token returns error."""
        user, error = EmailVerificationService.verify_token("invalid-token-string")
        self.assertIsNone(user)
        self.assertIsNotNone(error)
        self.assertIn("Invalid", error)

    @override_settings(EMAIL_VERIFICATION_TOKEN_EXPIRY=0)
    def test_verify_expired_token(self):
        """Expired token returns error."""
        token = EmailVerificationService.generate_token(self.user)
        # Token expires immediately with 0 expiry
        import time
        time.sleep(0.1)
        user, error = EmailVerificationService.verify_token(token)
        self.assertIsNone(user)
        self.assertIn("expired", error.lower())


class EmailVerificationAPITests(APITestCase):
    """Integration tests for email verification endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.request_url = reverse("user-request-email-verification")
        self.verify_url = reverse("user-verify-email")

    def test_request_verification_authenticated(self):
        """Authenticated user can request verification email."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.request_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_verification_already_verified(self):
        """Already verified user gets error."""
        self.user.email_verification_status = "verified"
        self.user.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.request_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_with_valid_token(self):
        """Valid token verifies email."""
        token = EmailVerificationService.generate_token(self.user)
        response = self.client.post(self.verify_url, {"token": token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email_verification_status, "verified")

    def test_verify_email_with_invalid_token(self):
        """Invalid token returns error."""
        response = self.client.post(self.verify_url, {"token": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_missing_token(self):
        """Missing token returns error."""
        response = self.client.post(self.verify_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RegistrationEmailVerificationTests(APITestCase):
    """Test auto-send verification email on registration."""
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_registration_sends_verification_email(self):
        """Registration automatically sends verification email."""
        from django.core import mail
        
        response = self.client.post(
            reverse("user-list"),
            {
                "email": "newuser@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "securepass123"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())
        self.assertIn("newuser@example.com", mail.outbox[0].to)


class EmailChangeVerificationTests(APITestCase):
    """Test email verification reset on email change."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="original@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123"
        )
        self.user.email_verification_status = "verified"
        self.user.save()
        self.client.force_authenticate(user=self.user)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_change_resets_verification(self):
        """Changing email resets verification status to pending."""
        from django.core import mail
        
        response = self.client.patch(
            reverse("user-detail", kwargs={"user_id": self.user.user_id}),
            {"email": "newemail@example.com"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")
        self.assertEqual(self.user.email_verification_status, "pending")
        
        # Verification email sent
        self.assertEqual(len(mail.outbox), 1)

    def test_same_email_no_reset(self):
        """Same email (case-insensitive) doesn't reset verification."""
        response = self.client.patch(
            reverse("user-detail", kwargs={"user_id": self.user.user_id}),
            {"email": "ORIGINAL@example.com"}  # Same email, different case
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        # Status should remain verified
        self.assertEqual(self.user.email_verification_status, "verified")
