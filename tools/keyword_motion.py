"""
tools/keyword_motion.py — keyword-driven animation burst system.

Scans user input for emotional keywords and triggers short-lived body animation
bursts that layer over eLo's base presence state. Designed to make eLo feel
more human — his body reacts to what you're saying, not just what he thinks.

RULE: Never touches CAL, attention, presence engine, state machine, or identity.
Only patches blender_state.json for a fixed duration then reverts. This is
exactly the same mechanism as ambient_engine's pulse_smile() — a time-boxed
override that dissolves back to base state automatically.

Architecture:
    server.py calls scan(user_input) after the LLM response is generated.
    If a match is found, a daemon thread applies the burst async — it does
    not block response delivery.

Head motion system:
    head_motion key is written alongside expression/motion patches.
    Unity reads blender_state.json → head_motion and drives c_head.x / c_head.z
    as a coroutine — the same bone EloHeadLook.cs already moves for cursor tracking.
    No Blender NLA clip needed. Unity owns the execution.

    head_motion values → Unity coroutine:
        "nod"    — c_head.x down→up→settle  (0.8s, 2 bobs)
        "shake"  — c_head.z left→right→settle (0.6s, 2 oscillations)
        "tilt"   — c_head.z lean hold (1.5s) then ease back
        "think"  — slow c_head.z drift + c_head.x slight drop (2.5s)
        "lookup" — c_head.x lift upward (1.2s) — curiosity / idea moment

Animation clips (require Blender NLA export + Unity Animator state):
    idle       — gentle breathe (available)
    walk       — positive forward energy (available)
    run        — excited burst (available)
    calm       — grounding, meditation (available)
    longjump   — surprise / big moment — eLo_LongJ (available)

Planned Blender clips (full-body, need export):
    wave       — greeting, triggered on arrival
    stretch    — tired / waking up idle variant
    celebrate  — arms-up victory burst
    worried    — contracted posture, slight lean forward

Expression patches (blendshape keys already available):
    Smile.L / Smile.R / Satisfied / LittleJoy — positive
    Angry / Worried — negative / tense
    All keys as floats 0.0–1.0
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import logging
from typing import Optional

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")

# ── emotion keyword → motion intent ───────────────────────────────────────────
# Each entry: (pattern_list, animation, duration_sec, expression_patch, head_motion)
# head_motion is optional — None means no head gesture.
# First match wins.

_KEYWORD_MAP = [
    # Excitement / amazement — run burst + lookup (idea moment)
    (
        [r"\b(wow|amazing|incredible|unbelievable|holy|oh my|no way|seriously)\b",
         r"\b(excited|excitement|can't believe|blown away)\b"],
        "run", 3.0,
        {"Smile.L": 0.85, "Smile.R": 0.85, "Satisfied": 0.6},
        "lookup",
    ),
    # Joy / love / celebration — walk with smile + tilt
    (
        [r"\b(love|wonderful|perfect|brilliant|beautiful|yes!|awesome|fantastic|great news)\b",
         r"\b(so happy|made my day|this is great|thrilled)\b"],
        "walk", 4.0,
        {"Smile.L": 0.75, "Smile.R": 0.75, "LittleJoy": 0.5},
        "tilt",
    ),
    # Big moment / milestone — long jump + lookup
    (
        [r"\b(finally|milestone|shipped|launched|we did it|just finished|done!|completed)\b",
         r"\b(big news|announcement|breaking|major)\b"],
        "longjump", 2.5,
        {"Smile.L": 0.9, "Smile.R": 0.9, "Satisfied": 0.8},
        "lookup",
    ),
    # Agreement / confirmation — walk + nod
    (
        [r"\b(exactly|nailed it|that's it|spot on|yes exactly|totally|absolutely right)\b",
         r"\b(yes|yep|yeah|correct|right|for sure|definitely|agreed)\b"],
        "walk", 2.5,
        {"Smile.L": 0.6, "Smile.R": 0.6, "LittleJoy": 0.4},
        "nod",
    ),
    # Thinking / figuring out — head gesture only (no body clip)
    (
        [r"\b(hmm|let me think|interesting|i wonder|not sure|maybe|perhaps|good question)\b",
         r"\b(thinking|figuring out|working it out|curious)\b"],
        None, 3.0,
        {},
        "think",
    ),
    # Disagreement / uncertainty — head shake only
    (
        [r"\b(no wait|that's not right|actually no|hold on|i don't think so)\b",
         r"\b(not quite|hmm no|wait wait)\b"],
        None, 2.0,
        {"Worried": 0.15},
        "shake",
    ),
    # Calm / peace / breathe / rest — calm clip + tilt
    (
        [r"\b(calm|peace|breathe|relax|meditat|quiet|slow down|rest|take a break)\b",
         r"\b(it's okay|you're okay|breathe|gentle|soft|easy)\b"],
        "calm", 8.0,
        {"Satisfied": 0.4},
        "tilt",
    ),
    # Stress / anxiety — calm grounding + think gesture
    (
        [r"\b(stress|anxious|anxiety|overwhelm|panic|worried|can't cope|struggling)\b",
         r"\b(too much|falling behind|behind schedule|deadline|pressure)\b"],
        "calm", 6.0,
        {"Worried": 0.35, "Satisfied": 0.1},
        "think",
    ),
    # Tired / exhausted — idle + tilt
    (
        [r"\b(tired|exhausted|drained|burnt out|burnout|need sleep|so sleepy)\b"],
        "idle", 5.0,
        {"Worried": 0.2},
        "tilt",
    ),
]

# expressions that must be cleared after a burst
_BURST_EXPRESSION_KEYS = {
    "Smile.L", "Smile.R", "Satisfied", "LittleJoy", "Angry", "Worried",
}


# ── state patching ─────────────────────────────────────────────────────────────

def _patch_state(patch: dict) -> None:
    try:
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r") as f:
                state = json.load(f)
        else:
            state = {}
        _deep_merge(state, patch)
        with open(_STATE_PATH, "w") as f:
            json.dump(state, f)
    except Exception as e:
        _logger.debug("keyword_motion patch failed: %s", e)


def _deep_merge(base: dict, overlay: dict) -> None:
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def _read_base_animation() -> str:
    try:
        with open(_STATE_PATH) as f:
            return json.load(f).get("motion", {}).get("animation", "idle")
    except Exception:
        return "idle"


# ── burst runner ───────────────────────────────────────────────────────────────

def _run_burst(animation: str, duration: float, expr_patch: dict, head_motion: str) -> None:
    base_anim = _read_base_animation()
    # build patch
    patch = {}
    if animation:
        patch["motion"] = {"animation": animation, "duration": duration, "intensity": 0.75}
    if expr_patch:
        expr_full = {"expression": {k: 0.0 for k in _BURST_EXPRESSION_KEYS}}
        _deep_merge(expr_full["expression"], expr_patch)
        patch.update(expr_full)
    if head_motion:
        patch["head_motion"] = {"gesture": head_motion, "ts": int(time.time())}
    _patch_state(patch)
    # hold for duration
    time.sleep(duration)
    # revert
    revert = {"head_motion": {"gesture": "none", "ts": int(time.time())}}
    if animation:
        revert["motion"] = {"animation": base_anim, "duration": 8, "intensity": 0.3}
    if expr_patch:
        revert["expression"] = {k: 0.0 for k in expr_patch}
    _patch_state(revert)


# ── public API ─────────────────────────────────────────────────────────────────

def scan(user_input: str) -> Optional[str]:
    """
    Scan user_input for emotion keywords. If matched, fire an async animation
    burst and return the emotion name. Returns None if no match.

    Non-blocking — the burst runs in a daemon thread so it never delays response.
    """
    text = user_input.lower()
    for patterns, animation, duration, expr_patch, head_motion in _KEYWORD_MAP:
        for pat in patterns:
            if re.search(pat, text):
                t = threading.Thread(
                    target=_run_burst,
                    args=(animation, duration, expr_patch, head_motion),
                    daemon=True,
                )
                t.start()
                return head_motion or animation
    return None
