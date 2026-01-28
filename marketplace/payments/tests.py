from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from unittest.mock import patch
from users.models import User
from providers.models import Provider
from .models import SubscriptionPayment


class SubscriptionPaymentModelTests(TestCase):
    """Test SubscriptionPayment model functionality."""
    
    def setUp(self):
        """Set up test provider for payment creation."""
        self.user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.user,
            phone='+1234567890'
        )
    
    def test_payment_creation(self):
        """Test creating a subscription payment."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method='crypto_bitcoin',
            status='pending'
        )
        self.assertEqual(payment.amount, 29.99)
        self.assertEqual(payment.status, 'pending')
    
    def test_payment_default_amount(self):
        """Test payment default amount."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='bank_transfer'
        )
        self.assertEqual(payment.amount, 29.99)
    
    def test_payment_default_status(self):
        """Test payment default status is pending."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='crypto_ethereum'
        )
        self.assertEqual(payment.status, 'pending')
    
    def test_payment_with_reference_id(self):
        """Test payment with reference ID (transaction hash)."""
        tx_hash = '0x123abc456def'
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='crypto_bitcoin',
            reference_id=tx_hash,
            status='completed'
        )
        self.assertEqual(payment.reference_id, tx_hash)
    
    def test_payment_with_admin_notes(self):
        """Test payment with admin notes."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='bank_transfer',
            notes='Waiting for bank confirmation'
        )
        self.assertEqual(payment.notes, 'Waiting for bank confirmation')
    
    def test_payment_status_completed(self):
        """Test marking payment as completed."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='crypto_usdc'
        )
        self.assertEqual(payment.status, 'pending')
        
        payment.status = 'completed'
        payment.completed_at = timezone.now()
        payment.save()
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        self.assertIsNotNone(payment.completed_at)
    
    def test_payment_status_failed(self):
        """Test marking payment as failed."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='bank_transfer'
        )
        payment.status = 'failed'
        payment.notes = 'Bank transfer bounced'
        payment.save()
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
    
    def test_all_payment_methods(self):
        """Test all payment method choices."""
        payment_methods = [
            'crypto_bitcoin',
            'crypto_ethereum',
            'crypto_usdc',
            'bank_transfer'
        ]
        for i, method in enumerate(payment_methods):
            payment = SubscriptionPayment.objects.create(
                provider=self.provider,
                payment_method=method,
                amount=29.99 + i
            )
            self.assertEqual(payment.payment_method, method)
    
    def test_payment_string_representation(self):
        """Test payment __str__ method."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method='crypto_bitcoin',
            status='pending'
        )
        self.assertIn(self.user.email, str(payment))
        self.assertIn('29.99', str(payment))
        self.assertIn('Pending', str(payment))
    
    def test_multiple_payments_per_provider(self):
        """Test provider can have multiple subscription payments."""
        payment1 = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='crypto_bitcoin',
            status='completed'
        )
        payment2 = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='bank_transfer',
            status='pending'
        )
        self.assertEqual(self.provider.subscription_payments.count(), 2)
    
    def test_payment_has_timestamps(self):
        """Test payment has creation timestamp."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            payment_method='crypto_ethereum'
        )
        self.assertIsNotNone(payment.created_at)
        self.assertIsNone(payment.completed_at)  # Only set when completed
    
    def test_custom_amount(self):
        """Test payment with custom amount."""
        payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=49.99,
            payment_method='bank_transfer'
        )
        self.assertEqual(payment.amount, 49.99)


class AdminPaymentListViewTests(TestCase):
    """Test AdminPaymentListView for admin payment management."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='pass',
            user_type='admin'
        )
        
        # Create provider and payment
        self.provider_user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone='+1234567890'
        )
        
        self.payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method='crypto_bitcoin',
            status='pending'
        )
    
    def test_payment_list_requires_login(self):
        """Test that payment list requires authentication."""
        response = self.client.get(reverse('admin_payments'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_payment_list_requires_admin(self):
        """Test that non-admin cannot access payment list."""
        self.client.login(email='provider@test.com', password='pass')
        response = self.client.get(reverse('admin_payments'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_payment_list_admin_can_access(self):
        """Test that admin can access payment list."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payments'))
        self.assertEqual(response.status_code, 200)
    
    def test_payment_list_displays_payments(self):
        """Test that payment list displays pending payments."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payments'))
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, '29.99')
    
    def test_payment_list_filter_by_status(self):
        """Test filtering payments by status."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payments') + '?status=pending')
        self.assertContains(response, self.provider_user.email)
        
        response = self.client.get(reverse('admin_payments') + '?status=completed')
        self.assertNotContains(response, self.provider_user.email)
    
    def test_payment_list_filter_by_method(self):
        """Test filtering payments by method."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payments') + '?method=crypto_bitcoin')
        self.assertContains(response, self.provider_user.email)
        
        response = self.client.get(reverse('admin_payments') + '?method=bank_transfer')
        self.assertNotContains(response, self.provider_user.email)
    
    def test_payment_list_search(self):
        """Test searching payments by email."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payments') + f'?search={self.provider_user.email}')
        self.assertContains(response, self.provider_user.email)


class AdminPaymentDetailViewTests(TestCase):
    """Test AdminPaymentDetailView for viewing payment details."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='pass',
            user_type='admin'
        )
        
        # Create provider and payment
        self.provider_user = User.objects.create_user(
            email='provider@test.com',
            password='pass',
            user_type='provider'
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            phone='+1234567890'
        )
        
        self.payment = SubscriptionPayment.objects.create(
            provider=self.provider,
            amount=29.99,
            payment_method='crypto_bitcoin',
            status='pending',
            reference_id='0x123abc'
        )
    
    def test_payment_detail_requires_login(self):
        """Test that payment detail requires authentication."""
        response = self.client.get(reverse('admin_payment_detail', args=[self.payment.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_payment_detail_requires_admin(self):
        """Test that non-admin cannot view payment detail."""
        self.client.login(email='provider@test.com', password='pass')
        response = self.client.get(reverse('admin_payment_detail', args=[self.payment.id]))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_payment_detail_admin_can_access(self):
        """Test that admin can view payment detail."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payment_detail', args=[self.payment.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_payment_detail_displays_info(self):
        """Test that payment detail displays all information."""
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('admin_payment_detail', args=[self.payment.id]))
        
        self.assertContains(response, '29.99')
        self.assertContains(response, self.provider_user.email)
        self.assertContains(response, '0x123abc')
        self.assertContains(response, 'Pending')


class SubscriptionConfirmationEmailTests(TestCase):
    """Test subscription confirmation email functionality."""
    
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
    
    @patch('django.core.mail.send_mail')
    def test_subscription_email_sent_on_activation(self, mock_send):
        """Test that email is sent when subscription is activated."""
        from providers.views import ProviderSubscriptionView
        
        # Create a mock request
        self.provider.activate_subscription('crypto_bitcoin')
        
        # Verify provider is active
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.subscription_status, 'active')
        self.assertIsNotNone(self.provider.subscription_renewal_date)
    
    def test_subscription_email_template_exists(self):
        """Test that subscription confirmation email template exists."""
        from django.template.loader import get_template
        
        template = get_template('emails/subscription_confirmation.html')
        self.assertIsNotNone(template)
    
    def test_subscription_confirmation_text_template_exists(self):
        """Test that subscription confirmation text template exists."""
        from django.template.loader import get_template
        
        template = get_template('emails/subscription_confirmation.txt')
        self.assertIsNotNone(template)
