from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


class AllAuthHeadlessFlowTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "StrongPass123!"
        self.signup_url = "/users/auth/v1/signup"  # mapped in users/urls.py
        self.login_url = "/users/auth/v1/login"
        self.logout_url = "/users/auth/v1/logout"
        # token_refresh url in allauth headless is usually managed via specific endpoint or just login
        # actually allauth headless has a "session" endpoint or we check if our strategy exposes refresh
        # With SimpleJWT, we might need to check how to refresh.
        # AllAuth headless usually has /auth/session endpoint for checking/refreshing session?
        # But for JWT strategy, we returned {access, refresh} in login.
        # We need to verify if there is a standardized refresh endpoint in allauth headless for tokens.
        # If not, we might rely on re-login or standard simplejwt refresh if we mounted it?
        # But we removed auth views. AllAuth Headless should facilitate token refresh if strategy supports it.

    def test_signup_flow(self):
        """Test user registration via AllAuth Headless."""
        data = {
            "email": self.email,
            "password": self.password,
        }
        response = self.client.post(self.signup_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if user exists
        self.assertTrue(User.objects.filter(email=self.email).exists())

        # Response should contain session/token data depending on Headless config
        # We configured HEADLESS_TOKEN_STRATEGY = SimpleJWT...
        # It should return data matching what create_session/create_tokens returns.

    def test_login_flow(self):
        """Test login and token receipt."""
        # Create user first
        user = User.objects.create_user(email=self.email, password=self.password)

        data = {
            "email": self.email,
            "password": self.password,
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify content
        # With HEADLESS_CLIENT='app', we expect JSON response with tokens?
        # Our strategy returns simplejwt tokens.
        # AllAuth headless wraps this.
        # We expect 'data' -> 'user', 'meta' -> ...
        # Or maybe check headers if we said serve_token_as='header'.

        # If HEADLESS_SERVE_TOKEN_AS = 'header', access token is in X-Session-Token or Authorization?
        # allauth documentation says X-Session-Token by default for session, but for custom strategy?
        # Let's check headers.

        self.assertIn("data", response.json())

    def test_token_claims(self):
        """Verify the issued token contains our custom claims."""
        user = User.objects.create_user(email=self.email, password=self.password)

        data = {"email": self.email, "password": self.password}
        response = self.client.post(self.login_url, data, format="json")

        # Extract token
        # If in Custom Strategy we returned str(refresh.access_token) for create_access_token
        # It might be in the headers or body.
        # Assuming body for now or header 'X-Session-Token'.
        token = response.headers.get("X-Session-Token")

        # If not in header, check body?
        # But we configured HEADLESS_SERVE_TOKEN_AS = "header"

        if not token:
            # Fallback check
            token = response.json().get("data", {}).get("token")

        # Just print for debugging if it fails
        if not token:
            print("Response Headers:", response.headers)
            print("Response Body:", response.json())

        self.assertIsNotNone(token)

        # Decode and verify claims
        access = AccessToken(token)
        self.assertEqual(access["email"], self.email)
        self.assertIn("session_version", access)
