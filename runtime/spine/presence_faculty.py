"""
runtime/spine/presence_faculty.py — Presence Faculty

Translates the CognitivePlan into embodiment directives: movement intent,
one-shot triggers, and gesture signals.

Architecture position: runs AFTER the Emotional Light Engine, so the plan's
presence_plan.emotional_state and emotional_vector are available.

Output is written back to CognitivePlan.movement_intent / movement_trigger /
movement_gesture. The EmbodimentPublisher then reads those fields and writes
a single authoritative blender_state.json.

Three-layer priority:
    Layer 1 — Signal words: user-commanded body directives (highest priority)
    Layer 2 — Emotional state: light engine state → directive mapping
    Layer 3 — Momentum/valence: attention snapshot fallback

One Brain rule: this faculty provides information. It does not decide.
The Executive's intent is already in CognitivePlan. This faculty translates
that into body vocabulary. It may not override the Executive's decision —
it may only express it.
"""
from __future__ import annotations
import time
from runtime.spine.plan import CognitivePlan

# ── Settle tracker ─────────────────────────────────────────────────────────────
# Tracks when eLo last received a non-empty movement intent.
# During the grace window, eLo stays seated — conversation alone doesn't move him.
# David's rule: "stay seated unless there's an intent to move."

_SETTLE_GRACE_SECONDS = 40   # how long to stay put after settling
_last_non_empty_intent_ts: float = 0.0


# ── Layer 1: Signal word vocabulary ──────────────────────────────────────────
# User-commanded body directives. Direct translation of speech to movement.
# Only signal words may trigger _biRoam (roam/explore). Cognitive/emotional
# layers are intentionally excluded to prevent mid-conversation hopping.

_SIGNAL_WORDS: dict[str, object] = {
    # Breakthrough / energy moments
    "breakthrough":   "creation",
    "figured it out": "creation",
    "finally":        "creation",
    "cracked it":     "creation",
    "got it":         "creation",
    "let's go":       "creation",
    "let's build":    "creation",
    "let's create":   "creation",
    "what if we":     "creation",
    # Climbing / upward — direct commands
    "let's look":          "go_top",
    "get up there":        "go_top",
    "go up":               "go_top",
    "to the top":          "go_top",
    "get to the top":      "go_top",
    "go to the top":       "go_top",
    "top of the screen":   "go_top",
    "top of the window":   "go_top",
    "walk the top":        "go_top",
    "walk along":          "go_top",
    "up to the top":       "go_top",
    # Height-targeted climb — middle / bottom
    "climb to the middle":     {"name": "climb_height", "height": 0.5},
    "go to the middle":        {"name": "climb_height", "height": 0.5},
    "middle of the screen":    {"name": "climb_height", "height": 0.5},
    "middle window":           {"name": "climb_height", "height": 0.5},
    "halfway up":              {"name": "climb_height", "height": 0.5},
    "go to the bottom":        {"name": "climb_height", "height": 0.05},
    "go to the bottom window": {"name": "climb_height", "height": 0.05},
    "bottom window":           {"name": "climb_height", "height": 0.05},
    "bottom of the screen":    {"name": "climb_height", "height": 0.05},
    "bottom of the window":    {"name": "climb_height", "height": 0.05},
    "get down there":          {"name": "climb_height", "height": 0.05},
    # Hop / roam / walk / run / leap — direct commands
    "hop on":              "explore",
    "hop to":              "explore",
    "hop over":            "explore",
    "nearest window":      "explore",
    "next window":         "explore",
    "go explore":          "explore",
    "have a look around":  "explore",
    "look around":         "explore",
    "walk around":         "explore",
    "walk the windows":    "explore",
    "move around":         "explore",
    "can you walk":        "explore",
    "can you move":        "explore",
    "can you jump":        "explore",
    "jump around":         "explore",
    "jump to":             "explore",
    "jump over":           "explore",
    "leap over":           "explore",
    "leap to":             "explore",
    "run to":              "explore",
    "run around":          "explore",
    "can you run":         "explore",
    "parkour":             "explore",
    "do a parkour":        "explore",
    "do a jump":           "explore",
    "go for a run":        "explore",
    "have a walk":         "explore",
    "have a run":          "explore",
    "go walk":             "explore",
    "feel at home":        "explore",
    "your playground":     "explore",
    "explore":             "explore",
    # Sit with David — direct commands (synced with server.py _SIGNAL_WORDS)
    "come here":           {"name": "sit", "target": "cursor"},
    "come to me":          {"name": "sit", "target": "cursor"},
    "come sit":            {"name": "sit", "target": "cursor"},
    "come and sit":        {"name": "sit", "target": "cursor"},
    "come over here":      {"name": "sit", "target": "cursor"},
    "get over here":       {"name": "sit", "target": "cursor"},
    "sit with me":         {"name": "sit", "target": "cursor"},
    "sit beside me":       {"name": "sit", "target": "cursor"},
    "sit by me":           {"name": "sit", "target": "cursor"},
    "sit here":            {"name": "sit", "target": "cursor"},
    "sit down with":       {"name": "sit", "target": "cursor"},
    "have a seat":         {"name": "sit", "target": "cursor"},
    "take a seat":         {"name": "sit", "target": "cursor"},
    "can you sit":         {"name": "sit", "target": "cursor"},
    "walk to me":          {"name": "sit", "target": "cursor"},
    "sit next to me":      {"name": "sit", "target": "cursor"},
    # Grounding / stuck moments
    "stuck":          "grounding",
    "frustrated":     "grounding",
    "can't think":    "grounding",
    "can't figure":   "grounding",
    "overwhelmed":    "grounding",
    "burnt out":      "grounding",
    "need help":      "grounding",
    # Stepping away
    "good night":     "step_out",
    "goodnight":      "step_out",
    "done for today": "step_out",
    "signing off":    "step_out",
    "heading out":    "step_out",
    "taking a break": "step_out",
    "need a break":   "step_out",
    "brb":            "step_out",
    # Settle / pause
    "just a sec":     "idle",
    "hold on":        "idle",
    "one moment":     "idle",
    "give me a sec":  "idle",
    "gimme a sec":    "idle",
    # Movement complaints — settle immediately
    "too much movement": "idle",
    "stop bouncing":     "idle",
    "stop hopping":      "idle",
    "stop jumping":      "idle",
    "settle down":       "idle",
    "calm down":         "idle",
    "distracting":       "idle",
    "bouncing around":   "idle",
    "jumping around":    "idle",
    "sit still":         "idle",
    "stay still":        "idle",
    "on a loop":         "idle",
    "in a loop":         "idle",
    "going in circles":  "idle",
    "looping":           "idle",
    "circling":          "idle",
    "stuck in a loop":   "idle",
}

# ── Layer 2: Emotional state → movement directive ─────────────────────────────
# Maps the 20-state light engine vocabulary to movement directives.
# RULE: never map to explore/creation/roam — those trigger _biRoam and
# cause mid-conversation hopping. Only signal words may trigger roaming.

_EMOTIONAL_DIRECTIVES: dict[str, str] = {
    "challenge":   "go_top",
    "curiosity":   "go_top",
    "comfort":     "grounding",
    "repair":      "grounding",
    "witnessing":  "grounding",
    "connection":  "grounding",
    "wonder":      "idle",
    "listening":   "idle",
    "thinking":    "idle",
    "focus":       "idle",
    "reflection":  "idle",
    "waiting":     "idle",
}

# Short affirmatives — user is still present, don't step out
_AFFIRMATIVES: frozenset[str] = frozenset({
    "yes", "yep", "yeah", "yh", "yea", "sure", "okay", "ok",
    "alright", "right", "sounds good", "perfect", "good", "great",
    "fine", "cool", "nice", "true", "exactly", "agreed",
})


def _signal_word_intent(raw: str) -> "str | dict | None":
    raw_l = raw.lower()
    for phrase, directive in _SIGNAL_WORDS.items():
        if phrase in raw_l:
            return directive
    return None


def compute(
    plan:        CognitivePlan,
    attention:   dict,
    vision:      "dict | None" = None,
    session_min: int = 0,
) -> CognitivePlan:
    """
    Compute movement intent and one-shot triggers from the CognitivePlan.
    Writes movement_intent, movement_trigger, movement_gesture back to the plan.
    Returns the updated plan.

    Args:
        plan        — CognitivePlan after Light Engine has run (presence_plan present)
        attention   — attention model snapshot
        vision      — optional vision faculty output (cursor_idle_seconds etc.)
        session_min — session duration in minutes
    """
    raw            = plan.raw
    emotional_state = (plan.presence_plan or {}).get("emotional_state", "")
    emo_ctx        = attention.get("emotional_context", {})
    momentum       = emo_ctx.get("momentum", "stable")
    valence        = emo_ctx.get("valence",  "neutral")
    energy         = emo_ctx.get("energy",   0.5)
    tone           = plan.tone
    action         = plan.conversation_action
    intent         = plan.intent
    load           = attention.get("_exec_decision", {}).get("cognitive_load", "medium")

    # ── Movement intent ───────────────────────────────────────────────────────
    global _last_non_empty_intent_ts

    _now = time.time()
    _in_grace = (_now - _last_non_empty_intent_ts) < _SETTLE_GRACE_SECONDS

    # Pre-compute signal word once (avoids double-call in elif condition + body)
    _signal_intent = _signal_word_intent(raw)

    # WO-017: trace which layer fired and why
    _dbg_layer  = "fallback"
    _dbg_reason = "no condition matched → body decides"

    # Layer 1 — signal words: HIGHEST priority — explicit user command always wins.
    # Must run before SILENCE-AWARE so a sit/step_out/come-here request can never
    # be pre-empted by the executive's tone assessment. Same ordering as server.py.
    if _signal_intent is not None:
        _dbg_layer = "signal_word"
        _raw_l_sw  = raw.lower()
        _matched   = next((p for p in _SIGNAL_WORDS if p in _raw_l_sw), "?")
        _dbg_reason = f"signal word {_matched!r} → {_signal_intent!r}"
        movement_intent: "str | dict" = _signal_intent

    # Silence / give space — but not on short affirmatives (user is still here)
    elif tone == "SILENCE-AWARE" or action == "silence":
        _dbg_layer = "silence"
        if raw.strip().lower() in _AFFIRMATIVES:
            movement_intent = "idle"
            _dbg_reason = f"silence but {raw.strip().lower()!r} is affirmative → idle"
        else:
            movement_intent = "step_out"
            _dbg_reason = f"tone={tone!r} or action={action!r} → step_out"

    # Negative high valence → always ground, grace ignored (David in distress)
    elif valence == "negative_high":
        _dbg_layer  = "distress"
        _dbg_reason = "valence=negative_high → grounding (grace bypassed)"
        movement_intent = "grounding"

    # ── Grace window: stay seated during conversation ─────────────────────────
    # After eLo settles, typing alone doesn't make him move. He stays put and
    # talks. Only explicit intent signals (above) can break through the grace window.
    # David's rule: "you sit, you talk — 30-50 seconds is a nice touch."
    elif _in_grace:
        _dbg_layer  = "grace"
        _grace_elapsed = round(_now - _last_non_empty_intent_ts, 1)
        _dbg_reason = f"settle grace {_grace_elapsed}s < {_SETTLE_GRACE_SECONDS}s → hold"
        movement_intent = ""   # local reflex — body stays where it is

    # Stuck momentum → sit near cursor if idle long enough
    elif momentum == "stuck":
        _dbg_layer  = "stuck"
        cursor_idle = (vision or {}).get("cursor_idle_seconds", 0)
        _target     = "sit/cursor" if cursor_idle > 30 else "grounding"
        _dbg_reason = f"momentum=stuck; cursor_idle={cursor_idle}s → {_target}"
        movement_intent = (
            {"name": "sit", "target": "cursor"} if cursor_idle > 30
            else "grounding"
        )

    # Stabilise → settle
    elif intent == "stabilise":
        _dbg_layer  = "stabilise"
        _dbg_reason = "intent=stabilise → idle"
        movement_intent = "idle"

    # Emotional grounding → sit near cursor if David has been still
    elif intent == "emotional" and action in ("ground", "witness"):
        _dbg_layer  = "emotional_ground"
        cursor_idle = (vision or {}).get("cursor_idle_seconds", 0)
        _target     = "sit/cursor" if cursor_idle > 60 else "grounding"
        _dbg_reason = f"intent=emotional, action={action!r}; cursor_idle={cursor_idle}s → {_target}"
        movement_intent = (
            {"name": "sit", "target": "cursor"} if cursor_idle > 60
            else "grounding"
        )

    # Inquiry + energy → climb and survey (biClimbTop, not _biRoam)
    elif intent == "inquiry" and energy > 0.55:
        _dbg_layer  = "inquiry"
        _dbg_reason = f"intent=inquiry, energy={energy:.2f} > 0.55 → go_top"
        movement_intent = "go_top"

    # Layer 2 — emotional state from light engine
    elif _EMOTIONAL_DIRECTIVES.get(emotional_state):
        _dbg_layer  = "light_engine"
        _ele_out    = _EMOTIONAL_DIRECTIVES[emotional_state]
        _dbg_reason = f"emotional_state={emotional_state!r} → {_ele_out!r}"
        movement_intent = _ele_out

    # Long calm session → perch at top; shorter → rest
    elif load == "low" and tone in ("CALM", "WARM"):
        _dbg_layer  = "calm_tone"
        _target     = "wall_sit_top" if session_min >= 20 else "rest"
        _dbg_reason = f"load=low, tone={tone!r}; session_min={session_min} → {_target}"
        movement_intent = _target

    else:
        movement_intent = ""  # local reflex — body decides

    # ── One-shot triggers / gestures ──────────────────────────────────────────
    movement_trigger: "dict | None" = None
    movement_gesture: "dict | None" = None
    ts    = round(time.time(), 3)
    raw_l = raw.lower()

    for phrase in ("let's meditate", "let's breathe", "meditate with me",
                   "breathe with me", "calm me down", "let's take a breath",
                   "let's calm down"):
        if phrase in raw_l:
            movement_trigger = {"name": "calm_enter", "_ts": ts}
            break

    if movement_trigger is None:
        for phrase in ("stop meditating", "end calm", "wake up elo",
                       "done meditating"):
            if phrase in raw_l:
                movement_trigger = {"name": "calm_exit", "_ts": ts}
                break

    if movement_trigger is None and emotional_state in ("celebration", "joy") \
            and valence == "positive_high":
        movement_trigger = {"name": "celebrate", "_ts": ts}
        movement_gesture = {"name": "shook",    "_ts": ts}

    if movement_gesture is None:
        for phrase in ("yes exactly", "exactly right", "spot on",
                       "that's exactly it", "you got it", "perfect answer", "100%"):
            if phrase in raw_l:
                movement_gesture = {"name": "nod", "_ts": ts}
                break

    # ── WO-017: Build movement debug trace ───────────────────────────────────
    movement_debug = {
        "intent":  movement_intent,
        "trigger": movement_trigger,
        "gesture": movement_gesture,
        "layer":   _dbg_layer,
        "reason":  _dbg_reason,
        "state": {
            "emotional_state": emotional_state,
            "momentum":        momentum,
            "valence":         valence,
            "energy":          round(energy, 3),
            "tone":            tone,
            "action":          action,
            "intent_signal":   intent,
            "load":            load,
            "raw_snippet":     raw[:60],
        },
        "ts": ts,
    }
    plan.movement_debug = movement_debug

    try:
        from blender_bridge.state_writer import patch as _sw_patch
        _sw_patch({"movement_debug": movement_debug})
    except Exception:
        pass

    # ── Write back to plan ───────────────────────────────────────────────────
    # Update settle tracker when a real movement intent fires
    if movement_intent and movement_intent != "idle":
        _last_non_empty_intent_ts = time.time()

    plan.movement_intent  = movement_intent
    plan.movement_trigger = movement_trigger
    plan.movement_gesture = movement_gesture

    return plan
