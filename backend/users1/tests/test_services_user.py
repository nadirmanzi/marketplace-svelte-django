import unittest
from users1.services.user_service import UserLifecycleService


class FakeUser:
    def __init__(self, pk=1, user_id="u1", is_active=True, is_soft_deleted=False, deleted_at=None):
        self.pk = pk
        self.user_id = user_id
        self.is_active = is_active
        self.is_soft_deleted = is_soft_deleted
        self.deleted_at = deleted_at
        self._saved = False
        self._update_fields = None

    def save(self, update_fields=None):
        self._saved = True
        self._update_fields = update_fields

    def full_clean(self):
        # Assume valid for tests
        return None


class TestUserService(unittest.TestCase):
    def test_soft_delete_user(self):
        u = FakeUser(is_active=True, is_soft_deleted=False)
        user, error = UserLifecycleService.soft_delete_user(u)
        self.assertIsNone(error)
        self.assertTrue(user.is_soft_deleted)
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)
        self.assertTrue(user._saved)

    def test_soft_delete_already_deleted(self):
        u = FakeUser(is_soft_deleted=True)
        user, error = UserLifecycleService.soft_delete_user(u)
        self.assertIsNone(user)
        self.assertIsNotNone(error)

    def test_deactivate_user(self):
        u = FakeUser(is_active=True, is_soft_deleted=False)
        user, error = UserLifecycleService.deactivate_user(u)
        self.assertIsNone(error)
        self.assertFalse(user.is_active)

    def test_deactivate_soft_deleted(self):
        u = FakeUser(is_active=True, is_soft_deleted=True)
        user, error = UserLifecycleService.deactivate_user(u)
        self.assertIsNone(user)
        self.assertIsNotNone(error)

    def test_reactivate_user(self):
        u = FakeUser(is_active=False, is_soft_deleted=False)
        user, error = UserLifecycleService.reactivate_user(u)
        self.assertIsNone(error)
        self.assertTrue(user.is_active)

    def test_reactivate_deleted_user(self):
        u = FakeUser(is_active=False, is_soft_deleted=True)
        user, error = UserLifecycleService.reactivate_user(u)
        self.assertIsNone(user)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()
