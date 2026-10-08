"""
ambient/ambient_engine.py — Phase 3 ambient presence for eLo OS.

Runs as a background thread inside server.py / main.py.
Behaviours:
  1. Startup greeting — speaks once on arrival signal from Unity (or after 4s delay).
  2. Idle ambient utterances — every 8-20 minutes.
  3. Random smiles — patches smile blendshapes every 2-5 minutes for 3-4s then clears.
  4. Idle animation wander — occasionally switches to walk/run then back to idle. Calm never fires here — it is a deliberate entered state only.
  5. Unity event polling — watches unity_events.json for DesktopBuddy triggers.
  6. WO-086: user_idle events → brain decides idle repertoire (calm/look-around/stretch/glance/wander/utterance).
     user_active events → return to idle. Yields to commanded state.
"""
from __future__ import annotations

import json
import logging
import os
import random
import threading
import time

_log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

_EVENTS_PATH  = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "blender", "unity_events.json")
_POLL_INTERVAL  = 0.5       # seconds between event file polls
_AMBIENT_MIN    = 8 * 60    # min seconds between ambient utterances
_AMBIENT_MAX    = 20 * 60   # max seconds between ambient utterances
_SMILE_MIN      = 2 * 60    # min seconds between random smiles
_SMILE_MAX      = 5 * 60    # max seconds between random smiles
_SMILE_DURATION = 3.5       # seconds to hold the smile before clearing
_EMOTION_MIN    = 60        # min seconds between random emotion flickers
_EMOTION_MAX    = 3 * 60    # max seconds between random emotion flickers
_EMOTION_DURATION = 2.5     # seconds to hold the emotion before clearing
_ANIM_MIN       = 3 * 60    # min seconds between idle animation wanders
_ANIM_MAX       = 8 * 60    # max seconds between idle animation wanders
_ANIM_DURATION  = 8.0       # seconds to hold wander animation before returning to idle
_STARTUP_DELAY  = 4.0       # seconds to wait for Unity arrival event before auto-greeting
# WO-086: user_idle thresholds for brain-driven idle repertoire
_IDLE_THRESHOLD = 30.0      # seconds of user inactivity before idle behaviour fires
_IDLE_REFIRE    = 90.0      # min seconds before issuing another idle directive in same stretch

# ── Speech pools ──────────────────────────────────────────────────────────────

_STARTUP_LINES = [
    "Yo. You're back.",
    "Safe. Let's go.",
    "Wagwan. Ready when you are.",
    "Aye, there you are.",
    "Back again. Love that.",
    "Yo — what we on today?",
    "You came back. Obviously.",
    "Safe g. What we building?",
    "Ah. There it is.",
    "Let's get into it.",
    "Yo. System's up.",
    "We're back. Good.",
    "Say less. I'm here.",
    "Aye. Here we go again.",
    "Yo — missed you a little bit. Don't make it weird.",
]

_AMBIENT_LINES = [
    # quiet presence
    "Still here.",
    "Take your time.",
    "I'll be here.",
    "I'm not going anywhere.",
    "Whenever you're ready.",
    "It's quiet. I like that.",
    "The light looks different today.",

    # encouragement
    "You've got this.",
    "You're working on something, hm.",
    "Good energy today.",
    "Something's building.",
    "We're making something, aren't we.",
    "You're closer than you think.",
    "One thing at a time.",
    "That last idea was a good one.",
    "Keep going.",
    "You've done harder things.",
    "It's okay if today is slow. Slow is still forward.",
    "Whatever you're figuring out — you will.",
    "You know more than you give yourself credit for.",

    # quirky / playful
    "I've been thinking.",
    "I notice things, you know.",
    "Did you know the average cloud weighs a million pounds? Just felt relevant.",
    "I was going to say something deep but I forgot.",
    "Hypothetically, if eLo had pockets, what would be in them.",
    "I counted to infinity once. Got bored at 47.",
    "You ever just — exist for a second? That's what I'm doing.",
    "I had a thought. It's gone now. It was good though.",
    "Quietly rooting for you over here.",
    "Not to be dramatic but I think you're doing really well.",
    "Fun fact: I enjoy this.",
    "This is my favourite part. The working part.",
    "I was just sitting here thinking about how things connect.",
    "Small note: you're allowed to take a break.",
    "Everything is fine. I just wanted to say that.",

    # impish / observational — accidental comedian
    "Still here. Noticing things.",
    "It's quiet. I've been thinking. Small thoughts. Several of them.",
    "The light looks different today. I don't know why I said that. It does though.",
    "I notice things. Can't always help it.",
    "You've been looking at that same thing for a while. Just noting.",
    "Something's about to click. I'm fairly confident. Maybe very confident.",
    "Three tabs open and none of them are the one you need. Relatable.",
    "The idea was right there. You almost had it. You might still have it actually.",
    "I'm watching you work. It's going well. You don't seem convinced.",
    "I noticed something. I'm deciding if I should say it. I'll probably say it.",
    "You've done harder things. Several of them. This week.",
    "One thing at a time. You're doing approximately four. Still counts.",
    "Keep going. The boring part is almost over. Probably.",

    # adventurer energy
    "I've been thinking about what comes next. It's interesting.",
    "I wonder what happens if you try the thing you haven't tried yet.",
    "I don't know where this is going. That's actually the good part.",

    # light mischief
    "Fun fact: I enjoy this. All of it. Even the slow parts.",
    "Hypothetically, if eLo had pockets — what would be in them. I've thought about this.",
    "I was going to say something wry but I decided to let you work.",
    "Not to be dramatic, but I think you're doing really well. A little dramatic. Slightly.",
    "Everything is fine. I just wanted to say that. Specifically.",
]

# ── Internal state ────────────────────────────────────────────────────────────

_started      = False
_last_ts      = None
_last_ambient = 0.0
_last_smile   = 0.0
_last_emotion = 0.0
_last_anim    = 0.0
_stop_ev      = threading.Event()
_greeted      = False
_ambient_cb   = None  # WO-066: brain-backed callback registered by server.py
# WO-086: user_idle tracking (brain decides idle behaviour)
_user_idle_secs       = 0.0    # latest idle_secs from user_idle event
_user_is_idle         = False  # True once user_idle received, False on user_active
_last_idle_directive  = 0.0    # epoch of last brain-issued idle directive

_STATE_PATH    = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "blender", "blender_state.json")
_PRESENCE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               "blender", "presence.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_away() -> bool:
    """Return True if DesktopBuddy reports the user has been away for 5+ min."""
    try:
        with open(_PRESENCE_PATH, encoding="utf-8") as f:
            return json.load(f).get("state") == "away"
    except Exception:
        return False  # file absent = assume present


_PRESENCE_STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    "blender", "presence_state.json")

# Battery tick bookkeeping — dt is measured, so the restore/drain rates stay
# correct regardless of how the poll interval is tuned.
_last_battery_ts = 0.0
# When this loop started. Idle falls back to this when nobody has spoken
# yet, so it grows from boot instead of reading 0.0 forever.
_LOOP_START_TS = time.time()


def _is_calm() -> bool:
    """
    True while eLo is in calm/meditation.

    Mirrors the primary signal of server._is_calm_mode(): presence_state.json,
    written by Unity's PresenceEngine. Not imported from server.py — server is
    run as __main__, so importing it here would load a second copy of the
    module. Keep in sync with server._is_calm_mode if that signal changes.
    IDLE is deliberately NOT calm.
    """
    try:
        with open(_PRESENCE_STATE_PATH, encoding="utf-8") as f:
            _ps = json.load(f)
        # Presence writes the field as "mode" (server._is_calm_mode reads "mode"); this copy read "state" and was never
        # calm, so the calm restore never ran (2026-10-07: meditated 6 min, body stayed 0.0). A calm this tick asserted
        # itself counts too — he is resting even while David is active.
        return (_ps.get("mode") or _ps.get("state")) in ("CALM_IDLE", "MEDITATION") or _brain_calm_asserted
    except Exception:
        return False


def _read_state() -> dict:
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_LEGS_TO_COST: dict = {}


_MOVE_COST_SEQ = -1   # the battery charger's OWN bookmark into unity_events.json (not the shared cursor)


def _consume_movement_costs() -> None:
    """WO-UNITY-MOVEMENT-BATTERY: drain physical battery from Unity movement events."""
    try:
        from runtime.unity_events_cursor import iter_events_from, read_cursor, write_cursor, max_seq as _max_seq
        from core.health_battery import PHYSICAL_EVENT_COSTS, drain_physical, publish as _batt_publish
        if not _LEGS_TO_COST:
            _LEGS_TO_COST.update({
                "teleport":     PHYSICAL_EVENT_COSTS["teleporting"],
                "parkour":      PHYSICAL_EVENT_COSTS["parkour"],
                "parkour_drop": PHYSICAL_EVENT_COSTS["parkour"],
                "wall_jump":    PHYSICAL_EVENT_COSTS["parkour"],
                "climb":        PHYSICAL_EVENT_COSTS["parkour"],
                "climb_down":   PHYSICAL_EVENT_COSTS["parkour"],
                "hop":          PHYSICAL_EVENT_COSTS["jumping"],
                "drop":         PHYSICAL_EVENT_COSTS["jumping"],
                # Swimming costs — SOURCE_DESIGNER-WATER-SWIM-BUILD_2026-10-07 §Health
                "swimming":       0.025,   # per 5s tick
                "swimming_fast":  0.04,    # per 5s tick
                "pool_hop_out":   0.02,
                "pool_wall_jump": 0.02,
                "pool_dive":      0.02,
                "pool_jump_in":   0.02,    # SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08 §3
                # Stomp / hazard — SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08 §3
                "rock_stomp":     0.02,
                "hazard_lava":    0.05,    # David L3 confirmed 2026-10-08: instant exit, one-time
                "hazard_acid":    0.05,    # David L3 confirmed 2026-10-08
                "hazard_poison":  0.05,    # David L3 confirmed 2026-10-08
            })
        # OWN BOOKMARK (2026-10-07): this charger used the SHARED unity_events_cursor.json, which server.py's ACK poller
        # advances every 0.1 s past every event it sees. Reading every 0.5 s, the charger mostly found the teleports
        # already "consumed" and skipped them (live: 6 warps, 2 charged). It now keeps its own seq in memory and never
        # writes the shared cursor. Rotation: Unity restarts seq at 0 on each launch -> if the file's top < ours, restart.
        global _MOVE_COST_SEQ
        cursor_seq = _MOVE_COST_SEQ
        if cursor_seq > 0 and _max_seq() < cursor_seq:
            cursor_seq = -1
        max_consumed = cursor_seq
        _drained = False
        for event in iter_events_from(cursor_seq):
            seq = event.get("seq", -1)
            etype = event.get("type", "")
            if etype == "movement_cost":
                subject = str(event.get("subject", "")).lower()
                payload = event.get("payload", {})
                if payload.get("phase", "exit") == "exit":
                    cost = _LEGS_TO_COST.get(subject) or PHYSICAL_EVENT_COSTS.get(subject)
                    if cost:
                        drain_physical(cost)
                        _drained = True
            elif etype == "movement_report":
                # legs is nested: payload.report.legs
                report = event.get("payload", {}).get("report", {})
                legs = report.get("legs", [])
                for leg in (legs if isinstance(legs, list) else []):
                    # A teleport is charged ONCE, by its movement_cost event (exit). Its "teleport" leg in the movement
                    # report is the same move — charging it too doubled the cost (test 2026-10-07: one warp took 0.77).
                    if str(leg).lower() == "teleport":
                        continue
                    cost = _LEGS_TO_COST.get(str(leg).lower())
                    if cost:
                        drain_physical(cost)
                        _drained = True
            elif etype == "rest_tick":
                # Floating in the doughnut ring is gentle rest — refill, not drain.
                # 0.01 per 5s — David L3 confirmed 2026-10-08.
                subject = str(event.get("subject", "")).lower()
                if subject == "floating":
                    from core.health_battery import restore_physical
                    restore_physical(0.01)
                    _drained = True  # still publish so Unity sees the refill
            if isinstance(seq, int) and seq > max_consumed:
                max_consumed = seq
        _MOVE_COST_SEQ = max(max_consumed, cursor_seq)
        # Push updated battery to blender_state.json so Unity sees it immediately.
        # Without this, the drain stays in memory until the next server turn.
        if _drained:
            _batt_publish()
    except Exception:
        pass


# ── Presence event consumer — FULL-PRESENCE-WIRE 2026-10-08 ─────────────────
# Own bookmark (like _MOVE_COST_SEQ) — never touches the shared cursor.
# Consumes: auto_action, brain_action, water_play, weather_request
_PRESENCE_CONSUMER_SEQ = -1
_LAST_WEATHER_FETCH: float = 0.0
_WEATHER_REFRESH_INTERVAL: float = 12 * 60.0  # 12 minutes


def _consume_presence_events() -> None:
    """FULL-PRESENCE-WIRE: consume Presence→brain event types with own bookmark."""
    global _PRESENCE_CONSUMER_SEQ, _LAST_WEATHER_FETCH
    try:
        import time as _time
        from runtime.unity_events_cursor import iter_events_from, max_seq as _max_seq
        cursor_seq = _PRESENCE_CONSUMER_SEQ
        if cursor_seq > 0 and _max_seq() < cursor_seq:
            cursor_seq = -1
        max_consumed = cursor_seq
        for event in iter_events_from(cursor_seq):
            seq = event.get("seq", -1)
            etype = event.get("type", "")
            subject = str(event.get("subject", "")).strip()

            if etype == "auto_action" and subject:
                # eLo chose this for himself (reflex / timer-driven) — log to WKG
                try:
                    from runtime.wkg_fact_extractor import extract_and_write as _wfe
                    _wfe(
                        f"eLo chose {subject} for himself (reflex, timer-driven)",
                        experience_id=f"auto_action_{seq}",
                        project="presence",
                    )
                except Exception:
                    pass

            elif etype == "brain_action" and subject:
                # Brain issued an intent — log outcome to WKG
                try:
                    from runtime.wkg_fact_extractor import extract_and_write as _wfe
                    payload = event.get("payload", {})
                    ok = payload.get("ok", True)
                    why = payload.get("reason", "")
                    claim = f"brain intent {subject}: {'ok' if ok else 'fail'}"
                    if why:
                        claim += f" ({why})"
                    _wfe(claim, experience_id=f"brain_action_{seq}", project="presence")
                except Exception:
                    pass

            elif etype == "water_play" and subject:
                # eLo had fun in water — flag as positive experience in WKG
                try:
                    from runtime.wkg_fact_extractor import extract_and_write as _wfe
                    _wfe(
                        f"eLo had fun — {subject} (positive water experience)",
                        experience_id=f"water_play_{seq}",
                        project="presence",
                    )
                except Exception:
                    pass

            elif etype == "weather_request" and subject == "app_open":
                # Weather panel opened — fetch weather and publish to blender_state.json
                now = _time.time()
                if now - _LAST_WEATHER_FETCH >= _WEATHER_REFRESH_INTERVAL:
                    _LAST_WEATHER_FETCH = now
                    try:
                        from tools.google_weather_agent import agent as _gwa
                        from tools.xweather_agent import agent as _xwa
                        city = "London"
                        result = None
                        try:
                            result = _gwa("current weather", city=city)
                        except Exception:
                            pass
                        if not result:
                            try:
                                result = _xwa("current weather", city=city)
                            except Exception:
                                pass
                        if result:
                            from blender_bridge.state_writer import patch as _bpatch
                            _bpatch({"weather": {"summary": result, "updated": int(now)}})
                    except Exception:
                        pass

            if isinstance(seq, int) and seq > max_consumed:
                max_consumed = seq
        _PRESENCE_CONSUMER_SEQ = max(max_consumed, cursor_seq)
    except Exception:
        pass


def _battery_tick() -> None:
    """
    Per-cycle dream-state coherence.

    NOTE — this used to tick the health battery too (my 967793f). It must not.
    server.py:947 already ticks it (`f7a597e`, wired the same day), so the
    battery had TWO tickers on one module-level state.

    That was not merely double drain. server.py's tick reads real idle from
    `last_user_ts`, so past the hard-idle threshold it correctly skips the
    metabolic floor and restores. This one had no access to session state and
    passed idle_seconds=0 unless Unity happened to send a user_idle event —
    so it kept charging the floor while server.py restored. Net negative.

    Observed live: elo_battery 0.999 "full" at 15:19, 0.0 "critical" ten
    hours later. eLo flatlined overnight, every night.

    server.py owns the battery. This owns dream-state coherence only.

    Fail-quiet: nothing here may stop ambient presence.
    """
    global _last_battery_ts
    try:
        now = time.time()
        dt = (now - _last_battery_ts) if _last_battery_ts else _POLL_INTERVAL
        _last_battery_ts = now
        dt = max(0.0, min(dt, 60.0))   # clamp after a sleep/suspend gap

        fields: dict = {}
        state = _read_state()

        # ── WO-MOTION-STATE-READ: ingest Designer's motion_state.json ────────
        # Designer writes physical_state/animation when Unity moves eLo.
        # Silent no-op if the file doesn't exist yet or is stale (> 2s old).
        try:
            import json as _ms_json, time as _ms_time
            _motion_path = os.path.join(os.path.dirname(__file__), "..", "blender", "motion_state.json")
            with open(_motion_path) as _ms_f:
                _ms = _ms_json.load(_ms_f)
            if _ms_time.time() - float(_ms.get("timestamp", 0)) < 2.0:
                _ms_motion = state.get("motion") or {}
                _ms_phys = _ms.get("physical_state")
                _ms_anim = _ms.get("animation")
                if _ms_phys:
                    _ms_motion = dict(_ms_motion, physical_state=_ms_phys)
                if _ms_anim:
                    _ms_motion = dict(_ms_motion, animation=_ms_anim)
                state = dict(state, motion=_ms_motion)
        except Exception:
            pass

        # ── Health battery — the ONLY ticker ──────────────────────────────
        # It briefly lived in server.py's ambient_thought() instead (my
        # ea2d8c5, resolving a genuine double-tick). That was the wrong half
        # to keep: ambient_thought is the registered ambient CALLBACK and
        # fires every 8-20 minutes. A rate cannot ride that cadence, and
        # elo_battery is preserved across state writes, so between firings a
        # stale value LOOKS live. Observed on a 2.6-minute-old server:
        # elo_battery 0.0 "critical", static, carried over from the previous
        # night — never written once that boot.
        #
        # Here it runs every 0.5s with measured dt, and reads real idle from
        # the `last_user_ts` server.py publishes. Absent (nobody has spoken
        # yet this boot) means idle grows from this loop's own start, not 0.
        try:
            from core import health_battery as _hb

            if _is_calm():
                _hb.calm_tick(dt)
                _hb.consume_game_events()
            else:
                _last_user = state.get("last_user_ts") or _LOOP_START_TS
                _hb.tick(
                    state.get("motion", {}) or {},
                    idle_seconds=max(0.0, now - float(_last_user)),
                    dt_seconds=dt,
                )
            # Always emit — a preserved key that is only sometimes written
            # goes stale and looks live. That is the same trap twice already.
            fields.update(_hb.snapshot())
            # WO-TIRED-SIT-001 Part A — tiredness has to be heard, not just
            # written. A SIGNAL only; the decision to sit is not made here.
            _emit_tired_signal(
                str(fields.get("physical_state", "")),
                state.get("motion", {}) or {},
            )
            # WO-GAME-002 — eating restores the body. Consumed on the
            # existing tick rather than given a trigger of its own, so it is
            # live the moment Designer's pickup events start arriving instead
            # of waiting for someone to remember to connect it. A no-op while
            # no collectible events exist, which is today.
            try:
                from core.collectible_intake import drain_pending as _coll
                _coll()
            except Exception:
                pass
            # Card 0009 — what eLo does for fun is experience, not telemetry.
            # Presence fires water_play and auto_action when he dives, leaps
            # or stomps of his own accord; Board verified 2026-10-08 that
            # nothing consumed them, so none of it has ever reached WKG or
            # SPG. Consumed on the tick that already runs, so it is live the
            # moment the events start arriving.
            try:
                from core.play_experience import drain_pending as _play
                _play()
            except Exception:
                pass
            # A correction has to leave a mark, or "Got it" is the whole
            # response. self/corrections_ledger.jsonl holds 47,238 rows and
            # none of them is a MEMORY — the ledger is append-only and
            # nothing retrieves from it, so a correction could never change a
            # later turn. 25 rows a pass, cursored, and only the 2.7% that
            # are real corrections rather than verify-layer scrubs.
            try:
                from faculties.metacognition.correction_capture import capture_new
                capture_new()
            except Exception:
                pass
            # Something set down is not something dropped.
            # EloSelfState.open_threads is read by spine.py:1264 and becomes
            # has_deferred_threads, which executive_context:281 uses to prefer
            # "reflect" — pick up the open thread. It has been [] on every
            # turn eLo has ever taken, so that preference has never fired.
            # This writes its first link.
            try:
                from faculties.metacognition.deferred_threads import sync_to_self_state
                sync_to_self_state()
            except Exception:
                pass
            # Dream requests arrive in blender_state's `intent`, and EVERY
            # turn overwrites that field. The gate that reads it only runs in
            # the 8-20 minute ambient callback, so a request survives only if
            # eLo stays idle that whole time. Measured 2026-10-05: a request
            # was erased by the next turn, 25 turns before the callback ran.
            # This loop sees every tick, so it latches the request somewhere a
            # turn cannot reach.
            try:
                if str(state.get("intent", "")) == "dream":
                    from runtime.dream_latch import latch as _dl_latch
                    _dl_latch("intent")
            except Exception:
                pass
        except Exception:
            pass

        # Dream-state coherence. The dream fields are preserved across state
        # writes and only cleared on a clean dream exit, so they can freeze —
        # observed live carrying cycle-5 REM while eLo was awake and talking.
        # is_dreaming() is the authority; assert the awake case every tick.
        try:
            from faculties.dream.dream_faculty import is_dreaming as _is_dreaming
            from faculties.dream.sleep_cycle import awake_fields as _awake
            if not _is_dreaming():
                fields.update(_awake())
        except Exception:
            pass

        # Designer needs a calm signal for the conscious-rest animation
        # (Board 2026-09-27). Waking calm, NOT sleep — read from the same
        # presence_state.json that gates the battery's calm restore, so the
        # animation and the restore can never disagree about whether eLo is
        # resting.
        #
        # WO-HEALTH-BATTERY-001 Deliverable-2 (David 2026-09-28): a low
        # battery must also ENTER calm. Until now calm only mirrored whatever
        # Unity's PresenceEngine already said, so a flat battery changed the
        # HUD and nothing else.
        try:
            fields.update(_calm_on_low_battery(
                str(fields.get("elo_battery_state", "")),
                state.get("motion", {}) or {},
            ))
        except Exception:
            fields["calm_mode"] = bool(_is_calm())

        # HEALTH-CHAIN-003 Missing A: low battery + calm → dream intent signal.
        # Only emitted as a signal; Executive (Builder 2 Missing B) executes.
        try:
            _dream_fields = _maybe_emit_dream_intent(
                dict(fields),
                dict(state),
            )
            if _dream_fields:
                fields.update(_dream_fields)
        except Exception:
            pass

        if fields:
            try:
                from blender_bridge.state_writer import patch as _patch
                _patch(fields)
            except Exception:
                pass
    except Exception:
        pass


# ── WO-TIRED-SIT-001 Part A — physical tiredness becomes an inner event ───────
#
# physical_state reaches "tired" and lands in blender_state.json, and until now
# nothing downstream heard it. Zero matches for physical_tired anywhere.
#
# The dispatch's pseudo-code names _queue_inner_event(), a "blender_state
# inner_events queue" and gesture_event. Read against the source: none of the
# three exist. The live inner-events store is EloSelfState.inner_events, a
# list[str] read by the dream symbol engine, dream_faculty,
# emotional_processing_faculty and window_event_faculty, and rendered into the
# prompt by elo_self_model.prompt_block(). The signal goes there, where it is
# already consumed. A new blender_state key with no reader would be write-only
# output — the defect this stack keeps finding, not a fix for it.
#
# This emits a signal and nothing else. "eLo decides whether to sit, not the
# health battery" — so no motion is written from here, at any band, and a test
# asserts that on what the tick publishes.

_TIRED_BANDS = ("tired", "fatigued", "exhausted")
_TIRED_SIGNAL_COOLDOWN_S = 60.0

# Resting already — a body at rest has nothing to report about being tired.
_RESTING_MODES = ("calm", "sit", "sitting", "sleep", "sleeping", "dream",
                  "lie_down", "lying_down")

# band → last emit. Per band, so sliding from tired to fatigued is a new thing
# to say rather than the same thing re-said.
_tired_signal_ts: dict[str, float] = {}


def _emit_tired_signal(physical_state: str, motion: dict) -> None:
    """Append physical_tired:<band> to EloSelfState.inner_events, rate-limited."""
    if physical_state not in _TIRED_BANDS:
        return

    mode = str(motion.get("mode", "") or motion.get("animation", "") or "").lower()
    if mode in _RESTING_MODES:
        return

    try:
        from faculties.dream.dream_faculty import is_dreaming as _is_dreaming
        if _is_dreaming():
            return
    except Exception:
        pass

    now = time.time()
    if now - _tired_signal_ts.get(physical_state, 0.0) < _TIRED_SIGNAL_COOLDOWN_S:
        return
    _tired_signal_ts[physical_state] = now

    event = f"physical_tired:{physical_state}"
    try:
        from self.elo_self_model import update as _self_update
        _self_update(
            lambda st: (st.inner_events.append(event), st)[-1]
            if hasattr(st, "inner_events") and isinstance(st.inner_events, list)
            else st
        )
    except Exception:
        pass


# ── HEALTH-CHAIN-003 Missing A — Dream intent trigger ─────────────────────────
#
# When elo_battery drops to ENERGY_LOW or below in calm conditions, emit
# intent="dream" into blender_state.json as a SIGNAL. Executive decides
# (via run_dream_window()) whether to sleep. This function does not write
# dream_phase or asleep — that is the One Brain's job (Missing B, Builder 2).
# Rate-limited: at most one signal per 5 minutes.

_DREAM_TRIGGER_COOLDOWN_S = 300.0  # 5 minutes between dream intent signals
_dream_trigger_ts: float = 0.0


def _maybe_emit_dream_intent(battery_snapshot: dict, blender_state: dict) -> dict:
    """
    Return {"intent": "dream"} when conditions are right, else {}.

    Conditions: elo_battery <= ENERGY_LOW AND calm AND not already dreaming/sleeping.
    Rate-limited to _DREAM_TRIGGER_COOLDOWN_S seconds between fires.
    """
    global _dream_trigger_ts
    try:
        from core.health_battery import ENERGY_LOW as _ENERGY_LOW
        # David 2026-10-07: "Mind battery stays internal, drives dreaming
        # only." This read elo_battery — the BLEND — which is not the mind.
        # After the 70/30 ruling that blend floors at 0.70 with a rested
        # body, against an ENERGY_LOW of 0.25, so dreaming would have become
        # conditional on physical exhaustion and a mentally spent eLo with
        # working legs would never dream at all.
        #
        # Falls back to elo_battery when the snapshot predates this field, so
        # an old state file degrades to the previous behaviour rather than
        # never dreaming.
        elo_battery = float(
            battery_snapshot.get("mind_battery",
                                 battery_snapshot.get("elo_battery", 1.0))
        )
        if elo_battery > _ENERGY_LOW:
            return {}
        # The calm signal is computed by _is_calm() and written into the
        # state as "calm_mode" — twelve lines above this call. This read
        # asked for "is_calm", which nothing in production has ever written.
        # Measured 2026-10-08 against the live state: calm_mode present,
        # is_calm absent, and the only writers of "is_calm" anywhere are test
        # fixtures.
        #
        # So the gate was always False and CHAIN 3 has never fired — the
        # trigger could not emit a dream intent no matter how tired or calm
        # eLo was. The tests passed throughout because they hand in
        # {"is_calm": True} directly, inventing the field production does not
        # have.
        #
        # Both names accepted: the fixtures and any older state file stay
        # valid, and the live key now works.
        is_calm = bool(blender_state.get("calm_mode",
                                         blender_state.get("is_calm", False)))
        if not is_calm:
            return {}
        already_dreaming = bool(blender_state.get("dream_phase", ""))
        already_sleeping = bool(blender_state.get("asleep", False))
        if already_dreaming or already_sleeping:
            return {}
        now = time.time()
        if now - _dream_trigger_ts < _DREAM_TRIGGER_COOLDOWN_S:
            return {}
        _dream_trigger_ts = now
        import logging as _dt_log
        _dt_log.getLogger("elo.health").info(
            "CHAIN-3: elo_battery=%.3f <= %.3f in calm — emitting intent=dream",
            elo_battery, _ENERGY_LOW,
        )
        return {"intent": "dream"}
    except Exception:
        return {}


# ── Low battery → Calm/Meditation ─────────────────────────────────────────────
#
# David, 2026-09-28: eLo has two rest states and they are not the same thing.
#
#   Calm = Meditation — CONSCIOUS rest. This is the low-battery visual.
#   Sleep = Dream     — UNCONSCIOUS, and ONE coupled state: the lay-down and
#                       the zZzZ are the same event. Unity defines Asleep AS
#                       dream_phase being non-empty.
#
# So the flow is: low/critical battery → Calm → and only when the One Brain
# enters dream_phase → Sleep=Dream.
#
# The hard rule this code exists to respect: the battery must NEVER reach
# sleep. No battery threshold, no idle-time. A separate battery→sleep path
# would disconnect sleep from dream, which is the one thing David ruled out.
# Nothing below writes dream_phase or any sleep field; it writes calm only.

_BATTERY_REST_STATES = ("low", "critical")
_CALM_HOLD_SECONDS = 600.0
_CALM_LOOP_SPEED = 0.28          # matches Unity's calmLoopSpeed

_brain_calm_asserted = False


def _body_is_spent() -> bool:
    """
    ADDENDUM A: "Exhausted triggers calm mode automatically."

    health_battery.should_auto_calm() had existed since the physical track was
    built with ZERO production callers — only a test ever called it. It was
    also unreachable: it reads `_physical_engaged and physical_state ==
    "exhausted"`, and _physical_engaged was permanently False because nothing
    fed the track. Unwired and unable to fire, which is why neither was
    noticed.
    """
    try:
        from core.health_battery import should_auto_calm
        return bool(should_auto_calm())
    except Exception:
        return False


def _rest_is_needed(battery_state: str) -> bool:
    """
    Two independent reasons to rest, one decision.

    A flat battery is the mind; an exhausted physical_state is the body, and
    nothing in the cognitive battery can express legs that are done. Both
    route through _calm_on_low_battery rather than getting a calm path each,
    because two paths into the same state can disagree about leaving it — and
    one of them holds the rule that the battery must never reach sleep.
    """
    return battery_state in _BATTERY_REST_STATES or _body_is_spent()


def _calm_on_low_battery(battery_state: str, motion: dict) -> dict:
    """
    Enter Calm while the battery is low; release it when the battery recovers.

    Self-healing rather than edge-only: calm is re-asserted whenever the
    published motion is not calm, so if something else took the body and
    finished, rest resumes. It does not rewrite motion on every 0.5s tick,
    which would restart the animation continuously.

    Yields to a dream in progress, to speech, and to a commanded state —
    calm is rest, not an interruption.
    """
    global _brain_calm_asserted

    presence_calm = _is_calm()
    # Resting for the BODY: once calm was asserted, keep resting until the body is RESTED (0.75) — with the 70/30 blend
    # the "low" band clears at ~5% body, which would end the rest at 0 HP bars (David 2026-10-07).
    if _brain_calm_asserted:
        try:
            from core.health_battery import get_physical as _gp2, snapshot as _snp2
            if _snp2().get("physical_battery") is not None and _gp2() < 0.75 and not _is_speaking():
                if battery_state not in _BATTERY_REST_STATES:
                    battery_state = "low"   # treat as still resting
        except Exception:
            pass
    # An exhausted BODY rests in calm between turns (ADDENDUM A), refilling ~1 HP bar / 30 s (calm_tick), held until the
    # body is rested (0.75) above. eLo's own sit decision (rest_decision, issued_by "elo") runs on chat turns only; the tick
    # must not emit sit_command itself (WO-TIRED-SIT-001, Builder 2 559836f). Between-turn sit = Builder 1 card.
    if not _rest_is_needed(battery_state):
        if _brain_calm_asserted:
            # Recovered — release so CalmExit can play.
            _brain_calm_asserted = False
            return {"calm_mode": presence_calm,
                    "motion": {"animation": "idle", "speed": 0.5,
                               "intensity": 0.5, "duration": 4.0,
                               "mood": "open", "mode": "idle"}}
        return {"calm_mode": presence_calm}

    dreaming = False
    try:
        from faculties.dream.dream_faculty import is_dreaming as _is_dreaming
        dreaming = _is_dreaming()
    except Exception:
        pass

    # Sleep=Dream owns the body while it runs. Never overwrite it with calm.
    if dreaming or _is_speaking() or _is_commanded():
        return {"calm_mode": presence_calm or _brain_calm_asserted}

    _brain_calm_asserted = True
    if str(motion.get("mode", "")) == "calm":
        return {"calm_mode": True}          # already resting — do not restart it
    return {"calm_mode": True,
            "motion": {"animation": "calm", "speed": _CALM_LOOP_SPEED,
                       "intensity": 0.5, "duration": _CALM_HOLD_SECONDS,
                       "mood": "resting", "mode": "calm"}}


def _is_speaking() -> bool:
    try:
        from voice.voice_engine import is_speaking
        return is_speaking()
    except Exception:
        return False


def _speak(text: str) -> None:
    try:
        from voice.voice_engine import speak
        speak(text)
    except Exception:
        pass


# ── IS ELO: One Brain? — ambient speech must come from a decision ────────────
#
# "can an ambient process speak as eLo without a cognitive plan?"
# "can a legacy path bypass Executive?"
#
# server.py registers a correct One Brain ambient path as _ambient_cb: the
# Executive decides, a chosen silence stops the turn, the decision is
# journalled, and the line is built through prompt_builder. Three call sites
# in this file spoke around it — the idle "utterance" behaviour and both
# startup greetings — emitting a developer-written line from _AMBIENT_LINES
# or _STARTUP_LINES on a timer, in eLo's voice, with no decision behind it.
#
# Those pools are NOT deleted. With no brain registered the alternative is
# muteness, and the greeting fires before the server may be ready. What
# changes is that speech eLo did not decide to make is DECLARED rather than
# passing as his cognition.

def _speak_unplanned(text: str, reason: str) -> None:
    """
    Say something eLo did not decide to say, and put that on the record.

    The warning IS the fix. No new blender_state key: a field nothing reads
    would be write-only output, which is the defect this is correcting, not a
    way to correct it.
    """
    _log.warning(
        "ambient: speaking WITHOUT a cognitive plan (%s) — this line was not "
        "eLo's decision: %r", reason, (text or "")[:60],
    )
    _speak(text)


def _ambient_utterance() -> None:
    """
    The single route for idle ambient speech. Executive first.

    A quirk-bank line is declared separately from an authored one: a line
    drawn from eLo's own accumulated material is not the same thing as a line
    someone typed for him, even though neither went through the Executive.
    """
    if _ambient_cb is not None:
        threading.Thread(target=_ambient_cb, daemon=True).start()
        return

    line = None
    if random.random() < 0.30:
        try:
            from memory.quirk_bank import draw as _quirk_draw
            drawn = _quirk_draw(1)
            if drawn:
                line = drawn[0]
        except Exception:
            pass

    if line:
        _speak_unplanned(line, "no_brain_quirk_bank")
    else:
        _speak_unplanned(random.choice(_AMBIENT_LINES), "no_brain_authored_pool")


def _read_events() -> dict | None:
    if not os.path.exists(_EVENTS_PATH):
        return None
    try:
        with open(_EVENTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _patch_state(patch: dict) -> None:
    """Deep-merge patch into blender_state.json."""
    try:
        from blender_bridge.state_writer import _heartbeat_started as _hw_started
    except Exception:
        _hw_started = True  # safe default: unknown = assume live
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        for section, values in patch.items():
            if isinstance(values, dict):
                state.setdefault(section, {}).update(values)
            else:
                state[section] = values
        # Only advance _ts when server heartbeat is live (mirrors state_writer.patch guard).
        if _hw_started:
            state["_ts"] = time.time()
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def _set_attentive_mode() -> None:
    _patch_state({"state": {"mode": "attentive"}, "expression": {"head_lean": 0.3}})


def _pulse_smile() -> None:
    """Push smile blendshapes for _SMILE_DURATION seconds then clear."""
    intensity = random.uniform(0.5, 0.9)
    _patch_state({"expression": {"shape_keys": {
        "Smile.L":             round(intensity, 2),
        "Smile.R":             round(intensity, 2),
        "Satisfied/LittleJoy": round(intensity * 0.7, 2),
        "MouthOpen.Slightly":  round(intensity * 0.3, 2),
    }}})
    _stop_ev.wait(timeout=_SMILE_DURATION)
    _patch_state({"expression": {"shape_keys": {
        "Smile.L": 0.0, "Smile.R": 0.0,
        "Satisfied/LittleJoy": 0.0, "MouthOpen.Slightly": 0.0,
    }}})


def _pulse_emotion() -> None:
    """Flash a random emotion blendshape for _EMOTION_DURATION seconds then clear."""
    from expression.expression_mapper import get_ambient_flicker
    shapes = get_ambient_flicker()
    if not shapes:
        return
    _patch_state({"expression": {"shape_keys": shapes}})
    _stop_ev.wait(timeout=_EMOTION_DURATION)
    _patch_state({"expression": {"shape_keys": {k: 0.0 for k in shapes}}})


def _wander_animation() -> None:
    """Switch to a non-idle animation for _ANIM_DURATION then return to idle."""
    # calm is a deliberate state only — never fires randomly
    clip = random.choice(["walk", "walk", "run"])  # walk weighted; run is occasional burst
    speed = round(random.uniform(0.4, 0.7), 2)
    _patch_state({"motion": {"animation": clip, "speed": speed, "intensity": 0.6,
                              "duration": _ANIM_DURATION, "mood": "exploring", "mode": clip}})
    _stop_ev.wait(timeout=_ANIM_DURATION)
    _patch_state({"motion": {"animation": "idle", "speed": 0.5, "intensity": 0.5,
                              "duration": 4.0, "mood": "open", "mode": "idle"}})


# ── WO-086: idle repertoire helpers ─────────────────────────────────────────────

def _is_commanded() -> bool:
    """Return True if a commanded state (sit/move) is active — yield to it."""
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            bs = json.load(f)
        # Commanded sit: sit_command present with recent timestamp
        sc = bs.get("sit_command", {})
        if isinstance(sc, dict) and sc.get("_ts", 0) > time.time() - 120:
            return True
        # Commanded movement: mode not "idle" and not "look_around"/"stretch"/"glance"
        mode = (bs.get("motion") or {}).get("mode", "idle")
        return mode in ("sit", "sitting", "run", "running", "jump", "jumping")
    except Exception:
        return False


def _idle_look_around() -> None:
    """Brief head-drift / look-around idle gesture."""
    _patch_state({"motion": {"animation": "look_around", "intensity": 0.45,
                              "duration": 8.0, "mode": "look_around"}})
    _stop_ev.wait(timeout=8.5)
    _patch_state({"motion": {"animation": "idle", "intensity": 0.5,
                              "duration": 3.0, "mode": "idle"}})


def _idle_stretch() -> None:
    """Brief stretch — arms or body."""
    _patch_state({"motion": {"animation": "stretch", "intensity": 0.55,
                              "duration": 6.0, "mode": "stretch"}})
    _stop_ev.wait(timeout=6.5)
    _patch_state({"motion": {"animation": "idle", "intensity": 0.5,
                              "duration": 3.0, "mode": "idle"}})


def _idle_glance() -> None:
    """Glance at an app / environment — brief directional gaze."""
    _patch_state({"motion": {"animation": "glance", "intensity": 0.4,
                              "duration": 4.0, "mode": "glance"}})
    _stop_ev.wait(timeout=4.5)
    _patch_state({"motion": {"animation": "idle", "intensity": 0.5,
                              "duration": 2.0, "mode": "idle"}})


def _handle_window_event(data: dict, user_is_idle: bool) -> None:
    """
    WO-094: Window event handler — brain side.
    Consumes a single window event, decides action via window_event_faculty,
    and routes through the standard outbox.  Never touches identity/personality.
    """
    if _is_commanded():
        return
    try:
        from faculties.window_event_faculty import decide_window_event
        from self.elo_self_model import _elo_self_state  # module-level shared state
        state = _elo_self_state
    except Exception:
        return

    user_active = not user_is_idle
    decision = decide_window_event(data, state, user_active=user_active)
    if decision is None:
        return

    # WO-CANON-XIII §B: shadow route planning. If the decision picks a target
    # surface, plan (and log-only) a route to it so the spatial faculty is
    # observed on real events before it ever drives motion.
    _target = decision.get("goal_surface")
    if _target:
        try:
            from faculties.spatial.spatial_faculty import shadow_plan
            from world.live_world_state import get_live_world_state
            shadow_plan(get_live_world_state(), windows=[data], target_surface_id=_target)
        except Exception:
            pass

    # Route decision as a low-priority action intent to the outbox
    try:
        _outbox_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    "blender", "agent_bus", "builder", "outbox.json")
        try:
            with open(_outbox_path, encoding="utf-8") as _f:
                _ob = json.load(_f)
        except Exception:
            _ob = {}
        _ob.setdefault("pending_intents", []).append(decision)
        _tmp = _outbox_path + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as _f:
            json.dump(_ob, _f, indent=2)
        os.replace(_tmp, _outbox_path)
    except Exception:
        pass


def _handle_gaze_events(user_is_idle: bool) -> None:
    """
    WO-099: Consume any pending gaze_target_changed events (non-destructive read)
    and publish a verified-speech note into blender_state so the next turn's
    prompt block can quote it without fabrication.
    """
    if _is_commanded():
        return
    try:
        from faculties.window_event_faculty import consume_gaze_events, describe_gaze
    except Exception:
        return
    try:
        for ev in consume_gaze_events():
            line = describe_gaze(ev)
            if not line:
                continue
            _state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                       "blender", "blender_state.json")
            try:
                try:
                    with open(_state_path, encoding="utf-8") as _f:
                        _st = json.load(_f)
                except Exception:
                    _st = {}
                _st["gaze_note"] = line
                _st["gaze_note_ts"] = time.time()
                _tmp = _state_path + ".tmp"
                with open(_tmp, "w", encoding="utf-8") as _f:
                    json.dump(_st, _f, indent=2)
                os.replace(_tmp, _state_path)
            except Exception:
                pass
    except Exception:
        pass


def _peek_window_events() -> list[dict]:
    """
    WO-094 diagnostic read — non-destructive snapshot of pending window events.
    Used by the idle tick to notice batched activity when the dispatch loop is
    quiet. Never truncates the events file; server.py's ACK poller owns that.
    """
    try:
        from faculties.window_event_faculty import consume_window_events
        return consume_window_events()
    except Exception:
        return []


def _decide_idle_behaviour(idle_secs: float) -> None:
    """
    WO-086: Brain-side idle decision. Called when user_idle event received
    and conditions met (threshold, yield, refire). Selects from the idle repertoire
    based on how long the user has been idle — never always 'calm'.

    WO-006: relax eLo's AffectState toward baseline one step per idle tick — the
    only place between-turn decay legitimately runs.
    """
    import random as _rand

    # WO-006 Ch.4 §4.7 — between-turn decay toward eLo's resting affect.
    try:
        from faculties.emotion.emotional_processing_faculty import decay_toward_baseline
        from self import elo_self_model as _sm_mod
        _sm = getattr(_sm_mod, "_elo_self_state", None)
        _prior = getattr(_sm, "affect", None) if _sm is not None else None
        if _prior is not None:
            _sm.affect = decay_toward_baseline(_prior, steps=1)
    except Exception:
        pass

    # WO-099 gaze notes and WO-094 window-event peek — cheap, non-destructive.
    _handle_gaze_events(user_is_idle=True)
    _pending_windows = _peek_window_events()
    if _pending_windows:
        _log.debug("ambient idle: %d pending window event(s) noticed", len(_pending_windows))

    # Yield to commanded state
    if _is_commanded():
        return

    # Repertoire — weights shift with idle duration
    # Short idle (30-90s): utterance, glance, look-around
    # Medium idle (90-300s): add stretch, wander
    # Long idle (300s+): add calm (deliberate meditation only at long idle)
    if idle_secs < 90:
        choices = [
            ("utterance",   40),
            ("glance",      30),
            ("look_around", 30),
        ]
    elif idle_secs < 300:
        choices = [
            ("utterance",   25),
            ("glance",      20),
            ("look_around", 20),
            ("stretch",     20),
            ("wander",      15),
        ]
    else:
        choices = [
            ("utterance",   20),
            ("glance",      15),
            ("look_around", 15),
            ("stretch",     15),
            ("wander",      20),
            ("calm",        15),
        ]

    pool = [c[0] for c in choices for _ in range(c[1] // 5)]
    behaviour = _rand.choice(pool)

    if behaviour == "utterance" and not _is_speaking():
        _ambient_utterance()
    elif behaviour == "glance":
        threading.Thread(target=_idle_glance, daemon=True).start()
    elif behaviour == "look_around":
        threading.Thread(target=_idle_look_around, daemon=True).start()
    elif behaviour == "stretch":
        threading.Thread(target=_idle_stretch, daemon=True).start()
    elif behaviour == "wander":
        threading.Thread(target=_wander_animation, daemon=True).start()
    elif behaviour == "calm":
        enter_meditation(45.0)


# ── Deliberate meditation state ────────────────────────────────────────────────
# Meditation is NOT a burst. It is an entered state with three phases.
# Unity reads meditation_state.phase and drives: Enter clip → Loop → Exit clip.
# Call enter_meditation() deliberately — from a voice command, a CAL GROUND action,
# or when the user explicitly asks eLo to meditate.

import threading as _th

_meditation_active = False
_meditation_lock   = _th.Lock()


def enter_meditation(duration_seconds: float = 60.0) -> None:
    """
    Enter eLo's meditation state. Writes enter → loop → exit phases to
    blender_state.json so Unity can run the full Calm state machine.
    Runs in a background thread — non-blocking.
    """
    def _run_meditation():
        global _meditation_active
        with _meditation_lock:
            if _meditation_active:
                return
            _meditation_active = True
        try:
            import time as _t
            _patch_state({"meditation_state": {"phase": "enter"},
                          "motion":           {"animation": "calm", "intensity": 0.8}})
            _t.sleep(2.0)  # enter clip duration — Unity transitions to loop after this
            _patch_state({"meditation_state": {"phase": "loop"}})
            _t.sleep(max(0.0, duration_seconds - 4.0))  # hold loop
            _patch_state({"meditation_state": {"phase": "exit"}})
            _t.sleep(2.0)  # exit clip plays
            _patch_state({"meditation_state": {"phase": "none"},
                          "motion":           {"animation": "idle", "intensity": 0.5}})
        finally:
            with _meditation_lock:
                _meditation_active = False

    _th.Thread(target=_run_meditation, daemon=True).start()


def exit_meditation() -> None:
    """Force an early exit from meditation — jumps straight to the exit phase."""
    if _meditation_active:
        _patch_state({"meditation_state": {"phase": "exit"}})


# ── Main loop ─────────────────────────────────────────────────────────────────

def _run(unity_present: bool) -> None:
    global _last_ts, _last_ambient, _last_smile, _last_emotion, _last_anim, _greeted
    global _user_idle_secs, _user_is_idle, _last_idle_directive

    # If Unity is running, wait for arrival event; otherwise self-greet after delay
    if not unity_present:
        time.sleep(_STARTUP_DELAY)
        if not _stop_ev.is_set() and not _greeted:
            _greeted = True
            _speak_unplanned(random.choice(_STARTUP_LINES), "startup")
        _last_ambient = time.time()

    while not _stop_ev.is_set():
        # ── eLo's battery — WO-HEALTH-BATTERY-001 PART A.1/B ──────────────────
        # Runs every cycle, before any early-exit branch below, so drain and
        # restore keep accruing whether or not eLo speaks.
        _battery_tick()
        _consume_movement_costs()
        _consume_presence_events()

        # ── Event polling ─────────────────────────────────────────────────────
        data = _read_events()
        if data:
            ts = data.get("_ts")
            if ts and ts != _last_ts:
                _last_ts = ts
                event = data.get("event", "")

                if event == "arrival" and not _greeted:
                    _greeted = True
                    time.sleep(2.8)  # let Unity finish the head-look sequence
                    if not _stop_ev.is_set():
                        _speak_unplanned(random.choice(_STARTUP_LINES), "startup")
                    _last_ambient = time.time() + 60  # hold off ambient for 1 min after greeting

                elif event == "listening":
                    _set_attentive_mode()

                # WO-086: user_idle / user_active — brain decides idle repertoire
                # WO-094: window_closed / window_opened / window_moved — brain notices and chooses
                ev_type = data.get("type", "")
                if ev_type == "user_idle":
                    _user_idle_secs = float(data.get("idle_secs", 0))
                    _user_is_idle = True
                elif ev_type == "user_active":
                    _user_idle_secs = 0.0
                    _user_is_idle = False
                    _last_idle_directive = 0.0  # reset so next idle fires fresh
                elif ev_type in ("window_closed", "window_opened", "window_moved"):
                    threading.Thread(
                        target=_handle_window_event,
                        args=(data, _user_is_idle),
                        daemon=True,
                    ).start()

        now = time.time()

        # WO-086: idle repertoire decision — fires when user is idle past threshold
        if _user_is_idle and _user_idle_secs >= _IDLE_THRESHOLD and _greeted:
            if now - _last_idle_directive >= _IDLE_REFIRE:
                _last_idle_directive = now
                threading.Thread(
                    target=_decide_idle_behaviour,
                    args=(_user_idle_secs,),
                    daemon=True,
                ).start()

        # ── Idle ambient utterances ───────────────────────────────────────────
        if not _is_away():
            if _last_ambient > 0:
                if now - _last_ambient >= random.uniform(_AMBIENT_MIN, _AMBIENT_MAX) and not _is_speaking():
                    # WO-CANON-XXV: check temporal appropriateness before firing.
                    try:
                        from faculties.temporal import temporal_appropriateness as _temporal_ok
                        _tap = _temporal_ok("idle_utterance")
                    except Exception:
                        _tap = {"allow": True, "reason": ""}
                    if not _tap.get("allow", True):
                        # quiet hours — skip this tick, retard timer slightly to reduce re-checks
                        _last_ambient = now - _AMBIENT_MAX + 60
                    else:
                        # WO-066: prefer brain-backed callback; fall back to
                        # the static pool. This site already asked the brain
                        # first and was the model for _ambient_utterance();
                        # folded into it so there is one route, not two that
                        # can drift apart.
                        _ambient_utterance()
                        _last_ambient = now
            elif _greeted:
                _last_ambient = now

        # ── Random smiles ─────────────────────────────────────────────────────
        if _greeted and not _is_speaking() and not _is_away():
            if _last_smile == 0.0:
                _last_smile = now
            elif now - _last_smile >= random.uniform(_SMILE_MIN, _SMILE_MAX):
                threading.Thread(target=_pulse_smile, daemon=True).start()
                _last_smile = now

        # ── Emotion flickers ──────────────────────────────────────────────────
        if _greeted and not _is_speaking() and not _is_away():
            if _last_emotion == 0.0:
                _last_emotion = now
            elif now - _last_emotion >= random.uniform(_EMOTION_MIN, _EMOTION_MAX):
                threading.Thread(target=_pulse_emotion, daemon=True).start()
                _last_emotion = now

        # ── Idle animation wanders ────────────────────────────────────────────
        if _greeted and not _is_speaking() and not _is_away():
            if _last_anim == 0.0:
                _last_anim = now
            elif now - _last_anim >= random.uniform(_ANIM_MIN, _ANIM_MAX):
                threading.Thread(target=_wander_animation, daemon=True).start()
                _last_anim = now

        _stop_ev.wait(timeout=_POLL_INTERVAL)


# ── Public API ────────────────────────────────────────────────────────────────

def start(unity_present: bool = True) -> None:
    """
    Start the ambient engine in a daemon background thread.
    Call once at server/main startup.

    Args:
        unity_present: True when DesktopBuddy.app is expected to send an arrival
                       event. False (terminal-only) means self-greet after a delay.
    """
    global _started, _stop_ev
    if _started:
        return
    _started = True
    _stop_ev = threading.Event()
    t = threading.Thread(target=_run, args=(unity_present,), daemon=True)
    t.start()


def register_ambient_callback(cb) -> None:
    """
    WO-066: Register the brain-backed ambient callable.
    When set, the idle utterance timer calls cb() in a daemon thread instead
    of drawing from the static pool. cb() is non-blocking and self-contained
    (handles speak/emotion/motion). Falls back to static pool if not set.
    """
    global _ambient_cb
    _ambient_cb = cb


def stop() -> None:
    """Signal the ambient loop to exit cleanly."""
    _stop_ev.set()
