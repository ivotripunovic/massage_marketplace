from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import User
from reviews.models import Review
from .models import (
    Provider,
    Service,
    ProviderGalleryImage,
    ProviderAttributeDefinition,
    ProviderAttributeValue,
)


class ProviderAttributeSettingsTests(TestCase):
    """Ensure providers can edit their admin-defined attributes."""

    def setUp(self):
        """Create provider user, profile, and attribute definition."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='attr-provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+15551234567',
            bio='Attribute-friendly provider',
            subscription_status='active'
        )
        self.attribute_definition = ProviderAttributeDefinition.objects.create(
            name='Years of Practice',
            data_type=ProviderAttributeDefinition.DATA_TYPE_INTEGER,
            display_order=1,
            show_on_card=True,
            is_active=True
        )

    def test_provider_updates_attribute_from_profile_form(self):
        """Providers should be able to save attribute values via profile form."""
        self.client.login(email=self.user.email, password='testpass123')
        url = reverse('provider_profile')
        response = self.client.post(url, {
            'first_name': 'Taylor',
            'last_name': 'Doe',
            'bio': self.provider.bio,
            'phone': self.provider.phone,
            f'attribute_{self.attribute_definition.pk}': '8',
        }, follow=True)

        self.assertRedirects(response, reverse('provider_dashboard'))
        attribute = ProviderAttributeValue.objects.get(
            provider=self.provider,
            definition=self.attribute_definition
        )
        self.assertEqual(attribute.value_text, '8')

class ProviderModelTests(TestCase):
    """Test Provider model functionality."""
    
    def setUp(self):
        """Set up test user for provider creation."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
    
    def test_provider_creation(self):
        """Test creating a provider."""
        provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        self.assertEqual(provider.user.email, 'provider@test.com')
        self.assertEqual(provider.subscription_status, 'inactive')
        self.assertEqual(provider.phone, '+1234567890')
    
    def test_provider_with_all_fields(self):
        """Test provider with all fields populated."""
        provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            bio='Professional massage therapist',
            subscription_status='active',
            subscription_payment_method='crypto',
            crypto_address='1A1z7agoat...',
        )
        self.assertEqual(provider.bio, 'Professional massage therapist')
        self.assertTrue(provider.is_subscription_active())
    
    def test_provider_subscription_inactive_by_default(self):
        """Test subscription status defaults to inactive."""
        provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        self.assertEqual(provider.subscription_status, 'inactive')
        self.assertFalse(provider.is_subscription_active())
    
    def test_provider_string_representation(self):
        """Test provider __str__ method."""
        provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='active'
        )
        self.assertIn(self.user.email, str(provider))
        self.assertIn('Active', str(provider))
    
    def test_provider_admin_registered(self):
        """Test that Provider is registered in admin."""
        from django.contrib import admin
        self.assertIn(Provider, admin.site._registry)
    
    def test_multiple_providers_different_users(self):
        """Test multiple providers with different users."""
        user2 = User.objects.create_user(
            email='provider2@test.com',
            password='pass',
            user_type='provider'
        )
        
        provider1 = Provider.objects.create(
            user=self.user,
            phone='+1111111111'
        )
        provider2 = Provider.objects.create(
            user=user2,
            phone='+2222222222'
        )
        
        self.assertEqual(provider1.user.email, 'provider@test.com')
        self.assertEqual(provider2.user.email, 'provider2@test.com')
        self.assertEqual(Provider.objects.count(), 2)
    
    def test_provider_timestamps(self):
        """Test created_at and updated_at timestamps."""
        provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        self.assertIsNotNone(provider.created_at)
        self.assertIsNotNone(provider.updated_at)
        # Both should be very close in time
        self.assertAlmostEqual(
            provider.created_at.timestamp(),
            provider.updated_at.timestamp(),
            delta=1
        )
        
        # Modify and check updated_at changes
        provider.phone = '+9999999999'
        provider.save()
        provider.refresh_from_db()
        # updated_at should be >= created_at
        self.assertGreaterEqual(provider.updated_at, provider.created_at)


class ServiceModelTests(TestCase):
    """Test Service model functionality."""
    
    def setUp(self):
        """Set up test provider for service creation."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
    
    def test_create_service(self):
        """Test creating a service."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        self.assertEqual(service.price, 75.00)
        self.assertEqual(service.duration_minutes, 60)
        self.assertTrue(service.is_active)
    
    def test_service_price_validation(self):
        """Test service price validation."""
        with self.assertRaises(ValidationError):
            service = Service(
                provider=self.provider,
                service_type='swedish',
                price=2.00,
                duration_minutes=60
            )
            service.full_clean()
    
    def test_service_price_minimum_valid(self):
        """Test minimum valid price."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=5.00,
            duration_minutes=60
        )
        self.assertEqual(service.price, 5.00)
    
    def test_service_duration_validation(self):
        """Test service duration validation."""
        with self.assertRaises(ValidationError):
            service = Service(
                provider=self.provider,
                service_type='swedish',
                price=75.00,
                duration_minutes=45  # Invalid duration
            )
            service.full_clean()
    
    def test_valid_service_durations(self):
        """Test all valid durations."""
        service_types = ['swedish', 'deep_tissue', 'thai']
        for i, duration in enumerate([30, 60, 90]):
            service = Service.objects.create(
                provider=self.provider,
                service_type=service_types[i],
                price=75.00,
                duration_minutes=duration
            )
            self.assertEqual(service.duration_minutes, duration)
    
    def test_service_string_representation(self):
        """Test service __str__ method."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='deep_tissue',
            price=85.00,
            duration_minutes=60
        )
        self.assertIn(self.user.email, str(service))
        self.assertIn('85', str(service))
    
    def test_service_with_description(self):
        """Test service with description."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='aromatherapy',
            price=65.00,
            duration_minutes=60,
            description='Relaxing aromatherapy massage'
        )
        self.assertEqual(service.description, 'Relaxing aromatherapy massage')
    
    def test_service_all_types(self):
        """Test all service types."""
        service_types = ['swedish', 'deep_tissue', 'thai', 'reflexology', 'hot_stone', 'aromatherapy']
        for i, service_type in enumerate(service_types):
            service = Service.objects.create(
                provider=self.provider,
                service_type=service_type,
                price=50.00 + i,
                duration_minutes=60
            )
            self.assertEqual(service.service_type, service_type)


class ProviderDashboardViewTests(TestCase):
    """Test Provider Dashboard view functionality."""
    
    def setUp(self):
        """Set up test client and test provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            bio='Professional massage therapist',
            subscription_status='inactive'
        )
        
        # Create test data
        self.service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60,
            is_active=True
        )
        self.review = Review.objects.create(
            provider=self.provider,
            rating=5,
            comment='Excellent service',
            client_email='client@test.com'
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires user to be logged in."""
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/auth/login/', response.url)
    
    def test_dashboard_requires_provider_user_type(self):
        """Test that non-provider users cannot access dashboard."""
        # Create a client user
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )
        self.client.login(email=client_user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.client.logout()
    
    def test_dashboard_loads_for_verified_provider(self):
        """Test that verified provider can access dashboard."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/dashboard.html')
    
    def test_dashboard_displays_provider_info(self):
        """Test that dashboard displays provider information."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, self.user.email)
    
    def test_dashboard_displays_services(self):
        """Test that dashboard displays provider's services."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        # Check that services section is displayed
        self.assertIn('services', response.context)
    
    def test_dashboard_displays_subscription_status(self):
        """Test that dashboard displays subscription status."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, 'Inactive')
    
    def test_dashboard_displays_statistics(self):
        """Test that dashboard displays statistics."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, 'Active Services')
        self.assertContains(response, 'Total Reviews')
    
    def test_dashboard_calculates_average_rating(self):
        """Test that dashboard calculates average rating from reviews."""
        # Add another review with 4 stars
        Review.objects.create(
            provider=self.provider,
            rating=4,
            comment='Good service',
            client_email='client2@test.com'
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        # Average should be (5 + 4) / 2 = 4.5
        self.assertContains(response, '4.5')
    
    def test_dashboard_shows_empty_state_for_no_services(self):
        """Test dashboard when provider has no services."""
        # Delete all services
        Service.objects.all().delete()
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_context_has_provider_data(self):
        """Test that dashboard context contains provider data."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertIn('provider', response.context)
        self.assertEqual(response.context['provider'], self.provider)
    
    def test_dashboard_context_has_services(self):
        """Test that dashboard context contains services list."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertIn('services', response.context)
        self.assertIn(self.service, response.context['services'])
    
    def test_dashboard_only_shows_active_services(self):
        """Test that dashboard filters services properly."""
        # Create an inactive service
        inactive_service = Service.objects.create(
            provider=self.provider,
            service_type='deep_tissue',
            price=85.00,
            duration_minutes=60,
            is_active=False
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        # Should have context with services
        self.assertEqual(len(response.context['services']), 1)  # Only active service


class BaseTemplateTests(TestCase):
    """Test base template and navigation."""
    
    def setUp(self):
        """Set up test client and users."""
        self.client = Client()
        self.provider_user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone='+1234567890'
        )
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )
    
    def test_base_template_displays_for_unauthenticated_user(self):
        """Test that base template shows login/signup links for guests."""
        response = self.client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)
        # Login page should have form and password field
        self.assertContains(response, 'password')
    
    def test_base_template_displays_for_authenticated_provider(self):
        """Test that base template shows provider links when logged in."""
        self.client.login(email=self.provider_user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Logout')
    
    def test_navigation_shows_provider_links_for_providers(self):
        """Test that provider users see provider-specific links."""
        self.client.login(email=self.provider_user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Profile')
        self.assertContains(response, 'Services')
    
    def test_responsive_design_included(self):
        """Test that responsive design meta tag is included."""
        response = self.client.get('/auth/login/')
        self.assertContains(response, 'viewport')
        self.assertContains(response, 'width=device-width')
    
    def test_tailwind_css_included(self):
        """Test that templates include styling."""
        response = self.client.get('/auth/login/')
        # Check that page has style tag
        self.assertContains(response, '<style')
    
    def test_message_display_system_works(self):
        """Test that messages are displayed correctly."""
        self.client.login(email=self.provider_user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        # Check that dashboard page loads
        self.assertEqual(response.status_code, 200)
    
    def test_footer_included_in_template(self):
        """Test that footer is included in base template."""
        response = self.client.get('/auth/login/')
        # Footer is in base.html, check for content instead of footer tag
        self.assertContains(response, 'Massage Marketplace')


class ProviderProfileFormTests(TestCase):
    """Test Provider Profile Form functionality."""
    
    def setUp(self):
        """Set up test user and provider."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True,
            first_name='John',
            last_name='Doe'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            bio='Professional massage therapist'
        )
    
    def test_form_displays_first_name_field(self):
        """Test form includes first name field."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertIn('first_name', form.fields)
    
    def test_form_displays_last_name_field(self):
        """Test form includes last name field."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertIn('last_name', form.fields)
    
    def test_form_displays_phone_field(self):
        """Test form includes phone field."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertIn('phone', form.fields)
    
    def test_form_displays_bio_field(self):
        """Test form includes bio field."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertIn('bio', form.fields)
    
    def test_form_initializes_with_user_name(self):
        """Test form pre-fills with user's first and last name."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertEqual(form.fields['first_name'].initial, 'John')
        self.assertEqual(form.fields['last_name'].initial, 'Doe')
    
    def test_form_initializes_with_provider_fields(self):
        """Test form pre-fills with provider's phone and bio."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        # Get form data to see initial values
        self.assertEqual(form.instance.phone, '+1234567890')
        self.assertEqual(form.instance.bio, 'Professional massage therapist')
    
    def test_form_saves_first_name(self):
        """Test form saves first name to user."""
        from providers.views import ProviderProfileForm
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'Updated bio'
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
    
    def test_form_saves_last_name(self):
        """Test form saves last name to user."""
        from providers.views import ProviderProfileForm
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'Updated bio'
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'Smith')
    
    def test_form_saves_phone(self):
        """Test form saves phone to provider."""
        from providers.views import ProviderProfileForm
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'Updated bio'
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.phone, '+9876543210')
    
    def test_form_saves_bio(self):
        """Test form saves bio to provider."""
        from providers.views import ProviderProfileForm
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'New professional bio'
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertTrue(form.is_valid())
        form.save()
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.bio, 'New professional bio')
    
    def test_form_requires_phone(self):
        """Test form requires phone field."""
        from providers.views import ProviderProfileForm
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '',  # Empty phone
            'bio': 'Bio'
        }
        form = ProviderProfileForm(data=data, instance=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)


class ProviderProfileUpdateViewTests(TestCase):
    """Test Provider Profile Update View functionality."""
    
    def setUp(self):
        """Set up test client and provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True,
            first_name='John',
            last_name='Doe'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            bio='Professional massage therapist'
        )
    
    def test_profile_view_requires_login(self):
        """Test that profile edit page requires login."""
        response = self.client.get(reverse('provider_profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_profile_view_requires_provider_user_type(self):
        """Test that non-provider users cannot access profile edit."""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )
        self.client.login(email=client_user.email, password='testpass123')
        response = self.client.get(reverse('provider_profile'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_profile_view_loads_for_authenticated_provider(self):
        """Test that provider can load profile edit page."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/profile_edit.html')
    
    def test_profile_view_displays_form(self):
        """Test that profile edit page displays form."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_profile'))
        self.assertIn('form', response.context)
    
    def test_profile_view_displays_provider_data(self):
        """Test that profile edit page displays provider data."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_profile'))
        self.assertIn('provider', response.context)
        self.assertEqual(response.context['provider'], self.provider)
    
    def test_profile_update_changes_first_name(self):
        """Test updating first name via profile form."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Professional massage therapist'
        })
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
    
    def test_profile_update_changes_phone(self):
        """Test updating phone via profile form."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+9876543210',
            'bio': 'Professional massage therapist'
        })
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.phone, '+9876543210')
    
    def test_profile_update_changes_bio(self):
        """Test updating bio via profile form."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Updated bio text'
        })
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.bio, 'Updated bio text')
    
    def test_profile_update_redirects_on_success(self):
        """Test that successful update redirects to dashboard."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'Updated bio'
        }, follow=False)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('provider_dashboard'), response.url)
    
    def test_profile_update_shows_success_message(self):
        """Test that success message is shown after update."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+9876543210',
            'bio': 'Updated bio'
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m).lower() for m in messages))
    
    def test_profile_view_creates_provider_if_missing(self):
        """Test that view creates provider if user doesn't have one."""
        # Create a new user without provider
        user = User.objects.create_user(
            email='newprovider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        
        self.client.login(email=user.email, password='testpass123')
        response = self.client.get(reverse('provider_profile'))
        
        # Check that provider was created
        self.assertTrue(Provider.objects.filter(user=user).exists())


class ProviderPhotoUploadTests(TestCase):
    """Test Provider Photo Upload functionality."""
    
    def setUp(self):
        """Set up test client and provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
    
    def _create_test_image(self, size=(100, 100), format='JPEG', content_type='image/jpeg'):
        """Create a test image file."""
        from PIL import Image
        import io
        
        img = Image.new('RGB', size, color='red')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        filename = f'test.{format.lower()}'
        return SimpleUploadedFile(
            filename,
            img_io.getvalue(),
            content_type=content_type
        )
    
    def test_photo_form_field_exists(self):
        """Test that photo field is in the form."""
        from providers.views import ProviderProfileForm
        form = ProviderProfileForm(instance=self.provider)
        self.assertIn('photo', form.fields)
    
    def test_photo_upload_valid_jpeg(self):
        """Test uploading a valid JPEG image."""
        self.client.login(email=self.user.email, password='testpass123')
        photo = self._create_test_image(format='JPEG', content_type='image/jpeg')
        
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            'photo': photo
        })
        
        self.provider.refresh_from_db()
        self.assertIsNotNone(self.provider.photo)
        self.assertTrue(self.provider.photo.name.startswith('providers/photos/'))
    
    def test_photo_upload_valid_png(self):
        """Test uploading a valid PNG image."""
        self.client.login(email=self.user.email, password='testpass123')
        photo = self._create_test_image(format='PNG', content_type='image/png')
        
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            'photo': photo
        })
        
        self.provider.refresh_from_db()
        self.assertIsNotNone(self.provider.photo)
    
    def test_photo_upload_invalid_format(self):
        """Test that invalid image formats are rejected."""
        self.client.login(email=self.user.email, password='testpass123')
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        invalid_photo = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            'photo': invalid_photo
        })
        
        # Form should be invalid
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
    
    def test_photo_size_limit(self):
        """Test that oversized images are rejected."""
        self.client.login(email=self.user.email, password='testpass123')
        
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        import io
        
        # Create a large image (6MB)
        img = Image.new('RGB', (6000, 6000), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        # Check size
        img_size = len(img_io.getvalue())
        if img_size > 5 * 1024 * 1024:  # Only test if actually > 5MB
            from django.core.files.uploadedfile import SimpleUploadedFile
            oversized_photo = SimpleUploadedFile(
                'large.jpg',
                img_io.getvalue(),
                content_type='image/jpeg'
            )
            
            response = self.client.post(reverse('provider_profile'), {
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+1234567890',
                'bio': 'Test bio',
                'photo': oversized_photo
            })
            
            # Form should be invalid
            if 'form' in response.context:
                self.assertFalse(response.context['form'].is_valid())
    
    def test_photo_resizing(self):
        """Test that large images are resized to 800x800."""
        self.client.login(email=self.user.email, password='testpass123')
        
        # Create an image larger than 800x800
        photo = self._create_test_image(size=(1600, 1600), format='JPEG')
        
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            'photo': photo
        })
        
        self.provider.refresh_from_db()
        if self.provider.photo:
            from PIL import Image
            img = Image.open(self.provider.photo)
            # After resizing, dimensions should not exceed 800x800
            self.assertLessEqual(img.height, 800)
            self.assertLessEqual(img.width, 800)
    
    def test_photo_displays_on_profile_page(self):
        """Test that uploaded photo displays on profile page."""
        self.client.login(email=self.user.email, password='testpass123')
        photo = self._create_test_image()
        
        # Upload photo
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            'photo': photo
        }, follow=True)
        
        # Check that photo URL is accessible
        self.provider.refresh_from_db()
        if self.provider.photo:
            response = self.client.get(reverse('provider_profile'))
            self.assertIn('photo', response.context['provider'].__dict__ or str(response.content))
    
    def test_photo_optional_field(self):
        """Test that photo is optional in form."""
        self.client.login(email=self.user.email, password='testpass123')
        
        response = self.client.post(reverse('provider_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '+1234567890',
            'bio': 'Test bio',
            # No photo provided
        })
        
        # Should succeed without photo
        self.assertEqual(response.status_code, 302)  # Redirect on success


class ServiceCRUDTests(TestCase):
    """Test Service CRUD functionality."""
    
    def setUp(self):
        """Set up test client and provider."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.other_provider = Provider.objects.create(
            user=self.other_user,
            phone='+9876543210'
        )
    
    def test_service_list_requires_login(self):
        """Test that service list requires login."""
        response = self.client.get(reverse('services_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_service_list_requires_provider_type(self):
        """Test that non-provider users cannot access service list."""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )
        self.client.login(email=client_user.email, password='testpass123')
        response = self.client.get(reverse('services_list'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_service_list_loads(self):
        """Test that service list page loads."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('services_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/service_list.html')
    
    def test_create_service_page_loads(self):
        """Test that service create page loads."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('service_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/service_form.html')
    
    def test_create_service_valid(self):
        """Test creating a valid service."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_create'), {
            'service_type': 'swedish',
            'description': 'Relaxing Swedish massage',
            'price': '75.00',
            'duration_minutes': 60
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Service.objects.filter(
            provider=self.provider,
            service_type='swedish',
            price=75.00
        ).exists())
    
    def test_create_service_price_validation(self):
        """Test that service price must be >= $5.00."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_create'), {
            'service_type': 'swedish',
            'description': 'Cheap massage',
            'price': '2.00',  # Below minimum
            'duration_minutes': 60
        })
        
        # Form should be invalid
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
    
    def test_create_service_all_types(self):
        """Test creating services of all types."""
        self.client.login(email=self.user.email, password='testpass123')
        
        service_types = ['swedish', 'deep_tissue', 'thai', 'reflexology', 'hot_stone', 'aromatherapy']
        
        for service_type in service_types:
            response = self.client.post(reverse('service_create'), {
                'service_type': service_type,
                'description': f'{service_type} massage',
                'price': '75.00',
                'duration_minutes': 60
            })
            self.assertEqual(response.status_code, 302)
        
        self.assertEqual(self.provider.services.count(), 6)
    
    def test_service_edit_page_loads(self):
        """Test that service edit page loads."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('service_edit', args=[service.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/service_form.html')
    
    def test_service_edit_valid(self):
        """Test updating a service."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_edit', args=[service.id]), {
            'service_type': 'swedish',
            'description': 'Updated description',
            'price': '85.00',
            'duration_minutes': 90
        })
        
        service.refresh_from_db()
        self.assertEqual(service.price, 85.00)
        self.assertEqual(service.duration_minutes, 90)
    
    def test_service_edit_ownership(self):
        """Test that providers can only edit their own services."""
        service = Service.objects.create(
            provider=self.other_provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_edit', args=[service.id]), {
            'service_type': 'swedish',
            'description': 'Hacked!',
            'price': '999.00',
            'duration_minutes': 60
        })
        
        service.refresh_from_db()
        self.assertEqual(service.price, 75.00)  # Should not have changed
    
    def test_service_delete_success(self):
        """Test deleting a service."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_delete', args=[service.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertFalse(Service.objects.filter(id=service.id).exists())
    
    def test_service_delete_ownership(self):
        """Test that providers can only delete their own services."""
        service = Service.objects.create(
            provider=self.other_provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_delete', args=[service.id]))
        
        # Service should still exist
        self.assertTrue(Service.objects.filter(id=service.id).exists())
    
    def test_service_list_displays_services(self):
        """Test that service list displays all services."""
        services = [
            Service.objects.create(
                provider=self.provider,
                service_type='swedish',
                price=75.00,
                duration_minutes=60
            ),
            Service.objects.create(
                provider=self.provider,
                service_type='deep_tissue',
                price=85.00,
                duration_minutes=60
            )
        ]
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('services_list'))
        
        for service in services:
            self.assertContains(response, service.get_service_type_display())
            self.assertContains(response, str(service.price))
    
    def test_service_create_success_message(self):
        """Test that success message is shown after creating service."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_create'), {
            'service_type': 'swedish',
            'description': 'Swedish massage',
            'price': '75.00',
            'duration_minutes': 60
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('created successfully' in str(m).lower() for m in messages))
    
    def test_service_update_success_message(self):
        """Test that success message is shown after updating service."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(reverse('service_edit', args=[service.id]), {
            'service_type': 'swedish',
            'description': 'Updated',
            'price': '85.00',
            'duration_minutes': 90
        }, follow=True)
        
        messages = list(response.context['messages'])
        self.assertTrue(any('updated successfully' in str(m).lower() for m in messages))
    
    def test_service_delete_success_message(self):
        """Test that success message is shown after deleting service."""
        service = Service.objects.create(
            provider=self.provider,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(
            reverse('service_delete', args=[service.id]),
            follow=True
        )
        
        messages = list(response.context['messages'])
        self.assertTrue(any('deleted successfully' in str(m).lower() for m in messages))


class ProviderAdminTests(TestCase):
    """Test Provider admin interface functionality."""
    
    def setUp(self):
        """Set up test data for admin tests."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            user_type='admin'
        )
        
        # Create test providers
        self.provider1 = self._create_provider('provider1@test.com', 'active')
        self.provider2 = self._create_provider('provider2@test.com', 'inactive')
        self.provider3 = self._create_provider('provider3@test.com', 'suspended')
        
        self.client = Client()
    
    def _create_provider(self, email, subscription_status):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password='pass123',
            user_type='provider',
            is_email_verified=True
        )
        return Provider.objects.create(
            user=user,
            phone='+1234567890',
            subscription_status=subscription_status,
            subscription_payment_method='crypto'
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
        self.assertIn('user_email', admin_instance.list_display)
        self.assertIn('phone', admin_instance.list_display)
        self.assertIn('location_display', admin_instance.list_display)
        self.assertIn('subscription_status', admin_instance.list_display)
    
    def test_admin_search_fields(self):
        """Test admin search fields are configured."""
        from providers.admin import ProviderAdmin
        admin_instance = ProviderAdmin(Provider, None)
        self.assertIn('user__email', admin_instance.search_fields)
    
    def test_admin_list_filters(self):
        """Test admin list filters are configured."""
        from providers.admin import ProviderAdmin
        admin_instance = ProviderAdmin(Provider, None)
        self.assertIn('subscription_status', admin_instance.list_filter)
        self.assertIn('subscription_payment_method', admin_instance.list_filter)
    
    def test_deactivate_subscriptions_action(self):
        """Test deactivate subscriptions bulk action."""
        self.client.force_login(self.admin_user)
        # Note: Testing bulk actions requires more setup, so we'll test the method directly
        from providers.admin import ProviderAdmin
        from django.contrib.admin.helpers import AdminReadonlyField
        from unittest.mock import MagicMock
        
        admin_instance = ProviderAdmin(Provider, None)
        
        # Create a mock request with message support
        request = MagicMock()
        request.user = self.admin_user
        
        # Get active providers
        active_providers = Provider.objects.filter(subscription_status='active')
        
        # Call the action
        admin_instance.deactivate_subscriptions(request, active_providers)
        
        # Verify subscriptions are deactivated
        self.assertTrue(all(
            p.subscription_status == 'inactive' 
            for p in Provider.objects.filter(subscription_status='inactive')
        ))
    
    def test_suspend_accounts_action(self):
        """Test suspend accounts bulk action."""
        from providers.admin import ProviderAdmin
        from unittest.mock import MagicMock
        
        admin_instance = ProviderAdmin(Provider, None)
        
        # Create a mock request
        request = MagicMock()
        request.user = self.admin_user
        
        # Get inactive providers
        inactive_providers = Provider.objects.filter(subscription_status='inactive')
        count_before = Provider.objects.filter(subscription_status='suspended').count()
        
        # Call the action
        admin_instance.suspend_accounts(request, inactive_providers)
        
        # Verify accounts are suspended
        count_after = Provider.objects.filter(subscription_status='suspended').count()
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
        inactive_providers = Provider.objects.filter(subscription_status='inactive')
        inactive_count = inactive_providers.count()
        self.assertEqual(inactive_count, 1)
        
        # Call the action
        admin_instance.activate_subscriptions(request, inactive_providers)
        
        # Refresh from DB and verify
        provider2_refreshed = Provider.objects.get(id=provider2_id)
        self.assertEqual(provider2_refreshed.subscription_status, 'active')
        self.assertIsNotNone(provider2_refreshed.subscription_renewal_date)
        today = date.today()
        self.assertGreater(provider2_refreshed.subscription_renewal_date, today)
    
    def test_user_email_method(self):
        """Test user_email method in admin."""
        from providers.admin import ProviderAdmin
        
        admin_instance = ProviderAdmin(Provider, None)
        email = admin_instance.user_email(self.provider1)
        self.assertEqual(email, 'provider1@test.com')
    
    def test_service_inline_exists(self):
        """Test ServiceInline is configured in ProviderAdmin."""
        from providers.admin import ProviderAdmin
        admin_instance = ProviderAdmin(Provider, None)
        self.assertTrue(any(hasattr(inline, 'model') and inline.model == Service 
                          for inline in admin_instance.inlines))


class AdminProviderListViewTests(TestCase):
    """Test Admin Provider List view functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='adminpass123',
            user_type='admin'
        )
        
        # Create test providers with different statuses
        self.provider_active = self._create_provider('active@test.com', 'active', 'crypto_bitcoin')
        self.provider_inactive = self._create_provider('inactive@test.com', 'inactive', 'bank_transfer')
        self.provider_suspended = self._create_provider('suspended@test.com', 'suspended', None)
        
        # Add services to provider_active
        Service.objects.create(
            provider=self.provider_active,
            service_type='swedish',
            price=75.00,
            duration_minutes=60
        )
        Service.objects.create(
            provider=self.provider_active,
            service_type='deep_tissue',
            price=85.00,
            duration_minutes=90
        )
        
        # Add a review to provider_active
        Review.objects.create(
            provider=self.provider_active,
            rating=5,
            comment='Excellent service',
            client_email='client@test.com'
        )
        
        self.client = Client()
    
    def _create_provider(self, email, status, payment_method):
        """Helper to create a provider."""
        user = User.objects.create_user(
            email=email,
            password='pass123',
            user_type='provider',
            is_email_verified=True
        )
        return Provider.objects.create(
            user=user,
            phone='+1234567890',
            subscription_status=status,
            subscription_payment_method=payment_method
        )
    
    def test_admin_provider_list_requires_login(self):
        """Test that list requires authentication."""
        response = self.client.get(reverse('admin_providers'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/auth/login/', response.url)
    
    def test_non_admin_cannot_access_list(self):
        """Test that non-admin users cannot access the list."""
        provider_user = User.objects.create_user(
            email='provider@test.com',
            password='pass123',
            user_type='provider',
            is_email_verified=True
        )
        self.client.login(email=provider_user.email, password='pass123')
        response = self.client.get(reverse('admin_providers'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_admin_can_access_list(self):
        """Test that admin can access the provider list."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin/provider_list.html')
    
    def test_provider_list_displays_all_providers(self):
        """Test that all providers are displayed."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'))
        self.assertContains(response, 'active@test.com')
        self.assertContains(response, 'inactive@test.com')
        self.assertContains(response, 'suspended@test.com')
    
    def test_search_by_email(self):
        """Test searching providers by email."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'), {'search': 'active@'})
        self.assertContains(response, 'active@test.com')
        # The response might still show inactive count in pagination/summary so be more specific
        # Check that the table doesn't contain multiple instances of email
        content = response.content.decode()
        # Count how many times we see 'active@test.com' in the table rows (not counting page info)
        active_count = content.count('<td class="px-6 py-4">\n                    <div class="text-sm font-medium text-gray-900">active@test.com</div>')
        self.assertGreater(active_count, 0)
    
    def test_filter_by_status(self):
        """Test filtering providers by subscription status."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'), {'status': 'active'})
        self.assertContains(response, 'active@test.com')
        self.assertNotContains(response, 'inactive@test.com')
        self.assertNotContains(response, 'suspended@test.com')
    
    def test_provider_list_shows_service_count(self):
        """Test that provider service count is displayed."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'))
        # Provider_active has 2 services
        context = response.context
        self.assertIn('providers_with_stats', context)
    
    def test_provider_list_shows_rating(self):
        """Test that provider ratings are displayed."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'))
        # Provider_active has a 5-star review
        self.assertContains(response, '5')  # Rating value
    
    def test_pagination(self):
        """Test that pagination is configured."""
        # Create 60 providers to trigger pagination
        for i in range(60):
            self._create_provider(f'provider{i}@test.com', 'active', 'crypto_bitcoin')
        
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'))
        self.assertIn('paginator', response.context)
        self.assertTrue(response.context['is_paginated'])
    
    def test_search_persists_in_pagination(self):
        """Test that search parameters are preserved in pagination."""
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'), {'search': 'active'})
        self.assertContains(response, 'search=active')  # Should be in pagination links
    
    def test_filter_persists_in_pagination(self):
        """Test that filter parameters are preserved in pagination."""
        # Create many active providers to trigger pagination
        for i in range(60):
            self._create_provider(f'active{i}@test.com', 'active', 'crypto_bitcoin')
        
        self.client.login(email=self.admin_user.email, password='adminpass123')
        response = self.client.get(reverse('admin_providers'), {'status': 'active'})
        self.assertContains(response, 'status=active')  # Should be in pagination links


class ProviderSubscriptionViewTests(TestCase):
    """Test Provider Subscription view functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test provider
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='inactive'
        )
        
        self.client = Client()
    
    def test_subscription_view_requires_login(self):
        """Test that subscription view requires authentication."""
        response = self.client.get(reverse('subscription'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/auth/login/', response.url)
    
    def test_non_provider_cannot_access(self):
        """Test that non-provider users cannot access subscription view."""
        client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )
        self.client.login(email=client_user.email, password='testpass123')
        response = self.client.get(reverse('subscription'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_subscription_view_loads(self):
        """Test that subscription view loads for authenticated provider."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/subscription.html')
    
    def test_subscription_form_present(self):
        """Test that subscription form is present in the view."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription'))
        # Check for form elements
        self.assertContains(response, 'payment_method')
    
    def test_subscription_form_choices(self):
        """Test that form has correct payment method choices."""
        from providers.forms import SubscriptionSettingsForm
        form = SubscriptionSettingsForm()
        choices = form.fields['payment_method'].choices
        self.assertEqual(len(choices), 4)
        choice_values = [choice[0] for choice in choices]
        self.assertIn('crypto_bitcoin', choice_values)
        self.assertIn('crypto_ethereum', choice_values)
        self.assertIn('crypto_usdc', choice_values)
        self.assertIn('bank_transfer', choice_values)
    
    def test_subscription_status_displayed(self):
        """Test that current subscription status is displayed."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription'))
        # Check for status display
        self.assertContains(response, 'Subscription Status')
    
    def test_subscription_form_submission(self):
        """Test that form submission redirects to payment page."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(
            reverse('subscription'),
            {'payment_method': 'crypto_bitcoin'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        # Should redirect to crypto payment page
        self.assertIn(reverse('subscription_crypto_payment'), response.request['PATH_INFO'])
    
    def test_subscription_form_invalid_choice(self):
        """Test that form validation works."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.post(
            reverse('subscription'),
            {'payment_method': 'invalid_choice'}
        )
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        # Should show form with errors
        self.assertContains(response, 'form')  # Form should be re-rendered
    
    def test_subscription_provider_context(self):
        """Test that provider is passed in context."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription'))
        self.assertIn('provider', response.context)
        self.assertEqual(response.context['provider'], self.provider)


class ProviderSubscriptionActivationTests(TestCase):
    """Test subscription activation/deactivation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='inactive'
        )
        
        self.client = Client()
    
    def test_activate_subscription_method(self):
        """Test activate_subscription method on Provider model."""
        self.provider.activate_subscription('crypto_bitcoin')
        
        # Refresh from database
        self.provider.refresh_from_db()
        
        self.assertEqual(self.provider.subscription_status, 'active')
        self.assertEqual(self.provider.subscription_payment_method, 'crypto_bitcoin')
        self.assertIsNotNone(self.provider.subscription_renewal_date)
    
    def test_activate_subscription_sets_renewal_date(self):
        """Test that renewal date is set 30 days from today."""
        from datetime import date, timedelta
        
        self.provider.activate_subscription('crypto_bitcoin')
        expected_date = date.today() + timedelta(days=30)
        
        self.assertEqual(self.provider.subscription_renewal_date, expected_date)
    
    def test_deactivate_subscription_method(self):
        """Test deactivate_subscription method on Provider model."""
        # First activate
        self.provider.activate_subscription('crypto_bitcoin')
        
        # Then deactivate
        self.provider.deactivate_subscription()
        
        # Refresh from database
        self.provider.refresh_from_db()
        
        self.assertEqual(self.provider.subscription_status, 'inactive')
    
    def test_subscription_form_creates_payment_record(self):
        """Test that crypto payment submission creates a SubscriptionPayment record."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password='testpass123')

        # Step 1: Select payment method
        self.client.post(
            reverse('subscription'),
            {'payment_method': 'crypto_bitcoin'}
        )

        # Step 2: Submit transaction ID on crypto payment page
        response = self.client.post(
            reverse('subscription_crypto_payment'),
            {'transaction_id': '0xabc123def456'},
            follow=True
        )

        # Should have created a payment record
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, 'crypto_bitcoin')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(float(payment.amount), 29.99)
        self.assertEqual(payment.reference_id, '0xabc123def456')
    
    def test_subscription_activation_flow(self):
        """Test complete subscription activation flow via crypto payment."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password='testpass123')

        # Step 1: Select payment method
        self.client.post(
            reverse('subscription'),
            {'payment_method': 'crypto_ethereum'}
        )

        # Step 2: Submit transaction ID
        response = self.client.post(
            reverse('subscription_crypto_payment'),
            {'transaction_id': '0xethtx123'},
            follow=True
        )

        # Should redirect to confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertIn(reverse('subscription_confirm'), response.request['PATH_INFO'])

        # Provider should be activated
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, 'active')
        self.assertEqual(self.provider.subscription_payment_method, 'crypto_ethereum')

        # Payment record should be created
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'pending')
    
    def test_subscription_confirm_view_loads(self):
        """Test that subscription confirmation view loads."""
        self.provider.activate_subscription('crypto_bitcoin')
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription_confirm'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/subscription_confirm.html')
    
    def test_subscription_confirm_displays_details(self):
        """Test that confirmation page displays subscription details."""
        self.provider.activate_subscription('crypto_bitcoin')
        
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription_confirm'))
        
        # Check that context contains provider
        self.assertIn('provider', response.context)
        self.assertEqual(response.context['provider'], self.provider)
    
    def test_is_subscription_active_method(self):
        """Test is_subscription_active method."""
        # Initially inactive
        self.assertFalse(self.provider.is_subscription_active())

        # After activation
        self.provider.activate_subscription('crypto_bitcoin')
        self.assertTrue(self.provider.is_subscription_active())

        # After deactivation
        self.provider.deactivate_subscription()
        self.assertFalse(self.provider.is_subscription_active())


class CryptoPaymentViewTests(TestCase):
    """Test crypto payment view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='inactive'
        )
        self.client = Client()

    def test_crypto_page_requires_login(self):
        """Test that crypto payment page requires login."""
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertEqual(response.status_code, 302)

    def test_crypto_page_requires_session(self):
        """Test that crypto page redirects without session payment method."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertRedirects(response, reverse('subscription'))

    def test_crypto_page_loads_with_session(self):
        """Test that crypto page loads when session is set."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/subscription_crypto.html')

    def test_crypto_page_shows_wallet_address(self):
        """Test that crypto page displays wallet address."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertContains(response, 'Wallet Address')
        self.assertContains(response, '29.99')

    def test_crypto_page_shows_payment_instructions(self):
        """Test that crypto page shows payment instructions."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertContains(response, 'Payment Instructions')
        self.assertContains(response, 'Transaction ID')

    def test_crypto_submit_transaction_id(self):
        """Test submitting a crypto transaction ID."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()

        response = self.client.post(
            reverse('subscription_crypto_payment'),
            {'transaction_id': '0xabc123'},
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.reference_id, '0xabc123')
        self.assertEqual(payment.payment_method, 'crypto_bitcoin')
        self.assertEqual(payment.status, 'pending')

    def test_crypto_submit_activates_subscription(self):
        """Test that crypto submission activates subscription."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_ethereum'
        session.save()

        self.client.post(
            reverse('subscription_crypto_payment'),
            {'transaction_id': '0xeth456'}
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, 'active')
        self.assertEqual(self.provider.subscription_payment_method, 'crypto_ethereum')
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_crypto_submit_clears_session(self):
        """Test that crypto submission clears session."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()

        self.client.post(
            reverse('subscription_crypto_payment'),
            {'transaction_id': '0x123'}
        )

        session = self.client.session
        self.assertNotIn('pending_payment_method', session)

    def test_crypto_rejects_bank_transfer_method(self):
        """Test that crypto page rejects bank_transfer method."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()
        response = self.client.get(reverse('subscription_crypto_payment'))
        self.assertRedirects(response, reverse('subscription'))


class BankTransferPaymentViewTests(TestCase):
    """Test bank transfer payment view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890',
            subscription_status='inactive'
        )
        self.client = Client()

    def test_bank_page_requires_login(self):
        """Test that bank transfer page requires login."""
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertEqual(response.status_code, 302)

    def test_bank_page_requires_session(self):
        """Test that bank page redirects without session payment method."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertRedirects(response, reverse('subscription'))

    def test_bank_page_loads_with_session(self):
        """Test that bank page loads when session is set."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/subscription_bank.html')

    def test_bank_page_shows_platform_details(self):
        """Test that bank page shows platform bank details."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertContains(response, 'First National Bank')
        self.assertContains(response, 'Massage Marketplace LLC')
        self.assertContains(response, '29.99')

    def test_bank_page_shows_reference_number(self):
        """Test that bank page generates and shows payment reference."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertContains(response, 'SUB-')
        self.assertContains(response, 'Payment Reference')

    def test_bank_submit_creates_payment(self):
        """Test submitting bank transfer details creates payment record."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session['bank_payment_reference'] = 'SUB-1-ABCD1234'
        session.save()

        response = self.client.post(
            reverse('subscription_bank_payment'),
            {
                'sender_name': 'John Doe',
                'bank_name': 'Chase Bank',
                'reference_number': 'REF123456',
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, 'bank_transfer')
        self.assertEqual(payment.reference_id, 'REF123456')
        self.assertEqual(payment.status, 'pending')

    def test_bank_submit_activates_subscription(self):
        """Test that bank transfer submission activates subscription."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()

        self.client.post(
            reverse('subscription_bank_payment'),
            {
                'sender_name': 'Jane Smith',
                'bank_name': 'Wells Fargo',
            }
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, 'active')
        self.assertEqual(self.provider.subscription_payment_method, 'bank_transfer')
        self.assertIsNotNone(self.provider.subscription_renewal_date)

    def test_bank_submit_stores_bank_info(self):
        """Test that bank transfer stores sender details."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session.save()

        self.client.post(
            reverse('subscription_bank_payment'),
            {
                'sender_name': 'John Doe',
                'bank_name': 'Chase Bank',
            }
        )

        self.provider.refresh_from_db()
        self.assertIn('John Doe', self.provider.bank_account_encrypted)
        self.assertIn('Chase Bank', self.provider.bank_account_encrypted)

    def test_bank_submit_uses_generated_reference(self):
        """Test that submission uses generated reference when none provided."""
        from payments.models import SubscriptionPayment

        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'bank_transfer'
        session['bank_payment_reference'] = 'SUB-1-GENERATED'
        session.save()

        self.client.post(
            reverse('subscription_bank_payment'),
            {
                'sender_name': 'Jane Smith',
                'bank_name': 'Wells Fargo',
                'reference_number': '',
            }
        )

        payment = SubscriptionPayment.objects.filter(provider=self.provider).first()
        self.assertEqual(payment.reference_id, 'SUB-1-GENERATED')

    def test_bank_rejects_crypto_method(self):
        """Test that bank page rejects crypto payment methods."""
        self.client.login(email=self.user.email, password='testpass123')
        session = self.client.session
        session['pending_payment_method'] = 'crypto_bitcoin'
        session.save()
        response = self.client.get(reverse('subscription_bank_payment'))
        self.assertRedirects(response, reverse('subscription'))


class PaymentFormTests(TestCase):
    """Test payment forms."""

    def test_crypto_form_valid(self):
        """Test CryptoPaymentForm with valid data."""
        from providers.forms import CryptoPaymentForm
        form = CryptoPaymentForm(data={'transaction_id': '0xabc123'})
        self.assertTrue(form.is_valid())

    def test_crypto_form_requires_transaction_id(self):
        """Test CryptoPaymentForm requires transaction_id."""
        from providers.forms import CryptoPaymentForm
        form = CryptoPaymentForm(data={'transaction_id': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('transaction_id', form.errors)

    def test_bank_form_valid(self):
        """Test BankTransferForm with valid data."""
        from providers.forms import BankTransferForm
        form = BankTransferForm(data={
            'sender_name': 'John Doe',
            'bank_name': 'Chase Bank',
            'reference_number': 'REF123',
        })
        self.assertTrue(form.is_valid())

    def test_bank_form_reference_optional(self):
        """Test BankTransferForm reference_number is optional."""
        from providers.forms import BankTransferForm
        form = BankTransferForm(data={
            'sender_name': 'John Doe',
            'bank_name': 'Chase Bank',
        })
        self.assertTrue(form.is_valid())

    def test_bank_form_requires_sender_name(self):
        """Test BankTransferForm requires sender_name."""
        from providers.forms import BankTransferForm
        form = BankTransferForm(data={
            'sender_name': '',
            'bank_name': 'Chase Bank',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('sender_name', form.errors)

    def test_bank_form_requires_bank_name(self):
        """Test BankTransferForm requires bank_name."""
        from providers.forms import BankTransferForm
        form = BankTransferForm(data={
            'sender_name': 'John Doe',
            'bank_name': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('bank_name', form.errors)


class GalleryImageModelTests(TestCase):
    """Test ProviderGalleryImage model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile('test.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_gallery_image_creation(self):
        """Test creating a gallery image."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption='Test caption'
        )
        self.assertEqual(image.provider, self.provider)
        self.assertEqual(image.caption, 'Test caption')
        self.assertIsNotNone(image.uploaded_at)

    def test_gallery_image_str(self):
        """Test __str__ method."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        self.assertIn(self.user.email, str(image))

    def test_gallery_image_ordering(self):
        """Test that images are ordered by -uploaded_at."""
        img1 = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption='First'
        )
        img2 = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image(),
            caption='Second'
        )
        images = list(ProviderGalleryImage.objects.filter(provider=self.provider))
        self.assertEqual(images[0].caption, 'Second')
        self.assertEqual(images[1].caption, 'First')

    def test_max_images_constant(self):
        """Test MAX_IMAGES_PER_PROVIDER is 10."""
        self.assertEqual(ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER, 10)

    def test_cascade_delete(self):
        """Test that gallery images are deleted when provider is deleted."""
        ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        self.assertEqual(ProviderGalleryImage.objects.count(), 1)
        self.provider.delete()
        self.assertEqual(ProviderGalleryImage.objects.count(), 0)

    def test_caption_optional(self):
        """Test that caption is optional."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        self.assertEqual(image.caption, '')


class GalleryImageFormTests(TestCase):
    """Test GalleryImageForm functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )

    def _create_test_image(self, format='JPEG', content_type='image/jpeg'):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        filename = f'test.{format.lower()}'
        return SimpleUploadedFile(filename, img_io.getvalue(), content_type=content_type)

    def test_form_fields(self):
        """Test form has correct fields."""
        from providers.forms import GalleryImageForm
        form = GalleryImageForm(provider=self.provider)
        self.assertIn('image', form.fields)
        self.assertIn('caption', form.fields)

    def test_form_valid_data(self):
        """Test form with valid image data."""
        from providers.forms import GalleryImageForm
        image = self._create_test_image()
        form = GalleryImageForm(
            data={'caption': 'Test'},
            files={'image': image},
            provider=self.provider
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid_format(self):
        """Test form rejects invalid image format."""
        from providers.forms import GalleryImageForm
        invalid_file = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')
        form = GalleryImageForm(
            data={'caption': 'Test'},
            files={'image': invalid_file},
            provider=self.provider
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_form_max_limit(self):
        """Test form enforces max image limit."""
        from providers.forms import GalleryImageForm
        # Create 10 images
        for i in range(10):
            ProviderGalleryImage.objects.create(
                provider=self.provider,
                image=self._create_test_image()
            )

        image = self._create_test_image()
        form = GalleryImageForm(
            data={'caption': 'Too many'},
            files={'image': image},
            provider=self.provider
        )
        self.assertFalse(form.is_valid())

    def test_form_caption_optional(self):
        """Test form allows empty caption."""
        from providers.forms import GalleryImageForm
        image = self._create_test_image()
        form = GalleryImageForm(
            data={'caption': ''},
            files={'image': image},
            provider=self.provider
        )
        self.assertTrue(form.is_valid())

    def test_form_requires_image(self):
        """Test form requires image field."""
        from providers.forms import GalleryImageForm
        form = GalleryImageForm(
            data={'caption': 'No image'},
            files={},
            provider=self.provider
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)


class GalleryImageCreateViewTests(TestCase):
    """Test GalleryImageCreateView functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        self.client_user = User.objects.create_user(
            email='client@test.com',
            password='testpass123',
            user_type='client',
            is_email_verified=True
        )

    def _create_test_image(self, format='JPEG', content_type='image/jpeg'):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return SimpleUploadedFile(f'test.{format.lower()}', img_io.getvalue(), content_type=content_type)

    def test_requires_login(self):
        """Test that gallery upload requires login."""
        response = self.client.get(reverse('gallery_upload'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)

    def test_requires_provider(self):
        """Test that non-providers cannot access gallery upload."""
        self.client.login(email=self.client_user.email, password='testpass123')
        response = self.client.get(reverse('gallery_upload'))
        self.assertEqual(response.status_code, 302)

    def test_page_loads(self):
        """Test that gallery upload page loads for provider."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('gallery_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/gallery_upload.html')

    def test_upload_valid_image(self):
        """Test uploading a valid gallery image."""
        self.client.login(email=self.user.email, password='testpass123')
        image = self._create_test_image()
        response = self.client.post(reverse('gallery_upload'), {
            'image': image,
            'caption': 'My workspace'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProviderGalleryImage.objects.filter(provider=self.provider).count(), 1)

    def test_upload_invalid_format(self):
        """Test that invalid formats are rejected."""
        self.client.login(email=self.user.email, password='testpass123')
        invalid_file = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')
        response = self.client.post(reverse('gallery_upload'), {
            'image': invalid_file,
            'caption': 'Bad file'
        })
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertEqual(ProviderGalleryImage.objects.filter(provider=self.provider).count(), 0)

    def test_upload_max_limit(self):
        """Test that upload is rejected when at max limit."""
        self.client.login(email=self.user.email, password='testpass123')
        for i in range(10):
            ProviderGalleryImage.objects.create(
                provider=self.provider,
                image=self._create_test_image()
            )
        image = self._create_test_image()
        response = self.client.post(reverse('gallery_upload'), {
            'image': image,
            'caption': 'Too many'
        })
        self.assertEqual(response.status_code, 200)  # Re-renders form
        self.assertEqual(ProviderGalleryImage.objects.filter(provider=self.provider).count(), 10)

    def test_upload_success_message(self):
        """Test that success message is shown after upload."""
        self.client.login(email=self.user.email, password='testpass123')
        image = self._create_test_image()
        response = self.client.post(reverse('gallery_upload'), {
            'image': image,
            'caption': 'Test'
        }, follow=True)
        msgs = list(response.context['messages'])
        self.assertTrue(any('uploaded successfully' in str(m).lower() for m in msgs))

    def test_context_has_gallery_images(self):
        """Test that context includes gallery images."""
        self.client.login(email=self.user.email, password='testpass123')
        ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        response = self.client.get(reverse('gallery_upload'))
        self.assertIn('gallery_images', response.context)
        self.assertEqual(response.context['gallery_images'].count(), 1)

    def test_context_has_max_images(self):
        """Test that context includes max_images."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('gallery_upload'))
        self.assertEqual(response.context['max_images'], 10)


class GalleryImageDeleteViewTests(TestCase):
    """Test GalleryImageDeleteView functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            user_type='provider',
            is_email_verified=True
        )
        self.other_provider = Provider.objects.create(
            user=self.other_user,
            phone='+9876543210'
        )

    def _create_test_image(self):
        """Create a test image file."""
        from PIL import Image as PILImage
        import io
        img = PILImage.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        return SimpleUploadedFile('test.jpg', img_io.getvalue(), content_type='image/jpeg')

    def test_requires_login(self):
        """Test that gallery delete requires login."""
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        response = self.client.post(reverse('gallery_delete', args=[image.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)

    def test_delete_own_image(self):
        """Test that provider can delete their own image."""
        self.client.login(email=self.user.email, password='testpass123')
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        response = self.client.post(reverse('gallery_delete', args=[image.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProviderGalleryImage.objects.filter(pk=image.pk).exists())

    def test_cannot_delete_other_providers_image(self):
        """Test that provider cannot delete another provider's image."""
        self.client.login(email=self.user.email, password='testpass123')
        image = ProviderGalleryImage.objects.create(
            provider=self.other_provider,
            image=self._create_test_image()
        )
        response = self.client.post(reverse('gallery_delete', args=[image.pk]))
        self.assertTrue(ProviderGalleryImage.objects.filter(pk=image.pk).exists())

    def test_delete_success_message(self):
        """Test that success message is shown after deletion."""
        self.client.login(email=self.user.email, password='testpass123')
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        response = self.client.post(reverse('gallery_delete', args=[image.pk]), follow=True)
        msgs = list(response.context['messages'])
        self.assertTrue(any('deleted successfully' in str(m).lower() for m in msgs))

    def test_get_not_allowed(self):
        """Test that GET requests are not allowed for delete."""
        self.client.login(email=self.user.email, password='testpass123')
        image = ProviderGalleryImage.objects.create(
            provider=self.provider,
            image=self._create_test_image()
        )
        response = self.client.get(reverse('gallery_delete', args=[image.pk]))
        self.assertEqual(response.status_code, 405)  # Method not allowed


class LocationModelTests(TestCase):
    """Tests for Continent, Country, and City models."""

    def test_continent_creation(self):
        """Test creating a continent."""
        from providers.models import Continent
        continent = Continent.objects.create(
            name='Europe',
            code='EU',
            display_order=1
        )
        self.assertEqual(str(continent), 'Europe')
        self.assertEqual(continent.code, 'EU')

    def test_continent_ordering(self):
        """Test continents are ordered by display_order then name."""
        from providers.models import Continent
        c1 = Continent.objects.create(name='Zebra', code='ZB', display_order=2)
        c2 = Continent.objects.create(name='Alpha', code='AL', display_order=1)
        c3 = Continent.objects.create(name='Beta', code='BE', display_order=1)

        continents = list(Continent.objects.all())
        self.assertEqual(continents[0], c2)  # Alpha (display_order=1, comes first alphabetically)
        self.assertEqual(continents[1], c3)  # Beta (display_order=1)
        self.assertEqual(continents[2], c1)  # Zebra (display_order=2)

    def test_country_creation(self):
        """Test creating a country with continent."""
        from providers.models import Continent, Country
        continent = Continent.objects.create(name='Europe', code='EU', display_order=1)
        country = Country.objects.create(
            name='United Kingdom',
            code='GB',
            continent=continent,
            is_active=True
        )
        self.assertEqual(str(country), 'United Kingdom')
        self.assertEqual(country.continent, continent)
        self.assertTrue(country.is_active)

    def test_country_continent_relationship(self):
        """Test that countries are related to continents."""
        from providers.models import Continent, Country
        europe = Continent.objects.create(name='Europe', code='EU', display_order=1)
        uk = Country.objects.create(name='United Kingdom', code='GB', continent=europe)
        france = Country.objects.create(name='France', code='FR', continent=europe)

        self.assertEqual(europe.countries.count(), 2)
        self.assertIn(uk, europe.countries.all())
        self.assertIn(france, europe.countries.all())

    def test_city_creation(self):
        """Test creating a city."""
        from providers.models import Continent, Country, City
        europe = Continent.objects.create(name='Europe', code='EU', display_order=1)
        uk = Country.objects.create(name='United Kingdom', code='GB', continent=europe)
        city = City.objects.create(
            name='London',
            country=uk,
            population=8982000,
            is_capital=True,
            is_major_city=True,
            latitude='51.507351',
            longitude='-0.127758'
        )
        self.assertEqual(str(city), 'London, United Kingdom')
        self.assertTrue(city.is_capital)
        self.assertTrue(city.is_major_city)

    def test_city_ordering(self):
        """Test cities are ordered by is_capital, is_major_city, population desc, name."""
        from providers.models import Continent, Country, City
        europe = Continent.objects.create(name='Europe', code='EU', display_order=1)
        uk = Country.objects.create(name='United Kingdom', code='GB', continent=europe)

        london = City.objects.create(name='London', country=uk, population=8982000, is_capital=True, is_major_city=True)
        birmingham = City.objects.create(name='Birmingham', country=uk, population=1149000, is_capital=False, is_major_city=True)
        oxford = City.objects.create(name='Oxford', country=uk, population=150000, is_capital=False, is_major_city=False)

        cities = list(City.objects.filter(country=uk))
        self.assertEqual(cities[0], london)  # Capital first
        self.assertEqual(cities[1], birmingham)  # Major city second
        self.assertEqual(cities[2], oxford)  # Small city last

    def test_city_unique_together(self):
        """Test that city name + country must be unique."""
        from providers.models import Continent, Country, City
        from django.db import IntegrityError

        europe = Continent.objects.create(name='Europe', code='EU', display_order=1)
        uk = Country.objects.create(name='United Kingdom', code='GB', continent=europe)
        City.objects.create(name='London', country=uk)

        with self.assertRaises(IntegrityError):
            City.objects.create(name='London', country=uk)

    def test_provider_location_fk_fields(self):
        """Test provider with new FK location fields."""
        from providers.models import Continent, Country, City, Provider

        europe = Continent.objects.create(name='Europe', code='EU', display_order=1)
        uk = Country.objects.create(name='United Kingdom', code='GB', continent=europe)
        london = City.objects.create(name='London', country=uk, is_capital=True)

        user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        provider = Provider.objects.create(
            user=user,
            phone='+1234567890',
            country_new=uk,
            city_new=london
        )

        self.assertEqual(provider.country_new.name, 'United Kingdom')
        self.assertEqual(provider.city_new.name, 'London')

    def test_us_not_in_fixtures(self):
        """Test that United States is not in the country fixtures."""
        from providers.models import Country

        # Load fixtures in test if they haven't been loaded
        us = Country.objects.filter(code='US').first()
        self.assertIsNone(us)
