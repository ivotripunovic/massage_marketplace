# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based massage therapy marketplace platform that connects service providers with clients. The platform uses a subscription-based business model where providers pay monthly to list their services, while clients can browse and contact providers for free.

**Key Architecture:**
- Django 5.0 with email-based authentication (no usernames)
- Custom User model with three types: provider, client, admin
- Server-side rendered HTML with Tailwind CSS
- PostgreSQL for production, SQLite for development
- Payment support: Cryptocurrency via NOWPayments (dynamic coin list)
- Error tracking: Sentry SDK (cloud, free tier)
- Structured JSON logging to stdout → systemd journal

## Development Commands

### Testing
```bash
# Run all tests with optimized settings (~396 tests in ~7s)
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

## Code Architecture

### Authentication Flow

1. **Signup**: User creates account → Email verification token generated → Verification email sent
2. **Email Verification**: User clicks link → Token validated → User marked as verified
3. **Login**: Email + password → EmailBackend authenticates → Session created
4. **Password Reset**: Email → Token generated → Reset link sent → Token validated → New password set

**Important**: The authentication backend is in `users/backends.py` and is configured in settings as `AUTHENTICATION_BACKENDS = ['users.backends.EmailBackend']`.

### Provider Subscription Flow

1. Provider completes profile
2. Provider navigates to subscription page
3. Provider selects cryptocurrency from dynamic coin picker (fetched from NOWPayments API, cached 1 hour)
4. NOWPayments creates a payment — provider pays to the generated address
5. NOWPayments IPN webhook (`/payments/webhook/nowpayments/`) confirms payment
6. `Provider.activate_subscription(payment_method)` is called automatically
7. SubscriptionPayment record created with status='completed'

### Access Control Mixins

Two key mixins are used throughout the codebase:

- **ProviderRequiredMixin**: Ensures user is logged in and user_type='provider'
- **AdminRequiredMixin**: Ensures user is logged in and user_type='admin'

Both inherit from LoginRequiredMixin and redirect unauthorized users.

## Development Guidelines

### Template Development

- Tailwind CSS via CDN (no build process required)

### Testing Best Practices

- `NOWPAYMENTS_API_KEY = ""` in test_settings prevents real API calls; `get_currencies()` returns `FALLBACK_CURRENCIES` immediately when key is empty

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
- Payments processed automatically via NOWPayments IPN webhook
- Payment method stored as NOWPayments currency code (e.g. `btc`, `eth`, `usdterc20`)
- Currency list fetched from NOWPayments `/v1/full-currencies` endpoint, cached 1 hour in Redis
- Fallback currency list in `payments/nowpayments.py` used when API key is missing or API is unreachable

### Payment Verification Workflow

- Admin views: `AdminPaymentListView` and `AdminPaymentDetailView`
- Admin can filter by status, payment method, email
- Admin marks payments as completed/failed
- Confirmation emails sent automatically

## Environment Variables

See `.env.example` for all variables. Key ones:
- `SECRET_KEY` — change in production
- `DEBUG` — `False` in production
- `ALLOWED_HOSTS` — comma-separated hostnames
- `DB_*` — PostgreSQL connection settings
- `EMAIL_*` — SMTP configuration
- `NOW_PAYMENTS_API_KEY`, `NOW_PAYMENTS_IPN` — NOWPayments credentials
- `NOWPAYMENTS_SANDBOX` — `true` for sandbox testing
- `SENTRY_DSN` — Sentry error tracking (leave blank to disable)
- `REDIS_URL` — Redis connection (used for caching in production)

## Security Considerations

- NOWPayments IPN webhook verified with HMAC-SHA512 signature

## Git Workflow

Current branch: `main`

When committing:
1. Make focused, atomic commits
2. Write clear commit messages
3. Run tests before committing: `./test.sh`
4. Ensure migrations are included if models changed
