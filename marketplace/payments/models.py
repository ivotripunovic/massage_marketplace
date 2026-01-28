from django.db import models
from django.conf import settings
from providers.models import Provider


class SubscriptionPayment(models.Model):
    """Payment record for provider subscriptions."""
    
    PAYMENT_METHOD_CHOICES = (
        ('crypto_bitcoin', 'Bitcoin'),
        ('crypto_ethereum', 'Ethereum'),
        ('crypto_usdc', 'USDC'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='subscription_payments'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=29.99,
        help_text='Subscription cost in USD'
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    reference_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Transaction hash for crypto, transaction ID for bank'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Admin notes'
    )

    class Meta:
        db_table = 'payments_subscription_payment'
        verbose_name = 'Subscription Payment'
        verbose_name_plural = 'Subscription Payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider.user.email} - ${self.amount} - {self.get_status_display()} - {self.created_at.date()}"

    def mark_completed(self):
        """Mark payment as completed."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self):
        """Mark payment as failed."""
        self.status = 'failed'
        self.save()
