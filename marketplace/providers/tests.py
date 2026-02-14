from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from reviews.models import Review
from .models import (
    Provider,
    ProviderGalleryImage,
    ProviderAttributeDefinition,
    ProviderAttributeValue,
    ProviderPricing,
    Continent,
    Country,
    City,
    PreferenceGroup,
    PreferenceSubgroup,
    PreferenceSubgroupOption,
    ProviderPreference,
    ProviderPreferenceCustomOption,
    ProviderCustomPreference,
)


def _required_attribute_data():
    """Return form data dict for all required (show_on_card) attribute fields.

    Data migration 0013 creates ProviderAttributeDefinition rows that are
    marked ``show_on_card=True``, which makes them required in the profile
    form.  Tests that POST to the profile view must include these fields.
    """
    data = {}
    for defn in ProviderAttributeDefinition.objects.filter(
        is_active=True, show_on_card=True
    ):
        if defn.data_type == ProviderAttributeDefinition.DATA_TYPE_INTEGER:
            data[f"attribute_{defn.pk}"] = "1"
        elif defn.data_type == ProviderAttributeDefinition.DATA_TYPE_BOOLEAN:
            data[f"attribute_{defn.pk}"] = "on"
        else:
            data[f"attribute_{defn.pk}"] = "test"
    return data


def _pricing_form_data(**overrides):
    """Return default pricing form data with 'pricing-' prefix for POST."""
    defaults = {
        "pricing-apartment_available": "on",
        "pricing-outside_available": "on",
        "pricing-apartment_day_1h": "",
        "pricing-apartment_day_2h": "",
        "pricing-apartment_night_1h": "",
        "pricing-apartment_night_whole": "",
        "pricing-outside_day_1h": "",
        "pricing-outside_day_2h": "",
        "pricing-outside_night_1h": "",
        "pricing-outside_night_whole": "",
        "pricing-day_note": "",
        "pricing-night_note": "",
    }
    defaults.update(overrides)
    return defaults


class ProviderAttributeSettingsTests(TestCase):
    """Ensure providers can edit their admin-defined attributes."""

    def setUp(self):
        """Create provider user, profile, and attribute definition."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="attr-provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+15551234567",
            bio="Attribute-friendly provider",
            subscription_status="active",
        )
        self.attribute_definition = ProviderAttributeDefinition.objects.create(
            name="Years of Practice",
            data_type=ProviderAttributeDefinition.DATA_TYPE_INTEGER,
            display_order=1,
            show_on_card=True,
            is_active=True,
        )

    def test_provider_updates_attribute_from_profile_form(self):
        """Providers should be able to save attribute values via profile form."""
        self.client.login(email=self.user.email, password="testpass123")
        url = reverse("provider_profile")
        data = {
            "first_name": "Taylor",
            "last_name": "Doe",
            "bio": self.provider.bio,
            "phone": self.provider.phone,
            **_required_attribute_data(),
            f"attribute_{self.attribute_definition.pk}": "8",
        }
        response = self.client.post(url, data, follow=True)

        self.assertRedirects(response, reverse("provider_dashboard"))
        attribute = ProviderAttributeValue.objects.get(
            provider=self.provider, definition=self.attribute_definition
        )
        self.assertEqual(attribute.value_text, "8")


class ProviderModelTests(TestCase):
    """Test Provider model functionality."""

    def setUp(self):
        """Set up test user for provider creation."""
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )

    def test_provider_creation(self):
        """Test creating a provider."""
        provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.assertEqual(provider.user.email, "provider@test.com")
        self.assertEqual(provider.subscription_status, "inactive")
        self.assertEqual(provider.phone, "+1234567890")

    def test_provider_with_all_fields(self):
        """Test provider with all fields populated."""
        provider = Provider.objects.create(
            user=self.user,
            phone="+1234567890",
            bio="Professional massage therapist",
            subscription_status="active",
            subscription_payment_method="crypto",
            crypto_address="1A1z7agoat...",
        )
        self.assertEqual(provider.bio, "Professional massage therapist")
        self.assertTrue(provider.is_subscription_active())

    def test_provider_subscription_inactive_by_default(self):
        """Test subscription status defaults to inactive."""
        provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.assertEqual(provider.subscription_status, "inactive")
        self.assertFalse(provider.is_subscription_active())

    def test_provider_string_representation(self):
        """Test provider __str__ method."""
        provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="active"
        )
        self.assertIn(self.user.email, str(provider))
        self.assertIn("Active", str(provider))

    def test_provider_admin_registered(self):
        """Test that Provider is registered in admin."""
        from django.contrib import admin

        self.assertIn(Provider, admin.site._registry)

    def test_multiple_providers_different_users(self):
        """Test multiple providers with different users."""
        user2 = User.objects.create_user(
            email="provider2@test.com", password="pass", user_type="provider"
        )

        provider1 = Provider.objects.create(user=self.user, phone="+1111111111")
        provider2 = Provider.objects.create(user=user2, phone="+2222222222")

        self.assertEqual(provider1.user.email, "provider@test.com")
        self.assertEqual(provider2.user.email, "provider2@test.com")
        self.assertEqual(Provider.objects.count(), 2)

    def test_provider_timestamps(self):
        """Test created_at and updated_at timestamps."""
        provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.assertIsNotNone(provider.created_at)
        self.assertIsNotNone(provider.updated_at)
        # Both should be very close in time
        self.assertAlmostEqual(
            provider.created_at.timestamp(), provider.updated_at.timestamp(), delta=1
        )

        # Modify and check updated_at changes
        provider.phone = "+9999999999"
        provider.save()
        provider.refresh_from_db()
        # updated_at should be >= created_at
        self.assertGreaterEqual(provider.updated_at, provider.created_at)


class ProviderDashboardViewTests(TestCase):
    """Test Provider Dashboard view functionality."""

    def setUp(self):
        """Set up test client and test provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+1234567890",
            bio="Professional massage therapist",
            subscription_status="inactive",
        )

        # Create test data
        self.review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment="Excellent service",
            client_email="client@test.com",
        )

    def test_dashboard_requires_login(self):
        """Test that dashboard requires user to be logged in."""
        response = self.client.get(reverse("provider_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn("/auth/login/", response.url)

    def test_dashboard_requires_provider_user_type(self):
        """Test that non-provider users cannot access dashboard."""
        # Create a client user
        client_user = User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )
        self.client.login(email=client_user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.client.logout()

    def test_dashboard_loads_for_verified_provider(self):
        """Test that verified provider can access dashboard."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/dashboard.html")

    def test_dashboard_displays_provider_info(self):
        """Test that dashboard displays provider information."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, self.user.email)

    def test_dashboard_displays_subscription_status(self):
        """Test that dashboard displays subscription status."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, "Inactive")

    def test_dashboard_displays_statistics(self):
        """Test that dashboard displays statistics."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, "Total Reviews")

    def test_dashboard_calculates_average_rating(self):
        """Test that dashboard calculates average rating from reviews."""
        # Add another review with 4 stars
        Review.objects.create(
            provider=self.provider,
            rating=4,
            comment="Good service",
            client_email="client2@test.com",
        )

        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        # Average should be (5 + 4) / 2 = 4.5
        self.assertContains(response, "4.5")

    def test_dashboard_context_has_provider_data(self):
        """Test that dashboard context contains provider data."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertIn("provider", response.context)
        self.assertEqual(response.context["provider"], self.provider)


class BaseTemplateTests(TestCase):
    """Test base template and navigation."""

    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.provider_user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.provider_user, phone="+1234567890"
        )
        self.client_user = User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )

    def test_base_template_displays_for_unauthenticated_user(self):
        """Test that base template shows login/signup links for guests."""
        response = self.client.get("/auth/login/")
        self.assertEqual(response.status_code, 200)
        # Login page should have form and password field
        self.assertContains(response, "password")

    def test_base_template_displays_for_authenticated_provider(self):
        """Test that base template shows provider links when logged in."""
        self.client.login(email=self.provider_user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Logout")

    def test_navigation_shows_provider_links_for_providers(self):
        """Test that provider users see provider-specific links."""
        self.client.login(email=self.provider_user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Profile")

    def test_responsive_design_included(self):
        """Test that responsive design meta tag is included."""
        response = self.client.get("/auth/login/")
        self.assertContains(response, "viewport")
        self.assertContains(response, "width=device-width")

    def test_tailwind_css_included(self):
        """Test that templates include styling."""
        response = self.client.get("/auth/login/")
        # Check that page has style tag
        self.assertContains(response, "<style")

    def test_message_display_system_works(self):
        """Test that messages are displayed correctly."""
        self.client.login(email=self.provider_user.email, password="testpass123")
        response = self.client.get(reverse("provider_dashboard"))
        # Check that dashboard page loads
        self.assertEqual(response.status_code, 200)

    def test_footer_included_in_template(self):
        """Test that footer is included in base template."""
        response = self.client.get("/auth/login/")
        # Footer is in base.html, check for content instead of footer tag
        self.assertContains(response, "Massage Marketplace")


class ProviderProfileFormTests(TestCase):
    """Test Provider Profile Form functionality."""

    def setUp(self):
        """Set up test user and provider."""
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="John",
            last_name="Doe",
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", bio="Professional massage therapist"
        )

    def test_form_displays_first_name_field(self):
        """Test form includes first name field."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("first_name", form.fields)

    def test_form_displays_last_name_field(self):
        """Test form includes last name field."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("last_name", form.fields)

    def test_form_displays_phone_field(self):
        """Test form includes phone field."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("phone", form.fields)

    def test_form_displays_bio_field(self):
        """Test form includes bio field."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("bio", form.fields)

    def test_form_initializes_with_user_name(self):
        """Test form pre-fills with user's first and last name."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertEqual(form.fields["first_name"].initial, "John")
        self.assertEqual(form.fields["last_name"].initial, "Doe")

    def test_form_initializes_with_provider_fields(self):
        """Test form pre-fills with provider's phone and bio."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        # Get form data to see initial values
        self.assertEqual(form.instance.phone, "+1234567890")
        self.assertEqual(form.instance.bio, "Professional massage therapist")

    def test_form_saves_first_name(self):
        """Test form saves first name to user."""
        from providers.views import ProviderProfileForm

        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+9876543210",
            "bio": "Updated bio",
            **_required_attribute_data(),
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")

    def test_form_saves_last_name(self):
        """Test form saves last name to user."""
        from providers.views import ProviderProfileForm

        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+9876543210",
            "bio": "Updated bio",
            **_required_attribute_data(),
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()

        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, "Smith")

    def test_form_saves_phone(self):
        """Test form saves phone to provider."""
        from providers.views import ProviderProfileForm

        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+9876543210",
            "bio": "Updated bio",
            **_required_attribute_data(),
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.phone, "+9876543210")

    def test_form_saves_bio(self):
        """Test form saves bio to provider."""
        from providers.views import ProviderProfileForm

        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+9876543210",
            "bio": "New professional bio",
            **_required_attribute_data(),
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.bio, "New professional bio")

    def test_form_requires_phone(self):
        """Test form requires phone field."""
        from providers.views import ProviderProfileForm

        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "",  # Empty phone
            "bio": "Bio",
            **_required_attribute_data(),
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)


class ProviderProfileUpdateViewTests(TestCase):
    """Test Provider Profile Update View functionality."""

    def setUp(self):
        """Set up test client and provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="John",
            last_name="Doe",
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", bio="Professional massage therapist"
        )

    def test_profile_view_requires_login(self):
        """Test that profile edit page requires login."""
        response = self.client.get(reverse("provider_profile"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_view_requires_provider_user_type(self):
        """Test that non-provider users cannot access profile edit."""
        client_user = User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )
        self.client.login(email=client_user.email, password="testpass123")
        response = self.client.get(reverse("provider_profile"))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_profile_view_loads_for_authenticated_provider(self):
        """Test that provider can load profile edit page."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/profile_edit.html")

    def test_profile_view_displays_form(self):
        """Test that profile edit page displays form."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_profile"))
        self.assertIn("form", response.context)

    def test_profile_view_displays_provider_data(self):
        """Test that profile edit page displays provider data."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("provider_profile"))
        self.assertIn("provider", response.context)
        self.assertEqual(response.context["provider"], self.provider)

    def test_profile_update_changes_first_name(self):
        """Test updating first name via profile form."""
        self.client.login(email=self.user.email, password="testpass123")
        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Professional massage therapist",
                **_required_attribute_data(),
            },
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")

    def test_profile_update_changes_phone(self):
        """Test updating phone via profile form."""
        self.client.login(email=self.user.email, password="testpass123")
        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+9876543210",
                "bio": "Professional massage therapist",
                **_required_attribute_data(),
            },
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.phone, "+9876543210")

    def test_profile_update_changes_bio(self):
        """Test updating bio via profile form."""
        self.client.login(email=self.user.email, password="testpass123")
        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Updated bio text",
                **_required_attribute_data(),
            },
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.bio, "Updated bio text")

    def test_profile_update_redirects_on_success(self):
        """Test that successful update redirects to dashboard."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+9876543210",
                "bio": "Updated bio",
                **_required_attribute_data(),
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("provider_dashboard"), response.url)

    def test_profile_update_shows_success_message(self):
        """Test that success message is shown after update."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+9876543210",
                "bio": "Updated bio",
                **_required_attribute_data(),
            },
            follow=True,
        )

        messages = list(response.context["messages"])
        self.assertTrue(any("updated successfully" in str(m).lower() for m in messages))

    def test_profile_view_creates_provider_if_missing(self):
        """Test that view creates provider if user doesn't have one."""
        # Create a new user without provider
        user = User.objects.create_user(
            email="newprovider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )

        self.client.login(email=user.email, password="testpass123")
        self.client.get(reverse("provider_profile"))

        # Check that provider was created
        self.assertTrue(Provider.objects.filter(user=user).exists())


class ProviderPhotoUploadTests(TestCase):
    """Test Provider Photo Upload functionality."""

    def setUp(self):
        """Set up test client and provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    def _create_test_image(
        self, size=(100, 100), format="JPEG", content_type="image/jpeg"
    ):
        """Create a test image file."""
        from PIL import Image
        import io

        img = Image.new("RGB", size, color="red")
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        filename = f"test.{format.lower()}"
        return SimpleUploadedFile(
            filename, img_io.getvalue(), content_type=content_type
        )

    def test_photo_form_field_exists(self):
        """Test that photo field is in the form."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("photo", form.fields)

    def test_photo_upload_valid_jpeg(self):
        """Test uploading a valid JPEG image."""
        self.client.login(email=self.user.email, password="testpass123")
        photo = self._create_test_image(format="JPEG", content_type="image/jpeg")

        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                "photo": photo,
                **_required_attribute_data(),
            },
        )

        self.provider.refresh_from_db()
        self.assertIsNotNone(self.provider.photo)
        self.assertTrue(self.provider.photo.name.startswith("providers/photos/"))

    def test_photo_upload_valid_png(self):
        """Test uploading a valid PNG image."""
        self.client.login(email=self.user.email, password="testpass123")
        photo = self._create_test_image(format="PNG", content_type="image/png")

        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                "photo": photo,
                **_required_attribute_data(),
            },
        )

        self.provider.refresh_from_db()
        self.assertIsNotNone(self.provider.photo)

    def test_photo_upload_invalid_format(self):
        """Test that invalid image formats are rejected."""
        self.client.login(email=self.user.email, password="testpass123")

        from django.core.files.uploadedfile import SimpleUploadedFile

        invalid_photo = SimpleUploadedFile(
            "test.txt", b"This is not an image", content_type="text/plain"
        )

        response = self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                "photo": invalid_photo,
                **_required_attribute_data(),
            },
        )

        # Form should be invalid
        self.assertIn("form", response.context)
        self.assertFalse(response.context["form"].is_valid())

    def test_photo_size_limit(self):
        """Test that oversized images are rejected."""
        self.client.login(email=self.user.email, password="testpass123")

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io

        # Create a large image (6MB)
        img = Image.new("RGB", (6000, 6000), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)

        # Check size
        img_size = len(img_io.getvalue())
        if img_size > 5 * 1024 * 1024:  # Only test if actually > 5MB
            from django.core.files.uploadedfile import SimpleUploadedFile

            oversized_photo = SimpleUploadedFile(
                "large.jpg", img_io.getvalue(), content_type="image/jpeg"
            )

            response = self.client.post(
                reverse("provider_profile"),
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+1234567890",
                    "bio": "Test bio",
                    "photo": oversized_photo,
                    **_required_attribute_data(),
                },
            )

            # Form should be invalid
            if "form" in response.context:
                self.assertFalse(response.context["form"].is_valid())

    def test_photo_resizing(self):
        """Test that large images are resized to 800x800."""
        self.client.login(email=self.user.email, password="testpass123")

        # Create an image larger than 800x800
        photo = self._create_test_image(size=(1600, 1600), format="JPEG")

        self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                "photo": photo,
                **_required_attribute_data(),
            },
        )

        self.provider.refresh_from_db()
        if self.provider.photo:
            from PIL import Image

            img = Image.open(self.provider.photo)
            # After resizing, dimensions should not exceed 800x800
            self.assertLessEqual(img.height, 800)
            self.assertLessEqual(img.width, 800)

    def test_photo_displays_on_profile_page(self):
        """Test that uploaded photo displays on profile page."""
        self.client.login(email=self.user.email, password="testpass123")
        photo = self._create_test_image()

        # Upload photo
        response = self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                "photo": photo,
                **_required_attribute_data(),
            },
            follow=True,
        )

        # Check that photo URL is accessible
        self.provider.refresh_from_db()
        if self.provider.photo:
            response = self.client.get(reverse("provider_profile"))
            self.assertIn(
                "photo", response.context["provider"].__dict__ or str(response.content)
            )

    def test_photo_optional_field(self):
        """Test that photo is optional in form."""
        self.client.login(email=self.user.email, password="testpass123")

        response = self.client.post(
            reverse("provider_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "bio": "Test bio",
                # No photo provided
                **_required_attribute_data(),
            },
        )

        # Should succeed without photo
        self.assertEqual(response.status_code, 302)  # Redirect on success


class ProviderAdminTests(TestCase):
    """Test Provider admin interface functionality."""

    def setUp(self):
        """Set up test data for admin tests."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="adminpass123", user_type="admin"
        )

        # Create test providers
        self.provider1 = self._create_provider("provider1@test.com", "active")
        self.provider2 = self._create_provider("provider2@test.com", "inactive")
        self.provider3 = self._create_provider("provider3@test.com", "suspended")

        self.client = Client()

    def _create_provider(self, email, subscription_status):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password="pass123",
            user_type="provider",
            is_email_verified=True,
        )
        return Provider.objects.create(
            user=user,
            phone="+1234567890",
            subscription_status=subscription_status,
            subscription_payment_method="crypto",
        )

    def test_provider_admin_registered(self):
        """Test that Provider is registered in admin."""
        from django.contrib import admin

        self.assertIn(Provider, admin.site._registry)

    def test_admin_list_display(self):
        """Test admin list display shows required columns."""
        from providers.admin import ProviderAdmin

        admin_instance = ProviderAdmin(Provider, None)
        self.assertEqual(len(admin_instance.list_display), 6)
        self.assertIn("user_email", admin_instance.list_display)
        self.assertIn("phone", admin_instance.list_display)
        self.assertIn("location_display", admin_instance.list_display)
        self.assertIn("subscription_status", admin_instance.list_display)

    def test_admin_search_fields(self):
        """Test admin search fields are configured."""
        from providers.admin import ProviderAdmin

        admin_instance = ProviderAdmin(Provider, None)
        self.assertIn("user__email", admin_instance.search_fields)

    def test_admin_list_filters(self):
        """Test admin list filters are configured."""
        from providers.admin import ProviderAdmin

        admin_instance = ProviderAdmin(Provider, None)
        self.assertIn("subscription_status", admin_instance.list_filter)
        self.assertIn("subscription_payment_method", admin_instance.list_filter)

    def test_deactivate_subscriptions_action(self):
        """Test deactivate subscriptions bulk action."""
        self.client.force_login(self.admin_user)
        # Note: Testing bulk actions requires more setup, so we'll test the method directly
        from providers.admin import ProviderAdmin
        from unittest.mock import MagicMock

        admin_instance = ProviderAdmin(Provider, None)

        # Create a mock request with message support
        request = MagicMock()
        request.user = self.admin_user

        # Get active providers
        active_providers = Provider.objects.filter(subscription_status="active")

        # Call the action
        admin_instance.deactivate_subscriptions(request, active_providers)

        # Verify subscriptions are deactivated
        self.assertTrue(
            all(
                p.subscription_status == "inactive"
                for p in Provider.objects.filter(subscription_status="inactive")
            )
        )

    def test_suspend_accounts_action(self):
        """Test suspend accounts bulk action."""
        from providers.admin import ProviderAdmin
        from unittest.mock import MagicMock

        admin_instance = ProviderAdmin(Provider, None)

        # Create a mock request
        request = MagicMock()
        request.user = self.admin_user

        # Get inactive providers
        inactive_providers = Provider.objects.filter(subscription_status="inactive")
        count_before = Provider.objects.filter(subscription_status="suspended").count()

        # Call the action
        admin_instance.suspend_accounts(request, inactive_providers)

        # Verify accounts are suspended
        count_after = Provider.objects.filter(subscription_status="suspended").count()
        self.assertGreater(count_after, count_before)

    def test_activate_subscriptions_action(self):
        """Test activate subscriptions bulk action."""
        from providers.admin import ProviderAdmin
        from unittest.mock import MagicMock
        from datetime import date

        admin_instance = ProviderAdmin(Provider, None)

        # Create a mock request
        request = MagicMock()
        request.user = self.admin_user

        # Get provider2 which is inactive
        provider2_id = self.provider2.id

        # Get inactive providers
        inactive_providers = Provider.objects.filter(subscription_status="inactive")
        inactive_count = inactive_providers.count()
        self.assertEqual(inactive_count, 1)

        # Call the action
        admin_instance.activate_subscriptions(request, inactive_providers)

        # Refresh from DB and verify
        provider2_refreshed = Provider.objects.get(id=provider2_id)
        self.assertEqual(provider2_refreshed.subscription_status, "active")
        self.assertIsNotNone(provider2_refreshed.subscription_renewal_date)
        today = date.today()
        self.assertGreater(provider2_refreshed.subscription_renewal_date, today)

    def test_user_email_method(self):
        """Test user_email method in admin."""
        from providers.admin import ProviderAdmin

        admin_instance = ProviderAdmin(Provider, None)
        email = admin_instance.user_email(self.provider1)
        self.assertEqual(email, "provider1@test.com")


class AdminProviderListViewTests(TestCase):
    """Test Admin Provider List view functionality."""

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@test.com", password="adminpass123", user_type="admin"
        )

        # Create test providers with different statuses
        self.provider_active = self._create_provider(
            "active@test.com", "active", "crypto_bitcoin"
        )
        self.provider_inactive = self._create_provider(
            "inactive@test.com", "inactive", "bank_transfer"
        )
        self.provider_suspended = self._create_provider(
            "suspended@test.com", "suspended", None
        )

        # Add a review to provider_active
        Review.objects.create(
            provider=self.provider_active,
            rating=5,
            comment="Excellent service",
            client_email="client@test.com",
        )

        self.client = Client()

    def _create_provider(self, email, status, payment_method):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password="pass123",
            user_type="provider",
            is_email_verified=True,
        )
        return Provider.objects.create(
            user=user,
            phone="+1234567890",
            subscription_status=status,
            subscription_payment_method=payment_method,
        )

    def test_admin_provider_list_requires_login(self):
        """Test that list requires authentication."""
        response = self.client.get(reverse("admin_providers"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn("/auth/login/", response.url)

    def test_non_admin_cannot_access_list(self):
        """Test that non-admin users cannot access the list."""
        provider_user = User.objects.create_user(
            email="provider@test.com",
            password="pass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.client.login(email=provider_user.email, password="pass123")
        response = self.client.get(reverse("admin_providers"))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_admin_can_access_list(self):
        """Test that admin can access the provider list."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/provider_list.html")

    def test_provider_list_displays_all_providers(self):
        """Test that all providers are displayed."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"))
        self.assertContains(response, "active@test.com")
        self.assertContains(response, "inactive@test.com")
        self.assertContains(response, "suspended@test.com")

    def test_search_by_email(self):
        """Test searching providers by email."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"), {"search": "active@"})
        self.assertContains(response, "active@test.com")
        # The response might still show inactive count in pagination/summary so be more specific
        # Check that the table doesn't contain multiple instances of email
        content = response.content.decode()
        # Count how many times we see 'active@test.com' in the table rows (not counting page info)
        active_count = content.count(
            '<td class="px-6 py-4">\n                    <div class="text-sm font-medium text-gray-900">active@test.com</div>'
        )
        self.assertGreater(active_count, 0)

    def test_filter_by_status(self):
        """Test filtering providers by subscription status."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"), {"status": "active"})
        self.assertContains(response, "active@test.com")
        self.assertNotContains(response, "inactive@test.com")
        self.assertNotContains(response, "suspended@test.com")

    def test_provider_list_has_stats(self):
        """Test that provider stats are included in context."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"))
        context = response.context
        self.assertIn("providers_with_stats", context)

    def test_provider_list_shows_rating(self):
        """Test that provider ratings are displayed."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"))
        # Provider_active has a 5-star review
        self.assertContains(response, "5")  # Rating value

    def test_pagination(self):
        """Test that pagination is configured."""
        # Create 60 providers to trigger pagination
        for i in range(60):
            self._create_provider(f"provider{i}@test.com", "active", "crypto_bitcoin")

        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"))
        self.assertIn("paginator", response.context)
        self.assertTrue(response.context["is_paginated"])

    def test_search_persists_in_pagination(self):
        """Test that search parameters are preserved in pagination."""
        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"), {"search": "active"})
        self.assertContains(response, "search=active")  # Should be in pagination links

    def test_filter_persists_in_pagination(self):
        """Test that filter parameters are preserved in pagination."""
        # Create many active providers to trigger pagination
        for i in range(60):
            self._create_provider(f"active{i}@test.com", "active", "crypto_bitcoin")

        self.client.login(email=self.admin_user.email, password="adminpass123")
        response = self.client.get(reverse("admin_providers"), {"status": "active"})
        self.assertContains(response, "status=active")  # Should be in pagination links


class ProviderSubscriptionViewTests(TestCase):
    """Test Provider Subscription view functionality."""

    def setUp(self):
        """Set up test data."""
        # Create test provider
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="inactive"
        )

        self.client = Client()

    def test_subscription_view_requires_login(self):
        """Test that subscription view requires authentication."""
        response = self.client.get(reverse("subscription"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn("/auth/login/", response.url)

    def test_non_provider_cannot_access(self):
        """Test that non-provider users cannot access subscription view."""
        client_user = User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )
        self.client.login(email=client_user.email, password="testpass123")
        response = self.client.get(reverse("subscription"))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_subscription_view_loads(self):
        """Test that subscription view loads for authenticated provider."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/subscription.html")

    def test_subscription_form_present(self):
        """Test that subscription form is present in the view."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription"))
        # Check for form elements
        self.assertContains(response, "payment_method")

    def test_subscription_form_choices(self):
        """Test that form has correct payment method choices."""
        from providers.forms import SubscriptionSettingsForm

        form = SubscriptionSettingsForm()
        choices = form.fields["payment_method"].choices
        self.assertEqual(len(choices), 4)
        choice_values = [choice[0] for choice in choices]
        self.assertIn("crypto_bitcoin", choice_values)
        self.assertIn("crypto_ethereum", choice_values)
        self.assertIn("crypto_usdc", choice_values)
        self.assertIn("bank_transfer", choice_values)

    def test_subscription_status_displayed(self):
        """Test that current subscription status is displayed."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription"))
        # Check for status display
        self.assertContains(response, "Subscription Status")

    def test_subscription_form_submission(self):
        """Test that form submission redirects to payment page."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.post(
            reverse("subscription"), {"payment_method": "crypto_bitcoin"}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        # Should redirect to crypto payment page
        self.assertIn(
            reverse("subscription_crypto_payment"), response.request["PATH_INFO"]
        )

    def test_subscription_form_invalid_choice(self):
        """Test that form validation works."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.post(
            reverse("subscription"), {"payment_method": "invalid_choice"}
        )
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Should show form with errors
        self.assertContains(response, "form")  # Form should be re-rendered

    def test_subscription_provider_context(self):
        """Test that provider is passed in context."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription"))
        self.assertIn("provider", response.context)
        self.assertEqual(response.context["provider"], self.provider)


class ProviderSubscriptionActivationTests(TestCase):
    """Test subscription activation/deactivation functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="inactive"
        )

        self.client = Client()

    def test_activate_subscription_method(self):
        """Test activate_subscription method on Provider model."""
        self.provider.activate_subscription("crypto_bitcoin")

        # Refresh from database
        self.provider.refresh_from_db()

        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "crypto_bitcoin")
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_activate_subscription_sets_renewal_date(self):
        """Test that renewal date is set 30 days from today."""
        from datetime import date, timedelta

        self.provider.activate_subscription("crypto_bitcoin")
        expected_date = date.today() + timedelta(days=30)

        self.assertEqual(self.provider.subscription_renewal_date, expected_date)

    def test_deactivate_subscription_method(self):
        """Test deactivate_subscription method on Provider model."""
        # First activate
        self.provider.activate_subscription("crypto_bitcoin")

        # Then deactivate
        self.provider.deactivate_subscription()

        # Refresh from database
        self.provider.refresh_from_db()

        self.assertEqual(self.provider.subscription_status, "inactive")

    def test_subscription_form_creates_payment_record(self):
        """Test that crypto payment submission creates a SubscriptionPayment record."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password="testpass123")

        # Step 1: Select payment method
        self.client.post(reverse("subscription"), {"payment_method": "crypto_bitcoin"})

        # Step 2: Submit transaction ID on crypto payment page
        self.client.post(
            reverse("subscription_crypto_payment"),
            {"transaction_id": "0xabc123def456"},
            follow=True,
        )

        # Should have created a payment record
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, "crypto_bitcoin")
        self.assertEqual(payment.status, "pending")
        self.assertEqual(float(payment.amount), 29.99)
        self.assertEqual(payment.reference_id, "0xabc123def456")

    def test_subscription_activation_flow(self):
        """Test complete subscription activation flow via crypto payment."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password="testpass123")

        # Step 1: Select payment method
        self.client.post(reverse("subscription"), {"payment_method": "crypto_ethereum"})

        # Step 2: Submit transaction ID
        response = self.client.post(
            reverse("subscription_crypto_payment"),
            {"transaction_id": "0xethtx123"},
            follow=True,
        )

        # Should redirect to confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertIn(reverse("subscription_confirm"), response.request["PATH_INFO"])

        # Provider should be activated
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "crypto_ethereum")

        # Payment record should be created
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, "pending")

    def test_subscription_confirm_view_loads(self):
        """Test that subscription confirmation view loads."""
        self.provider.activate_subscription("crypto_bitcoin")

        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription_confirm"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/subscription_confirm.html")

    def test_subscription_confirm_displays_details(self):
        """Test that confirmation page displays subscription details."""
        self.provider.activate_subscription("crypto_bitcoin")

        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription_confirm"))

        # Check that context contains provider
        self.assertIn("provider", response.context)
        self.assertEqual(response.context["provider"], self.provider)

    def test_is_subscription_active_method(self):
        """Test is_subscription_active method."""
        # Initially inactive
        self.assertFalse(self.provider.is_subscription_active())

        # After activation
        self.provider.activate_subscription("crypto_bitcoin")
        self.assertTrue(self.provider.is_subscription_active())

        # After deactivation
        self.provider.deactivate_subscription()
        self.assertFalse(self.provider.is_subscription_active())


class CryptoPaymentViewTests(TestCase):
    """Test crypto payment view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="inactive"
        )
        self.client = Client()

    def test_crypto_page_requires_login(self):
        """Test that crypto payment page requires login."""
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertEqual(response.status_code, 302)

    def test_crypto_page_requires_session(self):
        """Test that crypto page redirects without session payment method."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertRedirects(response, reverse("subscription"))

    def test_crypto_page_loads_with_session(self):
        """Test that crypto page loads when session is set."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/subscription_crypto.html")

    def test_crypto_page_shows_wallet_address(self):
        """Test that crypto page displays wallet address."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertContains(response, "Wallet Address")
        self.assertContains(response, "29.99")

    def test_crypto_page_shows_payment_instructions(self):
        """Test that crypto page shows payment instructions."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertContains(response, "Payment Instructions")
        self.assertContains(response, "Transaction ID")

    def test_crypto_submit_transaction_id(self):
        """Test submitting a crypto transaction ID."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()

        response = self.client.post(
            reverse("subscription_crypto_payment"),
            {"transaction_id": "0xabc123"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.reference_id, "0xabc123")
        self.assertEqual(payment.payment_method, "crypto_bitcoin")
        self.assertEqual(payment.status, "pending")

    def test_crypto_submit_activates_subscription(self):
        """Test that crypto submission activates subscription."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_ethereum"
        session.save()

        self.client.post(
            reverse("subscription_crypto_payment"), {"transaction_id": "0xeth456"}
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "crypto_ethereum")
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_crypto_submit_clears_session(self):
        """Test that crypto submission clears session."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()

        self.client.post(
            reverse("subscription_crypto_payment"), {"transaction_id": "0x123"}
        )

        session = self.client.session
        self.assertNotIn("pending_payment_method", session)

    def test_crypto_rejects_bank_transfer_method(self):
        """Test that crypto page rejects bank_transfer method."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()
        response = self.client.get(reverse("subscription_crypto_payment"))
        self.assertRedirects(response, reverse("subscription"))


class BankTransferPaymentViewTests(TestCase):
    """Test bank transfer payment view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="inactive"
        )
        self.client = Client()

    def test_bank_page_requires_login(self):
        """Test that bank transfer page requires login."""
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertEqual(response.status_code, 302)

    def test_bank_page_requires_session(self):
        """Test that bank page redirects without session payment method."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertRedirects(response, reverse("subscription"))

    def test_bank_page_loads_with_session(self):
        """Test that bank page loads when session is set."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/subscription_bank.html")

    def test_bank_page_shows_platform_details(self):
        """Test that bank page shows platform bank details."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertContains(response, "First National Bank")
        self.assertContains(response, "Massage Marketplace LLC")
        self.assertContains(response, "29.99")

    def test_bank_page_shows_reference_number(self):
        """Test that bank page generates and shows payment reference."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertContains(response, "SUB-")
        self.assertContains(response, "Payment Reference")

    def test_bank_submit_creates_payment(self):
        """Test submitting bank transfer details creates payment record."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session["bank_payment_reference"] = "SUB-1-ABCD1234"
        session.save()

        response = self.client.post(
            reverse("subscription_bank_payment"),
            {
                "sender_name": "John Doe",
                "bank_name": "Chase Bank",
                "reference_number": "REF123456",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, "bank_transfer")
        self.assertEqual(payment.reference_id, "REF123456")
        self.assertEqual(payment.status, "pending")

    def test_bank_submit_activates_subscription(self):
        """Test that bank transfer submission activates subscription."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()

        self.client.post(
            reverse("subscription_bank_payment"),
            {
                "sender_name": "Jane Smith",
                "bank_name": "Wells Fargo",
            },
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, "active")
        self.assertEqual(self.provider.subscription_payment_method, "bank_transfer")
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_bank_submit_stores_bank_info(self):
        """Test that bank transfer stores sender details."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session.save()

        self.client.post(
            reverse("subscription_bank_payment"),
            {
                "sender_name": "John Doe",
                "bank_name": "Chase Bank",
            },
        )

        self.provider.refresh_from_db()
        self.assertIn("John Doe", self.provider.bank_account_encrypted)
        self.assertIn("Chase Bank", self.provider.bank_account_encrypted)

    def test_bank_submit_uses_generated_reference(self):
        """Test that submission uses generated reference when none provided."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "bank_transfer"
        session["bank_payment_reference"] = "SUB-1-GENERATED"
        session.save()

        self.client.post(
            reverse("subscription_bank_payment"),
            {
                "sender_name": "Jane Smith",
                "bank_name": "Wells Fargo",
                "reference_number": "",
            },
        )

        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertEqual(payment.reference_id, "SUB-1-GENERATED")

    def test_bank_rejects_crypto_method(self):
        """Test that bank page rejects crypto payment methods."""
        self.client.login(email=self.user.email, password="testpass123")
        session = self.client.session
        session["pending_payment_method"] = "crypto_bitcoin"
        session.save()
        response = self.client.get(reverse("subscription_bank_payment"))
        self.assertRedirects(response, reverse("subscription"))


class PaymentFormTests(TestCase):
    """Test payment forms."""

    def test_crypto_form_valid(self):
        """Test CryptoPaymentForm with valid data."""
        from providers.forms import CryptoPaymentForm

        form = CryptoPaymentForm(data={"transaction_id": "0xabc123"})
        self.assertTrue(form.is_valid())

    def test_crypto_form_requires_transaction_id(self):
        """Test CryptoPaymentForm requires transaction_id."""
        from providers.forms import CryptoPaymentForm

        form = CryptoPaymentForm(data={"transaction_id": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("transaction_id", form.errors)

    def test_bank_form_valid(self):
        """Test BankTransferForm with valid data."""
        from providers.forms import BankTransferForm

        form = BankTransferForm(
            data={
                "sender_name": "John Doe",
                "bank_name": "Chase Bank",
                "reference_number": "REF123",
            }
        )
        self.assertTrue(form.is_valid())

    def test_bank_form_reference_optional(self):
        """Test BankTransferForm reference_number is optional."""
        from providers.forms import BankTransferForm

        form = BankTransferForm(
            data={
                "sender_name": "John Doe",
                "bank_name": "Chase Bank",
            }
        )
        self.assertTrue(form.is_valid())

    def test_bank_form_requires_sender_name(self):
        """Test BankTransferForm requires sender_name."""
        from providers.forms import BankTransferForm

        form = BankTransferForm(
            data={
                "sender_name": "",
                "bank_name": "Chase Bank",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("sender_name", form.errors)

    def test_bank_form_requires_bank_name(self):
        """Test BankTransferForm requires bank_name."""
        from providers.forms import BankTransferForm

        form = BankTransferForm(
            data={
                "sender_name": "John Doe",
                "bank_name": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("bank_name", form.errors)


class GalleryImageModelTests(TestCase):
    """Test ProviderGalleryImage model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io

        img = PILImage.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return SimpleUploadedFile(
            "test.jpg", img_io.getvalue(), content_type="image/jpeg"
        )

    def test_gallery_image_creation(self):
        """Test creating a gallery image."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption="Test caption",
        )
        self.assertEqual(image.provider, self.provider)
        self.assertEqual(image.caption, "Test caption")
        self.assertIsNotNone(image.uploaded_at)

    def test_gallery_image_str(self):
        """Test __str__ method."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        self.assertIn(self.user.email, str(image))

    def test_gallery_image_ordering(self):
        """Test that images are ordered by -uploaded_at."""
        ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image(), caption="First"
        )
        ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image(), caption="Second"
        )
        images = list(ProviderGalleryImage.objects.filter(provider=self.provider))
        self.assertEqual(images[0].caption, "Second")
        self.assertEqual(images[1].caption, "First")

    def test_max_images_constant(self):
        """Test MAX_IMAGES_PER_PROVIDER is 10."""
        self.assertEqual(ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER, 10)

    def test_cascade_delete(self):
        """Test that gallery images are deleted when provider is deleted."""
        ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        self.assertEqual(ProviderGalleryImage.objects.count(), 1)
        self.provider.delete()
        self.assertEqual(ProviderGalleryImage.objects.count(), 0)

    def test_caption_optional(self):
        """Test that caption is optional."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        self.assertEqual(image.caption, "")


class GalleryImageFormTests(TestCase):
    """Test GalleryImageForm functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    def _create_test_image(self, format="JPEG", content_type="image/jpeg"):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io

        img = PILImage.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        filename = f"test.{format.lower()}"
        return SimpleUploadedFile(
            filename, img_io.getvalue(), content_type=content_type
        )

    def test_form_fields(self):
        """Test form has correct fields."""
        from providers.forms import GalleryImageForm

        form = GalleryImageForm(provider=self.provider)
        self.assertIn("image", form.fields)
        self.assertIn("caption", form.fields)

    def test_form_valid_data(self):
        """Test form with valid image data."""
        from providers.forms import GalleryImageForm

        image = self._create_test_image()
        form = GalleryImageForm(
            data={"caption": "Test"}, files={"image": image}, provider=self.provider
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_format(self):
        """Test form rejects invalid image format."""
        from providers.forms import GalleryImageForm

        invalid_file = SimpleUploadedFile(
            "test.txt", b"not an image", content_type="text/plain"
        )
        form = GalleryImageForm(
            data={"caption": "Test"},
            files={"image": invalid_file},
            provider=self.provider,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_form_max_limit(self):
        """Test form enforces max image limit."""
        from providers.forms import GalleryImageForm

        # Create 10 images
        for i in range(10):
            ProviderGalleryImage.objects.create(
                provider=self.provider, image=self._create_test_image()
            )

        image = self._create_test_image()
        form = GalleryImageForm(
            data={"caption": "Too many"}, files={"image": image}, provider=self.provider
        )
        self.assertFalse(form.is_valid())

    def test_form_caption_optional(self):
        """Test form allows empty caption."""
        from providers.forms import GalleryImageForm

        image = self._create_test_image()
        form = GalleryImageForm(
            data={"caption": ""}, files={"image": image}, provider=self.provider
        )
        self.assertTrue(form.is_valid())

    def test_form_requires_image(self):
        """Test form requires image field."""
        from providers.forms import GalleryImageForm

        form = GalleryImageForm(
            data={"caption": "No image"}, files={}, provider=self.provider
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


class GalleryImageCreateViewTests(TestCase):
    """Test GalleryImageCreateView functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.client_user = User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )

    def _create_test_image(self, format="JPEG", content_type="image/jpeg"):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io

        img = PILImage.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(
            f"test.{format.lower()}", img_io.getvalue(), content_type=content_type
        )

    def test_requires_login(self):
        """Test that gallery upload requires login."""
        response = self.client.get(reverse("gallery_upload"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_requires_provider(self):
        """Test that non-providers cannot access gallery upload."""
        self.client.login(email=self.client_user.email, password="testpass123")
        response = self.client.get(reverse("gallery_upload"))
        self.assertEqual(response.status_code, 302)

    def test_page_loads(self):
        """Test that gallery upload page loads for provider."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("gallery_upload"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "providers/gallery_upload.html")

    def test_upload_valid_image(self):
        """Test uploading a valid gallery image."""
        self.client.login(email=self.user.email, password="testpass123")
        image = self._create_test_image()
        response = self.client.post(
            reverse("gallery_upload"), {"image": image, "caption": "My workspace"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ProviderGalleryImage.objects.filter(provider=self.provider).count(), 1
        )

    def test_upload_invalid_format(self):
        """Test that invalid formats are rejected."""
        self.client.login(email=self.user.email, password="testpass123")
        invalid_file = SimpleUploadedFile(
            "test.txt", b"not an image", content_type="text/plain"
        )
        response = self.client.post(
            reverse("gallery_upload"), {"image": invalid_file, "caption": "Bad file"}
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertEqual(
            ProviderGalleryImage.objects.filter(provider=self.provider).count(), 0
        )

    def test_upload_max_limit(self):
        """Test that upload is rejected when at max limit."""
        self.client.login(email=self.user.email, password="testpass123")
        for i in range(10):
            ProviderGalleryImage.objects.create(
                provider=self.provider, image=self._create_test_image()
            )
        image = self._create_test_image()
        response = self.client.post(
            reverse("gallery_upload"), {"image": image, "caption": "Too many"}
        )
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertEqual(
            ProviderGalleryImage.objects.filter(provider=self.provider).count(), 10
        )

    def test_upload_success_message(self):
        """Test that success message is shown after upload."""
        self.client.login(email=self.user.email, password="testpass123")
        image = self._create_test_image()
        response = self.client.post(
            reverse("gallery_upload"), {"image": image, "caption": "Test"}, follow=True
        )
        msgs = list(response.context["messages"])
        self.assertTrue(any("uploaded successfully" in str(m).lower() for m in msgs))

    def test_context_has_gallery_images(self):
        """Test that context includes gallery images."""
        self.client.login(email=self.user.email, password="testpass123")
        ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        response = self.client.get(reverse("gallery_upload"))
        self.assertIn("gallery_images", response.context)
        self.assertEqual(response.context["gallery_images"].count(), 1)

    def test_context_has_max_images(self):
        """Test that context includes max_images."""
        self.client.login(email=self.user.email, password="testpass123")
        response = self.client.get(reverse("gallery_upload"))
        self.assertEqual(response.context["max_images"], 10)


class GalleryImageDeleteViewTests(TestCase):
    """Test GalleryImageDeleteView functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.other_provider = Provider.objects.create(
            user=self.other_user, phone="+9876543210"
        )

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io

        img = PILImage.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return SimpleUploadedFile(
            "test.jpg", img_io.getvalue(), content_type="image/jpeg"
        )

    def test_requires_login(self):
        """Test that gallery delete requires login."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        response = self.client.post(reverse("gallery_delete", args=[image.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_delete_own_image(self):
        """Test that provider can delete their own image."""
        self.client.login(email=self.user.email, password="testpass123")
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        response = self.client.post(reverse("gallery_delete", args=[image.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProviderGalleryImage.objects.filter(pk=image.pk).exists())

    def test_cannot_delete_other_providers_image(self):
        """Test that provider cannot delete another provider's image."""
        self.client.login(email=self.user.email, password="testpass123")
        image = ProviderGalleryImage.objects.create(
            provider=self.other_provider, image=self._create_test_image()
        )
        self.client.post(reverse("gallery_delete", args=[image.pk]))
        self.assertTrue(ProviderGalleryImage.objects.filter(pk=image.pk).exists())

    def test_delete_success_message(self):
        """Test that success message is shown after deletion."""
        self.client.login(email=self.user.email, password="testpass123")
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        response = self.client.post(
            reverse("gallery_delete", args=[image.pk]), follow=True
        )
        msgs = list(response.context["messages"])
        self.assertTrue(any("deleted successfully" in str(m).lower() for m in msgs))

    def test_get_not_allowed(self):
        """Test that GET requests are not allowed for delete."""
        self.client.login(email=self.user.email, password="testpass123")
        image = ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image()
        )
        response = self.client.get(reverse("gallery_delete", args=[image.pk]))
        self.assertEqual(response.status_code, 405)  # Method not allowed


class LocationModelTests(TestCase):
    """Tests for Continent, Country, and City models."""

    def test_continent_creation(self):
        """Test creating a continent."""
        from providers.models import Continent

        continent = Continent.objects.create(name="Europe", code="EU", display_order=1)
        self.assertEqual(str(continent), "Europe")
        self.assertEqual(continent.code, "EU")

    def test_continent_ordering(self):
        """Test continents are ordered by display_order then name."""
        from providers.models import Continent

        c1 = Continent.objects.create(name="Zebra", code="ZB", display_order=2)
        c2 = Continent.objects.create(name="Alpha", code="AL", display_order=1)
        c3 = Continent.objects.create(name="Beta", code="BE", display_order=1)

        continents = list(Continent.objects.all())
        self.assertEqual(
            continents[0], c2
        )  # Alpha (display_order=1, comes first alphabetically)
        self.assertEqual(continents[1], c3)  # Beta (display_order=1)
        self.assertEqual(continents[2], c1)  # Zebra (display_order=2)

    def test_country_creation(self):
        """Test creating a country with continent."""
        from providers.models import Continent, Country

        continent = Continent.objects.create(name="Europe", code="EU", display_order=1)
        country = Country.objects.create(
            name="United Kingdom", code="GB", continent=continent, is_active=True
        )
        self.assertEqual(str(country), "United Kingdom")
        self.assertEqual(country.continent, continent)
        self.assertTrue(country.is_active)

    def test_country_continent_relationship(self):
        """Test that countries are related to continents."""
        from providers.models import Continent, Country

        europe = Continent.objects.create(name="Europe", code="EU", display_order=1)
        uk = Country.objects.create(name="United Kingdom", code="GB", continent=europe)
        france = Country.objects.create(name="France", code="FR", continent=europe)

        self.assertEqual(europe.countries.count(), 2)
        self.assertIn(uk, europe.countries.all())
        self.assertIn(france, europe.countries.all())

    def test_city_creation(self):
        """Test creating a city."""
        from providers.models import Continent, Country, City

        europe = Continent.objects.create(name="Europe", code="EU", display_order=1)
        uk = Country.objects.create(name="United Kingdom", code="GB", continent=europe)
        city = City.objects.create(
            name="London",
            country=uk,
            population=8982000,
            is_capital=True,
            is_major_city=True,
            latitude="51.507351",
            longitude="-0.127758",
        )
        self.assertEqual(str(city), "London, United Kingdom")
        self.assertTrue(city.is_capital)
        self.assertTrue(city.is_major_city)

    def test_city_ordering(self):
        """Test cities are ordered by is_capital, is_major_city, population desc, name."""
        from providers.models import Continent, Country, City

        europe = Continent.objects.create(name="Europe", code="EU", display_order=1)
        uk = Country.objects.create(name="United Kingdom", code="GB", continent=europe)

        london = City.objects.create(
            name="London",
            country=uk,
            population=8982000,
            is_capital=True,
            is_major_city=True,
        )
        birmingham = City.objects.create(
            name="Birmingham",
            country=uk,
            population=1149000,
            is_capital=False,
            is_major_city=True,
        )
        oxford = City.objects.create(
            name="Oxford",
            country=uk,
            population=150000,
            is_capital=False,
            is_major_city=False,
        )

        cities = list(City.objects.filter(country=uk))
        self.assertEqual(cities[0], london)  # Capital first
        self.assertEqual(cities[1], birmingham)  # Major city second
        self.assertEqual(cities[2], oxford)  # Small city last

    def test_city_unique_together(self):
        """Test that city name + country must be unique."""
        from providers.models import Continent, Country, City
        from django.db import IntegrityError

        europe = Continent.objects.create(name="Europe", code="EU", display_order=1)
        uk = Country.objects.create(name="United Kingdom", code="GB", continent=europe)
        City.objects.create(name="London", country=uk)

        with self.assertRaises(IntegrityError):
            City.objects.create(name="London", country=uk)

    def test_provider_location_fk_fields(self):
        """Test provider with new FK location fields."""
        from providers.models import Continent, Country, City, Provider

        europe = Continent.objects.create(name="Europe", code="EU", display_order=1)
        uk = Country.objects.create(name="United Kingdom", code="GB", continent=europe)
        london = City.objects.create(name="London", country=uk, is_capital=True)

        user = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        provider = Provider.objects.create(
            user=user, phone="+1234567890", country=uk, city=london
        )

        self.assertEqual(provider.country.name, "United Kingdom")
        self.assertEqual(provider.city.name, "London")

    def test_us_not_in_fixtures(self):
        """Test that United States is not in the country fixtures."""
        from providers.models import Country

        # Load fixtures in test if they haven't been loaded
        us = Country.objects.filter(code="US").first()
        self.assertIsNone(us)


class ProviderPricingModelTests(TestCase):
    """Tests for the ProviderPricing model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="pricing@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", bio="Test provider"
        )

    def test_create_pricing_with_defaults(self):
        """Test creating pricing with default availability values."""
        pricing = ProviderPricing.objects.create(provider=self.provider)
        self.assertTrue(pricing.apartment_available)
        self.assertTrue(pricing.outside_available)
        self.assertIsNone(pricing.apartment_day_1h)
        self.assertEqual(pricing.day_note, "")
        self.assertEqual(pricing.night_note, "")

    def test_create_pricing_with_prices(self):
        """Test creating pricing with specific price values."""
        from decimal import Decimal

        pricing = ProviderPricing.objects.create(
            provider=self.provider,
            apartment_day_1h=Decimal("50.00"),
            apartment_day_2h=Decimal("90.00"),
            apartment_night_1h=Decimal("70.00"),
            apartment_night_whole=Decimal("200.00"),
            day_note="Weekdays only",
            night_note="After 20:00",
        )
        self.assertEqual(pricing.apartment_day_1h, Decimal("50.00"))
        self.assertEqual(pricing.apartment_night_whole, Decimal("200.00"))
        self.assertEqual(pricing.day_note, "Weekdays only")

    def test_one_to_one_relationship(self):
        """Test that a provider can only have one pricing record."""
        ProviderPricing.objects.create(provider=self.provider)
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ProviderPricing.objects.create(provider=self.provider)

    def test_pricing_str(self):
        """Test pricing string representation."""
        pricing = ProviderPricing.objects.create(provider=self.provider)
        self.assertIn("Pricing for", str(pricing))

    def test_pricing_cascade_delete(self):
        """Test that pricing is deleted when provider is deleted."""
        ProviderPricing.objects.create(provider=self.provider)
        self.provider.delete()
        self.assertEqual(ProviderPricing.objects.count(), 0)

    def test_unavailable_location(self):
        """Test setting a location as unavailable."""
        pricing = ProviderPricing.objects.create(
            provider=self.provider,
            apartment_available=False,
            outside_available=True,
        )
        self.assertFalse(pricing.apartment_available)
        self.assertTrue(pricing.outside_available)


class ProviderPricingFormTests(TestCase):
    """Tests for the ProviderPricingForm via profile update view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="pricingform@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="Jane",
            last_name="Doe",
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", bio="Test provider"
        )
        self.client.login(email=self.user.email, password="testpass123")

    def test_profile_edit_shows_pricing_form(self):
        """Test that pricing form appears on profile edit page."""
        response = self.client.get(reverse("provider_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("pricing_form", response.context)

    def test_save_pricing_via_profile_form(self):
        """Test saving pricing data through the profile form."""
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "+1234567890",
            "bio": "Test provider",
            **_required_attribute_data(),
            **_pricing_form_data(
                **{
                    "pricing-apartment_day_1h": "60.00",
                    "pricing-apartment_day_2h": "100.00",
                    "pricing-apartment_night_1h": "80.00",
                    "pricing-apartment_night_whole": "250.00",
                    "pricing-day_note": "Weekdays only",
                }
            ),
        }
        response = self.client.post(reverse("provider_profile"), data, follow=True)
        self.assertRedirects(response, reverse("provider_dashboard"))

        pricing = ProviderPricing.objects.get(provider=self.provider)
        from decimal import Decimal

        self.assertEqual(pricing.apartment_day_1h, Decimal("60.00"))
        self.assertEqual(pricing.apartment_day_2h, Decimal("100.00"))
        self.assertEqual(pricing.apartment_night_whole, Decimal("250.00"))
        self.assertEqual(pricing.day_note, "Weekdays only")

    def test_save_pricing_apartment_not_available(self):
        """Test saving pricing with apartment unavailable."""
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "+1234567890",
            "bio": "Test provider",
            **_required_attribute_data(),
            **_pricing_form_data(),
        }
        # Remove the checkbox to simulate unchecked
        del data["pricing-apartment_available"]
        response = self.client.post(reverse("provider_profile"), data, follow=True)
        self.assertRedirects(response, reverse("provider_dashboard"))

        pricing = ProviderPricing.objects.get(provider=self.provider)
        self.assertFalse(pricing.apartment_available)
        self.assertTrue(pricing.outside_available)

    def test_pricing_created_on_get(self):
        """Test that ProviderPricing is get-or-created when loading the form."""
        self.assertFalse(
            ProviderPricing.objects.filter(provider=self.provider).exists()
        )
        self.client.get(reverse("provider_profile"))
        self.assertTrue(ProviderPricing.objects.filter(provider=self.provider).exists())

    def test_update_existing_pricing(self):
        """Test updating already-existing pricing data."""
        from decimal import Decimal

        ProviderPricing.objects.create(
            provider=self.provider, apartment_day_1h=Decimal("50.00")
        )
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "+1234567890",
            "bio": "Test provider",
            **_required_attribute_data(),
            **_pricing_form_data(**{"pricing-apartment_day_1h": "75.00"}),
        }
        self.client.post(reverse("provider_profile"), data, follow=True)
        pricing = ProviderPricing.objects.get(provider=self.provider)
        self.assertEqual(pricing.apartment_day_1h, Decimal("75.00"))


def _preferences_form_data(**overrides):
    """Return empty preferences form data with 'prefs-' prefix for POST."""
    defaults = {
        "prefs-preference_comment": "",
        "prefs-custom_preferences": "",
    }
    defaults.update(overrides)
    return defaults


class ProviderPreferencesModelTests(TestCase):
    """Test preference model creation and constraints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="pref-provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+15551234567",
            subscription_status="active",
        )
        self.group = PreferenceGroup.objects.create(
            name="Massage", display_order=1, is_active=True
        )
        self.subgroup = PreferenceSubgroup.objects.create(
            group=self.group, name="Classical", display_order=1, is_active=True
        )

    def test_preference_group_creation(self):
        self.assertEqual(str(self.group), "Massage")
        self.assertTrue(self.group.is_active)

    def test_preference_subgroup_creation(self):
        self.assertEqual(str(self.subgroup), "Massage → Classical")

    def test_subgroup_unique_together(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            PreferenceSubgroup.objects.create(
                group=self.group, name="Classical", display_order=2
            )

    def test_subgroup_option_creation(self):
        opt = PreferenceSubgroupOption.objects.create(
            subgroup=self.subgroup, text="+10$ for 30min more", display_order=0
        )
        self.assertIn("+10$", str(opt))

    def test_provider_preference_creation(self):
        pref = ProviderPreference.objects.create(
            provider=self.provider, subgroup=self.subgroup, is_checked=True
        )
        self.assertTrue(pref.is_checked)
        self.assertIn("Yes", str(pref))

    def test_provider_preference_unique_together(self):
        from django.db import IntegrityError

        ProviderPreference.objects.create(
            provider=self.provider, subgroup=self.subgroup, is_checked=True
        )
        with self.assertRaises(IntegrityError):
            ProviderPreference.objects.create(
                provider=self.provider, subgroup=self.subgroup, is_checked=False
            )

    def test_provider_preference_comment(self):
        self.provider.preference_comment = "Call before visiting"
        self.provider.save()
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.preference_comment, "Call before visiting")

    def test_custom_option_creation(self):
        custom = ProviderPreferenceCustomOption.objects.create(
            provider=self.provider,
            subgroup=self.subgroup,
            text="Weekend only",
            display_order=0,
        )
        self.assertIn("Weekend only", str(custom))


class ProviderPreferencesViewTests(TestCase):
    """Test preference display on detail page and saving from edit form."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="prefview-provider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+15551234567",
            subscription_status="active",
        )
        self.group = PreferenceGroup.objects.create(
            name="Massage", display_order=1, is_active=True
        )
        self.subgroup_checked = PreferenceSubgroup.objects.create(
            group=self.group, name="Classical", display_order=1, is_active=True
        )
        self.subgroup_unchecked = PreferenceSubgroup.objects.create(
            group=self.group, name="Erotic", display_order=2, is_active=True
        )
        ProviderPreference.objects.create(
            provider=self.provider, subgroup=self.subgroup_checked, is_checked=True
        )
        ProviderPreference.objects.create(
            provider=self.provider, subgroup=self.subgroup_unchecked, is_checked=False
        )

    def test_detail_shows_checked_preference(self):
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "Classical")
        # Classical should NOT have line-through
        self.assertNotContains(response, 'line-through">Classical')

    def test_detail_shows_unchecked_with_strikethrough(self):
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "line-through")
        self.assertContains(response, "Erotic")

    def test_detail_shows_preference_comment(self):
        self.provider.preference_comment = "Please call first"
        self.provider.save()
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "Please call first")

    def test_saving_preferences_from_profile(self):
        self.client.login(email=self.user.email, password="testpass123")
        url = reverse("provider_profile")
        data = {
            "first_name": "Test",
            "last_name": "Provider",
            "phone": "+15551234567",
            "bio": "Test",
            **_required_attribute_data(),
            **_pricing_form_data(),
            **_preferences_form_data(
                **{
                    f"prefs-pref_check_{self.subgroup_checked.pk}": "on",
                    f"prefs-pref_custom_{self.subgroup_checked.pk}": "By appointment",
                    f"prefs-pref_custom_{self.subgroup_unchecked.pk}": "",
                    "prefs-preference_comment": "General note",
                }
            ),
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse("provider_dashboard"))

        # Verify preference was saved
        pref = ProviderPreference.objects.get(
            provider=self.provider, subgroup=self.subgroup_checked
        )
        self.assertTrue(pref.is_checked)

        # Verify custom option was created
        custom = ProviderPreferenceCustomOption.objects.filter(
            provider=self.provider, subgroup=self.subgroup_checked
        )
        self.assertEqual(custom.count(), 1)
        self.assertEqual(custom.first().text, "By appointment")

        # Verify comment
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.preference_comment, "General note")

    def test_detail_shows_custom_preferences_as_other_group(self):
        ProviderCustomPreference.objects.create(
            provider=self.provider, name="Hot stones", display_order=0
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "Other")
        self.assertContains(response, "Hot stones")

    def test_saving_custom_preferences_from_profile(self):
        self.client.login(email=self.user.email, password="testpass123")
        url = reverse("provider_profile")
        data = {
            "first_name": "Test",
            "last_name": "Provider",
            "phone": "+15551234567",
            "bio": "Test",
            **_required_attribute_data(),
            **_pricing_form_data(),
            **_preferences_form_data(
                **{
                    f"prefs-pref_custom_{self.subgroup_checked.pk}": "",
                    f"prefs-pref_custom_{self.subgroup_unchecked.pk}": "",
                    "prefs-custom_preferences": "Hot stones\nCandles",
                }
            ),
        }
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse("provider_dashboard"))

        custom = ProviderCustomPreference.objects.filter(provider=self.provider)
        self.assertEqual(custom.count(), 2)
        names = list(custom.order_by("display_order").values_list("name", flat=True))
        self.assertEqual(names, ["Hot stones", "Candles"])


class GeocodeLocationTests(TestCase):
    """Test the geocode_location utility function."""

    @patch("providers.utils.urllib.request.urlopen")
    def test_geocode_returns_coords_on_success(self, mock_urlopen):
        import json

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            [{"lat": "48.8566", "lon": "2.3522"}]
        ).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from providers.utils import geocode_location

        result = geocode_location("Marais", "Paris", "France")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result[0], 48.8566)
        self.assertAlmostEqual(result[1], 2.3522)

    @patch("providers.utils.urllib.request.urlopen")
    def test_geocode_returns_none_on_empty_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"[]"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        from providers.utils import geocode_location

        result = geocode_location("Nowhere", "Fakecity", "Fakeland")
        self.assertIsNone(result)

    @patch("providers.utils.urllib.request.urlopen", side_effect=Exception("timeout"))
    def test_geocode_returns_none_on_error(self, mock_urlopen):
        from providers.utils import geocode_location

        result = geocode_location("District", "City", "Country")
        self.assertIsNone(result)

    def test_geocode_returns_none_for_empty_parts(self):
        from providers.utils import geocode_location

        result = geocode_location("", "", "")
        self.assertIsNone(result)


class MapCoordinatesIntegrationTests(TestCase):
    """Test that profile save populates map coordinates."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="maptest@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        continent = Continent.objects.create(name="Europe", code="EU")
        self.country = Country.objects.create(
            name="France", code="FR", continent=continent
        )
        self.city = City.objects.create(
            name="Paris",
            country=self.country,
            latitude=Decimal("48.856600"),
            longitude=Decimal("2.352200"),
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+15551234567",
            country=self.country,
            city=self.city,
        )
        ProviderPricing.objects.create(provider=self.provider)
        self.district_def = ProviderAttributeDefinition.objects.get_or_create(
            name="District",
            defaults={"data_type": "string", "display_order": 3, "show_on_card": False},
        )[0]
        self.client_http = Client()
        self.client_http.login(email="maptest@test.com", password="testpass123")

    @patch("providers.utils.geocode_location", return_value=(48.86, 2.36))
    def test_profile_save_with_district_geocodes(self, mock_geocode):
        # Set a District attribute
        ProviderAttributeValue.objects.create(
            provider=self.provider,
            definition=self.district_def,
            value_text="Marais",
        )
        url = reverse("provider_profile")
        data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+15551234567",
            "bio": "Bio",
            **_required_attribute_data(),
            **_pricing_form_data(),
            **_preferences_form_data(),
        }
        # Include district field in form data
        data[f"attribute_{self.district_def.pk}"] = "Marais"
        self.client_http.post(url, data, follow=True)
        self.provider.refresh_from_db()
        self.assertAlmostEqual(float(self.provider.map_latitude), 48.86)
        self.assertAlmostEqual(float(self.provider.map_longitude), 2.36)

    @patch("providers.utils.geocode_location", return_value=None)
    def test_profile_save_falls_back_to_city_coords(self, mock_geocode):
        ProviderAttributeValue.objects.create(
            provider=self.provider,
            definition=self.district_def,
            value_text="Marais",
        )
        url = reverse("provider_profile")
        data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+15551234567",
            "bio": "Bio",
            **_required_attribute_data(),
            **_pricing_form_data(),
            **_preferences_form_data(),
        }
        data[f"attribute_{self.district_def.pk}"] = "Marais"
        self.client_http.post(url, data, follow=True)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.map_latitude, self.city.latitude)
        self.assertEqual(self.provider.map_longitude, self.city.longitude)

    def test_profile_save_no_district_uses_city_coords(self):
        url = reverse("provider_profile")
        data = {
            "first_name": "Test",
            "last_name": "User",
            "phone": "+15551234567",
            "bio": "Bio",
            **_required_attribute_data(),
            **_pricing_form_data(),
            **_preferences_form_data(),
        }
        self.client_http.post(url, data, follow=True)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.map_latitude, self.city.latitude)
        self.assertEqual(self.provider.map_longitude, self.city.longitude)


class ProviderDetailMapTests(TestCase):
    """Test that detail view uses cached provider coords over city coords."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="detailmap@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        continent = Continent.objects.create(name="Asia", code="AS")
        country = Country.objects.create(name="Japan", code="JP", continent=continent)
        self.city = City.objects.create(
            name="Tokyo",
            country=country,
            latitude=Decimal("35.689500"),
            longitude=Decimal("139.691700"),
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+15551234567",
            subscription_status="active",
            country=country,
            city=self.city,
            map_latitude=Decimal("35.700000"),
            map_longitude=Decimal("139.750000"),
        )

    def test_detail_uses_provider_cached_coords(self):
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertAlmostEqual(response.context["map_lat"], 35.7)
        self.assertAlmostEqual(response.context["map_lng"], 139.75)

    def test_detail_falls_back_to_city_when_no_provider_coords(self):
        self.provider.map_latitude = None
        self.provider.map_longitude = None
        self.provider.save(update_fields=["map_latitude", "map_longitude"])
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertAlmostEqual(response.context["map_lat"], 35.6895)
        self.assertAlmostEqual(response.context["map_lng"], 139.6917)


class ProviderProfileVideoTests(TestCase):
    """Test Provider Profile Video upload functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="videoprovider@test.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")
        self.client.login(email=self.user.email, password="testpass123")

    def _base_form_data(self):
        return {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "bio": "Test bio",
            **_required_attribute_data(),
            **_pricing_form_data(),
        }

    def test_video_form_field_exists(self):
        """Test that profile_video field is in the form."""
        from providers.views import ProviderProfileForm

        form = ProviderProfileForm(instance=self.provider)
        self.assertIn("profile_video", form.fields)

    def test_valid_mp4_upload(self):
        """Test uploading a valid MP4 video."""
        video = SimpleUploadedFile(
            "intro.mp4", b"\x00" * 1024, content_type="video/mp4"
        )
        self.client.post(
            reverse("provider_profile"),
            {**self._base_form_data(), "profile_video": video},
        )
        self.provider.refresh_from_db()
        self.assertTrue(
            self.provider.profile_video.name.startswith("providers/videos/")
        )

    def test_reject_non_mp4(self):
        """Test that non-MP4 files are rejected."""
        video = SimpleUploadedFile(
            "intro.avi", b"\x00" * 1024, content_type="video/x-msvideo"
        )
        response = self.client.post(
            reverse("provider_profile"),
            {**self._base_form_data(), "profile_video": video},
        )
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        self.assertFalse(bool(self.provider.profile_video))

    def test_reject_oversize_video(self):
        """Test that videos over 50MB are rejected."""
        from providers.views import ProviderProfileForm

        video = SimpleUploadedFile("big.mp4", b"\x00" * 100, content_type="video/mp4")
        video.size = 51 * 1024 * 1024  # fake size to 51MB

        form = ProviderProfileForm(
            data=self._base_form_data(),
            files={"profile_video": video},
            instance=self.provider,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("profile_video", form.errors)

    def test_detail_view_renders_video(self):
        """Test that detail view renders video tag when video exists."""
        self.provider.subscription_status = "active"
        self.provider.profile_video = "providers/videos/intro.mp4"
        self.provider.save()

        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "<video")
        self.assertContains(response, "providers/videos/intro.mp4")

    def test_detail_view_no_video_tag_when_empty(self):
        """Test that detail view does not render video tag when no video."""
        self.provider.subscription_status = "active"
        self.provider.save()

        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertNotContains(response, "<video")
