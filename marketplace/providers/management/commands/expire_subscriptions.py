"""Management command to expire overdue subscriptions and send renewal reminders.

Intended to run daily via cron:
    0 1 * * * deploy /opt/massage_marketplace/venv/bin/python \
        /opt/massage_marketplace/marketplace/manage.py expire_subscriptions

Two actions are taken each run:
  1. Deactivate — providers whose renewal_date is in the past are set to inactive.
  2. Remind     — providers whose renewal_date is exactly REMINDER_DAYS_BEFORE days
                  away receive a renewal reminder email.

After each run an admin summary email is sent to ADMIN_EMAILS when:
  - any subscriptions were expired, OR
  - any renewal reminders were sent, OR
  - any individual emails failed to deliver.
Runs where nothing happened produce no email.
"""

import logging
import time
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from providers.models import Provider

logger = logging.getLogger(__name__)

REMINDER_DAYS_BEFORE = 3

# Email domains treated as test addresses — no emails are sent to these.
TEST_EMAIL_DOMAINS = {"example.com", "seed.example.com"}

# Seconds to wait between outgoing emails to avoid SMTP rate-limit triggers.
# Override with EMAIL_BULK_DELAY in settings if needed.
EMAIL_BULK_DELAY = 2


class Command(BaseCommand):
    help = "Deactivate expired subscriptions and email renewal reminders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would happen without making any changes or sending emails",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        today = date.today()
        reminder_date = today + timedelta(days=REMINDER_DAYS_BEFORE)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made"))

        # Accumulated failures: list of (email, action, error_message)
        failures = []

        expired_count = self._expire_overdue(today, dry_run, failures)
        reminded_count = self._send_reminders(reminder_date, dry_run, failures)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Expired: {expired_count}, Reminders sent: {reminded_count}, "
                f"Failures: {len(failures)}"
            )
        )
        logger.info(
            "expire_subscriptions: expired=%d reminded=%d failures=%d dry_run=%s",
            expired_count,
            reminded_count,
            len(failures),
            dry_run,
        )

        if not dry_run:
            self._send_admin_summary(today, expired_count, reminded_count, failures)

    # -------------------------------------------------------------------------
    # Core logic
    # -------------------------------------------------------------------------

    def _expire_overdue(self, today, dry_run, failures):
        """Deactivate all active subscriptions whose renewal date has passed."""
        overdue = Provider.objects.filter(
            subscription_status="active",
            subscription_renewal_date__lt=today,
        ).select_related("user")

        count = overdue.count()
        if count == 0:
            return 0

        delay = getattr(settings, "EMAIL_BULK_DELAY", EMAIL_BULK_DELAY)
        for provider in overdue:
            self.stdout.write(
                f"  Expiring {provider.user.email} "
                f"(renewal was {provider.subscription_renewal_date})"
            )
            if not dry_run:
                provider.deactivate_subscription()
                logger.info(
                    "Subscription expired for %s (renewal_date=%s)",
                    provider.user.email,
                    provider.subscription_renewal_date,
                )
                self._send_expiry_email(provider, failures)
                time.sleep(delay)

        return count

    def _send_reminders(self, reminder_date, dry_run, failures):
        """Email providers whose subscription expires in REMINDER_DAYS_BEFORE days."""
        due = Provider.objects.filter(
            subscription_status="active",
            subscription_renewal_date=reminder_date,
        ).select_related("user")

        count = due.count()
        if count == 0:
            return 0

        delay = getattr(settings, "EMAIL_BULK_DELAY", EMAIL_BULK_DELAY)
        for provider in due:
            self.stdout.write(
                f"  Reminding {provider.user.email} "
                f"(renewal on {provider.subscription_renewal_date})"
            )
            if not dry_run:
                self._send_reminder_email(provider, failures)
                logger.info(
                    "Renewal reminder sent to %s (renewal_date=%s)",
                    provider.user.email,
                    provider.subscription_renewal_date,
                )
                time.sleep(delay)

        return count

    # -------------------------------------------------------------------------
    # Provider emails
    # -------------------------------------------------------------------------

    @staticmethod
    def _is_test_email(email):
        domain = email.split("@")[-1].lower()
        return domain in TEST_EMAIL_DOMAINS

    def _send_reminder_email(self, provider, failures):
        if self._is_test_email(provider.user.email):
            logger.debug("Skipping renewal reminder for test address %s", provider.user.email)
            return

        renewal_date = provider.subscription_renewal_date.strftime("%B %d, %Y")
        name = provider.get_name()
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "your-domain.com"

        try:
            send_mail(
                subject="Your subscription renews in 3 days — Massage Marketplace",
                message=(
                    f"Hi {name},\n\n"
                    f"Your Massage Marketplace subscription is due for renewal on {renewal_date}.\n\n"
                    f"To keep your profile active and visible to clients, please renew before that date:\n\n"
                    f"    https://{host}/provider/subscription/\n\n"
                    f"If you have any questions, reply to this email.\n\n"
                    f"— Massage Marketplace"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[provider.user.email],
                fail_silently=False,
            )
        except Exception as exc:
            msg = str(exc)
            logger.exception("Failed to send renewal reminder to %s", provider.user.email)
            failures.append((provider.user.email, "renewal reminder", msg))

    def _send_expiry_email(self, provider, failures):
        if self._is_test_email(provider.user.email):
            logger.debug("Skipping expiry email for test address %s", provider.user.email)
            return

        name = provider.get_name()
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "your-domain.com"

        try:
            send_mail(
                subject="Your subscription has expired — Massage Marketplace",
                message=(
                    f"Hi {name},\n\n"
                    f"Your Massage Marketplace subscription has expired and your profile "
                    f"is no longer visible to clients.\n\n"
                    f"To reactivate your listing, renew your subscription here:\n\n"
                    f"    https://{host}/provider/subscription/\n\n"
                    f"— Massage Marketplace"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[provider.user.email],
                fail_silently=False,
            )
        except Exception as exc:
            msg = str(exc)
            logger.exception("Failed to send expiry email to %s", provider.user.email)
            failures.append((provider.user.email, "expiry notification", msg))

    # -------------------------------------------------------------------------
    # Admin summary
    # -------------------------------------------------------------------------

    def _send_admin_summary(self, today, expired_count, reminded_count, failures):
        """Send a summary email to ADMIN_EMAILS if anything happened."""
        admin_emails = getattr(settings, "ADMIN_EMAILS", [])
        if not admin_emails:
            return

        # Silent run — nothing to report
        if expired_count == 0 and reminded_count == 0 and not failures:
            return

        status = "⚠️ completed with failures" if failures else "✅ completed successfully"
        subject = f"[Massage Marketplace] Subscription cron {status} — {today}"

        lines = [
            f"Subscription maintenance ran on {today}.",
            "",
            "SUMMARY",
            "-------",
            f"  Subscriptions expired:   {expired_count}",
            f"  Renewal reminders sent:  {reminded_count}",
            f"  Email failures:          {len(failures)}",
        ]

        if failures:
            lines += [
                "",
                "FAILURES",
                "--------",
                "The following emails could not be delivered:",
                "",
            ]
            for email, action, error in failures:
                lines.append(f"  • {email} ({action})")
                lines.append(f"    Error: {error}")
                lines.append("")
            lines += [
                "Action required: check SMTP configuration and retry manually if needed.",
                "Sentry will have captured the full traceback.",
            ]

        lines += ["", "— Massage Marketplace automated job"]

        try:
            send_mail(
                subject=subject,
                message="\n".join(lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True,  # don't crash the cron job if admin email fails
            )
            logger.info("Admin summary sent to %s", admin_emails)
        except Exception:
            logger.exception("Failed to send admin summary email")
