from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class SessionInvalidationTests(APITestCase):
    def setUp(self):
        self.email = "test@example.com"
        self.password = "password123"
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name="Test",
            last_name="User"
        )
        self.login_url = reverse('user-login')
        # Assuming we have a protected endpoint to test against. 
        # We can use 'user-detail' for the current user.
        self.protected_url = reverse('user-detail', kwargs={'user_id': self.user.user_id})

    def test_session_invalidation_on_password_change(self):
        """
        Test that changing password invalidates existing tokens due to session_version mismatch.
        """
        # 1. Login to get initial tokens (v0)
        response = self.client.post(self.login_url, {'email': self.email, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token_v0 = response.data['access']
        
        # 2. Verify access works with v0 token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token_v0}')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Change password (increments session_version v0 -> v1)
        # We'll do this directly on the model for simplicity, as if done via a password reset flow
        self.user.set_password("newpassword456")
        self.user.save()
        
        # 4. Verify access fails with v0 token (401 Unauthorized)
        # The token still has session_version=0, but user has session_version=1
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Session is invalid", str(response.data))
        
        # 5. Login again to get new tokens (v1)
        response = self.client.post(self.login_url, {'email': self.email, 'password': "newpassword456"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token_v1 = response.data['access']
        
        # 6. Verify access works with v1 token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token_v1}')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_session_version_in_token_claims(self):
        """Verify session_version is present in token claims."""
        response = self.client.post(self.login_url, {'email': self.email, 'password': self.password})
        access_token = response.data['access']
        
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(access_token)
        self.assertIn('session_version', token)
        self.assertEqual(token['session_version'], 0)
