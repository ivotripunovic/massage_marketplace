# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based massage therapy marketplace platform that connects service providers with clients. The platform uses a subscription-based business model where providers pay monthly to list their services, while clients can browse and contact providers for free.

**Key Architecture:**
- Django 5.0 with email-based authentication (no usernames)
- Custom User model with three types: provider, client, admin
- Server-side rendered HTML with Tailwind CSS
- PostgreSQL for production, SQLite for development
- Payment support: Cryptocurrency (BTC, ETH, USDC) and bank transfers

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python marketplace/manage.py migrate

# Create superuser
python marketplace/manage.py createsuperuser

# Run development server
python marketplace/manage.py runserver
```

### Testing
```bash
# Run all tests with optimized settings (84 tests in ~0.24s)
./test.sh

# Run specific app tests
./test.sh users
./test.sh providers

# Run specific test class
python marketplace/manage.py test users.tests.CustomUserModelTests --settings=marketplace.test_settings

# Run specific test method
python marketplace/manage.py test users.tests.CustomUserModelTests.test_create_user --settings=marketplace.test_settings

# Run with production settings (slower, ~47s due to PBKDF2 hashing)
python marketplace/manage.py test users providers reviews payments
```

**Important:** Always use `--settings=marketplace.test_settings` for fast development testing. The test settings use MD5 hashing (196x faster) and in-memory database.

### Database Management
```bash
# Create migrations after model changes
python marketplace/manage.py makemigrations

# Apply migrations
python marketplace/manage.py migrate

# Access Django shell
python marketplace/manage.py shell
```

## Code Architecture

### Application Structure

The project follows Django's app-based architecture with clear separation:

```
marketplace/
├── marketplace/          # Project settings and configuration
│   ├── settings.py       # Main settings (DEBUG=True, production settings)
│   ├── test_settings.py  # Optimized test settings (MD5 hashing, in-memory DB)
│   └── urls.py           # Root URL configuration
│
├── users/                # Authentication and user management
│   ├── models.py         # Custom User model (email-based, no username)
│   ├── backends.py       # EmailBackend for authentication
│   ├── utils.py          # Email verification token utilities
│   └── views.py          # Signup, login, email verification flows
│
├── providers/            # Provider profiles and service management
│   ├── models.py         # Provider, Service, Certification models
│   ├── views.py          # Provider dashboard, profile editing, subscription
│   └── forms.py          # Provider forms with validation
│
├── payments/             # Subscription payment processing
│   ├── models.py         # SubscriptionPayment model
│   ├── views.py          # Admin payment verification views
│   └── admin.py          # Payment admin interface
│
├── reviews/              # Review and rating system
│   └── models.py         # Review model
│
└── templates/            # HTML templates (server-side rendered)
    ├── base.html         # Base template with navigation
    ├── includes/         # Reusable components (_messages, _form, _cards)
    ├── users/            # Auth templates
    ├── providers/        # Provider templates
    └── admin/            # Admin templates
```

### Key Models and Relationships

**User Model** (`users/models.py`):
- Custom AbstractUser with email as USERNAME_FIELD (no username)
- Fields: email (unique), user_type (provider/client/admin), is_email_verified, email_verification_token, phone_number
- Manager: CustomUserManager handles email normalization

**Provider Model** (`providers/models.py`):
- OneToOne with User
- Fields: bio, phone, photo, subscription_status, subscription_payment_method, subscription_renewal_date, crypto_address, bank_account_encrypted
- Methods: `is_subscription_active()`, `activate_subscription(payment_method)`, `deactivate_subscription()`
- Related models: Service (many-to-one) and Certification (many-to-one)

**Service Model** (`providers/models.py`):
- ForeignKey to Provider
- Fields: service_type, description, price (min $5.00), duration (30/60/90 minutes), is_active
- Validation: price must be >= 5.00, duration must be in (30, 60, 90)

**SubscriptionPayment Model** (`payments/models.py`):
- ForeignKey to Provider
- Fields: amount, status (pending/completed/failed), payment_method, transaction_reference
- Used for admin payment verification workflow

### Authentication Flow

1. **Signup**: User creates account → Email verification token generated → Verification email sent
2. **Email Verification**: User clicks link → Token validated → User marked as verified
3. **Login**: Email + password → EmailBackend authenticates → Session created
4. **Password Reset**: Email → Token generated → Reset link sent → Token validated → New password set

**Important**: The authentication backend is in `users/backends.py` and is configured in settings as `AUTHENTICATION_BACKENDS = ['users.backends.EmailBackend']`.

### Provider Subscription Flow

1. Provider completes profile
2. Provider navigates to subscription page
3. Provider selects payment method (crypto or bank transfer)
4. Provider submits payment details
5. `Provider.activate_subscription(payment_method)` is called
6. SubscriptionPayment record created with status='pending'
7. Email sent to provider with payment instructions
8. Admin verifies payment in admin dashboard
9. Admin marks payment as completed/failed

### Access Control Mixins

Two key mixins are used throughout the codebase:

- **ProviderRequiredMixin**: Ensures user is logged in and user_type='provider'
- **AdminRequiredMixin**: Ensures user is logged in and user_type='admin'

Both inherit from LoginRequiredMixin and redirect unauthorized users.

## Development Guidelines

### When Modifying Models

1. Make changes to model in respective app's `models.py`
2. Run `python marketplace/manage.py makemigrations`
3. Review generated migration file
4. Run `python marketplace/manage.py migrate`
5. Update corresponding forms in `forms.py` if needed
6. Add/update tests in `tests.py`
7. Run tests to ensure nothing breaks: `./test.sh`

### When Adding New Views

1. Define view in app's `views.py` (prefer class-based views)
2. Add URL pattern to `marketplace/urls.py`
3. Create template in `templates/[app_name]/`
4. Use appropriate mixin for access control (ProviderRequiredMixin, AdminRequiredMixin)
5. Handle form validation and error messages
6. Add tests for the view

### When Working with Forms

1. Use Django ModelForms for model-backed forms
2. Implement custom validation in `clean_[field]()` methods
3. Handle image uploads with proper validation (file type, size)
4. Use the reusable `_form.html` template for consistent form rendering
5. Display validation errors using Django messages framework

### Template Development

- Base template: `templates/base.html` includes navigation and message display
- Reusable includes: `_messages.html`, `_form.html`, `_service_card.html`, `_certification_card.html`
- Tailwind CSS via CDN (no build process required)
- Minimal JavaScript (prefer server-side rendering)
- Always use `{% csrf_token %}` in forms

### Testing Best Practices

- Use `--settings=marketplace.test_settings` for fast feedback (0.24s for 84 tests)
- Test both success and failure cases
- Use Django's TestCase for database tests
- Mock email sending in tests (already configured in test_settings)
- Keep tests isolated (no dependencies between tests)
- Use `setUp()` for test data creation
- Current coverage: 84 tests across users, providers, reviews, payments

## Important Implementation Details

### Email Verification Tokens

- Generated in `users/utils.py` using `generate_email_verification_token()`
- Stored in `User.email_verification_token`
- One-time use: Token is cleared after successful verification
- Validation in `verify_email_token()`

### Image Handling

- Provider photos: `media/providers/photos/`
- Certifications: `media/providers/certifications/`
- Validation: File type (JPEG/PNG/GIF), size (5MB max)
- Image format verification with PIL
- Images are resized/optimized on upload

### Subscription Management

- Subscriptions are 30-day recurring
- Status: active, inactive, suspended
- Renewal date tracked in `Provider.subscription_renewal_date`
- Manual admin verification for payments (no automatic processing in MVP)
- Payment methods: crypto (BTC/ETH/USDC) or bank transfer

### Payment Verification Workflow

- Admin views: `AdminPaymentListView` and `AdminPaymentDetailView`
- Admin can filter by status, payment method, email
- Admin marks payments as completed/failed
- Confirmation emails sent automatically

## Common Patterns

### Creating a Provider Profile

```python
# User must be created first
user = User.objects.create_user(
    email='provider@example.com',
    password='password',
    user_type='provider'
)

# Create provider profile
provider = Provider.objects.create(
    user=user,
    phone='+1234567890',
    bio='Experienced massage therapist...'
)
```

### Checking Subscription Status

```python
# In view or template
if request.user.provider_profile.is_subscription_active():
    # Allow provider actions
    pass
```

### Adding Services

```python
# Service creation with validation
service = Service.objects.create(
    provider=provider,
    service_type='swedish',
    description='Relaxing Swedish massage',
    price=50.00,  # Must be >= 5.00
    duration=60,  # Must be 30, 60, or 90
    is_active=True
)
```

## URL Patterns

Key URL patterns to know:

- Auth: `/auth/signup/`, `/auth/login/`, `/auth/logout/`
- Provider: `/provider/dashboard/`, `/provider/profile/`, `/provider/subscription/`
- Services: `/provider/services/`, `/provider/services/create/`, `/provider/services/<id>/edit/`
- Admin: `/internal/admin/providers/`, `/internal/admin/payments/`

## Environment Variables

See `.env.example` for required environment variables:
- Database configuration (PostgreSQL in production)
- Email backend configuration
- SECRET_KEY (change in production)
- DEBUG setting
- ALLOWED_HOSTS

## Security Considerations

- CSRF protection enabled on all forms
- Email-based authentication (more secure than usernames)
- Password hashing: PBKDF2 in production, MD5 in tests only
- Image upload validation (type, size, format)
- Bank account details stored encrypted (TextField, encryption implementation TBD)
- Admin access protected with AdminRequiredMixin
- Session-based authentication

## Git Workflow

Current branch: `master`
Recent work: Sprint 1 complete (Admin Extensions & Subscription System)

When committing:
1. Make focused, atomic commits
2. Write clear commit messages
3. Run tests before committing: `./test.sh`
4. Ensure migrations are included if models changed
