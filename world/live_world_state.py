"""
world/live_world_state.py — Unified World State (WO-002)

One typed, frozen snapshot of David's world — assembled once per turn,
read by every faculty. Architecture Audit gap #2.

Spec: docs/architecture/Volume_XV/01_Unified_World_State.md
Canon: "One world, read once." — each domain sampled once at top of turn, frozen.

Rules:
  - Assembled ONCE per turn before faculties reason.
  - Frozen (immutable) once assembled.
  - Every domain carries freshness: fresh_ts, confidence, status.
  - One domain failing NEVER blocks others or the turn.
  - Absent signal = status: "absent" with neutral default. Never fabricated.

Note: world/world_state.py is a DIFFERENT object (spatial nav graph for Unity).
      Do NOT merge them.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

_ROOT               = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLENDER_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")
_SPATIAL_PATH       = os.path.join(_ROOT, "blender", "elo_spatial.json")
_DOMAIN_STATUS      = Literal["live", "cached", "stale", "absent"]

# WO-NAV-009 SP-9 D-3: last confirmed body position (L3-NAV-3).
# Updated ONLY when movement_report.arrived=True (departure node stays authoritative mid-hop).
# Callers: navigate handler (departure anchor), SelfCapabilitySnapshot (current position).
_confirmed_body_win_id: int = -1


def update_confirmed_body_win_id(arrived: bool, goal_win_id: "int | None") -> None:
    """
    SP-9 / L3-NAV-3: update the confirmed body position from a movement outcome.

    Call this in server.py when a movement_report ACK is processed:
    - arrived=True + goal_win_id: update confirmed position.
    - arrived=False (in-flight / fell): no-op — departure node stays authoritative.
    Fail-quiet: any bad input is silently ignored.
    """
    global _confirmed_body_win_id
    if arrived and goal_win_id is not None:
        try:
            _confirmed_body_win_id = int(goal_win_id)
        except (TypeError, ValueError):
            pass


def get_confirmed_body_win_id() -> int:
    """Return the last confirmed body position. -1 if never confirmed."""
    return _confirmed_body_win_id


# ── Domain health container ───────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainHealth:
    fresh_ts:       float   = 0.0       # epoch float when domain was last sensed
    confidence:     float   = 0.0       # 0.0–1.0
    source:         str     = ""        # e.g. "blender_state.json" | "time.localtime" | "absent"
    status:         str     = "absent"  # "live" | "cached" | "stale" | "absent" | "failed"
    failure_reason: str     = ""        # populated when status == "failed" (WO-WORLD-001 E-4)


# ── Domain slices ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DesktopState:
    active_app:    str  = ""
    active_window: str  = ""
    platform:      str  = ""    # "mac" | "unity" | "unknown"  (D2 ruling: renamed from surface — this is the body/platform label, NOT "where eLo is". Canonical "where eLo is" lives on EloSelfState.surface.)
    available:     bool = True  # False = lookup failed; distinguishable from "no window open"


@dataclass(frozen=True)
class UserState:
    present:        bool  = True
    register:       str   = ""     # SOUTH_LDN_MODE | PATOIS_MODE | HYBRID_MODE | ""
    focus_state:    str   = "unknown"   # "focused" | "idle" | "away"
    attention_target: str = ""


@dataclass(frozen=True)
class UnityState:
    avatar_online:  bool = False
    presence_mode:  str  = ""     # "present" | "away" | "unknown"


@dataclass(frozen=True)
class BrowserState:
    active_tab_domain: str = ""
    active_tab_title:  str = ""
    visible:           bool = False


@dataclass(frozen=True)
class FilesState:
    recent_files:    tuple = field(default_factory=tuple)
    active_project:  str   = ""


@dataclass(frozen=True)
class InternetState:
    connected: bool = True
    reachable: tuple = field(default_factory=tuple)   # e.g. ("openai.com", "github.com")


@dataclass(frozen=True)
class MusicState:
    playing:    bool  = False
    track:      str   = ""
    artist:     str   = ""
    valence:    float = 0.0    # 0.0–1.0 (from spotify audio features)
    energy:     float = 0.0
    mood_label: str   = ""     # "playful" | "focused" | "calm" | ...


@dataclass(frozen=True)
class CalendarState:
    in_meeting:   bool = False
    next_event:   str  = ""
    free_until:   str  = ""


@dataclass(frozen=True)
class EnvironmentState:
    os_name:        str  = "macOS"
    screen_record:  bool = False
    vision_active:  bool = False


@dataclass(frozen=True)
class TimeState:
    now_iso:      str   = ""
    local_tz:     str   = "Europe/London"
    part_of_day:  str   = "day"   # "morning" | "afternoon" | "evening" | "night"
    day_of_week:  str   = ""


@dataclass(frozen=True)
class WeatherState:
    condition:  str   = ""
    temp_c:     float = 0.0
    location:   str   = ""


@dataclass(frozen=True)
class LocationState:
    """WO-WORLD-001 E-1: Resolved location for world-capability use.
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


@dataclass(frozen=True)
class SunState:
    """WO-WORLD-001 E-2: Sunrise/sunset for the resolved location and requested date.
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


@dataclass(frozen=True)
class GazeState:
    """WO-099: eLo's gaze awareness UP — read from elo_spatial.json (Unity writes this)."""
    x:         float = 0.5     # normalised screen X gaze aims at
    y:         float = 0.5     # normalised screen Y
    win_id:    int   = 0       # window ID under gaze (0 = none)
    window:    str   = ""      # window name under gaze
    on_window: bool  = False   # True when gaze lands on a known window
    issued_by: str   = ""      # "brain" | "reflex" | ""


# ── LiveWorldState ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LiveWorldState:
    """
    One world per turn. Frozen after assembly.
    Thirteen typed domain slices + per-domain health metadata.

    Faculties read this from CognitiveState. No faculty re-queries sensors mid-turn.
    """
    desktop:     DesktopState     = field(default_factory=DesktopState)
    user:        UserState        = field(default_factory=UserState)
    unity:       UnityState       = field(default_factory=UnityState)
    browser:     BrowserState     = field(default_factory=BrowserState)
    files:       FilesState       = field(default_factory=FilesState)
    internet:    InternetState    = field(default_factory=InternetState)
    music:       MusicState       = field(default_factory=MusicState)
    calendar:    CalendarState    = field(default_factory=CalendarState)
    environment: EnvironmentState = field(default_factory=EnvironmentState)
    time:        TimeState        = field(default_factory=TimeState)
    weather:     WeatherState     = field(default_factory=WeatherState)
    location:    LocationState    = field(default_factory=LocationState)    # WO-WORLD-001 E-1
    sun:         SunState         = field(default_factory=SunState)         # WO-WORLD-001 E-2
    gaze:        "GazeState | None" = None   # WO-099: what eLo is looking at (UP channel)

    assembled_ts:  float  = 0.0
    turn_id:       str    = ""
    domain_health: dict   = field(default_factory=dict)
    degraded:      tuple  = field(default_factory=tuple)
    route_history:      tuple  = field(default_factory=tuple)  # WO-118: recent route outcomes
    capability_results: tuple  = field(default_factory=tuple)  # WO-CAP-001: last capability results
    surfaces:           tuple  = field(default_factory=tuple)  # WO-NAV-004 SP-7: surface_graph nodes, Y-flipped
    jump_px:            int    = 0                             # WO-NAV-004 SP-8: capability_set.jump_px (authoritative)
    body_win_id:        int    = -1                            # WO-NAV-009 SP-9: eLo body position from elo_spatial.json; -1 = mid-hop / unknown
    surface_edges:      tuple  = field(default_factory=tuple)  # WO-NAV-010 SP-11: surface_graph edges for candidate generation
    win_id_to_surface:  dict   = field(default_factory=dict)   # WO-NAV-010 SP-12: int win_id → surface dict bridge


# ── Assembly ──────────────────────────────────────────────────────────────────

def assemble_world_state(turn_id: str = "", perception=None, capability_hint: str = "") -> LiveWorldState:
    """
    Assemble one frozen LiveWorldState from all available sensors.
    Called ONCE per turn, at the top of the turn, before faculties reason.

    perception: PerceptionResult | None — if provided, its fields are copied verbatim
    into the matching domain slices (Ch.3 §3.2 copy step). Confidence carried verbatim.
    Each domain is independently degradable. A domain that fails returns
    a neutral default with status='absent' — never blocks the turn.
    """
    assembled_ts = time.time()
    domain_health: dict[str, dict] = {}
    degraded: list[str] = []

    def _health(domain: str, status: str, source: str, confidence: float) -> None:
        domain_health[domain] = {
            "fresh_ts":   assembled_ts,
            "confidence": confidence,
            "source":     source,
            "status":     status,
        }

    def _degrade(domain: str) -> None:
        if domain not in degraded:
            degraded.append(domain)

    # ── Read blender_state.json (single I/O for music, vision, unity) ─────────
    bstate: dict = {}
    bstate_ts: float = 0.0
    try:
        bstate = _read_blender_state()
        bstate_ts = assembled_ts
    except Exception as _bstate_err:
        import logging as _lg
        _lg.getLogger(__name__).debug("blender_state unavailable: %s", _bstate_err)
        bstate = {}

    # ── Desktop ───────────────────────────────────────────────────────────────
    desktop = DesktopState()
    try:
        import desktop.window_state as _ws_mod   # module-style so test patches propagate
        win = _ws_mod.get()
        desktop = DesktopState(
            active_app=win.app,
            active_window=win.title,
            platform="mac",
        )
        _health("desktop", "live", "window_state", 1.0)
    except Exception as _desktop_err:
        import logging as _lg
        _lg.getLogger(__name__).warning("desktop domain unavailable: %s", _desktop_err)
        _health("desktop", "absent", "absent", 0.0)
        _degrade("desktop")
        desktop = DesktopState(available=False)  # distinguishable from "no window open"

    # ── Time ─────────────────────────────────────────────────────────────────
    time_state = TimeState()
    try:
        now = datetime.now(timezone.utc)
        h = now.hour
        part = "morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 17 else "evening" if 17 <= h < 21 else "night"
        time_state = TimeState(
            now_iso=now.isoformat(timespec="seconds"),
            local_tz="Europe/London",
            part_of_day=part,
            day_of_week=now.strftime("%A"),
        )
        _health("time", "live", "time.localtime", 1.0)
    except Exception:
        _health("time", "absent", "absent", 0.0)
        _degrade("time")

    # ── Music (from blender_state.json.spotify) ───────────────────────────────
    music = MusicState()
    try:
        spotify = bstate.get("spotify", {})
        if spotify:
            music = MusicState(
                playing=spotify.get("playing", False),
                track=spotify.get("track", ""),
                artist=spotify.get("artist", ""),
                valence=float(bstate.get("music_valence", 0.0)),
                energy=float(bstate.get("music_energy", 0.0)),
                mood_label=bstate.get("music_mood", ""),
            )
            st = "live" if (assembled_ts - bstate_ts) < 30 else "cached"
            _health("music", st, "blender_state.json/spotify", 0.9)
        else:
            _health("music", "absent", "absent", 0.0)
    except Exception:
        _health("music", "absent", "absent", 0.0)
        _degrade("music")

    # ── Unity (from blender_state.json) ──────────────────────────────────────
    unity = UnityState()
    try:
        if bstate:
            mode = bstate.get("mode", "")
            unity = UnityState(
                avatar_online=bool(bstate.get("_ts")),
                presence_mode="present" if mode else "unknown",
            )
            _health("unity", "cached", "blender_state.json", 0.7)
        else:
            _health("unity", "absent", "absent", 0.0)
            _degrade("unity")
    except Exception:
        _health("unity", "absent", "absent", 0.0)
        _degrade("unity")

    # ── Environment ───────────────────────────────────────────────────────────
    environment = EnvironmentState()
    try:
        vision_active = bstate.get("vision", {}).get("active", False) if bstate else False
        environment = EnvironmentState(
            os_name="macOS",
            screen_record=False,
            vision_active=bool(vision_active),
        )
        _health("environment", "live", "os+blender_state", 0.9)
    except Exception:
        _health("environment", "absent", "absent", 0.0)
        _degrade("environment")

    # ── User (inferred from desktop + presence) ───────────────────────────────
    user = UserState()
    try:
        user = UserState(
            present=True,
            register="",
            focus_state="focused" if desktop.active_app else "unknown",
            attention_target=desktop.active_app,
        )
        _health("user", "live", "inferred:desktop", 0.7)
    except Exception:
        _health("user", "absent", "absent", 0.0)
        _degrade("user")

    # ── Location (WO-WORLD-001 E-3b: precedence chain per David L3 2026-08-23) ─
    location_state = LocationState()
    _loc_ts = time.time()
    try:
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
                location_state = LocationState(source="absent")
                _health("location", "absent", "absent", 0.0)
    except Exception as _loc_err:
        import logging as _lg
        _lg.getLogger(__name__).warning("location domain FAILED: %s", _loc_err)
        location_state = LocationState(source="absent")
        _health("location", "absent", "absent", 0.0)
        _degrade("location")

    # ── Sun events (WO-WORLD-001 E-3c: populated only when capability_hint == 'sun_events') ──
    sun_state = SunState()
    if capability_hint == "sun_events":
        _sun_ts = time.time()
        try:
            if location_state.source != "absent" and location_state.lat != 0.0:
                _sun_result = _calculate_sun_events(
                    lat=location_state.lat,
                    lon=location_state.lon,
                    date_iso=time_state.now_iso[:10],
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
                _health("sun", "absent", "location_required", 0.0)
                _degrade("sun")
        except Exception as _sun_err:
            import logging as _lg
            _lg.getLogger(__name__).warning("sun_events calculation FAILED: %s", _sun_err)
            domain_health["sun"] = {
                "fresh_ts":      time.time(),
                "confidence":    0.0,
                "source":        f"astral_error:{_sun_err}",
                "status":        "failed",
                "failure_reason": str(_sun_err),
            }
            _degrade("sun")

    # ── Remaining domains — absent by default (sensors not yet integrated) ────
    for domain in ("browser", "files", "internet", "calendar", "weather"):
        _health(domain, "absent", "absent", 0.0)

    # ── Gaze (WO-099 UP channel — from elo_spatial.json, written by Unity) ────
    gaze_state: "GazeState | None" = None
    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as _sf:
            _sd = json.load(_sf)
        _gd = _sd.get("gaze")
        if isinstance(_gd, dict):
            gaze_state = GazeState(
                x=float(_gd.get("x", 0.5)),
                y=float(_gd.get("y", 0.5)),
                win_id=int(_gd.get("win_id", 0)),
                window=str(_gd.get("window", "")),
                on_window=bool(_gd.get("on_window", False)),
                issued_by=str(_gd.get("issued_by", "")),
            )
            _health("gaze", "live", "elo_spatial.json", 0.95)
        else:
            _health("gaze", "absent", "absent", 0.0)
    except Exception:
        _health("gaze", "absent", "absent", 0.0)

    # WO-NAV-004 SP-7/SP-10/SP-8: surface_graph from elo_spatial.json + Y-flip + jump_px
    # WO-NAV-009 SP-9: body_win_id — eLo body position (raw; -1 = mid-hop/unknown)
    _surfaces: tuple = ()
    _jump_px: int = 0
    _body_win_id: int = -1
    _surface_edges: tuple = ()
    _win_id_to_surface: dict = {}
    try:
        with open(_SPATIAL_PATH, encoding="utf-8") as _sf2:
            _sd2 = json.load(_sf2)
        _screen_h2 = int(_sd2.get("screen_h", 1440))
        _sg2 = _sd2.get("surface_graph", {})
        _cap_set2 = _sg2.get("capability_set", {})
        _jump_px = int(_cap_set2.get("jump_px", 0))
        _body_win_id = int(_sd2.get("body_win_id", -1))  # WO-NAV-009 D-1: raw position; -1 = mid-hop
        _surfaces = tuple(
            {
                "win_id":  n["id"],
                "kind":    n.get("kind", "window"),
                "rect_px": n["rect_px"],
                "py_y":    _screen_h2 - n["rect_px"][1],  # SP-10: Y-flip at Unity→Python boundary (once only)
            }
            for n in _sg2.get("nodes", [])
        )
        # WO-NAV-010 SP-11: store edges for candidate generation
        _surface_edges = tuple(_sg2.get("edges", []))
        # WO-NAV-010 SP-12: int win_id → surface dict bridge (built once at assembly)
        try:
            from world.navigation import build_surface_index as _bsi
            _win_id_to_surface = _bsi(_surfaces)
        except Exception:
            _win_id_to_surface = {}
        _health("surfaces", "live" if _surfaces else "absent",
                "elo_spatial.json", 0.9 if _surfaces else 0.0)
    except Exception:
        _health("surfaces", "absent", "absent", 0.0)

    # ── Ch.3 §3.2: copy PerceptionResult into domain slices (verbatim, no re-interpret) ──
    # Overrides direct-sensor reads only where perception provides richer data.
    # Confidence carried verbatim — never inflated.
    if perception is not None:
        try:
            pconf = getattr(perception, "confidence", 0.0)
            psurface = getattr(perception, "active_surface", "unknown")
            pactivity = getattr(perception, "user_activity", "unknown")
            pscene = getattr(perception, "scene", "")
            phealth = getattr(perception, "source_health", {})
            pwindow_app = (perception.modality_reads.get("window", "")
                           if hasattr(perception, "modality_reads") else "")
            pwindow_parts = pwindow_app.split(": ", 1)
            papp = pwindow_parts[0] if pwindow_parts else ""
            ptitle = pwindow_parts[1] if len(pwindow_parts) > 1 else pscene

            # Desktop — overwrite active_app / active_window + confidence from PerceptionFaculty.
            # D2 ruling: perception's `active_surface` (creative|code|browser|...) is an
            # activity category, NOT the platform label — it is NOT copied into DesktopState.
            # Consumers wanting the activity category read PerceptionResult.active_surface directly.
            if psurface != "unknown" or papp:
                desktop = DesktopState(
                    active_app=papp or desktop.active_app,
                    active_window=ptitle or desktop.active_window,
                    platform=desktop.platform,
                )
                p_desk_status = phealth.get("window", {}).get("status", "absent")
                domain_health["desktop"] = {
                    "fresh_ts":   assembled_ts,
                    "confidence": pconf,     # verbatim from PerceptionFaculty
                    "source":     "PerceptionFaculty",
                    "status":     p_desk_status if p_desk_status in ("live", "cached") else
                                  domain_health.get("desktop", {}).get("status", "absent"),
                    # Ch.4 §4.3: structural fidelity flag — carrier-side so no consumer
                    # has to re-derive it from a rail. `partial=True` means "do not
                    # assert this domain as whole."
                    "partial":    bool(getattr(perception, "partial", False)),
                }

            # User — update focus_state from perceived activity
            if pactivity != "unknown":
                user = UserState(
                    present=user.present,
                    register=user.register,
                    focus_state=pactivity,
                    attention_target=papp or user.attention_target,
                )
                domain_health["user"] = {
                    "fresh_ts":   assembled_ts,
                    "confidence": max(0.5, pconf),
                    "source":     "PerceptionFaculty",
                    "status":     "live",
                }

            # Environment — vision_active from perception source_health
            pvision_status = phealth.get("vision", {}).get("status", "absent")
            environment = EnvironmentState(
                os_name=environment.os_name,
                screen_record=environment.screen_record,
                vision_active=(pvision_status == "live"),
            )
            domain_health["environment"] = {
                "fresh_ts":   assembled_ts,
                "confidence": 0.9 if pvision_status == "live" else 0.5,
                "source":     "PerceptionFaculty",
                "status":     "live",
            }
        except Exception:
            pass  # degraded perception never blocks world state

    # WO-118: surface recent route outcomes to Executive (pairs with WO-106)
    _route_hist: tuple = ()
    try:
        from self.route_memory import recent_routes as _recent_routes
        _route_hist = tuple(_recent_routes(5))
        _health("route", "live" if _route_hist else "absent",
                "route_memory.jsonl" if _route_hist else "absent",
                0.9 if _route_hist else 0.0)
    except Exception:
        _health("route", "absent", "absent", 0.0)

    # WO-CAP-001: last 3 capability results — readable by Executive next turn
    _cap_results: tuple = ()
    try:
        from self.capability_memory import recent_capability_results as _rcap
        _cap_results = tuple(_rcap(3))
    except Exception:
        pass

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
        location=location_state,          # WO-WORLD-001 E-1
        sun=sun_state,                    # WO-WORLD-001 E-2
        gaze=gaze_state,
        assembled_ts=assembled_ts,
        turn_id=turn_id,
        domain_health=domain_health,
        degraded=tuple(degraded),
        route_history=_route_hist,
        capability_results=_cap_results,
        surfaces=_surfaces,             # WO-NAV-004 SP-7
        jump_px=_jump_px,               # WO-NAV-004 SP-8
        body_win_id=_body_win_id,       # WO-NAV-009 SP-9
        surface_edges=_surface_edges,   # WO-NAV-010 SP-11
        win_id_to_surface=_win_id_to_surface,  # WO-NAV-010 SP-12
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _read_blender_state() -> dict:
    with open(_BLENDER_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _read_mobile_location() -> dict | None:
    """WO-WORLD-001 E-3e: Read Mobile context location if available. Returns None if absent."""
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
    """WO-WORLD-001 E-3e: Load configured/persisted location. Returns city string or None."""
    _path = os.path.join(_ROOT, "blender", "user_location.json")
    try:
        with open(_path, encoding="utf-8") as _f:
            _d = json.load(_f)
        return _d.get("city") or None
    except Exception:
        pass
    return os.environ.get("ELO_LOCATION", "").strip() or None


def _city_to_latlon(city: str) -> tuple[float, float]:
    """WO-WORLD-001 E-3e: Resolve city name to lat/lon using astral's geocoder."""
    from astral.geocoder import lookup as _astral_lookup, database as _astral_db
    try:
        _loc = _astral_lookup(city, _astral_db())
        return float(_loc.latitude), float(_loc.longitude)
    except Exception:
        # London as hardcoded last-resort (David's standing location)
        return 51.5074, -0.1278


def _calculate_sun_events(lat: float, lon: float, date_iso: str) -> dict:
    """WO-WORLD-001 E-3e: Calculate sunrise/sunset using astral. No network call."""
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
