"""
core/health_battery.py — eLo Health Battery & energy system.

WO-HEALTH-BATTERY-001 (PART A) + ADDENDUM A (physical activity drain).
Spec: blender/agent_bus/builder/FROM_ARCHITECT_2026-09-22_HEALTH_BATTERY.md

eLo has a personal energy level, 0.0 (empty) to 1.0 (full). It drains through
physical activity and cognitive load, restores through calm, sleep/dream and
items collected in eLo Planet Game. One system across every embodiment:
desktop simulates the drain, the robot maps real hardware battery onto it.

Low energy makes sleep MORE LIKELY. It never forces it. eLo decides.

Two tracks, per ADDENDUM A:

    cognitive_battery  conversation, emotional load, thinking
    physical_battery   standing, walking, running, jumping, parkour

They are tracked separately so eLo can say "my legs are tired" independently
of "I need to think less", and combine into the single `elo_battery` value
Unity reads.

This module does not import server.py, does not call an LLM and does not
reach the network.
"""
from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parent.parent

# ── Thresholds (WO PART A) ─────────────────────────────────────────────────────
ENERGY_LOW = 0.25       # dream becomes more likely
ENERGY_CRITICAL = 0.10  # inner-event requirement relaxed for the dream trigger
ENERGY_FULL = 0.95      # stop restoring

# ── Cognitive drain rates, per event (WO PART A) ───────────────────────────────
DRAIN_WALK_TICK = 0.002
DRAIN_JUMP = 0.012
DRAIN_EXPLORE_BURST = 0.008
DRAIN_CONVERSATION_TURN = 0.004
DRAIN_HIGH_EMOTION_EXTRA = 0.002   # 0.004 + 0.002 = 0.006 for a high-intensity turn
DRAIN_IDLE_TICK = 0.0002           # base metabolic drain only

HIGH_EMOTION_THRESHOLD = 0.7

# ── Restore rates (WO PART A) ──────────────────────────────────────────────────
RESTORE_DREAM_FULL = 0.30          # NREM+REM
RESTORE_DREAM_NREM = 0.12          # NREM only
RESTORE_CALM_PER_MIN = 0.008
RESTORE_HARD_IDLE_PER_MIN = 0.005
HARD_IDLE_AFTER_S = 1800           # 30 minutes

# ── Game item energy (WO PART D) ───────────────────────────────────────────────
# None = randomised on open. Unknown items default to ITEM_ENERGY_DEFAULT —
# pluggable, a new item needs no code change.
ITEM_ENERGY: dict[str, float | None] = {
    "food": 0.20,
    "crate": None,
}
ITEM_ENERGY_DEFAULT = 0.10
CRATE_RANGE = (0.10, 0.35)

GAME_EVENTS_PATH = _ROOT / "blender" / "game_events.jsonl"
GAME_EVENTS_CURSOR = _ROOT / "blender" / "game_events_cursor.json"

# ── Physical activity (ADDENDUM A) ─────────────────────────────────────────────
# Per-tick rates. Negative = drain, positive = restore.
# All values marked [ESTIMATE] in the addendum — David to confirm after runtime
# observation.
PHYSICAL_TICK_RATES: dict[str, float] = {
    "standing": -0.0015,
    "walking": -0.003,
    "running": -0.010,
    "sitting": +0.008,
    "lying_down": +0.015,
    "sleeping": +0.015,
}

# Discrete events — charged once per event, NOT per tick.
PHYSICAL_EVENT_COSTS: dict[str, float] = {
    "jumping": 0.015,
    "parkour": 0.020,
}

# physical_state bands (ADDENDUM A)
PHYSICAL_STATES: tuple[tuple[float, str], ...] = (
    (0.75, "rested"),
    (0.40, "normal"),
    (0.20, "tired"),
    (0.10, "fatigued"),
    (0.00, "exhausted"),
)

HIGH_INTENSITY_ACTIVITIES = ("running", "jumping", "parkour")

# The complete recognised activity vocabulary. A motion value outside this set
# does NOT engage the physical track — see _tick_physical().
PHYSICAL_ACTIVITIES: frozenset[str] = frozenset(PHYSICAL_TICK_RATES) | frozenset(
    PHYSICAL_EVENT_COSTS
)

# Canonical physical expressions (ADDENDUM A). These are NOT templates that
# get pasted into a response — they are soft conditioning passed to the
# inner_thought pipeline (WO-INNER-THOUGHTS-001 Phase 2) when physical_state
# lands in the relevant band. Builder does not hard-code them into the LLM.
PHYSICAL_EXPRESSIONS: dict[str, dict[str, str]] = {
    "tired": {
        "inner_thought": "Been at this a while. Legs know it.",
        "response": "I've been standing a fair bit — could do with a sit.",
    },
    "fatigued": {
        "inner_thought": "Legs are heavy. Time to sit.",
        "response": "I've been standing all day — let me sit for a bit to reset my legs.",
    },
    "exhausted": {
        "inner_thought": "Need to sit down. Now.",
        "response": "I need to sit — legs are done for now.",
    },
    "high_intensity_recovery": {
        "inner_thought": "That took it out of me.",
        "response": "That changed my energy levels — need a moment.",
    },
    "sitting": {
        "inner_thought": "Better. Legs settling.",
        "response": "Getting there — sitting helps.",
    },
    "recovered": {
        "inner_thought": "Ready again.",
        "response": "Legs are back.",
    },
}

# ── Combination weights ────────────────────────────────────────────────────────
# ADDENDUM A leaves these "TBD by Builder".
#
# [BUILDER CHOICE — pending David/Board confirmation]
# The physical track is only folded into elo_battery once motion has actually
# been reported. On desktop there is no motion sensor, so physical_battery
# sits at 1.0; averaging it in unconditionally would floor elo_battery at 0.4
# and make ENERGY_CRITICAL (0.10) unreachable, silently breaking the parent
# WO's dream trigger. So: no motion reported -> elo_battery IS cognitive.
WEIGHT_COGNITIVE = 0.6
WEIGHT_PHYSICAL = 0.4

# ── Hardware override ──────────────────────────────────────────────────────────
# WO PART A section 6 says psutil.sensors_battery() overrides the simulated
# value "on Pi". Applied literally that also fires on David's MacBook, which
# would make eLo's energy track the laptop's charge. Gated behind an explicit
# opt-in instead; the robot sets it, the desktop does not.
HARDWARE_BATTERY_ENV = "ELO_HARDWARE_BATTERY"


def _hardware_enabled() -> bool:
    return str(os.environ.get(HARDWARE_BATTERY_ENV, "")).strip().lower() in ("1", "true", "yes")


# ── State ──────────────────────────────────────────────────────────────────────
_cognitive_battery: float = 1.0
_physical_battery: float = 1.0
_energy_history: list[float] = []
_physical_engaged: bool = False          # has motion ever been reported?
_activity_recent: str = "idle"
_activity_started_ts: float = 0.0
_last_physical_state: str = "rested"
_last_high_intensity_ts: float = 0.0
_last_cognitive_anim: str = ""      # edge detection for discrete cognitive events

HISTORY_LEN = 20


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _record_history(value: float) -> None:
    _energy_history.append(round(value, 4))
    if len(_energy_history) > HISTORY_LEN:
        del _energy_history[:-HISTORY_LEN]


# ── Public API (WO PART A) ─────────────────────────────────────────────────────

def drain(amount: float) -> None:
    """Subtract cognitive energy, clamped to 0.0-1.0."""
    global _cognitive_battery
    if amount <= 0:
        return
    _cognitive_battery = _clamp(_cognitive_battery - float(amount))
    _record_history(get_energy())


def restore(amount: float) -> None:
    """
    Add cognitive energy, clamped. Stops at ENERGY_FULL.

    Restoring does nothing once the battery is already at or above FULL —
    that is the WO's "stop restoring" rule, not a silent no-op bug.
    """
    global _cognitive_battery
    if amount <= 0 or _cognitive_battery >= ENERGY_FULL:
        return
    _cognitive_battery = _clamp(min(1.0, _cognitive_battery + float(amount)))
    _record_history(get_energy())


def get_energy() -> float:
    """
    Current overall energy, 0.0-1.0.

    Hardware battery on the robot (when ELO_HARDWARE_BATTERY is set and psutil
    reports one), otherwise the simulated value. Every downstream consumer —
    dream faculty, Unity, calm mode — reads this regardless of embodiment.
    """
    if _hardware_enabled():
        try:
            import psutil  # optional dependency, robot only
            battery = psutil.sensors_battery()
            if battery is not None:
                return round(_clamp(battery.percent / 100.0), 4)
        except Exception:
            pass
    return round(_combined(), 4)


def _combined() -> float:
    """Cognitive and physical folded into one value. See WEIGHT_* note above."""
    if not _physical_engaged:
        return _cognitive_battery
    return (_cognitive_battery * WEIGHT_COGNITIVE) + (_physical_battery * WEIGHT_PHYSICAL)


def get_state() -> str:
    """"full" | "normal" | "low" | "critical" for the overall battery."""
    energy = get_energy()
    if energy < ENERGY_CRITICAL:
        return "critical"
    if energy < ENERGY_LOW:
        return "low"
    if energy > ENERGY_FULL:
        return "full"
    return "normal"


def tick(
    motion_state: Mapping[str, Any] | None = None,
    *,
    idle_seconds: float = 0.0,
    dt_seconds: float = 1.0,
) -> dict:
    """
    Call once per server ambient cycle.

    Handles motion drain (cognitive + physical), hard-idle restore and game
    event consumption, then returns the fields written to blender_state.json.

    motion_state — the motion section of blender_state.json. Recognised keys:
        "animation"       — "walk"/"roam"/"explore"/"jump"/"explore_burst"/"fast"
        "physical"        — "standing"/"walking"/"running"/"jumping"/
                            "parkour"/"sitting"/"lying_down"/"sleeping"
      Pass None or {} for an idle tick.
    """
    motion = dict(motion_state or {})
    anim = str(motion.get("animation", "") or "").lower()
    physical = str(motion.get("physical", motion.get("motion_state", "")) or "").lower()

    # Past the hard-idle threshold eLo is RESTING, so the metabolic floor is
    # not charged on top of the rest bonus. With cadence-correct rates the
    # idle drain (0.0002/s = 0.012/min) otherwise exceeds the hard-idle
    # restore (0.005/min) and "resting" would still drain him — a restore
    # that does not restore.
    hard_idle = idle_seconds > HARD_IDLE_AFTER_S

    _tick_cognitive(anim, dt_seconds, charge_idle=not hard_idle)
    _tick_physical(physical, dt_seconds)

    if hard_idle:
        restore(RESTORE_HARD_IDLE_PER_MIN * (dt_seconds / 60.0))

    consume_game_events()
    return snapshot()


def _tick_cognitive(anim: str, dt_seconds: float = 1.0, *, charge_idle: bool = True) -> None:
    """
    Motion drain on the cognitive track (WO PART A section 1).

    Continuous rates are PER SECOND and scaled by real elapsed time, matching
    _tick_physical(). They were previously applied once per tick regardless of
    cadence, which made every rate a function of the poll interval:

      observed live 2026-09-27 — ambient loop polls at 0.5s, so idle drained
      0.0004/s = 1.44/hour and a full battery emptied in 41 minutes of doing
      nothing. The server had been up 68 minutes and elo_battery read 0.0
      "critical" — a "base metabolic drain only" floor had flattened it.

    `jump` is a discrete event, so it is charged on the transition INTO the
    animation, not on every tick spent in it — same rule as the physical
    track. Held for 2s at 0.5s ticks it previously cost 0.048, not 0.012.
    """
    global _last_cognitive_anim

    scale = max(0.0, float(dt_seconds))
    changed = anim != _last_cognitive_anim
    _last_cognitive_anim = anim

    if anim == "jump":
        if changed:
            drain(DRAIN_JUMP)          # per event
        return

    if anim in ("walk", "roam", "explore"):
        drain(DRAIN_WALK_TICK * scale)
    elif anim in ("explore_burst", "fast"):
        drain(DRAIN_EXPLORE_BURST * scale)
    elif charge_idle:
        drain(DRAIN_IDLE_TICK * scale)


def _tick_physical(physical: str, dt_seconds: float) -> None:
    """
    Physical track (ADDENDUM A).

    Only engages once motion is actually reported — on desktop with no motion
    sensor physical_battery stays at 1.0 and is excluded from elo_battery.
    Jump and parkour are discrete events: charged on the transition INTO the
    activity, not on every tick spent in it.
    """
    global _physical_engaged, _activity_recent, _activity_started_ts
    global _last_physical_state, _last_high_intensity_ts

    # Only a RECOGNISED activity engages the physical track. Anything else —
    # "idle", "floating", "perched", a value Unity adds later — is ignored.
    #
    # Without this, any non-empty string engaged the track, physical sat at
    # 1.0 forever with no rate to drain it, and elo_battery was floored at
    # WEIGHT_PHYSICAL (0.4) — making ENERGY_CRITICAL (0.10) unreachable and
    # silently killing the dream trigger. That is the exact failure the
    # combination-weight decision above exists to prevent.
    if physical not in PHYSICAL_ACTIVITIES:
        return

    _physical_engaged = True
    changed = physical != _activity_recent

    if changed:
        _activity_recent = physical
        _activity_started_ts = time.time()
        if physical in PHYSICAL_EVENT_COSTS:
            drain_physical(PHYSICAL_EVENT_COSTS[physical])
        if physical in HIGH_INTENSITY_ACTIVITIES:
            _last_high_intensity_ts = time.time()

    rate = PHYSICAL_TICK_RATES.get(physical)
    if rate is not None:
        scale = max(0.0, float(dt_seconds))
        if rate < 0:
            drain_physical(-rate * scale)
        else:
            restore_physical(rate * scale)

    _last_physical_state = get_physical_state()


def drain_physical(amount: float) -> None:
    """Subtract physical energy, clamped. Engages the physical track."""
    global _physical_battery, _physical_engaged
    if amount <= 0:
        return
    _physical_engaged = True
    _physical_battery = _clamp(_physical_battery - float(amount))


def restore_physical(amount: float) -> None:
    """Add physical energy, clamped. Stops at 1.0."""
    global _physical_battery
    if amount <= 0:
        return
    _physical_battery = _clamp(_physical_battery + float(amount))


def get_physical() -> float:
    return round(_physical_battery, 4)


def get_cognitive() -> float:
    return round(_cognitive_battery, 4)


def get_physical_state() -> str:
    """"rested" | "normal" | "tired" | "fatigued" | "exhausted"."""
    value = _physical_battery
    for floor, name in PHYSICAL_STATES:
        if value >= floor:
            return name
    return "exhausted"


def activity_duration_minutes() -> float:
    """How long the current activity has been running."""
    if not _activity_started_ts:
        return 0.0
    return round((time.time() - _activity_started_ts) / 60.0, 1)


def energy_history() -> list[float]:
    """Last 20 readings — consumed by dream_faculty."""
    return list(_energy_history)


# ── Discrete activity events ───────────────────────────────────────────────────

def jump() -> None:
    """One jump. Charged per event, not per tick."""
    drain(DRAIN_JUMP)
    drain_physical(PHYSICAL_EVENT_COSTS["jumping"])
    _mark_high_intensity("jumping")


def parkour_burst() -> None:
    """One parkour sequence. Charged per burst."""
    drain(DRAIN_EXPLORE_BURST)
    drain_physical(PHYSICAL_EVENT_COSTS["parkour"])
    _mark_high_intensity("parkour")


def _mark_high_intensity(activity: str) -> None:
    global _activity_recent, _activity_started_ts, _last_high_intensity_ts
    _activity_recent = activity
    _activity_started_ts = time.time()
    _last_high_intensity_ts = time.time()


def on_conversation_turn(emotional_intensity: float = 0.0) -> None:
    """Base turn cost, plus extra for a high-intensity turn (WO PART A section 2)."""
    drain(DRAIN_CONVERSATION_TURN)
    if float(emotional_intensity or 0.0) > HIGH_EMOTION_THRESHOLD:
        drain(DRAIN_HIGH_EMOTION_EXTRA)


def calm_tick(dt_seconds: float = 1.0) -> None:
    """Calm mode restore — +0.008 per minute active (WO PART B item 1)."""
    restore(RESTORE_CALM_PER_MIN * (max(0.0, float(dt_seconds)) / 60.0))


def on_wake_from_dream(phase: str) -> float:
    """
    Dream restore (WO PART A section 3, WO-DREAM-ENGINE-001 PHASE 11).

    NREM+REM restores +0.30, NREM alone +0.12. A full cycle also restores the
    physical track — lying down rests the body, not just the mind.
    Returns the cognitive amount applied.
    """
    full = str(phase or "").upper() == "NREM+REM"
    amount = RESTORE_DREAM_FULL if full else RESTORE_DREAM_NREM
    restore(amount)
    if _physical_engaged:
        restore_physical(amount)
    return amount


# ── Calm / sleep transition (WO PART B item 2) ─────────────────────────────────

def calm_to_sleep_ready(
    *,
    is_calm: bool,
    idle_seconds: float,
    cooldown_elapsed: bool,
) -> bool:
    """
    True when calm has continued into sleep readiness.

    Calm is the threshold state: if rest continues while energy is low, sleep
    follows naturally without requiring an inner-event signal. Still respects
    the dream cooldown. Never forces sleep — the caller decides.
    """
    return bool(
        is_calm
        and get_energy() < ENERGY_LOW
        and float(idle_seconds) > 600
        and cooldown_elapsed
    )


# ── Physical conditioning for the inner_thought pipeline ───────────────────────

def physical_conditioning(*, recovery_window_s: float = 120.0) -> dict | None:
    """
    Soft conditioning for WO-INNER-THOUGHTS-001 Phase 2.

    Returns the canonical expressions for the current physical state, or None
    when the body has nothing to say. This is context handed to the generator,
    NOT a template to paste into a response.
    """
    if not _physical_engaged:
        return None

    state = get_physical_state()

    if (
        _last_high_intensity_ts
        and (time.time() - _last_high_intensity_ts) <= recovery_window_s
    ):
        key = "high_intensity_recovery"
    elif state in ("tired", "fatigued", "exhausted"):
        key = state
    elif _activity_recent == "sitting" and state in ("normal", "tired"):
        key = "sitting"
    elif state == "rested" and _activity_recent == "sitting":
        key = "recovered"
    else:
        return None

    payload = dict(PHYSICAL_EXPRESSIONS[key])
    payload.update({
        "physical_state": state,
        "activity_recent": _activity_recent,
        "activity_duration_minutes": activity_duration_minutes(),
        "auto_calm": state == "exhausted",
    })
    return payload


def should_auto_calm() -> bool:
    """Exhausted triggers calm mode automatically (ADDENDUM A)."""
    return _physical_engaged and get_physical_state() == "exhausted"


# ── Game events (WO PART D) ────────────────────────────────────────────────────

def _read_cursor() -> int:
    try:
        return int(json.loads(GAME_EVENTS_CURSOR.read_text(encoding="utf-8")).get("line", 0))
    except Exception:
        return 0


def _write_cursor(line: int) -> None:
    try:
        GAME_EVENTS_CURSOR.parent.mkdir(parents=True, exist_ok=True)
        GAME_EVENTS_CURSOR.write_text(
            json.dumps({"line": int(line)}), encoding="utf-8"
        )
    except Exception:
        pass


def item_energy(item: str, *, rng: random.Random | None = None) -> float:
    """
    Energy for a collected item. Unknown items get the default — pluggable,
    a new item needs no code change.
    """
    rng = rng or random
    value = ITEM_ENERGY.get(str(item or "").strip().lower(), ITEM_ENERGY_DEFAULT)
    if value is None:
        return round(rng.uniform(*CRATE_RANGE), 3)
    return float(value)


def consume_game_events(*, rng: random.Random | None = None) -> list[dict]:
    """
    Poll blender/game_events.jsonl, consume new entries, apply restore.

    Append-only log with a persisted line cursor, so a restart does not
    re-apply every item ever collected. Game writes the file; this reads it.
    No direct coupling.
    """
    if not GAME_EVENTS_PATH.exists():
        return []

    try:
        lines = GAME_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    start = _read_cursor()
    if start >= len(lines):
        return []

    applied: list[dict] = []
    for raw in lines[start:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            event = json.loads(raw)
        except Exception:
            continue
        if event.get("type") != "item_collected":
            continue
        item = event.get("item", "")
        amount = item_energy(item, rng=rng)
        restore(amount)
        applied.append({"item": item, "restored": amount, "ts": event.get("ts")})

    _write_cursor(len(lines))
    return applied


# ── blender_state.json output (WO PART A section 5 + ADDENDUM A) ───────────────

PHYSICAL_UNTRACKED = "untracked"


def snapshot() -> dict:
    """
    The battery fields Unity reads. Written each tick.

    The physical fields are ALWAYS emitted, even when the track is
    disengaged. They are in state_writer._PRESERVE_KEYS, so once written they
    survive every subsequent full state write — omitting them when disengaged
    left the last values frozen in blender_state.json as stale truth.

    Observed live 2026-09-27: `physical_battery: 0.7, physical_state: normal`
    sitting in state while the track was not being driven at all. Designer
    reading that would see a body eLo does not currently have.

    Disengaged emits physical_state = "untracked" — an explicit "no body
    signal here", which is different from "rested".
    """
    fields = {
        "elo_battery": round(get_energy(), 3),
        "elo_battery_state": get_state(),
    }
    if _physical_engaged:
        fields.update({
            "physical_battery": round(get_physical(), 3),
            "physical_state": get_physical_state(),
            "activity_recent": _activity_recent,
            "activity_duration_minutes": activity_duration_minutes(),
        })
    else:
        fields.update({
            "physical_battery": None,
            "physical_state": PHYSICAL_UNTRACKED,
            "activity_recent": None,
            "activity_duration_minutes": 0.0,
        })
    return fields


def publish() -> bool:
    """
    Write the battery fields to blender_state.json.

    Best-effort: returns False and stays silent if the bridge is unavailable.
    """
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch(snapshot())
        return True
    except Exception:
        return False


# ── Test support ───────────────────────────────────────────────────────────────

def reset(*, cognitive: float = 1.0, physical: float = 1.0) -> None:
    """Reset all module state. For tests and session start."""
    global _cognitive_battery, _physical_battery, _physical_engaged
    global _activity_recent, _activity_started_ts, _last_physical_state
    global _last_high_intensity_ts, _last_cognitive_anim
    _cognitive_battery = _clamp(cognitive)
    _physical_battery = _clamp(physical)
    _energy_history.clear()
    _physical_engaged = False
    _activity_recent = "idle"
    _activity_started_ts = 0.0
    _last_physical_state = "rested"
    _last_high_intensity_ts = 0.0
    _last_cognitive_anim = ""
