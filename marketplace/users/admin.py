from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""

    list_display = ("email", "user_type", "is_email_verified", "is_staff", "created_at")
    list_filter = (
        "user_type",
        "is_email_verified",
        "is_staff",
        "is_active",
        "created_at",
    )
    search_fields = ("email", "phone_number", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone_number")}),
        ("User Type", {"fields": ("user_type",)}),
        (
            "Email Verification",
            {"fields": ("is_email_verified", "email_verification_token")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "user_type"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")
