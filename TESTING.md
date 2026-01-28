# Testing Guide

## Quick Start

Run all tests with optimized settings (0.24 seconds):

```bash
./test.sh
```

Or for a specific app:

```bash
./test.sh users
./test.sh providers
```

## Full Testing Commands

### Run All Tests (Optimized)
```bash
python manage.py test users providers reviews payments --settings=marketplace.test_settings
```

### Run Specific App
```bash
python manage.py test users --settings=marketplace.test_settings
```

### Run Specific Test Class
```bash
python manage.py test users.tests.CustomUserModelTests --settings=marketplace.test_settings
```

### Run Specific Test Method
```bash
python manage.py test users.tests.CustomUserModelTests.test_create_user --settings=marketplace.test_settings
```

### Run with Verbosity
```bash
python manage.py test users --settings=marketplace.test_settings -v 2
```

## Test Settings

### Optimized for Development (test_settings.py)
- **MD5 password hashing**: 196x faster than PBKDF2
- **In-memory database**: No disk I/O
- **No password validators**: Speeds up user creation
- **Local memory email backend**: Fast email testing

### Production Settings (settings.py)
- **PBKDF2 password hashing**: Secure, intentionally slow
- **SQLite database**: Persistent storage
- **Full password validation**: Ensures strong passwords

## Test Execution Time

| Scenario | Time | Notes |
|----------|------|-------|
| 84 tests (optimized) | 0.24s | Fast feedback loop |
| 84 tests (production) | ~47s | Realistic hashing |

## Test Coverage

Current test distribution:
- **26 user tests**: Models, authentication, email verification
- **19 provider tests**: Models, services, certifications
- **23 review/payment tests**: Models and validation
- **16 form/view tests**: Signup forms and views

Total: **84 tests all passing** ✓

## Test Organization

```
marketplace/
├── users/
│   ├── tests.py              # Model tests
│   ├── test_forms.py         # Form validation tests
│   └── test_views.py         # View tests
├── providers/
│   └── tests.py              # Model tests
├── reviews/
│   └── tests.py              # Model tests
├── payments/
│   └── tests.py              # Model tests
└── conftest.py               # Pytest configuration
```

## Writing New Tests

### Using Django's TestCase
```python
from django.test import TestCase
from users.models import User

class UserTests(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
```

### Using Django's Client for Views
```python
from django.test import TestCase, Client

class SignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_signup_loads(self):
        response = self.client.get('/auth/signup/')
        self.assertEqual(response.status_code, 200)
```

## Best Practices

1. **One assertion per test method** (when possible)
2. **Clear test names**: `test_user_creation_with_valid_email`
3. **Use setUp/tearDown** for test data
4. **Test both success and failure cases**
5. **Mock external dependencies** (emails, external APIs)
6. **Keep tests isolated** (no test dependencies)

## Continuous Integration

For CI/CD pipelines, use production settings to verify realistic performance:

```bash
python manage.py test users providers reviews payments
```

This ensures passwords will hash correctly in production.

## Debugging Tests

### Run with Breakpoint
```python
import pdb; pdb.set_trace()
```

### Run Single Test Interactively
```bash
python manage.py test users.tests.UserTests.test_create_user -v 2
```

### Inspect Test Database
```bash
python manage.py test users --keepdb --settings=marketplace.test_settings
```

## Common Issues

### "No module named 'users'"
Make sure you're in the marketplace directory:
```bash
cd marketplace
python manage.py test users --settings=test_settings
```

### Tests are slow
Use optimized settings:
```bash
# Good - 0.24s
./test.sh

# Slow - 47s
python manage.py test users providers reviews payments
```

### Database locked errors
Clear in-memory database and restart:
```bash
python manage.py test users --settings=marketplace.test_settings
```

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [Django TestCase API](https://docs.djangoproject.com/en/5.0/ref/test-utils/)
- [Django Database Backends](https://docs.djangoproject.com/en/5.0/ref/databases/)
