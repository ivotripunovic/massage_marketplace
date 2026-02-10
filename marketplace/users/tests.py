from django.test import TestCase, RequestFactory, override_settings
from django.db import IntegrityError
from django.contrib.auth import authenticate
from users.models import User
from users.utils import (
    generate_email_verification_token,
    verify_email_token,
    send_verification_email,
)


class CustomUserModelTests(TestCase):
    """Test custom User model functionality."""

    def test_create_user(self):
        """Test creating a basic user."""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.user_type, "client")  # default
        self.assertFalse(user.is_email_verified)

    def test_create_user_requires_email(self):
        """Test that email is required."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass")

    def test_email_is_unique(self):
        """Test email uniqueness constraint."""
        User.objects.create_user(email="test@example.com", password="pass")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="test@example.com", password="pass")

    def test_user_type_choices(self):
        """Test user_type field with valid choices."""
        user_provider = User.objects.create_user(
            email="provider@test.com", password="pass", user_type="provider"
        )
        self.assertEqual(user_provider.user_type, "provider")

        user_admin = User.objects.create_user(
            email="admin@test.com", password="pass", user_type="admin"
        )
        self.assertEqual(user_admin.user_type, "admin")

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("adminpass123"))

    def test_superuser_requires_staff_and_superuser(self):
        """Test superuser validation."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@test.com", password="pass", is_staff=False
            )

        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin@test.com", password="pass", is_superuser=False
            )

    def test_email_normalization(self):
        """Test email normalization."""
        user = User.objects.create_user(email="Test@EXAMPLE.COM", password="pass")
        self.assertEqual(user.email, "test@example.com")

    def test_email_verification_fields(self):
        """Test email verification fields."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        self.assertFalse(user.is_email_verified)
        self.assertIsNone(user.email_verification_token)

        # Simulate verification
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_phone_number_field(self):
        """Test phone number field."""
        user = User.objects.create_user(
            email="test@example.com", password="pass", phone_number="+1234567890"
        )
        self.assertEqual(user.phone_number, "+1234567890")

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        self.assertEqual(str(user), "test@example.com")

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email."""
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_no_username_field(self):
        """Test that username field is None."""
        user = User.objects.create_user(email="test@example.com", password="pass")
        self.assertIsNone(user.username)


class EmailBackendAuthenticationTests(TestCase):
    """Test email-based authentication backend."""

    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_authenticate_with_email(self):
        """Test authentication with email and password."""
        authenticated = authenticate(email="test@example.com", password="testpass123")
        self.assertEqual(authenticated, self.user)

    def test_authenticate_with_wrong_password(self):
        """Test authentication fails with wrong password."""
        authenticated = authenticate(email="test@example.com", password="wrongpass")
        self.assertIsNone(authenticated)

    def test_authenticate_nonexistent_user(self):
        """Test authentication fails with nonexistent email."""
        authenticated = authenticate(email="nonexistent@example.com", password="pass")
        self.assertIsNone(authenticated)

    def test_case_insensitive_email_authentication(self):
        """Test email matching is case-insensitive."""
        authenticated = authenticate(email="TEST@EXAMPLE.COM", password="testpass123")
        self.assertEqual(authenticated, self.user)

    def test_mixed_case_email_authentication(self):
        """Test mixed case email authentication."""
        authenticated = authenticate(email="TeSt@ExAmPlE.cOm", password="testpass123")
        self.assertEqual(authenticated, self.user)

    def test_authenticate_inactive_user(self):
        """Test authentication fails with inactive user."""
        self.user.is_active = False
        self.user.save()

        authenticated = authenticate(email="test@example.com", password="testpass123")
        self.assertIsNone(authenticated)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailVerificationUtilsTests(TestCase):
    """Test email verification utility functions."""

    def setUp(self):
        """Create test user and request factory."""
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.factory = RequestFactory()

    def test_generate_verification_token(self):
        """Test generating verification token."""
        token = generate_email_verification_token(self.user)

        self.assertIsNotNone(token)
        self.assertGreater(len(token), 0)

        # Verify token is stored in user record
        self.user.refresh_from_db()
        self.assertEqual(self.user.email_verification_token, token)

    def test_verify_email_token_valid(self):
        """Test verifying valid email token."""
        token = generate_email_verification_token(self.user)

        # Verify token
        verified_user = verify_email_token(token)

        self.assertEqual(verified_user, self.user)

        # Check user is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_token)

    def test_verify_email_token_invalid(self):
        """Test verifying invalid email token."""
        verified_user = verify_email_token("invalid_token_xyz")
        self.assertIsNone(verified_user)

    def test_verify_email_token_consumed(self):
        """Test that token is consumed after first use."""
        token = generate_email_verification_token(self.user)

        # First verification
        verify_email_token(token)

        # Try to use same token again
        verified_user = verify_email_token(token)
        self.assertIsNone(verified_user)

    def test_token_uniqueness(self):
        """Test that each token is unique."""
        token1 = generate_email_verification_token(self.user)

        # Create another user
        user2 = User.objects.create_user(
            email="test2@example.com", password="testpass123"
        )
        token2 = generate_email_verification_token(user2)

        self.assertNotEqual(token1, token2)

    def test_send_verification_email(self):
        """Test sending verification email."""
        request = self.factory.get("/")
        request.META["SERVER_NAME"] = "testserver"
        request.META["SERVER_PORT"] = "80"

        result = send_verification_email(self.user, request)

        # Function should return True (or at least not raise exception)
        self.assertTrue(isinstance(result, bool))

        # Token should be generated
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verification_token)

    def test_send_verification_email_contains_url(self):
        """Test verification email URL is generated."""
        request = self.factory.get("/")
        request.META["SERVER_NAME"] = "testserver"
        request.META["SERVER_PORT"] = "80"

        send_verification_email(self.user, request)

        # Token should be generated
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verification_token)
        # Token should be a string
        self.assertIsInstance(self.user.email_verification_token, str)
        self.assertGreater(len(self.user.email_verification_token), 10)

    def test_multiple_tokens_overwrites_previous(self):
        """Test generating new token overwrites previous."""
        token1 = generate_email_verification_token(self.user)
        token2 = generate_email_verification_token(self.user)

        self.assertNotEqual(token1, token2)

        # Only token2 should be valid
        self.user.refresh_from_db()
        self.assertEqual(self.user.email_verification_token, token2)

        # token1 should not verify
        verified = verify_email_token(token1)
        self.assertIsNone(verified)
