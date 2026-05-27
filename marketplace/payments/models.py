from django.db import models
from providers.models import Provider
from payments.nowpayments import SUPPORTED_CURRENCIES


class SubscriptionPayment(models.Model):
    """Payment record for provider subscriptions."""

    PAYMENT_METHOD_CHOICES = tuple(
        (c["code"], c["name"]) for c in SUPPORTED_CURRENCIES
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial", "Partially Paid"),
    )

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="subscription_payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=29.99,
        help_text="Subscription cost in USD",
    )

    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    reference_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Transaction hash for crypto, transaction ID for bank",
    )

    # NOWPayments integration fields
    nowpayments_payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="NOWPayments internal payment ID",
    )
    pay_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Crypto address the provider must send funds to",
    )
    pay_amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Exact crypto amount the provider must send",
    )
    pay_currency = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="NOWPayments currency code (e.g. usdtmatic)",
    )

    invoice_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="NOWPayments hosted invoice URL (encodes address + amount + network; used as QR code content)",
    )

    actually_paid = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Actual crypto amount received (from NOWPayments IPN)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True, help_text="Admin notes")

    class Meta:
        db_table = "payments_subscription_payment"
        verbose_name = "Subscription Payment"
        verbose_name_plural = "Subscription Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider.user.email} - ${self.amount} - {self.get_status_display()} - {self.created_at.date()}"

    def mark_completed(self):
        """Mark payment as completed."""
        from django.utils import timezone

        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self):
        """Mark payment as failed."""
        self.status = "failed"
        self.save()

    def mark_partial(self, actually_paid=None):
        """Mark payment as partially paid and record the amount received."""
        self.status = "partial"
        if actually_paid is not None:
            self.actually_paid = actually_paid
        self.save()
