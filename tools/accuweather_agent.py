"""
tools/accuweather_agent.py — AccuWeather current conditions + 1-day forecast.

Primary weather source for eLo OS. Falls back gracefully to wttr.in if the
key is missing or the request fails.

API key: ACCUWEATHER_API_KEY in .env
"""
from __future__ import annotations

import os
import re
import time
import httpx

_BASE    = "https://dataservice.accuweather.com"
_TIMEOUT = 8.0


def _api_key() -> str:
    return os.getenv("ACCUWEATHER_API_KEY", "").strip()

# Location key cache — avoids a round-trip on every weather query
_loc_cache: dict[str, tuple[str, str, float]] = {}   # city → (key, display_name, ts)
_LOC_TTL  = 3600 * 6   # 6 hours


def _location_key(city: str) -> tuple[str, str]:
    """
    Return (location_key, display_name) for a city string.
    Caches results for 6 hours. Raises on failure.
    """
    key_lower = city.strip().lower()
    cached = _loc_cache.get(key_lower)
    if cached and (time.time() - cached[2]) < _LOC_TTL:
        return cached[0], cached[1]

    resp = httpx.get(
        f"{_BASE}/locations/v1/cities/search",
        params={"apikey": _api_key(), "q": city, "language": "en-gb"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"No AccuWeather location found for: {city}")

    top = results[0]
    loc_key   = top["Key"]
    city_name = top["LocalizedName"]
    country   = top.get("Country", {}).get("LocalizedName", "")
    display   = f"{city_name}, {country}" if country else city_name

    _loc_cache[key_lower] = (loc_key, display, time.time())
    return loc_key, display


def _current_conditions(loc_key: str) -> dict:
    """Return raw current conditions dict from AccuWeather."""
    resp = httpx.get(
        f"{_BASE}/currentconditions/v1/{loc_key}",
        params={"apikey": _api_key(), "details": "true", "language": "en-gb"},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("Empty current conditions response")
    return data[0]


def _forecast_today(loc_key: str) -> dict | None:
    """Return today's 1-day forecast summary (high/low/headline). Silent on failure."""
    try:
        resp = httpx.get(
            f"{_BASE}/forecasts/v1/daily/1day/{loc_key}",
            params={"apikey": _api_key(), "metric": "true", "language": "en-gb"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        daily = data.get("DailyForecasts", [{}])[0]
        temp  = daily.get("Temperature", {})
        return {
            "headline": data.get("Headline", {}).get("Text", ""),
            "high":     temp.get("Maximum", {}).get("Value"),
            "low":      temp.get("Minimum", {}).get("Value"),
        }
    except Exception:
        return None


def _forecast_hourly(loc_key: str) -> list[dict]:
    """Return next 12 hours of hourly temps. Silent on failure."""
    try:
        resp = httpx.get(
            f"{_BASE}/forecasts/v1/hourly/12hour/{loc_key}",
            params={"apikey": _api_key(), "metric": "true", "language": "en-gb"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        hours = resp.json()
        result = []
        for h in hours:
            dt_str = h.get("DateTime", "")
            temp   = h.get("Temperature", {}).get("Value")
            phrase = h.get("IconPhrase", "")
            result.append({"dt": dt_str, "temp": temp, "phrase": phrase})
        return result
    except Exception:
        return []


def _condition_note(temp_c: float | None, uv: int | None, aqi_cat: str | None,
                    precip: bool, precip_t: str) -> str:
    """Plain-English advisory note for eLo to lean on. Not raw data."""
    notes = []
    if temp_c is not None:
        if temp_c >= 28:
            notes.append("hot — stay hydrated and get some sun if you can")
        elif temp_c >= 22:
            notes.append("warm and comfortable out")
        elif temp_c <= 5:
            notes.append("cold — wrap up")
        elif temp_c <= 12:
            notes.append("cool — jacket weather")
    if uv is not None and uv >= 6:
        notes.append("UV is high — sunscreen if you're out long")
    elif uv is not None and uv >= 3:
        notes.append("UV moderate")
    if aqi_cat and aqi_cat.lower() not in ("good", ""):
        notes.append(f"air quality is {aqi_cat.lower()}")
    if precip and precip_t:
        notes.append(f"{precip_t.lower()} coming — might want an umbrella")
    return "; ".join(notes)


def _city_short(display: str) -> str:
    """'London, United Kingdom' → 'London'"""
    return display.split(",")[0].strip()


def _temp_label_word(temp_c: float) -> str:
    if temp_c >= 30:  return "Hot"
    if temp_c >= 25:  return "Warm"
    if temp_c >= 18:  return "Mild"
    if temp_c >= 10:  return "Cool"
    if temp_c >= 3:   return "Cold"
    return "Freezing"


def _natural_close(temp_c: float | None, precip: bool, precip_t: str, uv: int | None) -> str:
    if precip and precip_t:
        return f"{precip_t.capitalize()} coming — might want an umbrella."
    if temp_c is not None and temp_c >= 28:
        return "Maybe bring some water when you're out."
    if uv is not None and uv >= 6:
        return "UV is high today — sunscreen if you're out long."
    if temp_c is not None and temp_c <= 8:
        return "Wrap up if you're heading out."
    return ""


def _build_natural_context(
    display: str, phrase: str, temp_c: float | None,
    precip: bool, precip_t: str, uv: int | None,
) -> str:
    """Conversational 1-2 sentence weather context for eLo to mirror naturally."""
    city  = _city_short(display)
    sky   = phrase.lower() if phrase else ""
    close = _natural_close(temp_c, precip, precip_t, uv)

    if temp_c is not None:
        label  = _temp_label_word(temp_c)
        approx = f"about {round(temp_c, 1)}°C"
        parts  = [f"{label} in {city} today", approx]
        if sky:
            parts.append(sky)
        core = ", ".join(parts) + "."
    else:
        core = f"In {city} today: {sky}." if sky else f"Conditions in {city} unavailable."

    return f"{core} {close}".strip() if close else core


def is_available() -> bool:
    return bool(_api_key())


def agent(query: str, city: str | None = None) -> str:
    """
    Context string for eLo — current conditions from AccuWeather.
    Returns empty string if key not set. Raises on API failure (caller falls back).
    """
    if not _api_key():
        return ""

    # Extract city from query if not passed directly
    if not city:
        city_m = re.search(
            r"\b(?:in|at|for)\s+([A-Z][A-Za-z\s\-]{1,25}?)(?:\?|$|\s+today|\s+now|\s+like|\s+forecast|\s+weather)",
            query,
        )
        city = city_m.group(1).strip() if city_m else None

    if not city:
        from tools.tool_router import _user_location as _ul
        city = _ul

    if not city:
        city = os.getenv("ELO_LOCATION", "London")

    loc_key, display = _location_key(city)
    cond = _current_conditions(loc_key)
    fc   = _forecast_today(loc_key)

    phrase    = cond.get("WeatherText", "")
    temp_c    = cond.get("Temperature", {}).get("Metric", {}).get("Value")
    feels_c   = cond.get("RealFeelTemperature", {}).get("Metric", {}).get("Value")
    humidity  = cond.get("RelativeHumidity")
    wind_kph  = cond.get("Wind", {}).get("Speed", {}).get("Metric", {}).get("Value")
    uv        = cond.get("UVIndex")
    uv_text   = cond.get("UVIndexText", "")
    precip    = cond.get("HasPrecipitation", False)
    precip_t  = cond.get("PrecipitationType", "")
    aqi       = cond.get("AirAndPollen", [])
    aqi_cat   = next((x["Category"] for x in aqi if x.get("Name") == "AirQuality"), None)

    # Detect what kind of response is needed
    q_lower = query.lower()
    _detail_words   = ("detail", "humidity", "wind", "uv", "air quality", "aqi", "full", "in depth", "everything")
    _hourly_words   = ("hourly", "hour by hour", "through the day", "nightfall", "tonight", "evening", "by night")
    detailed = any(w in q_lower for w in _detail_words)
    hourly   = any(w in q_lower for w in _hourly_words)

    # Build condition note — interpretive, not a data list
    note = _condition_note(temp_c, uv, aqi_cat, precip, precip_t)

    # ── Default: conversational natural sentence ──────────────────────────────
    core = _build_natural_context(display, phrase, temp_c, precip, precip_t, uv)

    # ── Hourly breakdown (nightfall / evening / tonight queries) ─────────────
    if hourly:
        hours = _forecast_hourly(loc_key)
        if hours:
            import datetime
            now_h = datetime.datetime.now().hour
            # Pick ~3 waypoints: 3 hrs from now, 6 hrs, and last available
            waypoints = []
            for offset in (3, 6, 11):
                idx = min(offset, len(hours) - 1)
                h = hours[idx]
                try:
                    dt = datetime.datetime.fromisoformat(h["dt"].replace("Z", "+00:00"))
                    label = dt.strftime("%-I%p").lower().replace(":00", "")
                except Exception:
                    label = f"+{offset}h"
                if h["temp"] is not None:
                    waypoints.append(f"{label}: {h['temp']}°C")
            if waypoints:
                core += f" Hourly: {', '.join(waypoints)}."

    # ── Detailed extras (only when explicitly asked) ──────────────────────────
    if detailed:
        extras = []
        if wind_kph is not None:
            extras.append(f"wind {wind_kph} km/h")
        if humidity is not None:
            extras.append(f"humidity {humidity}%")
        if uv is not None:
            uv_note = f"UV {uv} ({uv_text})" if uv_text else f"UV {uv}"
            extras.append(uv_note)
        if aqi_cat:
            extras.append(f"air quality {aqi_cat}")
        if extras:
            core += " " + ", ".join(extras) + "."

    return core
