# Massage Marketplace — Provider Tours (Requirements)

**Status**: Implemented (migration `providers/0024_tour_stop`)
**Date**: 2026-11-10
**Apps affected**: `providers`, `clients`

---

## 1. Overview

Today a provider has exactly one location (`Provider.country` and `Provider.city`),
and the directory only matches providers on that location. Many providers
travel. They work in other countries and cities for a few days or weeks at a
time, and could serve clients anywhere in the world.

This feature lets a provider publish a **tour schedule**: a list of *tour stops*,
each one a city and a date range. Clients searching a city then find:

- providers **based** in that city, and
- providers **visiting** that city, with the visit dates shown.

This way a client can plan around when a provider is in their city.

Contact stays the same as today. The client calls the provider using the phone
details on the profile. No booking or request flow is added.

---

## 2. User stories

### Provider
- As a touring provider, I can add a tour stop (city + start date + end date +
  optional note), so that clients in that city can find me while I'm there.
- As a provider, I can see my current and upcoming stops and delete any of them.
- As a provider, I see my next stop on my dashboard.

### Client
- As a client searching my city, I see providers based here **and** providers
  visiting here. Visitors carry a badge with their dates.
- As a client, I can filter by the dates I need ("When"), so that I only see
  providers who are in my city during that period.
- As a client viewing a profile, I see the provider's tour schedule and whether
  they are currently away, so that I can plan around their arrival.

### Admin
- As an admin, I can view and edit a provider's tour stops in Django admin.

---

## 3. Business rules

| # | Rule |
|---|------|
| R1 | A tour stop is one **city** in an active country (the country comes from the city) plus an **inclusive** date range `start_date … end_date`. |
| R2 | `end_date ≥ start_date`. |
| R3 | `end_date` must not be in the past when the stop is created. Finished stops stay valid, so admin can still save them. |
| R4 | A single stop lasts at most **90 days**. |
| R5 | A provider's stops must not overlap each other. |
| R6 | A provider can have at most **20** current or upcoming stops. |
| R7 | Past stops (`end_date < today`) are never shown to clients. They are kept in the database. |
| R8 | Only providers that are already listable appear in search: active subscription and verified email. |
| R9 | While one of a provider's stops overlaps the search window, the provider is **hidden from their home city and country** results (see §4). |

---

## 4. Search semantics

The directory takes new optional parameters `date_from` and `date_to` (ISO
dates). Invalid values are ignored. If only `date_from` is given, `date_to`
equals `date_from`.

Two windows are used:

| Window | Dates given | No dates given |
|--------|-------------|----------------|
| **Tour-match**: decides whether a stop in the searched city counts | `[date_from, date_to]` | `[today, ∞)`, so all current and upcoming visits show |
| **Home-hiding**: decides whether the provider is away from home | `[date_from, date_to]` | `[today, today]` |

A stop overlaps a window when `start_date ≤ window_end AND end_date ≥ window_start`.

A provider matches a **city** search when either:

- their home city is the searched city **and** they have no stop overlapping the
  home-hiding window, **or**
- they have a stop in the searched city that overlaps the tour-match window.

A **country** search (no city chosen) works the same way, using the home
country and the stop's `city.country`.

With **no location** filter, every listable provider appears once. A provider
who is on tour today is labelled with their current stop.

Each provider appears **at most once** in the results, even with several
matching stops. The badge shows the earliest matching stop.

The provider counts in the country and city autocomplete also include
providers who have a current or upcoming stop there. Providers who are away
today are not counted at home, which matches a no-dates search.

### Examples (today = 1 Dec; provider based in Belgrade, stop in Paris 10–20 Dec)

| Search | Dates | Shown? | Badge |
|--------|-------|--------|-------|
| Paris | none | Yes | "Visiting 10–20 Dec" |
| Paris | 12–14 Dec | Yes | "Visiting 10–20 Dec" |
| Paris | 22–25 Dec | No | — |
| Belgrade | none | Yes (not away today) | — |
| Belgrade | 12–14 Dec | **No** (away) | — |
| Belgrade | 22–25 Dec | Yes | — |
| France | none | Yes | "Visiting Paris 10–20 Dec" |

---

## 5. UI requirements

### Provider portal
- **Manage tour** page at `/provider/tour/`, for providers only:
  - Add-stop form: country → city autocomplete (same picker as the directory),
    start date, end date, optional note (≤200 chars).
  - List of current and upcoming stops, each with a delete button (POST).
  - Validation errors for R2–R6 shown in the form.
- **Dashboard** card "Tour schedule": the next or current stop and a
  "Manage tour" link.

### Directory (`/providers/`)
- A "When" date-range input (from / to) in the desktop and mobile search bars,
  kept when filtering and paginating.
- A badge on the provider card:
  - "Here now · until 18 Dec" when the stop is current
  - "Visiting 12–18 Dec" when the stop is upcoming
  - With no location filter: "On tour: Paris until 18 Dec" if the provider is
    away today

### Provider profile (`/providers/<slug>/`)
- A "Tour schedule" section listing current and upcoming stops (city, country,
  dates, note).
- A banner "Currently in X until <date>" when a stop is current.

---

## 6. Out of scope

- Booking, or clients requesting a visit to their city
- Notifying clients when a provider plans a stop in their city
- Moving the profile map to the tour city (the map stays on the home location)
- Recurring or repeating tours
- Editing a stop in place (delete and re-add instead)

---

## 6a. Implementation map

| Concern | Location |
|---------|----------|
| Model, validation, `overlapping()` / `upcoming()` | `providers/models.py` (`TourStop`, `TourStopQuerySet`) |
| Add-stop form (R6 limit) | `providers/forms.py` (`TourStopForm`) |
| Provider pages | `providers/views.py` (`TourStopListCreateView`, `TourStopDeleteView`), `templates/providers/tour_manage.html` |
| Search windows and filtering | `clients/tour_search.py` (`parse_search_window`, `apply_location_filter`, `attach_tour_stops`, `provider_counts_by`) |
| Directory and profile UI | `templates/clients/provider_list.html`, `templates/includes/_tour_badge.html`, `templates/clients/provider_detail.html` |
| Admin | `providers/admin.py` (`TourStopInline`) |
| Tests | `providers/test_tours.py`, `clients/test_tours.py` (both run by `./test.sh`) |

---

## 7. Data model (summary)

New model `providers.TourStop`:

| Field | Type | Notes |
|-------|------|-------|
| `provider` | FK → Provider | `related_name="tour_stops"`, CASCADE |
| `city` | FK → City | PROTECT. The country is `city.country`. |
| `start_date` | Date | inclusive |
| `end_date` | Date | inclusive |
| `note` | Char(200) | optional |
| `created_at` | DateTime | auto |

Indexes: `(city, end_date)`, `(provider, start_date)`.

---

## 8. Acceptance criteria

- [x] A provider can add a valid stop, which then appears in their list and on their dashboard.
- [x] Stops that break R2–R6 are rejected with a clear form error.
- [x] A provider cannot delete another provider's stop. Non-providers cannot reach `/provider/tour/`.
- [x] A visiting provider appears in the tour city's results during the window, with the correct badge.
- [x] A visiting provider is hidden from their home city and country during an overlapping stop, and shown there outside it.
- [x] With no dates, current and upcoming visits appear and past ones don't.
- [x] Country-level search behaves like city-level search.
- [x] Invalid `date_from` or `date_to` values are ignored without an error.
- [x] A provider with several matching stops appears only once.
- [x] The profile page shows the tour schedule and the "Currently in" banner.
- [x] Inactive or unverified providers never appear, whatever their stops.
- [x] The date filter is kept when filtering and paginating.
