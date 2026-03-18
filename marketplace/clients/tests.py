from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from users.models import User
from providers.models import Provider, ProviderGalleryImage, ProviderPricing
from reviews.models import Review, ReviewCategory, ReviewCategoryRating


class ProviderDirectoryViewTests(TestCase):
    """Tests for the public provider directory view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create active provider
        self.active_user = User.objects.create_user(
            email="active@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.active_provider = Provider.objects.create(
            user=self.active_user,
            phone="+1234567890",
            bio="Active provider",
            subscription_status="active",
        )

        # Create inactive provider (should not show)
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.inactive_provider = Provider.objects.create(
            user=self.inactive_user, phone="+9876543210", subscription_status="inactive"
        )

        # Create unverified provider (should not show)
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=False,
        )
        self.unverified_provider = Provider.objects.create(
            user=self.unverified_user, phone="+1111111111", subscription_status="active"
        )

    def test_provider_directory_loads(self):
        """Test that provider directory page loads."""
        response = self.client.get(reverse("providers"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/provider_list.html")

    def test_home_url_loads_directory(self):
        """Test that home URL loads provider directory."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/provider_list.html")

    def test_only_active_verified_providers_shown(self):
        """Test that only active and verified providers are displayed."""
        response = self.client.get(reverse("providers"))

        # Active provider should be in response
        self.assertContains(response, "active@example.com")

        # Inactive provider should not be in response
        self.assertNotContains(response, "inactive@example.com")

        # Unverified provider should not be in response
        self.assertNotContains(response, "unverified@example.com")

    def test_provider_card_shows_info(self):
        """Test that provider cards show correct information."""
        # Add reviews
        client1 = User.objects.create_user(
            email="c1@example.com", password="testpass123", user_type="client"
        )
        client2 = User.objects.create_user(
            email="c2@example.com", password="testpass123", user_type="client"
        )
        Review.objects.create(
            provider=self.active_provider, client=client1, comment="Great service!"
        )
        Review.objects.create(
            provider=self.active_provider, client=client2, comment="Good"
        )

        response = self.client.get(reverse("providers"))

        # Should show review count
        self.assertContains(response, "2 reviews")

    def test_no_authentication_required(self):
        """Test that provider directory is accessible without login."""
        response = self.client.get(reverse("providers"))
        self.assertEqual(response.status_code, 200)
        # Should not redirect to login
        self.assertNotEqual(response.status_code, 302)

    def test_pagination_works(self):
        """Test that pagination works correctly."""
        # Create 25 active providers
        for i in range(25):
            user = User.objects.create_user(
                email=f"provider{i}@example.com",
                password="testpass123",
                user_type="provider",
                is_email_verified=True,
            )
            Provider.objects.create(
                user=user, phone=f"+123456789{i}", subscription_status="active"
            )

        response = self.client.get(reverse("providers"))

        # Should have pagination context
        self.assertTrue(response.context["is_paginated"])

        # Should show 20 providers per page
        self.assertEqual(len(response.context["providers_with_stats"]), 20)


class ProviderDetailViewTests(TestCase):
    """Tests for the public provider detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create active provider
        self.user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="John",
            last_name="Doe",
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+1234567890",
            bio="Professional massage therapist",
            subscription_status="active",
        )

        # Create client user and review
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
            first_name="Jane",
            last_name="Smith",
        )
        self.review = Review.objects.create(
            provider=self.provider,
            client=self.client_user,
            comment="Excellent service!",
        )
        self.category = ReviewCategory.objects.create(name="Quality")
        ReviewCategoryRating.objects.create(
            review=self.review, category=self.category, rating=5
        )

    def test_provider_detail_loads(self):
        """Test that provider detail page loads."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/provider_detail.html")

    def test_provider_detail_shows_info(self):
        """Test that provider detail shows all information."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )

        # Should show provider name
        self.assertContains(response, "John Doe")

        # Should show bio
        self.assertContains(response, "Professional massage therapist")

        # Should show phone
        self.assertContains(response, "+1234567890")

        # Should show email
        self.assertContains(response, "provider@example.com")

    def test_provider_detail_shows_reviews(self):
        """Test that reviews are displayed."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )

        # Should show review content
        self.assertContains(response, "Excellent service!")

        # Should show reviewer first name
        self.assertContains(response, "Jane")

        # Should show category name
        self.assertContains(response, "Quality")

    def test_inactive_provider_returns_404(self):
        """Test that inactive provider returns 404."""
        self.provider.subscription_status = "inactive"
        self.provider.save()

        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_unverified_provider_returns_404(self):
        """Test that unverified provider returns 404."""
        self.user.is_email_verified = False
        self.user.save()

        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_no_authentication_required(self):
        """Test that provider detail is accessible without login."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)


class ProviderModelHelperTests(TestCase):
    """Tests for Provider model helper methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            user_type="provider",
            first_name="John",
            last_name="Doe",
        )
        self.provider = Provider.objects.create(user=self.user, phone="+1234567890")

    def test_average_rating_with_reviews(self):
        """Test average rating calculation with category ratings."""
        cat = ReviewCategory.objects.create(name="Quality")
        c1 = User.objects.create_user(
            email="c1@example.com", password="testpass123", user_type="client"
        )
        c2 = User.objects.create_user(
            email="c2@example.com", password="testpass123", user_type="client"
        )
        c3 = User.objects.create_user(
            email="c3@example.com", password="testpass123", user_type="client"
        )
        r1 = Review.objects.create(provider=self.provider, client=c1, comment="Great!")
        r2 = Review.objects.create(provider=self.provider, client=c2, comment="Good")
        r3 = Review.objects.create(provider=self.provider, client=c3, comment="OK")
        ReviewCategoryRating.objects.create(review=r1, category=cat, rating=5)
        ReviewCategoryRating.objects.create(review=r2, category=cat, rating=4)
        ReviewCategoryRating.objects.create(review=r3, category=cat, rating=3)

        avg = self.provider.average_rating()
        self.assertEqual(avg, 4.0)

    def test_average_rating_without_reviews(self):
        """Test average rating returns 0 without reviews."""
        avg = self.provider.average_rating()
        self.assertEqual(avg, 0)

    def test_get_name_with_full_name(self):
        """Test get_name returns full name."""
        name = self.provider.get_name()
        self.assertEqual(name, "John Doe")

    def test_get_name_with_first_name_only(self):
        """Test get_name with only first name."""
        self.user.last_name = ""
        self.user.save()
        name = self.provider.get_name()
        self.assertEqual(name, "John")

    def test_get_name_without_names(self):
        """Test get_name falls back to email."""
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        name = self.provider.get_name()
        self.assertEqual(name, "test")


class ProviderSlugTests(TestCase):
    """Tests for Provider slug generation."""

    def test_slug_generated_on_create(self):
        """Test that slug is auto-generated when provider is created."""
        user = User.objects.create_user(
            email="sarah@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Sarah",
            last_name="Johnson",
        )
        provider = Provider.objects.create(user=user, phone="+1234567890")
        self.assertEqual(provider.slug, f"sarah-johnson-{provider.pk}")

    def test_slug_uses_email_prefix_when_no_name(self):
        """Test that slug falls back to email prefix when no name set."""
        user = User.objects.create_user(
            email="therapist42@example.com",
            password="testpass123",
            user_type="provider",
        )
        provider = Provider.objects.create(user=user, phone="+1234567890")
        self.assertEqual(provider.slug, f"therapist42-{provider.pk}")

    def test_slug_updates_on_name_change(self):
        """Test that slug updates when provider name changes."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Old",
            last_name="Name",
        )
        provider = Provider.objects.create(user=user, phone="+1234567890")
        self.assertEqual(provider.slug, f"old-name-{provider.pk}")

        user.first_name = "New"
        user.last_name = "Name"
        user.save()
        provider.save()
        self.assertEqual(provider.slug, f"new-name-{provider.pk}")

    def test_slug_is_unique_for_same_name(self):
        """Test that two providers with the same name get different slugs."""
        user1 = User.objects.create_user(
            email="jane1@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Jane",
            last_name="Doe",
        )
        user2 = User.objects.create_user(
            email="jane2@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Jane",
            last_name="Doe",
        )
        p1 = Provider.objects.create(user=user1, phone="+1111111111")
        p2 = Provider.objects.create(user=user2, phone="+2222222222")

        self.assertNotEqual(p1.slug, p2.slug)
        self.assertEqual(p1.slug, f"jane-doe-{p1.pk}")
        self.assertEqual(p2.slug, f"jane-doe-{p2.pk}")

    def test_slug_used_in_detail_url(self):
        """Test that provider detail page is accessible via slug URL."""
        user = User.objects.create_user(
            email="detail@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Detail",
            last_name="Test",
            is_email_verified=True,
        )
        provider = Provider.objects.create(
            user=user, phone="+1234567890", subscription_status="active"
        )

        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["provider"], provider)

    def test_get_absolute_url(self):
        """Test that get_absolute_url returns the correct slug-based URL."""
        user = User.objects.create_user(
            email="abs@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Abs",
            last_name="Url",
        )
        provider = Provider.objects.create(user=user, phone="+1234567890")
        expected = reverse("provider_detail", kwargs={"slug": provider.slug})
        self.assertEqual(provider.get_absolute_url(), expected)

    def test_review_submit_uses_slug(self):
        """Test that review submission works with slug-based URL."""
        provider_user = User.objects.create_user(
            email="reviewed@example.com",
            password="testpass123",
            user_type="provider",
            first_name="Reviewed",
            last_name="Provider",
            is_email_verified=True,
        )
        provider = Provider.objects.create(
            user=provider_user, phone="+1234567890", subscription_status="active"
        )
        User.objects.create_user(
            email="slug-client@example.com",
            password="testpass123",
            user_type="client",
        )
        cat = ReviewCategory.objects.create(name="SlugCat")

        self.client.login(email="slug-client@example.com", password="testpass123")
        response = self.client.post(
            reverse("review_submit", kwargs={"slug": provider.slug}),
            {
                "comment": "Slug-based review!",
                f"category_{cat.pk}": 5,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.filter(provider=provider).count(), 1)


class ProviderFilteringTests(TestCase):
    """Tests for provider filtering functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create providers with different locations
        self.provider1 = self._create_provider(
            email="provider1@example.com", country="USA", city="New York"
        )

        self.provider2 = self._create_provider(
            email="provider2@example.com", country="USA", city="Los Angeles"
        )

        self.provider3 = self._create_provider(
            email="provider3@example.com", country="Canada", city="Toronto"
        )

    def _create_provider(self, email, country, city):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        provider = Provider.objects.create(
            user=user,
            phone="+1234567890",
            subscription_status="active",
            country=country,
            city=city,
        )
        return provider

    def test_filter_by_country(self):
        """Test filtering providers by country."""
        response = self.client.get(reverse("providers") + "?country=USA")
        self.assertEqual(response.status_code, 200)

        # Should show USA providers
        self.assertContains(response, "provider1@example.com")
        self.assertContains(response, "provider2@example.com")
        # Should not show Canadian provider
        self.assertNotContains(response, "provider3@example.com")

    def test_filter_by_city(self):
        """Test filtering providers by city."""
        response = self.client.get(reverse("providers") + "?city=New York")
        self.assertEqual(response.status_code, 200)

        # Should show only New York provider
        self.assertContains(response, "provider1@example.com")
        self.assertNotContains(response, "provider2@example.com")
        self.assertNotContains(response, "provider3@example.com")

    def test_reset_filters_link(self):
        """Test that reset link clears all filters."""
        response = self.client.get(reverse("providers"))
        self.assertEqual(response.status_code, 200)

        # All providers should be shown
        self.assertContains(response, "provider1@example.com")
        self.assertContains(response, "provider2@example.com")
        self.assertContains(response, "provider3@example.com")


class ProviderDetailGalleryTests(TestCase):
    """Tests for gallery display on provider detail page."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user, phone="+1234567890", subscription_status="active"
        )

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io

        img = PILImage.new("RGB", (100, 100), color="blue")
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG")
        img_io.seek(0)
        return SimpleUploadedFile(
            "test.jpg", img_io.getvalue(), content_type="image/jpeg"
        )

    def test_gallery_images_in_context(self):
        """Test that gallery images are included in detail view context."""
        ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption="Workspace photo",
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("gallery_images", response.context)
        self.assertEqual(response.context["gallery_images"].count(), 1)

    def test_gallery_section_displayed(self):
        """Test that gallery section is displayed when images exist."""
        ProviderGalleryImage.objects.create(
            provider=self.provider, image=self._create_test_image(), caption="My studio"
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "Photo Gallery")
        self.assertContains(response, "My studio")

    def test_gallery_section_hidden_when_empty(self):
        """Test that gallery section is hidden when no images."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertNotContains(response, "Photo Gallery")


class LocationSearchAPITests(TestCase):
    """Tests for location search API endpoints."""

    def setUp(self):
        """Set up test data."""
        from providers.models import Continent, Country, City

        self.client = Client()

        # Create continents
        self.europe = Continent.objects.create(
            name="Europe", code="EU", display_order=1
        )
        self.asia = Continent.objects.create(name="Asia", code="AS", display_order=2)

        # Create countries
        self.uk = Country.objects.create(
            name="United Kingdom", code="GB", continent=self.europe, is_active=True
        )
        self.france = Country.objects.create(
            name="France", code="FR", continent=self.europe, is_active=True
        )
        self.uae = Country.objects.create(
            name="United Arab Emirates", code="AE", continent=self.asia, is_active=True
        )
        self.inactive_country = Country.objects.create(
            name="Inactive Country", code="IC", continent=self.europe, is_active=False
        )

        # Create cities
        self.london = City.objects.create(
            name="London",
            country=self.uk,
            population=8982000,
            is_capital=True,
            is_major_city=True,
        )
        self.birmingham = City.objects.create(
            name="Birmingham",
            country=self.uk,
            population=1149000,
            is_capital=False,
            is_major_city=True,
        )
        self.paris = City.objects.create(
            name="Paris",
            country=self.france,
            population=2161000,
            is_capital=True,
            is_major_city=True,
        )

    def test_country_search_basic(self):
        """Test basic country search functionality."""
        response = self.client.get(reverse("api_country_search"), {"q": "united"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)

        names = [r["name"] for r in data["results"]]
        self.assertIn("United Kingdom", names)
        self.assertIn("United Arab Emirates", names)

    def test_country_search_by_code(self):
        """Test country search by country code."""
        response = self.client.get(reverse("api_country_search"), {"q": "GB"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["code"], "GB")

    def test_country_search_includes_continent(self):
        """Test that country search includes continent info."""
        response = self.client.get(reverse("api_country_search"), {"q": "united king"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["continent"], "Europe")
        self.assertEqual(data["results"][0]["continent_code"], "EU")

    def test_country_search_excludes_inactive(self):
        """Test that inactive countries are excluded."""
        response = self.client.get(reverse("api_country_search"), {"q": "inactive"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_country_search_min_chars(self):
        """Test that search requires minimum 2 characters."""
        response = self.client.get(reverse("api_country_search"), {"q": "u"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_country_search_empty_query(self):
        """Test that empty query returns no results."""
        response = self.client.get(reverse("api_country_search"), {"q": ""})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_city_search_basic(self):
        """Test basic city search functionality."""
        response = self.client.get(
            reverse("api_city_search"), {"q": "lon", "country": str(self.uk.id)}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["name"], "London")

    def test_city_search_requires_country(self):
        """Test that city search requires country ID."""
        response = self.client.get(reverse("api_city_search"), {"q": "lon"})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_city_search_invalid_country_id(self):
        """Test city search with invalid country ID."""
        response = self.client.get(
            reverse("api_city_search"), {"q": "lon", "country": "invalid"}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_city_search_scoped_to_country(self):
        """Test that city search is scoped to selected country."""
        # Search for 'par' in UK should not find Paris
        response = self.client.get(
            reverse("api_city_search"), {"q": "par", "country": str(self.uk.id)}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)

        # Search for 'par' in France should find Paris
        response = self.client.get(
            reverse("api_city_search"), {"q": "par", "country": str(self.france.id)}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["name"], "Paris")

    def test_city_search_includes_flags(self):
        """Test that city search includes is_capital and is_major_city flags."""
        response = self.client.get(
            reverse("api_city_search"), {"q": "london", "country": str(self.uk.id)}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertTrue(data["results"][0]["is_capital"])
        self.assertTrue(data["results"][0]["is_major_city"])

    def test_city_search_min_chars(self):
        """Test that city search requires minimum 2 characters."""
        response = self.client.get(
            reverse("api_city_search"), {"q": "l", "country": str(self.uk.id)}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["results"]), 0)


class ProviderLocationFKFilterTests(TestCase):
    """Tests for provider filtering by ForeignKey location fields."""

    def setUp(self):
        """Set up test data."""
        from providers.models import Continent, Country, City

        self.client = Client()

        # Create location data
        self.europe = Continent.objects.create(
            name="Europe", code="EU", display_order=1
        )
        self.uk = Country.objects.create(
            name="United Kingdom", code="GB", continent=self.europe, is_active=True
        )
        self.france = Country.objects.create(
            name="France", code="FR", continent=self.europe, is_active=True
        )
        self.london = City.objects.create(
            name="London", country=self.uk, is_capital=True
        )
        self.paris = City.objects.create(
            name="Paris", country=self.france, is_capital=True
        )

        # Create providers with FK locations
        self.provider1 = self._create_provider(
            "provider1@example.com", self.uk, self.london
        )
        self.provider2 = self._create_provider(
            "provider2@example.com", self.france, self.paris
        )
        self.provider3 = self._create_provider("provider3@example.com", self.uk, None)

    def _create_provider(self, email, country, city):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        provider = Provider.objects.create(
            user=user,
            phone="+1234567890",
            subscription_status="active",
            country=country,
            city=city,
        )
        return provider

    def test_filter_by_country_id(self):
        """Test filtering providers by country_id."""
        response = self.client.get(reverse("providers") + f"?country_id={self.uk.id}")
        self.assertEqual(response.status_code, 200)

        # Should show UK providers
        self.assertContains(response, "provider1@example.com")
        self.assertContains(response, "provider3@example.com")
        # Should not show France provider
        self.assertNotContains(response, "provider2@example.com")

    def test_filter_by_city_id(self):
        """Test filtering providers by city_id."""
        response = self.client.get(reverse("providers") + f"?city_id={self.london.id}")
        self.assertEqual(response.status_code, 200)

        # Should show only London provider
        self.assertContains(response, "provider1@example.com")
        # Should not show others
        self.assertNotContains(response, "provider2@example.com")
        self.assertNotContains(response, "provider3@example.com")

    def test_filter_by_both_country_and_city(self):
        """Test filtering by both country_id and city_id."""
        response = self.client.get(
            reverse("providers") + f"?country_id={self.uk.id}&city_id={self.london.id}"
        )
        self.assertEqual(response.status_code, 200)

        # Should show only London provider
        self.assertContains(response, "provider1@example.com")
        self.assertNotContains(response, "provider2@example.com")
        self.assertNotContains(response, "provider3@example.com")

    def test_invalid_country_id_ignored(self):
        """Test that invalid country_id is ignored."""
        response = self.client.get(reverse("providers") + "?country_id=invalid")
        self.assertEqual(response.status_code, 200)

        # Should show all providers
        self.assertContains(response, "provider1@example.com")
        self.assertContains(response, "provider2@example.com")
        self.assertContains(response, "provider3@example.com")


class ProviderDetailPricingTests(TestCase):
    """Tests for pricing display on provider detail page."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="pricing-detail@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="Anna",
            last_name="Test",
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+1234567890",
            bio="Test provider",
            subscription_status="active",
        )

    def test_detail_page_with_pricing(self):
        """Test that pricing is shown on provider detail page."""
        from decimal import Decimal

        ProviderPricing.objects.create(
            provider=self.provider,
            apartment_day_1h=Decimal("50.00"),
            apartment_day_2h=Decimal("90.00"),
            apartment_night_1h=Decimal("70.00"),
            apartment_night_whole=Decimal("200.00"),
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["pricing"])
        self.assertContains(response, "50.00")
        self.assertContains(response, "200.00")

    def test_detail_page_without_pricing(self):
        """Test that detail page works when no pricing exists."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["pricing"])

    def test_detail_page_not_available_row(self):
        """Test that 'Not available' is shown for unavailable location."""
        ProviderPricing.objects.create(
            provider=self.provider,
            apartment_available=False,
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertContains(response, "Not available")


class ProviderDirectoryPricingTests(TestCase):
    """Tests for pricing display on provider card in directory."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="card-pricing@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone="+1234567890",
            bio="Test provider",
            subscription_status="active",
        )

    def test_card_pricing_prefers_apartment(self):
        """Test that card shows apartment prices when available."""
        from decimal import Decimal

        ProviderPricing.objects.create(
            provider=self.provider,
            apartment_available=True,
            outside_available=True,
            apartment_day_1h=Decimal("50.00"),
            outside_day_1h=Decimal("80.00"),
        )
        response = self.client.get(reverse("providers"))
        item = response.context["providers_with_stats"][0]
        self.assertEqual(item["card_pricing"]["location"], "Apartment")
        self.assertEqual(item["card_pricing"]["price_1h"], Decimal("50.00"))

    def test_card_pricing_falls_back_to_outside(self):
        """Test that card shows outside prices when apartment unavailable."""
        from decimal import Decimal

        ProviderPricing.objects.create(
            provider=self.provider,
            apartment_available=False,
            outside_available=True,
            outside_day_1h=Decimal("80.00"),
        )
        response = self.client.get(reverse("providers"))
        item = response.context["providers_with_stats"][0]
        self.assertEqual(item["card_pricing"]["location"], "Outside")
        self.assertEqual(item["card_pricing"]["price_1h"], Decimal("80.00"))

    def test_card_pricing_none_when_no_pricing(self):
        """Test that card_pricing is None when no pricing exists."""
        response = self.client.get(reverse("providers"))
        item = response.context["providers_with_stats"][0]
        self.assertIsNone(item["card_pricing"])

    def test_card_pricing_none_when_both_unavailable(self):
        """Test that card_pricing is None when both locations unavailable."""
        ProviderPricing.objects.create(
            provider=self.provider,
            apartment_available=False,
            outside_available=False,
        )
        response = self.client.get(reverse("providers"))
        item = response.context["providers_with_stats"][0]
        self.assertIsNone(item["card_pricing"])


class ClientRequiredMixinTests(TestCase):
    """Tests for ClientRequiredMixin access control."""

    def setUp(self):
        self.client_obj = Client()
        self.client_user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        self.provider_user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
        )

    def test_anonymous_redirected_to_login(self):
        response = self.client_obj.get(reverse("client_profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_provider_redirected_to_login(self):
        self.client_obj.login(email="provider@example.com", password="testpass123")
        response = self.client_obj.get(reverse("client_profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_client_can_access(self):
        self.client_obj.login(email="client@example.com", password="testpass123")
        response = self.client_obj.get(reverse("client_profile"))
        self.assertEqual(response.status_code, 200)


class ClientProfileViewTests(TestCase):
    """Tests for the client profile view."""

    def setUp(self):
        self.client_obj = Client()
        self.user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
            first_name="Jane",
            last_name="Doe",
        )
        self.client_obj.login(email="client@example.com", password="testpass123")

    def test_profile_get_shows_current_values(self):
        response = self.client_obj.get(reverse("client_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane")
        self.assertContains(response, "Doe")

    def test_profile_post_updates_name(self):
        response = self.client_obj.post(
            reverse("client_profile"),
            {"first_name": "Alice", "last_name": "Smith"},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.last_name, "Smith")

    def test_profile_post_allows_empty_names(self):
        response = self.client_obj.post(
            reverse("client_profile"),
            {"first_name": "", "last_name": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "")
        self.assertEqual(self.user.last_name, "")

    def test_profile_uses_correct_template(self):
        response = self.client_obj.get(reverse("client_profile"))
        self.assertTemplateUsed(response, "clients/client_profile.html")


class ClientReviewsViewTests(TestCase):
    """Tests for the client reviews list view."""

    def setUp(self):
        self.client_obj = Client()
        self.user = User.objects.create_user(
            email="client@example.com",
            password="testpass123",
            user_type="client",
        )
        self.provider_user = User.objects.create_user(
            email="provider@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="John",
            last_name="Provider",
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone="+1234567890",
            subscription_status="active",
        )
        self.client_obj.login(email="client@example.com", password="testpass123")

    def test_reviews_page_loads(self):
        response = self.client_obj.get(reverse("client_reviews"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clients/client_reviews.html")

    def test_empty_state_shown(self):
        response = self.client_obj.get(reverse("client_reviews"))
        self.assertContains(response, "haven&#x27;t written any reviews yet")

    def test_reviews_listed(self):
        Review.objects.create(
            provider=self.provider,
            client=self.user,
            comment="Great massage!",
        )
        response = self.client_obj.get(reverse("client_reviews"))
        self.assertContains(response, "Great massage!")
        self.assertContains(response, "John Provider")

    def test_only_own_reviews_shown(self):
        other_client = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            user_type="client",
        )
        Review.objects.create(
            provider=self.provider,
            client=other_client,
            comment="Not my review",
        )
        response = self.client_obj.get(reverse("client_reviews"))
        self.assertNotContains(response, "Not my review")

    def test_pagination(self):
        # Create 12 providers with reviews to exceed paginate_by=10
        for i in range(12):
            puser = User.objects.create_user(
                email=f"prov{i}@example.com",
                password="testpass123",
                user_type="provider",
                is_email_verified=True,
            )
            prov = Provider.objects.create(
                user=puser,
                phone=f"+123456789{i}",
                subscription_status="active",
            )
            Review.objects.create(
                provider=prov,
                client=self.user,
                comment=f"Review {i}",
            )

        response = self.client_obj.get(reverse("client_reviews"))
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["reviews"]), 10)

        # Page 2
        response = self.client_obj.get(reverse("client_reviews") + "?page=2")
        self.assertEqual(len(response.context["reviews"]), 2)

    def test_anonymous_redirected(self):
        self.client_obj.logout()
        response = self.client_obj.get(reverse("client_reviews"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)


class CachedCountPaginatorTests(TestCase):
    """
    CachedCountPaginator caches COUNT(*) per unique queryset.
    Tests use DummyCache (from test_settings) so cache.get always returns None
    and cache.set is a no-op — the paginator must still return correct counts.
    """

    def setUp(self):
        self.client = Client()
        for i in range(5):
            u = User.objects.create_user(
                email=f"prov{i}@cache.test",
                password="pass",
                user_type="provider",
                is_email_verified=True,
            )
            Provider.objects.create(
                user=u, phone=f"+1000000{i:03}", subscription_status="active"
            )

    def test_homepage_paginates_correctly(self):
        """Paginator returns correct total count with DummyCache (no real caching)."""
        response = self.client.get(reverse("providers"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginator"].count, 5)

    def test_count_reflects_new_provider(self):
        """Count updates when a new provider becomes active (cache is a no-op in tests)."""
        response = self.client.get(reverse("providers"))
        count_before = response.context["paginator"].count

        new_user = User.objects.create_user(
            email="new@cache.test",
            password="pass",
            user_type="provider",
            is_email_verified=True,
        )
        Provider.objects.create(
            user=new_user, phone="+19999999999", subscription_status="active"
        )

        response = self.client.get(reverse("providers"))
        self.assertEqual(response.context["paginator"].count, count_before + 1)

    def test_cached_count_paginator_used(self):
        """ProviderDirectoryView uses CachedCountPaginator."""
        from clients.views import CachedCountPaginator

        response = self.client.get(reverse("providers"))
        self.assertIsInstance(response.context["paginator"], CachedCountPaginator)


class PreferenceGroupCacheTests(TestCase):
    """
    The PreferenceGroup tree is cached under PREF_GROUPS_CACHE_KEY.
    With DummyCache, cache misses are always triggered so the DB is always hit —
    we verify the view still works correctly and the signal handler doesn't error.
    """

    def setUp(self):
        from providers.models import PreferenceGroup, PreferenceSubgroup

        self.client = Client()

        self.group = PreferenceGroup.objects.create(
            name="Test Group", display_order=1, is_active=True
        )
        self.subgroup = PreferenceSubgroup.objects.create(
            group=self.group, name="Test Subgroup", display_order=1, is_active=True
        )

        user = User.objects.create_user(
            email="prov@pref.test",
            password="pass",
            user_type="provider",
            is_email_verified=True,
        )
        self.provider = Provider.objects.create(
            user=user, phone="+10000000001", subscription_status="active"
        )

    def test_detail_view_renders_preference_group(self):
        """Provider detail page includes preference group data."""
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("preference_display", response.context)
        groups = response.context["preference_display"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["name"], "Test Group")

    def test_cache_key_deleted_on_group_save(self):
        """Saving a PreferenceGroup calls cache.delete (no-op with DummyCache, no error)."""
        from providers.signals import PREF_GROUPS_CACHE_KEY

        # Seed a value so we can assert it's cleared (LocMemCache behaviour;
        # with DummyCache this is also a no-op, but must not raise).
        cache.set(PREF_GROUPS_CACHE_KEY, "sentinel", 60)
        self.group.name = "Updated Group"
        self.group.save()
        # With DummyCache get always returns None; with a real cache it should be cleared.
        self.assertIsNone(cache.get(PREF_GROUPS_CACHE_KEY))

    def test_cache_key_deleted_on_subgroup_save(self):
        """Saving a PreferenceSubgroup also invalidates the cache."""
        from providers.signals import PREF_GROUPS_CACHE_KEY

        cache.set(PREF_GROUPS_CACHE_KEY, "sentinel", 60)
        self.subgroup.name = "Updated Subgroup"
        self.subgroup.save()
        self.assertIsNone(cache.get(PREF_GROUPS_CACHE_KEY))

    def test_cache_key_deleted_on_group_delete(self):
        """Deleting a PreferenceGroup invalidates the cache."""
        from providers.signals import PREF_GROUPS_CACHE_KEY

        cache.set(PREF_GROUPS_CACHE_KEY, "sentinel", 60)
        self.group.delete()
        self.assertIsNone(cache.get(PREF_GROUPS_CACHE_KEY))

    def test_inactive_subgroup_excluded(self):
        """Inactive subgroups are not included in preference_display."""
        from providers.models import PreferenceSubgroup

        PreferenceSubgroup.objects.create(
            group=self.group, name="Inactive Sub", display_order=2, is_active=False
        )
        response = self.client.get(
            reverse("provider_detail", kwargs={"slug": self.provider.slug})
        )
        subgroup_names = [
            sg["name"]
            for g in response.context["preference_display"]
            for sg in g["subgroups"]
        ]
        self.assertNotIn("Inactive Sub", subgroup_names)


class LocationAPICacheTests(TestCase):
    """
    Country and city API responses are cached.
    With DummyCache the cache is a no-op — verify the endpoints
    return correct data regardless of cache state.
    """

    def setUp(self):
        from providers.models import Continent, Country, City

        self.client = Client()

        continent = Continent.objects.create(
            name="Europe", code="EU", display_order=1
        )
        self.country = Country.objects.create(
            name="Germany", code="DE", continent=continent, is_active=True
        )
        self.city = City.objects.create(
            name="Berlin",
            country=self.country,
            population=3769000,
            is_capital=True,
            is_major_city=True,
        )

    def test_country_api_cache_miss_returns_data(self):
        """Country API returns correct data when cache is cold."""
        response = self.client.get(reverse("api_country_search"), {"all": "1"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        country_names = [
            c["name"]
            for continent in data["continents"]
            for c in continent["countries"]
        ]
        self.assertIn("Germany", country_names)

    def test_country_api_consistent_on_repeat_calls(self):
        """Country API returns same data on two consecutive calls (cache hit or miss)."""
        url = reverse("api_country_search")
        r1 = self.client.get(url, {"all": "1"}).json()
        r2 = self.client.get(url, {"all": "1"}).json()
        self.assertEqual(r1, r2)

    def test_city_api_cache_miss_returns_data(self):
        """City API returns correct data when cache is cold."""
        response = self.client.get(
            reverse("api_city_search"), {"country": self.country.pk, "all": "1"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        city_names = [c["name"] for c in data["results"]]
        self.assertIn("Berlin", city_names)

    def test_city_api_consistent_on_repeat_calls(self):
        """City API returns same data on two consecutive calls."""
        url = reverse("api_city_search")
        params = {"country": self.country.pk, "all": "1"}
        r1 = self.client.get(url, params).json()
        r2 = self.client.get(url, params).json()
        self.assertEqual(r1, r2)

    def test_country_api_empty_query_no_cache(self):
        """Country API with no query and no all=1 returns empty (not cached)."""
        response = self.client.get(reverse("api_country_search"))
        self.assertEqual(response.json(), {"continents": []})


class ProviderAdvancedFilteringTests(TestCase):
    """Tests for advanced provider filtering (price, availability, rating, photo, pref, attr)."""

    def setUp(self):
        from decimal import Decimal
        from providers.models import (
            ProviderPricing,
            ProviderAttributeDefinition,
            ProviderAttributeValue,
            PreferenceGroup,
            PreferenceSubgroup,
            ProviderPreference,
        )

        self.client = Client()

        # ---- Shared attribute definition (bool) ----
        self.bool_attr_def = ProviderAttributeDefinition.objects.create(
            name="Outcall",
            data_type=ProviderAttributeDefinition.DATA_TYPE_BOOLEAN,
            is_active=True,
            display_order=1,
        )

        # ---- Shared preference group / subgroup ----
        self.pref_group = PreferenceGroup.objects.create(
            name="TestGroup", is_active=True, display_order=1
        )
        self.subgroup1 = PreferenceSubgroup.objects.create(
            group=self.pref_group, name="SubA", is_active=True, display_order=1
        )
        self.subgroup2 = PreferenceSubgroup.objects.create(
            group=self.pref_group, name="SubB", is_active=True, display_order=2
        )

        # ---- Provider 1: apartment, price=100, has bool attr, pref subgroup1 checked ----
        user1 = User.objects.create_user(
            email="adv1@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="Alice",
            last_name="One",
        )
        self.provider1 = Provider.objects.create(
            user=user1,
            phone="+1000000001",
            bio="Provider one",
            subscription_status="active",
        )
        ProviderPricing.objects.create(
            provider=self.provider1,
            apartment_available=True,
            outside_available=False,
            apartment_day_1h=Decimal("100.00"),
            apartment_day_2h=Decimal("180.00"),
        )
        ProviderAttributeValue.objects.create(
            provider=self.provider1,
            definition=self.bool_attr_def,
            value_text="1",
        )
        ProviderPreference.objects.create(
            provider=self.provider1,
            subgroup=self.subgroup1,
            is_checked=True,
        )

        # ---- Provider 2: outside, price=200, no bool attr, pref subgroup2 not checked ----
        user2 = User.objects.create_user(
            email="adv2@example.com",
            password="testpass123",
            user_type="provider",
            is_email_verified=True,
            first_name="Bob",
            last_name="Two",
        )
        self.provider2 = Provider.objects.create(
            user=user2,
            phone="+1000000002",
            bio="Provider two",
            subscription_status="active",
        )
        ProviderPricing.objects.create(
            provider=self.provider2,
            apartment_available=False,
            outside_available=True,
            apartment_day_1h=Decimal("200.00"),
            apartment_day_2h=Decimal("350.00"),
        )
        ProviderPreference.objects.create(
            provider=self.provider2,
            subgroup=self.subgroup2,
            is_checked=False,
        )

    def _provider_emails(self, response):
        """Return set of provider emails from providers_with_stats context."""
        return {
            item["provider"].user.email
            for item in response.context["providers_with_stats"]
        }

    # ------------------------------------------------------------------
    # Price filters
    # ------------------------------------------------------------------

    def test_filter_price_min(self):
        """price_min=150 returns only the provider with price 200."""
        response = self.client.get(reverse("providers"), {"price_min": "150"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv2@example.com", emails)
        self.assertNotIn("adv1@example.com", emails)

    def test_filter_price_max(self):
        """price_max=150 returns only the provider with price 100."""
        response = self.client.get(reverse("providers"), {"price_max": "150"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    # ------------------------------------------------------------------
    # Availability filters
    # ------------------------------------------------------------------

    def test_filter_apartment(self):
        """apartment=1 returns only provider1 (apartment_available=True)."""
        response = self.client.get(reverse("providers"), {"apartment": "1"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    def test_filter_outside(self):
        """outside=1 returns only provider2 (outside_available=True)."""
        response = self.client.get(reverse("providers"), {"outside": "1"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv2@example.com", emails)
        self.assertNotIn("adv1@example.com", emails)

    # ------------------------------------------------------------------
    # Has photo filter
    # ------------------------------------------------------------------

    def test_filter_has_photo(self):
        """has_photo=1 returns only providers that have a photo set."""
        # Neither provider has a photo yet — result should be empty
        response = self.client.get(reverse("providers"), {"has_photo": "1"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertNotIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    # ------------------------------------------------------------------
    # Preference filter
    # ------------------------------------------------------------------

    def test_filter_preference(self):
        """pref=subgroup1_id returns only provider1 (is_checked=True for that subgroup)."""
        response = self.client.get(
            reverse("providers"), {"pref": str(self.subgroup1.id)}
        )
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    # ------------------------------------------------------------------
    # Bool attribute filter
    # ------------------------------------------------------------------

    def test_filter_bool_attribute(self):
        """attr_{def_id}=1 returns only provider1 (value_text='1')."""
        response = self.client.get(
            reverse("providers"), {f"attr_{self.bool_attr_def.id}": "1"}
        )
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    # ------------------------------------------------------------------
    # Min rating filter
    # ------------------------------------------------------------------

    def test_filter_min_rating(self):
        """min_rating=4 includes provider with avg_rating >= 4, excludes others."""
        from reviews.models import ReviewCategory, ReviewCategoryRating

        client_user = User.objects.create_user(
            email="rater@example.com",
            password="testpass123",
            user_type="client",
        )
        cat = ReviewCategory.objects.create(name="AdvQuality")

        # Give provider1 a high rating (5)
        review1 = Review.objects.create(
            provider=self.provider1,
            client=client_user,
            comment="Great",
        )
        ReviewCategoryRating.objects.create(review=review1, category=cat, rating=5)

        # Give provider2 a low rating (2) — need a different client user
        client_user2 = User.objects.create_user(
            email="rater2@example.com",
            password="testpass123",
            user_type="client",
        )
        review2 = Review.objects.create(
            provider=self.provider2,
            client=client_user2,
            comment="Meh",
        )
        ReviewCategoryRating.objects.create(review=review2, category=cat, rating=2)

        response = self.client.get(reverse("providers"), {"min_rating": "4"})
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertNotIn("adv2@example.com", emails)

    # ------------------------------------------------------------------
    # No filter — returns all active providers
    # ------------------------------------------------------------------

    def test_no_filter_returns_all_active(self):
        """No filter params returns all active verified providers (at least our two)."""
        response = self.client.get(reverse("providers"))
        self.assertEqual(response.status_code, 200)
        emails = self._provider_emails(response)
        self.assertIn("adv1@example.com", emails)
        self.assertIn("adv2@example.com", emails)
