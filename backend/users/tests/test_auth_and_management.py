from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, ContentType
from users.services.management_services import UserManagementService

User = get_user_model()

@override_settings(REST_FRAMEWORK={
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
})
class AuthAndManagementTests(TestCase):
    def setUp(self):
        cache.clear()  # Reset throttle cache between tests
        self.client = APIClient() # Initialize APIClient explicitly
        self.user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "telephone_number": "+16505551234"
        }
        self.user = User.objects.create_user(**self.user_data)
        
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            full_name="Admin User",
            telephone_number="+16505551235"
        )
        
        # Login to get tokens
        url = reverse("user-login")
        response = self.client.post(url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.access_token = response.data["access"]
        self.refresh_token = response.data["refresh"]

    def test_logout_invalidates_access_token(self):
        """Test that logging out invalidates existing access tokens (via session version)."""
        
        # 1. Verify access token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(reverse("user-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Logout
        logout_url = reverse("user-logout")
        response = self.client.post(logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Verify access token NO LONGER works
        response = self.client.get(reverse("user-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_login_invalidates_old_token(self):
        """Test that logging in again invalidates previous access tokens (single session/device)."""
        # 1. Get Token A (already got in setUp)
        token_a = self.access_token
        
        # 2. Login again to get Token B
        url = reverse("user-login")
        response = self.client.post(url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_b = response.data["access"]
        
        # 3. Verify Token A NO LONGER works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")
        response = self.client.get(reverse("user-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4. Verify Token B WORKS
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        response = self.client.get(reverse("user-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_set_staff_status(self):
        """Test setting staff status via service."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-set-staff-status", kwargs={"pk": self.user.pk})
        
        # Set to True
        response = self.client.post(url, {"is_staff": True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)
        
        # Set to False
        response = self.client.post(url, {"is_staff": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)

    def test_invalid_boolean_status(self):
        """Test that invalid boolean input raises ServiceValidationError (400)."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-set-staff-status", kwargs={"pk": self.user.pk})
        
        # Passing a string instead of a boolean (in JSON)
        response = self.client.post(url, {"is_staff": "not-a-bool"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("must be a boolean", response.data["detail"])

    def test_set_superuser_status(self):
        """Test setting superuser status via service."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-set-superuser-status", kwargs={"pk": self.user.pk})
        
        # Set to True
        response = self.client.post(url, {"is_superuser": True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_superuser)

        # Set to False
        response = self.client.post(url, {"is_superuser": False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)

    def test_manage_groups(self):
        """Test managing groups via service."""
        group = Group.objects.create(name="Test Group")
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-manage-groups", kwargs={"pk": self.user.pk})
        
        # Add group
        response = self.client.post(url, {"action": "add", "group_ids": [group.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.groups.filter(name="Test Group").exists())
        
        # Remove group
        response = self.client.post(url, {"action": "remove", "group_ids": [group.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user.groups.filter(name="Test Group").exists())

    def test_manage_permissions(self):
        """Test managing permissions via service."""
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="can_test",
            name="Can Test",
            content_type=content_type
        )
        self.client.force_authenticate(user=self.superuser)
        url = reverse("user-manage-permissions", kwargs={"pk": self.user.pk})
        
        # Add permission
        response = self.client.post(url, {"action": "add", "permission_ids": [permission.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check response data
        self.assertIn("can_test", response.data.get("current_permissions", []))
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.user_permissions.filter(codename="can_test").exists())
        
        # Remove permission
        response = self.client.post(url, {"action": "remove", "permission_ids": [permission.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.user_permissions.filter(codename="can_test").exists())
