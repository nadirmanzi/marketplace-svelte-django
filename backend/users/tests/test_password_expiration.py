from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class PasswordExpirationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )

    def test_password_expired_with_none_changed_at(self):
        """Test that password is expired if password_changed_at is None."""
        # By default create_user might set password_changed_at via set_password
        # So we manually set it to None to simulate legacy user or specific case
        self.user.password_changed_at = None
        self.user.save()
        self.assertTrue(self.user.password_expired)

    def test_password_not_expired_fresh(self):
        """Test that a freshly changed password is not expired."""
        # User created in setUp has just had password set
        self.assertFalse(self.user.password_expired)

    def test_password_expired_after_duration(self):
        """Test that password expires after the configured duration."""
        # Set password changed date to past the expiration window
        days_ago = self.user.password_expires_in_days + 1
        self.user.password_changed_at = timezone.now() - timedelta(days=days_ago)
        self.user.save()
        self.assertTrue(self.user.password_expired)

    def test_custom_expiration_duration(self):
        """Test that changing the expiration duration works."""
        self.user.password_expires_in_days = 30
        
        # 29 days ago - NOT expired
        self.user.password_changed_at = timezone.now() - timedelta(days=29)
        self.user.save()
        self.assertFalse(self.user.password_expired)
        
        # 31 days ago - EXPIRED
        self.user.password_changed_at = timezone.now() - timedelta(days=31)
        self.user.save()
        self.assertTrue(self.user.password_expired)

    def test_set_password_updates_changed_at(self):
        """Verify set_password updates the timestamp."""
        old_timestamp = self.user.password_changed_at
        
        # Ensure some time passes or mock time, but for simple check:
        # We can just check it's not None and roughly now.
        # Better: set it to old time, call set_password, check it updated.
        
        old_time = timezone.now() - timedelta(days=100)
        self.user.password_changed_at = old_time
        self.user.save()
        
        self.user.set_password("newpassword123")
        self.user.save()
        
        self.assertNotEqual(self.user.password_changed_at, old_time)
        self.assertFalse(self.user.password_expired)
