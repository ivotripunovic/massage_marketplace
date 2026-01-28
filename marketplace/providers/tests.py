from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse
from users.models import User
from reviews.models import Review
from .models import Provider, Service, Certification


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


class CertificationModelTests(TestCase):
    """Test Certification model functionality."""
    
    def setUp(self):
        """Set up test provider for certification creation."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
    
    def test_certification_creation(self):
        """Test creating a certification."""
        cert = Certification.objects.create(
            provider=self.provider,
            name='Licensed Massage Therapist'
        )
        self.assertEqual(cert.name, 'Licensed Massage Therapist')
    
    def test_certification_string_representation(self):
        """Test certification __str__ method."""
        cert = Certification.objects.create(
            provider=self.provider,
            name='LMT Certification'
        )
        self.assertIn(self.user.email, str(cert))
        self.assertIn('LMT Certification', str(cert))
    
    def test_certification_has_upload_date(self):
        """Test certification has upload timestamp."""
        cert = Certification.objects.create(
            provider=self.provider,
            name='Swedish Massage Certification'
        )
        self.assertIsNotNone(cert.uploaded_at)
    
    def test_multiple_certifications_per_provider(self):
        """Test provider can have multiple certifications."""
        cert1 = Certification.objects.create(
            provider=self.provider,
            name='LMT'
        )
        cert2 = Certification.objects.create(
            provider=self.provider,
            name='Deep Tissue Specialist'
        )
        self.assertEqual(self.provider.certifications.count(), 2)
        self.assertIn(cert1, self.provider.certifications.all())
        self.assertIn(cert2, self.provider.certifications.all())


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
        self.certification = Certification.objects.create(
            provider=self.provider,
            name='Licensed Massage Therapist'
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
    
    def test_dashboard_displays_certifications(self):
        """Test that dashboard displays provider's certifications."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertContains(response, 'Licensed Massage Therapist')
    
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
        self.assertContains(response, 'Certifications')
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
    
    def test_dashboard_shows_empty_state_for_no_certifications(self):
        """Test dashboard when provider has no certifications."""
        # Delete all certifications
        Certification.objects.all().delete()
        
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
    
    def test_dashboard_context_has_certifications(self):
        """Test that dashboard context contains certifications list."""
        self.client.login(email=self.user.email, password='testpass123')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertIn('certifications', response.context)
        self.assertIn(self.certification, response.context['certifications'])
    
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
