"""
ambient/ambient_engine.py — Phase 3 ambient presence for eLo OS.

Runs as a background thread inside server.py / main.py.
Behaviours:
  1. Startup greeting — speaks once on arrival signal from Unity (or after 4s delay).
  2. Idle ambient utterances — every 8-20 minutes.
  3. Random smiles — patches smile blendshapes every 2-5 minutes for 3-4s then clears.
  4. Idle animation wander — occasionally switches to walk/calm then back to idle.
  5. Unity event polling — watches unity_events.json for DesktopBuddy triggers.
"""
from __future__ import annotations

import json
import os
import random
import threading
import time

# ── Config ────────────────────────────────────────────────────────────────────

_EVENTS_PATH  = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "blender", "unity_events.json")
_POLL_INTERVAL  = 0.5       # seconds between event file polls
_AMBIENT_MIN    = 8 * 60    # min seconds between ambient utterances
_AMBIENT_MAX    = 20 * 60   # max seconds between ambient utterances
_SMILE_MIN      = 2 * 60    # min seconds between random smiles
_SMILE_MAX      = 5 * 60    # max seconds between random smiles
_SMILE_DURATION = 3.5       # seconds to hold the smile before clearing
_ANIM_MIN       = 3 * 60    # min seconds between idle animation wanders
_ANIM_MAX       = 8 * 60    # max seconds between idle animation wanders
_ANIM_DURATION  = 8.0       # seconds to hold wander animation before returning to idle
_STARTUP_DELAY  = 4.0       # seconds to wait for Unity arrival event before auto-greeting

# ── Speech pools ──────────────────────────────────────────────────────────────

_STARTUP_LINES = [
    "Oh, it's nice here. Nice little place to call home.",
    "Here we are. Good to be back.",
    "Ah. Here we go.",
    "Oh — there you are.",
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
]

# ── Internal state ────────────────────────────────────────────────────────────

_started      = False
_last_ts      = None
_last_ambient = 0.0
_last_smile   = 0.0
_last_anim    = 0.0
_stop_ev      = threading.Event()
_greeted      = False

_STATE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "blender", "blender_state.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _wander_animation() -> None:
    """Switch to a non-idle animation for _ANIM_DURATION then return to idle."""
    clip = random.choice(["walk", "calm", "calm"])  # calm weighted more — meditative
    speed = round(random.uniform(0.4, 0.7), 2)
    _patch_state({"motion": {"animation": clip, "speed": speed, "intensity": 0.6,
                              "duration": _ANIM_DURATION, "mood": "exploring", "mode": clip}})
    _stop_ev.wait(timeout=_ANIM_DURATION)
    _patch_state({"motion": {"animation": "idle", "speed": 0.5, "intensity": 0.5,
                              "duration": 4.0, "mood": "open", "mode": "idle"}})


# ── Main loop ─────────────────────────────────────────────────────────────────

def _run(unity_present: bool) -> None:
    global _last_ts, _last_ambient, _last_smile, _last_anim, _greeted

    # If Unity is running, wait for arrival event; otherwise self-greet after delay
    if not unity_present:
        time.sleep(_STARTUP_DELAY)
        if not _stop_ev.is_set() and not _greeted:
            _greeted = True
            _speak(random.choice(_STARTUP_LINES))
        _last_ambient = time.time()

    while not _stop_ev.is_set():
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

        now = time.time()

        # ── Idle ambient utterances ───────────────────────────────────────────
        if _last_ambient > 0:
            if now - _last_ambient >= random.uniform(_AMBIENT_MIN, _AMBIENT_MAX) and not _is_speaking():
                _speak(random.choice(_AMBIENT_LINES))
                _last_ambient = now
        elif _greeted:
            _last_ambient = now

        # ── Random smiles ─────────────────────────────────────────────────────
        if _greeted and not _is_speaking():
            if _last_smile == 0.0:
                _last_smile = now
            elif now - _last_smile >= random.uniform(_SMILE_MIN, _SMILE_MAX):
                threading.Thread(target=_pulse_smile, daemon=True).start()
                _last_smile = now

        # ── Idle animation wanders ────────────────────────────────────────────
        if _greeted and not _is_speaking():
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


def stop() -> None:
    """Signal the ambient loop to exit cleanly."""
    _stop_ev.set()
