from django.db import models
from django.conf import settings
from django.utils.text import slugify
from datetime import timedelta, date


class Continent(models.Model):
    """Continent model for geographical organization."""

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(
        max_length=2, unique=True, help_text="2-character continent code"
    )
    display_order = models.IntegerField(
        default=0, help_text="Order for display in lists"
    )

    class Meta:
        db_table = "providers_continent"
        verbose_name = "Continent"
        verbose_name_plural = "Continents"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class Country(models.Model):
    """Country model - excludes United States."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=2, unique=True, help_text="ISO 3166-1 alpha-2 country code"
    )
    continent = models.ForeignKey(
        Continent, on_delete=models.CASCADE, related_name="countries"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this country is available for selection"
    )
    display_order = models.IntegerField(
        default=0, help_text="Order for display within continent"
    )

    class Meta:
        db_table = "providers_country"
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["continent", "display_order", "name"]
        indexes = [
            models.Index(fields=["continent", "name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class City(models.Model):
    """City model with population and geographic data."""

    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="cities"
    )
    population = models.IntegerField(null=True, blank=True, help_text="City population")
    is_capital = models.BooleanField(
        default=False, help_text="Whether this is a capital city"
    )
    is_major_city = models.BooleanField(
        default=False,
        help_text="Whether this is a major city (pop > 500k or important)",
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude coordinate",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude coordinate",
    )

    class Meta:
        db_table = "providers_city"
        verbose_name = "City"
        verbose_name_plural = "Cities"
        ordering = ["-is_capital", "-is_major_city", "-population", "name"]
        unique_together = ("name", "country")
        indexes = [
            models.Index(fields=["country", "name"]),
            models.Index(fields=["is_major_city"]),
        ]

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class Provider(models.Model):
    """Provider profile model."""

    SUBSCRIPTION_STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("crypto", "Cryptocurrency"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )

    slug = models.SlugField(max_length=200, unique=True, blank=True)

    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    phone_hours = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Good time to call, e.g. 10:00 – 18:00",
    )
    photo = models.ImageField(upload_to="providers/photos/", blank=True, null=True)
    profile_video = models.FileField(
        upload_to="providers/videos/", blank=True, null=True
    )

    # Location fields (ForeignKey)
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="providers",
        help_text="Country where services are provided",
    )
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="providers",
        help_text="City where services are provided",
    )

    subscription_status = models.CharField(
        max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default="inactive"
    )

    subscription_payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True
    )

    subscription_renewal_date = models.DateField(blank=True, null=True)

    crypto_address = models.CharField(
        max_length=255, blank=True, null=True, help_text="Bitcoin/Ethereum address"
    )

    map_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Cached latitude for map display (geocoded from district/city)",
    )
    map_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Cached longitude for map display (geocoded from district/city)",
    )

    preference_comment = models.TextField(
        blank=True,
        default="",
        help_text="General comment displayed at bottom of preferences",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "providers_provider"
        verbose_name = "Provider"
        verbose_name_plural = "Providers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["subscription_status"]),
            models.Index(fields=["subscription_status", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_subscription_status_display()}"

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            args = ()
            kwargs = {}
        self.slug = slugify(self.get_name()) + "-" + str(self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("provider_detail", kwargs={"slug": self.slug})

    def is_subscription_active(self):
        """Check if subscription is active."""
        return self.subscription_status == "active"

    def activate_subscription(self, payment_method):
        """Activate subscription for 30 days from today."""
        self.subscription_status = "active"
        self.subscription_payment_method = payment_method
        self.subscription_renewal_date = date.today() + timedelta(days=30)
        self.save()

    def deactivate_subscription(self):
        """Deactivate subscription."""
        self.subscription_status = "inactive"
        self.save()

    def average_rating(self):
        """Calculate average rating from all category ratings across reviews."""
        from django.db.models import Avg
        from reviews.models import ReviewCategoryRating

        avg = ReviewCategoryRating.objects.filter(review__provider=self).aggregate(
            Avg("rating")
        )["rating__avg"]
        return round(avg, 1) if avg else 0

    def get_name(self):
        """Get provider display name."""
        if self.user.first_name or self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.email.split("@")[0]


class ProviderGalleryImage(models.Model):
    """Gallery image for a provider's profile."""

    MAX_IMAGES_PER_PROVIDER = 10

    provider = models.ForeignKey(
        "Provider", on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ImageField(upload_to="providers/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "providers_galleryimage"
        verbose_name = "Gallery Image"
        verbose_name_plural = "Gallery Images"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Gallery image for {self.provider.user.email} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class ProviderAttributeDefinition(models.Model):
    """Admin-defined custom attributes that providers can fill in."""

    DATA_TYPE_STRING = "string"
    DATA_TYPE_INTEGER = "int"
    DATA_TYPE_BOOLEAN = "bool"

    DATA_TYPE_CHOICES = (
        (DATA_TYPE_STRING, "String"),
        (DATA_TYPE_INTEGER, "Integer"),
        (DATA_TYPE_BOOLEAN, "Boolean"),
    )

    name = models.CharField(max_length=150, unique=True)
    data_type = models.CharField(
        max_length=10,
        choices=DATA_TYPE_CHOICES,
        default=DATA_TYPE_STRING,
        help_text="Controls how providers input this attribute",
    )
    display_order = models.PositiveIntegerField(default=0)
    show_on_card = models.BooleanField(
        default=False,
        help_text="Whether this attribute should be highlighted on the provider card",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this attribute from provider-facing forms",
    )

    class Meta:
        db_table = "providers_attribute_definition"
        verbose_name = "Provider Attribute Definition"
        verbose_name_plural = "Provider Attribute Definitions"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class ProviderAttributeValue(models.Model):
    """Stores provider-specific values for admin-defined attributes."""

    provider = models.ForeignKey(
        "Provider", on_delete=models.CASCADE, related_name="attribute_values"
    )
    definition = models.ForeignKey(
        ProviderAttributeDefinition, on_delete=models.CASCADE, related_name="values"
    )
    value_text = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "providers_attribute_value"
        verbose_name = "Provider Attribute Value"
        verbose_name_plural = "Provider Attribute Values"
        unique_together = ("provider", "definition")

    def __str__(self):
        return f"{self.definition.name} → {self.provider.get_name()}"

    def get_typed_value(self):
        """Return the stored value in the correct Python type."""
        raw = self.value_text
        if raw in (None, ""):
            return None

        dtype = self.definition.data_type
        if dtype == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            normalized = raw.strip().lower()
            if normalized in ("1", "true", "yes", "on"):
                return True
            if normalized in ("0", "false", "no", "off"):
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
        if typed in (None, ""):
            return None

        if self.definition.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            return "Yes" if typed else "No"

        return str(typed)


class ProviderPricing(models.Model):
    """Structured pricing grid for a provider (apartment/outside × day/night × 1h/2h)."""

    provider = models.OneToOneField(
        Provider, on_delete=models.CASCADE, related_name="pricing"
    )

    apartment_available = models.BooleanField(default=True)
    outside_available = models.BooleanField(default=True)

    apartment_day_1h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    apartment_day_2h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    apartment_night_1h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    apartment_night_whole = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    outside_day_1h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    outside_day_2h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    outside_night_1h = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    outside_night_whole = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    day_note = models.CharField(max_length=120, blank=True, default="")
    night_note = models.CharField(max_length=120, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "providers_pricing"
        verbose_name = "Provider Pricing"
        verbose_name_plural = "Provider Pricings"

    def __str__(self):
        return f"Pricing for {self.provider.get_name()}"


class PreferenceGroup(models.Model):
    """Admin-defined top-level preference group (e.g., 'Massage')."""

    name = models.CharField(max_length=150, unique=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "providers_preference_group"
        verbose_name = "Preference Group"
        verbose_name_plural = "Preference Groups"
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name


class PreferenceSubgroup(models.Model):
    """Admin-defined option within a preference group (e.g., 'Classical', 'Erotic')."""

    group = models.ForeignKey(
        PreferenceGroup, on_delete=models.CASCADE, related_name="subgroups"
    )
    name = models.CharField(max_length=150)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "providers_preference_subgroup"
        verbose_name = "Preference Subgroup"
        verbose_name_plural = "Preference Subgroups"
        ordering = ["display_order", "name"]
        unique_together = ("group", "name")

    def __str__(self):
        return f"{self.group.name} → {self.name}"


class PreferenceSubgroupOption(models.Model):
    """Admin-defined predefined text for a subgroup (e.g., '+10$ for 30min more')."""

    subgroup = models.ForeignKey(
        PreferenceSubgroup, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "providers_preference_subgroup_option"
        verbose_name = "Preference Subgroup Option"
        verbose_name_plural = "Preference Subgroup Options"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.subgroup}: {self.text}"


class ProviderPreference(models.Model):
    """Per-provider toggle for each subgroup."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="preferences"
    )
    subgroup = models.ForeignKey(
        PreferenceSubgroup,
        on_delete=models.CASCADE,
        related_name="provider_preferences",
    )
    is_checked = models.BooleanField(default=False)

    class Meta:
        db_table = "providers_provider_preference"
        verbose_name = "Provider Preference"
        verbose_name_plural = "Provider Preferences"
        unique_together = ("provider", "subgroup")

    def __str__(self):
        status = "Yes" if self.is_checked else "No"
        return f"{self.provider.get_name()} – {self.subgroup.name}: {status}"


class ProviderPreferenceCustomOption(models.Model):
    """Provider free-text option for a subgroup."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="preference_custom_options"
    )
    subgroup = models.ForeignKey(
        PreferenceSubgroup, on_delete=models.CASCADE, related_name="custom_options"
    )
    text = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "providers_preference_custom_option"
        verbose_name = "Provider Preference Custom Option"
        verbose_name_plural = "Provider Preference Custom Options"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.provider.get_name()} – {self.subgroup.name}: {self.text}"


class ProviderCustomPreference(models.Model):
    """Provider-created preference item shown as its own subgroup in an 'Other' group."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="custom_preferences"
    )
    name = models.CharField(max_length=150)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "providers_custom_preference"
        verbose_name = "Provider Custom Preference"
        verbose_name_plural = "Provider Custom Preferences"
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.provider.get_name()} – {self.name}"
