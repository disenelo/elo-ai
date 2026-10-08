"""
faculties/spatial/spatial_faculty.py — Volume XIII: Spatial Faculty

WO-CANON-XIII §B — sole canonical owner of spatial reasoning.

The only component that may answer:
  "can I reach that?"     → check_reachability()
  "how do I get there?"  → plan_route()

Shadow mode (§B): produces routes, logs them, drives nothing.
§D wires routes into move_command with issued_by=SpatialFaculty.
§E retires Unity's local route selection (requires David L3 + Designer seat).

Reads from: LiveWorldState (domain health) + desktop/spatial_state (geometry).
Issues no move_command in §B — shadow log only.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)

_ROOT       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SHADOW_LOG = os.path.join(_ROOT, "blender", "spatial_shadow.jsonl")


# ── Gibson affordance set (Vol XIII Ch.2 §2.3) ────────────────────────────────
AFF_LEDGE_RUN   = "LEDGE_RUN"
AFF_BALANCE     = "BALANCE"
AFF_WALL_CLIMB  = "WALL_CLIMB"
AFF_WALL_JUMP   = "WALL_JUMP"
AFF_HANG        = "HANG"
AFF_SLIDE       = "SLIDE"
AFF_DROP        = "DROP"
AFF_GAP_LEAP    = "GAP_LEAP"
AFF_GO_BEHIND   = "GO_BEHIND"
AFF_PERCH       = "PERCH"
AFF_SIT         = "SIT"
AFF_HIDE        = "HIDE"
AFF_PEEK        = "PEEK"
AFF_OBSERVE     = "OBSERVE"
AFF_EXIT_SCREEN = "EXIT_SCREEN"

ALL_AFFORDANCES = frozenset({
    AFF_LEDGE_RUN, AFF_BALANCE, AFF_WALL_CLIMB, AFF_WALL_JUMP, AFF_HANG,
    AFF_SLIDE, AFF_DROP, AFF_GAP_LEAP, AFF_GO_BEHIND, AFF_PERCH,
    AFF_SIT, AFF_HIDE, AFF_PEEK, AFF_OBSERVE, AFF_EXIT_SCREEN,
})


# ── Twelve-verb movement grammar (Vol XI Ch.2 §2.2) ───────────────────────────
VERB_APPROACH = "APPROACH"
VERB_CLIMB    = "CLIMB"
VERB_BALANCE  = "BALANCE"
VERB_LEAP     = "LEAP"
VERB_HANG     = "HANG"
VERB_SLIDE    = "SLIDE"
VERB_PEEK     = "PEEK"
VERB_PERCH    = "PERCH"
VERB_REST     = "REST"
VERB_OBSERVE  = "OBSERVE"
VERB_RETREAT  = "RETREAT"
VERB_RETURN   = "RETURN"
VERB_DROP     = "DROP"

MOVEMENT_VERBS = frozenset({
    VERB_APPROACH, VERB_CLIMB, VERB_BALANCE, VERB_LEAP, VERB_HANG,
    VERB_SLIDE, VERB_PEEK, VERB_PERCH, VERB_REST, VERB_OBSERVE,
    VERB_RETREAT, VERB_RETURN, VERB_DROP,
})


# ── Reachability verdicts ─────────────────────────────────────────────────────
VERDICT_REACHABLE   = "REACHABLE"
VERDICT_UNREACHABLE = "UNREACHABLE"


# ── Presence states (Vol XIII Ch.1 — Presence and Situated Being) ─────────────
PRESENCE_PERIPHERAL = "PERIPHERAL"   # David is working; eLo plans nothing
PRESENCE_ACTIVE     = "ACTIVE"
PRESENCE_AWAY       = "AWAY"


# ── Surface types ─────────────────────────────────────────────────────────────
SURF_WINDOW_TOP    = "window_top"
SURF_WINDOW_BODY   = "window_body"
SURF_DESKTOP_FLOOR = "desktop_floor"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BodySchema:
    """eLo's physical parameters — determines which routes are possible."""
    jump_px: "int | None" = 0        # SP-8: max horizontal gap crossable with LEAP (px); read from capability_set.jump_px; None = LEAP disabled
    width_px: int = 40               # body width — landing must be at least this wide
    height_px: int = 120             # body height


@dataclass(frozen=True)
class Reachability:
    """Can eLo cross a gap or reach a surface?"""
    direct_ok: bool     # True = direct route viable
    verdict: str        # REACHABLE | UNREACHABLE
    margin: int         # positive = slack, negative = how far over the limit
    blocked_by: str     # human-readable: "gap_px=82, jump_px=572"


@dataclass(frozen=True)
class Surface:
    """
    One navigable surface in the desktop world.

    The whole window is walkable: a GO_BEHIND affordance on the body surface
    means eLo can go behind a window (not a paint-order trick — a real spatial action).
    """
    surface_id: str
    surface_type: str      # SURF_WINDOW_TOP | SURF_WINDOW_BODY | SURF_DESKTOP_FLOOR
    rect: tuple            # (x, y, w, h) pixel coords; y=0 is top of screen
    z: int = 0             # z-order (higher = closer to front)
    is_focused: bool = False
    is_own: bool = False   # True = eLo's own Presence window
    regions: tuple = ()    # named regions present: ("top_ledge", "walls", ...)
    affordances: frozenset = field(default_factory=frozenset)
    stability: float = 1.0    # 0.0 = about to close; gates route selection
    available: bool = True    # False = landing too narrow, or surface is closed


@dataclass
class DesktopWorldMap:
    """
    Frozen world snapshot for one turn.

    Assembled from LiveWorldState domain health + window geometry from spatial_state.
    Confidence drops when the desktop domain is stale — no cross-surface routes issued.
    """
    surfaces: list = field(default_factory=list)    # list[Surface]
    screen: tuple = (2560, 1440)                    # (width_px, height_px)
    z_order: list = field(default_factory=list)     # surface_ids back → front
    map_ts: float = 0.0
    confidence: float = 1.0    # drops if desktop domain stale


@dataclass(frozen=True)
class RouteLeg:
    """One movement action in a route."""
    verb: str                                        # from MOVEMENT_VERBS
    to: "dict" = field(default_factory=dict)        # {"surface_id": ..., "anchor": {"x", "y"}}
    precondition: tuple = ()                         # ("PEEK",) for LEAP legs
    expected_ms: int = 500


@dataclass(frozen=True)
class Route:
    """Ordered sequence of route legs. issued_by is always SpatialFaculty."""
    legs: tuple = ()           # tuple[RouteLeg]
    issued_by: str = "SpatialFaculty"
    confidence: float = 1.0

    @property
    def total_ms(self) -> int:
        return sum(leg.expected_ms for leg in self.legs)


@dataclass(frozen=True)
class NoRoute:
    """Planning failed or was gated — eLo does not move, makes no arrival claim."""
    reason: str    # "peripheral_presence" | "surface_unavailable:..." | "no_gap_leap" | ...


# ── Exception ─────────────────────────────────────────────────────────────────

class RoutePreconditionError(ValueError):
    """A LEAP was not preceded by PEEK — route rejected at the channel (Vol XI Ch.2 §2.4)."""


# ── Affordance table (Gibson set by surface type, Vol XIII Ch.2 §2.3) ─────────

def affordances_for_type(surface_type: str) -> frozenset:
    """Return the Gibson affordance set for a surface type."""
    if surface_type == SURF_WINDOW_TOP:
        return frozenset({
            AFF_LEDGE_RUN, AFF_BALANCE, AFF_PERCH, AFF_OBSERVE,
            AFF_GAP_LEAP, AFF_PEEK, AFF_SLIDE, AFF_DROP,
        })
    if surface_type == SURF_WINDOW_BODY:
        return frozenset({
            AFF_WALL_CLIMB, AFF_WALL_JUMP, AFF_HANG,
            AFF_GO_BEHIND, AFF_HIDE, AFF_SIT,
        })
    if surface_type == SURF_DESKTOP_FLOOR:
        return frozenset({AFF_LEDGE_RUN, AFF_EXIT_SCREEN})
    return frozenset()


# ── Core logic ────────────────────────────────────────────────────────────────

def check_reachability(gap_px: int, body: BodySchema) -> Reachability:
    """
    Reachability arithmetic — "can eLo cross this gap?"

    No guessing, no defaults. If jump_px is None, LEAP is disabled entirely.
    margin is the signed distance from the limit: +5 = 5px of slack, -7 = 7px over.
    """
    if body.jump_px is None:
        return Reachability(
            direct_ok=False,
            verdict=VERDICT_UNREACHABLE,
            margin=0,
            blocked_by="GAP_LEAP disabled (jump_px=None)",
        )
    margin = body.jump_px - gap_px
    ok = margin >= 0
    return Reachability(
        direct_ok=ok,
        verdict=VERDICT_REACHABLE if ok else VERDICT_UNREACHABLE,
        margin=margin,
        blocked_by="" if ok else f"gap_px={gap_px}, jump_px={body.jump_px}",
    )


def validate_route(route: Route) -> None:
    """
    Enforce the PEEK precondition on every LEAP leg (Vol XI Ch.2 §2.4).

    Raises RoutePreconditionError if any LEAP is not immediately preceded by PEEK.
    Rejection is at the route level — nothing partial executes.
    """
    legs = list(route.legs)
    for i, leg in enumerate(legs):
        if leg.verb == VERB_LEAP:
            if i == 0 or legs[i - 1].verb != VERB_PEEK:
                raise RoutePreconditionError(
                    f"LEAP at leg {i} has no immediately preceding PEEK — route rejected at channel."
                )


def _gap_between(surface_a: Surface, surface_b: Surface) -> int:
    """Horizontal pixel gap between two surfaces (based on their top-edge rects)."""
    ax, _ay, aw, _ah = surface_a.rect
    bx, _by, _bw, _bh = surface_b.rect
    right_a = ax + aw
    return max(0, bx - right_a)


def _route_around(from_surface: Surface, to_surface: Surface) -> Route:
    """
    Generate the canonical detour when a direct LEAP is unreachable.

    SLIDE from current surface → APPROACH along the floor → CLIMB up target.
    (Vol XIII §2.3 example path.)
    """
    legs = (
        RouteLeg(
            verb=VERB_SLIDE,
            to={"surface_id": "desktop_floor", "anchor": {"x": 0.5, "y": 1.0}},
            precondition=(),
            expected_ms=300,
        ),
        RouteLeg(
            verb=VERB_APPROACH,
            to={"surface_id": to_surface.surface_id, "anchor": {"x": 0.0, "y": 1.0}},
            precondition=(),
            expected_ms=600,
        ),
        RouteLeg(
            verb=VERB_CLIMB,
            to={"surface_id": to_surface.surface_id, "anchor": {"x": 0.5, "y": 0.0}},
            precondition=(),
            expected_ms=400,
        ),
    )
    return Route(legs=legs, issued_by="SpatialFaculty", confidence=0.7)


def plan_route(
    from_surface: Surface,
    to_surface: Surface,
    body: BodySchema,
    presence: str = PRESENCE_ACTIVE,
) -> "Route | NoRoute":
    """
    Plan a route from from_surface to to_surface for eLo.

    Presence gates FIRST — if PERIPHERAL, return NoRoute immediately.
    No route is planned-then-cancelled; the gate fires before any computation.

    LEAP always requires a preceding PEEK leg (Vol XI Ch.2 §2.4).
    NoRoute if to_surface is unavailable (too narrow, closed, or confidence too low).
    Unreachable direct gap → detour via SLIDE → APPROACH → CLIMB.
    """
    # ── Presence gate (Vol XIII Ch.1): PERIPHERAL → no route, no side-effects ─
    if presence == PRESENCE_PERIPHERAL:
        return NoRoute(reason="peripheral_presence")

    # ── Target availability ────────────────────────────────────────────────────
    if not to_surface.available:
        return NoRoute(reason=f"surface_unavailable:{to_surface.surface_id}")

    # ── Adjacent or overlapping — APPROACH directly ────────────────────────────
    gap_px = _gap_between(from_surface, to_surface)
    if gap_px == 0:
        leg = RouteLeg(
            verb=VERB_APPROACH,
            to={"surface_id": to_surface.surface_id, "anchor": {"x": 0.5, "y": 0.0}},
            precondition=(),
            expected_ms=500,
        )
        return Route(legs=(leg,), issued_by="SpatialFaculty", confidence=1.0)

    # ── Gap check: LEAP if reachable, detour if not ────────────────────────────
    if AFF_GAP_LEAP not in from_surface.affordances:
        return NoRoute(reason="no_gap_leap_affordance")

    reach = check_reachability(gap_px, body)

    if reach.direct_ok:
        # PEEK must immediately precede LEAP (Vol XI Ch.2 §2.4)
        peek_leg = RouteLeg(
            verb=VERB_PEEK,
            to={"surface_id": to_surface.surface_id, "anchor": {"x": 0.5, "y": 0.0}},
            precondition=(),
            expected_ms=200,
        )
        leap_leg = RouteLeg(
            verb=VERB_LEAP,
            to={"surface_id": to_surface.surface_id, "anchor": {"x": 0.5, "y": 0.0}},
            precondition=("PEEK",),
            expected_ms=600,
        )
        route = Route(legs=(peek_leg, leap_leg), issued_by="SpatialFaculty", confidence=0.9)
        validate_route(route)    # belt-and-suspenders: must not raise here
        return route

    # Unreachable direct → detour
    return _route_around(from_surface, to_surface)


# ── World map builder ─────────────────────────────────────────────────────────

def build_map(
    windows: list,
    screen: tuple = (2560, 1440),
    body: "BodySchema | None" = None,
    domain_confidence: float = 1.0,
) -> DesktopWorldMap:
    """
    Build a DesktopWorldMap from a list of WindowBounds (from desktop/spatial_state).

    domain_confidence comes from LiveWorldState.domain_health["desktop"].confidence.
    Confidence carries verbatim — never inflated.
    """
    if body is None:
        body = BodySchema()

    screen_w, screen_h = screen
    surfaces: list[Surface] = []
    z_order: list[str] = []

    for i, win in enumerate(windows):
        # Window top surface — the ledge eLo walks on
        top_id = f"window_{win.app}_top"
        top_w = getattr(win, "w", 0)
        top_surf = Surface(
            surface_id=top_id,
            surface_type=SURF_WINDOW_TOP,
            rect=(getattr(win, "x", 0), getattr(win, "y", 0), top_w, 4),
            z=i + 1,
            is_focused=False,
            regions=("top_ledge",),
            affordances=affordances_for_type(SURF_WINDOW_TOP),
            stability=1.0,
            available=(top_w >= body.width_px),
        )
        surfaces.append(top_surf)
        z_order.append(top_id)

        # Window body surface — where eLo can go behind (GO_BEHIND)
        body_id = f"window_{win.app}_body"
        body_surf = Surface(
            surface_id=body_id,
            surface_type=SURF_WINDOW_BODY,
            rect=(getattr(win, "x", 0), getattr(win, "y", 0) + 4,
                  top_w, max(0, getattr(win, "h", 0) - 4)),
            z=i + 1,
            is_focused=False,
            regions=("walls", "interior"),
            affordances=affordances_for_type(SURF_WINDOW_BODY),
            stability=1.0,
            available=True,
        )
        surfaces.append(body_surf)

    # Desktop floor — always present at screen bottom
    floor = Surface(
        surface_id="desktop_floor",
        surface_type=SURF_DESKTOP_FLOOR,
        rect=(0, screen_h - 1, screen_w, 1),
        z=0,
        is_focused=False,
        regions=("bottom_edge",),
        affordances=affordances_for_type(SURF_DESKTOP_FLOOR),
        stability=1.0,
        available=True,
    )
    surfaces.append(floor)
    z_order.insert(0, "desktop_floor")

    return DesktopWorldMap(
        surfaces=surfaces,
        screen=screen,
        z_order=z_order,
        map_ts=time.time(),
        confidence=domain_confidence,
    )


# ── Presence detection from LiveWorldState ────────────────────────────────────

def presence_from_live_state(live_state) -> str:
    """
    Derive presence mode from LiveWorldState.user.focus_state.
    "focused" → PERIPHERAL (David is working; eLo registers peripheral, plans nothing).
    "away"    → AWAY.
    Anything else → ACTIVE.
    """
    try:
        focus = live_state.user.focus_state
        if focus == "focused":
            return PRESENCE_PERIPHERAL
        if focus == "away":
            return PRESENCE_AWAY
    except Exception:
        pass
    return PRESENCE_ACTIVE


# ── Shadow mode (§B — logs routes, drives nothing) ────────────────────────────

def shadow_plan(
    live_state,
    windows: list,
    target_surface_id: str = "",
    body: "BodySchema | None" = None,
) -> None:
    """
    §B shadow mode: plan a route, log it — issue no move_command.

    This is the §B exit criterion: "the faculty produces routes in shadow mode,
    logged and compared, driving nothing."

    Reads LiveWorldState for domain health metadata.
    Reads window geometry from the supplied windows list (from desktop/spatial_state).
    """
    if body is None:
        body = BodySchema()

    presence = presence_from_live_state(live_state)

    # Desktop domain health from LiveWorldState
    domain_health = getattr(live_state, "domain_health", {})
    desktop_h = domain_health.get("desktop", {})
    domain_conf = float(desktop_h.get("confidence", 1.0))
    domain_status = desktop_h.get("status", "absent")

    # Stale/absent desktop → map confidence drops; no cross-surface route
    if domain_status in ("stale", "absent"):
        _shadow_log({
            "shadow_ts": time.time(),
            "gate": "stale_desktop",
            "domain_status": domain_status,
            "confidence": domain_conf,
            "result_type": "no_route",
        })
        return

    try:
        screen_w = 2560
        screen_h = 1440
    except Exception:
        screen_w, screen_h = 2560, 1440

    world_map = build_map(windows, screen=(screen_w, screen_h), body=body,
                          domain_confidence=domain_conf)

    surfaces_by_id = {s.surface_id: s for s in world_map.surfaces}
    from_surface = surfaces_by_id.get("desktop_floor")
    to_surface = surfaces_by_id.get(target_surface_id) if target_surface_id else None

    if not from_surface or not to_surface:
        _shadow_log({
            "shadow_ts": time.time(),
            "gate": "no_target",
            "target": target_surface_id,
            "result_type": "no_route",
        })
        return

    result = plan_route(from_surface, to_surface, body, presence=presence)

    _shadow_log({
        "shadow_ts": time.time(),
        "presence": presence,
        "from": from_surface.surface_id,
        "to": to_surface.surface_id,
        "confidence": world_map.confidence,
        "result_type": "route" if isinstance(result, Route) else "no_route",
        "result": (
            {
                "legs": [{"verb": l.verb, "to": l.to} for l in result.legs],
                "total_ms": result.total_ms,
            }
            if isinstance(result, Route)
            else {"reason": result.reason}
        ),
    })


def _shadow_log(entry: dict) -> None:
    """Append one entry to the shadow log (NDJSON). Never blocks the turn."""
    try:
        with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as _e:
        _log.debug("spatial_faculty shadow_log write: %s", _e)


# ── Executive prompt context (never blocks; silent when peripheral) ────────────

@dataclass(frozen=True)
class SpatialContext:
    """Read-only spatial context assembled from live desktop state."""
    affordances: tuple = ()          # reachable surface affordances
    presence:    str   = "active"    # current presence tier
    surface_count: int = 0           # surfaces in the world map


def assemble(live_state=None, world_map: "DesktopWorldMap | None" = None) -> "SpatialContext":
    """Assemble a SpatialContext from live state. Never raises — returns empty context on failure."""
    try:
        presence  = presence_from_live_state(live_state) if live_state else PRESENCE_ACTIVE
        n         = len(world_map.surfaces) if world_map else 0
        affordances = tuple()
        if world_map:
            for surf in world_map.surfaces:
                affordances = affordances + tuple(affordances_for_type(surf.surface_type))
        return SpatialContext(
            affordances=affordances,
            presence=presence,
            surface_count=n,
        )
    except Exception as _e:
        _log.debug("SpatialFaculty.assemble: %s", _e)
        return SpatialContext()


def context_block(live_state=None, world_map: "DesktopWorldMap | None" = None) -> str:
    """
    Return a prompt-ready spatial context block for the Executive.
    Empty string on any failure — never blocks the turn.
    Silent when presence is PERIPHERAL.
    """
    try:
        presence = presence_from_live_state(live_state) if live_state else PRESENCE_ACTIVE
        if presence == PRESENCE_PERIPHERAL:
            return ""

        parts: list[str] = []
        if world_map:
            n = len(world_map.surfaces)
            parts.append(f"surfaces={n}")
            if world_map.confidence < 0.5:
                parts.append(f"confidence={world_map.confidence:.1f}")

        return "[SPATIAL] " + " | ".join(parts) if parts else ""
    except Exception as _e:
        _log.debug("SpatialFaculty.context_block: %s", _e)
        return ""


# ── §D: route serialisation + direction→surface resolution ────────────────────

def leg_to_dict(leg: RouteLeg) -> dict:
    """Serialise one RouteLeg to a JSON-safe dict for blender_state move_command."""
    return {
        "verb": leg.verb,
        "to": leg.to,
        "precondition": list(leg.precondition),
        "expected_ms": leg.expected_ms,
    }


def route_to_list(route: Route) -> list:
    """Serialise all legs of a Route to a JSON-safe list."""
    return [leg_to_dict(leg) for leg in route.legs]


def _nearest_surface_in_direction(
    elo_x: int,
    elo_y: int,
    direction: str,
    world_map: DesktopWorldMap,
) -> "Surface | None":
    """
    Find the nearest walkable surface in the given cardinal direction.

    direction: "left" | "right" | "up" | "down"
    Returns the closest Surface whose rect is in the requested direction,
    or None if nothing is reachable.
    """
    candidates: list[tuple[float, Surface]] = []
    for surf in world_map.surfaces:
        if not surf.available:
            continue
        x, y, w, h = surf.rect
        cx = x + w // 2
        cy = y + h // 2
        if direction == "right" and cx > elo_x:
            candidates.append((cx - elo_x, surf))
        elif direction == "left" and cx < elo_x:
            candidates.append((elo_x - cx, surf))
        elif direction == "up" and cy < elo_y:
            candidates.append((elo_y - cy, surf))
        elif direction == "down" and cy > elo_y:
            candidates.append((cy - elo_y, surf))
    if not candidates:
        return None
    return min(candidates, key=lambda t: t[0])[1]


def route_for_direction(
    elo_x: int,
    elo_y: int,
    direction: str,
    world_map: DesktopWorldMap,
    body: "BodySchema | None" = None,
    presence: str = PRESENCE_ACTIVE,
) -> "Route | NoRoute":
    """
    §D entry-point: plan a Python-issued route for a directional move intent.

    Maps a cardinal direction to the nearest target surface, then calls
    plan_route(). Returns NoRoute when no suitable target exists or the
    movement is blocked by presence gate.

    Callers attach the result to the move_command via leg_to_dict / route_to_list.
    """
    if body is None:
        body = BodySchema()

    # Derive from_surface: eLo's current floor or nearest surface under them
    from_surface: Surface | None = None
    for surf in sorted(world_map.surfaces, key=lambda s: s.z, reverse=True):
        x, y, w, h = surf.rect
        if x <= elo_x <= x + w:
            from_surface = surf
            break
    if from_surface is None:
        # Fallback: desktop floor
        for surf in world_map.surfaces:
            if surf.surface_type == SURF_DESKTOP_FLOOR:
                from_surface = surf
                break
    if from_surface is None:
        return NoRoute(reason="no_from_surface")

    to_surface = _nearest_surface_in_direction(elo_x, elo_y, direction, world_map)
    if to_surface is None:
        return NoRoute(reason=f"no_target_in_direction:{direction}")

    if to_surface.surface_id == from_surface.surface_id:
        return NoRoute(reason="already_at_target")

    return plan_route(from_surface, to_surface, body, presence=presence)
