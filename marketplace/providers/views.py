from django.views.generic import (
    TemplateView,
    FormView,
    CreateView,
    DeleteView,
    ListView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django import forms
from django.http import HttpResponseForbidden
from providers.models import (
    Provider,
    ProviderGalleryImage,
    ProviderAttributeDefinition,
    ProviderAttributeValue,
    ProviderPricing,
    PreferenceGroup,
    ProviderPreference,
    ProviderPreferenceCustomOption,
    ProviderCustomPreference,
)
from providers.forms import (
    SubscriptionSettingsForm,
    GalleryImageForm,
)
import logging

logger = logging.getLogger(__name__)


class ProviderRequiredMixin(LoginRequiredMixin):
    """Mixin to require provider user type."""

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is a provider."""
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.user_type != "provider":
            messages.error(request, "This page is only available to providers.")
            return redirect("login")

        return super().dispatch(request, *args, **kwargs)


class ProviderDashboardView(ProviderRequiredMixin, TemplateView):
    """Provider dashboard view."""

    template_name = "providers/dashboard.html"

    def get_context_data(self, **kwargs):
        """Add provider data to context."""
        context = super().get_context_data(**kwargs)

        try:
            provider = Provider.objects.get(user=self.request.user)
            context["provider"] = provider
            # Calculate stats
            from reviews.models import Review

            reviews = Review.objects.filter(provider=provider)
            context["total_reviews"] = reviews.count()
            context["average_rating"] = provider.average_rating()
            context["gallery_images"] = ProviderGalleryImage.objects.filter(
                provider=provider
            )
            context["attribute_values"] = ProviderAttributeValue.objects.select_related(
                "definition"
            ).filter(provider=provider, definition__is_active=True)
        except Provider.DoesNotExist:
            # Provider profile not yet created, redirect to create
            context["provider"] = None
            context["message"] = "Please complete your profile to get started."

        return context


class ProviderProfileForm(forms.ModelForm):
    """Form for updating provider profile."""

    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="First Name",
        widget=forms.TextInput(
            attrs={"class": "input-dark w-full", "placeholder": "First Name"}
        ),
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
        widget=forms.TextInput(
            attrs={"class": "input-dark w-full", "placeholder": "Last Name"}
        ),
    )

    class Meta:
        model = Provider
        fields = ("bio", "phone", "phone_hours", "photo", "profile_video")
        labels = {
            "bio": "Bio / About",
            "phone": "Phone Number",
            "phone_hours": "Good Time to Call",
            "photo": "Profile Photo",
            "profile_video": "Profile Video",
        }
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "class": "input-dark w-full",
                    "placeholder": "Tell clients about your experience and specialties",
                    "rows": 4,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "input-dark w-full",
                    "placeholder": "+1 (555) 123-4567",
                    "type": "tel",
                }
            ),
            "phone_hours": forms.TextInput(
                attrs={
                    "class": "input-dark w-full",
                    "placeholder": "e.g. 10:00 – 18:00",
                }
            ),
            "photo": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-text-primary file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gold file:text-dark cursor-pointer",
                    "accept": "image/jpeg,image/png,image/gif",
                }
            ),
            "profile_video": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-text-primary file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gold file:text-dark cursor-pointer",
                    "accept": "video/mp4",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with user data."""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
        self.attribute_definitions = list(
            ProviderAttributeDefinition.objects.filter(is_active=True).order_by(
                "display_order", "name"
            )
        )
        self.attribute_fields = []
        for definition in self.attribute_definitions:
            field_name = f"attribute_{definition.pk}"
            field = self._build_attribute_field(definition)
            initial_value = self._get_attribute_initial(definition)
            if initial_value is not None:
                field.initial = initial_value
            self.fields[field_name] = field
            bound_field = self[field_name]
            self.attribute_fields.append(
                {
                    "definition": definition,
                    "name": field_name,
                    "bound_field": bound_field,
                }
            )

    def clean_photo(self):
        """Validate photo file."""
        photo = self.cleaned_data.get("photo")

        if photo and hasattr(photo, "content_type"):
            # Only validate newly uploaded files (not existing ImageFieldFile)
            # Check file size (< 5MB)
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image must be smaller than 5MB")

            # Check file format
            valid_formats = ["image/jpeg", "image/png", "image/gif"]
            if photo.content_type not in valid_formats:
                raise forms.ValidationError(
                    "Only JPEG, PNG, and GIF images are allowed"
                )

            # Validate that it's a real image
            try:
                from PIL import Image

                img = Image.open(photo)
                img.verify()
                # Reset file pointer after verification
                photo.seek(0)
            except Exception:
                raise forms.ValidationError("The uploaded file is not a valid image")

        return photo

    def clean_profile_video(self):
        """Validate profile video file."""
        video = self.cleaned_data.get("profile_video")

        if video and hasattr(video, "content_type"):
            if video.size > 50 * 1024 * 1024:
                raise forms.ValidationError("Video must be smaller than 50MB")

            if video.content_type != "video/mp4":
                raise forms.ValidationError("Only MP4 videos are allowed")

        return video

    def save(self, commit=True):
        """Save form and update user fields."""
        provider = super().save(commit=False)

        # Update user first and last name
        user = provider.user
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")

        # Resize image if provided
        if provider.photo:
            self._resize_image(provider)

        if commit:
            user.save()
            provider.save()
            self._save_attribute_values(provider)

        return provider

    def _resize_image(self, provider):
        """Resize image to maximum 800x800 pixels."""
        from PIL import Image
        import io

        if not provider.photo:
            return

        # Read the image
        img = Image.open(provider.photo)
        original_format = img.format

        # Check if resizing is needed
        if img.height > 800 or img.width > 800:
            # Create thumbnail
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)

            # Save the resized image back to the field
            img_io = io.BytesIO()

            # Determine format from filename or image format
            filename_lower = provider.photo.name.lower()
            if filename_lower.endswith(".png"):
                save_format = "PNG"
            elif filename_lower.endswith(".gif"):
                save_format = "GIF"
            else:  # Default to JPEG
                save_format = "JPEG"

            # If original image had a format, use that
            if original_format:
                save_format = original_format

            img.save(img_io, format=save_format)
            img_io.seek(0)
            provider.photo.save(provider.photo.name, img_io, save=False)

    def _build_attribute_field(self, definition):
        """Create a form field for a provider attribute definition."""
        common_widget_attrs = {"class": "input-dark w-full"}
        is_required = definition.show_on_card

        if definition.data_type == ProviderAttributeDefinition.DATA_TYPE_INTEGER:
            return forms.IntegerField(
                label=definition.name,
                required=is_required,
                widget=forms.NumberInput(attrs=common_widget_attrs),
            )

        if definition.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            return forms.BooleanField(
                label=definition.name,
                required=False,
                widget=forms.CheckboxInput(
                    attrs={"class": "form-checkbox h-4 w-4 text-gold"}
                ),
            )

        return forms.CharField(
            label=definition.name,
            required=is_required,
            max_length=255,
            widget=forms.TextInput(attrs=common_widget_attrs),
        )

    def _get_attribute_initial(self, definition):
        """Return the initial value for a provider attribute field."""
        if not self.instance or not self.instance.pk:
            return None

        try:
            attribute_value = ProviderAttributeValue.objects.get(
                provider=self.instance, definition=definition
            )
            typed = attribute_value.get_typed_value()
            if typed is not None:
                return typed
            return attribute_value.value_text
        except ProviderAttributeValue.DoesNotExist:
            return None

    def _serialize_attribute_value(self, definition, raw_value):
        """Convert cleaned value into normalized text."""
        if definition.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            if raw_value in (None, ""):
                return ""
            return "1" if raw_value else "0"

        if raw_value in (None, ""):
            return ""

        text = str(raw_value).strip()
        return text

    def _save_attribute_values(self, provider):
        """Persist attribute values using the cleaned data."""
        for definition in self.attribute_definitions:
            field_name = f"attribute_{definition.pk}"
            if field_name not in self.cleaned_data:
                continue
            serialized = self._serialize_attribute_value(
                definition, self.cleaned_data.get(field_name)
            )
            if serialized == "":
                ProviderAttributeValue.objects.filter(
                    provider=provider, definition=definition
                ).delete()
                continue
            ProviderAttributeValue.objects.update_or_create(
                provider=provider,
                definition=definition,
                defaults={"value_text": serialized},
            )


class ProviderPricingForm(forms.ModelForm):
    """Form for the provider pricing grid."""

    class Meta:
        model = ProviderPricing
        exclude = ("provider", "created_at", "updated_at")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        price_attrs = {
            "class": "input-dark w-full",
            "placeholder": "0.00",
            "step": "0.01",
            "min": "0",
        }
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DecimalField):
                field.widget = forms.NumberInput(attrs=price_attrs)
            elif field_name in ("day_note", "night_note"):
                field.widget = forms.TextInput(
                    attrs={
                        "class": "input-dark w-full",
                        "placeholder": "Optional note",
                        "maxlength": "120",
                    }
                )


class ProviderPreferencesForm(forms.Form):
    """Dynamic form for provider preferences: checkbox per subgroup + custom text."""

    preference_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "input-dark w-full",
                "rows": 3,
                "placeholder": "General comment about your preferences",
            }
        ),
        label="Preference Comment",
    )

    def __init__(self, *args, provider=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider = provider
        self._groups = []

        if provider:
            self.fields["preference_comment"].initial = provider.preference_comment

        # Fetch active groups/subgroups
        groups = (
            PreferenceGroup.objects.filter(is_active=True)
            .prefetch_related("subgroups")
            .order_by("display_order", "name")
        )

        # Bulk fetch existing preferences
        pref_map = {}
        custom_map = {}
        if provider and provider.pk:
            for pref in ProviderPreference.objects.filter(provider=provider):
                pref_map[pref.subgroup_id] = pref.is_checked
            for custom in ProviderPreferenceCustomOption.objects.filter(
                provider=provider
            ).order_by("display_order"):
                custom_map.setdefault(custom.subgroup_id, []).append(custom.text)

        for group in groups:
            group_fields = []
            for sg in group.subgroups.filter(is_active=True).order_by(
                "display_order", "name"
            ):
                # Checkbox field
                cb_name = f"pref_check_{sg.pk}"
                self.fields[cb_name] = forms.BooleanField(
                    required=False,
                    label=sg.name,
                    initial=pref_map.get(sg.pk, False),
                    widget=forms.CheckboxInput(
                        attrs={"class": "form-checkbox h-4 w-4 text-gold"}
                    ),
                )

                # Custom options textarea
                txt_name = f"pref_custom_{sg.pk}"
                custom_texts = custom_map.get(sg.pk, [])
                self.fields[txt_name] = forms.CharField(
                    required=False,
                    label=f"{sg.name} custom options",
                    initial="\n".join(custom_texts),
                    widget=forms.Textarea(
                        attrs={
                            "class": "input-dark w-full",
                            "rows": 2,
                            "placeholder": "One per line",
                        }
                    ),
                )

                group_fields.append(
                    {
                        "subgroup": sg,
                        "checkbox": self[cb_name],
                        "custom_textarea": self[txt_name],
                    }
                )

            if group_fields:
                self._groups.append({"group": group, "fields": group_fields})

        # "Other" — provider's own custom items (one per line)
        custom_initial = ""
        if provider and provider.pk:
            custom_items = ProviderCustomPreference.objects.filter(
                provider=provider
            ).order_by("display_order", "name")
            custom_initial = "\n".join(cp.name for cp in custom_items)

        self.fields["custom_preferences"] = forms.CharField(
            required=False,
            label="Other",
            initial=custom_initial,
            widget=forms.Textarea(
                attrs={
                    "class": "input-dark w-full",
                    "rows": 4,
                    "placeholder": "Your own items, one per line",
                }
            ),
        )

    @property
    def grouped_fields(self):
        return self._groups

    def save(self, provider):
        """Save preference toggles and custom options."""
        provider.preference_comment = self.cleaned_data.get("preference_comment", "")
        provider.save(update_fields=["preference_comment"])

        for group_data in self._groups:
            for field_data in group_data["fields"]:
                sg = field_data["subgroup"]
                is_checked = self.cleaned_data.get(f"pref_check_{sg.pk}", False)
                custom_text = self.cleaned_data.get(f"pref_custom_{sg.pk}", "")

                ProviderPreference.objects.update_or_create(
                    provider=provider,
                    subgroup=sg,
                    defaults={"is_checked": is_checked},
                )

                # Replace custom options
                ProviderPreferenceCustomOption.objects.filter(
                    provider=provider, subgroup=sg
                ).delete()
                for i, line in enumerate(custom_text.strip().splitlines()):
                    line = line.strip()
                    if line:
                        ProviderPreferenceCustomOption.objects.create(
                            provider=provider,
                            subgroup=sg,
                            text=line,
                            display_order=i,
                        )

        # Save provider's own custom preference items ("Other" group)
        custom_prefs_text = self.cleaned_data.get("custom_preferences", "")
        ProviderCustomPreference.objects.filter(provider=provider).delete()
        for i, line in enumerate(custom_prefs_text.strip().splitlines()):
            line = line.strip()
            if line:
                ProviderCustomPreference.objects.create(
                    provider=provider,
                    name=line,
                    display_order=i,
                )


class ProviderProfileUpdateView(ProviderRequiredMixin, FormView):
    """View for updating provider profile."""

    template_name = "providers/profile_edit.html"
    form_class = ProviderProfileForm
    success_url = reverse_lazy("provider_dashboard")

    def _get_provider(self):
        try:
            return Provider.objects.get(user=self.request.user)
        except Provider.DoesNotExist:
            return Provider.objects.create(user=self.request.user, phone="")

    def get_form_kwargs(self):
        """Pass provider instance to form."""
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self._get_provider()
        return kwargs

    def _get_pricing_form(self):
        """Build the pricing form from POST data or existing instance."""
        provider = self._get_provider()
        pricing, _ = ProviderPricing.objects.get_or_create(provider=provider)
        if self.request.method == "POST":
            return ProviderPricingForm(
                self.request.POST, instance=pricing, prefix="pricing"
            )
        return ProviderPricingForm(instance=pricing, prefix="pricing")

    def _get_preferences_form(self):
        """Build the preferences form from POST data or existing provider."""
        provider = self._get_provider()
        if self.request.method == "POST":
            return ProviderPreferencesForm(
                self.request.POST, provider=provider, prefix="prefs"
            )
        return ProviderPreferencesForm(provider=provider, prefix="prefs")

    def post(self, request, *args, **kwargs):
        """Handle POST: validate all forms together."""
        form = self.get_form()
        pricing_form = self._get_pricing_form()
        preferences_form = self._get_preferences_form()
        if form.is_valid() and pricing_form.is_valid() and preferences_form.is_valid():
            form.save()
            pricing_form.save()
            provider = self._get_provider()
            preferences_form.save(provider)
            self._update_map_coordinates(provider)
            messages.success(request, "Your profile has been updated successfully.")
            return self.form_valid_redirect()
        return self.render_to_response(
            self.get_context_data(
                form=form,
                pricing_form=pricing_form,
                preferences_form=preferences_form,
            )
        )

    def form_valid_redirect(self):
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())

    def _update_map_coordinates(self, provider):
        """Geocode provider location and cache coordinates."""
        from providers.utils import geocode_location

        # Get district attribute value
        district = (
            ProviderAttributeValue.objects.filter(
                provider=provider,
                definition__name="District",
                definition__is_active=True,
            )
            .values_list("value_text", flat=True)
            .first()
        ) or ""

        city_name = provider.city.name if provider.city else ""
        country_name = provider.country.name if provider.country else ""

        if district and city_name:
            result = geocode_location(district, city_name, country_name)
            if result:
                provider.map_latitude, provider.map_longitude = result
                provider.save(update_fields=["map_latitude", "map_longitude"])
                return

        # Fall back to city coordinates
        if provider.city and provider.city.latitude and provider.city.longitude:
            provider.map_latitude = provider.city.latitude
            provider.map_longitude = provider.city.longitude
        else:
            provider.map_latitude = None
            provider.map_longitude = None
        provider.save(update_fields=["map_latitude", "map_longitude"])

    def get_context_data(self, **kwargs):
        """Add provider data to context."""
        context = super().get_context_data(**kwargs)
        context["provider"] = self._get_provider()
        context["attribute_fields"] = getattr(context["form"], "attribute_fields", [])
        if "pricing_form" not in context:
            context["pricing_form"] = self._get_pricing_form()
        if "preferences_form" not in context:
            context["preferences_form"] = self._get_preferences_form()
        return context


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to require admin user type."""

    def dispatch(self, request, *args, **kwargs):
        """Check if user is authenticated and is an admin."""
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.user_type != "admin":
            return HttpResponseForbidden(
                "You do not have permission to access this page."
            )

        return super().dispatch(request, *args, **kwargs)


class AdminProviderListView(AdminRequiredMixin, ListView):
    """View for listing all providers (admin only)."""

    model = Provider
    template_name = "admin/provider_list.html"
    context_object_name = "providers"
    paginate_by = 50

    def get_queryset(self):
        """Get all providers with annotations."""

        queryset = Provider.objects.select_related("user").all()

        # Search by email
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(user__email__icontains=search)

        # Filter by status
        status = self.request.GET.get("status", "").strip()
        if status and status in ["active", "inactive", "suspended"]:
            queryset = queryset.filter(subscription_status=status)

        # Order by email
        queryset = queryset.order_by("user__email")

        return queryset

    def get_context_data(self, **kwargs):
        """Add search/filter info to context."""
        context = super().get_context_data(**kwargs)

        # Add search and filter values
        context["search"] = self.request.GET.get("search", "")
        context["status"] = self.request.GET.get("status", "")
        context["status_choices"] = ["active", "inactive", "suspended"]

        # Calculate statistics for each provider
        from reviews.models import Review

        providers_with_stats = []
        for provider in context["providers"]:
            review_count = Review.objects.filter(provider=provider).count()
            providers_with_stats.append(
                {
                    "provider": provider,
                    "review_count": review_count,
                    "avg_rating": provider.average_rating(),
                }
            )
        context["providers_with_stats"] = providers_with_stats

        return context


class ProviderSubscriptionView(ProviderRequiredMixin, FormView):
    """View for managing provider subscriptions."""

    form_class = SubscriptionSettingsForm
    template_name = "providers/subscription.html"
    success_url = reverse_lazy("subscription_confirm")

    def _get_currencies(self):
        try:
            import payments.nowpayments as nowpayments
            return nowpayments.get_currencies()
        except Exception as exc:
            logger.error("Failed to fetch NOWPayments currencies: %s", exc)
            from payments.nowpayments import FALLBACK_CURRENCIES
            return FALLBACK_CURRENCIES

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["currencies"] = self._get_currencies()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            provider = Provider.objects.get(user=self.request.user)
            context["provider"] = provider
        except Provider.DoesNotExist:
            context["provider"] = None
        context["currencies"] = self._get_currencies()
        return context

    def form_valid(self, form):
        """Store chosen currency and redirect to crypto payment page."""
        payment_method = form.cleaned_data["payment_method"]
        self.request.session["pending_payment_method"] = payment_method
        return redirect("subscription_crypto_payment")


def _qr_data_uri(data: str) -> str:
    """Return a base64 PNG data URI for the given string."""
    import base64
    import io
    import qrcode
    from PIL import Image

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#f5f5f5", back_color="#111827")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


class CryptoPaymentView(ProviderRequiredMixin, View):
    """Crypto payment via NOWPayments: create a payment and display the address."""

    template_name = "providers/subscription_crypto.html"

    def dispatch(self, request, *args, **kwargs):
        self.payment_method = request.session.get("pending_payment_method")
        if not self.payment_method:
            messages.error(request, "Please select a payment method first.")
            return redirect("subscription")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from django.conf import settings as django_settings
        from payments.models import SubscriptionPayment
        import payments.nowpayments as nowpayments

        provider = get_object_or_404(Provider, user=request.user)
        amount = getattr(django_settings, "SUBSCRIPTION_AMOUNT", 29.99)

        # Reuse existing pending NOWPayments payment if one was already created
        existing_id = request.session.get("nowpayments_payment_id")
        payment_record = None
        if existing_id:
            payment_record = SubscriptionPayment.objects.filter(
                nowpayments_payment_id=existing_id,
                provider=provider,
                status="pending",
            ).first()

        if not payment_record:
            # Build the IPN callback URL
            ipn_url = request.build_absolute_uri("/payments/webhook/nowpayments/")
            try:
                result = nowpayments.create_payment(
                    amount_usd=amount,
                    pay_currency=self.payment_method,
                    order_id=f"{provider.pk}-{provider.user.email}",
                    ipn_callback_url=ipn_url,
                )
            except Exception as exc:
                response = getattr(exc, "response", None)
                response_text = response.text if response is not None else ""
                logger.error(
                    "NOWPayments create_payment failed for provider %s (%s): %s %s",
                    provider.pk,
                    request.user.email,
                    exc,
                    response_text,
                )
                messages.error(
                    request,
                    "Could not create payment. Please try again or contact support.",
                )
                return redirect("subscription")

            payment_record = SubscriptionPayment.objects.create(
                provider=provider,
                amount=amount,
                payment_method=self.payment_method,
                status="pending",
                nowpayments_payment_id=str(result["payment_id"]),
                pay_address=result.get("pay_address", ""),
                pay_amount=result.get("pay_amount"),
                pay_currency=result.get("pay_currency", ""),
            )
            request.session["nowpayments_payment_id"] = str(result["payment_id"])

        # Build wallet URI for QR code and deeplink
        from payments.nowpayments import SUPPORTED_CURRENCIES
        pay_currency_lower = (payment_record.pay_currency or "").lower()
        currency_meta = next(
            (c for c in SUPPORTED_CURRENCIES if c["code"] == pay_currency_lower), None
        )
        uri_scheme = currency_meta["uri_scheme"] if currency_meta else "ethereum"
        wallet_uri = f"{uri_scheme}:{payment_record.pay_address}"

        qr_data_uri = ""
        if payment_record.pay_address:
            try:
                qr_data_uri = _qr_data_uri(wallet_uri)
            except Exception:
                pass

        try:
            currencies = nowpayments.get_currencies()
            currency_name = {c["code"]: c["name"] for c in currencies}.get(
                self.payment_method, self.payment_method.upper()
            )
        except Exception:
            currency_name = self.payment_method.upper()

        context = {
            "provider": provider,
            "payment_method": self.payment_method,
            "payment_method_display": currency_name,
            "amount": amount,
            "pay_address": payment_record.pay_address,
            "pay_amount": payment_record.pay_amount,
            "pay_currency": (payment_record.pay_currency or "").upper(),
            "wallet_uri": wallet_uri,
            "qr_data_uri": qr_data_uri,
            "payment": payment_record,
        }
        from django.shortcuts import render
        return render(request, self.template_name, context)

    def post(self, request):
        """Provider confirmed they sent the payment — redirect to confirm page."""
        request.session.pop("pending_payment_method", None)
        return redirect("subscription_confirm")


class CryptoPaymentStatusView(ProviderRequiredMixin, View):
    """JSON endpoint polled by the payment page to detect confirmation."""

    def get(self, request, nowpayments_payment_id):
        from django.http import JsonResponse
        from payments.models import SubscriptionPayment

        provider = get_object_or_404(Provider, user=request.user)
        payment = get_object_or_404(
            SubscriptionPayment,
            nowpayments_payment_id=nowpayments_payment_id,
            provider=provider,
        )
        return JsonResponse({"status": payment.status})



class SubscriptionConfirmView(ProviderRequiredMixin, TemplateView):
    """View to confirm subscription activation."""

    template_name = "providers/subscription_confirm.html"

    def get_context_data(self, **kwargs):
        """Add provider and payment info to context."""
        context = super().get_context_data(**kwargs)
        try:
            provider = Provider.objects.get(user=self.request.user)
            context["provider"] = provider

            from payments.models import SubscriptionPayment

            recent_payment = (
                SubscriptionPayment.objects.filter(provider=provider)
                .order_by("-created_at")
                .first()
            )
            context["recent_payment"] = recent_payment
            # Show pending state for NOWPayments crypto payments awaiting confirmation
            context["payment_pending"] = bool(
                recent_payment
                and recent_payment.nowpayments_payment_id
                and recent_payment.status == "pending"
            )
        except Provider.DoesNotExist:
            context["provider"] = None
            context["payment_pending"] = False
        return context


class GalleryImageCreateView(ProviderRequiredMixin, CreateView):
    """View for uploading a gallery image."""

    model = ProviderGalleryImage
    form_class = GalleryImageForm
    template_name = "providers/gallery_upload.html"
    success_url = reverse_lazy("gallery_upload")

    def get_form_kwargs(self):
        """Pass provider to form for limit check."""
        kwargs = super().get_form_kwargs()
        kwargs["provider"] = Provider.objects.get(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        """Assign image to current provider."""
        provider = Provider.objects.get(user=self.request.user)
        form.instance.provider = provider
        messages.success(self.request, "Gallery image uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add existing gallery images to context."""
        context = super().get_context_data(**kwargs)
        provider = Provider.objects.get(user=self.request.user)
        context["provider"] = provider
        context["gallery_images"] = ProviderGalleryImage.objects.filter(
            provider=provider
        )
        context["max_images"] = ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER
        return context


class GalleryImageDeleteView(ProviderRequiredMixin, DeleteView):
    """View for deleting a gallery image."""

    model = ProviderGalleryImage
    success_url = reverse_lazy("gallery_upload")
    pk_url_kwarg = "pk"
    http_method_names = ["post"]

    def get_object(self, queryset=None):
        """Get image and verify ownership."""
        image = super().get_object(queryset)
        provider = Provider.objects.get(user=self.request.user)
        if image.provider != provider:
            messages.error(
                self.request, "You do not have permission to delete this image."
            )
            raise PermissionError("Image does not belong to this provider")
        return image

    def post(self, request, *args, **kwargs):
        """Handle deletion with message."""
        try:
            messages.success(request, "Gallery image deleted successfully.")
            return super().post(request, *args, **kwargs)
        except (PermissionError, ProviderGalleryImage.DoesNotExist):
            return redirect("gallery_upload")
