"""Tests for token rotation and refresh functionality."""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from users.services.token_service import TokenService
from users.tokens import CustomRefreshToken


User = get_user_model()


class TokenRotationServiceTests(TestCase):
    """Unit tests for token rotation in TokenService."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )

    def test_create_login_tokens(self):
        """Create login tokens returns access and refresh."""
        tokens = TokenService.create_login_tokens(self.user)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)
        self.assertTrue(len(tokens["access"]) > 0)
        self.assertTrue(len(tokens["refresh"]) > 0)

    def test_verify_valid_token(self):
        """Verify valid access token succeeds."""
        tokens = TokenService.create_login_tokens(self.user)
        ok, error = TokenService.verify_token(tokens["access"])
        self.assertTrue(ok)
        self.assertIsNone(error)

    def test_verify_invalid_token(self):
        """Verify invalid token fails."""
        ok, error = TokenService.verify_token("invalid-token")
        self.assertFalse(ok)
        self.assertIsNotNone(error)

    @override_settings(
        SIMPLE_JWT={"ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True}
    )
    def test_refresh_token_returns_new_tokens(self):
        """Refresh token returns new access and refresh tokens."""
        tokens = TokenService.create_login_tokens(self.user)
        old_refresh = tokens["refresh"]

        new_tokens, error = TokenService.refresh_token(old_refresh)

        self.assertIsNone(error)
        self.assertIn("access", new_tokens)
        self.assertIn("refresh", new_tokens)

    def test_refresh_invalid_token(self):
        """Refresh with invalid token fails."""
        tokens, error = TokenService.refresh_token("invalid-refresh-token")
        self.assertIsNone(tokens)
        self.assertIsNotNone(error)

    def test_invalidate_token(self):
        """Invalidate token blacklists it."""
        tokens = TokenService.create_login_tokens(self.user)

        ok, error = TokenService.invalidate_token(tokens["refresh"])
        self.assertTrue(ok)
        self.assertIsNone(error)


class TokenRotationAPITests(APITestCase):
    """Integration tests for token rotation endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )
        self.login_url = reverse("user-login")
        self.refresh_url = reverse("user-token-refresh")

    def test_login_returns_tokens(self):
        """Login returns access and refresh tokens."""
        response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user_id", response.data)

    def test_refresh_returns_new_tokens(self):
        """Token refresh returns new tokens."""
        # Login first
        login_response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "testpass123"}
        )
        refresh_token = login_response.data["refresh"]

        # Refresh
        response = self.client.post(self.refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_with_blacklisted_token_fails(self):
        """Using blacklisted token for refresh fails."""
        # Login and get tokens
        login_response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "testpass123"}
        )
        refresh_token = login_response.data["refresh"]

        # Logout (blacklists the token)
        self.client.post(reverse("user-logout"), {"refresh": refresh_token})

        # Try to use blacklisted token
        response = self.client.post(self.refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_access_token_works(self):
        """New access token from refresh works for authenticated requests."""
        # Login
        login_response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "testpass123"}
        )

        # Refresh
        refresh_response = self.client.post(
            self.refresh_url, {"refresh": login_response.data["refresh"]}
        )
        new_access = refresh_response.data["access"]

        # Use new token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        response = self.client.get(
            reverse("user-detail", kwargs={"user_id": self.user.user_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenBlacklistTests(APITestCase):
    """Tests for token blacklisting on logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="testpass123",
        )
        self.login_url = reverse("user-login")
        self.logout_url = reverse("user-logout")

        login_response = self.client.post(
            self.login_url, {"email": "test@example.com", "password": "testpass123"}
        )

        if login_response.status_code == status.HTTP_200_OK:
            self.access_token = login_response.data["access"]
            self.refresh_token = login_response.data["refresh"]

            # 🚀 ADD THIS CRITICAL LINE 🚀
            # This authenticates the client for ALL subsequent tests in this class
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        else:
            self.access_token = None

    def test_logout_blacklists_token(self):
        """Logout blacklists the refresh token."""

        # We use the refresh_token obtained in setUp
        # Client is already authenticated via self.client.credentials() in setUp
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_access_token_fails(self):
        """Unauthenticated access to logout should be rejected with 401."""

        # 1. This test correctly clears the credentials set in setUp
        self.client.credentials()

        # 2. Send request with no headers/tokens
        response = self.client.post(self.logout_url, {})

        # 3. ASSERT: Expect DRF to stop it with 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_access_but_no_refresh_token_fails(self):
        """Authenticated request with missing refresh token in body fails with 400."""

        # The client is already authenticated by setUp, so we just send the request.
        response = self.client.post(
            self.logout_url, {}, content_type="application/json"
        )

        # ASSERT: Expect the view's internal 'if not refresh_token:' logic to be hit
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(b"Refresh token is required.", response.content)
