from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to verify email configuration"

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Email address to send the test email to")

    def handle(self, *args, **options):
        recipient = options["recipient"]
        backend = settings.EMAIL_BACKEND

        self.stdout.write(f"Email backend: {backend}")
        self.stdout.write(f"Sending test email to {recipient}...")

        try:
            send_mail(
                subject="Test Email - Massage Marketplace",
                message="This is a test email. If you received this, email sending is working correctly.",
                from_email=settings.DEFAULT_FROM_EMAIL
                if hasattr(settings, "DEFAULT_FROM_EMAIL")
                else None,
                recipient_list=[recipient],
            )
            self.stdout.write(self.style.SUCCESS("Email sent successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
