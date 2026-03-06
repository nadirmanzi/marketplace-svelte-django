from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

User = get_user_model()

class PasswordChangeTests(APITestCase):
    def setUp(self):
        # Clear cache for test isolation
        cache.clear()
        self.user = User.objects.create_user(
            email="change@example.com",
            password="ComplexPassword123!",
            full_name="Change User"
        )
        self.login_url = reverse('user-login')
        self.profile_url = reverse('user-me')
        self.change_password_url = reverse('user-change-password')

    def test_login_with_expired_password(self):
        """Test that login returns 403 when password is expired."""
        # Expire password
        self.user.password_changed_at = timezone.now() - timedelta(days=365)
        self.user.save()
        
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'password_expired')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_expired_user_can_only_change_password(self):
        """Test that expired user is blocked from others but allowed on change-password."""
        # Expire and login (get tokens)
        self.user.password_changed_at = timezone.now() - timedelta(days=365)
        self.user.save()
        
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Blocked from profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Allowed on change-password (GET not allowed, but endpoint exists)
        # Using post with empty data to see if it reaches the view logic
        response = self.client.post(self.change_password_url, {})
        # Should be 400 (validation error) not 403 (blocked by middleware)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_password_change(self):
        """Test that password change works and reactivates account access."""
        # Expire and login
        self.user.password_changed_at = timezone.now() - timedelta(days=365)
        self.user.save()
        
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Change password
        response = self.client.post(self.change_password_url, {
            'old_password': 'ComplexPassword123!',
            'new_password': 'NewComplexPassword456!',
            'confirm_password': 'NewComplexPassword456!'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        new_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_token}')
        
        # Now allowed on profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user model updated
        self.user.refresh_from_db()
        self.assertFalse(self.user.password_expired)
        self.assertTrue(self.user.check_password('NewComplexPassword456!'))
