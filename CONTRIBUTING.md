# Contributing to Massage Marketplace

## Development Workflow

### 1. Feature Branches
Always create a feature branch for new work:

```bash
git checkout -b feature/task-name
```

Branch naming convention:
- `feature/task-description` - New features
- `fix/bug-description` - Bug fixes
- `refactor/improvement` - Code improvements

### 2. Commits

Write clear, descriptive commit messages:

```
[TASK-ID] Brief description of change

Longer explanation if needed. Reference any related issues.

- Bullet point 1
- Bullet point 2
```

Example:
```
[1.1] Initialize Django project with models

- Created Django 5.0 project with 5 apps
- Added custom User model with email-based auth
- Configured database settings
- Added requirements.txt with dependencies
```

### 3. Code Style

#### Python
- Use PEP 8 style guide
- 4 spaces for indentation
- Max line length: 99 characters
- Use type hints where appropriate

```python
# Good
def create_user(email: str, password: str) -> User:
    """Create a new user."""
    return User.objects.create_user(email=email, password=password)
```

#### Django
- Use class-based views for most views
- Keep models in `models.py`
- Register models in `admin.py`
- Create forms in `forms.py`
- Organize templates in `templates/<app>/`

### 4. Testing Requirements

**All code must be tested before committing.**

Fastest path — from the repository root:
```bash
# Run the full suite with optimized settings (~7s, ~396 tests)
./test.sh

# Run a specific app
./test.sh users
./test.sh providers
```

Under the hood `./test.sh` runs:

```bash
python marketplace/manage.py test users providers reviews payments.tests \
    users.test_security users.test_legal --settings=marketplace.test_settings
```

Equivalent manual commands (run from the repository root):

```bash
# All tests
python marketplace/manage.py test --settings=marketplace.test_settings

# With verbosity
python marketplace/manage.py test --settings=marketplace.test_settings -v 2

# Specific app / class / method
python marketplace/manage.py test users --settings=marketplace.test_settings
python marketplace/manage.py test users.tests.CustomUserModelTests --settings=marketplace.test_settings
python marketplace/manage.py test users.tests.CustomUserModelTests.test_create_user --settings=marketplace.test_settings
```

> `payments/tests_sandbox.py` (live NOWPayments sandbox integration) is
> excluded from `./test.sh`. Run it explicitly when needed:
> `python marketplace/manage.py test payments.tests_sandbox --settings=marketplace.test_settings`

#### Test settings

`marketplace/test_settings.py` inherits the main settings and optimizes for speed:

- **MD5 password hashing** — ~196x faster than PBKDF2
- **In-memory SQLite** — no disk I/O
- **No password validators** — faster user creation
- **Locmem email backend** — fast email assertions
- **DummyCache** — no Redis required
- **Rate limiting disabled** — security tests re-enable it explicitly
- **`NOWPAYMENTS_API_KEY = ""`** — no real API calls; `get_currencies()` returns the fallback list immediately

Without `--settings=marketplace.test_settings`, tests use production-like PBKDF2
hashing and take dramatically longer. Always use the fast settings during
development.

#### Test organization

```
marketplace/
├── users/
│   ├── tests.py          # models, auth, email verification
│   ├── test_forms.py     # form validation
│   ├── test_views.py     # view responses
│   ├── test_security.py  # rate limiting, auth hardening
│   └── test_legal.py     # legal pages
├── providers/tests.py    # models, services, certification, location, preferences
├── clients/tests.py      # directory, detail, filters, autocomplete APIs
├── reviews/tests.py      # reviews, categories, replies
├── payments/tests.py     # payment model, IPN webhook, admin flows
└── payments/tests_sandbox.py  # live sandbox integration (excluded by default)
```

**Test File Naming:**
- `tests.py` - Main tests for models and views
- `test_forms.py` - Form tests
- `test_views.py` - View tests
- `test_<feature>.py` - Focused suites (e.g. `test_security.py`)

#### Writing tests

```python
from django.test import TestCase, Client
from users.models import User

class UserTests(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.assertEqual(user.email, "test@example.com")
```

Best practices:
1. One assertion per test method (when possible)
2. Clear names: `test_user_creation_with_valid_email`
3. Use `setUp`/`tearDown` for shared data
4. Test both success and failure cases
5. Mock external dependencies (email, NOWPayments API)
6. Keep tests isolated (no inter-test dependencies)

#### Debugging tests

```bash
# Single test, interactive
python marketplace/manage.py test users.tests.UserTests.test_create_user -v 2

# Reuse the test database between runs
python marketplace/manage.py test users --keepdb --settings=marketplace.test_settings
```

Add `import pdb; pdb.set_trace()` inside a test to drop into a debugger.

#### Common issues

- **"No module named 'users'"** — use `python marketplace/manage.py ...` from the
  repo root (or `python manage.py ...` from inside `marketplace/`).
- **Tests are slow** — you forgot `--settings=marketplace.test_settings`; use `./test.sh`.
- **Database locked errors** — the suite uses in-memory SQLite; re-run rather than
  reusing on-disk state.

**Test Coverage Requirements:** aim for full coverage on models, forms, views, and utils.

### 5. Pull Request Process

1. Push your feature branch
2. Create a pull request with:
   - Descriptive title
   - Summary of changes
   - Related issues/tasks
   - Test results showing all passing

3. Code review checklist:
   - [ ] All tests pass
   - [ ] Code follows style guide
   - [ ] Models have proper validation
   - [ ] Views have appropriate decorators/mixins
   - [ ] Forms validate correctly
   - [ ] Templates are properly structured
   - [ ] No hardcoded credentials or sensitive data
   - [ ] Documentation is updated

### 6. Documentation

- Update `README.md` for setup changes
- Update `docs/` when behaviour or architecture changes
- Add docstrings to all functions and classes
- Comment complex logic
- Update this file with any new conventions

> Historical planning documents live in `docs/archive/` and are not maintained.

## Task Workflow

Each task follows this pattern:

1. **Plan**: Break the work into atomic steps
2. **Implement**: Write code with tests
3. **Test**: Run full test suite (all passing)
4. **Document**: Update `README.md` / `docs/` as needed
5. **Commit**: Push changes with a clear commit message

## Running the Project Locally

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python marketplace/manage.py migrate

# Create superuser
python marketplace/manage.py createsuperuser

# Start development server
python marketplace/manage.py runserver

# Access admin
# http://localhost:8000/admin
```

## Database

### Migrations
Always create migrations after model changes:
```bash
python marketplace/manage.py makemigrations
python marketplace/manage.py migrate
```

### Resetting Database (Development Only)
```bash
rm marketplace/db.sqlite3
python marketplace/manage.py migrate
python marketplace/manage.py createsuperuser
```

## Common Commands

```bash
# Run tests
./test.sh <app>   # e.g. ./test.sh providers

# Create migration
python marketplace/manage.py makemigrations

# Apply migrations
python marketplace/manage.py migrate

# Check for issues
python marketplace/manage.py check

# Shell with context
python marketplace/manage.py shell

# Create fixture (for testing data)
python marketplace/manage.py dumpdata > fixtures.json
python marketplace/manage.py loaddata fixtures.json
```

## Environment Variables

Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

Never commit `.env` file (it's in `.gitignore`).

## Git Workflow Summary

```bash
# 1. Create feature branch
git checkout -b feature/task-name

# 2. Make changes and test
./test.sh

# 3. Stage and commit
git add .
git commit -m "[TASK-ID] Clear description"

# 4. Push to remote
git push origin feature/task-name

# 5. Create pull request and merge after review
```

## Questions?

Check:
1. README.md for setup help and feature overview
2. docs/ for architecture, schema, flows and deployment
3. This file for conventions and testing
4. docs/archive/ for historical planning documents
