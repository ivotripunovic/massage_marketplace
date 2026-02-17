from django.contrib import admin
from .models import Review, ReviewCategory, ReviewCategoryRating, ReviewReply


@admin.register(ReviewCategory)
class ReviewCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    list_display_links = ("name",)
    ordering = ("display_order", "name")


class ReviewCategoryRatingInline(admin.TabularInline):
    model = ReviewCategoryRating
    extra = 0
    readonly_fields = ("category", "rating")


class ReviewReplyInline(admin.StackedInline):
    model = ReviewReply
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("provider_email", "client_email", "category_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("provider__user__email", "client__email", "comment")
    readonly_fields = ("created_at",)
    inlines = [ReviewCategoryRatingInline, ReviewReplyInline]

    fieldsets = (
        ("Provider", {"fields": ("provider",)}),
        ("Review Information", {"fields": ("client", "comment")}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def provider_email(self, obj):
        return obj.provider.user.email

    provider_email.short_description = "Provider"
    provider_email.admin_order_field = "provider__user__email"

    def client_email(self, obj):
        return obj.client.email

    client_email.short_description = "Client"
    client_email.admin_order_field = "client__email"

    def category_count(self, obj):
        return obj.category_ratings.count()

    category_count.short_description = "Ratings"
