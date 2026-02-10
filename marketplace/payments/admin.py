from django.contrib import admin
from .models import SubscriptionPayment


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    """Admin interface for SubscriptionPayment model."""

    list_display = (
        "provider_email",
        "amount",
        "payment_method",
        "status",
        "created_at",
    )
    list_filter = ("payment_method", "status", "created_at")
    search_fields = ("provider__user__email", "reference_id", "notes")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Provider", {"fields": ("provider",)}),
        (
            "Payment Information",
            {"fields": ("amount", "payment_method", "reference_id")},
        ),
        ("Status", {"fields": ("status", "completed_at")}),
        ("Admin Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email

    provider_email.short_description = "Provider Email"
    provider_email.admin_order_field = "provider__user__email"
