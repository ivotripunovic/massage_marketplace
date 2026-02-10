from django.views.generic import ListView, DetailView
from django.db.models import Count, Avg, Q, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from providers.models import (
    Provider,
    Service,
    ProviderGalleryImage,
    Country,
    City,
    ProviderAttributeValue,
)
from reviews.models import Review


@require_GET
def country_search_api(request):
    """Search countries by name or code, or list all countries grouped by continent."""
    query = request.GET.get('q', '').strip()
    list_all = request.GET.get('all', '').strip() == '1'

    # Get provider counts per country
    provider_counts = dict(
        Provider.objects.filter(
            subscription_status='active',
            user__is_email_verified=True,
            country__isnull=False
        ).values('country').annotate(count=Count('id')).values_list('country', 'count')
    )

    if list_all or len(query) >= 1:
        # Filter by query if provided
        countries_qs = Country.objects.filter(is_active=True).select_related('continent')
        if query:
            countries_qs = countries_qs.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        # Order: Europe first (display_order), then by country name
        countries_qs = countries_qs.order_by('continent__display_order', 'name')

        # Group by continent
        continents = {}
        for c in countries_qs:
            continent_name = c.continent.name
            if continent_name not in continents:
                continents[continent_name] = {
                    'name': continent_name,
                    'code': c.continent.code,
                    'order': c.continent.display_order,
                    'countries': []
                }
            continents[continent_name]['countries'].append({
                'id': c.id,
                'name': c.name,
                'code': c.code,
                'provider_count': provider_counts.get(c.id, 0)
            })

        # Sort continents by display order and convert to list
        results = sorted(continents.values(), key=lambda x: x['order'])

        return JsonResponse({'continents': results})

    return JsonResponse({'continents': []})


@require_GET
def city_search_api(request):
    """List or search cities within a selected country."""
    query = request.GET.get('q', '').strip()
    country_id = request.GET.get('country', '').strip()
    list_all = request.GET.get('all', '').strip() == '1'

    if not country_id:
        return JsonResponse({'results': []})

    try:
        country_id = int(country_id)
    except ValueError:
        return JsonResponse({'results': []})

    # Get provider counts per city
    provider_counts = dict(
        Provider.objects.filter(
            subscription_status='active',
            user__is_email_verified=True,
            city__isnull=False,
            country_id=country_id
        ).values('city').annotate(count=Count('id')).values_list('city', 'count')
    )

    cities_qs = City.objects.filter(country_id=country_id).select_related('country')

    if query:
        cities_qs = cities_qs.filter(name__icontains=query)

    cities_qs = cities_qs.order_by('-is_capital', '-is_major_city', '-population', 'name')

    if not list_all:
        cities_qs = cities_qs[:20]

    results = [{
        'id': c.id,
        'name': c.name,
        'country': c.country.name,
        'is_capital': c.is_capital,
        'is_major_city': c.is_major_city,
        'provider_count': provider_counts.get(c.id, 0)
    } for c in cities_qs]

    return JsonResponse({'results': results})


class ProviderDirectoryView(ListView):
    """Public provider directory view - no authentication required."""

    model = Provider
    template_name = 'clients/provider_list.html'
    context_object_name = 'providers'
    paginate_by = 20

    def get_queryset(self):
        """Get all active verified providers with related data."""
        attribute_values_qs = ProviderAttributeValue.objects.select_related('definition').filter(
            definition__is_active=True
        )
        attribute_values_prefetch = Prefetch(
            'attribute_values',
            queryset=attribute_values_qs,
            to_attr='active_attribute_values'
        )
        queryset = Provider.objects.filter(
            subscription_status='active',
            user__is_email_verified=True
        ).select_related('user', 'country', 'city').prefetch_related(
            'services',
            'reviews',
            attribute_values_prefetch
        )

        # Apply filters from query parameters
        service_type = self.request.GET.get('service_type', '').strip()
        country_id = self.request.GET.get('country_id', '').strip()
        city_id = self.request.GET.get('city_id', '').strip()
        keyword = self.request.GET.get('keyword', '').strip()
        price_min = self.request.GET.get('price_min', '').strip()
        price_max = self.request.GET.get('price_max', '').strip()

        # Filter by service type (providers who offer this service)
        if service_type:
            queryset = queryset.filter(services__service_type=service_type, services__is_active=True).distinct()

        # Filter by location using ForeignKey fields
        if country_id:
            try:
                queryset = queryset.filter(country_id=int(country_id))
            except ValueError:
                pass
        if city_id:
            try:
                queryset = queryset.filter(city_id=int(city_id))
            except ValueError:
                pass

        # Filter by keyword (search in bio, user name, services)
        if keyword:
            queryset = queryset.filter(
                Q(bio__icontains=keyword) |
                Q(user__first_name__icontains=keyword) |
                Q(user__last_name__icontains=keyword) |
                Q(services__description__icontains=keyword)
            ).distinct()

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

            # Get active services for display
            services = Service.objects.filter(provider=provider, is_active=True)[:3]

            # Get price range
            all_services = Service.objects.filter(provider=provider, is_active=True)
            if all_services.exists():
                min_price = all_services.order_by('price').first().price
                max_price = all_services.order_by('-price').first().price
            else:
                min_price = max_price = None

            card_attributes = []
            for attr in getattr(provider, 'active_attribute_values', []):
                definition = attr.definition
                if not definition.show_on_card:
                    continue
                formatted = attr.formatted_value()
                if not formatted:
                    continue
                card_attributes.append({
                    'name': definition.name,
                    'value': formatted,
                    'order': definition.display_order,
                })
            card_attributes.sort(key=lambda entry: entry['order'])

            providers_with_stats.append({
                'provider': provider,
                'service_count': service_count,
                'services': services,
                'review_count': reviews.count(),
                'avg_rating': avg_rating,
                'min_price': min_price,
                'max_price': max_price,
                'card_attributes': card_attributes,
            })

        context['providers_with_stats'] = providers_with_stats

        # Add filter choices and current values
        context['service_types'] = Service.SERVICE_TYPE_CHOICES
        context['current_service_type'] = self.request.GET.get('service_type', '')
        context['current_country_id'] = self.request.GET.get('country_id', '')
        context['current_city_id'] = self.request.GET.get('city_id', '')
        context['current_keyword'] = self.request.GET.get('keyword', '')
        context['current_price_min'] = self.request.GET.get('price_min', '')
        context['current_price_max'] = self.request.GET.get('price_max', '')

        # Get country and city names for display if IDs are set
        if context['current_country_id']:
            try:
                country = Country.objects.get(pk=int(context['current_country_id']))
                context['current_country_name'] = country.name
            except (Country.DoesNotExist, ValueError):
                context['current_country_name'] = ''
        else:
            context['current_country_name'] = ''

        if context['current_city_id']:
            try:
                city = City.objects.get(pk=int(context['current_city_id']))
                context['current_city_name'] = city.name
            except (City.DoesNotExist, ValueError):
                context['current_city_name'] = ''
        else:
            context['current_city_name'] = ''

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
        context['attribute_values'] = ProviderAttributeValue.objects.select_related('definition').filter(
            provider=provider,
            definition__is_active=True
        )

        return context
