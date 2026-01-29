from django.contrib import admin
from .models import Provider, Service, ProviderGalleryImage


class ServiceInline(admin.TabularInline):
    """Inline editor for services."""
    model = Service
    extra = 1
    fields = ('service_type', 'price', 'duration_minutes', 'is_active')


class GalleryImageInline(admin.TabularInline):
    """Inline editor for gallery images."""
    model = ProviderGalleryImage
    extra = 1
    fields = ('image', 'caption', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin interface for Provider model."""
    
    list_display = (
        'user_email',
        'phone',
        'subscription_status',
        'subscription_payment_method',
        'created_at'
    )
    list_filter = (
        'subscription_status',
        'subscription_payment_method',
        'created_at',
        'updated_at'
    )
    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'phone'
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ServiceInline, GalleryImageInline]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('bio', 'phone', 'photo')
        }),
        ('Subscription', {
            'fields': (
                'subscription_status',
                'subscription_payment_method',
                'subscription_renewal_date'
            )
        }),
        ('Payment Information', {
            'fields': ('crypto_address', 'bank_account_encrypted'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['deactivate_subscriptions', 'suspend_accounts', 'activate_subscriptions']
    
    def user_email(self, obj):
        """Display user email in list view."""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def deactivate_subscriptions(self, request, queryset):
        """Bulk action to deactivate subscriptions."""
        count = queryset.update(subscription_status='inactive')
        self.message_user(request, f'{count} provider(s) subscription(s) deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'
    
    def suspend_accounts(self, request, queryset):
        """Bulk action to suspend provider accounts."""
        count = queryset.update(subscription_status='suspended')
        self.message_user(request, f'{count} provider account(s) suspended.')
    suspend_accounts.short_description = 'Suspend selected accounts'
    
    def activate_subscriptions(self, request, queryset):
        """Bulk action to activate subscriptions."""
        from datetime import timedelta, date
        count = 0
        for provider in queryset:
            if provider.subscription_status != 'active':
                provider.subscription_status = 'active'
                provider.subscription_renewal_date = date.today() + timedelta(days=30)
                provider.save()
                count += 1
        self.message_user(request, f'{count} provider subscription(s) activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""
    
    list_display = (
        'provider_email',
        'service_type',
        'price',
        'duration_minutes',
        'is_active',
        'created_at'
    )
    list_filter = ('service_type', 'is_active', 'duration_minutes', 'created_at')
    search_fields = ('provider__user__email', 'service_type', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Provider', {
            'fields': ('provider',)
        }),
        ('Service Information', {
            'fields': ('service_type', 'description', 'price', 'duration_minutes')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email
    provider_email.short_description = 'Provider Email'
    provider_email.admin_order_field = 'provider__user__email'


@admin.register(ProviderGalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    """Admin interface for ProviderGalleryImage model."""

    list_display = ('provider_email', 'caption', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('provider__user__email', 'caption')
    readonly_fields = ('uploaded_at',)

    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email
    provider_email.short_description = 'Provider Email'
    provider_email.admin_order_field = 'provider__user__email'
