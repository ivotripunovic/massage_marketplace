from django.views.generic import ListView, DetailView
from django.db.models import Count, Avg, Q
from providers.models import Provider, Service, ProviderGalleryImage
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

        # Apply filters from query parameters
        service_type = self.request.GET.get('service_type', '').strip()
        country = self.request.GET.get('country', '').strip()
        city = self.request.GET.get('city', '').strip()
        price_min = self.request.GET.get('price_min', '').strip()
        price_max = self.request.GET.get('price_max', '').strip()

        # Filter by service type (providers who offer this service)
        if service_type:
            queryset = queryset.filter(services__service_type=service_type, services__is_active=True).distinct()

        # Filter by location
        if country:
            queryset = queryset.filter(country__iexact=country)
        if city:
            queryset = queryset.filter(city__iexact=city)

        # Filter by price range (providers who have services in this range)
        if price_min:
            try:
                min_price = float(price_min)
                queryset = queryset.filter(services__price__gte=min_price, services__is_active=True).distinct()
            except ValueError:
                pass

        if price_max:
            try:
                max_price = float(price_max)
                queryset = queryset.filter(services__price__lte=max_price, services__is_active=True).distinct()
            except ValueError:
                pass

        # Order by created date (newest first)
        queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        """Add provider stats and filter choices to context."""
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

        # Add filter choices and current values
        context['service_types'] = Service.SERVICE_TYPE_CHOICES
        context['current_service_type'] = self.request.GET.get('service_type', '')
        context['current_country'] = self.request.GET.get('country', '')
        context['current_city'] = self.request.GET.get('city', '')
        context['current_price_min'] = self.request.GET.get('price_min', '')
        context['current_price_max'] = self.request.GET.get('price_max', '')

        # Get unique countries and cities from active providers
        context['countries'] = Provider.objects.filter(
            subscription_status='active',
            country__isnull=False
        ).values_list('country', flat=True).distinct().order_by('country')

        context['cities'] = Provider.objects.filter(
            subscription_status='active',
            city__isnull=False
        ).values_list('city', flat=True).distinct().order_by('city')

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
        ).select_related('user').prefetch_related('services', 'reviews', 'gallery_images')

    def get_context_data(self, **kwargs):
        """Add services and reviews to context."""
        context = super().get_context_data(**kwargs)
        provider = context['provider']

        # Get services
        context['services'] = Service.objects.filter(
            provider=provider,
            is_active=True
        ).order_by('service_type')

        # Get gallery images
        context['gallery_images'] = ProviderGalleryImage.objects.filter(provider=provider)

        # Get reviews
        context['reviews'] = Review.objects.filter(
            provider=provider
        ).order_by('-created_at')

        # Calculate stats
        context['avg_rating'] = provider.average_rating()
        context['total_reviews'] = context['reviews'].count()

        # Add review form
        from reviews.forms import ReviewForm
        context['form'] = ReviewForm()

        return context
