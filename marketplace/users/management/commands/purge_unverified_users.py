"""Management command to delete accounts that never verified their email.

Intended to run daily via cron:
    30 1 * * * deploy /opt/massage_marketplace/venv/bin/python \
        /opt/massage_marketplace/marketplace/manage.py purge_unverified_users

Each deleted account is logged (email, user_type, created_at) to the "users"
logger and printed to stdout, so the cron log file keeps a permanent record.
Admin accounts are never touched.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User

logger = logging.getLogger(__name__)

DEFAULT_DAYS = 7


class Command(BaseCommand):
    help = "Delete provider/client accounts still unverified after N days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=DEFAULT_DAYS,
            help=f"Delete accounts unverified for more than this many days (default {DEFAULT_DAYS})",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be deleted without deleting anything",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(days=options["days"])

        users = User.objects.filter(
            is_email_verified=False,
            user_type__in=["provider", "client"],
            created_at__lt=cutoff,
        ).order_by("created_at")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made"))

        count = 0
        for user in users:
            self.stdout.write(
                f"{'Would delete' if dry_run else 'Deleting'} {user.email} "
                f"({user.user_type}, created {user.created_at:%Y-%m-%d %H:%M})"
            )
            if not dry_run:
                logger.info(
                    "Purged unverified user",
                    extra={
                        "user_id": user.pk,
                        "email": user.email,
                        "user_type": user.user_type,
                        "created_at": user.created_at.isoformat(),
                    },
                )
                user.delete()
            count += 1

        verb = "Would delete" if dry_run else "Deleted"
        self.stdout.write(self.style.SUCCESS(f"{verb} {count} unverified account(s)"))
