from django.test import TestCase
from users.forms import SignupForm
from users.models import User


class SignupFormTests(TestCase):
    """Test signup form validation."""
    
    def test_signup_form_valid(self):
        """Test form with valid data."""
        form = SignupForm(data={
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
            'accept_terms': True,
        })
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_signup_form_password_mismatch(self):
        """Test form with mismatched passwords."""
        form = SignupForm(data={
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'different123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('Passwords do not match', str(form.errors))
    
    def test_signup_form_short_password(self):
        """Test form with password < 8 characters."""
        form = SignupForm(data={
            'email': 'new@example.com',
            'password': 'short',
            'password_confirm': 'short',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('at least 8 characters', str(form.errors).lower())
    
    def test_signup_form_invalid_email(self):
        """Test form with invalid email."""
        form = SignupForm(data={
            'email': 'not-an-email',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
    
    def test_signup_form_duplicate_email(self):
        """Test form with existing email."""
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        
        form = SignupForm(data={
            'email': 'existing@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('already exists', str(form.errors))
    
    def test_signup_form_duplicate_email_case_insensitive(self):
        """Test email uniqueness is case-insensitive."""
        User.objects.create_user(
            email='Test@Example.com',
            password='testpass123'
        )
        
        form = SignupForm(data={
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('already exists', str(form.errors))
    
    def test_signup_form_missing_email(self):
        """Test form without email."""
        form = SignupForm(data={
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_signup_form_missing_password(self):
        """Test form without password."""
        form = SignupForm(data={
            'email': 'new@example.com',
            'password_confirm': 'testpass123',
            'user_type': 'provider',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
