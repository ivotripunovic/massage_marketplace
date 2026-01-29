from django.conf import settings
from django.test import TestCase, override_settings

from marketplace.middleware import RateLimitMiddleware
from users.models import User


class SecurityHeadersTests(TestCase):
    """Verify security-related response headers."""

    def test_x_frame_options_deny(self):
        """Pages should include X-Frame-Options: DENY."""
        response = self.client.get('/auth/login/')
        self.assertEqual(response.get('X-Frame-Options'), 'DENY')

    def test_csrf_middleware_active(self):
        """CSRF middleware must be in the middleware stack."""
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE,
        )

    def test_security_middleware_active(self):
        """SecurityMiddleware must be first in the middleware stack."""
        self.assertEqual(
            settings.MIDDLEWARE[0],
            'django.middleware.security.SecurityMiddleware',
        )

    def test_clickjacking_middleware_active(self):
        """X-Frame-Options middleware must be active."""
        self.assertIn(
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            settings.MIDDLEWARE,
        )

    def test_session_cookie_httponly(self):
        """Session cookie must be HTTP-only."""
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_csrf_cookie_httponly(self):
        """CSRF cookie must be HTTP-only."""
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)

    def test_session_cookie_samesite(self):
        """Session cookie must have SameSite=Lax."""
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')

    def test_csrf_cookie_samesite(self):
        """CSRF cookie must have SameSite=Lax."""
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')


class ProductionSecuritySettingsTests(TestCase):
    """Verify that production-only security settings exist in the settings module."""

    def test_production_settings_block_exists(self):
        """The settings module must define production security logic."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        self.assertIn('SECURE_SSL_REDIRECT', source)
        self.assertIn('SECURE_HSTS_SECONDS', source)
        self.assertIn('SESSION_COOKIE_SECURE', source)
        self.assertIn('CSRF_COOKIE_SECURE', source)
        self.assertIn('SECURE_HSTS_INCLUDE_SUBDOMAINS', source)
        self.assertIn('SECURE_HSTS_PRELOAD', source)
        self.assertIn('SECURE_CONTENT_TYPE_NOSNIFF', source)


class CSRFProtectionTests(TestCase):
    """Verify CSRF protection on all POST endpoints."""

    def test_login_post_without_csrf_fails(self):
        """POST to login without CSRF token must be rejected."""
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth/login/', {
            'email': 'test@example.com',
            'password': 'pass',
        })
        self.assertEqual(response.status_code, 403)

    def test_signup_post_without_csrf_fails(self):
        """POST to signup without CSRF token must be rejected."""
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth/signup/', {
            'email': 'new@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
        })
        self.assertEqual(response.status_code, 403)

    def test_password_reset_post_without_csrf_fails(self):
        """POST to password-reset without CSRF token must be rejected."""
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth/password-reset/', {
            'email': 'test@example.com',
        })
        self.assertEqual(response.status_code, 403)


class PasswordHashingTests(TestCase):
    """Verify password hashing configuration."""

    def test_password_is_hashed(self):
        """Stored password must not be plaintext."""
        user = User.objects.create_user(
            email='hash@example.com',
            password='secretpass123'
        )
        self.assertNotEqual(user.password, 'secretpass123')
        self.assertTrue(user.password.startswith(('pbkdf2_', 'md5$')))

    def test_password_validators_configured(self):
        """Password validators must be set in production settings."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        self.assertIn('MinimumLengthValidator', source)
        self.assertIn('CommonPasswordValidator', source)
        self.assertIn('NumericPasswordValidator', source)
        self.assertIn('UserAttributeSimilarityValidator', source)


class RateLimitTests(TestCase):
    """Test the rate-limiting middleware."""

    def setUp(self):
        RateLimitMiddleware.reset()

    def tearDown(self):
        RateLimitMiddleware.reset()

    @override_settings(RATE_LIMIT_RULES={'login': (3, 60)})
    def test_login_rate_limited_after_max_attempts(self):
        """POST to /auth/login/ should be rejected after exceeding limit."""
        for _ in range(3):
            self.client.post('/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrong',
            })

        response = self.client.post('/auth/login/', {
            'email': 'test@example.com',
            'password': 'wrong',
        })
        self.assertEqual(response.status_code, 429)

    @override_settings(RATE_LIMIT_RULES={'signup': (2, 60)})
    def test_signup_rate_limited(self):
        """POST to /auth/signup/ should be rejected after exceeding limit."""
        for i in range(2):
            self.client.post('/auth/signup/', {
                'email': f'user{i}@example.com',
                'password': 'testpass123',
                'password_confirm': 'testpass123',
            })

        response = self.client.post('/auth/signup/', {
            'email': 'blocked@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
        })
        self.assertEqual(response.status_code, 429)

    @override_settings(RATE_LIMIT_RULES={'password_reset': (2, 60)})
    def test_password_reset_rate_limited(self):
        """POST to /auth/password-reset/ should be rejected after exceeding limit."""
        for _ in range(2):
            self.client.post('/auth/password-reset/', {
                'email': 'test@example.com',
            })

        response = self.client.post('/auth/password-reset/', {
            'email': 'test@example.com',
        })
        self.assertEqual(response.status_code, 429)

    @override_settings(RATE_LIMIT_RULES={'login': (3, 60)})
    def test_get_requests_not_rate_limited(self):
        """GET requests should never be rate-limited."""
        for _ in range(5):
            response = self.client.get('/auth/login/')
            self.assertEqual(response.status_code, 200)

    @override_settings(RATE_LIMIT_RULES={})
    def test_no_rules_means_no_limiting(self):
        """When no rules are configured, nothing is blocked."""
        for _ in range(20):
            response = self.client.post('/auth/login/', {
                'email': 'test@example.com',
                'password': 'wrong',
            })
            self.assertNotEqual(response.status_code, 429)


class EnvironmentVariableSecurityTests(TestCase):
    """Verify secrets are loaded from environment variables."""

    def test_secret_key_uses_env(self):
        """settings module should read SECRET_KEY from os.getenv."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        self.assertIn("os.getenv", source)
        self.assertIn("SECRET_KEY", source)

    def test_debug_uses_env(self):
        """DEBUG setting should be read from environment."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        self.assertIn("os.getenv('DEBUG'", source)

    def test_allowed_hosts_uses_env(self):
        """ALLOWED_HOSTS should be read from environment."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        self.assertIn("os.getenv('ALLOWED_HOSTS'", source)

    def test_no_insecure_secret_key_without_fallback_pattern(self):
        """In the codebase, SECRET_KEY should use getenv with a fallback."""
        import marketplace.settings as s
        source = open(s.__file__).read()
        # Ensure it's using os.getenv, not a bare assignment to the insecure key.
        self.assertNotIn("SECRET_KEY = 'django-insecure", source)


class AuthFlowSecurityTests(TestCase):
    """Test authentication-related security properties."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='secure@example.com',
            password='securepass123',
            user_type='provider',
            is_email_verified=True,
        )

    def test_login_does_not_reveal_email_existence(self):
        """Failed login should use a generic error message."""
        response = self.client.post('/auth/login/', {
            'email': 'nonexistent@example.com',
            'password': 'wrong',
        })
        content = response.content.decode().lower()
        self.assertNotIn('no account found', content)
        self.assertNotIn('email not registered', content)

    def test_password_reset_does_not_reveal_email_existence(self):
        """Password reset should use the same message for any email."""
        response = self.client.post('/auth/password-reset/', {
            'email': 'nonexistent@example.com',
        })
        # Should redirect (302) regardless of email existence.
        self.assertIn(response.status_code, [200, 302])

    def test_logout_requires_no_csrf_for_get(self):
        """GET logout should work (graceful redirect)."""
        self.client.login(email='secure@example.com', password='securepass123')
        response = self.client.get('/auth/logout/')
        self.assertIn(response.status_code, [200, 302])

    def test_unverified_user_cannot_login(self):
        """Users with is_email_verified=False should be rejected."""
        self.user.is_email_verified = False
        self.user.save()

        response = self.client.post('/auth/login/', {
            'email': 'secure@example.com',
            'password': 'securepass123',
        })
        # Should not redirect to dashboard.
        self.assertNotEqual(response.status_code, 302)

    def test_provider_dashboard_requires_login(self):
        """Unauthenticated access to provider dashboard should redirect."""
        response = self.client.get('/provider/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_admin_dashboard_requires_admin_user(self):
        """Non-admin users should be denied access to admin pages."""
        self.client.login(email='secure@example.com', password='securepass123')
        response = self.client.get('/internal/admin/')
        self.assertIn(response.status_code, [302, 403])
