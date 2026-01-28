from django.views.generic import ListView, DetailView
from django.db.models import Count, Avg, Q
from providers.models import Provider, Service
from reviews.models import Review


class ProviderDirectoryView(ListView):
    """Public provider directory view - no authentication required."""

    model = Provider
    template_name = 'clients/provider_list.html'
    context_object_name = 'providers'
    paginate_by = 20

    def get_queryset(self):
        """Get all active verified providers with related data."""
        queryset = Provider.objects.filter(
            subscription_status='active',
            user__is_email_verified=True
        ).select_related('user').prefetch_related('services', 'reviews')

        # Order by created date (newest first)
        queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """Add provider stats to context."""
        context = super().get_context_data(**kwargs)

        # Calculate statistics for each provider
        providers_with_stats = []
        for provider in context['providers']:
            reviews = Review.objects.filter(provider=provider)
            service_count = Service.objects.filter(provider=provider, is_active=True).count()
            avg_rating = provider.average_rating()

            providers_with_stats.append({
                'provider': provider,
                'service_count': service_count,
                'review_count': reviews.count(),
                'avg_rating': avg_rating
            })

        context['providers_with_stats'] = providers_with_stats

        return context


class ProviderDetailView(DetailView):
    """Public provider detail view - no authentication required."""

    model = Provider
    template_name = 'clients/provider_detail.html'
    context_object_name = 'provider'
    slug_field = 'user__email'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Only show active verified providers."""
        return Provider.objects.filter(
            subscription_status='active',
            user__is_email_verified=True
        ).select_related('user').prefetch_related('services', 'certifications', 'reviews')

    def get_context_data(self, **kwargs):
        """Add services, certifications, and reviews to context."""
        context = super().get_context_data(**kwargs)
        provider = context['provider']

        # Get services
        context['services'] = Service.objects.filter(
            provider=provider,
            is_active=True
        ).order_by('service_type')

        # Get certifications
        context['certifications'] = provider.certifications.all()

        # Get reviews
        context['reviews'] = Review.objects.filter(
            provider=provider
        ).order_by('-created_at')

        # Calculate stats
        context['avg_rating'] = provider.average_rating()
        context['total_reviews'] = context['reviews'].count()

        return context
