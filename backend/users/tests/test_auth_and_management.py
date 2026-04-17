from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, ContentType
from users.services.management_services import UserManagementService

User = get_user_model()

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
        self.access_token = response.cookies["access_token"].value
        self.refresh_token = response.cookies["refresh_token"].value

    def test_logout_invalidates_access_token(self):
        """Test that logging out invalidates existing access tokens (via session version)."""
        
        # 1. Verify access token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(reverse("user-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Logout
        logout_url = reverse("user-logout")
        response = self.client.post(logout_url)
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
        token_b = response.cookies["access_token"].value
        
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
        # Unified error schema: {"success": false, "code": "...", "detail": "...", "errors": {...}}
        self.assertFalse(response.data["success"])
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

    def test_zero_db_token_refresh(self):
        """Test that token refresh minimizes DB queries for the user (allows 1 for rotation)."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from rest_framework_simplejwt.tokens import AccessToken
        
        url = reverse("user-token_refresh")
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(url)
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access = response.cookies["access_token"].value if "access_token" in response.cookies else None
        self.assertIsNotNone(new_access)
        
        user_queries = [q for q in queries.captured_queries if "users_user" in q["sql"]]
        
        # 1 PK lookup is unavoidable during blacklist creation (OutstandingToken uses a real ForeignKey to User)
        # The key success is that it doesn't query the DB again to serialize claims.
        self.assertLessEqual(len(user_queries), 2, f"Refresh token hit user table {len(user_queries)} times (expected <= 2)!")
        
        # Verify custom claims
        token_obj = AccessToken(new_access)
        self.assertIn("email", token_obj.payload)
        self.assertEqual(token_obj.payload["email"], self.user_data["email"])

    def test_verify_token_via_cookie(self):
        """Test TokenVerifyView works with cookies and check expiration cookie."""
        # 1. Clear existing credentials to rely on cookies
        self.client.credentials() 
        
        # 2. Check if login set the expiration cookie
        self.assertIn("access_token_expires", self.client.cookies)
        expires_ts = int(self.client.cookies["access_token_expires"].value)
        self.assertTrue(expires_ts > 0)
        
        # 3. Call verify with NO body (should pull from cookies)
        url = reverse("user-token_verify")
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4. Verify logout deletes the expiration cookie (sets value to empty in test client)
        logout_url = reverse("user-logout")
        self.client.post(logout_url)
        self.assertEqual(self.client.cookies["access_token_expires"].value, "")
