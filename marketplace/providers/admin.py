from django.contrib import admin
from .models import Provider, Service, Certification


class ServiceInline(admin.TabularInline):
    """Inline editor for services."""
    model = Service
    extra = 1
    fields = ('service_type', 'price', 'duration_minutes', 'is_active')


class CertificationInline(admin.TabularInline):
    """Inline editor for certifications."""
    model = Certification
    extra = 1
    fields = ('name', 'image')


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
    inlines = [ServiceInline, CertificationInline]
    
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
    
    def user_email(self, obj):
        """Display user email in list view."""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'


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


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    """Admin interface for Certification model."""
    
    list_display = ('provider_email', 'name', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('provider__user__email', 'name')
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Provider', {
            'fields': ('provider',)
        }),
        ('Certification', {
            'fields': ('name', 'image')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )
    
    def provider_email(self, obj):
        """Display provider email in list view."""
        return obj.provider.user.email
    provider_email.short_description = 'Provider Email'
    provider_email.admin_order_field = 'provider__user__email'
