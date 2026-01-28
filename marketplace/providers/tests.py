from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import User
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
