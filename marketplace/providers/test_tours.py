"""Tests for provider tour stops (docs/PROVIDER_TOURS.md)."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User

from .forms import TourStopForm
from .models import City, Continent, Country, Provider, TourStop


def make_location():
    continent = Continent.objects.create(name="Europe", code="EU")
    serbia = Country.objects.create(name="Serbia", code="RS", continent=continent)
    france = Country.objects.create(name="France", code="FR", continent=continent)
    belgrade = City.objects.create(name="Belgrade", country=serbia)
    paris = City.objects.create(name="Paris", country=france)
    lyon = City.objects.create(name="Lyon", country=france)
    return {
        "serbia": serbia,
        "france": france,
        "belgrade": belgrade,
        "paris": paris,
        "lyon": lyon,
    }


def make_provider(email="provider@test.com", **kwargs):
    user = User.objects.create_user(
        email=email,
        password="testpass123",
        user_type="provider",
        is_email_verified=True,
    )
    return Provider.objects.create(user=user, phone="+381111111", **kwargs)


class TourStopModelTests(TestCase):
    def setUp(self):
        self.loc = make_location()
        self.provider = make_provider()
        self.today = timezone.localdate()

    def _stop(self, start, end, city=None):
        return TourStop(
            provider=self.provider,
            city=city or self.loc["paris"],
            start_date=self.today + timedelta(days=start),
            end_date=self.today + timedelta(days=end),
        )

    def test_valid_stop(self):
        self._stop(1, 5).full_clean()

    def test_single_day_stop_is_valid(self):
        self._stop(0, 0).full_clean()

    def test_end_before_start_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self._stop(5, 1).full_clean()
        self.assertIn("end_date", ctx.exception.message_dict)

    def test_past_end_date_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            self._stop(-5, -1).full_clean()
        self.assertIn("past", str(ctx.exception))

    def test_existing_past_stop_can_be_revalidated(self):
        """Regression: admin inlines re-validate finished stops on every save."""
        stop = self._stop(-10, -5)
        stop.save()
        stop.full_clean()

    def test_stop_already_started_is_allowed(self):
        self._stop(-3, 3).full_clean()

    def test_max_duration(self):
        self._stop(0, TourStop.MAX_DURATION_DAYS - 1).full_clean()
        with self.assertRaises(ValidationError):
            self._stop(0, TourStop.MAX_DURATION_DAYS).full_clean()

    def test_overlap_with_own_stop_rejected(self):
        self._stop(1, 5).save()
        with self.assertRaises(ValidationError) as ctx:
            self._stop(5, 8, city=self.loc["lyon"]).full_clean()
        self.assertIn("Paris", str(ctx.exception))

    def test_adjacent_stops_allowed(self):
        self._stop(1, 5).save()
        self._stop(6, 8).full_clean()

    def test_other_providers_stops_do_not_clash(self):
        self._stop(1, 5).save()
        other = make_provider("other@test.com")
        TourStop(
            provider=other,
            city=self.loc["paris"],
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=5),
        ).full_clean()

    def test_overlapping_queryset(self):
        stop = self._stop(5, 10)
        stop.save()
        qs = TourStop.objects.all()
        d = self.today
        self.assertIn(
            stop, qs.overlapping(d + timedelta(days=10), d + timedelta(days=12))
        )
        self.assertIn(stop, qs.overlapping(d, d + timedelta(days=5)))
        self.assertNotIn(stop, qs.overlapping(d, d + timedelta(days=4)))
        self.assertNotIn(
            stop, qs.overlapping(d + timedelta(days=11), d + timedelta(days=20))
        )
        self.assertIn(stop, qs.overlapping(d))  # open-ended

    def test_upcoming_excludes_past(self):
        past = self._stop(-10, -5)
        past.save()  # bypasses clean(): historical rows can exist
        current = self._stop(-1, 1)
        current.save()
        self.assertEqual(list(TourStop.objects.upcoming()), [current])

    def test_is_current(self):
        self.assertTrue(self._stop(-1, 1).is_current)
        self.assertFalse(self._stop(1, 2).is_current)


class TourStopFormTests(TestCase):
    def setUp(self):
        self.loc = make_location()
        self.provider = make_provider()
        self.today = timezone.localdate()

    def _data(self, start=1, end=3, city=None):
        return {
            "city": (city or self.loc["paris"]).pk,
            "start_date": (self.today + timedelta(days=start)).isoformat(),
            "end_date": (self.today + timedelta(days=end)).isoformat(),
            "note": "Hotel visits only",
        }

    def test_valid(self):
        form = TourStopForm(data=self._data(), provider=self.provider)
        self.assertTrue(form.is_valid(), form.errors)

    def test_city_required(self):
        data = self._data()
        data["city"] = ""
        form = TourStopForm(data=data, provider=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn("city", form.errors)

    def test_city_in_inactive_country_rejected(self):
        self.loc["france"].is_active = False
        self.loc["france"].save()
        form = TourStopForm(data=self._data(), provider=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn("city", form.errors)

    def test_overlap_is_non_field_error(self):
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["lyon"],
            start_date=self.today + timedelta(days=2),
            end_date=self.today + timedelta(days=4),
        )
        form = TourStopForm(data=self._data(), provider=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn("Lyon", str(form.non_field_errors()))

    def test_upcoming_limit(self):
        for i in range(TourStop.MAX_UPCOMING_STOPS):
            TourStop.objects.create(
                provider=self.provider,
                city=self.loc["paris"],
                start_date=self.today + timedelta(days=10 + i),
                end_date=self.today + timedelta(days=10 + i),
            )
        form = TourStopForm(data=self._data(), provider=self.provider)
        self.assertFalse(form.is_valid())
        self.assertIn("at most", str(form.non_field_errors()))

    def test_past_stops_do_not_count_toward_limit(self):
        for i in range(TourStop.MAX_UPCOMING_STOPS):
            TourStop.objects.create(
                provider=self.provider,
                city=self.loc["paris"],
                start_date=self.today - timedelta(days=100 + i),
                end_date=self.today - timedelta(days=100 + i),
            )
        form = TourStopForm(data=self._data(), provider=self.provider)
        self.assertTrue(form.is_valid(), form.errors)


class TourStopViewTests(TestCase):
    def setUp(self):
        self.loc = make_location()
        self.provider = make_provider()
        self.today = timezone.localdate()
        self.client.login(email="provider@test.com", password="testpass123")
        self.url = reverse("tour_manage")

    def _post(self, start=1, end=3):
        return self.client.post(
            self.url,
            {
                "city": self.loc["paris"].pk,
                "start_date": (self.today + timedelta(days=start)).isoformat(),
                "end_date": (self.today + timedelta(days=end)).isoformat(),
            },
        )

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_clients_cannot_access(self):
        User.objects.create_user(
            email="client@test.com",
            password="testpass123",
            user_type="client",
            is_email_verified=True,
        )
        self.client.login(email="client@test.com", password="testpass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_lists_upcoming_only(self):
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["lyon"],
            start_date=self.today - timedelta(days=10),
            end_date=self.today - timedelta(days=5),
        )
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today + timedelta(days=1),
            end_date=self.today + timedelta(days=2),
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tour_stops"]), 1)
        self.assertContains(response, "Paris, France")
        self.assertNotContains(response, "Lyon, France")

    def test_create_stop(self):
        response = self._post()
        self.assertRedirects(response, self.url)
        stop = TourStop.objects.get()
        self.assertEqual(stop.provider, self.provider)
        self.assertEqual(stop.city, self.loc["paris"])

    def test_invalid_post_rerenders_with_city(self):
        response = self._post(start=5, end=1)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(TourStop.objects.exists())
        self.assertEqual(response.context["selected_city"], self.loc["paris"])

    def test_delete_own_stop(self):
        stop = TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today,
            end_date=self.today,
        )
        response = self.client.post(reverse("tour_delete", args=[stop.pk]))
        self.assertRedirects(response, self.url)
        self.assertFalse(TourStop.objects.exists())

    def test_cannot_delete_other_providers_stop(self):
        other = make_provider("other@test.com")
        stop = TourStop.objects.create(
            provider=other,
            city=self.loc["paris"],
            start_date=self.today,
            end_date=self.today,
        )
        response = self.client.post(reverse("tour_delete", args=[stop.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(TourStop.objects.filter(pk=stop.pk).exists())

    def test_delete_requires_post(self):
        stop = TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today,
            end_date=self.today,
        )
        response = self.client.get(reverse("tour_delete", args=[stop.pk]))
        self.assertEqual(response.status_code, 405)

    def test_dashboard_shows_next_stop(self):
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today + timedelta(days=3),
            end_date=self.today + timedelta(days=4),
        )
        response = self.client.get(reverse("provider_dashboard"))
        self.assertContains(response, "Next stop")
        self.assertContains(response, "Paris, France")

    def test_dashboard_shows_current_stop(self):
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today - timedelta(days=1),
            end_date=self.today + timedelta(days=1),
        )
        response = self.client.get(reverse("provider_dashboard"))
        self.assertEqual(response.context["next_tour_stop"].city, self.loc["paris"])
        self.assertContains(response, "Currently in")
        self.assertNotContains(response, "Next stop")

    def test_dashboard_empty_state_ignores_past_stops(self):
        TourStop.objects.create(
            provider=self.provider,
            city=self.loc["paris"],
            start_date=self.today - timedelta(days=10),
            end_date=self.today - timedelta(days=5),
        )
        response = self.client.get(reverse("provider_dashboard"))
        self.assertIsNone(response.context["next_tour_stop"])
        self.assertContains(response, "No upcoming tour stops")
        self.assertContains(response, reverse("tour_manage"))


class TourStopAdminTests(TestCase):
    def test_provider_with_past_stop_saves_in_admin(self):
        """Regression: a finished stop must not block saving its provider."""
        loc = make_location()
        provider = make_provider(country=loc["serbia"], city=loc["belgrade"])
        today = timezone.localdate()
        stop = TourStop.objects.create(
            provider=provider,
            city=loc["paris"],
            start_date=today - timedelta(days=10),
            end_date=today - timedelta(days=5),
        )
        admin = User.objects.create_superuser(email="admin@test.com", password="pw")
        self.client.force_login(admin)
        url = reverse("admin:providers_provider_change", args=[provider.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = {
            "user": provider.user_id,
            "bio": "Updated",
            "phone": provider.phone,
            "country": loc["serbia"].pk,
            "city": loc["belgrade"].pk,
            "subscription_status": "inactive",
            "subscription_payment_method": "",
            "subscription_renewal_date": "",
            "crypto_address": "",
            # Gallery inline: no rows.
            "gallery_images-TOTAL_FORMS": "0",
            "gallery_images-INITIAL_FORMS": "0",
            # Tour inline: the existing, unchanged past stop.
            "tour_stops-TOTAL_FORMS": "1",
            "tour_stops-INITIAL_FORMS": "1",
            "tour_stops-0-id": stop.pk,
            "tour_stops-0-provider": provider.pk,
            "tour_stops-0-city": loc["paris"].pk,
            "tour_stops-0-start_date": stop.start_date.isoformat(),
            "tour_stops-0-end_date": stop.end_date.isoformat(),
            "tour_stops-0-note": "",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        provider.refresh_from_db()
        self.assertEqual(provider.bio, "Updated")
        self.assertTrue(TourStop.objects.filter(pk=stop.pk).exists())
