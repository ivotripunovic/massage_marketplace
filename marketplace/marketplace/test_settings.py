"""
Test settings - inherits from main settings but optimizes for test speed.
Use with: python manage.py test --settings=marketplace.test_settings
"""

from .settings import *  # noqa

# Use faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable password validators to speed up user creation
AUTH_PASSWORD_VALIDATORS = []

# Use in-memory email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use simple test database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # In-memory database for faster tests
    }
}

# Disable rate limiting by default in tests (security tests override this)
RATE_LIMIT_RULES = {}

# Use dummy cache in tests — no Redis dependency
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable NOWPayments API calls during tests (get_currencies returns fallback)
NOWPAYMENTS_API_KEY = ""

# Disable migrations for faster test setup
# (comment out if you need migration testing)
# MIGRATION_MODULES = {app: None for app in INSTALLED_APPS if 'django' not in app}
