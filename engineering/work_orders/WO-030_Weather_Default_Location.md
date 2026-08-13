---
id: WO-030
title: "Weather — default location to London (from known user profile) so it never IP-geolocates to the wrong country"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P1
reason: "Live bug (David 2026-08-02): 'what's the weather?' returned Campo Salles, Argentina. Root cause: ELO_LOCATION unset → city=None → AccuWeather (needs a city) errors → falls back to wttr.in → IP auto-detect → wrong country (VPN/routing). eLo already KNOWS David is South London/UK (SOUTH_LDN_MODE)."
review_required: L1 → L3
risk: low (default value + fallback behaviour; no new provider)
status: READY
created: 2026-08-02
diagnostics: "tools/tool_router.py:92 _user_location = ELO_LOCATION or None; :444 city = match or _user_location; :457 wttr target 'auto' when city None → IP geolocation"
---

# WO-030 — weather default location

## Root cause (grounded)
- `tools/tool_router.py:92`: `_user_location = os.environ.get("ELO_LOCATION","") or None` → unset → None.
- `:444`: no city in query + `_user_location` None → `city = None`.
- AccuWeather (`accuweather_agent.py`) needs a **city string** to resolve a location key — with None it
  raises "No AccuWeather location found" → caught → fallback.
- `:457-458`: wttr.in target becomes `"auto"` → **IP geolocation** → Campo Salles, Argentina (wrong).

## Root cause #2 — it never persisted (the "forgot after days")
`set_location()` (tool_router.py:125) only sets the in-memory global `_user_location` — despite the
docstring "optionally to .env", it never writes anything. So "I'm in London" holds only for the life of
the process. It survived *days* because eLo OS ran continuously; the WO-026 crash-restart wiped it → IP
fallback → Argentina. Also `accuweather_agent.py:211` DEFAULTS to "London" but tool_router.py:450 passes
`city=None` explicitly, overriding that default → inconsistency.

## DECISIVE EVIDENCE (David live transcript 2026-08-02)
Consecutive weather calls returned **different** South American cities — Campo Salles (AR) → Asuncion (PY)
→ Campo Salles (AR) → Itapitanga (BR) — and **"weather in London" returned Asuncion, Paraguay**. Also
"I'm in London" → "Understood" → next weather call STILL Argentina.
→ This is NOT consistent IP geolocation (that would be the same wrong city each time) and NOT just a
missing default. It means: **(a) AccuWeather is failing** (down / expired / quota — verify the key
live), and **(b) the wttr.in fallback is broken** — it ignores the explicitly-named city AND returns
random `nearest_area` values. The named city ("London") is not reaching the serving path at all.

## PRIMARY FIX — replace the flaky fallback, honour the named city
1. **Honour an explicit city unconditionally.** "weather in London" MUST resolve London — geocode the
   named city to fixed lat/long and query by coordinates, never hand a free-text/`auto` string to a
   service that fuzzy-matches or IP-detects. (Right now "in London" yields Paraguay — unacceptable.)
2. **Replace wttr.in with a reliable keyless provider — Open-Meteo** (`api.open-meteo.com`, no key,
   stable). Use a small city→lat/long map (London 51.5074,-0.1278 as the default home) + a geocoder for
   other cities. Deterministic: same city → same coordinates → correct weather, every call.
3. **Verify AccuWeather** on David's machine (key is 46 chars, ends …2d3c). If quota-exhausted or expired,
   either refresh/upgrade the key or demote AccuWeather to secondary behind Open-Meteo.
4. **Make set-location actually reach the weather path** — "I'm in London" returned "Understood" but the
   next call ignored it; confirm `_user_location` / persisted location is read by the live serving path.

## SECONDARY (from earlier) — four parts, source-of-truth first
1. **Use the Mac's real location (best source).** macOS Location Services already knows David is in London
   via WiFi positioning — eLo ignores it. Add a **CoreLocation read** (small Swift/`shortcuts`/helper that
   returns the current city, or reverse-geocode lat/long) as the **primary** location source. Cache it;
   refresh occasionally. This is accurate and needs no IP guess and no manual "I'm in London."
2. **Persist the manual set.** `set_location()` MUST write through (to `.env` `ELO_LOCATION=` or a small
   `blender/user_location.json`) so "I'm in London" survives restarts — never rely on process lifetime.
3. **Default to London, never IP.** Priority: explicit city in query > CoreLocation > persisted set/env >
   **London default** > (IP `"auto"` only as an absolute last resort, and if used, say so honestly).
4. **Fix the None-override:** don't pass `city=None` into the AccuWeather agent when a default exists —
   let London resolve. AccuWeather primary once a city resolves (key is in `.env`).

## UPDATE (David transcript 2026-08-02 — LLM recovered)
Good news: the LLM backend is answering again (real replies, not mock). Weather with an explicit city
now works ("Weather for London" → Holborn, UK ✅). Two remaining gaps only:
- **No-city default:** "what's the weather today?" still → Argentina (IP). → the London default (below).
- **Follow-up + compound parsing:** "What about London, Hackney Wick?" was NOT parsed as a weather query.
  Two misses: (a) the "what about X" **continuation** didn't carry the prior weather intent; (b) the
  **"City, District" comma form** ("London, Hackney Wick") wasn't extracted as a location. Fix the city
  regex to handle "what about <place>?" as a weather follow-up when the last intent was weather, and to
  accept comma-separated place forms.

## Acceptance
1. "what's the weather today?" with nothing set → London (via AccuWeather), not Argentina.
2. "weather in Paris" still overrides to Paris; "I'm in Manchester" still sets Manchester.
3. AccuWeather is the source when a city resolves (wttr.in only on true AccuWeather failure).
4. `tests/test_wo030_weather_location.py` (≥4 cases: default London, explicit city, session-set, fallback
   order). py_compile clean before commit.

## Notes
- Recurring "location issue" — this makes the home default explicit so it stops resurfacing.

---
## REOPENED (David live-test 2026-08-03) — behaviour spec, not just persistence
Persistence works (`user_location.json` present, `set_location()` + "I'm in X" detector exist,
default London). But the LIVE behaviour is wrong:
- Persisted city is **"Manchester"** — stale/wrong; David never set it.
- When unset it **silently defaults to London** instead of asking.
- It **invents granular areas** ("Nine Elms") not tied to David's location.
- "The studio is in Hackney Wick" / "I'm in Hackney Wick" did NOT reliably save + confirm.

### DESIRED BEHAVIOUR (David's exact spec) — Builder, eLo OS
1. Ask weather + **no location set → eLo ASKS "Where are you?"** (never silently default, never guess).
2. David states a location (incl. natural phrasings: "I'm in X", "the studio is in X", "set my
   location to X") → **save to `user_location.json` + CONFIRM** ("Saved — Hackney Wick.").
3. Thereafter use the saved location; **never invent a sub-area** (no "Nine Elms").
4. Clear the stale "Manchester" so David's real location takes over on first set.
5. Per ADR-Exec-001: eLo must not assert an unverified location — ask, don't fabricate.

### Acceptance
1. Fresh/unset → "where are you?" 2. "I'm in Hackney Wick" → saved + confirmed + used. 3. No invented areas.

### ALSO — the DATA is wrong, not just the location (David 2026-08-03)
Across the same exchange eLo gave 29°C → "actually 28°C, light rain" → Nine Elms "30°C" — inconsistent
figures turn to turn, and David confirms **the Nine Elms reading itself is wrong.** So beyond the
location-selection bug, the weather DATA is unreliable: verify which provider is actually answering
(the chain was AccuWeather→Google→XWeather→wttr.in), that it returns REAL current conditions for the
resolved city, and that the number doesn't drift between turns for the same place. One resolved
location → one correct, stable reading.
