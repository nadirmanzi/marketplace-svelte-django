"""Tests for password reset flow."""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users1.services.password_reset_service import PasswordResetService


User = get_user_model()


class PasswordResetServiceTests(TestCase):
    """Unit tests for PasswordResetService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="oldpassword123"
        )

    def test_generate_token_returns_string(self):
        """Token generation returns a non-empty string."""
        token = PasswordResetService.generate_token(self.user)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

    def test_verify_valid_token(self):
        """Valid token returns user without error."""
        token = PasswordResetService.generate_token(self.user)
        user, error = PasswordResetService.verify_token(token)
        self.assertEqual(user.user_id, self.user.user_id)
        self.assertIsNone(error)

    def test_verify_invalid_token(self):
        """Invalid token returns error."""
        user, error = PasswordResetService.verify_token("invalid-token-string")
        self.assertIsNone(user)
        self.assertIsNotNone(error)

    @override_settings(PASSWORD_RESET_TOKEN_EXPIRY=0)
    def test_verify_expired_token(self):
        """Expired token returns error."""
        token = PasswordResetService.generate_token(self.user)
        import time
        time.sleep(0.1)
        user, error = PasswordResetService.verify_token(token)
        self.assertIsNone(user)
        self.assertIn("expired", error.lower())

    def test_token_invalid_after_password_change(self):
        """Token becomes invalid after password change (session version mismatch)."""
        token = PasswordResetService.generate_token(self.user)
        
        # Change password (increments session_version)
        self.user.set_password("newpassword456")
        self.user.save()
        
        # Token should now be invalid
        user, error = PasswordResetService.verify_token(token)
        self.assertIsNone(user)
        self.assertIn("no longer valid", error.lower())


class PasswordResetAPITests(APITestCase):
    """Integration tests for password reset endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="oldpassword123"
        )
        self.request_url = reverse("user-request-password-reset")
        self.reset_url = reverse("user-reset-password")

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_request_password_reset_existing_email(self):
        """Request password reset for existing email sends email."""
        from django.core import mail
        
        response = self.client.post(self.request_url, {"email": "test@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset", mail.outbox[0].subject.lower())

    def test_request_password_reset_nonexistent_email(self):
        """Request password reset for non-existent email returns 200 (no email enumeration)."""
        response = self.client.post(self.request_url, {"email": "nonexistent@example.com"})
        # Should still return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_missing_email(self):
        """Request without email returns validation error."""
        response = self.client.post(self.request_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_with_valid_token(self):
        """Password reset with valid token succeeds."""
        token = PasswordResetService.generate_token(self.user)
        
        response = self.client.post(self.reset_url, {
            "token": token,
            "new_password": "newSecurePass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newSecurePass123!"))

    def test_reset_password_with_invalid_token(self):
        """Password reset with invalid token fails."""
        response = self.client.post(self.reset_url, {
            "token": "invalid-token",
            "new_password": "newSecurePass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_weak_password(self):
        """Password reset with weak password fails validation."""
        token = PasswordResetService.generate_token(self.user)
        
        response = self.client.post(self.reset_url, {
            "token": token,
            "new_password": "123"  # Too short
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_invalidates_tokens(self):
        """After password reset, old tokens are invalid."""
        # Login to get tokens
        login_response = self.client.post(reverse("user-login"), {
            "email": "test@example.com",
            "password": "oldpassword123"
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        old_access_token = login_response.data["access"]
        
        # Reset password
        reset_token = PasswordResetService.generate_token(self.user)
        self.client.post(self.reset_url, {
            "token": reset_token,
            "new_password": "newSecurePass123!"
        })
        
        # Old access token should now be invalid (session version mismatch)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_access_token}")
        response = self.client.get(
            reverse("user-detail", kwargs={"user_id": self.user.user_id})
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
