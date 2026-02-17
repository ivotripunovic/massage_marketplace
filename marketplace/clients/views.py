from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, FormView
from django.db.models import Avg, Count, OuterRef, Q, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from providers.models import (
    Provider,
    ProviderGalleryImage,
    ProviderPricing,
    Country,
    City,
    ProviderAttributeValue,
    PreferenceGroup,
    ProviderPreference,
    ProviderPreferenceCustomOption,
    ProviderCustomPreference,
)
from reviews.models import Review


@require_GET
def country_search_api(request):
    """Search countries by name or code, or list all countries grouped by continent."""
    query = request.GET.get("q", "").strip()
    list_all = request.GET.get("all", "").strip() == "1"

    # Get provider counts per country
    provider_counts = dict(
        Provider.objects.filter(
            subscription_status="active",
            user__is_email_verified=True,
            country__isnull=False,
        )
        .values("country")
        .annotate(count=Count("id"))
        .values_list("country", "count")
    )

    if list_all or len(query) >= 1:
        # Filter by query if provided
        countries_qs = Country.objects.filter(is_active=True).select_related(
            "continent"
        )
        if query:
            countries_qs = countries_qs.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        # Order: Europe first (display_order), then by country name
        countries_qs = countries_qs.order_by("continent__display_order", "name")

        # Group by continent
        continents = {}
        for c in countries_qs:
            continent_name = c.continent.name
            if continent_name not in continents:
                continents[continent_name] = {
                    "name": continent_name,
                    "code": c.continent.code,
                    "order": c.continent.display_order,
                    "countries": [],
                }
            continents[continent_name]["countries"].append(
                {
                    "id": c.id,
                    "name": c.name,
                    "code": c.code,
                    "provider_count": provider_counts.get(c.id, 0),
                }
            )

        # Sort continents by display order and convert to list
        results = sorted(continents.values(), key=lambda x: x["order"])

        return JsonResponse({"continents": results})

    return JsonResponse({"continents": []})


@require_GET
def city_search_api(request):
    """List or search cities within a selected country."""
    query = request.GET.get("q", "").strip()
    country_id = request.GET.get("country", "").strip()
    list_all = request.GET.get("all", "").strip() == "1"

    if not country_id:
        return JsonResponse({"results": []})

    try:
        country_id = int(country_id)
    except ValueError:
        return JsonResponse({"results": []})

    # Get provider counts per city
    provider_counts = dict(
        Provider.objects.filter(
            subscription_status="active",
            user__is_email_verified=True,
            city__isnull=False,
            country_id=country_id,
        )
        .values("city")
        .annotate(count=Count("id"))
        .values_list("city", "count")
    )

    cities_qs = City.objects.filter(country_id=country_id).select_related("country")

    if query:
        cities_qs = cities_qs.filter(name__icontains=query)

    cities_qs = cities_qs.order_by(
        "-is_capital", "-is_major_city", "-population", "name"
    )

    if not list_all:
        cities_qs = cities_qs[:20]

    results = [
        {
            "id": c.id,
            "name": c.name,
            "country": c.country.name,
            "is_capital": c.is_capital,
            "is_major_city": c.is_major_city,
            "provider_count": provider_counts.get(c.id, 0),
        }
        for c in cities_qs
    ]

    return JsonResponse({"results": results})


class ProviderDirectoryView(ListView):
    """Public provider directory view - no authentication required."""

    model = Provider
    template_name = "clients/provider_list.html"
    context_object_name = "providers"
    paginate_by = 20

    def get_queryset(self):
        """Get all active verified providers with related data."""
        attribute_values_qs = ProviderAttributeValue.objects.select_related(
            "definition"
        ).filter(definition__is_active=True)
        attribute_values_prefetch = Prefetch(
            "attribute_values",
            queryset=attribute_values_qs,
            to_attr="active_attribute_values",
        )
        queryset = (
            Provider.objects.filter(
                subscription_status="active", user__is_email_verified=True
            )
            .select_related("user", "country", "city")
            .prefetch_related("pricing", attribute_values_prefetch)
            .annotate(
                review_count=Coalesce(
                    Subquery(
                        Review.objects.filter(provider=OuterRef("pk"))
                        .values("provider")
                        .annotate(cnt=Count("id"))
                        .values("cnt")[:1]
                    ),
                    0,
                ),
                avg_rating=Subquery(
                    Review.objects.filter(provider=OuterRef("pk"))
                    .values("provider")
                    .annotate(avg=Avg("category_ratings__rating"))
                    .values("avg")[:1]
                ),
            )
        )

        # Apply filters from query parameters
        country_id = self.request.GET.get("country_id", "").strip()
        city_id = self.request.GET.get("city_id", "").strip()
        keyword = self.request.GET.get("keyword", "").strip()

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

        # Filter by keyword (search in bio, user name)
        if keyword:
            queryset = queryset.filter(
                Q(bio__icontains=keyword)
                | Q(user__first_name__icontains=keyword)
                | Q(user__last_name__icontains=keyword)
            ).distinct()

        # Order by created date (newest first)
        queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        """Add provider stats and filter choices to context."""
        context = super().get_context_data(**kwargs)

        # Build stats from annotated queryset (no extra queries)
        providers_with_stats = []
        for provider in context["providers"]:
            card_attributes = []
            for attr in getattr(provider, "active_attribute_values", []):
                definition = attr.definition
                if not definition.show_on_card:
                    continue
                formatted = attr.formatted_value()
                if not formatted:
                    continue
                card_attributes.append(
                    {
                        "name": definition.name,
                        "value": formatted,
                        "order": definition.display_order,
                    }
                )
            card_attributes.sort(key=lambda entry: entry["order"])

            # Build card pricing: prefer apartment (inside), fall back to outside
            card_pricing = None
            try:
                p = provider.pricing
                if p.apartment_available:
                    card_pricing = {
                        "location": "Apartment",
                        "price_1h": p.apartment_day_1h,
                        "price_2h": p.apartment_day_2h,
                        "price_whole": p.apartment_night_whole,
                    }
                elif p.outside_available:
                    card_pricing = {
                        "location": "Outside",
                        "price_1h": p.outside_day_1h,
                        "price_2h": p.outside_day_2h,
                        "price_whole": p.outside_night_whole,
                    }
            except ProviderPricing.DoesNotExist:
                pass

            providers_with_stats.append(
                {
                    "provider": provider,
                    "review_count": provider.review_count,
                    "avg_rating": round(provider.avg_rating, 1) if provider.avg_rating else 0,
                    "card_attributes": card_attributes,
                    "card_pricing": card_pricing,
                }
            )

        context["providers_with_stats"] = providers_with_stats

        # Add filter choices and current values
        context["current_country_id"] = self.request.GET.get("country_id", "")
        context["current_city_id"] = self.request.GET.get("city_id", "")
        context["current_keyword"] = self.request.GET.get("keyword", "")

        # Get country and city names for display if IDs are set
        if context["current_country_id"]:
            try:
                country = Country.objects.get(pk=int(context["current_country_id"]))
                context["current_country_name"] = country.name
            except (Country.DoesNotExist, ValueError):
                context["current_country_name"] = ""
        else:
            context["current_country_name"] = ""

        if context["current_city_id"]:
            try:
                city = City.objects.get(pk=int(context["current_city_id"]))
                context["current_city_name"] = city.name
            except (City.DoesNotExist, ValueError):
                context["current_city_name"] = ""
        else:
            context["current_city_name"] = ""

        return context


class ProviderDetailView(DetailView):
    """Public provider detail view - no authentication required."""

    model = Provider
    template_name = "clients/provider_detail.html"
    context_object_name = "provider"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """Only show active verified providers."""
        return (
            Provider.objects.filter(
                subscription_status="active", user__is_email_verified=True
            )
            .select_related("user", "country", "city")
            .prefetch_related("reviews", "gallery_images")
        )

    def get_context_data(self, **kwargs):
        """Add services and reviews to context."""
        context = super().get_context_data(**kwargs)
        provider = context["provider"]

        # Get gallery images
        context["gallery_images"] = ProviderGalleryImage.objects.filter(
            provider=provider
        )

        # Get reviews with category ratings and replies
        context["reviews"] = (
            Review.objects.filter(provider=provider)
            .select_related("client", "reply")
            .prefetch_related("category_ratings__category")
            .order_by("-created_at")
        )

        # Calculate stats
        context["avg_rating"] = provider.average_rating()
        context["total_reviews"] = context["reviews"].count()

        # Add review form (auth-aware)
        from reviews.forms import ReviewForm, ReviewReplyForm

        user = self.request.user
        context["can_review"] = False
        context["review_message"] = None
        if not user.is_authenticated:
            context["review_message"] = "log_in"
        elif user.user_type != "client":
            context["review_message"] = "clients_only"
        elif Review.objects.filter(provider=provider, client=user).exists():
            context["review_message"] = "already_reviewed"
        else:
            context["can_review"] = True
        context["form"] = ReviewForm()

        # Reply form for the provider
        context["is_owner"] = (
            user.is_authenticated
            and hasattr(user, "provider_profile")
            and user.provider_profile == provider
        )
        context["reply_form"] = ReviewReplyForm()
        context["attribute_values"] = (
            ProviderAttributeValue.objects.select_related("definition")
            .filter(provider=provider, definition__is_active=True)
            .order_by("definition__display_order")
        )

        try:
            context["pricing"] = provider.pricing
        except ProviderPricing.DoesNotExist:
            context["pricing"] = None

        # Build preference display
        context["preference_display"] = self._build_preference_display(provider)
        context["preference_comment"] = provider.preference_comment

        # Map data: prefer provider's cached coords, fall back to city
        map_lat = None
        map_lng = None
        if provider.map_latitude and provider.map_longitude:
            map_lat = float(provider.map_latitude)
            map_lng = float(provider.map_longitude)
        elif provider.city and provider.city.latitude and provider.city.longitude:
            map_lat = float(provider.city.latitude)
            map_lng = float(provider.city.longitude)

        if map_lat is not None:
            context["map_lat"] = map_lat
            context["map_lng"] = map_lng
            # Build location label: district + city + country
            parts = []
            district_attr = (
                ProviderAttributeValue.objects.filter(
                    provider=provider,
                    definition__name="District",
                    definition__is_active=True,
                )
                .values_list("value_text", flat=True)
                .first()
            )
            if district_attr:
                parts.append(district_attr)
            if provider.city:
                parts.append(provider.city.name)
            if provider.country:
                parts.append(provider.country.name)
            context["map_label"] = ", ".join(parts)

        return context

    def _build_preference_display(self, provider):
        """Build structured preference data for template rendering."""
        groups = (
            PreferenceGroup.objects.filter(is_active=True)
            .prefetch_related(
                "subgroups",
                "subgroups__options",
            )
            .order_by("display_order", "name")
        )

        # Bulk fetch provider's preferences and custom options
        pref_map = {}
        for pref in ProviderPreference.objects.filter(provider=provider):
            pref_map[pref.subgroup_id] = pref.is_checked

        custom_map = {}
        for custom in ProviderPreferenceCustomOption.objects.filter(
            provider=provider
        ).order_by("display_order"):
            custom_map.setdefault(custom.subgroup_id, []).append(custom.text)

        result = []
        for group in groups:
            subgroups = []
            for sg in group.subgroups.filter(is_active=True).order_by(
                "display_order", "name"
            ):
                is_checked = pref_map.get(sg.pk, False)
                predefined_options = [opt.text for opt in sg.options.all()]
                custom_options = custom_map.get(sg.pk, [])
                subgroups.append(
                    {
                        "name": sg.name,
                        "is_checked": is_checked,
                        "predefined_options": predefined_options,
                        "custom_options": custom_options,
                    }
                )
            if subgroups:
                result.append({"name": group.name, "subgroups": subgroups})

        # Append provider's custom preferences as an "Other" group
        custom_prefs = ProviderCustomPreference.objects.filter(
            provider=provider
        ).order_by("display_order", "name")
        if custom_prefs.exists():
            other_subgroups = [
                {
                    "name": cp.name,
                    "is_checked": True,
                    "predefined_options": [],
                    "custom_options": [],
                }
                for cp in custom_prefs
            ]
            result.append({"name": "Other", "subgroups": other_subgroups})

        return result


class ClientRequiredMixin(LoginRequiredMixin):
    """Mixin to require client user type."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.user_type != "client":
            messages.error(request, "This page is only available to clients.")
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)


class ClientProfileView(ClientRequiredMixin, FormView):
    """Edit client profile (first_name, last_name)."""

    template_name = "clients/client_profile.html"
    success_url = reverse_lazy("client_profile")

    def get_form_class(self):
        from django import forms

        class _Form(forms.Form):
            first_name = forms.CharField(max_length=150, required=False)
            last_name = forms.CharField(max_length=150, required=False)

        return _Form

    def get_initial(self):
        return {
            "first_name": self.request.user.first_name,
            "last_name": self.request.user.last_name,
        }

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.save(update_fields=["first_name", "last_name"])
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class ClientReviewsView(ClientRequiredMixin, ListView):
    """List reviews written by the current client."""

    template_name = "clients/client_reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        return (
            Review.objects.filter(client=self.request.user)
            .select_related("provider__user")
            .prefetch_related("category_ratings__category", "reply")
            .order_by("-created_at")
        )
