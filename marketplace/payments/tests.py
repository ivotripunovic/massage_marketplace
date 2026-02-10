from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from unittest.mock import patch
from users.models import User
from providers.models import Provider
from .models import SubscriptionPayment


class SubscriptionPaymentModelTests(TestCase):
    """Test SubscriptionPayment model functionality."""

    def setUp(self):
        """Set up test provider for payment creation."""
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    def test_payment_creation(self):
        """Test creating a subscription payment."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
        )
        self.assertEqual(payment.amount, 29.99)
        self.assertEqual(payment.status, "pending")

    def test_payment_default_amount(self):
        """Test payment default amount."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="bank_transfer"
        )
        self.assertEqual(payment.amount, 29.99)

    def test_payment_default_status(self):
        """Test payment default status is pending."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_ethereum"
        )
        self.assertEqual(payment.status, "pending")

    def test_payment_with_reference_id(self):
        """Test payment with reference ID (transaction hash)."""
        tx_hash = "0x123abc456def"
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method="crypto_bitcoin",
            reference_id=tx_hash,
            status="completed",
        )
        self.assertEqual(payment.reference_id, tx_hash)

    def test_payment_with_admin_notes(self):
        """Test payment with admin notes."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method="bank_transfer",
            notes="Waiting for bank confirmation",
        )
        self.assertEqual(payment.notes, "Waiting for bank confirmation")

    def test_payment_status_completed(self):
        """Test marking payment as completed."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_usdc"
        )
        self.assertEqual(payment.status, "pending")

        payment.status = "completed"
        payment.completed_at = timezone.now()
        payment.save()

        payment.refresh_from_db()
        self.assertEqual(payment.status, "completed")
        self.assertIsNotNone(payment.completed_at)

    def test_payment_status_failed(self):
        """Test marking payment as failed."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="bank_transfer"
        )
        payment.status = "failed"
        payment.notes = "Bank transfer bounced"
        payment.save()

        payment.refresh_from_db()
        self.assertEqual(payment.status, "failed")

    def test_all_payment_methods(self):
        """Test all payment method choices."""
        payment_methods = [
            "crypto_bitcoin",
            "crypto_ethereum",
            "crypto_usdc",
            "bank_transfer",
        ]
        for i, method in enumerate(payment_methods):
            payment = SubscriptionPayment.objects.create(
                provider=self.provider, payment_method=method, amount=29.99 + i
            )
            self.assertEqual(payment.payment_method, method)

    def test_payment_string_representation(self):
        """Test payment __str__ method."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
        )
        self.assertIn(self.user.email, str(payment))
        self.assertIn("29.99", str(payment))
        self.assertIn("Pending", str(payment))

    def test_multiple_payments_per_provider(self):
        """Test provider can have multiple subscription payments."""
        SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_bitcoin", status="completed"
        )
        SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="bank_transfer", status="pending"
        )
        self.assertEqual(self.provider.subscription_payments.count(), 2)

    def test_payment_has_timestamps(self):
        """Test payment has creation timestamp."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_ethereum"
        )
        self.assertIsNotNone(payment.created_at)
        self.assertIsNone(payment.completed_at)  # Only set when completed

    def test_custom_amount(self):
        """Test payment with custom amount."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, amount=49.99, payment_method="bank_transfer"
        )
        self.assertEqual(payment.amount, 49.99)

    def test_mark_completed(self):
        """Test mark_completed() sets status and completed_at."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_bitcoin"
        )
        self.assertEqual(payment.status, "pending")
        self.assertIsNone(payment.completed_at)

        payment.mark_completed()
        payment.refresh_from_db()

        self.assertEqual(payment.status, "completed")
        self.assertIsNotNone(payment.completed_at)

    def test_mark_failed(self):
        """Test mark_failed() sets status to failed."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="bank_transfer"
        )
        payment.mark_failed()
        payment.refresh_from_db()

        self.assertEqual(payment.status, "failed")

    def test_updated_at_field(self):
        """Test updated_at is set and changes on save."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider, payment_method="crypto_usdc"
        )
        self.assertIsNotNone(payment.updated_at)
        original_updated = payment.updated_at

        payment.notes = "Updated note"
        payment.save()
        payment.refresh_from_db()

        self.assertGreaterEqual(payment.updated_at, original_updated)


class AdminPaymentListViewTests(TestCase):
    """Test AdminPaymentListView for admin payment management."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )

        # Create provider and payment
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )

        self.payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
        )

    def test_payment_list_requires_login(self):
        """Test that payment list requires authentication."""
        response = self.client.get(reverse("admin_payments"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_payment_list_requires_admin(self):
        """Test that non-admin cannot access payment list."""
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.get(reverse("admin_payments"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_payment_list_admin_can_access(self):
        """Test that admin can access payment list."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_payments"))
        self.assertEqual(response.status_code, 200)

    def test_payment_list_displays_payments(self):
        """Test that payment list displays pending payments."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_payments"))
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, "29.99")

    def test_payment_list_filter_by_status(self):
        """Test filtering payments by status."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_payments") + "?status=pending")
        self.assertContains(response, self.provider_user.email)

        response = self.client.get(reverse("admin_payments") + "?status=completed")
        self.assertNotContains(response, self.provider_user.email)

    def test_payment_list_filter_by_method(self):
        """Test filtering payments by method."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_payments") + "?method=crypto_bitcoin")
        self.assertContains(response, self.provider_user.email)

        response = self.client.get(reverse("admin_payments") + "?method=bank_transfer")
        self.assertNotContains(response, self.provider_user.email)

    def test_payment_list_search(self):
        """Test searching payments by email."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_payments") + f"?search={self.provider_user.email}"
        )
        self.assertContains(response, self.provider_user.email)


class AdminPaymentDetailViewTests(TestCase):
    """Test AdminPaymentDetailView for viewing payment details."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )

        # Create provider and payment
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )

        self.payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
            reference_id="0x123abc",
        )

    def test_payment_detail_requires_login(self):
        """Test that payment detail requires authentication."""
        response = self.client.get(
            reverse("admin_payment_detail", args=[self.payment.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_payment_detail_requires_admin(self):
        """Test that non-admin cannot view payment detail."""
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.get(
            reverse("admin_payment_detail", args=[self.payment.id])
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_payment_detail_admin_can_access(self):
        """Test that admin can view payment detail."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_payment_detail", args=[self.payment.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_payment_detail_displays_info(self):
        """Test that payment detail displays all information."""
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_payment_detail", args=[self.payment.id])
        )

        self.assertContains(response, "29.99")
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, "0x123abc")
        self.assertContains(response, "Pending")


class AdminDashboardViewTests(TestCase):
    """Test admin dashboard view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890", subscription_status="active"
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_admin(self):
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_loads_for_admin(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/dashboard.html")

    def test_dashboard_shows_metrics(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertIn("total_providers", response.context)
        self.assertIn("active_providers", response.context)
        self.assertIn("total_revenue", response.context)
        self.assertIn("pending_payments", response.context)
        self.assertIn("total_services", response.context)
        self.assertIn("total_reviews", response.context)

    def test_dashboard_provider_counts(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.context["total_providers"], 1)
        self.assertEqual(response.context["active_providers"], 1)

    def test_dashboard_has_navigation_links(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertContains(response, reverse("admin_providers"))
        self.assertContains(response, reverse("admin_payments"))
        self.assertContains(response, reverse("admin_analytics"))


class AdminProviderDetailViewTests(TestCase):
    """Test admin provider detail view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890", subscription_status="active"
        )

    def test_detail_requires_admin(self):
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.get(
            reverse("admin_provider_detail", args=[self.provider.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_detail_loads_for_admin(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_provider_detail", args=[self.provider.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/provider_detail.html")

    def test_detail_shows_provider_info(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_provider_detail", args=[self.provider.pk])
        )
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, "+1234567890")

    def test_detail_shows_services(self):
        from providers.models import Service

        Service.objects.create(
            provider=self.provider,
            service_type="swedish",
            description="Swedish massage",
            price=60.00,
            duration_minutes=60,
        )
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_provider_detail", args=[self.provider.pk])
        )
        self.assertContains(response, "Swedish")

    def test_detail_shows_payments(self):
        SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
        )
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(
            reverse("admin_provider_detail", args=[self.provider.pk])
        )
        self.assertContains(response, "29.99")


class AdminProviderSuspendViewTests(TestCase):
    """Test admin provider suspend/activate actions."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890", subscription_status="active"
        )

    def test_suspend_requires_admin(self):
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.post(
            reverse("admin_provider_status", args=[self.provider.pk]),
            {"action": "suspend"},
        )
        self.assertEqual(response.status_code, 403)

    def test_suspend_provider(self):
        self.client.login(email="admin@test.com", password="pass")
        self.client.post(
            reverse("admin_provider_status", args=[self.provider.pk]),
            {"action": "suspend"},
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "suspended")

    def test_activate_provider(self):
        self.provider.subscription_status = "suspended"
        self.provider.save()

        self.client.login(email="admin@test.com", password="pass")
        self.client.post(
            reverse("admin_provider_status", args=[self.provider.pk]),
            {"action": "activate"},
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")

    def test_deactivate_provider(self):
        self.client.login(email="admin@test.com", password="pass")
        self.client.post(
            reverse("admin_provider_status", args=[self.provider.pk]),
            {"action": "deactivate"},
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "inactive")

    def test_suspend_redirects_to_detail(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.post(
            reverse("admin_provider_status", args=[self.provider.pk]),
            {"action": "suspend"},
        )
        self.assertRedirects(
            response, reverse("admin_provider_detail", args=[self.provider.pk])
        )


class AdminPaymentApproveViewTests(TestCase):
    """Test admin payment approve/reject actions."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890", subscription_status="active"
        )
        self.payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
        )

    def test_approve_requires_admin(self):
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.post(
            reverse("admin_payment_action", args=[self.payment.pk]),
            {"action": "approve"},
        )
        self.assertEqual(response.status_code, 403)

    def test_approve_payment(self):
        self.client.login(email="admin@test.com", password="pass")
        self.client.post(
            reverse("admin_payment_action", args=[self.payment.pk]),
            {"action": "approve"},
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "completed")
        self.assertIsNotNone(self.payment.completed_at)

    def test_reject_payment(self):
        self.client.login(email="admin@test.com", password="pass")
        self.client.post(
            reverse("admin_payment_action", args=[self.payment.pk]),
            {"action": "reject", "notes": "Invalid transaction"},
        )
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "failed")
        self.assertEqual(self.payment.notes, "Invalid transaction")

    def test_approve_redirects_to_detail(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.post(
            reverse("admin_payment_action", args=[self.payment.pk]),
            {"action": "approve"},
        )
        self.assertRedirects(
            response, reverse("admin_payment_detail", args=[self.payment.pk])
        )


class AdminAnalyticsViewTests(TestCase):
    """Test admin analytics view."""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.provider_user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890", subscription_status="active"
        )

    def test_analytics_requires_admin(self):
        self.client.login(email="provider@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(response.status_code, 403)

    def test_analytics_loads_for_admin(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/analytics.html")

    def test_analytics_has_metrics(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        self.assertIn("total_providers", response.context)
        self.assertIn("active_providers", response.context)
        self.assertIn("conversion_rate", response.context)
        self.assertIn("signup_data", response.context)
        self.assertIn("revenue_data", response.context)
        self.assertIn("service_type_data", response.context)

    def test_analytics_conversion_rate(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        # 1 active out of 1 total = 100%
        self.assertEqual(response.context["conversion_rate"], 100.0)

    def test_analytics_signup_data_has_6_months(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(len(response.context["signup_data"]), 6)

    def test_analytics_revenue_data_has_6_months(self):
        self.client.login(email="admin@test.com", password="pass")
        response = self.client.get(reverse("admin_analytics"))
        self.assertEqual(len(response.context["revenue_data"]), 6)


class MonitorCryptoPaymentsCommandTests(TestCase):
    """Test monitor_crypto_payments management command."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="active"
        )

    def test_command_finds_pending_crypto_payments(self):
        """Test that command finds pending crypto payments with tx hashes."""
        from io import StringIO
        from django.core.management import call_command

        SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
            reference_id="0xabc123",
        )

        out = StringIO()
        call_command("monitor_crypto_payments", stdout=out)
        output = out.getvalue()
        self.assertIn("Found 1 pending crypto payment", output)

    def test_command_ignores_completed_payments(self):
        """Test that command ignores already completed payments."""
        from io import StringIO
        from django.core.management import call_command

        SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="completed",
            reference_id="0xabc123",
        )

        out = StringIO()
        call_command("monitor_crypto_payments", stdout=out)
        output = out.getvalue()
        self.assertIn("Found 0 pending crypto payment", output)

    def test_command_ignores_bank_transfers(self):
        """Test that command ignores bank transfer payments."""
        from io import StringIO
        from django.core.management import call_command

        SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="bank_transfer",
            status="pending",
            reference_id="REF123",
        )

        out = StringIO()
        call_command("monitor_crypto_payments", stdout=out)
        output = out.getvalue()
        self.assertIn("Found 0 pending crypto payment", output)

    def test_command_dry_run(self):
        """Test dry run mode doesn't update payments."""
        from io import StringIO
        from django.core.management import call_command

        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method="crypto_bitcoin",
            status="pending",
            reference_id="0xabc123",
        )

        out = StringIO()
        call_command("monitor_crypto_payments", "--dry-run", stdout=out)

        payment.refresh_from_db()
        # Status should remain pending (stub returns not verified)
        self.assertEqual(payment.status, "pending")

    def test_command_reports_verification_summary(self):
        """Test that command reports summary at end."""
        from io import StringIO
        from django.core.management import call_command

        out = StringIO()
        call_command("monitor_crypto_payments", stdout=out)
        output = out.getvalue()
        self.assertIn("Done.", output)


class SubscriptionConfirmationEmailTests(TestCase):
    """Test subscription confirmation email functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    @patch("django.core.mail.send_mail")
    def test_subscription_email_sent_on_activation(self, mock_send):
        """Test that email is sent when subscription is activated."""

        # Create a mock request
        self.provider.activate_subscription("crypto_bitcoin")

        # Verify provider is active
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_subscription_email_template_exists(self):
        """Test that subscription confirmation email template exists."""
        from django.template.loader import get_template

        template = get_template("emails/subscription_confirmation.html")
        self.assertIsNotNone(template)

    def test_subscription_confirmation_text_template_exists(self):
        """Test that subscription confirmation text template exists."""
        from django.template.loader import get_template

        template = get_template("emails/subscription_confirmation.txt")
        self.assertIsNotNone(template)
