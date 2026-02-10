from django.test import TestCase
from django.urls import reverse

from users.forms import SignupForm


class LegalPageTests(TestCase):
    """Test that legal pages load correctly."""

    def test_terms_page_loads(self):
        response = self.client.get(reverse("terms"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Terms of Service")

    def test_privacy_page_loads(self):
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacy Policy")

    def test_payment_policy_page_loads(self):
        response = self.client.get(reverse("payment_policy"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Policy")

    def test_terms_contains_key_sections(self):
        response = self.client.get(reverse("terms"))
        content = response.content.decode()
        self.assertIn("Acceptance of Terms", content)
        self.assertIn("Limitation of Liability", content)
        self.assertIn("Termination", content)

    def test_privacy_contains_gdpr_section(self):
        response = self.client.get(reverse("privacy"))
        content = response.content.decode()
        self.assertIn("GDPR", content)
        self.assertIn("Data Security", content)

    def test_payment_policy_contains_refund_section(self):
        response = self.client.get(reverse("payment_policy"))
        content = response.content.decode()
        self.assertIn("Refund Policy", content)
        self.assertIn("Subscription", content)


class FooterLegalLinksTests(TestCase):
    """Test that legal links appear in the site footer."""

    def test_footer_has_terms_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("terms"))
        self.assertContains(response, "Terms of Service")

    def test_footer_has_privacy_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("privacy"))
        self.assertContains(response, "Privacy Policy")

    def test_footer_has_payment_policy_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("payment_policy"))
        self.assertContains(response, "Payment Policy")


class SignupTermsAcceptanceTests(TestCase):
    """Test that signup requires terms acceptance."""

    def test_signup_form_requires_accept_terms(self):
        form = SignupForm(
            data={
                "email": "test@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("accept_terms", form.errors)

    def test_signup_form_valid_with_accept_terms(self):
        form = SignupForm(
            data={
                "email": "test@example.com",
                "password": "testpass123",
                "password_confirm": "testpass123",
                "user_type": "provider",
                "accept_terms": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_signup_page_has_terms_checkbox(self):
        response = self.client.get(reverse("signup"))
        content = response.content.decode()
        self.assertIn("accept_terms", content)
        self.assertIn("Terms of Service", content)
        self.assertIn("Privacy Policy", content)
