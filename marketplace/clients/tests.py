from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from providers.models import Provider, Service, ProviderGalleryImage
from reviews.models import Review


class ProviderDirectoryViewTests(TestCase):
    """Tests for the public provider directory view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create active provider
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.active_provider = Provider.objects.create(
            user=self.active_user,
            phone='+1234567890',
            bio='Active provider',
            subscription_status='active'
        )

        # Create inactive provider (should not show)
        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.inactive_provider = Provider.objects.create(
            user=self.inactive_user,
            phone='+9876543210',
            subscription_status='inactive'
        )

        # Create unverified provider (should not show)
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=False
        )
        self.unverified_provider = Provider.objects.create(
            user=self.unverified_user,
            phone='+1111111111',
            subscription_status='active'
        )

    def test_provider_directory_loads(self):
        """Test that provider directory page loads."""
        response = self.client.get(reverse('providers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/provider_list.html')

    def test_home_url_loads_directory(self):
        """Test that home URL loads provider directory."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/provider_list.html')

    def test_only_active_verified_providers_shown(self):
        """Test that only active and verified providers are displayed."""
        response = self.client.get(reverse('providers'))

        # Active provider should be in response
        self.assertContains(response, 'active@example.com')

        # Inactive provider should not be in response
        self.assertNotContains(response, 'inactive@example.com')

        # Unverified provider should not be in response
        self.assertNotContains(response, 'unverified@example.com')

    def test_provider_card_shows_info(self):
        """Test that provider cards show correct information."""
        # Add services and reviews
        Service.objects.create(
            provider=self.active_provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        Review.objects.create(
            provider=self.active_provider,
            rating=5,
            comment='Great service!'
        )
        Review.objects.create(
            provider=self.active_provider,
            rating=4,
            comment='Good'
        )

        response = self.client.get(reverse('providers'))

        # Should show service count
        self.assertContains(response, '1 service')

        # Should show review count
        self.assertContains(response, '2 reviews')

    def test_no_authentication_required(self):
        """Test that provider directory is accessible without login."""
        response = self.client.get(reverse('providers'))
        self.assertEqual(response.status_code, 200)
        # Should not redirect to login
        self.assertNotEqual(response.status_code, 302)

    def test_pagination_works(self):
        """Test that pagination works correctly."""
        # Create 25 active providers
        for i in range(25):
            user = User.objects.create_user(
                email=f'provider{i}@example.com',
                password='testpass123',
                user_type='provider',
                is_email_verified=True
            )
            Provider.objects.create(
                user=user,
                phone=f'+123456789{i}',
                subscription_status='active'
            )

        response = self.client.get(reverse('providers'))

        # Should have pagination context
        self.assertTrue(response.context['is_paginated'])

        # Should show 20 providers per page
        self.assertEqual(len(response.context['providers_with_stats']), 20)


class ProviderDetailViewTests(TestCase):
    """Tests for the public provider detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create active provider
        self.user = User.objects.create_user(
            email='provider@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True,
            first_name='John',
            last_name='Doe'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            bio='Professional massage therapist',
            subscription_status='active'
        )

        # Create services
        self.service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            description='Relaxing Swedish massage',
            price=75.00,
            duration_minutes=60
        )

        # Create reviews
        self.review = Review.objects.create(
            provider=self.provider,
            rating=5,
            client_name='Jane Smith',
            comment='Excellent service!'
        )

    def test_provider_detail_loads(self):
        """Test that provider detail page loads."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clients/provider_detail.html')

    def test_provider_detail_shows_info(self):
        """Test that provider detail shows all information."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )

        # Should show provider name
        self.assertContains(response, 'John Doe')

        # Should show bio
        self.assertContains(response, 'Professional massage therapist')

        # Should show phone
        self.assertContains(response, '+1234567890')

        # Should show email
        self.assertContains(response, 'provider@example.com')

    def test_provider_detail_shows_services(self):
        """Test that services are displayed."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )

        # Should show service type
        self.assertContains(response, 'Swedish Massage')

        # Should show price
        self.assertContains(response, '75')

        # Should show duration
        self.assertContains(response, '60 minutes')

        # Should show description
        self.assertContains(response, 'Relaxing Swedish massage')

    def test_provider_detail_shows_reviews(self):
        """Test that reviews are displayed."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )

        # Should show review content
        self.assertContains(response, 'Excellent service!')

        # Should show reviewer name
        self.assertContains(response, 'Jane Smith')

        # Should show rating (5 stars)
        self.assertContains(response, '★')

    def test_inactive_provider_returns_404(self):
        """Test that inactive provider returns 404."""
        self.provider.subscription_status = 'inactive'
        self.provider.save()

        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertEqual(response.status_code, 404)

    def test_unverified_provider_returns_404(self):
        """Test that unverified provider returns 404."""
        self.user.is_email_verified = False
        self.user.save()

        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertEqual(response.status_code, 404)

    def test_no_authentication_required(self):
        """Test that provider detail is accessible without login."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertEqual(response.status_code, 200)


class ProviderModelHelperTests(TestCase):
    """Tests for Provider model helper methods."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            user_type='provider',
            first_name='John',
            last_name='Doe'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )

    def test_average_rating_with_reviews(self):
        """Test average rating calculation with reviews."""
        Review.objects.create(provider=self.provider, rating=5, comment='Great!')
        Review.objects.create(provider=self.provider, rating=4, comment='Good')
        Review.objects.create(provider=self.provider, rating=3, comment='OK')

        avg = self.provider.average_rating()
        self.assertEqual(avg, 4.0)

    def test_average_rating_without_reviews(self):
        """Test average rating returns 0 without reviews."""
        avg = self.provider.average_rating()
        self.assertEqual(avg, 0)

    def test_get_name_with_full_name(self):
        """Test get_name returns full name."""
        name = self.provider.get_name()
        self.assertEqual(name, 'John Doe')

    def test_get_name_with_first_name_only(self):
        """Test get_name with only first name."""
        self.user.last_name = ''
        self.user.save()
        name = self.provider.get_name()
        self.assertEqual(name, 'John')

    def test_get_name_without_names(self):
        """Test get_name falls back to email."""
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        name = self.provider.get_name()
        self.assertEqual(name, 'test')


class ProviderFilteringTests(TestCase):
    """Tests for provider filtering functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create providers with different services and locations
        self.provider1 = self._create_provider(
            email='provider1@example.com',
            country='USA',
            city='New York'
        )
        Service.objects.create(
            provider=self.provider1,
            service_type='swedish',
            price=50.00,
            duration_minutes=60
        )

        self.provider2 = self._create_provider(
            email='provider2@example.com',
            country='USA',
            city='Los Angeles'
        )
        Service.objects.create(
            provider=self.provider2,
            service_type='deep_tissue',
            price=80.00,
            duration_minutes=60
        )

        self.provider3 = self._create_provider(
            email='provider3@example.com',
            country='Canada',
            city='Toronto'
        )
        Service.objects.create(
            provider=self.provider3,
            service_type='swedish',
            price=100.00,
            duration_minutes=90
        )

    def _create_provider(self, email, country, city):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        provider = Provider.objects.create(
            user=user,
            phone='+1234567890',
            subscription_status='active',
            country=country,
            city=city
        )
        return provider

    def test_filter_by_service_type(self):
        """Test filtering providers by service type."""
        response = self.client.get(reverse('providers') + '?service_type=swedish')
        self.assertEqual(response.status_code, 200)

        # Should show providers 1 and 3 (both offer Swedish)
        self.assertContains(response, 'provider1@example.com')
        self.assertContains(response, 'provider3@example.com')
        # Should not show provider 2 (offers deep tissue)
        self.assertNotContains(response, 'provider2@example.com')

    def test_filter_by_country(self):
        """Test filtering providers by country."""
        response = self.client.get(reverse('providers') + '?country=USA')
        self.assertEqual(response.status_code, 200)

        # Should show USA providers
        self.assertContains(response, 'provider1@example.com')
        self.assertContains(response, 'provider2@example.com')
        # Should not show Canadian provider
        self.assertNotContains(response, 'provider3@example.com')

    def test_filter_by_city(self):
        """Test filtering providers by city."""
        response = self.client.get(reverse('providers') + '?city=New York')
        self.assertEqual(response.status_code, 200)

        # Should show only New York provider
        self.assertContains(response, 'provider1@example.com')
        self.assertNotContains(response, 'provider2@example.com')
        self.assertNotContains(response, 'provider3@example.com')

    def test_filter_by_price_range(self):
        """Test filtering providers by price range."""
        response = self.client.get(reverse('providers') + '?price_min=60&price_max=90')
        self.assertEqual(response.status_code, 200)

        # Should show providers 2 (80) but not 1 (50) or 3 (100)
        self.assertContains(response, 'provider2@example.com')
        self.assertNotContains(response, 'provider1@example.com')
        self.assertNotContains(response, 'provider3@example.com')

    def test_filter_by_min_price_only(self):
        """Test filtering by minimum price."""
        response = self.client.get(reverse('providers') + '?price_min=75')
        self.assertEqual(response.status_code, 200)

        # Should show providers 2 (80) and 3 (100)
        self.assertContains(response, 'provider2@example.com')
        self.assertContains(response, 'provider3@example.com')
        # Should not show provider 1 (50)
        self.assertNotContains(response, 'provider1@example.com')

    def test_filter_by_max_price_only(self):
        """Test filtering by maximum price."""
        response = self.client.get(reverse('providers') + '?price_max=75')
        self.assertEqual(response.status_code, 200)

        # Should show provider 1 (50)
        self.assertContains(response, 'provider1@example.com')
        # Should not show providers 2 (80) or 3 (100)
        self.assertNotContains(response, 'provider2@example.com')
        self.assertNotContains(response, 'provider3@example.com')

    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(
            reverse('providers') + '?service_type=swedish&country=USA&price_max=60'
        )
        self.assertEqual(response.status_code, 200)

        # Should show only provider 1 (Swedish, USA, $50)
        self.assertContains(response, 'provider1@example.com')
        # Should not show provider 2 (not Swedish) or 3 (not USA)
        self.assertNotContains(response, 'provider2@example.com')
        self.assertNotContains(response, 'provider3@example.com')

    def test_filter_preserves_url_params(self):
        """Test that current filter values are preserved in context."""
        response = self.client.get(
            reverse('providers') + '?service_type=swedish&country=USA&price_min=40&price_max=60'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_service_type'], 'swedish')
        self.assertEqual(response.context['current_country'], 'USA')
        self.assertEqual(response.context['current_price_min'], '40')
        self.assertEqual(response.context['current_price_max'], '60')

    def test_reset_filters_link(self):
        """Test that reset link clears all filters."""
        response = self.client.get(reverse('providers'))
        self.assertEqual(response.status_code, 200)

        # All providers should be shown
        self.assertContains(response, 'provider1@example.com')
        self.assertContains(response, 'provider2@example.com')
        self.assertContains(response, 'provider3@example.com')

    def test_invalid_price_values(self):
        """Test that invalid price values are ignored."""
        response = self.client.get(reverse('providers') + '?price_min=invalid&price_max=abc')
        self.assertEqual(response.status_code, 200)

        # Should show all providers (invalid filters ignored)
        self.assertContains(response, 'provider1@example.com')
        self.assertContains(response, 'provider2@example.com')
        self.assertContains(response, 'provider3@example.com')


class ProviderDetailGalleryTests(TestCase):
    """Tests for gallery display on provider detail page."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@example.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='active'
        )

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io
        img = PILImage.new('RGB', (100, 100), color='blue')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile('test.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_gallery_images_in_context(self):
        """Test that gallery images are included in detail view context."""
        ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption='Workspace photo'
        )
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('gallery_images', response.context)
        self.assertEqual(response.context['gallery_images'].count(), 1)

    def test_gallery_section_displayed(self):
        """Test that gallery section is displayed when images exist."""
        ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption='My studio'
        )
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertContains(response, 'Photo Gallery')
        self.assertContains(response, 'My studio')

    def test_gallery_section_hidden_when_empty(self):
        """Test that gallery section is hidden when no images."""
        response = self.client.get(
            reverse('provider_detail', kwargs={'slug': self.user.email})
        )
        self.assertNotContains(response, 'Photo Gallery')
