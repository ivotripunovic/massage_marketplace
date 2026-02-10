from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from datetime import timedelta, date


class Continent(models.Model):
    """Continent model for geographical organization."""

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=2, unique=True, help_text='2-character continent code')
    display_order = models.IntegerField(default=0, help_text='Order for display in lists')

    class Meta:
        db_table = 'providers_continent'
        verbose_name = 'Continent'
        verbose_name_plural = 'Continents'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Country(models.Model):
    """Country model - excludes United States."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=2,
        unique=True,
        help_text='ISO 3166-1 alpha-2 country code'
    )
    continent = models.ForeignKey(
        Continent,
        on_delete=models.CASCADE,
        related_name='countries'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this country is available for selection'
    )
    display_order = models.IntegerField(
        default=0,
        help_text='Order for display within continent'
    )

    class Meta:
        db_table = 'providers_country'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ['continent', 'display_order', 'name']
        indexes = [
            models.Index(fields=['continent', 'name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class City(models.Model):
    """City model with population and geographic data."""

    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name='cities'
    )
    population = models.IntegerField(
        null=True,
        blank=True,
        help_text='City population'
    )
    is_capital = models.BooleanField(
        default=False,
        help_text='Whether this is a capital city'
    )
    is_major_city = models.BooleanField(
        default=False,
        help_text='Whether this is a major city (pop > 500k or important)'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='Longitude coordinate'
    )

    class Meta:
        db_table = 'providers_city'
        verbose_name = 'City'
        verbose_name_plural = 'Cities'
        ordering = ['-is_capital', '-is_major_city', '-population', 'name']
        unique_together = ('name', 'country')
        indexes = [
            models.Index(fields=['country', 'name']),
            models.Index(fields=['is_major_city']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


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

    slug = models.SlugField(max_length=200, unique=True, blank=True)

    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    photo = models.ImageField(
        upload_to='providers/photos/',
        blank=True,
        null=True
    )

    # Location fields (ForeignKey)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers',
        help_text='Country where services are provided'
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='providers',
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

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            args = ()
            kwargs = {}
        self.slug = slugify(self.get_name()) + '-' + str(self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('provider_detail', kwargs={'slug': self.slug})

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


class ProviderGalleryImage(models.Model):
    """Gallery image for a provider's profile."""

    MAX_IMAGES_PER_PROVIDER = 10

    provider = models.ForeignKey(
        'Provider',
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = models.ImageField(upload_to='providers/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'providers_galleryimage'
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Gallery image for {self.provider.user.email} ({self.uploaded_at.strftime('%Y-%m-%d')})"


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


class ProviderAttributeDefinition(models.Model):
    """Admin-defined custom attributes that providers can fill in."""

    DATA_TYPE_STRING = 'string'
    DATA_TYPE_INTEGER = 'int'
    DATA_TYPE_BOOLEAN = 'bool'

    DATA_TYPE_CHOICES = (
        (DATA_TYPE_STRING, 'String'),
        (DATA_TYPE_INTEGER, 'Integer'),
        (DATA_TYPE_BOOLEAN, 'Boolean'),
    )

    name = models.CharField(max_length=150, unique=True)
    data_type = models.CharField(
        max_length=10,
        choices=DATA_TYPE_CHOICES,
        default=DATA_TYPE_STRING,
        help_text='Controls how providers input this attribute'
    )
    display_order = models.PositiveIntegerField(default=0)
    show_on_card = models.BooleanField(
        default=False,
        help_text='Whether this attribute should be highlighted on the provider card'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Uncheck to hide this attribute from provider-facing forms'
    )

    class Meta:
        db_table = 'providers_attribute_definition'
        verbose_name = 'Provider Attribute Definition'
        verbose_name_plural = 'Provider Attribute Definitions'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ProviderAttributeValue(models.Model):
    """Stores provider-specific values for admin-defined attributes."""

    provider = models.ForeignKey(
        'Provider',
        on_delete=models.CASCADE,
        related_name='attribute_values'
    )
    definition = models.ForeignKey(
        ProviderAttributeDefinition,
        on_delete=models.CASCADE,
        related_name='values'
    )
    value_text = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'providers_attribute_value'
        verbose_name = 'Provider Attribute Value'
        verbose_name_plural = 'Provider Attribute Values'
        unique_together = ('provider', 'definition')

    def __str__(self):
        return f"{self.definition.name} → {self.provider.get_name()}"

    def get_typed_value(self):
        """Return the stored value in the correct Python type."""
        raw = self.value_text
        if raw in (None, ''):
            return None

        dtype = self.definition.data_type
        if dtype == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            normalized = raw.strip().lower()
            if normalized in ('1', 'true', 'yes', 'on'):
                return True
            if normalized in ('0', 'false', 'no', 'off'):
                return False
            return None

        if dtype == ProviderAttributeDefinition.DATA_TYPE_INTEGER:
            try:
                return int(raw)
            except (ValueError, TypeError):
                return None

        return raw

    def formatted_value(self):
        """Return a human-readable representation for UI components."""
        typed = self.get_typed_value()
        if typed in (None, ''):
            return None

        if self.definition.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            return 'Yes' if typed else 'No'

        return str(typed)

