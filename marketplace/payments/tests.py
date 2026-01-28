from django.test import TestCase
from django.utils import timezone
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
