from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta, date


class Provider(models.Model):
    """Provider profile model."""
    
    SUBSCRIPTION_STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('crypto', 'Cryptocurrency'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_profile'
    )
    
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    photo = models.ImageField(
        upload_to='providers/photos/',
        blank=True,
        null=True
    )

    # Location fields
    country = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Country where services are provided'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='City where services are provided'
    )
    
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='inactive'
    )
    
    subscription_payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True
    )
    
    subscription_renewal_date = models.DateField(blank=True, null=True)
    
    crypto_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Bitcoin/Ethereum address'
    )
    
    bank_account_encrypted = models.TextField(
        blank=True,
        null=True,
        help_text='Encrypted bank account details'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'providers_provider'
        verbose_name = 'Provider'
        verbose_name_plural = 'Providers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription_status']),
            models.Index(fields=['subscription_status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_subscription_status_display()}"
    
    def is_subscription_active(self):
        """Check if subscription is active."""
        return self.subscription_status == 'active'
    
    def activate_subscription(self, payment_method):
        """Activate subscription for 30 days from today."""
        self.subscription_status = 'active'
        self.subscription_payment_method = payment_method
        self.subscription_renewal_date = date.today() + timedelta(days=30)
        self.save()
    
    def deactivate_subscription(self):
        """Deactivate subscription."""
        self.subscription_status = 'inactive'
        self.save()

    def average_rating(self):
        """Calculate average rating from reviews."""
        from django.db.models import Avg
        from reviews.models import Review

        avg = Review.objects.filter(provider=self).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def get_name(self):
        """Get provider display name."""
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.email.split('@')[0]


class Service(models.Model):
    """Service offered by a provider."""
    
    SERVICE_TYPE_CHOICES = (
        ('swedish', 'Swedish Massage'),
        ('deep_tissue', 'Deep Tissue Massage'),
        ('thai', 'Thai Massage'),
        ('reflexology', 'Reflexology'),
        ('hot_stone', 'Hot Stone Massage'),
        ('aromatherapy', 'Aromatherapy Massage'),
    )
    
    DURATION_CHOICES = (
        (30, '30 minutes'),
        (60, '60 minutes'),
        (90, '90 minutes'),
    )
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='services'
    )
    
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES
    )
    
    description = models.TextField(blank=True, null=True)
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Price must be at least $5.00'
    )
    
    duration_minutes = models.IntegerField(
        choices=DURATION_CHOICES
    )
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'providers_service'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        unique_together = ('provider', 'service_type')
    
    def __str__(self):
        return f"{self.provider.user.email} - {self.get_service_type_display()} - ${self.price}"
    
    def clean(self):
        """Validate service fields."""
        if self.price < 5.00:
            raise ValidationError({'price': 'Price must be at least $5.00'})
        
        if self.duration_minutes not in dict(self.DURATION_CHOICES).keys():
            raise ValidationError(
                {'duration_minutes': 'Duration must be 30, 60, or 90 minutes'}
            )
    
    def save(self, *args, **kwargs):
        """Validate before saving."""
        self.full_clean()
        super().save(*args, **kwargs)


class Certification(models.Model):
    """Certification or credential for a provider."""
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='certifications'
    )
    
    name = models.CharField(
        max_length=255,
        help_text='e.g., Licensed Massage Therapist'
    )
    
    image = models.ImageField(upload_to='providers/certifications/')
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'providers_certification'
        verbose_name = 'Certification'
        verbose_name_plural = 'Certifications'
    
    def __str__(self):
        return f"{self.provider.user.email} - {self.name}"
