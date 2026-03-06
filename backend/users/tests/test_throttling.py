from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

class ThrottlingTests(APITestCase):
    def setUp(self):
        # Clear cache to ensure tests are isolated
        cache.clear()
        
        # Create a test user
        self.user = User.objects.create_user(
            email="throttle@example.com",
            password="ComplexPassword123!",
            full_name="Throttle User"
        )
        self.login_url = reverse('user-login')
        self.register_url = reverse('user-list') # POST on list endpoint is register

    def test_login_throttle(self):
        """Test that login is throttled after 5 attempts."""
        # Rate is 5/min
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': 'wrong@example.com',
                'password': 'wrongpassword'
            })
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 6th attempt should be throttled
        response = self.client.post(self.login_url, {
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_registration_throttle(self):
        """Test that registration is throttled after 2 attempts."""
        # Rate is 2/hour
        data = {
            'email': 'new1@example.com',
            'full_name': 'New User 1',
            'password': 'ComplexPassword123!',
            'telephone_number': '+16102451234'
        }
        
        # 1st attempt
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2nd attempt
        data['email'] = 'new2@example.com'
        data['telephone_number'] = '+16102451235'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3rd attempt should be throttled
        data['email'] = 'new3@example.com'
        data['telephone_number'] = '+15551234569'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_search_throttle(self):
        """Test that user list (search) is throttled for staff."""
        # Create a regular staff user (not superuser, as superusers are exempt)
        from django.contrib.auth.models import Permission
        staff_user = User.objects.create_user(
            email="staff@throttle.com",
            password="staffpassword",
            full_name="Staff User",
            is_staff=True
        )
        # Grant view_user permission
        view_perm = Permission.objects.get(codename='view_user')
        staff_user.user_permissions.add(view_perm)
        
        self.client.force_authenticate(user=staff_user)
        
        # Rate is 30/min
        for i in range(30):
            response = self.client.get(self.register_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        # 31st attempt should be throttled
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_superuser_throttle_exemption(self):
        """Test that superusers are exempt from throttling."""
        admin = User.objects.create_superuser(
            email="exempt@admin.com",
            password="adminpassword",
            full_name="Exempt Admin"
        )
        self.client.force_authenticate(user=admin)
        
        # Try login (anon throttle bucket, but superuser mixin should check auth)
        # Actually LoginRateThrottle is AnonRateThrottle, so it checks IP.
        # But UserThrottle mixin checks request.user.is_superuser.
        
        # Let's test a UserRateThrottle first (Search)
        for i in range(40): # > 30 limit
            response = self.client.get(self.register_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        # Should still be 200 OK
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
