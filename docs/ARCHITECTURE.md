# Massage Marketplace — Architecture

Django 5.2 marketplace connecting massage-therapy providers with clients.
Providers pay a monthly cryptocurrency subscription (NOWPayments) to be listed;
clients browse and read reviews for free. Server-rendered HTML with minimal JS.

---

## 1. System overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  Django templates · Tailwind (CDN) · location-autocomplete.js│
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/HTTPS
┌───────────────────────────▼─────────────────────────────────┐
│                  Django 5.2 application                     │
│  urls.py → views → forms → models → templates               │
│  middleware: RateLimitMiddleware                            │
│  context processor: subscription_price                      │
└───────┬───────────────┬───────────────┬─────────────────────┘
        │               │               │
   ┌────▼────┐     ┌────▼────┐     ┌────▼─────────────┐
   │ SQLite  │     │  Redis  │     │  NOWPayments API │
   │ (dev)   │     │ (prod)  │     │  (create/IPN)    │
   │ Postgres│     │ cache   │     └──────────────────┘
   │ (prod)  │     └─────────┘
   └─────────┘
        │
   ┌────▼──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Media (local FS)  │   │ Sentry       │   │ journald     │
   │ photos/gallery/   │   │ error track  │   │ JSON logs    │
   │ certifications    │   └──────────────┘   └──────────────┘
   └───────────────────┘
```

Production runs Gunicorn + Nginx behind the bare-repo `post-receive` deploy hook.
See [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## 2. Repository layout

```
massage_marketplace/
├── marketplace/                 # Django project root
│   ├── manage.py
│   ├── marketplace/             # Project package
│   │   ├── settings.py          # env-driven settings
│   │   ├── test_settings.py     # fast test overrides (MD5, in-memory, DummyCache)
│   │   ├── urls.py              # all routes
│   │   ├── middleware.py        # RateLimitMiddleware
│   │   ├── context_processors.py# subscription_price (global template var)
│   │   ├── wsgi.py / asgi.py
│   ├── users/                   # auth, custom User, legal pages
│   ├── providers/               # Provider + catalog + location + preferences
│   ├── clients/                 # public directory/detail, filters, autocomplete APIs
│   ├── reviews/                 # reviews, categories, replies
│   ├── payments/                # NOWPayments client + subscription payments
│   ├── templates/               # base.html + per-app templates + includes/ + emails/
│   ├── static/                  # js/location-autocomplete.js, images
│   ├── media/                   # uploaded photos, gallery, certifications (gitignored)
│   ├── fixtures/ (providers/)   # continent/country/city seed data
│   └── db.sqlite3               # local dev database
├── deploy/                      # gunicorn.conf.py, marketplace.service, nginx.conf,
│                                #   post-receive, setup.sh, backup.sh
├── docs/                        # this doc, schema, flows, theme, deployment
│   └── archive/                 # historical PRD + task list
├── test.sh                      # fast test runner
└── requirements.txt
```

---

## 3. Applications

### 3.1 `users` — authentication & accounts

- **`User(AbstractUser)`** (`users/models.py`): email is `USERNAME_FIELD`, `username`
  removed, `user_type ∈ {provider, client, admin}`, `is_email_verified`,
  `email_verification_token`, `phone_number`. Table `users_user`.
- **`CustomUserManager`**: normalises/lowercases email, `create_user` /
  `create_superuser`.
- **`users/backends.py` — `EmailBackend`**: case-insensitive email auth. Registered
  as the sole `AUTHENTICATION_BACKENDS` entry.
- **`users/utils.py`**: `generate_email_verification_token`, `verify_email_token`
  (one-time use), `send_verification_email`, plus password-reset token helpers.
- **Views**: `SignupView`, `CheckEmailView`, `VerifyEmailView`,
  `ResendVerificationView`, `LoginView`, `LogoutView`, `PasswordResetView`,
  `PasswordResetSentView`, `PasswordResetConfirmView`.
- **Management command**: `test_email` (SMTP smoke test).

### 3.2 `providers` — profiles & catalog

Models (`providers/models.py`):

| Model | Purpose |
|-------|---------|
| `Continent` / `Country` / `City` | Location reference data; **US excluded** by fixture design |
| `Provider` | Profile, location FKs, subscription status/renewal, pricing/preferences root, gallery; `slug` generated on save |
| `ProviderGalleryImage` | Up to `MAX_IMAGES_PER_PROVIDER = 10` gallery images |
| `ProviderAttributeDefinition` / `ProviderAttributeValue` | Admin-defined typed custom attributes (string/int/bool) |
| `ProviderPricing` | One-to-one structured price grid (apartment/outside × day/night × 1h/2h) |
| `PreferenceGroup` / `PreferenceSubgroup` / `PreferenceSubgroupOption` | Admin-defined preference tree |
| `ProviderPreference` | Per-provider on/off toggle per subgroup |
| `ProviderPreferenceCustomOption` | Provider free-text option per subgroup |
| `ProviderCustomPreference` | Provider-created preference item ("Other" group) |

Provider helpers: `get_name()`, `get_absolute_url()` (slug-based),
`is_subscription_active()`, `activate_subscription(payment_method)`
(sets `active` + 30-day renewal), `deactivate_subscription()`,
`average_rating()` (averages category ratings).

Mixin: **`ProviderRequiredMixin`** (login + `user_type == 'provider'`).

Views: `ProviderDashboardView`, `ProviderProfileUpdateView` (profile + pricing +
preferences), `ProviderSubscriptionView`, `CryptoPaymentView`,
`CryptoPaymentStatusView`, `SubscriptionConfirmView`, `GalleryImageCreateView`,
`GalleryImageDeleteView`, `AdminProviderListView`, `AdminRequiredMixin`.

Signals (`providers/signals.py`, registered from `ProvidersConfig.ready()`):
invalidate the `pref_groups_tree` cache when preference-tree models change.

Fixtures: `providers/fixtures/00*.json` (continents, countries, cities by
continent). Load order documented in [`ui_theme.md`](ui_theme.md).

### 3.3 `clients` — public marketplace

No models (`clients/models.py` empty); all logic in views:

- `ProviderDirectoryView` — public list at `/` and `/providers/`; filters by
  `service` type, `country`, `city`, `price_min`, `price_max` via GET params;
  only `subscription_status='active'` + verified providers; paginated 20/page;
  caches counts (`CachedCountPaginator`).
- `ProviderDetailView` — public profile at `/providers/<slug>/`; 404 for
  inactive/unverified; prefetches gallery, reviews + category ratings + replies,
  attribute values, preferences and pricing.
- `ClientProfileView`, `ClientReviewsView` — authenticated client account pages.
- `country_search_api`, `city_search_api` — JSON autocomplete endpoints
  (`/api/countries/search/`, `/api/cities/search/`), backed by
  `static/js/location-autocomplete.js`.

`ClientRequiredMixin` gates the client account views.

### 3.4 `reviews`

- `ReviewCategory` — admin-defined rating dimensions.
- `Review` — one per `(provider, client)`, authenticated clients only, ≤250-char
  comment. `average_rating()` averages its category ratings.
- `ReviewCategoryRating` — 1–5 per category, unique per `(review, category)`.
- `ReviewReply` — provider's one-to-one response (≤500 chars).

Views: `ReviewSubmitView` (login required), `ReviewReplyView`.
Routes are slug-based: `/providers/<slug>/review/` and `.../<pk>/reply/`.

### 3.5 `payments`

- `SubscriptionPayment` (`payments/models.py`): amount, dynamic
  `payment_method` choices from `SUPPORTED_CURRENCIES`, `status ∈ {pending,
  completed, failed, partial}`, and NOWPayments fields (`nowpayments_payment_id`,
  `pay_address`, `pay_amount`, `pay_currency`, `invoice_url`, `actually_paid`).
- `payments/nowpayments.py`: API client + IPN verification.
  - `SUPPORTED_CURRENCIES` — curated list (currently USDT on Polygon `usdtmatic`
    and BSC `usdtbsc`), each with network, EIP-681 contract, chain id, decimals.
    **Add a coin by appending one entry** — no other code changes.
  - `get_currencies()` — fetches `/full-currencies`, filtered to supported codes,
    cached 1 hour; falls back to `FALLBACK_CURRENCIES` when API key is blank or
    API unreachable.
  - `create_payment(...)` — `POST /payment`; honours `NOWPAYMENTS_SANDBOX`.
  - `verify_ipn_signature(...)` — HMAC-SHA512 over key-sorted JSON, compared with
    `hmac.compare_digest`; rejects when the secret is unset.
- Views: `NowPaymentsWebhookView` (IPN), plus admin endpoints
  `AdminDashboardView`, `AdminPaymentListView`, `AdminPaymentDetailView`,
  `AdminPaymentApproveView`, `AdminProviderDetailView`,
  `AdminProviderSuspendView`, `AdminAnalyticsView` (all `AdminRequiredMixin`).
- Management command: `monitor_crypto_payments` (reconciliation).

---

## 4. Request flow (URL map)

| Area | Routes |
|------|--------|
| Public | `/`, `/providers/`, `/providers/<slug>/` |
| Reviews | `/providers/<slug>/review/`, `/providers/<slug>/review/<pk>/reply/` |
| Auth | `/auth/signup/`, `/auth/check-email/`, `/auth/resend-email/`, `/auth/verify-email/<token>/`, `/auth/login/`, `/auth/logout/`, `/auth/password-reset/…` |
| Client | `/client/profile/`, `/client/reviews/` |
| Provider | `/provider/dashboard/`, `/provider/profile/`, `/provider/subscription/…`, `/provider/gallery/upload/`, `/provider/gallery/<pk>/delete/` |
| Internal admin | `/internal/admin/…` (dashboard, providers, payments, analytics) |
| Legal | `/terms/`, `/privacy/`, `/payment-policy/` |
| APIs | `/api/countries/search/`, `/api/cities/search/` |
| Webhook | `/payments/webhook/nowpayments/` |
| Django admin | `/admin/` |

---

## 5. Key flows

### Authentication
`Signup → create User (unverified) → verification token stored → email (console
in dev) → VerifyEmailView marks verified + clears token → LoginView via
EmailBackend → session`. Password reset reuses the same token pattern.

### Provider onboarding
`ProviderProfileUpdateView` saves profile + location + `ProviderPricing` +
preference selections; photos and gallery images are validated (type/size),
resized with PIL, and stored under `media/providers/…`.

### Subscription & crypto payment
1. `ProviderSubscriptionView` — provider picks a supported coin.
2. `CryptoPaymentView` — calls `create_payment()`, stores a `SubscriptionPayment`
   (`pending`) with `pay_address` / `pay_amount` / `invoice_url`; renders address +
   QR (EIP-681 deep link).
3. `CryptoPaymentStatusView` — polls status via NOWPayments.
4. `NowPaymentsWebhookView` (IPN) — verifies HMAC signature, then on completed
   payment calls `Provider.activate_subscription(payment_method)` and marks the
   record `completed`; partial/failed/expired states update status accordingly.
5. Daily `expire_subscriptions` command deactivates past-due providers, emails
   renewal reminders (3 days out) and an admin summary.

### Reviews
Authenticated clients submit one review per provider with per-category ratings;
the provider can post a single reply. Ratings roll up via
`Provider.average_rating()`.

---

## 6. Cross-cutting concerns

### Settings & environment (`marketplace/settings.py`)
Env-driven via `python-dotenv` (`.env`). Key toggles:
- `DEBUG` selects console/verbose vs JSON logging, DummyCache vs Redis, and
  production-only security headers (HSTS, SSL redirect, secure cookies).
- `SUBSCRIPTION_AMOUNT` (default 29.99) exposed to templates via
  `subscription_price` context processor.
- `NOWPAYMENTS_API_KEY`, `NOWPAYMENTS_IPN_SECRET`, `NOWPAYMENTS_SANDBOX`.
- `PLATFORM_CRYPTO_ADDRESSES`, `PLATFORM_BANK_DETAILS`, `ADMIN_EMAILS`.
- `SENTRY_DSN` / `SENTRY_ENVIRONMENT` / `SENTRY_TRACES_SAMPLE_RATE`.

### Middleware
`RateLimitMiddleware` — per-IP POST limiting for named routes via
`RATE_LIMIT_RULES` (`login` 5/min, `signup` 5/hr, `password_reset` 3/hr). Uses an
in-process store; for multi-worker production a shared store (Redis) is the
recommended upgrade path. `RateLimitMiddleware.reset()` aids tests.

### Caching
Redis in production (`django-redis`), `DummyCache` in dev/test. Used for the
NOWPayments currency list, homepage/count pagination, and the preference-group
tree (invalidated by signals).

### Observability
Sentry SDK initialised only when `SENTRY_DSN` is set. Structured JSON logging via
`python-json-logger` in production, verbose text in dev; output flows to stdout →
systemd journal. See the `observability` skill for `journalctl` recipes.

### Security
Email-based auth; CSRF on all forms; Django ORM (SQLi-safe); template
auto-escaping (XSS-safe); `X_FRAME_OPTIONS=DENY`; signed/one-time verification
tokens; HMAC-verified payment webhook; file-upload validation (MIME + size +
PIL verification) with unique filenames.

### Frontend
Server-rendered Django templates extending `templates/base.html` (dark theme,
Tailwind via CDN). Reusable `templates/includes/` components (messages, form,
gallery card, pagination). Only bespoke JS is
`static/js/location-autocomplete.js` (debounced country/city search with
keyboard navigation and ARIA).

---

## 7. Management commands

| Command | App | Purpose |
|---------|-----|---------|
| `expire_subscriptions [--dry-run]` | providers | Deactivate expired, send renewal reminders + admin summary |
| `check_production` | providers | Production sanity/config checks |
| `seed_beta_data` | providers | Seed demo providers for beta |
| `seed_gallery_photos` | providers | Populate gallery images |
| `monitor_crypto_payments` | payments | Reconcile pending crypto payments |
| `test_email <addr>` | users | Verify SMTP configuration |

---

## 8. Testing

Fast suite: `./test.sh` (~396 tests, ~7s) using
`marketplace/marketplace/test_settings.py` — MD5 hashing, in-memory SQLite,
locmem email, DummyCache, rate limiting off, blank NOWPayments key. Live sandbox
tests live in `payments/tests_sandbox.py` and are excluded by default. Full
guide in [`../CONTRIBUTING.md`](../CONTRIBUTING.md#4-testing-requirements).

---

## 9. Deployment

Gunicorn (2 sync workers on a 1 GB VPS) behind Nginx; static/media served by
Nginx; Redis for cache; PostgreSQL in production. Deploys run
`git push production main` → `post-receive` hook (checkout, pip install,
migrate, collectstatic, service restart). Details, systemd unit, SSL, backups
and monitoring: [`DEPLOYMENT.md`](DEPLOYMENT.md).

---

## 10. Known limitations / future work

- `RateLimitMiddleware` uses an in-process store (swap for Redis at scale).
- Geolocation is fixture-based (capitals + major cities); no radius/"nearby"
  search or map view yet.
- Country/city fixtures exclude the US by design.
- Single subscription tier; no automated recurring billing (active window is set
  to 30 days and expired by cron).
</content>
