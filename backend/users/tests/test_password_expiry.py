from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

User = get_user_model()

class PasswordExpiryTests(APITestCase):
    def setUp(self):
        # Clear cache for test isolation
        cache.clear()
        # Create a test user
        self.user = User.objects.create_user(
            email="expiry@example.com",
            password="ComplexPassword123!",
            full_name="Expiry User"
        )
        self.url = reverse('user-me')
        self.login_url = reverse('user-login')

    def test_password_not_expired(self):
        """Test that user can access profile when password is not expired."""
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        
        if response.status_code != status.HTTP_200_OK:
            print(f"DEBUG NOT EXPIRED LOGIN: {response.status_code}, {response.data}")
            
        token = response.cookies['access_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_expired_blocks_access(self):
        """Test that access is blocked when password_expired is True."""
        # Manually expire password 
        expiry_days = self.user.password_expires_in_days
        self.user.password_changed_at = timezone.now() - timedelta(days=expiry_days + 1)
        self.user.save()
        
        # Login should return 403 Forbidden because password expired
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "password_expired")
        
        # But tokens should still be present
        token = response.cookies['access_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Accessing protected view should be blocked
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['code'], "password_expired")

    def test_superuser_exempt_from_expiry(self):
        """Test that superusers are exempt from password expiry blocks."""
        admin = User.objects.create_superuser(
            email="admin_expiry@example.com",
            password="ComplexPassword123!",
            full_name="Admin Expiry"
        )
        # Login
        response = self.client.post(self.login_url, {
            'email': admin.email,
            'password': 'ComplexPassword123!'
        })
        
        if response.status_code != status.HTTP_200_OK:
             print(f"DEBUG SUPERUSER LOGIN: {response.status_code}, {response.data}")
             
        token = response.cookies['access_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Expire admin password
        admin.refresh_from_db()
        expiry_days = admin.password_expires_in_days
        admin.password_changed_at = timezone.now() - timedelta(days=expiry_days + 1)
        admin.save()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expiry_warning_header(self):
        """Test that X-Password-Expires-In-Days header is present."""
        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'ComplexPassword123!'
        })
        token = response.cookies['access_token'].value
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(self.url)
        self.assertIn('X-Password-Expires-In-Days', response)
        # Check that it's a reasonable positive number (e.g. 89 or 90)
        days = int(response['X-Password-Expires-In-Days'])
        self.assertTrue(0 < days <= self.user.password_expires_in_days)
