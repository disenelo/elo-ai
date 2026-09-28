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
            return json.load(f).get("state") in ("CALM_IDLE", "MEDITATION")
    except Exception:
        return False


def _read_state() -> dict:
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


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
        fields["calm_mode"] = bool(_is_calm())

        if fields:
            try:
                from blender_bridge.state_writer import patch as _patch
                _patch(fields)
            except Exception:
                pass
    except Exception:
        pass


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
        with open(_STATE_PATH, encoding="utf-8") as f:
            state = json.load(f)
        for section, values in patch.items():
            if isinstance(values, dict):
                state.setdefault(section, {}).update(values)
            else:
                state[section] = values
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
        _speak(_rand.choice(_AMBIENT_LINES))
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
            _speak(random.choice(_STARTUP_LINES))
        _last_ambient = time.time()

    while not _stop_ev.is_set():
        # ── eLo's battery — WO-HEALTH-BATTERY-001 PART A.1/B ──────────────────
        # Runs every cycle, before any early-exit branch below, so drain and
        # restore keep accruing whether or not eLo speaks.
        _battery_tick()

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
                        _speak(random.choice(_STARTUP_LINES))
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
                        # WO-066: prefer brain-backed callback; fall back to static pool.
                        if _ambient_cb is not None:
                            threading.Thread(target=_ambient_cb, daemon=True).start()
                        else:
                            # 30% chance: draw from quirk bank if it has content
                            line = None
                            if random.random() < 0.30:
                                try:
                                    from memory.quirk_bank import draw as _quirk_draw
                                    drawn = _quirk_draw(1)
                                    if drawn:
                                        line = drawn[0]
                                except Exception:
                                    pass
                            _speak(line or random.choice(_AMBIENT_LINES))
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
