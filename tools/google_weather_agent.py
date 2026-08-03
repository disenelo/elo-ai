"""
tools/google_weather_agent.py — Google Weather API provider.

Uses:
  - Google Weather API  (currentConditions:lookup, key = GOOGLE_WEATHER_API_KEY)
  - Nominatim / OSM    (free geocoder: city name → lat/lon, no key required)

Priority: explicit city → session/env location → London default.
Falls back gracefully (returns None) so tool_router can try wttr.in next.
"""
from __future__ import annotations

import os
import re
from typing import Optional

_API_KEY_ENV = "GOOGLE_WEATHER_API_KEY"
_WEATHER_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"
_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
_UA          = "eLo-OS/1.0 dcharles@disenelo.com"

# Cached geocode results to avoid hammering Nominatim on repeated queries
_geocode_cache: dict[str, tuple[float, float]] = {}

# Inline lat/lon for the most common cities — avoids a Nominatim round-trip
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "london":     (51.5074, -0.1278),
    "manchester": (53.4808, -2.2426),
    "birmingham": (52.4862, -1.8904),
    "glasgow":    (55.8642, -4.2518),
    "edinburgh":  (55.9533, -3.1883),
    "bristol":    (51.4545, -2.5879),
    "leeds":      (53.8008, -1.5491),
    "liverpool":  (53.4084, -2.9916),
    "paris":      (48.8566,  2.3522),
    "berlin":     (52.5200, 13.4050),
    "tokyo":      (35.6762, 139.6503),
    "new york":   (40.7128, -74.0060),
    "los angeles":(34.0522, -118.2437),
    "sydney":     (-33.8688, 151.2093),
    "dubai":      (25.2048,  55.2708),
    "toronto":    (43.6532, -79.3832),
}


def _api_key() -> str:
    return os.environ.get(_API_KEY_ENV, "").strip()


def is_available() -> bool:
    return bool(_api_key())


def _geocode(city: str) -> Optional[tuple[float, float]]:
    """Return (lat, lon) for a city name. None if not found."""
    key = city.lower().strip()

    # Inline fast lookup first
    if key in _CITY_COORDS:
        return _CITY_COORDS[key]

    # Normalise comma-district forms: "London, Hackney Wick" → full string is fine for Nominatim
    if key in _geocode_cache:
        return _geocode_cache[key]

    try:
        import httpx
        resp = httpx.get(
            _GEOCODE_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": _UA},
            timeout=6.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            _geocode_cache[key] = (lat, lon)
            return lat, lon
    except Exception:
        pass
    return None


def _condition_text(cond: dict) -> str:
    """Extract a human-readable description from the weatherCondition block."""
    try:
        return cond["description"]["text"]
    except (KeyError, TypeError):
        t = cond.get("type", "")
        return t.replace("_", " ").title() if t else "Unknown"


def agent(query: str, city: str = "London") -> Optional[str]:
    """
    Fetch current weather for *city* using the Google Weather API.
    Returns a formatted string on success, None on any failure.
    """
    key = _api_key()
    if not key:
        return None

    coords = _geocode(city)
    if coords is None:
        return None

    lat, lon = coords
    try:
        import httpx
        resp = httpx.get(
            _WEATHER_URL,
            params={"key": key, "location.latitude": lat, "location.longitude": lon},
            timeout=8.0,
        )
        if resp.status_code == 404:
            return None  # location not covered — caller falls back to wttr.in
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    try:
        desc    = _condition_text(data.get("weatherCondition", {}))
        temp    = round(data["temperature"]["degrees"])
        feels   = round(data["feelsLikeTemperature"]["degrees"])
        # relativeHumidity is a bare int in the API response
        humid   = data.get("relativeHumidity")
        wind_sp = data.get("wind", {}).get("speed", {}).get("value")

        humid_str = f", humidity {round(humid)}%" if humid is not None else ""
        wind_kh   = f", wind {round(wind_sp)} km/h" if wind_sp is not None else ""

        display = city.title()
        return (f"Weather in {display}: {desc}, {temp}°C"
                f", feels like {feels}°C{humid_str}{wind_kh}.")
    except (KeyError, TypeError):
        return None
