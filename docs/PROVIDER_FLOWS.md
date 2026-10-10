# Massage Marketplace — Provider Flows

How a service provider signs up, builds a listing, and pays to be visible.
All routes and view/class names below match `marketplace/marketplace/urls.py`
and `providers/views.py`.

---

## 1. Signup & email verification

**Path**: `/auth/signup/`

1. User submits email + password (min 8 chars) + confirmation. There is no
   separate "user type" field on the form; the account starts as `client` and is
   promoted to `provider` when the provider profile flow is used.
2. `SignupForm` validates a unique, case-insensitive email and matching,
   ≥8-char password.
3. On success the `User` is created with `is_email_verified = False` and an
   `email_verification_token` (from `users/utils.py`).
4. A verification email is sent (console backend in dev) and the user is sent to
   `/auth/check-email/` (`CheckEmailView`).
5. `VerifyEmailView` (`/auth/verify-email/<token>/`) marks the account verified
   and clears the one-time token. Unverified users can request a new link at
   `/auth/resend-email/` (`ResendVerificationView`), which is rate-limited.

Related: `SignupView`, `LoginView`, `LogoutView`, `PasswordResetView`,
`PasswordResetSentView`, `PasswordResetConfirmView`.

---

## 2. Profile & listing

**Path**: `/provider/profile/`

**Prerequisites**: logged in, `user_type = 'provider'`. Access is enforced by
`ProviderRequiredMixin`; the `Provider` row is created on first access if needed.

`ProviderProfileUpdateView` renders `ProviderProfileForm`, `ProviderPricingForm`
and the preference-selection form together. It saves:

- **Identity**: `first_name`, `last_name` (on the User), `bio`, `phone`
  (required), `phone_hours`.
- **Media**: `photo` (JPEG/PNG/GIF, ≤5 MB, auto-resized to ≤800×800 with PIL,
  stored in `media/providers/photos/`), `profile_video` (MP4, ≤50 MB,
  `media/providers/videos/`).
- **Location**: `country` and `city` (city choices are filtered by the selected
  country). Location autocomplete is served by `/api/countries/search/` and
  `/api/cities/search/`.
- **Attributes**: admin-defined `ProviderAttributeDefinition`s are rendered as
  typed fields (string/int/bool) and persisted to `ProviderAttributeValue`.
- **Pricing** (`ProviderPricing`): apartment/outside availability plus the
  day/night × 1h/2h price grid and day/night notes.
- **Preferences**: checked subgroups from the admin catalog
  (`ProviderPreference`) plus provider free-text options
  (`ProviderPreferenceCustomOption`) and provider-created items
  (`ProviderCustomPreference`).

Validated on submit: phone present, image format/size, video format/size.
Success returns to the profile page with a message.

---

## 3. Gallery

**Paths**: `/provider/gallery/upload/`, `/provider/gallery/<pk>/delete/`

- `GalleryImageCreateView` lets a provider add a `ProviderGalleryImage`
  (image + optional caption). `GalleryImageForm` enforces the limit of
  `ProviderGalleryImage.MAX_IMAGES_PER_PROVIDER = 10`.
- `GalleryImageDeleteView` is POST-only and verifies ownership before deleting.

---

## 4. Dashboard

**Path**: `/provider/dashboard/`

`ProviderDashboardView` is the provider hub: profile summary and avatar,
subscription status / renewal date, and links to edit the profile, manage the
subscription, and manage gallery images. Query counts are kept low with
`select_related` / `prefetch_related`.

---

## 5. Subscription & crypto payment

**Paths**: `/provider/subscription/` → `/provider/subscription/crypto/` →
`/provider/subscription/confirm/`

1. `ProviderSubscriptionView` shows the current status and a dynamic coin picker.
   The coin list comes from `payments.nowpayments.get_currencies()` (cached 1 h,
   falls back to `FALLBACK_CURRENCIES`). The chosen code is stored in the session
   as `pending_payment_method`.
2. `CryptoPaymentView` calls `create_payment(amount_usd, pay_currency,
   order_id, ipn_callback_url)`, creates a `SubscriptionPayment`
   (status `pending`) with `nowpayments_payment_id`, `pay_address`,
   `pay_amount`, `pay_currency` and `invoice_url`, and renders the deposit
   address with a QR code and a wallet deep-link. An existing pending payment in
   the session is reused rather than creating duplicates.
3. `CryptoPaymentStatusView` is a JSON endpoint
   (`/provider/subscription/status/<nowpayments_payment_id>/`) the page polls to
   detect confirmation.
4. The provider clicks "I've sent the payment" → `SubscriptionConfirmView`,
   which shows `payment_pending` while the record is still `pending`.
5. `NowPaymentsWebhookView` (IPN, `/payments/webhook/nowpayments/`) verifies the
   HMAC-SHA512 signature, updates `actually_paid`/status, and on a completed
   payment calls `Provider.activate_subscription(payment_method)` (status
   `active`, renewal = today + 30 days).
6. The `expire_subscriptions` management command deactivates overdue providers
   and sends renewal reminders / an admin summary.

Supported coins are defined in `payments/nowpayments.py::SUPPORTED_CURRENCIES`.
Adding a coin is a one-line-list change; `SubscriptionPayment.PAYMENT_METHOD_CHOICES`
derives from that list.

---

## 6. Reviews

A provider can reply once to each review of their profile. `ReviewReplyView`
(`/providers/<slug>/review/<pk>/reply/`) enforces ownership and the 500-char
reply limit. The provider's average rating comes from
`Provider.average_rating()` across all category ratings.

---

## 7. Relationships

```
User (users_user)
  └── Provider (one-to-one, user.provider_profile)
        ├── ProviderGalleryImage (1:N, ≤10)
        ├── ProviderAttributeValue (1:N, per definition)
        ├── ProviderPricing (1:1)
        ├── ProviderPreference / …CustomOption (1:N)
        ├── ProviderCustomPreference (1:N)
        ├── Review (1:N)  └── ReviewReply (1:1)
        └── SubscriptionPayment (1:N)
```

See [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) for field-level detail.

---

## 8. Errors & handling

- Missing session payment method → redirected to `/provider/subscription/` with
  an error.
- NOWPayments `create_payment` failure → error message, redirect to the
  subscription page, exception logged.
- Non-provider or anonymous access to `/provider/…` → login redirect / denied by
  `ProviderRequiredMixin`.
- Invalid/oversized image or video → form validation message.

---

## 9. Manual test checklist

1. Sign up, verify via the console email link, log in.
2. Edit profile: name, phone, bio, photo (resized), location, pricing,
   attributes, preferences.
3. Upload gallery images until the 10-image cap blocks further uploads; delete
   one (POST) and confirm another provider's image cannot be deleted.
4. Start a subscription: pick a coin, confirm address + QR render, simulate IPN,
   confirm the provider becomes active with a renewal date.
5. Post a review as a client and reply to it as the provider.

Automated coverage runs via `./test.sh providers` (see
[`../CONTRIBUTING.md`](../CONTRIBUTING.md#4-testing-requirements)).
