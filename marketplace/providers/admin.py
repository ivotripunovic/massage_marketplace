from django.contrib import admin
from .models import (
    Provider,
    ProviderGalleryImage,
    ProviderAttributeDefinition,
    ProviderAttributeValue,
    Continent,
    Country,
    City,
    PreferenceGroup,
    PreferenceSubgroup,
    PreferenceSubgroupOption,
)


class GalleryImageInline(admin.TabularInline):
    """Inline editor for gallery images."""

    model = ProviderGalleryImage
    extra = 1
    fields = ("image", "caption", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(Continent)
class ContinentAdmin(admin.ModelAdmin):
    """Admin interface for Continent model."""

    list_display = ("name", "code", "display_order", "country_count")
    list_editable = ("display_order",)
    ordering = ("display_order", "name")

    def country_count(self, obj):
        return obj.countries.count()

    country_count.short_description = "Countries"


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin interface for Country model."""

    list_display = ("name", "code", "continent", "is_active", "city_count")
    list_filter = ("continent", "is_active")
    search_fields = ("name", "code")
    list_editable = ("is_active",)
    ordering = ("continent", "name")

    def city_count(self, obj):
        return obj.cities.count()

    city_count.short_description = "Cities"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """Admin interface for City model."""

    list_display = ("name", "country", "population", "is_capital", "is_major_city")
    list_filter = ("country__continent", "is_capital", "is_major_city")
    search_fields = ("name", "country__name")
    list_editable = ("is_capital", "is_major_city")
    autocomplete_fields = ("country",)
    ordering = ("country", "-is_capital", "-is_major_city", "name")


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin interface for Provider model."""

    list_display = (
        "user_email",
        "phone",
        "location_display",
        "subscription_status",
        "subscription_payment_method",
        "created_at",
    )
    list_filter = (
        "subscription_status",
        "subscription_payment_method",
        "country__continent",
        "country",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone",
        "country__name",
        "city__name",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = [GalleryImageInline]
    autocomplete_fields = ("country", "city")

    fieldsets = (
        ("User Information", {"fields": ("user",)}),
        ("Personal Information", {"fields": ("bio", "phone", "photo")}),
        (
            "Location",
            {
                "fields": ("country", "city"),
            },
        ),
        (
            "Subscription",
            {
                "fields": (
                    "subscription_status",
                    "subscription_payment_method",
                    "subscription_renewal_date",
                )
            },
        ),
        (
            "Payment Information",
            {
                "fields": ("crypto_address", "bank_account_encrypted"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def location_display(self, obj):
        """Display location in list view."""
        if obj.city and obj.country:
            return f"{obj.city.name}, {obj.country.name}"
        if obj.country:
            return obj.country.name
        return "-"

    location_display.short_description = "Location"

    actions = ["deactivate_subscriptions", "suspend_accounts", "activate_subscriptions"]

    def user_email(self, obj):
        """Display user email in list view."""
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def deactivate_subscriptions(self, request, queryset):
        """Bulk action to deactivate subscriptions."""
        count = queryset.update(subscription_status="inactive")
        self.message_user(request, f"{count} provider(s) subscription(s) deactivated.")

    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"

    def suspend_accounts(self, request, queryset):
        """Bulk action to suspend provider accounts."""
        count = queryset.update(subscription_status="suspended")
        self.message_user(request, f"{count} provider account(s) suspended.")

    suspend_accounts.short_description = "Suspend selected accounts"

    def activate_subscriptions(self, request, queryset):
        """Bulk action to activate subscriptions."""
        from datetime import timedelta
        from django.utils import timezone

        count = 0
        for provider in queryset:
            if provider.subscription_status != "active":
                provider.subscription_status = "active"
                provider.subscription_renewal_date = timezone.localdate() + timedelta(days=30)
                provider.save()
                count += 1
        self.message_user(request, f"{count} provider subscription(s) activated.")

    activate_subscriptions.short_description = "Activate selected subscriptions"


@admin.register(ProviderAttributeDefinition)
class ProviderAttributeDefinitionAdmin(admin.ModelAdmin):
    """Admin interface for provider attribute definitions."""

    list_display = (
        "name",
        "data_type",
        "show_on_card",
        "is_active",
        "display_order",
    )
    list_editable = ("show_on_card", "is_active", "display_order")
    list_filter = ("data_type", "show_on_card", "is_active")
    search_fields = ("name",)
    ordering = ("display_order", "name")


@admin.register(ProviderAttributeValue)
class ProviderAttributeValueAdmin(admin.ModelAdmin):
    """Admin interface for provider attribute values."""

    list_display = ("provider_email", "definition", "value_display", "updated_at")
    list_select_related = ("provider", "definition")
    list_filter = ("definition",)
    search_fields = (
        "provider__user__email",
        "definition__name",
        "value_text",
    )
    readonly_fields = ("updated_at",)
    raw_id_fields = ("provider",)

    def provider_email(self, obj):
        return obj.provider.user.email

    provider_email.short_description = "Provider Email"

    def value_display(self, obj):
        return obj.formatted_value() or obj.value_text or "-"

    value_display.short_description = "Value"


@admin.register(ProviderGalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """Admin interface for ProviderGalleryImage model."""

    list_display = ("provider_email", "caption", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("provider__user__email", "caption")
    readonly_fields = ("uploaded_at",)

    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email

    provider_email.short_description = "Provider Email"
    provider_email.admin_order_field = "provider__user__email"


class PreferenceSubgroupInline(admin.TabularInline):
    model = PreferenceSubgroup
    extra = 1
    fields = ("name", "display_order", "is_active")


class PreferenceSubgroupOptionInline(admin.TabularInline):
    model = PreferenceSubgroupOption
    extra = 1
    fields = ("text", "display_order")


@admin.register(PreferenceGroup)
class PreferenceGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active", "subgroup_count")
    list_editable = ("display_order", "is_active")
    ordering = ("display_order", "name")
    inlines = [PreferenceSubgroupInline]

    def subgroup_count(self, obj):
        return obj.subgroups.count()

    subgroup_count.short_description = "Subgroups"


@admin.register(PreferenceSubgroup)
class PreferenceSubgroupAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "display_order", "is_active")
    list_filter = ("group",)
    list_editable = ("display_order", "is_active")
    ordering = ("group__display_order", "display_order", "name")
    inlines = [PreferenceSubgroupOptionInline]
