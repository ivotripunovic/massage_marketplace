"""Location + date search rules for touring providers.

Implements §4 "Search semantics" of docs/PROVIDER_TOURS.md:

* tour-match window  – client's dates, or [today, ∞) when none given
* home-hiding window – client's dates, or [today, today] when none given

A provider matches a location when they are based there and have no stop
overlapping the home-hiding window, or when they have a stop there that
overlaps the tour-match window.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from django.db.models import Exists, OuterRef, Q, Subquery
from django.utils import timezone

from providers.models import Provider, TourStop


@dataclass(frozen=True)
class SearchWindow:
    """Date window a client is searching for."""

    date_from: date
    date_to: date | None  # None = open-ended
    dates_given: bool

    @property
    def home_from(self):
        return self.date_from

    @property
    def home_to(self):
        # Without explicit dates, "away" means away *today*.
        return self.date_to if self.dates_given else self.date_from


def _parse_date(value):
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def parse_search_window(params, today=None):
    """Build a SearchWindow from GET params; invalid values are ignored.

    Dates before today are clamped to today (past stops are never shown),
    and a reversed range is swapped.
    """
    today = today or timezone.localdate()
    date_from = _parse_date(params.get("date_from"))
    date_to = _parse_date(params.get("date_to"))

    if date_from is None and date_to is None:
        return SearchWindow(today, None, dates_given=False)

    if date_from is None:
        date_from = date_to
    if date_to is None:
        date_to = date_from
    if date_to < date_from:
        date_from, date_to = date_to, date_from

    date_from = max(date_from, today)
    date_to = max(date_to, date_from)
    return SearchWindow(date_from, date_to, dates_given=True)


def apply_location_filter(queryset, window, country_id=None, city_id=None):
    """Filter providers by home location or tour stop, and annotate badges.

    Adds a ``tour_stop_id`` annotation: the earliest stop that explains the
    match (or, with no location filter, the stop the provider is on during
    the home-hiding window). It is ``None`` for providers matched at home.
    """
    stops = TourStop.objects.filter(provider=OuterRef("pk"))
    away_stops = stops.overlapping(window.home_from, window.home_to)

    if city_id is not None:
        home_q = Q(city_id=city_id)
        match_stops = stops.overlapping(window.date_from, window.date_to).filter(
            city_id=city_id
        )
    elif country_id is not None:
        home_q = Q(country_id=country_id)
        match_stops = stops.overlapping(window.date_from, window.date_to).filter(
            city__country_id=country_id
        )
    else:
        # No location: everyone is listed; label those currently away.
        return queryset.annotate(
            tour_stop_id=Subquery(away_stops.order_by("start_date").values("pk")[:1])
        )

    return queryset.annotate(
        is_away=Exists(away_stops),
        tours_here=Exists(match_stops),
        tour_stop_id=Subquery(match_stops.order_by("start_date").values("pk")[:1]),
    ).filter((home_q & Q(is_away=False)) | Q(tours_here=True))


def attach_tour_stops(providers):
    """Set ``provider.tour_stop`` from the ``tour_stop_id`` annotation (1 query)."""
    ids = {p.tour_stop_id for p in providers if getattr(p, "tour_stop_id", None)}
    stops = {}
    if ids:
        stops = {
            s.pk: s
            for s in TourStop.objects.filter(pk__in=ids).select_related("city__country")
        }
    for p in providers:
        p.tour_stop = stops.get(getattr(p, "tour_stop_id", None))


def provider_counts_by(field, country_id=None):
    """Count distinct listable providers per ``"city"`` or ``"country"``.

    A provider counts for every location of a current or upcoming tour stop,
    and for their home location unless they are away today (matching the
    directory's no-dates search). Each provider counts once per location.
    """
    today = timezone.localdate()
    listable = Provider.objects.filter(
        subscription_status="active", user__is_email_verified=True
    )
    stops = TourStop.objects.upcoming().filter(provider__in=listable)
    at_home = listable.exclude(
        Exists(
            TourStop.objects.filter(provider=OuterRef("pk")).overlapping(today, today)
        )
    )
    if country_id is not None:
        at_home = at_home.filter(country_id=country_id)
        stops = stops.filter(city__country_id=country_id)

    stop_field = "city_id" if field == "city" else "city__country_id"
    pairs = set(
        at_home.filter(**{f"{field}__isnull": False}).values_list("id", f"{field}_id")
    )
    pairs |= set(stops.values_list("provider_id", stop_field))

    counts = defaultdict(int)
    for _provider_id, location_id in pairs:
        counts[location_id] += 1
    return counts
