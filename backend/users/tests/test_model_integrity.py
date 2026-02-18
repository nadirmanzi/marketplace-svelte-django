from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.services.management_services import UserManagementService

User = get_user_model()

class UserModelIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            full_name="Test User",
            password="testpassword123",
            telephone_number="+16505551234"
        )
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpassword123",
            full_name="Admin User"
        )

    def test_is_last_superuser_property(self):
        """Test the is_last_superuser property logic."""
        # 1. Check a non-superuser
        self.assertFalse(self.user.is_last_superuser)

        # 2. Check the only superuser
        self.assertTrue(self.superuser.is_last_superuser)

        # 3. Add another superuser
        another_admin = User.objects.create_superuser(
            email="admin2@example.com",
            password="adminpassword123",
            full_name="Admin 2"
        )
        
        # Now neither should be the "last"
        self.superuser.refresh_from_db() # Not strictly needed for pk check but good practice
        self.assertFalse(self.superuser.is_last_superuser)
        self.assertFalse(another_admin.is_last_superuser)

        # 4. Delete one
        another_admin.delete()
        self.assertTrue(self.superuser.is_last_superuser)

    def test_soft_delete_save_invariants(self):
        """Verify that User.save() handles soft-delete fields correctly."""
        user = self.user
        
        # Verify initial state
        self.assertFalse(user.is_soft_deleted)
        self.assertIsNone(user.soft_deleted_at)
        self.assertTrue(user.is_active)

        # Trigger soft-delete logic in save()
        user.is_soft_deleted = True
        user.save()

        self.assertTrue(user.is_soft_deleted)
        self.assertIsNotNone(user.soft_deleted_at)
        self.assertFalse(user.is_active)
        
        # Verify it persisted
        user.refresh_from_db()
        self.assertTrue(user.is_soft_deleted)
        self.assertIsNotNone(user.soft_deleted_at)
        self.assertFalse(user.is_active)

    def test_activate_save_invariants(self):
        """Verify that User.save() clears soft-delete fields on activation."""
        user = self.user
        user.is_soft_deleted = True
        user.soft_deleted_at = timezone.now()
        user.is_active = False
        user.save()

        # Reactivate
        user.is_soft_deleted = False
        user.is_active = True
        user.save()

        self.assertFalse(user.is_soft_deleted)
        self.assertIsNone(user.soft_deleted_at)
        self.assertTrue(user.is_active)

    def test_service_uses_model_invariants(self):
        """
        Verify that UserManagementService successfully leverages model invariants.
        
        The service no longer sets 'soft_deleted_at' or 'is_active' explicitly
        during soft-delete, relying on the model's save() instead.
        """
        user = self.user
        
        # Use service
        UserManagementService.soft_delete_user(user)

        # Verify model invariants were applied
        self.assertTrue(user.is_soft_deleted)
        self.assertIsNotNone(user.soft_deleted_at)
        self.assertFalse(user.is_active)
