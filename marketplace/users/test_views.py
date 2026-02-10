from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class SignupViewTests(TestCase):
    """Test signup view."""

    def setUp(self):
        """Create test client."""
        self.client = Client()
        self.signup_url = reverse("signup")

    def test_signup_view_get_loads(self):
        """Test signup page loads."""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertTemplateUsed(response, "users/signup.html")

    def test_signup_view_creates_user(self):
        """Test signup creates user."""
        self.client.post(
            self.signup_url,
            {
                "email": "new@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            },
        )

        # User should be created
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.user_type, "provider")
        self.assertFalse(user.is_email_verified)

    def test_signup_view_redirects_on_success(self):
        """Test signup redirects after success."""
        response = self.client.post(
            self.signup_url,
            {
                "email": "new@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("check-email", response.url)

    def test_signup_view_duplicate_email_rejected(self):
        """Test duplicate email is rejected."""
        User.objects.create_user(email="existing@example.com", password="testpass123")

        response = self.client.post(
            self.signup_url,
            {
                "email": "existing@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        # Check form has errors
        self.assertTrue(response.context["form"].has_error("email"))
        self.assertIn("already exists", str(response.context["form"].errors))

    def test_signup_view_password_mismatch_rejected(self):
        """Test password mismatch is rejected."""
        response = self.client.post(
            self.signup_url,
            {
                "email": "new@example.com",
                "password": "testpass123",
                "password_confirm": "different123",
                "user_type": "provider",
                "accept_terms": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        # Check form has non-field errors
        self.assertTrue(len(response.context["form"].non_field_errors()) > 0)
        self.assertIn("Passwords do not match", str(response.context["form"].errors))

    def test_signup_view_short_password_rejected(self):
        """Test short password is rejected."""
        response = self.client.post(
            self.signup_url,
            {
                "email": "new@example.com",
                "password": "short",
                "password_confirm": "short",
                "user_type": "provider",
                "accept_terms": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        # Should have form error
        self.assertTrue(response.context["form"].has_error("password"))


class CheckEmailViewTests(TestCase):
    """Test check email view."""

    def setUp(self):
        """Create test client."""
        self.client = Client()
        self.check_email_url = reverse("check_email")

    def test_check_email_view_loads(self):
        """Test check email page loads."""
        response = self.client.get(self.check_email_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/check_email.html")

    def test_check_email_view_content(self):
        """Test check email page has expected content."""
        response = self.client.get(self.check_email_url)
        content = response.content.decode()

        self.assertIn("Check Your Email", content)
        self.assertIn("verification", content.lower())
