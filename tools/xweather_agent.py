"""
tools/xweather_agent.py — XWeather (AerisWeather) weather provider.

Uses the AerisWeather /conditions/ endpoint.
15,000 requests / month on the free tier.

Credentials: XWEATHER_CLIENT_ID + XWEATHER_CLIENT_SECRET from .env.
The full key string uses underscore as delimiter: clientId_clientSecret.

Falls back gracefully (returns None) so tool_router can try wttr.in next.
"""
from __future__ import annotations

import os
from typing import Optional

_CLIENT_ID_ENV     = "XWEATHER_CLIENT_ID"
_CLIENT_SECRET_ENV = "XWEATHER_CLIENT_SECRET"
_BASE_URL          = "https://api.aerisapi.com/conditions"

_CITY_ALIASES: dict[str, str] = {
    "london":      "london,gb",
    "manchester":  "manchester,gb",
    "birmingham":  "birmingham,gb",
    "glasgow":     "glasgow,gb",
    "edinburgh":   "edinburgh,gb",
    "bristol":     "bristol,gb",
    "leeds":       "leeds,gb",
    "liverpool":   "liverpool,gb",
    "new york":    "new-york,ny",
    "los angeles": "los-angeles,ca",
    "toronto":     "toronto,on",
    "sydney":      "sydney,nsw",
    "paris":       "paris,fr",
    "berlin":      "berlin,de",
    "tokyo":       "tokyo,jp",
    "dubai":       "dubai,ae",
}


def _credentials() -> tuple[str, str]:
    return (
        os.environ.get(_CLIENT_ID_ENV, "").strip(),
        os.environ.get(_CLIENT_SECRET_ENV, "").strip(),
    )


def is_available() -> bool:
    cid, csec = _credentials()
    return bool(cid and csec)


def _normalise_location(city: str) -> str:
    key = city.lower().strip()
    return _CITY_ALIASES.get(key, key.replace(" ", "-"))


def agent(query: str, city: str = "London") -> Optional[str]:
    """
    Fetch current conditions for *city* via XWeather conditions API.
    Returns a formatted string on success, None on any failure.
    """
    cid, csec = _credentials()
    if not (cid and csec):
        return None

    location = _normalise_location(city)
    try:
        import httpx
        resp = httpx.get(
            f"{_BASE_URL}/{location}",
            params={"client_id": cid, "client_secret": csec},
            timeout=8.0,
        )
        if resp.status_code in (400, 401, 403, 404):
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    try:
        if not data.get("success"):
            return None
        response = data.get("response")
        if not response:
            return None
        item = response[0] if isinstance(response, list) else response
        periods = item.get("periods", [])
        if not periods:
            return None
        ob = periods[0]

        display  = city.title()
        desc     = ob.get("weather") or ob.get("weatherPrimary")
        temp_c   = ob.get("tempC")
        feels_c  = ob.get("feelslikeC")
        humidity = ob.get("humidity")
        wind_kph = ob.get("windSpeedKPH")

        if temp_c is None or not desc:
            return None

        parts = [f"{desc}, {round(temp_c)}°C"]
        if feels_c is not None and round(feels_c) != round(temp_c):
            parts.append(f"feels like {round(feels_c)}°C")
        if humidity is not None:
            parts.append(f"humidity {round(humidity)}%")
        if wind_kph is not None:
            parts.append(f"wind {round(wind_kph)} km/h")

        return f"Weather in {display}: {', '.join(parts)}."
    except (KeyError, TypeError, IndexError):
        return None
