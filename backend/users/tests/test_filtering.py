from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class UserFilteringTests(APITestCase):
    def setUp(self):
        # Create a superuser to perform the filtering (staff-only action)
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            full_name="Admin User"
        )
        self.client.force_authenticate(user=self.superuser)
        
        # Create some test users
        self.user1 = User.objects.create_user(
            email="alice@example.com",
            full_name="Alice Smith",
            password="password123",
            is_staff=True
        )
        self.user2 = User.objects.create_user(
            email="bob@example.com",
            full_name="Bob Jones",
            password="password123",
            is_staff=False
        )
        self.user3 = User.objects.create_user(
            email="charlie@other.com",
            full_name="Charlie Brown",
            password="password123",
            is_staff=False
        )
        
        self.url = reverse('user-list')

    def test_filter_by_email_icontains(self):
        """Test filtering users by email (partial match)."""
        response = self.client.get(self.url, {'email': 'example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check items directly in raw response data
        items = response.data
        if isinstance(items, dict) and 'results' in items:
            items = items['results']
        elif isinstance(items, dict) and 'items' in items:
            items = items['items']
            
        self.assertEqual(len(items), 3) # admin, alice, bob all have example.com
        
        response = self.client.get(self.url, {'email': 'alice'})
        items = response.data
        if isinstance(items, dict) and 'results' in items:
            items = items['results']
        elif isinstance(items, dict) and 'items' in items:
            items = items['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['email'], "alice@example.com")

    def test_filter_by_full_name_icontains(self):
        """Test filtering users by full name (partial match)."""
        response = self.client.get(self.url, {'full_name': 'Smith'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        items = response.data
        if isinstance(items, dict) and 'results' in items:
            items = items['results']
        elif isinstance(items, dict) and 'items' in items:
            items = items['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['full_name'], "Alice Smith")

    def test_filter_by_is_staff(self):
        """Test filtering users by staff status."""
        response = self.client.get(self.url, {'is_staff': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        items = response.data
        if isinstance(items, dict) and 'results' in items:
            items = items['results']
        elif isinstance(items, dict) and 'items' in items:
            items = items['items']
        # Superuser is also staff
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertTrue(item['is_staff'])

    def test_filter_by_date_range(self):
        """Test filtering users by creation date range."""
        # Setup: move one user's creation date back
        # Since created_at is auto_now_add, we need to update it with .update()
        past_date = timezone.now() - timedelta(days=5)
        User.objects.filter(email="alice@example.com").update(created_at=past_date)
        
        # Filter for users created in the last 2 days
        recent_date = timezone.now() - timedelta(days=2)
        response = self.client.get(self.url, {'created_at_after': recent_date.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        items = response.data
        if isinstance(items, dict) and 'results' in items:
            items = items['results']
        elif isinstance(items, dict) and 'items' in items:
            items = items['items']
        # alice should be excluded
        self.assertEqual(len(items), 3) # admin, bob, charlie
        emails = [item['email'] for item in items]
        self.assertNotIn("alice@example.com", emails)

    def test_unauthorized_filtering_denied(self):
        """Test that regular users without view_user permission are denied access to list."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {'email': 'example.com'})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
