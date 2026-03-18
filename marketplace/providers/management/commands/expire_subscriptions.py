"""Management command to expire overdue subscriptions and send renewal reminders.

Intended to run daily via cron:
    0 1 * * * deploy /opt/massage_marketplace/venv/bin/python \
        /opt/massage_marketplace/marketplace/manage.py expire_subscriptions

Two actions are taken each run:
  1. Deactivate — providers whose renewal_date is in the past are set to inactive.
  2. Remind     — providers whose renewal_date is exactly REMINDER_DAYS_BEFORE days
                  away receive a renewal reminder email.
"""

import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from providers.models import Provider

logger = logging.getLogger(__name__)

REMINDER_DAYS_BEFORE = 3


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

        expired_count = self._expire_overdue(today, dry_run)
        reminded_count = self._send_reminders(reminder_date, dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Expired: {expired_count}, Reminders sent: {reminded_count}"
            )
        )
        logger.info(
            "expire_subscriptions: expired=%d reminded=%d dry_run=%s",
            expired_count,
            reminded_count,
            dry_run,
        )

    def _expire_overdue(self, today, dry_run):
        """Deactivate all active subscriptions whose renewal date has passed."""
        overdue = Provider.objects.filter(
            subscription_status="active",
            subscription_renewal_date__lt=today,
        ).select_related("user")

        count = overdue.count()
        if count == 0:
            return 0

        for provider in overdue:
            self.stdout.write(
                f"  Expiring {provider.user.email} "
                f"(renewal was {provider.subscription_renewal_date})"
            )
            if not dry_run:
                provider.deactivate_subscription()
                self._send_expiry_email(provider)
                logger.info(
                    "Subscription expired for %s (renewal_date=%s)",
                    provider.user.email,
                    provider.subscription_renewal_date,
                )

        return count

    def _send_reminders(self, reminder_date, dry_run):
        """Email providers whose subscription expires in REMINDER_DAYS_BEFORE days."""
        due = Provider.objects.filter(
            subscription_status="active",
            subscription_renewal_date=reminder_date,
        ).select_related("user")

        count = due.count()
        if count == 0:
            return 0

        for provider in due:
            self.stdout.write(
                f"  Reminding {provider.user.email} "
                f"(renewal on {provider.subscription_renewal_date})"
            )
            if not dry_run:
                self._send_reminder_email(provider)
                logger.info(
                    "Renewal reminder sent to %s (renewal_date=%s)",
                    provider.user.email,
                    provider.subscription_renewal_date,
                )

        return count

    def _send_reminder_email(self, provider):
        from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@massagemarketplace.com"
        )
        renewal_date = provider.subscription_renewal_date.strftime("%B %d, %Y")
        name = provider.get_name()

        try:
            send_mail(
                subject="Your subscription renews in 3 days — Massage Marketplace",
                message=(
                    f"Hi {name},\n\n"
                    f"Your Massage Marketplace subscription is due for renewal on {renewal_date}.\n\n"
                    f"To keep your profile active and visible to clients, please renew your "
                    f"subscription before that date:\n\n"
                    f"    {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'your-domain.com'}"
                    f"/provider/subscription/\n\n"
                    f"If you have any questions, reply to this email.\n\n"
                    f"— Massage Marketplace"
                ),
                from_email=from_email,
                recipient_list=[provider.user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send renewal reminder to %s", provider.user.email)

    def _send_expiry_email(self, provider):
        from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@massagemarketplace.com"
        )
        name = provider.get_name()

        try:
            send_mail(
                subject="Your subscription has expired — Massage Marketplace",
                message=(
                    f"Hi {name},\n\n"
                    f"Your Massage Marketplace subscription has expired and your profile "
                    f"is no longer visible to clients.\n\n"
                    f"To reactivate your listing, renew your subscription here:\n\n"
                    f"    {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'your-domain.com'}"
                    f"/provider/subscription/\n\n"
                    f"— Massage Marketplace"
                ),
                from_email=from_email,
                recipient_list=[provider.user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send expiry email to %s", provider.user.email)
