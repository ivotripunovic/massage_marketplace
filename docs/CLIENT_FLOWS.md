# Massage Marketplace — Client Flows

How visitors browse, filter and evaluate providers, and how registered clients
manage their account and reviews. Routes and views match
`marketplace/marketplace/urls.py` and `clients/views.py`.

Browsing needs no account. Only **verified** providers with an **active**
subscription are listed (`subscription_status='active'` and
`user__is_email_verified=True`).

---

## 1. Browse the directory

**Paths**: `/` and `/providers/` → `ProviderDirectoryView` (public)

- Responsive grid of active, verified providers; 20 per page with pagination.
- Each card shows the provider photo/avatar, name, average rating + review count,
  and a pricing snippet (apartment price preferred, else outside).
- Empty state when no providers match.

**Filters** (GET parameters on `/providers/`):

| Param | Meaning |
|-------|---------|
| `keyword` | matches bio / first name / last name |
| `country_id`, `city_id` | exact location FKs (city list narrows by country) |
| `price_min`, `price_max` | bound on `pricing__apartment_day_1h` |
| `apartment=1` / `outside=1` | availability |
| `min_rating` | minimum average rating (annotated subquery) |
| `has_photo=1` | only providers with a profile photo |
| `pref` (repeatable) | any matching preference subgroup (OR) |

The country/city pickers use the autocomplete APIs `/api/countries/search/` and
`/api/cities/search/` (`country_search_api`, `city_search_api`) via
`static/js/location-autocomplete.js`. Queries use `select_related` /
`prefetch_related` and a cached count paginator.

---

## 2. View a provider profile

**Path**: `/providers/<slug>/` → `ProviderDetailView` (public)

Returns 404 for missing, inactive, or unverified providers. The page shows:

- **Header**: photo (or video), name, rating, country/city, phone, phone hours.
- **About**: bio and admin-defined attributes (`formatted_value()`)).
- **Pricing**: the structured apartment/outside × day/night grid + notes.
- **Preferences**: the provider's checked subgroups, custom options and
  "Other" items, plus `preference_comment`.
- **Gallery**: `ProviderGalleryImage`s.
- **Reviews**: list newest-first with per-category ratings and the provider's
  reply; rating summary computed from `ReviewCategoryRating`.

Related data is fetched with a single `select_related`/`prefetch_related` chain.

### Contact
Providers are contacted out-of-band via the displayed phone number. There is no
in-app messaging.

---

## 3. Reviews (reading)

Reviews appear on the profile page. Each shows the reviewer's name, date, comment
(≤250 chars), and category star ratings. The provider may reply once. Reviews are
only created by authenticated users (see `reviews` below), so there are no
anonymous reviews.

---

## 4. Client account (registered users)

Clients register with the same signup flow as providers (`/auth/signup/`).

- **`ClientProfileView`** — `/client/profile/`: account details.
- **`ClientReviewsView`** — `/client/reviews/`: reviews written by the client.
- **`ReviewSubmitView`** — `/providers/<slug>/review/`: submit one review per
  provider with per-category 1–5 ratings and an optional ≤250-char comment
  (login required; unique constraint on `(provider, client)`).
- **`ReviewReplyView`** — `/providers/<slug>/review/<pk>/reply/`: reply to a
  review (login required).

---

## 5. Common journeys

1. **Discover** — land on `/`, apply filters (location, price, availability,
   rating), open provider profiles.
2. **Evaluate** — compare rating, pricing grid, gallery, attributes and reviews.
3. **Contact** — call the provider directly.
4. **Review** — after signing up/in, leave a category-rated review and reply
   threads.

---

## 6. Navigation

```
Home / Directory (/ , /providers/)
└── Provider Detail (/providers/<slug>/)
    ├── About
    ├── Pricing
    ├── Preferences
    ├── Gallery
    └── Reviews  ──> submit review / reply (login required)
```

---

## 7. Responsive & accessibility

Tailwind CSS (CDN) with a dark theme; grid collapses from 4 → 2 → 1 columns.
`location-autocomplete.js` provides keyboard navigation and ARIA attributes;
images carry alt text and touch targets are ≥44 px.

---

## 8. Errors & empty states

- **Provider not found (404)**: missing slug, inactive, or unverified.
- **No providers**: empty-state message in the directory.
- **No reviews yet**: empty-state on the profile; invites the visitor to sign in
  and review.

---

## 9. Manual test checklist

1. `/providers/` shows only active, verified providers; pagination works.
2. Each filter narrows results; autocomplete returns countries/cities.
3. Profiles load gallery, pricing grid, preferences and reviews; inactive or
   unverified slugs 404.
4. As a client, submit a review (per-category ratings) and confirm it appears;
   attempt to submit twice and confirm the uniqueness rule.

Automated coverage runs via `./test.sh` (see
[`../CONTRIBUTING.md`](../CONTRIBUTING.md#4-testing-requirements)).
