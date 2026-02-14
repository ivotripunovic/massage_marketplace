import json
import logging
import urllib.request
import urllib.parse

logger = logging.getLogger(__name__)


def geocode_location(district, city, country):
    """Geocode a location string via Nominatim (OpenStreetMap).

    Returns (latitude, longitude) as floats, or None on failure.
    """
    parts = [p for p in (district, city, country) if p]
    if not parts:
        return None

    query = ", ".join(parts)
    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": "1"})
    url = f"https://nominatim.openstreetmap.org/search?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "MassageMarketplace/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        logger.warning("Geocoding failed for %r", query, exc_info=True)

    return None
