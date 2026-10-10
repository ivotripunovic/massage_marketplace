from unittest.mock import patch

from django.test import TestCase, override_settings
from email_validator import EmailUndeliverableError

from users.forms import SignupForm
from users.models import User


class SignupFormTests(TestCase):
    """Test signup form validation."""

    def test_signup_form_valid(self):
        """Test form with valid data."""
        form = SignupForm(
            data={
                "email": "new@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_signup_form_password_mismatch(self):
        """Test form with mismatched passwords."""
        form = SignupForm(
            data={
                "email": "new@example.com",
                "password": "testpass123",
                "password_confirm": "different123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Passwords do not match", str(form.errors))

    def test_signup_form_short_password(self):
        """Test form with password < 8 characters."""
        form = SignupForm(
            data={
                "email": "new@example.com",
                "password": "short",
                "password_confirm": "short",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("at least 8 characters", str(form.errors).lower())

    def test_signup_form_invalid_email(self):
        """Test form with invalid email."""
        form = SignupForm(
            data={
                "email": "not-an-email",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())

    def test_signup_form_duplicate_email(self):
        """Test form with existing email."""
        User.objects.create_user(email="existing@example.com", password="testpass123")

        form = SignupForm(
            data={
                "email": "existing@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("already exists", str(form.errors))

    def test_signup_form_duplicate_email_case_insensitive(self):
        """Test email uniqueness is case-insensitive."""
        User.objects.create_user(email="Test@Example.com", password="testpass123")

        form = SignupForm(
            data={
                "email": "test@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("already exists", str(form.errors))

    def test_signup_form_missing_email(self):
        """Test form without email."""
        form = SignupForm(
            data={
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_missing_password(self):
        """Test form without password."""
        form = SignupForm(
            data={
                "email": "new@example.com",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)


class SignupEmailDeliverabilityTests(TestCase):
    """Test that signup rejects disposable and undeliverable email addresses."""

    def _form(self, email):
        return SignupForm(
            data={
                "email": email,
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            }
        )

    def test_disposable_domain_rejected(self):
        form = self._form("someone@mailinator.com")
        self.assertFalse(form.is_valid())
        self.assertIn("Disposable", form.errors["email"][0])

    def test_disposable_subdomain_rejected(self):
        form = self._form("someone@mx.mailinator.com")
        self.assertFalse(form.is_valid())
        self.assertIn("Disposable", form.errors["email"][0])

    @override_settings(EMAIL_CHECK_DELIVERABILITY=True)
    @patch("users.email_checks.validate_email")
    def test_undeliverable_domain_rejected(self, mock_validate):
        mock_validate.side_effect = EmailUndeliverableError("no MX record")
        form = self._form("someone@nonexistent-domain-xyz123.com")
        self.assertFalse(form.is_valid())
        self.assertIn("cannot receive mail", form.errors["email"][0])
        self.assertTrue(mock_validate.call_args.kwargs["check_deliverability"])

    @override_settings(EMAIL_CHECK_DELIVERABILITY=True)
    @patch("users.email_checks.validate_email")
    def test_deliverable_domain_accepted(self, mock_validate):
        form = self._form("Someone@Gmail.com")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "someone@gmail.com")

    def test_deliverability_check_disabled_in_tests(self):
        form = self._form("someone@nonexistent-domain-xyz123.com")
        self.assertTrue(form.is_valid(), form.errors)
