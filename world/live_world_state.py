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


# ── Domain health container ───────────────────────────────────────────────────

@dataclass(frozen=True)
class DomainHealth:
    fresh_ts:   float   = 0.0       # epoch float when domain was last sensed
    confidence: float   = 0.0       # 0.0–1.0
    source:     str     = ""        # e.g. "blender_state.json" | "time.localtime" | "absent"
    status:     str     = "absent"  # "live" | "cached" | "stale" | "absent"


# ── Domain slices ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DesktopState:
    active_app:    str  = ""
    active_window: str  = ""
    surface:       str  = ""    # "mac" | "unity" | "unknown"
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
    Twelve typed domain slices + per-domain health metadata.

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
    gaze:        "GazeState | None" = None   # WO-099: what eLo is looking at (UP channel)

    assembled_ts:  float  = 0.0
    turn_id:       str    = ""
    domain_health: dict   = field(default_factory=dict)
    degraded:      tuple  = field(default_factory=tuple)
    route_history: tuple  = field(default_factory=tuple)  # WO-118: recent route outcomes


# ── Assembly ──────────────────────────────────────────────────────────────────

def assemble_world_state(turn_id: str = "", perception=None) -> LiveWorldState:
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
        from desktop.window_state import get as _ws_get
        win = _ws_get()
        desktop = DesktopState(
            active_app=win.app,
            active_window=win.title,
            surface="mac",
        )
        _health("desktop", "live", "window_state", 1.0)
    except Exception as _desktop_err:
        import logging as _lg
        _lg.getLogger(__name__).warning("desktop domain unavailable: %s", _desktop_err)
        _health("desktop", "error", str(_desktop_err)[:80], 0.0)
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

            # Desktop — overwrite with perception surface + confidence from PerceptionFaculty
            if psurface != "unknown" or papp:
                desktop = DesktopState(
                    active_app=papp or desktop.active_app,
                    active_window=ptitle or desktop.active_window,
                    surface=psurface if psurface != "unknown" else desktop.surface,
                )
                p_desk_status = phealth.get("window", {}).get("status", "absent")
                domain_health["desktop"] = {
                    "fresh_ts":   assembled_ts,
                    "confidence": pconf,     # verbatim from PerceptionFaculty
                    "source":     "PerceptionFaculty",
                    "status":     p_desk_status if p_desk_status in ("live", "cached") else
                                  domain_health.get("desktop", {}).get("status", "absent"),
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
        gaze=gaze_state,
        assembled_ts=assembled_ts,
        turn_id=turn_id,
        domain_health=domain_health,
        degraded=tuple(degraded),
        route_history=_route_hist,
    )


# ── Internal ──────────────────────────────────────────────────────────────────

def _read_blender_state() -> dict:
    with open(_BLENDER_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)
