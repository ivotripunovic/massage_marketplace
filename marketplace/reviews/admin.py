from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""

    list_display = ("provider_email", "client_name", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("provider__user__email", "client_name", "client_email", "comment")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Provider", {"fields": ("provider",)}),
        (
            "Review Information",
            {"fields": ("client_name", "client_email", "rating", "comment")},
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email

    provider_email.short_description = "Provider Email"
    provider_email.admin_order_field = "provider__user__email"
