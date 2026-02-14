import unittest

from users.utils.permission_utils import can_access_user, can_reactivate_user


class DummyUser:
    def __init__(self, authenticated=True, staff=False, user_id=None, pk=None):
        self.is_authenticated = authenticated
        self.is_staff = staff
        self.user_id = user_id
        self.pk = pk


class TestPermissionUtils(unittest.TestCase):
    def test_staff_can_access_any_user(self):
        staff = DummyUser(authenticated=True, staff=True, user_id="staff-1", pk=1)
        target = DummyUser(authenticated=True, staff=False, user_id="user-1", pk=2)
        self.assertTrue(can_access_user(staff, target))

    def test_user_can_access_self_by_user_id(self):
        user = DummyUser(authenticated=True, staff=False, user_id="user-1", pk=5)
        self.assertTrue(can_access_user(user, user))

    def test_user_cannot_access_other(self):
        a = DummyUser(authenticated=True, staff=False, user_id="a", pk=1)
        b = DummyUser(authenticated=True, staff=False, user_id="b", pk=2)
        self.assertFalse(can_access_user(a, b))

    def test_anonymous_cannot_access(self):
        anon = DummyUser(authenticated=False, staff=False)
        target = DummyUser(authenticated=True, staff=False, user_id="x", pk=1)
        self.assertFalse(can_access_user(anon, target))

    def test_can_reactivate_requires_staff(self):
        staff = DummyUser(authenticated=True, staff=True)
        regular = DummyUser(authenticated=True, staff=False)
        self.assertTrue(can_reactivate_user(staff))
        self.assertFalse(can_reactivate_user(regular))


if __name__ == "__main__":
    unittest.main()
