import unittest
from datetime import datetime, timedelta, timezone

from users.utils.token_utils import get_current_utc, make_datetime_aware, is_token_expired


class TestTokenUtils(unittest.TestCase):
    def test_get_current_utc_is_aware(self):
        now = get_current_utc()
        self.assertIsNotNone(now.tzinfo)

    def test_make_datetime_aware_converts_naive(self):
        naive = datetime(2020, 1, 1, 0, 0, 0)
        aware = make_datetime_aware(naive)
        self.assertIsNotNone(aware.tzinfo)

    def test_is_token_expired_none(self):
        self.assertTrue(is_token_expired(None))

    def test_is_token_expired_past(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        self.assertTrue(is_token_expired(past))

    def test_is_token_not_expired_future(self):
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        self.assertFalse(is_token_expired(future))


if __name__ == "__main__":
    unittest.main()
