from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from users.models import User


class PurgeUnverifiedUsersCommandTests(TestCase):
    """Test the purge_unverified_users management command."""

    def _user(self, email, user_type="provider", verified=False, age_days=10):
        user = User.objects.create_user(
            email=email,
            password="testpass123",
            user_type=user_type,
            is_email_verified=verified,
        )
        User.objects.filter(pk=user.pk).update(
            created_at=timezone.now() - timedelta(days=age_days)
        )
        return user

    def _run(self, *args):
        out = StringIO()
        call_command("purge_unverified_users", *args, stdout=out)
        return out.getvalue()

    def test_deletes_old_unverified_provider_and_client(self):
        self._user("old-provider@example.com")
        self._user("old-client@example.com", user_type="client")

        with self.assertLogs("users", level="INFO") as logs:
            out = self._run()

        self.assertFalse(User.objects.exists())
        self.assertIn("Deleted 2 unverified account(s)", out)
        self.assertEqual(len(logs.records), 2)
        self.assertEqual(logs.records[0].email, "old-provider@example.com")

    def test_keeps_verified_recent_and_admin_users(self):
        self._user("verified@example.com", verified=True)
        self._user("recent@example.com", age_days=3)
        self._user("admin@example.com", user_type="admin")

        self._run()

        self.assertEqual(User.objects.count(), 3)

    def test_days_option(self):
        self._user("three-days@example.com", age_days=3)

        self._run("--days", "2")

        self.assertFalse(User.objects.exists())

    def test_dry_run_deletes_nothing(self):
        self._user("old@example.com")

        out = self._run("--dry-run")

        self.assertTrue(User.objects.filter(email="old@example.com").exists())
        self.assertIn("Would delete 1 unverified account(s)", out)
