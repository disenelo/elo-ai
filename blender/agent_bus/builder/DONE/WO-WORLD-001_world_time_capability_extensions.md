# WO-WORLD-001 — World/Time Capability: Five Minimal Extensions
**Status:** 🔨 BUILD
**Authority:** David L3 ratification `_intake/SOURCE_2026-08-23_DAVID_L3_ratification_world_time_capability.md`
**Board ruling:** `findings/WORLD_TIME_CAPABILITY_RULING_2026-08-23.md`
**Lane:** Builder only — LA does not touch code (Rule 3)
**Scope:** Five extensions to existing files. No new subsystems, no new stores, no new faculties.

---

## The goal

When a user asks "When is sunrise?", eLo answers from the current assembled world state — not from language-model guessing. If the required world state is unavailable or failed, that state must be explicit and visible to the Executive/LLM. eLo must not manufacture world-state facts from training knowledge.

The architectural invariant: capability invocation is a world-state assembly step. The Executive reads the frozen result. The Executive is the sole decision-maker. No capability becomes a second reasoning path.

---

## Architectural constraints (hard lines from David L3)

- DO NOT create a new faculty, cognitive system, memory store, provenance system, or Executive decision path.
- DO NOT call any capability from inside the Executive faculty.
- DO NOT call `assemble_world_state()` more than once per turn.
- The frozen `LiveWorldState` is the only source the Executive reads.
- Absent/failed domain = explicit status in the frozen state. Never silently fall back to fabricated data.
- `assemble_world_state()` must remain independently degradable — one domain failing must never block others or the turn.

---

## E-1 — `LocationState` domain slice

**File:** `world/live_world_state.py`

Add this frozen dataclass **after the `WeatherState` dataclass** (around line 128):

```python
@dataclass(frozen=True)
class LocationState:
    """WO-WORLD-001: Resolved location for world-capability use.
    Source precedence (David L3 2026-08-23):
      1. mobile_device  — live Mobile context
      2. explicit       — user-established in current context
      3. configured     — studio/home default (blender/user_location.json or ELO_LOCATION env)
      4. absent         — no trustworthy location; do not invent one
    """
    city:        str   = ""
    country:     str   = ""
    lat:         float = 0.0
    lon:         float = 0.0
    source:      str   = ""      # "mobile_device" | "explicit" | "configured" | "absent"
    confidence:  float = 0.0     # 0.0–1.0
    fresh_ts:    float = 0.0     # epoch float when this was resolved
```

Add `location` field to `LiveWorldState` (alongside the other domain slices, around line 160):

```python
    location:    LocationState   = field(default_factory=LocationState)
```

Update the docstring line count: "Twelve typed domain slices" → "Thirteen typed domain slices".

---

## E-2 — `SunState` domain slice

**File:** `world/live_world_state.py`

Add this frozen dataclass **after `LocationState`**:

```python
@dataclass(frozen=True)
class SunState:
    """WO-WORLD-001: Sunrise/sunset for the resolved location and requested date.
    Populated only when capability_hint resolves to 'sun_events'.
    Absent by default — never fabricated.
    source = 'astral/calculated' when populated; 'absent' otherwise.
    """
    sunrise_iso:   str   = ""    # ISO 8601 local time, e.g. "2026-08-24T05:58:00"
    sunset_iso:    str   = ""
    date_iso:      str   = ""    # which date these apply to, e.g. "2026-08-24"
    location:      str   = ""    # city label used for calculation
    source:        str   = ""    # "astral/calculated" | "absent"
    confidence:    float = 0.0   # 1.0 for astronomical calculation; 0.0 when absent
    retrieved_at:  float = 0.0   # epoch float
```

Add `sun` field to `LiveWorldState`:

```python
    sun:         SunState        = field(default_factory=SunState)
```

---

## E-3 — `capability_hint` parameter on `assemble_world_state()`

**File:** `world/live_world_state.py`

### 3a — Signature change

Change the function signature from:
```python
def assemble_world_state(turn_id: str = "", perception=None) -> LiveWorldState:
```
to:
```python
def assemble_world_state(turn_id: str = "", perception=None, capability_hint: str = "") -> LiveWorldState:
```

### 3b — Location assembly (add before the "Remaining domains" block, line ~309)

Add the location assembly section inside `assemble_world_state()`. It must follow the same pattern as every other domain: independently degradable, neutral default on failure.

```python
    # ── Location (WO-WORLD-001: precedence chain per David L3 2026-08-23) ───────
    location_state = LocationState()
    _loc_ts = time.time()
    try:
        # Source 1: Mobile context (future — reads blender/mobile_context.json when present)
        _mobile_loc = _read_mobile_location()
        if _mobile_loc:
            location_state = LocationState(
                city=_mobile_loc.get("city", ""),
                country=_mobile_loc.get("country", ""),
                lat=float(_mobile_loc.get("lat", 0.0)),
                lon=float(_mobile_loc.get("lon", 0.0)),
                source="mobile_device",
                confidence=1.0,
                fresh_ts=_loc_ts,
            )
            _health("location", "live", "mobile_context.json", 1.0)
        else:
            # Source 2/3: explicit or configured (from tool_router persisted store / env)
            _cfg_city = _load_configured_location()
            if _cfg_city:
                _lat, _lon = _city_to_latlon(_cfg_city)
                location_state = LocationState(
                    city=_cfg_city,
                    country="",
                    lat=_lat,
                    lon=_lon,
                    source="configured",
                    confidence=0.85,
                    fresh_ts=_loc_ts,
                )
                _health("location", "cached", f"user_location:{_cfg_city}", 0.85)
            else:
                _health("location", "absent", "absent", 0.0)
    except Exception as _loc_err:
        import logging as _lg
        _lg.getLogger(__name__).warning("location domain FAILED: %s", _loc_err)
        _health("location", "absent", "absent", 0.0)
        _degrade("location")
```

### 3c — Sun events assembly (add after location assembly, conditional on capability_hint)

```python
    # ── Sun events (WO-WORLD-001: populated only when capability_hint == 'sun_events') ──
    sun_state = SunState()
    if capability_hint == "sun_events":
        _sun_ts = time.time()
        try:
            if location_state.source != "absent" and location_state.lat != 0.0:
                _sun_result = _calculate_sun_events(
                    lat=location_state.lat,
                    lon=location_state.lon,
                    date_iso=time_state.now_iso[:10],   # YYYY-MM-DD from TimeState
                )
                sun_state = SunState(
                    sunrise_iso=_sun_result["sunrise"],
                    sunset_iso=_sun_result["sunset"],
                    date_iso=_sun_result["date"],
                    location=location_state.city,
                    source="astral/calculated",
                    confidence=1.0,
                    retrieved_at=_sun_ts,
                )
                _health("sun", "live", "astral/calculated", 1.0)
            else:
                # Location absent — cannot calculate. Status must be explicit.
                _health("sun", "absent", "location_required", 0.0)
                _degrade("sun")
        except Exception as _sun_err:
            import logging as _lg
            _lg.getLogger(__name__).warning("sun_events calculation FAILED: %s", _sun_err)
            _health("sun", "failed", f"astral_error:{_sun_err}", 0.0)
            _degrade("sun")
```

### 3d — Add `location` and `sun` to the return statement

```python
    return LiveWorldState(
        desktop=desktop,
        user=user,
        unity=unity,
        browser=BrowserState(),
        files=FilesState(),
        internet=InternetState(),
        music=music,
        calendar=CalendarState(),
        environment=environment,
        time=time_state,
        weather=WeatherState(),
        location=location_state,         # E-1 (WO-WORLD-001)
        sun=sun_state,                   # E-2 (WO-WORLD-001)
        gaze=gaze_state,
        assembled_ts=assembled_ts,
        turn_id=turn_id,
        domain_health=domain_health,
        degraded=tuple(degraded),
        route_history=_route_hist,
    )
```

### 3e — Three internal helper functions (add near `_read_blender_state()`)

```python
def _read_mobile_location() -> dict | None:
    """WO-WORLD-001: Read Mobile context location if available. Returns None if absent."""
    _path = os.path.join(_ROOT, "blender", "mobile_context.json")
    try:
        with open(_path, encoding="utf-8") as _f:
            _d = json.load(_f)
        _loc = _d.get("location")
        if isinstance(_loc, dict) and _loc.get("city"):
            return _loc
    except Exception:
        pass
    return None


def _load_configured_location() -> str | None:
    """WO-WORLD-001: Load configured/persisted location. Returns city string or None."""
    _path = os.path.join(_ROOT, "blender", "user_location.json")
    try:
        with open(_path, encoding="utf-8") as _f:
            _d = json.load(_f)
        return _d.get("city") or None
    except Exception:
        pass
    return os.environ.get("ELO_LOCATION", "").strip() or None


def _city_to_latlon(city: str) -> tuple[float, float]:
    """WO-WORLD-001: Resolve city name to lat/lon using astral's geocoder."""
    from astral.geocoder import lookup as _astral_lookup, database as _astral_db
    try:
        _loc = _astral_lookup(city, _astral_db())
        return float(_loc.latitude), float(_loc.longitude)
    except Exception:
        # London as hardcoded last-resort (David's standing location)
        return 51.5074, -0.1278


def _calculate_sun_events(lat: float, lon: float, date_iso: str) -> dict:
    """WO-WORLD-001: Calculate sunrise/sunset using astral. No network call."""
    from astral import LocationInfo
    from astral.sun import sun as _astral_sun
    import datetime as _dt
    _loc = LocationInfo(latitude=lat, longitude=lon)
    _date = _dt.date.fromisoformat(date_iso)
    _s = _astral_sun(_loc.observer, date=_date)
    return {
        "sunrise": _s["sunrise"].isoformat(timespec="minutes"),
        "sunset":  _s["sunset"].isoformat(timespec="minutes"),
        "date":    date_iso,
    }
```

---

## E-4 — `DomainHealth` — add `"failed"` status and `failure_reason`

**File:** `world/live_world_state.py`

Change `DomainHealth` from:
```python
@dataclass(frozen=True)
class DomainHealth:
    fresh_ts:   float   = 0.0
    confidence: float   = 0.0
    source:     str     = ""
    status:     str     = "absent"  # "live" | "cached" | "stale" | "absent"
```

to:
```python
@dataclass(frozen=True)
class DomainHealth:
    fresh_ts:       float   = 0.0
    confidence:     float   = 0.0
    source:         str     = ""
    status:         str     = "absent"       # "live" | "cached" | "stale" | "absent" | "failed"
    failure_reason: str     = ""             # populated when status == "failed"
```

Note: `domain_health` in `LiveWorldState` is stored as `dict`, not `DomainHealth` instances — the dict entries already accept arbitrary keys. When status is `"failed"`, the `failure_reason` key must be present in the dict entry alongside the standard keys.

---

## E-5 — `sun_events` capability registry entry

**File:** `runtime/capabilities/registry.py`

Add to the `_UTILITY` list, after the `"weather"` entry:

```python
    Capability(
        id="sun_events",
        display_name="Sun Events",
        category=CAT_UTILITY,
        description="Sunrise, sunset, and daylight hours for a location and date",
        verbs=["sunrise", "sunset", "dawn", "dusk", "daylight",
               "when does the sun rise", "when does the sun set",
               "when does it get light", "when does it get dark",
               "how long until sunrise", "how long until sunset"],
        requires_api=False,            # astral library — local calculation, no network
        execution_priority=2,
        agent_module="world.live_world_state",   # invoked via assemble_world_state()
        ack_source=ACK_SYNC_RETURN,
        authority_scope=SCOPE_PERSON,
    ),
```

---

## `spine.py` — pass `capability_hint` to `assemble_world_state()`

**File:** `runtime/spine/spine.py`

The call to `assemble_world_state()` at ~line 587 currently is:
```python
_world = _assemble_world(turn_id=raw[:32] if raw else "", perception=_perception)
```

The capability faculty runs AFTER world assembly. So `capability_hint` must be extracted from the language faculty output BEFORE world assembly, or world assembly must be called after the language faculty.

Current order in `spine.run()`:
1. mint experience_id
2. perceive
3. **assemble_world_state** ← currently here
4. working memory
5. cognitive_snapshot
6. language_faculty
7. capability_faculty
8. assemble_cognitive_state
9. Executive

The language faculty runs at step 6 — after world assembly at step 3. To pass capability_hint to world assembly, two options:

**Option A (preferred — lightweight pre-pass):** Before calling `assemble_world_state()`, run a minimal intent sniff on `raw` to detect `capability_hint`. The capability_learning module or a lightweight keyword check against the registry verbs can produce this. This does NOT run the full language faculty — it is a fast pattern match.

**Option B:** Move `assemble_world_state()` to after the language faculty (step 6.5). This is architecturally cleaner but is a larger reorder.

**Board ruling: Builder chooses Option A or B, but must not run a separate LLM call or full language faculty pass to get the hint.** The hint is a fast capability-verb match against the raw input — the same kind of match `_capability_faculty()` already performs. A separate utility function calling `_capability_faculty()` with the raw input as meaning is acceptable.

**Whichever option chosen:** the call must become:
```python
_world = _assemble_world(
    turn_id=raw[:32] if raw else "",
    perception=_perception,
    capability_hint=_early_capability_hint,   # "sun_events" | "" | other
)
```

---

## Acceptance tests

All 8 ATs must pass before this WO is reported complete. G-3 pattern applies: Builder does NOT self-report the WO as architecturally validated — return results to Board/LA.

**AT-1 — `LocationState` assembled from configured source**
`assemble_world_state()` with no mobile context and London in `user_location.json` →
`world.location.source == "configured"`, `world.location.city == "London"`, `world.location.confidence == 0.85`

**AT-2 — `LocationState` absent when no source**
`assemble_world_state()` with no mobile, no `user_location.json`, no env →
`world.location.source == "absent"`, `world.location.confidence == 0.0`

**AT-3 — `SunState` absent when hint not "sun_events"**
`assemble_world_state(capability_hint="")` →
`world.sun.source == ""`, `world.sun.sunrise_iso == ""`, `world.sun.confidence == 0.0`

**AT-4 — `SunState` populated when hint is "sun_events" + location available**
`assemble_world_state(capability_hint="sun_events")` with London location →
`world.sun.source == "astral/calculated"`, `world.sun.sunrise_iso` is a non-empty ISO time string, `world.sun.confidence == 1.0`

**AT-5 — `SunState` absent + degraded when hint is "sun_events" + location absent**
`assemble_world_state(capability_hint="sun_events")` with no location source →
`world.sun.source == ""`, `world.sun.confidence == 0.0`, `"sun"` in `world.degraded`

**AT-6 — `DomainHealth` carries `failure_reason` on failed domain**
Simulate a calculation failure (e.g., mock `_calculate_sun_events` to raise) →
`world.domain_health["sun"]["status"] == "failed"`, `"failure_reason"` key present and non-empty

**AT-7 — `sun_events` capability registered**
`from runtime.capabilities.registry import CAPABILITIES` →
`any(c.id == "sun_events" for c in CAPABILITIES)` == True, `c.requires_api == False`

**AT-8 — `spine.run()` passes capability_hint to world assembly**
End-to-end: raw input "when is sunrise tomorrow?" →
`plan.world.sun.source == "astral/calculated"` (with a valid configured location present)

---

## Architectural constraints — repeated for emphasis

| Rule | Constraint |
|---|---|
| No new subsystem | All code in `world/live_world_state.py` + `runtime/capabilities/registry.py` + `runtime/spine/spine.py` |
| No Executive capability call | `sun_events` invoked in `assemble_world_state()` only |
| No second cognitive pass | `assemble_world_state()` called once per turn in `spine.run()` |
| Absent/failed = explicit | `SunState.source` must be non-empty on failure; `DomainHealth.status` must be "absent" or "failed" |
| No hallucination path | A missing sunrise time must remain absent in the frozen state. The LLM must not fill it. |
| Astral only | No network calls for `sun_events`. `requires_api=False` is an architectural commitment. |
| Do not touch | vault_layer, memory_faculty, decision_journal, spine executive logic, provenance systems |

---

## Return this WO to Board/LA as COMPLETE when all 8 ATs pass. Do not self-declare architectural validation.

---

## ✅ CLOSED — 2026-08-23

**Status:** COMPLETE

### Implementation summary

**Files modified (no new subsystems):**

| File | Change |
|------|--------|
| `world/live_world_state.py` | E-1: `LocationState` dataclass; E-2: `SunState` dataclass; E-3: `capability_hint` param on `assemble_world_state()`, location + sun assembly blocks, 3 helper functions; E-4: `DomainHealth.failure_reason` field + `"failed"` status. `LiveWorldState` gains `location` + `sun` fields. Docstring: Thirteen typed domain slices. |
| `runtime/capabilities/registry.py` | E-5: `sun_events` capability entry added after `weather`. |
| `runtime/spine/spine.py` | Option A fast verb pre-sniff before world assembly; `assemble_world_state()` call now passes `capability_hint=_early_capability_hint`. |
| `tests/test_canon_xv_world_state.py` | `_ALL_DOMAINS` updated to include `"location"` (always written to domain_health by E-3b). |

**New test file:** `tests/test_wo_world001_world_time_capability.py` (8 ATs).

**Library installed:** `astral` (pure Python astronomical calculations — no network).

### Architecture choices

- **Option A chosen** for `capability_hint`: fast keyword pre-sniff against registry verbs on the raw input before world assembly. No LLM call, no full language faculty pass. Falls through to `""` on any exception.
- `sun` domain only written to `domain_health` when `capability_hint == "sun_events"` — it is never in `domain_health` for other turns (intentional; `_ALL_DOMAINS` in canon XV does not include it for this reason).
- `location` domain always written to `domain_health` (with `source="absent"` when unresolved) so the frozen world state always carries explicit location status.

### Test results

```
8/8 WO-WORLD-001 ATs PASSED in 1.32s
14/14 test_canon_xv_world_state.py PASSED (0 regressions)
6/6 test_wo002_live_world_state.py PASSED (0 regressions)
All XDNA tests: 19/19 PASSED (unchanged)
```

AT coverage:
- AT-1: LocationState from configured source ✅
- AT-2: LocationState absent when no source ✅
- AT-3: SunState absent when hint != "sun_events" ✅
- AT-4: SunState populated with astral/calculated when hint + location available ✅
- AT-5: SunState absent + "sun" in degraded when location absent ✅
- AT-6: DomainHealth carries failure_reason on failed domain ✅
- AT-7: sun_events registered, requires_api=False ✅
- AT-8: spine fast pre-sniff routes "when is sunrise?" → sun_events hint → populated SunState ✅

### Return to Board/LA

WO-WORLD-001 is complete. Builder does not self-declare architectural validation. Results returned to Board/LA for independent validation.

The Capability Reality Audit (CRA) items — re-planning loop, route planning, capability-result-before-decision — are acknowledged as R&D/not-yet-authorised. No work has been done on them.
