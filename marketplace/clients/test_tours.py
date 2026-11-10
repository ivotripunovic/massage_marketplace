"""Directory search tests for touring providers (docs/PROVIDER_TOURS.md §4)."""

from datetime import date, timedelta

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.tour_search import parse_search_window
from providers.models import TourStop
from providers.test_tours import make_location, make_provider


class ParseSearchWindowTests(TestCase):
    today = date(2026, 12, 1)

    def test_no_dates(self):
        w = parse_search_window({}, today=self.today)
        self.assertEqual(
            (w.date_from, w.date_to, w.dates_given), (self.today, None, False)
        )
        self.assertEqual((w.home_from, w.home_to), (self.today, self.today))

    def test_both_dates(self):
        w = parse_search_window(
            {"date_from": "2026-12-12", "date_to": "2026-12-14"}, today=self.today
        )
        self.assertEqual(
            (w.date_from, w.date_to), (date(2026, 12, 12), date(2026, 12, 14))
        )
        self.assertEqual((w.home_from, w.home_to), (w.date_from, w.date_to))

    def test_only_from(self):
        w = parse_search_window({"date_from": "2026-12-12"}, today=self.today)
        self.assertEqual(w.date_from, w.date_to)

    def test_reversed_range_swapped(self):
        w = parse_search_window(
            {"date_from": "2026-12-14", "date_to": "2026-12-12"}, today=self.today
        )
        self.assertEqual(
            (w.date_from, w.date_to), (date(2026, 12, 12), date(2026, 12, 14))
        )

    def test_past_dates_clamped_to_today(self):
        w = parse_search_window(
            {"date_from": "2026-01-01", "date_to": "2026-01-05"}, today=self.today
        )
        self.assertEqual((w.date_from, w.date_to), (self.today, self.today))

    def test_invalid_dates_ignored(self):
        w = parse_search_window(
            {"date_from": "not-a-date", "date_to": "2026-13-45"}, today=self.today
        )
        self.assertFalse(w.dates_given)


class TourDirectorySearchTests(TestCase):
    """Provider based in Belgrade, touring Paris on days +10..+20."""

    def setUp(self):
        cache.clear()
        self.loc = make_location()
        self.today = timezone.localdate()
        self.touring = make_provider(
            "touring@test.com",
            country=self.loc["serbia"],
            city=self.loc["belgrade"],
            subscription_status="active",
        )
        self.stop = TourStop.objects.create(
            provider=self.touring,
            city=self.loc["paris"],
            start_date=self.today + timedelta(days=10),
            end_date=self.today + timedelta(days=20),
        )
        self.local = make_provider(
            "local@test.com",
            country=self.loc["france"],
            city=self.loc["paris"],
            subscription_status="active",
        )

    def _day(self, n):
        return (self.today + timedelta(days=n)).isoformat()

    def _search(self, **params):
        response = self.client.get(reverse("providers"), params)
        self.assertEqual(response.status_code, 200)
        return response, {p.pk: p for p in response.context["providers"]}

    def test_tour_city_no_dates_shows_upcoming_visit(self):
        response, found = self._search(city_id=self.loc["paris"].pk)
        self.assertEqual(set(found), {self.touring.pk, self.local.pk})
        self.assertEqual(found[self.touring.pk].tour_stop, self.stop)
        self.assertIsNone(found[self.local.pk].tour_stop)
        self.assertContains(response, "Visiting")

    def test_tour_city_within_window(self):
        _, found = self._search(
            city_id=self.loc["paris"].pk, date_from=self._day(12), date_to=self._day(14)
        )
        self.assertIn(self.touring.pk, found)

    def test_tour_city_outside_window(self):
        _, found = self._search(
            city_id=self.loc["paris"].pk, date_from=self._day(22), date_to=self._day(25)
        )
        self.assertEqual(set(found), {self.local.pk})

    def test_home_city_today_not_away(self):
        _, found = self._search(city_id=self.loc["belgrade"].pk)
        self.assertIn(self.touring.pk, found)
        self.assertIsNone(found[self.touring.pk].tour_stop)

    def test_home_city_hidden_while_away(self):
        _, found = self._search(
            city_id=self.loc["belgrade"].pk,
            date_from=self._day(12),
            date_to=self._day(14),
        )
        self.assertNotIn(self.touring.pk, found)

    def test_home_city_after_tour(self):
        _, found = self._search(
            city_id=self.loc["belgrade"].pk,
            date_from=self._day(22),
            date_to=self._day(25),
        )
        self.assertIn(self.touring.pk, found)

    def test_home_hidden_today_when_tour_is_current(self):
        self.stop.start_date = self.today
        self.stop.save()
        response, found = self._search(city_id=self.loc["belgrade"].pk)
        self.assertNotIn(self.touring.pk, found)
        response, found = self._search(city_id=self.loc["paris"].pk)
        self.assertContains(response, "Here now")

    def test_country_search(self):
        response, found = self._search(country_id=self.loc["france"].pk)
        self.assertEqual(set(found), {self.touring.pk, self.local.pk})
        self.assertContains(response, "Visiting Paris")
        _, found = self._search(
            country_id=self.loc["serbia"].pk,
            date_from=self._day(12),
            date_to=self._day(14),
        )
        self.assertNotIn(self.touring.pk, found)

    def test_past_stops_never_match(self):
        self.stop.start_date = self.today - timedelta(days=10)
        self.stop.end_date = self.today - timedelta(days=1)
        self.stop.save()
        _, found = self._search(city_id=self.loc["paris"].pk)
        self.assertEqual(set(found), {self.local.pk})

    def test_multiple_matching_stops_listed_once(self):
        TourStop.objects.create(
            provider=self.touring,
            city=self.loc["lyon"],
            start_date=self.today + timedelta(days=25),
            end_date=self.today + timedelta(days=26),
        )
        TourStop.objects.create(
            provider=self.touring,
            city=self.loc["paris"],
            start_date=self.today + timedelta(days=30),
            end_date=self.today + timedelta(days=31),
        )
        response, found = self._search(country_id=self.loc["france"].pk)
        ids = [p.pk for p in response.context["providers"]]
        self.assertEqual(ids.count(self.touring.pk), 1)
        self.assertEqual(found[self.touring.pk].tour_stop, self.stop)  # earliest

    def test_inactive_provider_never_listed(self):
        self.touring.subscription_status = "inactive"
        self.touring.save()
        _, found = self._search(city_id=self.loc["paris"].pk)
        self.assertNotIn(self.touring.pk, found)

    def test_no_location_lists_everyone_once_with_current_tour(self):
        self.stop.start_date = self.today
        self.stop.save()
        response, found = self._search()
        self.assertEqual(set(found), {self.touring.pk, self.local.pk})
        self.assertContains(response, "On tour: Paris")

    def test_invalid_city_id_keeps_city_in_badge(self):
        """Regression: an ignored city filter must not hide the badge's city."""
        self.stop.start_date = self.today
        self.stop.save()
        response, found = self._search(city_id="abc")
        self.assertIn(self.touring.pk, found)
        self.assertContains(response, "On tour: Paris")
        self.assertNotContains(response, "Here now")

    def test_invalid_dates_ignored(self):
        _, found = self._search(city_id=self.loc["paris"].pk, date_from="garbage")
        self.assertIn(self.touring.pk, found)

    def test_dates_kept_in_filter_params(self):
        response, _ = self._search(
            city_id=self.loc["paris"].pk, date_from=self._day(12), date_to=self._day(14)
        )
        self.assertIn(
            f"date_from={self._day(12)}", response.context["base_filter_params"]
        )
        self.assertEqual(response.context["current_date_to"], self._day(14))


class TourLocationCountsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.loc = make_location()
        today = timezone.localdate()
        provider = make_provider(
            country=self.loc["serbia"],
            city=self.loc["belgrade"],
            subscription_status="active",
        )
        TourStop.objects.create(
            provider=provider,
            city=self.loc["paris"],
            start_date=today,
            end_date=today + timedelta(days=2),
        )

    def _city_counts(self, country):
        response = self.client.get(
            reverse("api_city_search"), {"country": country.pk, "all": "1"}
        )
        return {c["name"]: c["provider_count"] for c in response.json()["results"]}

    def test_away_provider_not_counted_at_home(self):
        """Regression: counts match the directory, which hides away providers."""
        self.assertEqual(self._city_counts(self.loc["serbia"])["Belgrade"], 0)

    def test_future_tour_still_counted_at_home(self):
        today = timezone.localdate()
        TourStop.objects.update(
            start_date=today + timedelta(days=5), end_date=today + timedelta(days=6)
        )
        self.assertEqual(self._city_counts(self.loc["serbia"])["Belgrade"], 1)

    def test_city_counts_include_tour_stops(self):
        response = self.client.get(
            reverse("api_city_search"), {"country": self.loc["france"].pk, "all": "1"}
        )
        counts = {c["name"]: c["provider_count"] for c in response.json()["results"]}
        self.assertEqual(counts["Paris"], 1)
        self.assertEqual(counts["Lyon"], 0)

    def test_country_counts_include_tour_stops(self):
        response = self.client.get(reverse("api_country_search"), {"all": "1"})
        counts = {
            c["name"]: c["provider_count"]
            for continent in response.json()["continents"]
            for c in continent["countries"]
        }
        # Away in Paris today: counted in France, not at home in Serbia.
        self.assertEqual(counts, {"Serbia": 0, "France": 1})


class ProviderDetailTourTests(TestCase):
    def test_schedule_and_current_banner(self):
        loc = make_location()
        today = timezone.localdate()
        provider = make_provider(
            country=loc["serbia"], city=loc["belgrade"], subscription_status="active"
        )
        TourStop.objects.create(
            provider=provider,
            city=loc["paris"],
            start_date=today,
            end_date=today,
            note="Hotel visits only",
        )
        TourStop.objects.create(
            provider=provider,
            city=loc["lyon"],
            start_date=today - timedelta(days=9),
            end_date=today - timedelta(days=8),
        )
        response = self.client.get(provider.get_absolute_url())
        self.assertContains(response, "Tour Schedule")
        self.assertContains(response, "Currently in")
        self.assertContains(response, "Hotel visits only")
        self.assertNotContains(response, "Lyon")
