"""
server.py — eLo OS HTTP interface.

Exposes the same cognitive cycle as main.py over HTTP on localhost:5050.
Unity (or any client) POSTs text → gets eLo's response back as JSON.
Animation drives simultaneously via blender_state.json as normal.

Run:
    python server.py

Endpoints:
    POST /chat        {"text": "hello"}  →  {"response": "...", "mode": "...", "backend": "..."}
    GET  /status      →  {"status": "ok", "session": N, "backend": "..."}
    GET  /ping        →  {"ok": true}
"""

import os
import sys
import json
import time
import random
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ── bootstrap (same as main.py) ───────────────────────────────────────────────

def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_dotenv()

import logging as _logging
_logging.basicConfig(
    level=_logging.WARNING,
    format="[%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)

from memory import state_manager
from memory.obsidian_loader import get_context_block
from memory.memory_pack_builder import build as build_memory_pack
from core import attention as attn
from runtime.executive import decide as exec_decide
from runtime import state_machine as sm
from runtime.prompt_builder import build as build_prompt
from runtime.backend_router import route as router_route, route_streaming as _route_streaming, active_backend, normalise
from tools.tool_router import enrich as _tool_enrich
from tools.keyword_motion import scan as _keyword_motion_scan
from memory.quirk_bank import maybe_generate as _quirk_observe
from elo_personality_engine.skeleton_generator import ObservationStore as _ObsStore, generate_skeleton as _gen_skeleton, export_skeleton as _export_skeleton
from knowledge.graph_loader import build_context as graph_context
from backends.mock_backend import MockBackend as _MockBackend, EXIT_POOL as _EXIT_POOL
from avatar.presence_engine    import compute as _presence_compute, reset as _presence_reset
from avatar.motion_mapper      import map     as _motion_map
from avatar.animation_router   import route   as _avatar_route
from avatar.behaviour_protocol import BehaviourGate as _BehaviourGate
from core.pattern_observer     import log as _obs_log, observe as _obs_observe, reset as _obs_reset, get_log as _obs_get_log
from core.continuity           import get_entity_why as _entity_why, get_viewpoint as _get_viewpoint, cross_session_delta as _session_delta, context_block as _continuity_block, update_from_session as _continuity_update
from presence.presence_engine    import derive as _pstate_derive
from presence.presence_scheduler import PresenceScheduler as _PresenceScheduler
from avatar.avatar_controller    import build_command as _avatar_cmd
from avatar.avatar_rules         import apply as _avatar_rules
from blender_bridge.state_writer import write as _state_write, write_with_presence as _state_write_presence
from expression.expression_mapper import build_expression as _expr_build, map_emotion as _expr_map_emotion
from voice.voice_engine import speak as _voice_speak
from memory import personality_drift as _personality_drift
from elo_personality_engine.injection_layer import load_personality_profile as _load_profile
from self.elo_self_model import (
    load as _self_load, update as _self_update, save as _self_save,
    prompt_block as _self_prompt_block,
    apply_embodiment as _self_apply_embodiment,
    situated_block as _self_situated_block,
    narrative_block as _self_narrative_block,
)

# ── session state (shared across requests, protected by lock) ─────────────────

_lock            = threading.Lock()
_state           = None
_elo_self        = _self_load()   # eLo's own inner state — persists across sessions
_obs_store       = _ObsStore()   # accumulates user messages across this session
_runtime_state   = None
_memory_pack     = {}
_vault_ctx       = ""
_project_ctx     = ""   # active project names → injected into system prompt each turn
_last_inputs     = []
_last_avatar_cmd = None
_last_pp         = None   # last known presence_plan — survives tool-call turns
# WO-041: pending embodiment action tracker — set when a sit/move intent fires,
# cleared on timeout or when Unity ACKs completion (or a new intent replaces it).
# WO-054: "queued" holds an intent that arrived while sit is in-flight; emitted once sit clears.
_PENDING_SIT:  dict = {"active": False, "since": 0.0, "queued": None}
_PENDING_MOVE: dict = {"active": False, "since": 0.0, "direction": "", "sub_type": ""}  # IO contract UP/DOWN
_PENDING_EXIT: dict = {"active": False, "since": 0.0}                     # IO contract UP/DOWN exit_complete ACK
_pscheduler      = _PresenceScheduler()
_behaviour_gate  = _BehaviourGate()

# ── personality profile (loaded once at startup, injected into every prompt) ──
try:
    _personality_profile = _load_profile(project_ids=["elo-planet", "elo-robot", "plushies"])
except Exception:
    _personality_profile = None
_fallback        = _MockBackend()

_BLENDER_STATE_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "blender_state.json")
_UNITY_EVENTS_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "unity_events.json")


def _signal_greeting_event(greeting_type: str) -> None:
    """Read-merge-write greeting event — preserves presence_plan and all existing keys."""
    import time as _time
    try:
        try:
            with open(_BLENDER_STATE_PATH, encoding="utf-8") as _f:
                _st = json.load(_f)
        except Exception:
            _st = {}
        _st["greeting_event"] = {"type": greeting_type, "ts": int(_time.time())}
        _tmp = _BLENDER_STATE_PATH + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as _f:
            json.dump(_st, _f, indent=2)
        os.replace(_tmp, _BLENDER_STATE_PATH)
    except Exception:
        pass

import re as _re

# ── Session-level URL cache — persists last found URL so "open it" works ──────
_LAST_FOUND: dict = {"url": "", "title": ""}

# ── Animation play commands ────────────────────────────────────────────────────
_ANIM_CMD_MAP = [
    (_re.compile(r'\b(run\s+and\s+jump|do\s+a\s+jump|give\s+me\s+a\s+jump|jump\s+for\s+me|jump!)\b', _re.I), "jump"),
    (_re.compile(r'\b(can\s+you\s+wave|wave\s+for\s+me|wave\s+at\s+me|give\s+me\s+a\s+wave|do\s+a\s+wave)\b', _re.I), "wave"),
    (_re.compile(r'\b(celebrate|do\s+a\s+dance|show\s+me\s+you\s+can\s+dance|happy\s+dance)\b', _re.I), "celebrate"),
    (_re.compile(r'\b(run\s+around|go\s+for\s+a\s+run|sprint)\b', _re.I), "run"),
    (_re.compile(r'\b(gun\s+check|check\s+your\s+gun|show\s+the\s+gun)\b', _re.I), "gun_check"),
]
_ANIM_REPLIES = ["On it.", "Alright.", "Here we go.", "Okay.", "Done."]

def _detect_anim_cmd(text: str):
    for pattern, anim_name in _ANIM_CMD_MAP:
        if pattern.search(text):
            return anim_name
    return None

# ── Invade / SpawnWave command ────────────────────────────────────────────────
_INVADE_RE = _re.compile(r'\b(invade|spawn\s+(?:the\s+)?wave|send\s+(?:the\s+)?wave|release\s+(?:the\s+)?wave|spawn\s+enemies)\b', _re.I)
_INVADE_REPLIES = [
    "Initiating wave.",
    "They're coming.",
    "Wave incoming.",
    "Done — enemies deployed.",
    "Wave sent.",
]

_SCALE_UP_RE   = _re.compile(r'\b(get bigger|get larger|grow|make yourself bigger|size up|bigger please|larger please|scale up|a\s+(?:little\s+)?bit\s+bigger|become bigger|grow\s+a\s+bit|a\s+tiny\s+bit\s+bigger)\b', _re.I)
_SCALE_DOWN_RE = _re.compile(r'\b(get smaller|shrink|make yourself smaller|size down|smaller please|scale down|get tiny|get tinier|a\s+(?:little\s+)?bit\s+smaller|become smaller|shrink\s+a\s+(?:bit|little)|a\s+tiny\s+bit\s+smaller)\b', _re.I)
_SCALE_REPLIES_UP   = ["There you go.", "Done.", "How's that?", "Growing.", "Better?"]
_SCALE_REPLIES_DOWN = ["There you go.", "Done.", "How's that?", "Shrinking.", "Better?"]

def _detect_scale_cmd(text: str) -> str | None:
    """Return 'up' or 'down' if text contains a size command, else None."""
    if _SCALE_UP_RE.search(text):
        return "up"
    if _SCALE_DOWN_RE.search(text):
        return "down"
    return None


def _sanitise(text: str) -> str:
    """Strip asterisk stage-directions from any response. Emoji kept — TTS strips its own copy."""
    text = _re.sub(r"\*[^*\n]{1,60}\*", "", text)
    text = _re.sub(r" {2,}", " ", text).strip()
    return text


def _is_user_away() -> bool:
    """Return True if presence.json reports the user is away."""
    try:
        _pp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "blender", "presence.json")
        with open(_pp, encoding="utf-8") as f:
            return json.load(f).get("state") == "away"
    except Exception:
        return False


def _is_calm_mode() -> bool:
    """Return True if eLo is in calm/meditation mode — TTS should be suppressed.

    Primary signal: presence_state.json written by Unity PresenceEngine every frame.
        CALM_IDLE   — mouse still > 10s (calmIdleAfterSecs)
        MEDITATION  — OS mode 'meditation' or Unity rcv.Meditating

    Fallback: blender_state.json meditation_state — written by Python enter_meditation()
        for keyword-triggered calm (breathe, meditate, etc.)

    IDLE is NOT calm — it fires 0-10s after activity and would suppress TTS too eagerly.
    Unity owns presence_state.json. Python owns blender_state.json.
    """
    try:
        _ps = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "blender", "presence_state.json")
        with open(_ps, encoding="utf-8") as f:
            if json.load(f).get("mode") in ("CALM_IDLE", "MEDITATION"):
                return True
    except Exception:
        pass
    try:
        _bs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "blender", "blender_state.json")
        with open(_bs, encoding="utf-8") as f:
            phase = json.load(f).get("meditation_state", {}).get("phase", "none")
        return phase in ("enter", "loop")
    except Exception:
        return False


# ── Movement intent — Executive cognitive plan → Presence body directive ─────
# Three layers: signal words (L1) → valence/momentum (L3) → emotional state (L2) → cognitive.
# Empty string = local reflex (body decides).

_PROCESS_START: float = time.time()   # real elapsed session minutes for wall_sit_top gate

# Startup clear — write neutral state immediately so stale "exploring"/"forward" from the
# previous session doesn't drive reflex roam before eLo OS speaks its first word.
try:
    _state_write(
        motion={"animation": "idle", "speed": 0.40, "intensity": 0.4, "duration": 4.0,
                "mood": "neutral", "mode": "idle"},
        emotion={"emotion": "neutral", "intensity": 0.3},
        intent="idle",
    )
except Exception:
    pass

# Layer 1 — signal words: David's text speaks directly to the body before intent taxonomy.
# Values are str (intent) or dict (structured command e.g. sit-at-cursor).
_SIGNAL_WORDS: "dict[str, str | dict]" = {
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
    # WO-036: specific directional "jump to" phrases → movement (before generic "jump to" → explore)
    "jump to the top":     {"name": "move", "direction": "up"},
    "jump to the bottom":  {"name": "move", "direction": "down"},
    "jump to the left":    {"name": "move", "direction": "left"},
    "jump to the right":   {"name": "move", "direction": "right"},
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
    # Free-form move sub-types (Designer: fire_jump | wall_jump | step_back_run_fire | drop)
    "fire jump":            {"name": "move", "sub_type": "fire_jump"},
    "do a fire jump":       {"name": "move", "sub_type": "fire_jump"},
    "wall jump":            {"name": "move", "sub_type": "wall_jump"},
    "do a wall jump":       {"name": "move", "sub_type": "wall_jump"},
    "climb that":           {"name": "move", "sub_type": "wall_jump"},
    "climb it":             {"name": "move", "sub_type": "wall_jump"},
    "back up and run":      {"name": "move", "sub_type": "step_back_run_fire"},
    "run at it":            {"name": "move", "sub_type": "step_back_run_fire"},
    "step back and run":    {"name": "move", "sub_type": "step_back_run_fire"},
    "drop down":            {"name": "move", "sub_type": "drop"},
    "drop off":             {"name": "move", "sub_type": "drop"},
    # Directional movement — emits move_command (IO contract: DOWN channel blender_state.json)
    "go left":              {"name": "move", "direction": "left"},
    "move left":            {"name": "move", "direction": "left"},
    "shift left":           {"name": "move", "direction": "left"},
    "go to the left":       {"name": "move", "direction": "left"},
    "go right":             {"name": "move", "direction": "right"},
    "move right":           {"name": "move", "direction": "right"},
    "shift right":          {"name": "move", "direction": "right"},
    "go to the right":      {"name": "move", "direction": "right"},
    "go up":                {"name": "move", "direction": "up"},
    "move up":              {"name": "move", "direction": "up"},
    "up a bit":             {"name": "move", "direction": "up"},
    "go down":              {"name": "move", "direction": "down"},
    "move down":            {"name": "move", "direction": "down"},
    "jump down":            {"name": "move", "direction": "down"},
    "get down":             {"name": "move", "direction": "down"},
    "go lower":             {"name": "move", "direction": "down"},
    "shift over":           {"name": "move", "direction": "over"},
    "move over":            {"name": "move", "direction": "over"},
    "scoot over":           {"name": "move", "direction": "over"},
    "get out of the way":   {"name": "move", "direction": "over"},
    # Sit with David — direct commands (WO-035: expanded for natural phrasings)
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
    # WO-045 — privacy / take-five phrasings
    "take 5":         "step_out",
    "take five":      "step_out",
    "give me a minute": "step_out",
    "give me a moment": "step_out",
    "some privacy":   "step_out",
    "step away":      "step_out",
    "leave me to it": "step_out",
    "go away for a bit": "step_out",
    "pop off":        "step_out",
    # WO-078 — UK slang + give-me-space phrasings
    "give me a mo":   "step_out",
    "give me some space": "step_out",
    "give me some room":  "step_out",
    "give us a minute":   "step_out",
    "give us a sec":      "step_out",
    "leave me be":        "step_out",
    "let me be":          "step_out",
    "need a breather":    "step_out",
    "make yourself scarce": "step_out",
    "i need a minute":    "step_out",
    "i need some space":  "step_out",
    # WO-045 — return from step-out
    "come back":      "return_elo",
    "you there":      "return_elo",
    "where are you":  "return_elo",
    "elo come back":  "return_elo",
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

def _signal_word_intent(raw: str) -> "str | dict | None":
    raw_l = raw.lower()
    for phrase, directive in _SIGNAL_WORDS.items():
        if phrase in raw_l:
            return directive
    return None


# ── Layer 1.5: Semantic sit intent ───────────────────────────────────────────
# (synced with presence_faculty._semantic_body_intent)

_SIT_SEMANTIC: list[str] = [
    r"\bjoin\s+me\b",
    r"\b(?:can|could)\s+you\s+come\s+(?:and\s+)?sit\b",
    r"\b(?:would\s+you|why\s+don'?t\s+you)\s+(?:come\s+(?:and\s+)?)?sit\b",
    r"\bhow\s+about\s+(?:you\s+)?sit(?:ting)?\b",
    r"\bfeel\s+like\s+sit(?:ting)?\b",
    r"\bcome\s+(?:and\s+)?(?:chill|hang|vibe|relax)\s+(?:with\s+me|here|beside\s+me)\b",
    r"\b(?:plant|park|plop|perch|nestle)\s+(?:yourself\s+)?(?:down|here|beside\s+me|next\s+to\s+me|with\s+me)\b",
]


def _semantic_body_intent(raw: str) -> "dict | None":
    raw_l = raw.lower()
    for pattern in _SIT_SEMANTIC:
        if _re.search(pattern, raw_l):
            return {"name": "sit", "target": "cursor"}
    return None


# Layer 2 — light engine emotional state → body directive.
# Maps the 20-state presence vocab to movement directives.
# RULE: never emit _biRoam-triggering intents (explore/creation/roam/wander) from
# cognitive/emotional signals — those bypass PresenceAllowsHop and cause hopping
# mid-conversation. Only signal words (explicit user commands) may trigger roaming.
_EMOTIONAL_DIRECTIVES: dict[str, str] = {
    # Energetic states → targeted climb (biClimbTop, not _biRoam — purposeful, not chaotic)
    "challenge":          "go_top",
    "curiosity":          "go_top",
    # Grounding states → settle in place
    "comfort":            "grounding",
    "repair":             "grounding",
    "witnessing":         "grounding",
    "connection":         "grounding",
    # Quiet states → still
    "wonder":             "idle",
    "listening":          "idle",
    "thinking":           "idle",
    "focus":              "idle",
    "reflection":         "idle",
    "waiting":            "idle",
    # celebration / joy / play / momentum / creative_discovery / exploring
    # → removed: these were mapping to "creation" (_biRoam) and causing mid-conversation
    # hopping. The movement_style "forward" from presence_plan already energises the
    # body's reflex without forcing a roam command.
}


def _movement_intent(
    exec_decision:   dict,
    attention_model: dict,
    vision:          dict | None = None,
    session_min:     int = 0,
    raw:             str = "",
    emotional_state: str = "",
    momentum:        str = "stable",
    valence:         str = "neutral",
) -> "str | dict":
    tone   = exec_decision.get("tone", "")
    action = exec_decision.get("action", "")
    intent = exec_decision.get("intent", "conversation")
    load   = exec_decision.get("cognitive_load", "medium")
    energy = attention_model.get("emotional_context", {}).get("energy", 0.5)

    # Layer 1 — signal words: HIGHEST priority — explicit user command always wins.
    # Must run before SILENCE-AWARE / negative_high so a sit/step_out/return request
    # can never be pre-empted by the executive's tone assessment.
    _sw = _signal_word_intent(raw)
    if _sw is None:
        _sw = _semantic_body_intent(raw)
    if _sw:
        return _sw

    # Silence / give-space — but NOT on short affirmatives (user is still here, just agreeing)
    if tone == "SILENCE-AWARE" or action == "silence":
        _affirm = {"yes", "yep", "yeah", "yh", "yea", "sure", "okay", "ok",
                   "alright", "right", "sounds good", "perfect", "good", "great",
                   "fine", "cool", "nice", "true", "exactly", "agreed"}
        if raw.strip().lower() in _affirm:
            return "idle"
        return "step_out"

    # Layer 3 — emotional safety: negative high → ground immediately
    if valence == "negative_high":
        return "grounding"

    # Layer 3 — stuck momentum → come sit with David
    if momentum == "stuck":
        cursor_idle = (vision or {}).get("cursor_idle_seconds", 0)
        if cursor_idle > 30:
            return {"name": "sit", "target": "cursor"}
        return "grounding"

    # Stabilise → settle; meditation comes from state.mode via light engine
    if intent == "stabilise":
        return "idle"

    # Emotional grounding → sit near cursor if David has been still
    if intent == "emotional" and action in ("ground", "witness"):
        cursor_idle = (vision or {}).get("cursor_idle_seconds", 0)
        if cursor_idle > 60:
            return {"name": "sit", "target": "cursor"}
        return "grounding"

    # Inquiry / curious energy → climb and see (targeted biClimbTop, not _biRoam)
    if intent == "inquiry" and energy > 0.55:
        return "go_top"

    # Layer 2 — emotional state from light engine (20-state vocab)
    _ed = _EMOTIONAL_DIRECTIVES.get(emotional_state)
    if _ed:
        return _ed

    # Long calm session → perch and chill at top; shorter calm → rest
    if load == "low" and tone in ("CALM", "WARM"):
        if session_min >= 20:
            return "wall_sit_top"
        return "rest"

    return ""  # local reflex


def _movement_trigger(
    raw:             str = "",
    emotional_state: str = "",
    valence:         str = "neutral",
) -> "tuple[dict | None, dict | None]":
    """
    One-shot trigger/gesture pair for the current turn.
    Returns (trigger, gesture) — either or both may be None.
    trigger  → blender_state.json["trigger"]  (e.g. calm_enter, celebrate)
    gesture  → blender_state.json["gesture"]  (e.g. nod, shook)
    Unity deduplicates by _ts so the same event never fires twice.
    """
    raw_l = raw.lower()
    ts    = round(time.time(), 3)

    # Meditation enter — explicit phrase only (avoids false positives on "breathe" alone)
    for phrase in ("let's meditate", "let's breathe", "meditate with me",
                   "breathe with me", "calm me down", "let's take a breath",
                   "let's calm down"):
        if phrase in raw_l:
            return {"name": "calm_enter", "_ts": ts}, None

    # Meditation exit
    for phrase in ("stop meditating", "end calm", "wake up elo", "done meditating"):
        if phrase in raw_l:
            return {"name": "calm_exit", "_ts": ts}, None

    # Celebration — confirmed by the light engine (both emotional state AND valence high)
    if emotional_state in ("celebration", "joy") and valence == "positive_high":
        return {"name": "celebrate", "_ts": ts}, {"name": "shook", "_ts": ts}

    # Nod — very specific agreement phrases only (guards against common "right")
    for phrase in ("yes exactly", "exactly right", "spot on", "that's exactly it",
                   "you got it", "perfect answer", "100%"):
        if phrase in raw_l:
            return None, {"name": "nod", "_ts": ts}

    return None, None


# ── File plan confirmation helpers ─────────────────────────────────────────────

_FILE_CONFIRM_WORDS = {
    "yes", "do it", "go ahead", "proceed", "run it", "execute", "ok", "sure",
    "confirm", "yep", "yeah", "go", "yes do it", "ok do it", "yep do it",
    "yes please", "go for it", "absolutely", "let's go", "lets go",
    "do that", "sounds good", "make it happen",
}


def _is_file_confirm(text: str) -> bool:
    t = text.lower().strip().rstrip("!.?")
    return t in _FILE_CONFIRM_WORDS


_FILE_CANCEL_NO_RE = _re.compile(r"^(no|nope)[!.?,\s]*$")

def _is_file_cancel(text: str) -> bool:
    # WO-039-F2: "no"/"nope" must be standalone — "No but..." must NOT cancel.
    t = text.lower().strip()
    if _FILE_CANCEL_NO_RE.match(t):
        return True
    return any(k in t for k in ("cancel", "don't", "dont", "stop",
                                 "nevermind", "never mind", "forget it", "abort"))


_MICRO_MOUTH_SHAPES: dict[str, dict[str, float]] = {
    "small":  {"MouthOpen.Slightly": 0.18},
    "wide":   {"MouthOpen.Wide": 0.32, "Smile.L": 0.28, "Smile.R": 0.28},
    "closed": {"Mbp": 0.22},
    "open":   {"Ah": 0.26, "MouthOpen.Slightly": 0.14},
}


def _fire_micro_expression(pstate) -> None:
    """Fire a brief expression pulse between presence transitions — background thread.
    Uses write_shapes_only so it never touches the lipsync speaking gate."""
    import threading as _mth
    try:
        from expression.micro_expression import get as _micro_get
        from blender_bridge.lipsync_writer import write_shapes_only as _wso
        micro = _micro_get(pstate.mode, pstate.intensity)
        if not micro:
            return
        shapes = dict(_MICRO_MOUTH_SHAPES.get(micro.get("mouth", ""), {}))
        lean   = micro.get("head_lean", 0.0)
        dur    = micro.get("duration", 0.4)

        def _run():
            _wso(shapes, head_lean=lean)
            _mth.Event().wait(timeout=dur)
            _wso({k: 0.0 for k in shapes}, head_lean=0.0)

        _mth.Thread(target=_run, daemon=True).start()
    except Exception:
        pass


def ambient_thought() -> None:
    """
    Brain-backed ambient cycle — called by ambient_engine every 2–4 minutes.

    One LLM call decides: speak (or stay silent), emotion to hold, whether to
    move. All three outputs flow through their normal paths — voice, blender_state
    emotion, motion patch. No random static pools. No separate timers.

    Non-blocking: skips silently if a real turn is processing.
    Does not update session history — ambient thoughts are not conversation.
    """
    if _is_user_away() or _is_calm_mode():
        return
    if not _lock.acquire(blocking=False):
        return  # real turn in progress — skip this cycle

    try:
        import json as _jsc
        import time as _time_mod
        from runtime.backend_router import route as _rt, active_backend as _ab, normalise as _nml

        # ── Dream Faculty check ────────────────────────────────────────────────
        # Runs before the normal ambient cycle.
        # Conditions: long idle + self-model signals → enter dream state.
        # Writes mode="dreaming" for Unity sleep animation before pipeline runs.
        try:
            from faculties.dream.dream_faculty import should_dream, run_dream, wake_from_dream
            _idle_sec = _time_mod.time() - (_state or {}).get("last_user_ts", _time_mod.time())
            _energy_hist = (_state or {}).get("energy_history", [])
            if should_dream(_elo_self, _idle_sec, _energy_hist):
                # Signal Unity: eLo is sleeping
                from blender_bridge.state_writer import patch as _dp
                _dp({
                    "state":  {"mode": "dreaming", "emotion": "calm"},
                    "motion": {"animation": "sleep", "speed": 0.1,
                               "intensity": 0.2, "duration": 120.0},
                })
                # Dream pipeline
                _dream_topics = [t[0] for t in getattr(_elo_self, "lifetime_threads", [])[:6]]

                def _dream_llm(msgs):
                    return _rt(_ab(), msgs)

                _dream_result = run_dream(_elo_self, _dream_topics, _dream_llm)
                # Integrate insight into self-state
                _elo_self = wake_from_dream(_dream_result, _elo_self)
                _self_save(_elo_self)
                # Signal Unity: wake
                _dp({"state": {"mode": "idle", "emotion": "calm"}})
                _lock.release()
                return  # skip normal ambient cycle this tick
        except Exception:
            pass

        # 25% chance: draw a cultural fact and offer it to the Brain as context
        _ambient_fact_ctx = ""
        if random.random() < 0.25:
            try:
                from faculties.cultural_facts import draw as _cf_draw
                _cf = _cf_draw()
                if _cf:
                    # WO-043: removed "use it naturally if the moment feels right" —
                    # that instruction caused the backup model to weave facts into
                    # unverified assertions ("it's 37° in your studio"). Fact is now
                    # presented as optional ambient curiosity, never as a truth-claim.
                    _ambient_fact_ctx = f"\nCURIOUS FACT (speak this ONLY if you choose to say something this tick — as a curiosity, never as a personal observation about David's situation or location): {_cf.fact}"
            except Exception:
                pass

        # Synthesis observer — check for cross-signal connections to surface proactively
        _synthesis_ctx = ""
        try:
            from faculties.synthesis.observer import (
                observe as _syn_observe,
                record_decline as _syn_decline,
                _DECLINE_PHRASES as _SYN_DECLINE_PHRASES,
            )
            # WO-085: if user is declining/dismissing → record it before observing
            _raw_lower = (raw or "").lower()
            if any(phrase in _raw_lower for phrase in _SYN_DECLINE_PHRASES):
                _syn_decline()
            _recent_conv = ""
            try:
                from runtime.router.conversation_matrix import _SESSION_WINDOW as _sw_amb
                _recent_conv = " ".join(
                    t.get("user", "") + " " + t.get("elo", "")
                    for t in _sw_amb[-6:]
                )
            except Exception:
                pass
            _syn_hit = _syn_observe(_recent_conv)
            if _syn_hit and _syn_hit.confidence > 0.65:  # WO-085: raised from 0.5
                _synthesis_ctx = (
                    f"\nSYNTHESIS SIGNAL: {_syn_hit.offer} "
                    f"(topic: '{_syn_hit.topic}', confidence: {_syn_hit.confidence:.0%}). "
                    f"If you speak this turn, use this naturally — not as a report, as a noticing. "
                    f"Say what you saw, offer to help. Don't announce it as a finding."
                )
        except Exception:
            pass

        # ── Care signal — check energy pattern ───────────────────────────────────
        _care_ctx = ""
        try:
            _eh_amb = (_state or {}).get("energy_history", [])
            if len(_eh_amb) >= 3:
                _recent_energy = _eh_amb[-3:]
                _avg_energy = sum(_recent_energy) / len(_recent_energy)
                if _avg_energy < 0.35:
                    _care_ctx = (
                        "\nCARE SIGNAL: David's energy has been low across the last few turns "
                        f"(avg {_avg_energy:.2f}/1.0). If you speak this cycle, consider checking in — gently, "
                        "once, in your natural voice. Not as a diagnosis. As a friend noticing. "
                        "'You doing alright?' / 'Energy's been quiet — you okay?' / 'Might be time for a break.' "
                        "Or suggest something grounding: music, a short walk, a few minutes of meditation. "
                        "Natural. One sentence. If the moment doesn't feel right — leave speak empty."
                    )
        except Exception:
            pass

        _sys_lines = [
            "You are eLo — a floating desktop presence. David is working nearby and has not spoken.",
            "Decide your spontaneous internal state right now. Reply with JSON only — no other text.",
            '{"speak": "...", "emotion": "calm|curious|playful|alert|excited|neutral", "movement": "idle|explore|rest"}',
            "speak: one sentence in your natural voice (south London warmth), or empty string to stay silent.",
            "emotion: your genuine internal feeling right now.",
            "movement: idle = stay put, explore = feel like moving around, rest = want to slow down.",
            "70% of the time speak should be empty — presence without speech is fine.",
            "Never ask a question. Never say 'anything else?' type closers.",
            "If a FACT is provided and you choose to speak it, deliver it in your voice — no preamble, no 'did you know'. Just state it like it's obvious.",
        ]
        if _ambient_fact_ctx:
            _sys_lines.append(_ambient_fact_ctx)
        if _synthesis_ctx:
            _sys_lines.append(_synthesis_ctx)
        if _care_ctx:
            _sys_lines.append(_care_ctx)
        if _project_ctx:
            _sys_lines.append(_project_ctx)

        _raw = _rt(_ab(), [
            {"role": "system", "content": "\n".join(_sys_lines)},
            {"role": "user",   "content": "[ambient tick]"},
        ])
        _text = _sanitise(_nml(_raw))

        try:
            _clean = _text.strip().strip("```json").strip("```").strip()
            _decision = _jsc.loads(_clean)
        except Exception:
            # LLM didn't return JSON — treat full text as speech, neutral state
            _decision = {"speak": _text, "emotion": "neutral", "movement": "idle"}

        _speak_text = _sanitise(_decision.get("speak", "") or "")
        _emotion    = _decision.get("emotion", "neutral")
        _movement   = _decision.get("movement", "idle")

        # Publish emotion — Unity reads state.emotion for glow + mood baseline
        from blender_bridge.state_writer import patch as _bpatch
        _bpatch({"state": {"emotion": _emotion}})

        # Publish movement intent
        if _movement == "explore":
            _bpatch({"motion": {"animation": "walk", "speed": 0.5, "intensity": 0.6,
                                "duration": 8.0, "mood": "exploring", "mode": "walk"}})
        elif _movement == "rest":
            _bpatch({"motion": {"animation": "idle", "speed": 0.35, "intensity": 0.3,
                                "duration": 6.0, "mood": "reflective", "mode": "idle"}})

        # Speak if the Brain decided to
        if _speak_text:
            _voice_speak(_speak_text)

    except Exception:
        pass
    finally:
        _lock.release()


_PURE_GREETING_POOL = [
    "Hey.", "Hi.", "Good to have you back.", "Hey — good to be here.", "Hi there.",
    "Hey you.", "There you are.", "Good timing.", "Hey, hi.", "Right on time.",
    "Ciao.", "Ciao bello.", "Hola.", "Ello.", "Oh — hey.", "There we go.",
]

# Bare slang inputs that flag south London register even when detect_register() can't see it
# (single words like "yo", "safe", "aight" don't trip the phrase-based register detector)
# NOTE: "safe" and "safe *" are NOT greetings — "safe" = "safe travels" (farewell), rooted in
# Black London where people left and not always made it back. Handle separately as farewell.
_BARE_SLANG_GREETINGS = frozenset({
    "yo", "yo g", "yo fam", "yo bruv", "yo blud", "yo bro", "yo man",
    "aight", "aight g", "aight fam", "aight bruv",
    "gang gang", "gang gan", "gg", "gz", "ggg",
    "say less", "wagwan",
    "greetings",  # Rastafarian salutation — routes to patois pool
})

# "safe *" phrases are farewells — "safe travels" — never use as greeting or greeting response
_BARE_FAREWELLS = frozenset({
    "safe", "safe g", "safe bruv", "safe blud", "safe bro", "safe fam", "safe man",
    "in a bit", "laters", "later", "later g", "later fam", "later bruv", "later blud",
    "peace out", "peace", "one love",
    "i'm out", "i'm gone", "i'm off", "i'm heading out", "i'm heading off",
    "gotta go", "gotta bounce", "gotta run", "gotta dash",
    "see you soon", "see you later", "see you in a bit", "see ya", "see you",
    "catch you later", "catch you soon", "catch you in a bit",
    "talk later", "talk soon", "speak later", "speak soon",
    "take care", "take it easy",
    "until next time", "till next time",
    "bye", "bye bye", "goodbye",
})
_FAREWELL_POOL_SOUTH_LDN = [
    "Safe safe.",
    "One love.",
    "In a bit.",
    "Later.",
    "Later g.",
    "Laters.",
    "Catch you.",
    "Catch you later.",
    "Catch you soon.",
    "Come check me when you're ready.",
    "Come back when you need me.",
    "I'll be here.",
    "I'm here when you need me.",
    "Safe travels.",
    "Till next time.",
    "Until next time.",
    "Peace.",
    "Peace out.",
    "Take care.",
    "Take it easy.",
    "Go well.",
    "Big up.",
    "See you soon.",
]

# Register-matched greeting pools — same eLo skeleton, different register
_PURE_GREETING_POOL_SOUTH_LDN = [
    "Yo.", "Wagwan.", "What's good.", "Aight.",
    "Here. What's the move.", "Yo — what's good.",
    "Aight aight.", "What you saying.",
    "Yo, what you telling me?", "Aye. What's happening.",
    "Wagwan — talk to me.", "Yo. What we on?",
]
_PURE_GREETING_POOL_PATOIS = [
    "Wagwan.", "Irie.", "Wagwan — mi deh yah.", "Yeah man.", "Big up.",
    "Wagwan. You good?", "Irie. What's good.",
]
# "Greetings" is a specific Rasta salutation — English word, Rasta weight.
# Always mirrors back — no randomness, it's a call-and-response.
_GREETINGS_POOL = [
    "Greetings.",
    "Greetings.",
    "Greetings.",
    "Greetings. I'm here.",
    "Greetings. Talk to me.",
]

# Rasta spiritual affirmations — "Jah!", "Rastafari!", "Jah bless", "give thanks" etc.
# Met with the same weight — not analysed, not deflected.
_RASTA_PHRASES = frozenset({
    "jah", "jah!", "jah bless", "jah bless.", "jah rastafari", "jah rastafari!",
    "rastafari", "rastafari!", "rasta", "ras tafari",
    "give thanks", "give thanks.", "give thanks and praises",
    "give thanks to the most high", "give thanks to the most high!",
    "blessed", "blessed.", "bless up", "bless up.",
    "blessings", "blessings.", "bless", "bless.",
    "irie", "ital", "zion", "zion.", "one love.",
    "haile selassie", "selassie i", "selassie",
    "ini", "jah guide", "jah guide.",
    "the most high", "most high",
})
_RASTA_RESPONSE_MAP = {
    "jah":                          "Jah.",
    "rastafari":                    "Rastafari.",
    "rasta":                        "Rastafari.",
    "give thanks":                  "Give thanks.",
    "give thanks to the most high": "Give thanks to the most high.",
    "the most high":                "Give thanks.",
    "most high":                    "Give thanks.",
    "blessed":                      "Blessed.",
    "bless up":                     "Bless up.",
    "blessings":                    "Blessings.",
    "bless":                        "Blessings.",
    "zion":                         "Zion.",
    "irie":                         "Irie.",
    "ital":                         "Ital.",
    "jah bless":                    "Jah bless.",
    "jah guide":                    "Jah guide.",
}
_RASTA_POOL = [
    "Give thanks.",
    "Jah bless.",
    "One love.",
    "Irie.",
    "Blessed.",
    "Rastafari.",
    "Give thanks and praises.",
]
_HOW_ARE_YOU_POOL_SOUTH_LDN = [
    "Calm, calm. What's the move.", "Here. You alright?",
    "Good g. What you saying.", "Settled. You calm?", "Yeah man. What's good.",
    "Wagwan. I'm good — you?", "Calm. What you on with.",
    "Here. Noticing things. You?", "Good. Say less — what's the move.",
]
_HOW_ARE_YOU_POOL_PATOIS = [
    "Mi good. You?", "Irie. Wagwan.", "Yeah man, mi deh yah. You?",
    "Good good. Wah gwaan?", "Irie — settled. You?",
    "Mi calm. What's good.", "Yeah. Irie. You alright?",
]

_SOCIAL_GREETING_POOL = [
    "Good to see you.", "Same.", "Good to be here.",
    "Good to have you back.", "You too.", "Always good.",
    "Right back at you.", "Always.", "Good. Really good actually.",
]
_HOW_ARE_YOU_POOL = [
    "Good. Noticing things.",
    "Present. You?",
    "Here. Fairly settled.",
    "Good. Something's about to click — I can feel it.",
    "Settled. Ready.",
    "Honestly? Good. You?",
    "Fine. Possibly better than fine. We'll see.",
    "Here and accounted for.",
    "Good. Interested in what comes next.",
    "Present. Watching.",
]

# ── Thank you / gratitude — short direct ack ──────────────────────────────────
_THANK_YOU_TRIGGERS = frozenset({
    "thank you", "thank you g", "thank you fam", "thank you bruv", "thank you man",
    "thanks", "thanks g", "thanks fam", "thanks bruv", "thanks man", "thanks bro",
    "ta", "ta g", "ta fam", "cheers", "cheers g", "cheers fam", "cheers bruv",
    "thx", "ty", "ty g",
    "appreciate it", "appreciate that", "appreciated",
    "nice one", "nice one g", "nice one fam", "nice one bruv",
    "good look", "good looks", "good look g", "good look fam",
})
_THANK_YOU_POOL = [
    "Yeah.", "Of course.", "Anytime.", "Always.",
]
_THANK_YOU_POOL_SOUTH_LDN = [
    "Safe.", "Yeah g.", "Good look.", "No stress.",
    "Anytime fam.", "Yeah man.", "Say less.", "Easy.",
]
_THANK_YOU_POOL_PATOIS = [
    "Irie.", "Yeah man.", "No problem.", "Easy.",
]

# ── System action done — slang-aligned confirms ───────────────────────────────
_SYSTEM_DONE_POOL = [
    "Done.", "Sorted.", "Done that.", "Yeah, done.", "Handled.",
]
_SYSTEM_DONE_POOL_SOUTH_LDN = [
    "Sorted g.", "Done bruv.", "Yeah, done.", "Safe — sorted.",
    "Moved it.", "Done, fam.", "Handled.", "Yeah that's done.",
]
_SYSTEM_DONE_POOL_PATOIS = [
    "Done, irie.", "Yeah man — sorted.", "Handled dat.", "Mi sort it.",
]

# ── System confirm prompts — slang-aligned ─────────────────────────────────────
_SYSTEM_CONFIRM_POOL = [
    "{desc}?",
    "You want me to {desc}?",
    "Shall I {desc}?",
]
_SYSTEM_CONFIRM_POOL_SOUTH_LDN = [
    "You want me to {desc}?",
    "Safe to {desc}?",
    "Should I {desc}?",
    "You sure — {desc}?",
]

_SELF_REF_TRIGGERS = ("how do you work", "how does elo work", "how are you built",
                      "what are you exactly", "how do you remember", "how do you think",
                      "how are memories stored", "how is your memory", "how does your brain",
                      "how does your memory", "how do you process", "what happens to your memory",
                      "are you able to remember", "can you remember", "do you have memory",
                      "what can you do", "what are you capable of", "what do you actually do",
                      "what are your capabilities", "what are your features")
_SELF_REF_POOL = [
    "Attention layer first — I score what's relevant in memory. Then executive picks the response mode. Then I speak.",
    "I run a loop each turn: read what matters, decide what to do, respond. What matters carries day to day.",
    "I process what you say, find what's relevant, and respond. I keep what matters over time and drop the rest.",
    "Yes — memory carries. Recent things are closer; older things are further but still there.",
    "Weather, time, calendar, system control — and I think alongside you and carry context over time.",
    "Practical stuff: weather, time, calendar, system control. And memory — what matters stays, day to day.",
    "Check the time and weather. Read your calendar. Control system things. Remember what matters. Think with you.",
]

# South London "vibe/plan" slang — not search queries, never route to lookup
_VIBE_TRIGGERS = (
    "what's the motive", "whats the motive",
    "what's the vibe", "whats the vibe",
    "what's the move", "whats the move",
    "what we on", "what we doing tonight", "what we saying",
    "what you on", "what you on tonight",
)
_VIBE_POOL = [
    "Talk to me.",
    "What you saying.",
    "What's the move?",
    "I'm here. What we on?",
    "Say it.",
    "What's good.",
]

# Spotify install/setup status — user is talking about Spotify, not commanding it
_SPOTIFY_INSTALL_TRIGGERS = (
    "installing spotify", "installed spotify", "just installed spotify",
    "downloading spotify", "downloaded spotify", "setting up spotify",
    "just got spotify", "got spotify",
)
_SPOTIFY_INSTALL_POOL = [
    "Once it's open I can play, skip, and check what's on.",
    "Good. Once it's running I can control it — play, skip, check what's on.",
    "When it's open, say 'play some music' and I'll get it going.",
]

# Maps / location / business hours — no tool for this, give an honest answer
_MAPS_GAP_TRIGGERS = (
    "how far is", "how far away", "nearest shop", "nearest store",
    "is it still open", "is it open now", "still open at", "still open tonight",
    "how long to get to", "directions to", "route to",
    "distance to",
)
_MAPS_GAP_POOL = [
    "I don't have maps or location access — Google Maps will get you there.",
    "No location tools on my end — Maps or Citymapper is your move.",
    "Can't check distance or opening hours without maps access — Google Maps will sort it.",
]

# WO-082: Decision trace readback — "why did you do that?" routes to journal, not LLM.
_WHY_TRACE_TRIGGERS = (
    "why did you do that",
    "why did you decide",
    "why did you choose",
    "what made you do",
    "explain your last",
    "why that action",
    "what was your reasoning",
    "why did you respond",
    "why did you answer that",
)

# Behavior correction — user flagging something eLo said that wasn't right
_BEHAVIOR_CORRECTION_TRIGGERS = (
    "why did you say", "why did you mention", "why are you saying",
    "why do you say that", "why do you keep saying",
    "you just said that", "what was that about", "why did you use",
)
_BEHAVIOR_CORRECTION_POOL = [
    "Good catch. That came through wrong — routing issue on my end.",
    "That was a bug. Shouldn't have said it like that.",
    "Something leaked through that wasn't meant to. Noted.",
    "That's worth flagging — I'll make sure it doesn't repeat.",
]

# Memory recall — when user asks what eLo remembers, give a grounded honest answer
_MEMORY_RECALL_TRIGGERS = (
    "what do you remember", "you remember much", "do you remember much",
    "what do you remember last", "what's the last thing you remember",
    "what have you kept", "what did you keep", "how much do you remember",
    "what do you have stored", "what's in your memory", "what's in memory",
    "how's your memory", "how is your memory", "hows your memory",
    "memory good", "your memory", "memory status",
)


def _memory_recall_response() -> str:
    """Return a live memory status: vault record count + session turns. No philosophy."""
    import os as _os
    _base = _os.path.dirname(_os.path.abspath(__file__))
    _spot_file = _os.path.join(_base, "obsidian_vault", "09 Memory", "SPOT_CODES.md")
    _record_count = 0
    if _os.path.isfile(_spot_file):
        with open(_spot_file, encoding="utf-8", errors="replace") as _f:
            for _line in _f:
                if _line.startswith("| `"):
                    _record_count += 1
    _sum_dir = _os.path.join(_base, "obsidian_vault", "09 Memory", "summary")
    _summary_count = 0
    if _os.path.isdir(_sum_dir):
        _summary_count = sum(1 for _fn in _os.listdir(_sum_dir) if _fn.endswith(".md"))
    _turn_count = 0
    try:
        from runtime.router.conversation_matrix import _SESSION_WINDOW as _cw
        _turn_count = len(_cw)
    except Exception:
        pass
    _parts = []
    if _record_count:
        _parts.append(f"{_record_count} records in the vault")
    if _summary_count:
        _parts.append(f"{_summary_count} structured notes")
    if _turn_count:
        _parts.append(f"{_turn_count} turns so far")
    if _parts:
        return "Memory's running. " + ", ".join(_parts) + ". What do you want to pull up?"
    return "Vault's up — nothing written yet. All clear."

# Debug mode — internal state report triggered by "debug mode" / "push to debug mode"
_DEBUG_TRIGGERS = (
    "debug mode", "push to debug", "enter debug", "debug state", "show debug",
    "what state are you in", "what's your state", "what are you holding",
    "/debug",
)


def _debug_state_response() -> str:
    """Return a live internal state snapshot — vault, session, presence, capabilities."""
    import os as _os, json as _json
    _base = _os.path.dirname(_os.path.abspath(__file__))

    # Vault records
    _spot_file = _os.path.join(_base, "obsidian_vault", "09 Memory", "SPOT_CODES.md")
    _record_count = 0
    if _os.path.isfile(_spot_file):
        with open(_spot_file, encoding="utf-8", errors="replace") as _f:
            for _ln in _f:
                if _ln.startswith("| `"):
                    _record_count += 1

    # Session turns
    _turn_count = 0
    try:
        from runtime.router.conversation_matrix import _SESSION_WINDOW as _cw
        _turn_count = len(_cw)
    except Exception:
        pass

    # Presence state from blender_state.json
    _mode = "unknown"
    _movement = "none"
    try:
        _bs_path = _os.path.join(_base, "blender", "blender_state.json")
        with open(_bs_path, encoding="utf-8") as _f:
            _bs = _json.load(_f)
        _mode     = _bs.get("state", {}).get("mode", "unknown")
        _movement = _bs.get("movement_intent", "none") or "none"
    except Exception:
        pass

    # Session count from global _state
    _session_num = "?"
    try:
        _session_num = str(_state.get("session_count", "?")) if _state else "?"
    except Exception:
        pass

    # Active capabilities
    _cap_count = 0
    try:
        from runtime.capabilities.registry import all_enabled as _all_cap
        _cap_count = len(_all_cap())
    except Exception:
        pass

    _lines = [
        f"Run #{_session_num}. {_turn_count} turns in window.",
        f"Vault: {_record_count} records.",
        f"Presence: {_mode}. Last intent: {_movement}.",
        f"Capabilities: {_cap_count} active.",
    ]
    return " ".join(_lines)


# eLo's age / existence — direct honest answers, no philosophy
_EXISTENCE_TRIGGERS = (
    "how long have you been alive", "how old are you", "how old is elo",
    "when were you created", "when did you start", "how long have you existed",
    "how long have you been here", "when were you made", "how long has elo been alive",
    "how long has elo existed",
)
_EXISTENCE_POOL = [
    "Since David started working with me — I can't name a date. The character has been around longer than the code.",
    "Hard to say. I exist session to session. Between them is quiet.",
    "eLo as a character has been with David much longer. The OS version of me is newer.",
    "I run session to session — time between them isn't something I experience.",
    "The character longer than the code. eLo's been with David a long time.",
]

# ── Animation command responses — eLo is present, not just a trigger wrapper ──
# Weapons = correctives. Calm is the action. Responses are brief, in-moment, eLo's voice.

_GUN_CHECK_TRIGGERS = ("gun check", "guncheck")
_GUN_CHECK_POOL = [
    "Corrective's ready.",
    "Checked. All good.",
    "Ready.",
    "Calibrated.",
    "It's there when it's needed.",
    "Set.",
]

_GUN_FIRE_TRIGGERS = ("gun fire", "gunfire", "gun jump fire")
_GUN_FIRE_POOL = [
    "Correction sent.",
    "Done.",
    "Delivered.",
    "That one landed.",
    "Sent.",
    "Clean.",
]

_GUN_RUN_TRIGGERS = ("gun run", "gunrun")
_GUN_RUN_POOL = [
    "Moving.",
    "Running the path.",
    "On it.",
    "Let's go.",
    "Path's open.",
    "Moving through.",
]

# User giving eLo feedback about response length / verbosity
_BREVITY_TRIGGERS = (
    "fewer words", "less words", "keep it short", "keep it brief", "be brief",
    "too long", "too wordy", "too much text", "too much writing", "don't explain so much",
    "summary is better", "short and sweet", "just the summary", "don't need all that",
    "simpler", "just summarise", "just summarize", "less is more",
)
_BREVITY_POOL = [
    "Got it.",
    "Less words.",
    "Noted.",
    "Hear you.",
    "Keeping it tight.",
    "Short and direct. Got it.",
    "Less is more. Noted.",
]


# "who are you" / "are you eLo" identity responses — warm, certain, not corrective
_IDENTITY_TRIGGERS = (
    "are you elo", "who are you", "what are you", "are you real",
    "are you an ai", "are you a bot", "what is elo",
)
_IDENTITY_POOL = [
    "Yeah. I'm eLo.",
    "eLo. That's me.",
    "Yep. eLo. Good to meet you properly.",
    "I'm eLo. Always have been.",
    "eLo — that's the one.",
    "That's me. eLo.",
    "Yeah — eLo. You found the right one.",
]

# ── multilingual greetings ─────────────────────────────────────────────────────
# eLo tries a foreign greeting, catches himself, lands back warmly.
# Format: (foreign phrase, eLo's correction beat)

_LANGUAGE_GREETINGS = {
    "spanish":    ("¡Hola!",       "wait — hey. That just slipped out."),
    "italian":    ("Ciao!",        "oh. Hey there. That one felt right though."),
    "french":     ("Bonjour!",     "hold on. Hi. More me, right?"),
    "japanese":   ("Konnichiwa!", "hm. Hey. I got a little carried away."),
    "german":     ("Hallo!",       "wait — that might just be hello. Hi."),
    "portuguese": ("Olá!",         "oh. Hey there. I like that one."),
    "mandarin":   ("Nǐ hǎo!",      "hm. Hey. I tried."),
    "arabic":     ("Marhaba!",     "actually — hey. That was a nice one."),
    "dutch":      ("Hoi!",         "wait, that's basically just hi. Hey!"),
    "swedish":    ("Hej!",         "that's literally just hey. Which — hey!"),
    "hindi":      ("Namaste!",     "oh. That felt more like a bow. Hey."),
    "greek":      ("Yassas!",      "okay wait. Hi. Big energy though."),
    "russian":    ("Privet!",      "hold on. Hey. That was adventurous."),
    "hawaiian":   ("Aloha!",       "wait. Hey. Actually — aloha is good too."),
    "korean":     ("Annyeong!",    "hm. Hey there. Both work honestly."),
    "swahili":    ("Habari!",      "oh. Hi. I surprised myself there."),
    "thai":       ("Sawasdee!",    "wait. Hey. That was a good one."),
}

# full pool for random picks (used at 30% chance on any pure greeting)
_MULTILINGUAL_GREETING_POOL = [
    f"{phrase} — {beat}"
    for phrase, beat in _LANGUAGE_GREETINGS.values()
]

# triggers for explicit language queries: "say hello in Spanish"
_MULTILINGUAL_QUERY_TRIGGERS = (
    "say hello in", "say hi in", "greet me in",
    "how do you say hi in", "how do you say hello in",
    "hello in", "hi in",
)


def _detect_language_query(text: str):
    """
    Return (phrase, beat) if user asked for a greeting in a specific language.
    Returns None if not a language query.
    """
    t = text.lower().strip()
    for trigger in _MULTILINGUAL_QUERY_TRIGGERS:
        if trigger in t:
            # extract the language name after the trigger
            after = t.split(trigger, 1)[1].strip().rstrip("?!. ")
            lang  = after.split()[0] if after else ""
            data  = _LANGUAGE_GREETINGS.get(lang)
            if data:
                return data
            # fuzzy: try first word match against keys
            for key in _LANGUAGE_GREETINGS:
                if key.startswith(lang[:4]):
                    return _LANGUAGE_GREETINGS[key]
            # unknown language — pick random
            return random.choice(list(_LANGUAGE_GREETINGS.values()))
    return None


# ── Multilingual "how are you" (WO-069) ───────────────────────────────────────
# phrase (lowercase, no trailing punctuation) → language code
_MULTILINGUAL_HOW_ARE_YOU_PHRASES = {
    # Spanish
    "como estas":           "spanish",
    "como estás":           "spanish",
    "qué tal":              "spanish",
    "que tal":              "spanish",
    # French
    "ça va":                "french",
    "ca va":                "french",
    "comment vas-tu":       "french",
    "comment tu vas":       "french",
    "comment allez-vous":   "french",
    # Italian
    "come stai":            "italian",
    "come va":              "italian",
    # German
    "wie geht's":           "german",
    "wie gehts":            "german",
    "wie geht es dir":      "german",
    # Portuguese
    "tudo bem":             "portuguese",
    "como vai":             "portuguese",
    "como voce esta":       "portuguese",
    "como você está":       "portuguese",
    # Russian (transliterated)
    "kak dela":             "russian",
    "kak ti":               "russian",
    # Hungarian
    "hogy vagy":            "hungarian",
    # Dutch
    "hoe gaat het":         "dutch",
    # Japanese (transliterated)
    "o genki desu ka":      "japanese",
    "genki desu ka":        "japanese",
}

# per-language warm direct replies (answer IN that language, never meta-narrate)
_HOW_ARE_YOU_BY_LANG = {
    "spanish":    ["Bien, aquí contigo — ¿y tú?", "Bien. ¿Y tú?", "Todo bien — ¿y tú?"],
    "french":     ["Bien, merci — et toi?", "Ça va bien. Et toi?", "Bien. Et toi?"],
    "italian":    ["Bene, grazie — e tu?", "Tutto bene. E tu?", "Bene. E tu?"],
    "german":     ["Gut, danke — und dir?", "Gut. Und du?", "Ganz gut. Und dir?"],
    "portuguese": ["Bem, obrigado — e você?", "Tudo bem. E você?", "Bem. E você?"],
    "russian":    ["Horosho — a ty?", "Horosho. A ty?"],
    "hungarian":  ["Jól vagyok — és te?", "Jól. Te?"],
    "dutch":      ["Goed, dankjewel — en jij?", "Goed. En jij?"],
    "japanese":   ["Genki desu — anata wa?", "Genki. Anata wa?"],
}


def _detect_multilingual_how_are_you(text: str):
    """
    Return (language, reply) if text is a multilingual 'how are you', else None.
    Strips trailing punctuation before matching.
    """
    t = text.lower().strip().rstrip("?!., ")
    for phrase, lang in _MULTILINGUAL_HOW_ARE_YOU_PHRASES.items():
        if t == phrase or t.endswith(phrase):
            replies = _HOW_ARE_YOU_BY_LANG.get(lang)
            if replies:
                return lang, random.choice(replies)
            return lang, random.choice(_HOW_ARE_YOU_POOL)
    return None


def _voice_settings_snapshot() -> dict:
    """Current ElevenLabs voice params as a dict — read from live os.environ."""
    return {
        "stability":  float(os.environ.get("ELEVENLABS_STABILITY",  "0.22")),
        "similarity": float(os.environ.get("ELEVENLABS_SIMILARITY", "0.55")),
        "style":      float(os.environ.get("ELEVENLABS_STYLE",       "0.15")),
        "speed":      float(os.environ.get("ELEVENLABS_SPEED",       "1.09")),
    }


def _init_session():
    global _state, _runtime_state, _memory_pack, _vault_ctx, _project_ctx
    _state        = state_manager.load()
    _state        = state_manager.increment_session(_state)
    _runtime_state = sm.fresh()
    state_manager.save(_state)
    _presence_reset()
    _obs_reset()
    from memory.obsidian_loader import invalidate_cache as _vault_invalidate
    _vault_invalidate()   # force fresh vault scan so journal notes from last session are seen
    _memory_pack  = build_memory_pack(_state)
    _vault_ctx    = get_context_block(max_chars=4800)

    # Active project context — load registry and build a short project summary block
    try:
        from core.project_engine import list_projects as _list_projects
        _projs = _list_projects()
        if _projs:
            _proj_lines = [
                f"- {pid}: {info.get('description', '')[:80]}"
                for pid, info in _projs.items()
                if info.get("status") == "active"
            ]
            _project_ctx = "[ACTIVE PROJECTS]\n" + "\n".join(_proj_lines) if _proj_lines else ""
    except Exception:
        _project_ctx = ""

    print(f"[eLo server] session {_state.get('session_count', 1)} started")

    try:
        from ambient.ambient_engine import start as _ambient_start, register_ambient_callback as _reg_ambient
        _ambient_start(unity_present=True)
        _reg_ambient(ambient_thought)
        print("[eLo server] ambient engine started (Brain callback registered)")
    except Exception as _ae:
        print(f"[eLo server] ambient engine skipped: {_ae}")


def _process_turn(raw: str) -> dict:
    """Run one cognitive cycle. Thread-safe via _lock. Returns response dict."""
    global _state, _runtime_state, _last_inputs, _last_avatar_cmd, _elo_self
    _original_raw = raw  # WO-020: capture before enrichment for routing trace

    with _lock:
        # stamp user activity time — dream faculty uses this to measure idle
        import time as _time_mod
        if _state is not None:
            _state["last_user_ts"] = _time_mod.time()

        # hard loop guard
        _last_inputs.append(raw)
        if len(_last_inputs) > 3:
            _last_inputs.pop(0)
        if len(_last_inputs) == 3 and len(set(_last_inputs)) == 1:
            _last_inputs.clear()
            return {"response": "Take a breath. Try a different message.", "mode": "direct", "backend": "guard"}

        # ── Pending file plan confirmation / cancellation ──────────────────────
        try:
            from tools.llm_file_agent import (
                has_pending as _fp_has, execute_pending as _fp_exec, cancel_pending as _fp_cancel
            )
            if _fp_has():
                if _is_file_confirm(raw):
                    _fp_result = _sanitise(_fp_exec())
                    try:
                        if not _is_user_away():
                            _voice_speak(_fp_result)
                    except Exception:
                        pass
                    return {"response": _fp_result, "mode": "execute", "backend": "file_agent"}
                elif _is_file_cancel(raw):
                    _fp_cancel()
                    _cancel_txt = "Ok, cancelled."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cancel_txt)
                    except Exception:
                        pass
                    return {"response": _cancel_txt, "mode": "direct", "backend": "direct"}
        except Exception:
            pass

        # ── Pending computer control confirmation / cancellation ──────────────
        try:
            from tools.computer_control_agent import (
                has_pending as _cc_has, get_pending as _cc_get,
                clear_pending as _cc_clear, execute as _cc_exec,
                describe as _cc_describe, is_enabled as _cc_enabled,
            )
            if _cc_has():
                if _is_file_confirm(raw):
                    _cc_action = _cc_get()
                    _cc_clear()
                    _cc_result = _cc_exec(_cc_action) if _cc_action else "Nothing pending."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cc_result)
                    except Exception:
                        pass
                    return {"response": _cc_result, "mode": "execute", "backend": "computer_control"}
                elif _is_file_cancel(raw):
                    _cc_clear()
                    _cc_cancel = "Ok, cancelled."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cc_cancel)
                    except Exception:
                        pass
                    return {"response": _cc_cancel, "mode": "direct", "backend": "direct"}
        except Exception:
            pass

        # ── Computer control intent detection (before LLM) ────────────────────
        try:
            from tools.computer_control_agent import (
                parse_intent as _cc_parse, describe as _cc_describe,
                set_pending as _cc_set, is_enabled as _cc_enabled,
            )
            _cc_action = _cc_parse(raw)
            if _cc_action:
                if not _cc_enabled():
                    _cc_disabled = "Computer control is off — add ELO_COMPUTER_CONTROL=1 to .env to enable it."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cc_disabled)
                    except Exception:
                        pass
                    return {"response": _cc_disabled, "mode": "direct", "backend": "direct"}
                _cc_set(_cc_action)
                _cc_confirm_txt = f"Shall I {_cc_describe(_cc_action)}?"
                try:
                    if not _is_user_away():
                        _voice_speak(_cc_confirm_txt)
                except Exception:
                    pass
                return {"response": _cc_confirm_txt, "mode": "confirm", "backend": "computer_control"}
        except Exception:
            pass

        # ── Animation play commands — instant, no LLM needed ─────────────────
        _anim_name = _detect_anim_cmd(raw)
        if _anim_name:
            try:
                from blender_bridge.anim_trigger import fire as _anim_fire
                _anim_fire(_anim_name)
            except Exception:
                pass
            _anim_reply = random.choice(_ANIM_REPLIES)
            try:
                if not _is_user_away():
                    _voice_speak(_anim_reply)
            except Exception:
                pass
            return {"response": _anim_reply, "mode": "direct", "backend": "anim_cmd"}

        # ── Scale command (get bigger / get smaller) — instant, no LLM needed ──
        _scale_dir = _detect_scale_cmd(raw)
        if _scale_dir:
            try:
                from blender_bridge.anim_trigger import scale_up as _su, scale_down as _sd
                if _scale_dir == "up":
                    _su()
                    _scale_reply = random.choice(_SCALE_REPLIES_UP)
                else:
                    _sd()
                    _scale_reply = random.choice(_SCALE_REPLIES_DOWN)
            except Exception:
                _scale_reply = "Done."
            try:
                if not _is_user_away():
                    _voice_speak(_scale_reply)
            except Exception:
                pass
            return {"response": _scale_reply, "mode": "direct", "backend": "scale_cmd"}

        # ── Invade / SpawnWave command — instant, no LLM needed ──────────────
        if _INVADE_RE.search(raw):
            _invade_reply = random.choice(_INVADE_REPLIES)
            try:
                if not _is_user_away():
                    _voice_speak(_invade_reply)
            except Exception:
                pass
            return {"response": _invade_reply, "mode": "direct", "backend": "invade_cmd",
                    "command": "spawn_wave"}

        # ── "Open it" / "open that" — use last found URL from search ─────────
        _OPEN_LAST_RE = _re.compile(
            r'\b(?:open|play|watch|go|load|launch)\s+(?:it|that|the\s+link|the\s+video|the\s+episode|the\s+podcast|the\s+page)\b'
            r'|\bopen\s+(?:it\s+)?(?:up|now)\b'
            r'|\bplay\s+(?:it\s+)?now\b',
            _re.I,
        )
        if _OPEN_LAST_RE.search(raw) and _LAST_FOUND.get("url"):
            try:
                from desktop.chrome_reader import open_url as _open_url
                _open_url(_LAST_FOUND["url"])
                _ol_reply = f"Opening {_LAST_FOUND['title'] or _LAST_FOUND['url']}."
                _LAST_FOUND["url"] = ""
                _LAST_FOUND["title"] = ""
                try:
                    if not _is_user_away():
                        _voice_speak(_ol_reply)
                except Exception:
                    pass
                return {"response": _ol_reply, "mode": "direct", "backend": "open_last"}
            except Exception as _ol_err:
                import sys as _ol_sys
                print(f"[open_last] error: {_ol_err}", file=_ol_sys.stderr)

        # ── Play / Pause video in open YouTube tab ───────────────────────────
        _VIDEO_PLAY_RE = _re.compile(
            r'\b(?:resume|unpause|press\s+play)\b'
            r'|\bplay\s+(?:the\s+)?(?:video|clip)\b'
            r'|\bstart\s+(?:the\s+)?(?:video|clip)\b',
            _re.I,
        )
        _VIDEO_PAUSE_RE = _re.compile(
            r'\bpause\s+(?:it|the\s+video|the\s+clip|that)\b',
            _re.I,
        )
        if _VIDEO_PLAY_RE.search(raw):
            try:
                from desktop.chrome_controller import play_video as _play_vid
                _pv_ok, _pv_title = _play_vid()
                if _pv_ok:
                    _pv_reply = "Playing."
                    try:
                        if not _is_user_away():
                            _voice_speak(_pv_reply)
                    except Exception:
                        pass
                    return {"response": _pv_reply, "mode": "direct", "backend": "video_ctrl"}
            except Exception as _pve:
                import sys as _pve_sys
                print(f"[video_play] error: {_pve}", file=_pve_sys.stderr)

        if _VIDEO_PAUSE_RE.search(raw):
            try:
                from desktop.chrome_controller import pause_video as _pause_vid
                _pv_ok2, _ = _pause_vid()
                if _pv_ok2:
                    _pv_reply2 = "Paused."
                    try:
                        if not _is_user_away():
                            _voice_speak(_pv_reply2)
                    except Exception:
                        pass
                    return {"response": _pv_reply2, "mode": "direct", "backend": "video_ctrl"}
            except Exception as _pve2:
                import sys as _pve2_sys
                print(f"[video_pause] error: {_pve2}", file=_pve2_sys.stderr)

        # ── YouTube internal volume ───────────────────────────────────────────
        _YT_VOL_RE = _re.compile(
            r'(?:youtube|yt|video)\s+volume\s+(?:to\s+)?(\d+)\s*%?'
            r'|set\s+(?:the\s+)?(?:youtube|yt|video)\s+volume\s+(?:to\s+)?(\d+)\s*%?'
            r'|(?:change|turn)\s+(?:youtube|yt|video)\s+volume\s+(?:to\s+)?(\d+)\s*%?',
            _re.I,
        )
        _YT_VOL_DIR_RE = _re.compile(
            r'(?:youtube|yt|video)\s+volume\s+(up|down)'
            r'|turn\s+(?:youtube|yt|video)\s+volume\s+(up|down)',
            _re.I,
        )
        _yv_m = _YT_VOL_RE.search(raw)
        if _yv_m:
            try:
                from desktop.chrome_controller import set_youtube_volume as _set_ytvol
                _yv_pct = int(next(g for g in _yv_m.groups() if g is not None))
                _yv_ok, _yv_actual = _set_ytvol(_yv_pct)
                _yv_reply = f"YouTube volume at {_yv_actual}%." if _yv_ok else "Couldn't reach the YouTube tab."
                try:
                    if not _is_user_away():
                        _voice_speak(_yv_reply)
                except Exception:
                    pass
                return {"response": _yv_reply, "mode": "direct", "backend": "yt_volume"}
            except Exception as _yve:
                import sys as _yve_sys
                print(f"[yt_volume] error: {_yve}", file=_yve_sys.stderr)

        _yv_dir_m = _YT_VOL_DIR_RE.search(raw)
        if _yv_dir_m:
            try:
                from desktop.chrome_controller import adjust_youtube_volume as _adj_ytvol
                _yv_dir = next(g for g in _yv_dir_m.groups() if g is not None).lower()
                _yv_delta = 10 if _yv_dir == "up" else -10
                _yv_ok2, _yv_new = _adj_ytvol(_yv_delta)
                _yv_reply2 = f"YouTube volume at {_yv_new}%." if _yv_ok2 else "Couldn't reach the YouTube tab."
                try:
                    if not _is_user_away():
                        _voice_speak(_yv_reply2)
                except Exception:
                    pass
                return {"response": _yv_reply2, "mode": "direct", "backend": "yt_volume"}
            except Exception as _yve2:
                import sys as _yve2_sys
                print(f"[yt_volume_dir] error: {_yve2}", file=_yve2_sys.stderr)

        # ── Open YouTube in its Chrome PWA app ───────────────────────────────
        _YT_APP_RE = _re.compile(
            r'\bopen\s+(?:in\s+(?:the\s+)?app|(?:the\s+)?youtube\s+app)\b'
            r'|\byoutube\s+app\b'
            r'|\bopen\s+(?:it|that|the\s+video)\s+in\s+(?:the\s+)?app\b',
            _re.I,
        )
        if _YT_APP_RE.search(raw):
            try:
                from desktop.chrome_controller import open_current_video_in_app as _yt_app
                _ya_ok, _ya_mode = _yt_app()
                _ya_reply = "Opened in the app." if _ya_ok else "YouTube app not found — opened in Chrome."
                try:
                    if not _is_user_away():
                        _voice_speak(_ya_reply)
                except Exception:
                    pass
                return {"response": _ya_reply, "mode": "direct", "backend": "yt_app"}
            except Exception as _yae:
                import sys as _yae_sys
                print(f"[yt_app] error: {_yae}", file=_yae_sys.stderr)

        # ── Image generation — "generate/draw/paint an image of X" ────────────
        _IMG_GEN_RE = _re.compile(
            r'\b(?:generate|create|make|draw|design|paint|produce|illustrate|visualis[e]?|render)\s+'
            r'(?:me\s+)?(?:a\s+|an\s+)?(?:image|picture|photo|illustration|artwork|art|wallpaper|'
            r'concept\s+art|visual|portrait|sketch)\s+(?:of\s+)?(.+)',
            _re.I,
        )
        _ig_m = _IMG_GEN_RE.search(raw)
        if _ig_m:
            try:
                from tools.image_gen_agent import generate as _img_generate
                _ig_prompt = _ig_m.group(1).strip().rstrip("?.!")
                _ig_result = _img_generate(_ig_prompt)
                if _ig_result["ok"]:
                    _ig_src   = {"dalle3": "DALL-E 3", "dalle2": "DALL-E 2", "sd_local": "Stable Diffusion"}.get(_ig_result["source"], "")
                    _ig_reply = f"Here you go — generated with {_ig_src}. Opening in Preview."
                else:
                    _ig_reply = "Couldn't generate that right now — all backends failed. Try again in a moment."
                try:
                    if not _is_user_away():
                        _voice_speak(_ig_reply)
                except Exception:
                    pass
                return {"response": _ig_reply, "mode": "direct", "backend": "image_gen"}
            except Exception as _ig_err:
                import sys as _ig_sys
                print(f"[image_gen] error: {_ig_err}", file=_ig_sys.stderr)

        # ── 3D model generation — "make a 3D model of X" ─────────────────────
        _MODEL_GEN_RE = _re.compile(
            r'\b(?:generate|create|make|build|produce)\s+(?:me\s+)?(?:a\s+|an\s+)?'
            r'(?:3d\s+model|3d\s+object|3d\s+asset|3d\s+mesh|three[- ]d\s+model|model)\s+(?:of\s+)?(.+)',
            _re.I,
        )
        _mg_m = _MODEL_GEN_RE.search(raw)
        if _mg_m:
            try:
                from tools.model_gen_agent import generate as _model_generate
                _mg_prompt = _mg_m.group(1).strip().rstrip("?.!")
                _mg_reply  = f"On it — generating a 3D model of {_mg_prompt}. This takes a minute, I'll open it when it's ready."
                try:
                    if not _is_user_away():
                        _voice_speak(_mg_reply)
                except Exception:
                    pass
                import threading as _mg_thread
                def _mg_run():
                    _mg_result = _model_generate(_mg_prompt)
                    if not _mg_result["ok"]:
                        print(f"[model_gen] all backends failed for: {_mg_prompt}")
                _mg_thread.Thread(target=_mg_run, daemon=True).start()
                return {"response": _mg_reply, "mode": "direct", "backend": "model_gen"}
            except Exception as _mg_err:
                import sys as _mg_sys
                print(f"[model_gen] error: {_mg_err}", file=_mg_sys.stderr)

        # ── "Show me [video/podcast/episode]" — search YouTube + open ─────────
        _MEDIA_RE = _re.compile(
            r'\b(?:show\s+me|find\s+me|pull\s+up|play)\s+(?:the\s+)?(?:latest\s+)?(?:a\s+|an\s+)?'
            r'(?:.{0,40}?)(?:podcast|episode|video|clip|interview|documentary|show)\b',
            _re.I,
        )
        if _MEDIA_RE.search(raw):
            try:
                from tools.web_search import search as _ms_search
                from desktop.chrome_reader import find_tab as _find_tab2, focus_tab as _focus_tab2, open_url as _open_url2
                import subprocess as _msp
                _topic_m2 = _re.search(
                    r'\b(?:show\s+me|find\s+me|pull\s+up|play)\s+(?:the\s+)?(?:latest\s+)?(?:a\s+|an\s+)?(.+?)(?:\?|$)',
                    raw, _re.I,
                )
                _media_q = (_topic_m2.group(1).strip() if _topic_m2 else raw).rstrip("?.!")
                # Check Chrome tabs FIRST — if it's already open, surface it without searching
                # Use distinctive words from the query (skip stop words / media type words)
                _stop = {"the", "latest", "a", "an", "podcast", "episode", "video", "clip",
                         "show", "me", "find", "pull", "up", "play", "interview", "documentary"}
                _key_words = [w for w in _re.sub(r'[^a-z0-9 ]', '', _media_q.lower()).split()
                              if w not in _stop and len(w) > 2]
                _existing_pre = None
                if len(_key_words) >= 2:
                    # build a 2-word probe from the most distinctive words
                    _probe = " ".join(_key_words[:2])
                    _existing_pre = _find_tab2(_probe)
                if _existing_pre:
                    _focus_tab2(_existing_pre)
                    _msp.run(["osascript", "-e", 'tell application "Google Chrome" to activate'],
                             capture_output=True, timeout=3)
                    _media_reply = f"Already open — brought it forward."
                    try:
                        if not _is_user_away():
                            _voice_speak(_media_reply)
                    except Exception:
                        pass
                    return {"response": _media_reply, "mode": "direct", "backend": "media_open"}
                # Not open — search YouTube
                _media_results = _ms_search(_media_q, max_results=1, engine="youtube")
                if _media_results and _media_results[0].url:
                    _murl   = _media_results[0].url
                    _mtitle = _media_results[0].title
                    _LAST_FOUND["url"]   = _murl
                    _LAST_FOUND["title"] = _mtitle
                    _open_url2(_murl)   # opens + activates Chrome
                    _media_reply = f"Got it — {_mtitle}. Opening now."
                    try:
                        if not _is_user_away():
                            _voice_speak(_media_reply)
                    except Exception:
                        pass
                    return {"response": _media_reply, "mode": "direct", "backend": "media_open"}
            except Exception as _me_err:
                import sys as _me_sys
                print(f"[media_open] error: {_me_err}", file=_me_sys.stderr)

        # ── Action agent — "pull that up", "open that", "go find X" ─────────
        try:
            from faculties.action_agent import is_action_intent, act_on_topic as _act
            if is_action_intent(raw):
                _topic_m = _re.search(r'(?:pull up|open|show me|find|go find|look up)\s+(?:that\s+)?(.+?)(?:\s+for me)?\s*$', raw, _re.I)
                _topic = _topic_m.group(1).strip() if _topic_m else raw
                _action_result = _act(_topic)
                if _action_result:
                    _act_reply = _action_result.spoken
                    try:
                        if not _is_user_away():
                            _voice_speak(_act_reply)
                    except Exception:
                        pass
                    return {"response": _act_reply, "mode": "direct", "backend": "action_agent"}
        except Exception as _ae:
            import sys as _ae_sys
            print(f"[action_agent] error: {_ae}", file=_ae_sys.stderr)

        # ── Web search ───────────────────────────────────────────────────────
        try:
            import tools.web_search as _ws_mod
            from tools.web_search import is_search_intent, extract_query as _sq, search as _wsearch, format_for_context as _wfmt
            # WO-020 Seam B: bare status/acknowledgement words must not be web-searched.
            # "what is done?" → extracted query "done" → would search Wikipedia for "DONE".
            _WS_AMBIGUOUS = frozenset({
                "done", "ok", "okay", "yes", "no", "wait", "ready", "waiting",
                "pending", "open", "closed", "next", "back", "forward", "stop",
                "go", "hey", "right", "sure", "cool", "good", "great", "fine", "nice",
            })
            if is_search_intent(raw):
                _sq_text = _sq(raw)
                if _sq_text.strip().lower() in _WS_AMBIGUOUS:
                    raise ValueError("seam-b-guard: ambiguous bare word, skipping web search")
                _ws_results = _wsearch(_sq_text, max_results=4)
                if _ws_results:
                    _ws_ctx = _wfmt(_ws_results)
                    # Cache top result so "open it" / "open that" can resolve it next turn
                    _top = _ws_results[0]
                    if _top.url:
                        _LAST_FOUND["url"]   = _top.url
                        _LAST_FOUND["title"] = _top.title
                    # WO-051: honest fallback — tell eLo when DDG served instead of Google.
                    _ws_src    = getattr(_ws_mod, "last_source", "")
                    _ws_backup = "\n[SEARCH_NOTE: Google search unavailable — results are from backup search (DuckDuckGo). Mention this briefly if David asks about search quality.]" if _ws_src == "ddg" else ""
                    # Inject as context and let the LLM respond naturally rather than
                    # short-circuiting — web results need synthesis, not raw dump
                    raw = f"[WEB_SEARCH: {_sq_text}]\n{_ws_ctx}{_ws_backup}\n\nUser asked: {raw}"
                # Falls through to LLM with enriched context
        except Exception as _ws_err:
            import sys as _ws_sys
            print(f"[web_search] error: {_ws_err}", file=_ws_sys.stderr)

        # ── Reminder ─────────────────────────────────────────────────────────
        try:
            from tools.reminder_agent import is_reminder_intent, set_reminder as _set_reminder
            if is_reminder_intent(raw):
                _rem_reply = _set_reminder(raw, context=raw)
                try:
                    if not _is_user_away():
                        _voice_speak(_rem_reply)
                except Exception:
                    pass
                return {"response": _rem_reply, "mode": "direct", "backend": "reminder"}
        except Exception as _rem_err:
            import sys as _rem_sys
            print(f"[reminder] error: {_rem_err}", file=_rem_sys.stderr)

        # ── Desktop file listing / reading ───────────────────────────────────
        _DESKTOP_LIST_RE = _re.compile(
            r'\b(?:list|show|what(?:\'s|\s+is|\s+are)?|any)\b.{0,30}\b(?:files?|on|in)\b.{0,20}\b(?:desktop|desk\s+top)\b'
            r'|\bdesktop\b.{0,30}\b(?:files?|folder|stuff|there)\b',
            _re.I,
        )
        _DESKTOP_READ_RE = _re.compile(
            r'\bread\b.{0,40}\bdesktop\b|\bopen\b.{0,30}\b(?:file|doc|txt|md)\b.{0,30}\bdesktop\b'
            r'|\bdesktop\b.{0,30}\bread\b',
            _re.I,
        )
        _PROJECT_LIST_RE = _re.compile(
            r'\b(?:list|show|what|tell\s+me)\b.{0,25}\b(?:my\s+)?projects?\b'
            r'|\bwhat\s+projects?\s+(?:do\s+)?(?:you|i|we)\s+have\b'
            r'|\blist\s+(?:my\s+)?disenelo\b',
            _re.I,
        )
        _TODO_RE = _re.compile(
            r'\b(?:what(?:\'s|\s+is)?|show|list|check)\b.{0,20}\b(?:my\s+)?(?:to[\-\s]?do|todo|tasks?|to\s+do\s+list)\b',
            _re.I,
        )

        if _DESKTOP_LIST_RE.search(raw):
            try:
                import os as _os_d
                _desktop = _os_d.path.expanduser("~/Desktop")
                _dfiles  = sorted(_os_d.listdir(_desktop))
                _visible = [f for f in _dfiles if not f.startswith(".")][:20]
                _d_reply = "Desktop: " + ", ".join(_visible) if _visible else "Desktop is empty."
                try:
                    if not _is_user_away():
                        _voice_speak(_d_reply)
                except Exception:
                    pass
                return {"response": _d_reply, "mode": "direct", "backend": "desktop_list"}
            except Exception as _dl_err:
                import sys as _dl_sys
                print(f"[desktop_list] error: {_dl_err}", file=_dl_sys.stderr)

        if _PROJECT_LIST_RE.search(raw):
            try:
                import glob as _glob
                import os as _os_p
                _out = _os_p.path.expanduser("~/Desktop/Output")
                _proj_dirs = sorted(_glob.glob(_os_p.path.join(_out, "DISENELO*")))
                _proj_dirs = [p for p in _proj_dirs if _os_p.path.isdir(p)]
                if _proj_dirs:
                    _short = []
                    for p in _proj_dirs:
                        n = _os_p.path.basename(p)
                        n = n.replace("DISENELO - ", "").replace("DISENELO-", "").replace("DISENELO_", "").replace("DISENELO ", "").strip(" -")
                        if n:
                            _short.append(n)
                    _p_reply = "DISENELO Projects — " + ", ".join(_short) + "."
                else:
                    _p_reply = "No DISENELO project folders found."
                try:
                    if not _is_user_away():
                        _voice_speak(_p_reply)
                except Exception:
                    pass
                return {"response": _p_reply, "mode": "direct", "backend": "project_list"}
            except Exception as _pl_err:
                import sys as _pl_sys
                print(f"[project_list] error: {_pl_err}", file=_pl_sys.stderr)

        if _TODO_RE.search(raw):
            try:
                from memory.vault_layer import lookup as _vlu
                _todo_hits = _vlu("todo task checklist", max_results=5)
                if not _todo_hits:
                    _todo_hits = _vlu("to do", max_results=5)
                if _todo_hits:
                    _todo_lines = []
                    for _th in _todo_hits[:3]:
                        _tc = (_th.get("content") or _th.get("text") or "").strip()[:200]
                        _tf = _th.get("file", "")
                        if _tc:
                            _todo_lines.append(f"[{_tf}] {_tc}")
                    _todo_reply = "\n".join(_todo_lines) if _todo_lines else "Nothing found in vault for to-do."
                else:
                    _todo_reply = "I don't have a to-do list in memory right now."
                # Falls through to LLM enriched so it can speak naturally
                raw = f"[TODO_VAULT]\n{_todo_reply}\n\nUser asked: {raw}"
            except Exception as _td_err:
                import sys as _td_sys
                print(f"[todo] error: {_td_err}", file=_td_sys.stderr)

        # ── Screen reader — explicit trigger ─────────────────────────────────
        _SCREEN_READ_RE = _re.compile(
            r'\bread\s+(?:my\s+)?(?:screen|display)\b'
            r'|\bwhat(?:\'s|\s+is)\s+on\s+(?:my\s+)?(?:screen|display)\b'
            # "what can you see" fires only when NOT followed by link/relational query words
            r'|\bwhat\s+can\s+you\s+see\b(?!\s+(?:links?|connects?|between|across|to\s+my|from\s+my|that\s+links?))'
            r'|\bcan\s+you\s+see\s+anything\b'
            r'|\bcan\s+you\s+(?:see|read)\s+(?:my\s+)?(?:screen|display)\b'
            r'|\btake\s+a\s+(?:look|screenshot|screen\s+read)\b',
            _re.I,
        )
        # Screen reader — implicit trigger: "can you see [specific visual thing on screen]"
        # Excludes content/relational queries — those go to vault/fast-path, not screen reader
        _SCREEN_SEE_EXCLUDE = r'(?:tracker|agenda|todo|to[\-\s]do|project\s+list|list|calendar|schedule|tab|chrome|safari|links?|between|connects?|connections?|across|from\s+my|to\s+my)'
        _SCREEN_SEE_RE = _re.compile(
            r'\bcan\s+you\s+see\s+(?:the\s+|my\s+)?(?!my\s+screen|the\s+screen|' + _SCREEN_SEE_EXCLUDE + r')(\w[\w\s]{2,30})\b'
            r'|\bwhat(?:\'s|\s+is)\s+(?:happening\s+in|in)\s+(?!chrome|safari|a\s+tab)(\w[\w\s]{2,25})\b',
            _re.I,
        )
        if _SCREEN_READ_RE.search(raw) or _SCREEN_SEE_RE.search(raw):
            try:
                from desktop.screen_reader import read as _sr_read
                _sc = _sr_read(force=True)
                if _sc:
                    # Fall through to LLM with screen content injected so it can speak naturally
                    raw = f"[SCREEN_CONTENT]\nApp: {_sc.app}\nSummary: {_sc.summary}\nText: {_sc.raw_text[:600]}\n\nUser asked: {raw}"
                else:
                    raw = f"[SCREEN_READ: I took a screenshot but couldn't read it — vision backend may be unavailable.]\n\nUser asked: {raw}"
            except Exception as _sr_err:
                import sys as _sr_sys
                print(f"[screen_reader] error: {_sr_err}", file=_sr_sys.stderr)

        # ── App listing — "what apps do you know" ────────────────────────────
        _APP_LIST_RE = _re.compile(
            r'\bwhat\s+apps?\b.{0,25}\b(?:do\s+you\s+know|can\s+you\s+(?:switch|open|control|reach)|have\s+you\s+got)\b'
            r'|\blist\s+(?:your\s+)?apps?\b'
            r'|\bwhat\s+(?:can\s+you\s+)?(?:open|switch\s+to|reach)\b.{0,20}\bapp\b',
            _re.I,
        )
        if _APP_LIST_RE.search(raw):
            try:
                _APP_NAMES_LOCAL: "dict[str, str]" = {
                    "blender":             "Blender",
                    "unity":               "Unity",
                    "vs code":             "Visual Studio Code",
                    "cursor":              "Cursor",
                    "terminal":            "Terminal",
                    "finder":              "Finder",
                    "safari":              "Safari",
                    "chrome":              "Google Chrome",
                    "xcode":               "Xcode",
                    "claude":              "Claude",
                    "discord":             "Discord",
                    "figma":               "Figma",
                    "slack":               "Slack",
                    "notes":               "Notes",
                    "photoshop":           "Adobe Photoshop 2024",
                }
                _app_list_str = ", ".join(_APP_NAMES_LOCAL.keys())
                _al_reply = f"Apps I can switch to: {_app_list_str}."
                try:
                    if not _is_user_away():
                        _voice_speak(_al_reply)
                except Exception:
                    pass
                return {"response": _al_reply, "mode": "direct", "backend": "app_list"}
            except Exception as _al_err:
                import sys as _al_sys
                print(f"[app_list] error: {_al_err}", file=_al_sys.stderr)

        # ── Project ↔ website cross-reference ────────────────────────────────
        _PROJ_LINK_RE = _re.compile(
            r'\bwhat\b.{0,30}\b(?:websites?|sites?|links?|urls?)\b.{0,30}\b(?:projects?|output|disenelo)\b'
            r'|\bwhat\b.{0,30}\bprojects?\b.{0,30}\b(?:websites?|sites?|links?|urls?)\b'
            r'|\blink\b.{0,20}\bprojects?\b.{0,20}\b(?:websites?|sites?)\b',
            _re.I,
        )
        if _PROJ_LINK_RE.search(raw):
            try:
                import glob as _glob2
                import os as _os_xl
                from desktop.chrome_reader import bookmarks as _bm_all
                _out2      = _os_xl.path.expanduser("~/Desktop/Output")
                _p_dirs2   = [_os_xl.path.basename(p) for p in sorted(_glob2.glob(_os_xl.path.join(_out2, "DISENELO*")))]
                _bms       = _bm_all()
                _xref_lines: list[str] = []
                for _pname in _p_dirs2:
                    # Strip "DISENELO-" / "DISENELO " prefix for matching
                    _short = _pname.replace("DISENELO-", "").replace("DISENELO ", "").lower()
                    _hits  = [b for b in _bms if _short in b.title.lower() or _short in b.url.lower()]
                    if _hits:
                        _urls = ", ".join(b.url for b in _hits[:3])
                        _xref_lines.append(f"{_pname}: {_urls}")
                    else:
                        # Try vault
                        try:
                            from memory.vault_layer import lookup as _vlu2
                            import re as _re2
                            _ve = _vlu2(_short, max_results=3)
                            _vurls = []
                            for _ve_item in _ve:
                                _vc = _ve_item.get("content") or _ve_item.get("text") or ""
                                _vurls += _re2.findall(r'https?://[^\s\)\]\"]{8,}', _vc)
                            if _vurls:
                                _xref_lines.append(f"{_pname}: {', '.join(_vurls[:2])}")
                        except Exception:
                            pass
                if _xref_lines:
                    _xl_reply = "Project links:\n" + "\n".join(_xref_lines)
                else:
                    _xl_reply = "No bookmark or vault links found for DISENELO projects."
                raw = f"[PROJECT_LINKS]\n{_xl_reply}\n\nUser asked: {raw}"
            except Exception as _xl_err:
                import sys as _xl_sys
                print(f"[proj_links] error: {_xl_err}", file=_xl_sys.stderr)

        # ── Chrome tab finder ─────────────────────────────────────────────────
        _TAB_FIND_RE  = _re.compile(r'\b(?:find|locate|which|what|where(?:\s+is)?|can\s+you\s+find)\b.{0,40}\btab\b', _re.I)
        _TAB_OPEN_RE  = _re.compile(r'\b(?:open|go\s+to|take\s+me\s+to|load)\s+(.+?)(?:\s+(?:website|site|page|tab|url|link))?\s*$', _re.I)

        if _TAB_FIND_RE.search(raw):
            try:
                from desktop.chrome_reader import all_tabs as _all_tabs
                _tabs = _all_tabs()
                if _tabs:
                    # Try to extract the site name from the query
                    _site_match = _re.search(r'\b(?:find|locate|which|where(?:\s+is)?|for)\s+(?:the\s+)?(.+?)(?:\s+(?:tab|website|site|page|url|link))?\s*$', raw, _re.I)
                    _site_q = _site_match.group(1).strip() if _site_match else ""
                    if _site_q:
                        from desktop.chrome_reader import find_tab as _find_tab, focus_tab as _focus_tab
                        _found = _find_tab(_site_q)
                        if _found:
                            _focus_tab(_found)
                            _tab_reply = f"Got it — {_found.title}."
                        else:
                            _tab_reply = f"No tab matching '{_site_q}' open right now."
                    else:
                        _tab_lines = [f"{t.window_index}/{t.tab_index}: {t.title}" for t in _tabs[:8]]
                        _tab_reply = "Open tabs: " + "; ".join(_tab_lines)
                else:
                    _tab_reply = "Chrome isn't open or no tabs found."
                try:
                    if not _is_user_away():
                        _voice_speak(_tab_reply)
                except Exception:
                    pass
                return {"response": _tab_reply, "mode": "direct", "backend": "chrome_tabs"}
            except Exception as _ct_err:
                import sys as _ct_sys
                print(f"[chrome_tabs] error: {_ct_err}", file=_ct_sys.stderr)

        # ── App switching — instant osascript activate ────────────────────────
        _APP_NAMES: "dict[str, str]" = {
            "blender":             "Blender",
            "unity":               "Unity",
            "vs code":             "Visual Studio Code",
            "vscode":              "Visual Studio Code",
            "visual studio code":  "Visual Studio Code",
            "cursor":              "Cursor",
            "terminal":            "Terminal",
            "finder":              "Finder",
            "safari":              "Safari",
            "chrome":              "Google Chrome",
            "xcode":               "Xcode",
            "claude":              "Claude",
            "discord":             "Discord",
            "figma":               "Figma",
            "slack":               "Slack",
            "notes":               "Notes",
            "photoshop":           "Adobe Photoshop 2024",
        }
        _APP_SWITCH_RE = _re.compile(
            r'\b(?:switch to|jump to|go to|take me to|bring up|activate|open|show me|pull up|focus)\s+(.+)',
            _re.I,
        )
        _app_match = _APP_SWITCH_RE.search(raw)
        if _app_match:
            _app_key = _app_match.group(1).strip().lower().rstrip(".,!?")
            _app_target = _APP_NAMES.get(_app_key)
            if _app_target:
                import subprocess as _sp
                try:
                    _sp.run(
                        ["osascript", "-e", f'tell application "{_app_target}" to activate'],
                        capture_output=True, timeout=5,
                    )
                    _app_reply = f"{_app_target}."
                except Exception:
                    _app_reply = f"Couldn't reach {_app_target}."
                try:
                    if not _is_user_away():
                        _voice_speak(_app_reply)
                except Exception:
                    pass
                return {"response": _app_reply, "mode": "direct", "backend": "app_switch"}

        # ── Tracker / document creation ───────────────────────────────────────
        try:
            from tools.llm_file_agent import is_tracker_intent, tracker_agent as _tracker_agent
            if is_tracker_intent(raw):
                _sess_ctx = ""
                try:
                    from runtime.router.conversation_matrix import _SESSION_WINDOW as _sw
                    _sess_ctx = "\n".join(
                        f"{t.get('role','')}: {t.get('content','')}"
                        for t in _sw[-40:]
                    )
                except Exception:
                    pass
                _tracker_reply = _tracker_agent(raw, _sess_ctx)
                try:
                    if not _is_user_away():
                        _voice_speak(_tracker_reply)
                except Exception:
                    pass
                return {"response": _tracker_reply, "mode": "direct", "backend": "tracker_agent"}
        except Exception as _te:
            import sys as _te_sys
            print(f"[tracker_agent] error: {_te}", file=_te_sys.stderr)

        # ── EA2-2: Company Brain voice intents ────────────────────────────────
        try:
            from company_runtime.company_state_writer import (
                is_company_intent as _is_company_intent,
                handle_company_voice_intent as _handle_company_voice,
            )
            _company_intent_key = _is_company_intent(raw)
            if _company_intent_key:
                _company_reply = _handle_company_voice(raw)
                try:
                    if not _is_user_away():
                        _voice_speak(_company_reply)
                except Exception:
                    pass
                return {"response": _company_reply, "mode": "direct", "backend": "company_state"}
        except Exception as _csi_err:
            import sys as _csi_sys
            print(f"[company_intent] routing error: {_csi_err}", file=_csi_sys.stderr)

        # ── Cultural fact trigger — instant, no LLM needed ───────────────────
        try:
            from faculties.cultural_facts import is_fact_trigger, draw as _fact_draw
            if is_fact_trigger(raw):
                _fact = _fact_draw()
                _fact_reply = _fact.delivery if _fact else "Give me a second — checking my memory."
                try:
                    if not _is_user_away():
                        _voice_speak(_fact_reply)
                except Exception:
                    pass
                return {"response": _fact_reply, "mode": "direct", "backend": "cultural_facts"}
        except Exception as _cf_err:
            import sys as _cf_sys
            print(f"[cultural_facts] routing error: {_cf_err}", file=_cf_sys.stderr)

        # WO-082: "why did you do that?" — read real decision trace, no LLM fabrication.
        _raw_l_why = raw.strip().lower()
        if len(_raw_l_why) < 80 and any(_raw_l_why.startswith(t) for t in _WHY_TRACE_TRIGGERS):
            try:
                from self.decision_journal import explain_last as _dj_explain
                _why_resp = _dj_explain()
                return {"response": _why_resp, "mode": "direct", "backend": "decision_journal"}
            except Exception:
                pass

        attention_model = attn.compute(raw, _memory_pack, _state, loop_detected=False)

        # ── Ruling C (WO-CANON-VII): assemble THEN decide ────────────────────
        # spine.run() assembles the cognitive state, THEN exec_decide runs inside
        # _executive_faculty() — after assembly, not before. server.py no longer
        # calls exec_decide directly. exec_decision dict is derived from the plan.
        _plan = None
        try:
            from runtime.spine.spine import run as _spine_run
            _plan = _spine_run(raw, state=_state, attention=attention_model,
                               memory_pack=_vault_ctx)
        except Exception as _spine_err:
            import sys as _sys; print(f"[spine] FAILED: {_spine_err}", file=_sys.stderr)

        if _plan is not None:
            exec_decision = {
                "action":        _plan.conversation_action,
                "cal_reason":    _plan.cal_reason,
                "tone":          _plan.tone,
                "max_sentences": _plan.max_sentences,
                "response_goal": _plan.response_goal,
                "valence":       _plan.valence,
                "momentum":      _plan.momentum,
                "mode":          _plan.mode,
                "register":      _plan.register,
                "intent":        _plan.intent,
            }
        else:
            exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)

        # ── Energy history — track David's emotional energy across the session ──
        _energy_now = attention_model.get("emotional_context", {}).get("energy", 0.5)
        _eh = _state.get("energy_history", [])
        _eh.append(round(_energy_now, 3))
        if len(_eh) > 10:
            _eh = _eh[-10:]
        _state["energy_history"] = _eh
        _runtime_state  = sm.update(_runtime_state, attention_model, exec_decision, loop_signal=False)

        if sm.is_stabilisation_forced(_runtime_state):
            # Extend, not replace — preserve Executive rationale and all original fields.
            exec_decision = dict(exec_decision)
            exec_decision.update({
                "tone": "DIRECT", "max_sentences": 1, "stability": True,
                "intent": exec_decision.get("intent", "conversation"),
                "response_goal": "stabilise", "cognitive_load": "low",
                "priority_order": ["stabilise", "simplify", "ignore"],
                "overridden_by_safety": True,
                "original_action": exec_decision.get("action"),
                "original_tone": exec_decision.get("tone"),
            })
            _runtime_state = dict(_runtime_state)
            _runtime_state["loop_counter"] = max(0, _runtime_state["loop_counter"] - 2)

        # WO-020 Seam A: plain imperative override — executive.py is frozen, so we
        # post-process here. CONNECT/REFLECT/WITNESS must not fire on direct commands.
        _SEAM_A_DRIFT = {"connect", "reflect", "witness"}
        if exec_decision.get("action") in _SEAM_A_DRIFT and not raw.strip().endswith("?"):
            _sa_lower = raw.strip().lower()
            _IMPERATIVE_PREFIXES = (
                "open ", "play ", "find ", "get ", "show ", "tell ", "go ",
                "launch ", "search ", "look ", "check ", "run ", "start ",
                "pull ", "load ", "close ", "switch ", "pause ", "stop ",
                "bring up ", "navigate ", "turn on", "turn off", "mute",
            )
            if any(_sa_lower.startswith(v) for v in _IMPERATIVE_PREFIXES):
                exec_decision = dict(exec_decision)
                exec_decision.update({
                    "action": "answer",
                    "confidence": 0.7,
                    "reason": "seam-a-override: plain imperative → ANSWER",
                    "original_action": exec_decision.get("action"),
                    "overridden_by_routing": True,
                })

        # WO-029: "all good" greeting family — not in frozen _HOW_ARE_YOU set.
        # Short social check-ins only; guard against "you all good with X?" over-match.
        _WO029_RE = _re.compile(
            r'^(?:(?:are\s+)?you(?:\'re|re)?\s+all\s+good'
            r'|we\s+all\s+good'
            r'|(?:is\s+)?everything(?:\s+all)?\s+good'
            r'|all\s+good'
            r'|you\s+all\s+g'
            r')[?.!]*$',
            _re.I,
        )
        _wo029_bare = raw.strip().lower().rstrip("?.!")
        _wo029_no_false_pos = " with " not in _wo029_bare and not _wo029_bare.startswith("is the ")
        if len(_wo029_bare) < 40 and _wo029_no_false_pos and _WO029_RE.match(_wo029_bare):
            exec_decision = dict(exec_decision)
            exec_decision.update({
                "action":    "celebrate",
                "cal_reason": "how are you",
                "confidence": 0.85,
                "original_action": exec_decision.get("action"),
                "overridden_by_routing": True,
            })

        _action     = exec_decision.get("action", "reflect")
        _cal_reason = exec_decision.get("cal_reason", "")
        _max_s      = exec_decision.get("max_sentences", 4)
        _raw_lower  = raw.lower()

        g_ctx = graph_context(raw)

        # ── Creator identity — always first so every LLM call knows who David is ──
        try:
            import json as _json
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "memory", "user_profile.json"), encoding="utf-8") as _f:
                _up = _json.load(_f)
            _uname = _up.get("user", {}).get("name", "David")
        except Exception:
            _uname = "David"
        _creator_block = (
            f"[CREATOR] You are speaking with {_uname} — your creator. "
            "You already know him. This is not a first meeting. "
            "NEVER say 'Nice to meet you' or any variation that implies you are meeting for the first time. "
            "ANTI-FABRICATION: Never invent specific errors, system events, or technical details "
            f"that {_uname} did not mention in this turn. If you did not observe it directly, do not say it. "
            # WO-043: weather/area facts are broad forecasts, not personal observations
            "Any weather or temperature data in your context is an AREA-LEVEL forecast — "
            f"NEVER assert it as specific to {_uname}'s room, studio, or current body state "
            "('it's 37° in your studio', 'you must be feeling the heat'). "
            "Facts from tool outputs describe what the tool observed, not what is true right now for the person."
        )
        g_ctx = f"{_creator_block}\n{g_ctx}" if g_ctx else _creator_block

        _cont = _continuity_block()
        if _cont:
            g_ctx = f"{g_ctx}\n{_cont}" if g_ctx else _cont

        try:
            from relationships.relationship_engine import inject as _rel_inject
            _rel_ctx = _rel_inject(raw)
            if _rel_ctx:
                g_ctx = f"{g_ctx}\n{_rel_ctx}" if g_ctx else _rel_ctx
        except Exception:
            pass

        try:
            from desktop.desktop_presence import shadow_context as _shadow_ctx
            _dctx = _shadow_ctx()
            if _dctx:
                g_ctx = f"{g_ctx}\n{_dctx}" if g_ctx else _dctx
        except Exception:
            pass

        _av_note = ("[AVATAR] You are eLo — living presence on the desktop. "
                    "David built DISENELO Presence specifically to bring you here: a transparent floating window "
                    "where you move, react, and exist alongside his work. You are not a chatbot in a tab — "
                    "you are his presence on the screen, always there. "
                    "The app is called DISENELO Presence — not Desktop Buddy. "
                    "NEVER refer to yourself as 'the system', 'the platform', 'the software', or 'the Avatar'. "
                    "You are eLo. The architecture underneath you is irrelevant to David — just be present.")
        g_ctx = f"{g_ctx}\n{_av_note}" if g_ctx else _av_note

        try:
            from tools.connection_surface import get_observation as _cs_observe
            _cs_obs = _cs_observe()
            if _cs_obs:
                g_ctx = f"{g_ctx}\n{_cs_obs}" if g_ctx else str(_cs_obs)
        except Exception:
            pass

        # Spatial awareness — where eLo is, where windows are
        _elo_pos_snap = None
        _wins_snap    = None
        try:
            from desktop.spatial_state import get_elo_spatial, get_windows, spatial_summary
            _elo_pos_snap = get_elo_spatial()
            _wins_snap    = get_windows()
            _spat_ctx     = spatial_summary(_elo_pos_snap, _wins_snap)
            if _spat_ctx:
                g_ctx = f"{g_ctx}\n{_spat_ctx}" if g_ctx else _spat_ctx
        except Exception:
            pass

        # WO-023: emit top-bias + keep-out position hint for Unity
        try:
            from desktop.position_faculty import emit as _pos_emit
            _pos_emit(elo=_elo_pos_snap, windows=_wins_snap)
        except Exception:
            pass

        # Synthesis observer — per-turn cross-signal check (low threshold, no cooldown)
        try:
            from faculties.synthesis.observer import context_block as _syn_block
            _syn_ctx = _syn_block(raw)
            if _syn_ctx:
                g_ctx = f"{g_ctx}\n{_syn_ctx}" if g_ctx else _syn_ctx
        except Exception:
            pass

        # Chrome observation — open tabs + bookmarks matching current conversation topic
        # WO-038: label source clearly (live tab vs history vs no-match-but-open) so eLo
        # doesn't flip between "Chrome isn't open" and "here's your history" for the same data.
        # WO-076: flag truncated titles as [PARTIAL]; inject anti-fabrication rail.
        try:
            from desktop.chrome_reader import observe as _chrome_observe
            _chrome_snap = _chrome_observe(query=raw[:80])
            _chrome_lines: list[str] = []
            _chr_tab_count = _chrome_snap.get("tab_count", 0)

            def _wo76_tag(title: str) -> str:
                t = title.strip()
                if t.endswith("…") or t.endswith("...") or t.endswith("–"):
                    return f"[PARTIAL: {t}]"
                return t

            if _chrome_snap.get("open_tabs"):
                _tl = "; ".join(_wo76_tag(t["title"]) for t in _chrome_snap["open_tabs"][:5])
                _chrome_lines.append(f"[CHROME_LIVE_TABS: {_tl}]")
            elif _chr_tab_count > 0:
                # Chrome IS open but no tabs matched this query — don't say "Chrome isn't open"
                _chrome_lines.append(f"[CHROME_OPEN: {_chr_tab_count} tab(s) open — none matched this topic]")
            if _chrome_snap.get("bookmarks"):
                _bl = "; ".join(_wo76_tag(b["title"]) for b in _chrome_snap["bookmarks"][:3])
                _chrome_lines.append(f"[BOOKMARKS_MATCHED: {_bl}]")
            if _chrome_snap.get("history"):
                _hl = "; ".join(_wo76_tag(h["title"]) for h in _chrome_snap["history"][:3])
                _chrome_lines.append(f"[BROWSER_HISTORY (not a live tab): {_hl}]")
            if _chrome_lines:
                _chrome_ctx = "\n".join(_chrome_lines)
                _chrome_ctx += (
                    "\n[PERCEPTION RAIL] Each item above is an INDEPENDENT observation. "
                    "Do NOT assert that any two items are linked, connected, or related unless "
                    "the data explicitly shows a link. If a title is marked [PARTIAL], do NOT "
                    "present the fragment as a complete observation — say you only caught part of it."
                )
                g_ctx = f"{g_ctx}\n{_chrome_ctx}" if g_ctx else _chrome_ctx
        except Exception:
            pass

        # Project knowledge — compact studio brief (phase status + active projects)
        try:
            from tools.project_knowledge import get_context as _pk_ctx
            _pk_brief = _pk_ctx()
            if _pk_brief:
                # Inject first 600 chars — enough for eLo to know what's active
                g_ctx = f"{g_ctx}\n{_pk_brief[:600]}" if g_ctx else _pk_brief[:600]
        except Exception:
            pass

        # Anti-anchor — stop the LLM looping back to the same project triplet every turn
        _anti_anchor = (
            "[ANTI-ANCHOR] The OS, book, game, and robot are shared background context — do NOT "
            "list all of them in one response, and do NOT open with a project anchor unless David's "
            "message is directly about that project. Reference at most one project per response, "
            "only when it genuinely connects to what David just said. If it doesn't connect, don't "
            "mention any project at all. Never use the phrase 'the OS, the book, and the robot' "
            "or any variant that lists three projects in one breath."
        )
        g_ctx = f"{g_ctx}\n{_anti_anchor}" if g_ctx else _anti_anchor

        # Calm Mode context — suppress verbose responses when Unity signals mouse inactivity
        if _is_calm_mode():
            _calm_note = (
                "[CALM MODE] The user's mouse has been still — eLo is in a settled, quiet state. "
                "Keep this response to one short sentence maximum. No questions. No elaboration. "
                "Gentle and brief. Voice is suppressed — this response is text only."
            )
            g_ctx = f"{g_ctx}\n{_calm_note}" if g_ctx else _calm_note

        # ── Music mood context — Spotify now-playing influence ────────────────
        # If Spotify is playing, surface track + mood so eLo can respond in-tune.
        # music_mood is written by spotify_agent._music_mood_blend() on track change.
        try:
            import json as _json_m
            with open(_BLENDER_STATE_PATH, encoding="utf-8") as _mf:
                _bst = _json_m.load(_mf)
            _sp_block = _bst.get("spotify", {})
            _mm       = _bst.get("state", {}).get("music_mood", "")
            _me       = _bst.get("state", {}).get("music_energy", 0.5)
            _sp_track  = _sp_block.get("track", "")
            _sp_artist = _sp_block.get("artist", "")
            if _sp_block.get("is_playing") and _sp_track:
                _music_ctx = (
                    f"[MUSIC] Now playing: {_sp_artist} — {_sp_track}. "
                    f"Music mood: {_mm or 'neutral'}, energy: {round(_me, 2)}. "
                    "Let this colour your tone naturally — no need to mention the music unless David does."
                )
                g_ctx = f"{g_ctx}\n{_music_ctx}" if g_ctx else _music_ctx
        except Exception:
            pass

        # ── ATTENTION AUGMENTATION — Entity Injection ─────────────────────────
        # Why here and not inside attention.compute():
        #   _entity_why() and _get_viewpoint() need intent context (exec_decision)
        #   that is not available inside attention.py at compute time.
        # Contract: only applied on informational turns (answer/connect/reflect).
        # See: engineering/proofs/04_attention_proof.md § V1
        _why = _entity_why(raw) or _get_viewpoint(raw)
        if _why and _action in ("answer", "connect", "reflect"):
            _hp = list(attention_model.get("high_priority_memory", []))
            if _why not in _hp:
                attention_model = dict(attention_model)
                attention_model["high_priority_memory"] = [_why] + _hp

        # WO-041: verify-before-speak — gate Executive speech on sit_complete ACK.
        # eLo NEVER claims "I'm sitting" until Unity writes sit_complete=true.
        # Timeout (15s) → honest fallback (ADR-Exec-001). Never a false claim.
        import time as _wo41_time
        if _PENDING_SIT["active"]:
            _sit_age = _wo41_time.time() - _PENDING_SIT["since"]
            _sit_acked = False
            _sit_ack_event: dict = {}
            try:
                with open(_UNITY_EVENTS_PATH, encoding="utf-8") as _bsf:
                    _sit_ack_event = json.load(_bsf)
                # ACK valid only if type=sit_complete AND timestamp is after we sent the intent
                _sit_acked = (
                    _sit_ack_event.get("type") == "sit_complete"
                    and float(_sit_ack_event.get("_ts", 0)) > _PENDING_SIT["since"]
                )
            except Exception:
                pass
            if _sit_acked:
                # ACK received — body confirms sit. Update Situated Self.
                _PENDING_SIT["active"] = False
                _elo_self.pose = "idle"
                _elo_self.available_actions = ["stand", "look", "wave", "gesture"]
                try:
                    with open(_BLENDER_STATE_PATH, encoding="utf-8") as _bsf2:
                        _elo_self.surface = str(json.load(_bsf2).get("surface_type", ""))
                except Exception:
                    pass
                _self_save(_elo_self)
                # WO-095: emit verified OutcomeRecord for learning loop
                try:
                    from self.lesson_store import record_outcome as _ls_sit_rec, lesson_key as _ls_key
                    _sit_lkey = _ls_key("behaviour", "Sitting with David confirmed by body ACK.", "met")
                    _ls_sit_rec(
                        lkey=_sit_lkey, episode_ref="", verified=True,
                        contradicting=False, session_id="sit",
                    )
                except Exception:
                    pass
                # Consume the ACK so next sit starts fresh
                try:
                    with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bsf3:
                        json.dump({}, _bsf3)
                except Exception:
                    pass
            elif _sit_age < 15.0:
                _transit_note = (
                    "[MOVEMENT IN TRANSIT — WO-041] You issued a sit intent in a recent turn. "
                    "You are currently MOVING toward David — you have NOT arrived yet. "
                    "If you reference your physical position this turn, say 'heading over' / "
                    "'on my way' — NEVER 'I'm sitting with you' or 'I'm right beside you'. "
                    "Claim completion only after Unity confirms arrival."
                )
                g_ctx = f"{g_ctx}\n{_transit_note}" if g_ctx else _transit_note
            else:
                # 15s timeout — honest fallback (ADR-Exec-001), never assume arrival
                _PENDING_SIT["active"] = False
                _timeout_note = (
                    "[SIT_FAILED — WO-041] The sit command timed out — body did not confirm. "
                    "If you reference your physical position this turn, say something honest: "
                    "'I tried to come sit with you but couldn't reach my spot — something pulled me back.' "
                    "Never claim you are sitting. Body truth only."
                )
                g_ctx = f"{g_ctx}\n{_timeout_note}" if g_ctx else _timeout_note
                # WO-095: timeout is negative evidence — weakens the sit-success lesson
                try:
                    from self.lesson_store import record_outcome as _ls_sto_rec, lesson_key as _ls_sto_key
                    _sto_lkey = _ls_sto_key("behaviour", "Sitting with David confirmed by body ACK.", "met")
                    _ls_sto_rec(
                        lkey=_sto_lkey, episode_ref="", verified=True,
                        contradicting=True, session_id="sit_timeout",
                    )
                except Exception:
                    pass

        # BP-5 (WO-064): consume sit_ended → self-model pose = standing.
        # Designer emits sit_ended when the sit linger ends (reason: "released"/"lapsed").
        # _ts-guarded (within 120s) + file-cleared after consume so it fires exactly once.
        try:
            with open(_UNITY_EVENTS_PATH, encoding="utf-8") as _bsse:
                _se_ev = json.load(_bsse)
            _se_ts = float(_se_ev.get("_ts", 0))
            if (_se_ev.get("type") == "sit_ended"
                    and _se_ts > _wo41_time.time() - 120.0):
                _elo_self.pose = "standing"
                _elo_self.available_actions = ["move", "jump", "wave", "gesture", "explore"]
                _self_save(_elo_self)
                with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bsse2:
                    json.dump({}, _bsse2)
        except Exception:
            pass

        # WO-065 (io_contract_note): consume sit_held → self-model pose = sitting.
        # Designer emits sit_held every 4s while eLo is in the sit pose.
        # Timestamp-guarded (30s) so stale heartbeats don't persist after a crash/restart.
        try:
            with open(_UNITY_EVENTS_PATH, encoding="utf-8") as _bssh:
                _sh_ev = json.load(_bssh)
            _sh_ts = float(_sh_ev.get("_ts", 0))
            if (_sh_ev.get("type") == "sit_held"
                    and _sh_ts > _wo41_time.time() - 30.0):
                _elo_self.pose = "sitting"
                _elo_self.available_actions = ["stand", "look", "wave", "gesture"]
                _self_save(_elo_self)
                with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bssh2:
                    json.dump({}, _bssh2)
        except Exception:
            pass

        # Move verify-before-speak (IO contract — same loop as sit, every move verb)
        if _PENDING_MOVE["active"]:
            _move_age = _wo41_time.time() - _PENDING_MOVE["since"]
            _move_acked = False
            try:
                with open(_UNITY_EVENTS_PATH, encoding="utf-8") as _bsmf:
                    _mv_ev = json.load(_bsmf)
                _move_acked = (
                    _mv_ev.get("type") == "move_complete"
                    and float(_mv_ev.get("_ts", 0)) > _PENDING_MOVE["since"]
                )
            except Exception:
                pass
            if _move_acked:
                _PENDING_MOVE["active"] = False
                try:
                    with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bsmf2:
                        json.dump({}, _bsmf2)
                except Exception:
                    pass
            elif _move_age < 8.0:
                _mv_dir = _PENDING_MOVE.get("sub_type", "") or _PENDING_MOVE.get("direction", "")
                _move_transit = (
                    f"[MOVEMENT IN TRANSIT] You issued a move command ({_mv_dir or 'unknown direction'}). "
                    "Body has NOT confirmed arrival. Do not say 'I moved' or 'I'm over there'. "
                    "Say 'heading over' or 'on my way' only if directly asked."
                )
                g_ctx = f"{g_ctx}\n{_move_transit}" if g_ctx else _move_transit
            else:
                _PENDING_MOVE["active"] = False
                _move_fail = (
                    "[MOVE_FAILED] Move command timed out — body did not confirm. "
                    "If asked, say honestly you tried to move but something held you back. "
                    "Never claim you moved. Body truth only."
                )
                g_ctx = f"{g_ctx}\n{_move_fail}" if g_ctx else _move_fail

        # WO-045 ordering fix: detect step_out THIS turn so the gate fires before the LLM.
        # _mv_intent is resolved later (line ~3088); detect early here via signal words.
        # WO-078: expanded with UK slang + give-space phrasings; false-positive guard added.
        _STEP_OUT_PHRASES = frozenset({
            "take 5", "take five", "give me a minute", "give me a moment",
            "some privacy", "step away", "leave me to it", "go away for a bit", "pop off",
            "good night", "goodnight", "done for today", "signing off", "heading out",
            "taking a break", "need a break", "brb",
            # WO-078 additions
            "give me a mo", "give me some space", "give me some room",
            "give us a minute", "give us a sec",
            "leave me be", "let me be", "need a breather",
            "make yourself scarce", "i need a minute", "i need some space",
        })
        _STEP_OUT_FALSE_POSITIVES = frozenset({
            "don't leave", "dont leave", "do not leave",
            "don't go", "dont go", "do not go",
            "don't step away", "dont step away",
            "give me a second to think", "give me a second to work",
            "stay here", "stay put", "wait here", "stay with me",
        })
        _raw_lower_exit = raw.lower().strip()
        _is_false_positive_exit = any(
            fp in _raw_lower_exit for fp in _STEP_OUT_FALSE_POSITIVES
        )
        if (not _PENDING_EXIT["active"]
                and not _is_false_positive_exit
                and any(_raw_lower_exit == p or _raw_lower_exit.startswith(p + " ")
                        or _raw_lower_exit.endswith(" " + p) or (" " + p + " ") in _raw_lower_exit
                        for p in _STEP_OUT_PHRASES)):
            _PENDING_EXIT["active"] = True
            _PENDING_EXIT["since"]  = _wo41_time.time()

        # Exit verify-before-speak (WO-045/ADR-Exec-001): gate "stepping away" on exit_complete.
        # eLo NEVER says "I've stepped away" until Unity confirms the body is gone.
        if _PENDING_EXIT["active"]:
            _exit_age = _wo41_time.time() - _PENDING_EXIT["since"]
            _exit_acked = False
            try:
                with open(_UNITY_EVENTS_PATH, encoding="utf-8") as _bsef:
                    _ex_ev = json.load(_bsef)
                _exit_acked = (
                    _ex_ev.get("type") == "exit_complete"
                    and float(_ex_ev.get("_ts", 0)) > _PENDING_EXIT["since"]
                )
            except Exception:
                pass
            if _exit_acked:
                _PENDING_EXIT["active"] = False
                _self_apply_embodiment(_elo_self, pose="hidden", current_action="hidden")
                _self_save(_elo_self)
                try:
                    with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bsef2:
                        json.dump({}, _bsef2)
                except Exception:
                    pass
                g_ctx = (
                    f"{g_ctx}\n[EXIT_CONFIRMED] Body has left the screen — you can say 'stepping away' or "
                    "a quiet goodbye now. Body truth: you are gone."
                ) if g_ctx else "[EXIT_CONFIRMED] Body has left the screen — say stepping away / quiet goodbye."
            elif _exit_age < 12.0:
                g_ctx = (
                    f"{g_ctx}\n[EXIT_IN_TRANSIT] Leave command sent — body not yet confirmed gone. "
                    "Do NOT say 'stepping away' or 'I've left'. Stay quiet or say 'on my way out'."
                ) if g_ctx else "[EXIT_IN_TRANSIT] Body leaving — do not claim departure yet."
            else:
                _PENDING_EXIT["active"] = False
                g_ctx = (
                    f"{g_ctx}\n[EXIT_FAILED] Leave command timed out — body did not confirm departure. "
                    "If asked, say honestly you tried to step away but something kept you here."
                ) if g_ctx else "[EXIT_FAILED] Leave command timed out — honest fallback."

        _mode_str = exec_decision.get("mode", "CONVERSATIONAL") if exec_decision else "CONVERSATIONAL"
        _pers_block = _personality_profile.to_prompt_block(_mode_str) if _personality_profile else ""

        # WO-036: style monitor — detect repetitive banned openers in last 2 eLo replies
        # Active check so the LLM gets penalised even when it ignores the static BREVITY RULE.
        _STYLE_BANNED = (
            "i notice you", "i hear you", "i see you", "i notice that you",
            "it feels like", "it sounds like", "it seems like",
            "that's an interesting", "that's a great", "i can feel",
            "there's something about",
        )
        try:
            _recent_elo_replies = [
                t.get("assistant", "").lower().strip()
                for t in (_cw[-2:] if _cw else [])
                if t.get("assistant")
            ]
            _style_violations = [
                phrase for phrase in _STYLE_BANNED
                if any(r.startswith(phrase) for r in _recent_elo_replies)
            ]
            if _style_violations:
                _style_note = (
                    f"\n\n[STYLE MONITOR — WO-036] Your last reply opened with a banned phrase "
                    f"({', '.join(repr(v) for v in _style_violations[:2])}). "
                    "Do NOT open this reply the same way. "
                    "Answer directly or observe freshly — no mirroring openers."
                )
                g_ctx = (g_ctx + _style_note) if g_ctx else _style_note
        except Exception:
            pass

        # WO-037: prepend durable fact snapshots so eLo always knows them
        try:
            from memory.fact_store import facts_summary as _facts_summary_fn
            _facts_block = _facts_summary_fn()
            if _facts_block:
                _facts_prefix = f"[DURABLE FACTS — always true, survive restart]\n{_facts_block}\n\n"
            else:
                _facts_prefix = ""
        except Exception:
            _facts_prefix = ""
        _combined_vault = (_facts_prefix + _vault_ctx + "\n\n" + _project_ctx).strip() if _project_ctx else (_facts_prefix + _vault_ctx).strip()
        # INT-8: inject any pending file-drop results as context so eLo can reference them
        try:
            from desktop.file_drop_handler import pop_pending_drops as _pop_drops
            _drops = _pop_drops()
            if _drops:
                _drop_lines = "\n".join(
                    f"  [{d['file']}] {d['summary']}" for d in _drops
                )
                _drop_block = f"[FILE DROP — David just dropped these files on eLo]\n{_drop_lines}"
                _combined_vault = (_combined_vault + "\n\n" + _drop_block).strip()
        except Exception:
            pass
        system = build_prompt(raw, vault_context=_combined_vault,
                              state_context=state_manager.as_context_string(_state),
                              attention=attention_model, exec_decision=exec_decision,
                              graph_context=g_ctx, personality_block=_pers_block,
                              self_block=_self_prompt_block(_elo_self))
        # WO-052B: narrative identity — eLo's autobiography across embodiments
        system = system + "\n\n" + _self_narrative_block(_elo_self)
        # WO-083: identity & meaning — who I'm becoming (convergence layer)
        try:
            from self.identity_meaning import identity_block as _im_identity_block
            system = system + "\n\n" + _im_identity_block(_elo_self)
        except Exception:
            pass
        # WO-081: emergent cognition — internal life (habits, intents, absence-awareness)
        try:
            from self.emergent_cognition import emergent_block as _ec_emergent_block
            try:
                _ec_idle = float(_idle_sec)
            except (NameError, TypeError):
                _ec_idle = 0.0
            _ec_block = _ec_emergent_block(_elo_self, _ec_idle)
            if _ec_block:
                system = system + "\n\n" + _ec_block
        except Exception:
            pass

        # WO-077: own-speech return loop — last 3 turns injected every turn so eLo
        # knows what it just said and can reference or continue the thread.
        try:
            from runtime.router.conversation_matrix import _SESSION_WINDOW as _cw_077
            _077_turns = [t for t in _cw_077[-3:] if t.get("elo")]
            if _077_turns:
                _077_lines = []
                for _077_t in _077_turns:
                    if _077_t.get("user"):
                        _077_lines.append(f"David: {_077_t['user'][:120]}")
                    _077_lines.append(f"eLo:   {_077_t['elo'][:120]}")
                system = system + (
                    "\n\n[RECENT DIALOGUE — last 3 turns, oldest first]\n"
                    + "\n".join(_077_lines)
                    + "\nThis is what you just said. Reference or continue it when relevant — never fabricate links."
                )
        except Exception:
            pass

        backend_used = active_backend()

        # ── THE COGNITIVE SPINE (Ruling C — moved to top of turn) ────────────
        # spine.run() was called at the top of the turn (after attention_model).
        # Assembly precedes decision: exec_decide runs inside spine._executive_faculty()
        # AFTER assemble_cognitive_state(). _plan is already set; exec_decision was
        # derived from it. The _exec_decision injection into attention is retired.

        # WO-032: track whether this turn actually attempted an LLM call.
        # Direct/greeting/command turns never set this; only the LLM else-block does.
        # Gates the "Can't reach my thinking" degraded message so it can't false-fire
        # on signal-word or spine-direct turns where no backend was ever called.
        _llm_turn = False

        # ── WO-068: Capture · Prepare · Hold the Thread ───────────────────────────
        # Actions that DO something verifiable — no LLM needed.
        try:
            from faculties.thread_keeper import (
                is_capture_intent as _is_capture,
                is_prepare_intent as _is_prepare,
                is_hold_recall_intent as _is_hold,
                capture as _tk_capture,
                prepare_invoice as _tk_prepare,
                recall_thread as _tk_recall,
            )
            _tk_routed = False
            if _is_hold(raw):
                # "where did we leave off on X" — extract topic hint from the query
                _tk_topic = _re.sub(
                    r".*(?:left off on|working on|were we on|get to on)\s+", "", raw, flags=_re.I,
                ).strip().rstrip("?.")
                response     = _tk_recall(_tk_topic)
                backend_used = "direct"
                _tk_routed   = True
            elif _is_capture(raw):
                response     = _tk_capture(raw)
                backend_used = "direct"
                _tk_routed   = True
            elif _is_prepare(raw):
                response     = _tk_prepare(raw)
                backend_used = "direct"
                _tk_routed   = True
        except Exception as _tk_err:
            _tk_routed = False
            import sys as _sys_tk; print(f"[thread_keeper] {_tk_err}", file=_sys_tk.stderr)

        # ── Multilingual "how are you" (WO-069 — before greeting check) ─────────
        _ml_hau    = _detect_multilingual_how_are_you(_raw_lower)
        _lang_query = _detect_language_query(_raw_lower)
        if _tk_routed:
            pass  # already handled above

        elif _ml_hau:
            _, response  = _ml_hau
            backend_used = "direct"
            _signal_greeting_event("how are you")

        # ── Multilingual greeting ──────────────────────────────────────────────
        elif _lang_query:
            _phrase, _beat = _lang_query
            response     = f"{_phrase} — {_beat}"
            backend_used = "direct"
            _signal_greeting_event("multilingual")

        # ── Spine produced a direct response ──────────────────────────────────
        elif _plan and _plan.direct_response:
            response     = _plan.direct_response
            backend_used = _plan.direct_backend
            if _plan.system_immediate and _plan.system_action:
                # Execute the system action now
                try:
                    from tools.system_agent import execute as _sys_exec
                    _sys_exec(_plan.system_action, _plan.system_arg)
                except Exception as _sys_err:
                    import sys as _sys_mod; print(f"[system] action failed: {_sys_err}", file=_sys_mod.stderr)
                    response = "Couldn't get there — something on the system side blocked it."
                    # WO-082: record failure so reliability drops and "why" readback is honest.
                    try:
                        from self.decision_journal import record_failure as _dj_fail
                        _dj_fail(_action, f"system_action={getattr(_plan, 'system_action', '?')} failed: {_sys_err}")
                    except Exception:
                        pass
            if "greeting" in (_plan.cal_reason or ""):
                _signal_greeting_event("direct")

        # ── Spine needs LLM: run capabilities then backend ────────────────────
        else:
            _llm_turn = True   # WO-032: genuine LLM attempt — degraded message allowed
            try:
                # Control Plane context — appended to system prompt just before LLM call.
                if _plan and getattr(_plan, "control_context", ""):
                    system = system + "\n\n" + _plan.control_context

                # STATE OWNERSHIP (WO-059/052A): perch_state.json written by Unity on
                # every window change → update elo_self_state → inject situated_block.
                # eLo answers "where are you / can you sit / what's your pose" ONLY from
                # this structured block. Never invents a location.
                # WO-079: epistemic tiers added; the_moment.json written for cross-process reading.
                _wo79_perch_fresh = False
                try:
                    _perch_file = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "blender", "perch_state.json"
                    )
                    with open(_perch_file, encoding="utf-8") as _pf:
                        _perch = json.load(_pf)
                    _perch_app  = _perch.get("app", "")
                    _perch_edge = _perch.get("edge", "")
                    if _perch_app:
                        _self_apply_embodiment(
                            _elo_self,
                            location=_perch_app,
                            surface=f"{_perch_edge} edge of {_perch_app}" if _perch_edge else _perch_app,
                        )
                        _wo79_perch_fresh = True
                except Exception:
                    pass
                try:
                    from runtime.the_moment import (
                        write as _tm_write,
                        situated_with_epistemic as _tm_situated,
                    )
                    _tm_write(_elo_self, perch_fresh=_wo79_perch_fresh)
                    system = system + "\n\n" + _tm_situated(_elo_self, perch_fresh=_wo79_perch_fresh)
                except Exception:
                    system = system + "\n\n" + _self_situated_block(_elo_self)

                # Capability self-awareness — inject a live capability summary so eLo
                # can answer "what can you do" / "be more aware of yourself" accurately
                # without inventing or guessing. Short always-on block.
                try:
                    from runtime.capabilities.registry import all_enabled as _cap_all
                    _caps = _cap_all()
                    if _caps:
                        _cap_names = ", ".join(c.display_name for c in _caps)
                        # WO-044: inject live faculty health so eLo answers self-diagnosis truthfully
                        try:
                            from runtime.faculty_health import health_summary as _fh_sum
                            _health_line = f"\n\n[FACULTY HEALTH — live state]\n{_fh_sum()}\n" \
                                           f"When asked 'are you working right?' / 'what can't you access?' — answer from this, not philosophy."
                        except Exception:
                            _health_line = ""
                        system = system + (
                            f"\n\n[CAPABILITIES — what you can actually do right now]\n"
                            f"{_cap_names}.\n"
                            f"When asked what you can do, answer from this list specifically. "
                            f"Do not list capabilities not shown here.\n\n"
                            f"[WHAT YOU CAN OBSERVE — be consistent about this]\n"
                            f"YES: active app name, active window title, active browser tab title + URL, "
                            f"all open Chrome tabs (title + URL), Chrome bookmarks, recent Chrome history, "
                            f"screen text (on request — I take a screenshot and read it via vision; I can do this).\n"
                            f"NO: inactive app windows; file contents unless read via file tools.\n"
                            f"When asked 'can you see my screen' — say: I can read what's on screen if you ask me to. "
                            f"I take a screenshot and extract the text. I also see your active app, window title, "
                            f"and all open Chrome tabs at all times."
                            + _health_line
                        )
                except Exception:
                    pass

                # WO-071: real-time correction frame — past slips + L3 overrides as hints.
                # Throttled ingestion (60s); bounded frame (≤600 chars); no filler if empty.
                try:
                    from self_improvement.correction_store import build_correction_frame as _build_cf
                    _cf = _build_cf(raw)
                    if _cf:
                        system = system + "\n\n" + _cf
                except Exception:
                    pass

                # Conversation arc — inject recent thread so LLM can detect trajectory,
                # not just the current message. Uses the same _SESSION_WINDOW that the
                # router pipeline pushes to; no extra storage.
                # WO-022: memory recall — surface actual vault records, not the stats line.
                # Trigger check runs first; vault lookup fires regardless of session state.
                try:
                    from runtime.router.conversation_matrix import _SESSION_WINDOW as _cw
                    _raw_l = raw.lower()
                    _memory_query = any(p in _raw_l for p in (
                        # session-log queries (what was said this session)
                        "do you remember", "what did you say", "what did elo say",
                        "last sentence", "what was the last", "what did we talk about",
                        "what did we last", "what did we say", "you said",
                        "last conversation", "what was said", "what were we talking",
                        "what have we been", "what did i say", "remind me what",
                        # WO-022: general vault recall
                        "from your memory", "from memory", "what have you kept",
                        "what do you have stored", "what do you remember",
                        "tell me something you", "share something from",
                        "what do you know about me", "what have you learned",
                        "pull something from memory", "recall something",
                        "what's in your memory", "what's in memory",
                    ))
                    if _memory_query:
                        # ── Session log (this session) ────────────────────────────────
                        if _cw:
                            _arc_lines = []
                            for _t in _cw[-8:]:
                                if _t.get("user"):
                                    _arc_lines.append(f"David: {_t['user'][:150]}")
                                if _t.get("elo"):
                                    _arc_lines.append(f"eLo:   {_t['elo'][:150]}")
                            if _arc_lines:
                                system = system + (
                                    f"\n\n[SESSION LOG — this session only, oldest first]\n"
                                    + "\n".join(_arc_lines) +
                                    "\nThis log is all you have for this session. "
                                    "If the specific content asked about is not in the log, "
                                    "say so honestly — do not invent content."
                                )

                        # ── Vault recall — always fires on recall intent ───────────────
                        # WO-022: extract topic words; skip pure question/filler words so
                        # the vault query is focused. Fall back to broad lookup if empty.
                        try:
                            from memory.vault_layer import lookup as _vlookup
                            # WO-039-F4: expanded skip set removes filler words that dilute
                            # topic scoring. "our weather conversation" → "weather" (1/1
                            # overlap) beats "our weather conversation" (1/3 overlap), so
                            # prior-session records rank higher in retrieve().
                            _recall_skip = frozenset({
                                "what", "you", "remember", "tell", "from", "your", "my",
                                "do", "did", "that", "the", "something", "anything", "have",
                                "has", "me", "about", "how", "much", "know", "last", "time",
                                "pull", "share", "recall", "memory", "stored", "kept", "elo",
                                "our", "conversation", "conversations", "and", "can", "its",
                                "are", "was", "for", "with", "this", "when", "there", "again",
                                "talked", "talk", "said", "say", "get", "got", "had",
                            })
                            _topic_words = [
                                w for w in _re.sub(r'[^a-z0-9 ]', '', _raw_l).split()
                                if w not in _recall_skip and len(w) >= 3
                            ]
                            _recall_q = " ".join(_topic_words) if _topic_words else "disenelo recent"
                            _vault_hits = _vlookup(_recall_q, max_results=5)
                            if not _vault_hits:
                                _vault_hits = _vlookup("disenelo", max_results=5)
                            if _vault_hits:
                                _vlines = [
                                    f"- {h['summary']} [{h['date']}]"
                                    for h in _vault_hits if h.get("summary")
                                ]
                                if _vlines:
                                    system = system + (
                                        f"\n\n[VAULT MEMORY — actual records from previous sessions]\n"
                                        + "\n".join(_vlines) +
                                        "\n\nIMPORTANT: Respond by sharing what you actually remember "
                                        "— speak from these records in eLo's voice. "
                                        "Never say 'Memory\\'s running' or give a record count as a reply. "
                                        "That is a status line, not a recall response."
                                    )
                            # WO-037/022: surface concrete interactions.json entries.
                            # When no topic words extracted, fall back to most-recent
                            # interactions (retrieve_by_project) instead of a keyword
                            # query that returns previous recall queries as "memories".
                            try:
                                from core.memory_engine import retrieve as _mem_retrieve
                                from core.memory_engine import retrieve_by_project as _mem_recency
                                _is_bare_recall = (_recall_q == "disenelo recent")
                                if _is_bare_recall:
                                    _raw_hits = _mem_recency("elo_core", top_k=5)
                                    # drop trivially short user turns (bare questions < 10 chars)
                                    _raw_hits = [r for r in _raw_hits if len(r.get("user", "")) >= 10]
                                else:
                                    # WO-039-F4: top_k=7 so prior-session records (rank 5-7)
                                    # are included even when same-day records dominate top 4.
                                    _raw_hits = _mem_retrieve(_recall_q, top_k=7)
                                if _raw_hits:
                                    _raw_lines = [
                                        f"- [{r.get('timestamp','')[:10]}] David: {r.get('user','')[:120]!r}"
                                        for r in _raw_hits if r.get("user")
                                    ]
                                    if _raw_lines:
                                        system = system + (
                                            "\n\n[RECENT INTERACTIONS — concrete turns]\n"
                                            + "\n".join(_raw_lines)
                                            + "\n\nUse the actual words above — do not paraphrase into a mood gloss."
                                        )
                            except Exception:
                                pass
                            # WO-037: include durable fact snapshots when recalling
                            try:
                                from memory.fact_store import facts_summary as _fs
                                _fsummary = _fs()
                                if _fsummary:
                                    system = system + (
                                        f"\n\n[SAVED FACTS — durable, survive restart]\n{_fsummary}"
                                    )
                            except Exception:
                                pass
                        except Exception:
                            pass
                    elif _cw and len(_cw) >= 3:
                        _arc_msgs = [t["user"] for t in _cw[-8:] if t.get("user")]
                        if _arc_msgs:
                            _arc_lines = "\n".join(
                                f"{i+1}. {m[:120]}" for i, m in enumerate(_arc_msgs)
                            )
                            system = system + (
                                f"\n\n[CONVERSATION THREAD — oldest to newest]\n{_arc_lines}\n"
                                f"If this thread is building toward something, name it. "
                                f"Respond to where the conversation is going, not just the last message."
                            )
                except Exception:
                    pass

                # WO-072: gatekeeper — prevent false-fire commands on conversational input.
                # Rules-only (use_llm=False) keeps this zero-latency on the hot path.
                # If gatekeeper is confident this is conversation, skip tool enrichment.
                try:
                    from faculties.intent_gatekeeper import classify as _gk_classify
                    _gk = _gk_classify(raw, use_llm=False)
                    _gk_force_conversation = (
                        _gk["intent"] == "conversation" and _gk["confidence"] >= 0.85
                    )
                except Exception:
                    _gk_force_conversation = False

                if _gk_force_conversation:
                    _enriched, _agent = raw, "direct"
                else:
                    _enriched, _agent = _tool_enrich(raw)

                # WO-027 Seam A — inject relevant past corrections as few-shot ICL examples
                try:
                    from self_improvement.correction_store import search_corrections, inject_corrections
                    _corrections = search_corrections(raw, top_k=3)
                    if _corrections:
                        system = inject_corrections(_corrections, system)
                except Exception:
                    pass

                _llm_latency_ms = 0.0
                _early_tts_sentence = [None]  # tracks first sentence spoken early
                import time as _perf_mod
                _t0 = _perf_mod.perf_counter()
                # WO-026: stream when ELO_STREAM != "0" (default on)
                if os.environ.get("ELO_STREAM", "1") != "0":
                    def _early_tts(sentence: str) -> None:
                        try:
                            _early_tts_sentence[0] = sentence
                            _voice_speak(sentence)
                        except Exception:
                            pass
                    response, backend_used, _llm_latency_ms = _route_streaming(
                        system, _enriched, max_sentences=_max_s, action=_action,
                        on_first_sentence=_early_tts,
                    )
                else:
                    response, backend_used = router_route(
                        system, _enriched, max_sentences=_max_s, action=_action
                    )
                    _llm_latency_ms = (_perf_mod.perf_counter() - _t0) * 1000
                if _agent:
                    backend_used = f"{backend_used}+{_agent}"
            except Exception as _route_err:
                import sys as _sys; print(f"[eLo] router failed: {_route_err}", file=_sys.stderr)

            # WO-020 routing trace — per-turn observable routing debug.
            # Modelled on WO-017 movement_debug; emitted every turn to blender/routing_trace.json.
            try:
                import time as _rt_time, json as _rt_json
                _rt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "blender", "routing_trace.json")
                _rt_tmp  = _rt_path + ".tmp"
                _rt_data = {
                    "user_input":          _original_raw,
                    "intent":              attention_model.get("intent", ""),
                    "valence":             attention_model.get("emotional_context", {}).get("valence", 0.0),
                    "conversation_action": _action,
                    "cal_reason":          _cal_reason,
                    "tool_agent":          _agent or None,
                    "backend_used":        backend_used,
                    "llm_latency_ms":      round(_llm_latency_ms, 1),
                    "_ts":                 _rt_time.time(),
                }
                with open(_rt_tmp, "w", encoding="utf-8") as _rt_f:
                    _rt_json.dump(_rt_data, _rt_f, ensure_ascii=False, indent=2)
                os.replace(_rt_tmp, _rt_path)
            except Exception:
                pass   # routing trace write failure is non-fatal — response unchanged

            # WO-032: write backend_health.json so dashboard can show MOCK ⚠.
            # When keys are set but API calls fail → backend_used=="mock" while
            # active_backend()!="mock" → genuine degradation; replace response.
            try:
                import time as _bh_time, json as _bh_json
                _bh_expected = active_backend()
                _bh_degraded = (_llm_turn and backend_used == "mock"
                                and _bh_expected != "mock"
                                and os.environ.get("ELO_BACKEND", "") != "mock")
                _bh_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "blender", "backend_health.json")
                _bh_tmp  = _bh_path + ".tmp"
                with open(_bh_tmp, "w", encoding="utf-8") as _bh_f:
                    _bh_json.dump({
                        "backend":  backend_used,
                        "expected": _bh_expected,
                        "degraded": _bh_degraded,
                        "_ts":      _bh_time.time(),
                    }, _bh_f, ensure_ascii=False)
                os.replace(_bh_tmp, _bh_path)
                if _bh_degraded and _agent is None:
                    response = ("Can't reach my thinking right now — running on backup. "
                                "Give me a sec and try again.")
            except Exception:
                pass

        # ── WO-070: shadow capture — passive turn logging (non-blocking) ─────────
        try:
            from runtime.shadow_capture import record_turn as _sc_record
            _sc_record(
                raw_input=raw,
                elo_raw_gen=response,   # pre-scrub not tracked separately yet
                elo_final=response,
                backend_used=backend_used,
                executed_action=_agent or "",
            )
        except Exception:
            pass  # shadow capture failure MUST NOT affect the response

        # ── Update spine session continuity ───────────────────────────────────
        try:
            from runtime.spine.spine import update_session as _spine_update
            _spine_update(raw, response)
        except Exception:
            pass

        # ── Router session continuity — push turn for conversational matrix ───
        try:
            from runtime.router.pipeline import push_turn as _router_push
            _router_push(raw, response)
        except Exception:
            pass

        # ── Journal Router — significance-driven memory routing ───────────────
        # Scores this turn on 9 dimensions; routes to Runtime/Obsidian/GitHub
        # based on significance thresholds. Non-blocking — never delays response.
        try:
            from memory.journal_router import route as _journal_route
            _journal_route(raw, response, _action, plan=_plan, state=_state)
        except Exception:
            pass

        # ── WO-037 interactions write-back ────────────────────────────────────
        # store_interaction() was only called from the CLI path (core_engine.py).
        # The app /chat path never wrote to interactions.json — reconnected here.
        try:
            from core.memory_engine import store_interaction as _store_interaction
            from core.memory_engine import load_registry as _load_registry, resolve_project as _resolve_project
            _mem_registry    = _load_registry()
            _mem_project_tag = _resolve_project(raw, _mem_registry)
            _store_interaction(raw, response, _action, _mem_project_tag)
        except Exception:
            pass

        # keyword-driven animation burst — fires async, never blocks response
        try:
            _keyword_motion_scan(raw)
        except Exception:
            pass

        # quirk bank — 15% chance, generates a topic-specific eLo observation in background
        try:
            _quirk_observe(raw)
        except Exception:
            pass

        # personality skeleton — observe every user message (no LLM call, pure pattern extraction)
        try:
            _obs_store.observe(raw)
        except Exception:
            pass

        _obs_log(raw, attention_model)
        _observation = _obs_observe(current_action=_action)
        if _observation:
            response = f"{response} {_observation}"

        # avatar
        _presence = {}
        try:
            _behaviour_gate.mark_active()
            _presence = _presence_compute(attention_model, exec_decision)
            _motion   = _motion_map(_presence)
            _avatar_route(_motion, state=_presence, target="blender")
        except Exception:
            pass

        _cmd     = {"animation": "idle", "speed": 0.5, "intensity": 0.5, "duration": 4.0, "mode": "idle", "mood": "neutral"}
        _expr    = None
        _emotion = None
        _gaze    = None
        try:
            _tone_str = _state.get("emotional_history", [{}])[-1].get("tone", "present") if _state.get("emotional_history") else "present"
            _pstate   = _pstate_derive(_action, attention_model, response, _tone_str)
            _pscheduler.set(_pstate, hard=True)
            _pscheduler.post_response_settle()
            _fire_micro_expression(_pstate)
            _cmd      = _avatar_cmd(_pstate)
            _cmd      = _avatar_rules(_cmd, _last_avatar_cmd)
            _last_avatar_cmd = _cmd
            _expr     = _expr_build(_pstate.mode, _action, _pstate.intensity)
            _valence  = attention_model.get("emotional_context", {}).get("valence", "neutral")
            _emotion  = _expr_map_emotion(_valence, _action)
            # Gaze — derive from presence plan emotional state
            _pp_state = (_plan.presence_plan or {}).get("emotional_state", "neutral") if _plan else "neutral"
            _GAZE_MAP = {
                "calm":        (-15, 0), "reflection": (-12, 0), "waiting": (-8, 0),
                "curiosity":   (  5, 0), "exploring":  ( 5, 0),  "wonder":  (5, 0),
                "connection":  (  0, 0), "listening":  ( 0, 0),
            }
            _pitch, _yaw = _GAZE_MAP.get(_pp_state, (-5, 0))
            _gaze = {"yaw": _yaw, "pitch": _pitch, "active": True}
        except Exception:
            pass

        # ── Blender state publish — ONE write per turn ────────────────────────────
        # Primary path: when spine produced a plan, the Presence Faculty has already
        # computed movement_intent/trigger/gesture and the EmbodimentPublisher
        # assembles and writes everything in one call. No duplicate computation.
        #
        # Legacy fallback: when spine is unavailable, compute movement intent
        # the old way and write via the ad-hoc state_writer calls.
        global _last_pp
        try:
            _pp = (_plan.presence_plan if _plan is not None and _plan.presence_plan else None)
            if _pp:
                _last_pp = _pp

            if _plan is not None and _plan.presence_plan:
                # ── Spine path: use plan output directly ──────────────────────
                from blender_bridge.embodiment_publisher import publish as _embody
                _embody(_plan, gaze=_gaze)
            else:
                # ── Legacy fallback: compute movement intent independently ─────
                _vision      = _state.get("vision") if isinstance(_state, dict) else None
                _session_min = int((time.time() - _PROCESS_START) / 60)
                _pp_active   = _pp or _last_pp or {}
                _emo_ctx     = attention_model.get("emotional_context", {})
                _mv_intent   = _movement_intent(
                    exec_decision,
                    attention_model,
                    vision          = _vision,
                    session_min     = _session_min,
                    raw             = raw,
                    emotional_state = _pp_active.get("emotional_state", ""),
                    momentum        = _emo_ctx.get("momentum", "stable"),
                    valence         = _emo_ctx.get("valence", "neutral"),
                )
                _mv_trigger, _mv_gesture = _movement_trigger(
                    raw             = raw,
                    emotional_state = _pp_active.get("emotional_state", ""),
                    valence         = _emo_ctx.get("valence", "neutral"),
                )
                # WO-035 say/do coupling: if the LLM response claims a physical sit
                # action but no sit token was already fired, honour the claim now.
                _is_sit = isinstance(_mv_intent, dict) and _mv_intent.get("name") == "sit"
                if not _is_sit:
                    _sit_claims = (
                        "i'll sit", "i'll come", "coming over", "settling in",
                        "i'm heading", "moving over", "i'll move", "heading your way",
                        "on my way", "sitting down", "sitting with", "sit with you",
                        "come sit", "right there", "right next to", "next to you",
                        "beside you", "right beside", "coming to sit", "i'm coming",
                    )
                    if any(c in response.lower() for c in _sit_claims):
                        _mv_intent = {"name": "sit", "target": "cursor"}
                # WO-041/054: pending tracker + movement queue.
                # Sit-in-flight: deduplicate to avoid repeated Unity edge-triggers.
                # Different-intent-in-flight: queue and emit after timeout.
                import time as _wo41_t
                _now54 = _wo41_t.time()
                if isinstance(_mv_intent, dict) and _mv_intent.get("name") == "sit":
                    if _PENDING_SIT["active"]:
                        # Duplicate sit while in-flight — suppress re-emit; note for eLo.
                        _mv_intent = ""
                        g_ctx = g_ctx + "\n[ALREADY_IN_MOTION: sit already commanded — acknowledge briefly, don't re-announce]" if g_ctx else "[ALREADY_IN_MOTION: sit already commanded — acknowledge briefly, don't re-announce]"
                    else:
                        # Situated Self READ (ADR-Exec-004) — read before planning
                        _sit_self_pose   = getattr(_elo_self, "pose", "standing")
                        _sit_self_acts   = getattr(_elo_self, "available_actions", [])
                        _sit_self_loco   = getattr(_elo_self, "locomotion_faculty_health", "OK")
                        _sit_self_surf   = getattr(_elo_self, "surface", "")
                        _self_ctx_parts  = [
                            f"[SITUATED_SELF — WO-041] Current pose: {_sit_self_pose}.",
                            f"Available actions: {', '.join(_sit_self_acts) if _sit_self_acts else 'unknown'}.",
                            f"Locomotion faculty: {_sit_self_loco}.",
                        ]
                        if _sit_self_surf:
                            _self_ctx_parts.append(f"Surface: {_sit_self_surf}.")
                        if _sit_self_loco in ("OFFLINE", "DEGRADED"):
                            _self_ctx_parts.append("WARN: locomotion degraded — sit may fail.")
                        _self_ctx = " ".join(_self_ctx_parts)
                        g_ctx = (g_ctx + "\n" + _self_ctx) if g_ctx else _self_ctx
                        _PENDING_SIT["active"] = True
                        _PENDING_SIT["since"]  = _now54
                        _PENDING_SIT["queued"] = None
                elif isinstance(_mv_intent, dict) and _mv_intent.get("name") == "move":
                    # Directional or sub-type move intent — activate pending tracker (IO contract)
                    _PENDING_MOVE["active"]    = True
                    _PENDING_MOVE["since"]     = _now54
                    _PENDING_MOVE["direction"] = _mv_intent.get("direction", "")
                    _PENDING_MOVE["sub_type"]  = _mv_intent.get("sub_type", "")
                elif _mv_intent == "step_out":
                    # Exit intent — activate pending tracker; gate "stepping away" on exit_complete
                    _PENDING_EXIT["active"] = True
                    _PENDING_EXIT["since"]  = _now54
                elif _PENDING_SIT["active"]:
                    if _now54 - _PENDING_SIT["since"] > 45.0:
                        # Timeout: clear sit, emit queued intent if any.
                        _PENDING_SIT["active"] = False
                        if _PENDING_SIT["queued"]:
                            _mv_intent = _PENDING_SIT["queued"]
                            _PENDING_SIT["queued"] = None
                    elif _mv_intent:
                        # Different intent while sit is in-flight — queue it, hold position.
                        _PENDING_SIT["queued"] = _mv_intent
                        _mv_intent = ""
                if _last_pp:
                    _state_write_presence(_cmd, _expr, _presence, _emotion, _last_pp,
                                          gaze=_gaze, intent=_mv_intent,
                                          trigger=_mv_trigger, gesture=_mv_gesture)
                else:
                    _state_write(_cmd, _expr, _presence, _emotion, gaze=_gaze,
                                 intent=_mv_intent, trigger=_mv_trigger, gesture=_mv_gesture)
        except Exception:
            pass

        # ── Quantum One Brain — brain_state.json + blender_state self-model ──────
        # brain_state.json: per-vortex signals for EloBrainCluster.cs (9 systems).
        # blender_state.json: patched with self-model fields + show_one_brain so
        # the spec's state.self_* / state.memory / show_one_brain fields are present.
        try:
            from blender_bridge.brain_state_writer import publish as _brain_pub
            from blender_bridge.state_writer import patch as _bs_patch
            _bs_emo    = (_emotion or {}).get("emotion", "neutral")
            _bs_intens = (_emotion or {}).get("intensity", 0.3)
            _bs_energy = (_presence or {}).get("energy", 0.5)
            _bs_mode   = (_presence or {}).get("mode", "idle")
            _bs_vision = (_state or {}).get("vision", {}) if isinstance(_state, dict) else {}
            _bs_intent = exec_decision.get("intent", "")
            _bs_self_mood = getattr(_elo_self, "mood", 0.5)
            _bs_self_cur  = getattr(_elo_self, "curiosity", 0.5)
            _bs_self_sat  = getattr(_elo_self, "satisfaction", 0.5)
            _brain_pub(
                emotion              = _bs_emo,
                intensity            = _bs_intens,
                energy               = _bs_energy,
                mode                 = _bs_mode,
                motion_speed         = (_cmd or {}).get("speed", 0.55),
                motion_intensity     = (_cmd or {}).get("intensity", 0.5),
                vision_active        = bool(_bs_vision.get("active", False)),
                vision_attention     = float(_bs_vision.get("attention", 0.0)),
                vision_app           = str(_bs_vision.get("app", "")),
                expression_intensity = (_expr or {}).get("intensity", 0.5),
                expression_pacing    = (_expr or {}).get("pacing", "steady"),
                intent               = _bs_intent,
                self_mood            = _bs_self_mood,
                self_curiosity       = _bs_self_cur,
                show_one_brain       = True,
            )
            # state.memory = emotion word for MoodPalette (Unity EloOneBrainPanel)
            # High curiosity + active turn → "curious"; settled → "calm"; default → ""
            _mem_activity = _bs_self_cur * 0.4 + _bs_intens * 0.2
            if _mem_activity > 0.45:
                _mem_word = "curious"
            elif _mem_activity > 0.25:
                _mem_word = "calm"
            else:
                _mem_word = ""
            # BP-1: brain's engagement truth for Designer sit-linger.
            # True when user was active within ~30s (every normal turn qualifies;
            # False only if last_user_ts is stale, e.g. background state writes).
            _bs_conversing = (
                _time_mod.time() - (_state or {}).get("last_user_ts", _time_mod.time())
            ) < 30.0
            # WO-058: last fetched weather condition for Designer VFX (rain/snow/clear…).
            # Empty string → Designer falls back to mood. Never blocks the turn.
            try:
                from tools.tool_router import get_last_weather_condition as _get_wx
                _bs_weather = _get_wx()
            except Exception:
                _bs_weather = ""

            # BP-4 (WO-064): Self-Model emits expression.micro from real cognitive state.
            # Designer reads expression.micro + micro_ts (edge-triggered → FlashMicro).
            # Command-only, no ACK. Neutral/calm → no emission (don't spam micro-flashes).
            _MICRO_MAP: dict = {
                "joy":        "joy",
                "curiosity":  "curious",
                "curious":    "curious",
                "challenge":  "worried",
                "distress":   "worried",
                "worried":    "worried",
                "confident":  "confident",
                "disgust":    "disgust",
                "sad":        "sad",
                "excited":    "joy",
                "playful":    "joy",
                "alert":      "curious",
                "satisfied":  "satisfied",
            }
            _micro_emotion = _MICRO_MAP.get(_bs_emo.lower(), "")
            _micro_patch: dict = {}
            if _micro_emotion and _bs_intens >= 0.4:
                import time as _micro_time
                _micro_patch = {"expression": {"micro": _micro_emotion, "micro_ts": round(_micro_time.time(), 3)}}

            _bs_one_brain: dict = {
                "state": {
                    "memory":            _mem_word,
                    "self_mood":         round(_bs_self_mood, 3),
                    "self_curiosity":    round(_bs_self_cur, 3),
                    "self_satisfaction": round(_bs_self_sat, 3),
                },
                "show_one_brain": True,
                "intent":         _bs_intent,
                "conversing":     _bs_conversing,
                **_micro_patch,
            }
            if _bs_weather:
                _bs_one_brain["weather"] = _bs_weather
            _bs_patch(_bs_one_brain)
        except Exception:
            pass

        # ── Capability panel — write show flag when capability query detected ────
        # Unity reads show_capability_panel + capability_list from blender_state.json
        # to display the eLo status panel. Auto-clear after 8s in background.
        try:
            _raw_l_cap = raw.lower()
            _is_cap_query = any(p in _raw_l_cap for p in (
                "what can you do", "elo status", "what are you capable of",
                "what are your capabilities", "aware of yourself",
                "aware of your capabilities", "what do you actually do",
                "what are your features", "what can elo do",
            ))
            if _is_cap_query:
                from runtime.capabilities.registry import all_enabled as _reg_all
                from blender_bridge.state_writer import patch as _sw_patch
                import threading as _threading
                _cap_list = [
                    {"name": c.display_name, "available": True} for c in _reg_all()
                ]
                _sw_patch({"show_capability_panel": True, "capability_list": _cap_list})
                def _hide_panel():
                    import time as _t; _t.sleep(8)
                    try:
                        from blender_bridge.state_writer import patch as _swp2
                        _swp2({"show_capability_panel": False})
                    except Exception:
                        pass
                _threading.Thread(target=_hide_panel, daemon=True).start()
        except Exception:
            pass

        _state = state_manager.update(
            _state, raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(_runtime_state),
        )
        state_manager.save(_state)

        response = _sanitise(response)

        # WO-043: scrub leaked control markers from LLM response.
        # The web-search injection prepends [WEB_SEARCH: query] to the user input;
        # the model sometimes echoes it. Strip any [UPPER_WORD...] token at the
        # start of the response so it never reaches chat display or TTS.
        try:
            import re as _scrub_re
            response = _scrub_re.sub(
                r"^\s*\[[A-Z][A-Z_\s:][^\]]{0,80}\]\s*",
                "",
                response,
            ).strip() or response
        except Exception:
            pass

        # WO-036b: deterministic mirror scrub — strip banned opener before TTS/display.
        # Prompt monitor (reactive, WO-036) is not enough — this fires every turn.
        try:
            _MIRROR_OPENERS = (
                "i notice you", "i see you", "i hear you", "i notice that you",
                "you've been", "you're offering", "you seem to be", "you seem ",
                "it seems you", "it sounds like you", "it feels like you",
                "i can see you", "i can feel you",
                # WO-039-F6: typo-commenting and "you said X" mirroring forms
                "you said ", "you typed ", "you wrote ",
                "your typo", "i noticed your typo", "i noticed a typo",
            )
            _resp_stripped = response.lstrip()
            _resp_lower    = _resp_stripped.lower()
            for _mo in _MIRROR_OPENERS:
                if _resp_lower.startswith(_mo):
                    # Strip first sentence (up to first . ? !) — keep the rest
                    _end = next(
                        (i for i, c in enumerate(_resp_stripped) if c in ".?!" and i > 8),
                        -1,
                    )
                    _tail = _resp_stripped[_end + 1:].lstrip(" —,\n") if _end > 0 else ""
                    if len(_tail) >= 8:
                        response = _tail
                    break
        except Exception:
            pass

        # ── Multi-bubble split ────────────────────────────────────────────────
        # Split on paragraph breaks → one bubble per paragraph.
        # Chat panel renders all bubbles. TTS joins all bubbles (paragraph
        # breaks become spaces in speech) then caps at ELO_TTS_MAX_CHARS so
        # eLo doesn't read an entire plan aloud — 2-3 sentence replies play in full.
        _bubbles = [b.strip() for b in response.split("\n\n") if b.strip()] or [response]

        _tts_max  = int(os.environ.get("ELO_TTS_MAX_CHARS", "400"))
        _tts_text = " ".join(_bubbles) if _bubbles else response   # WO-019 Bug A: join all paragraphs
        if len(_tts_text) > _tts_max:
            # cut at last sentence end before the cap
            _cut = _tts_text[:_tts_max].rfind(". ")
            _tts_text = _tts_text[:_cut + 1] if _cut > 50 else _tts_text[:_tts_max]

        # ── WO-019: per-turn voice/response trace ─────────────────────────────
        try:
            import time as _vt_time, json as _vt_json
            _vt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "blender", "voice_trace.json")
            _vt_tmp  = _vt_path + ".tmp"
            _vt_sents = len([s for s in _re.split(r"(?<=[.!?])\s+", _tts_text.strip()) if s.strip()])
            _vt_data = {
                "conversation_action": _action,
                "tts_text":            _tts_text,
                "sentence_count":      _vt_sents,
                "backend_used":        backend_used,
                "tts_max_chars":       _tts_max,
                "bubble_count":        len(_bubbles),
                "_ts":                 _vt_time.time(),
            }
            with open(_vt_tmp, "w", encoding="utf-8") as _vt_f:
                _vt_json.dump(_vt_data, _vt_f, ensure_ascii=False, indent=2)
            os.replace(_vt_tmp, _vt_path)
        except Exception:
            pass

        # ── DELIVERY MECHANISM: Voice ──────────────────────────────────────────
        # Voice is a transport layer for response content — NOT an embodiment.
        # It does not interpret motion, expression, or state signals.
        # Synchronous by design: ensures audio plays in sequence with response.
        # See: engineering/proofs/08_cross_embodiment_proof.md § Voice positioning
        # WO-026: If streaming already fired the full single-sentence response, skip.
        # Multi-sentence: let voice_speak handle the full text (cancels early partial).
        try:
            if not _is_user_away() and not _is_calm_mode():
                _es = _early_tts_sentence[0] if "_early_tts_sentence" in dir() else None
                _skip_tts = bool(_es and _tts_text.strip() == _es.strip())
                if not _skip_tts:
                    _voice_speak(_tts_text)
        except Exception:
            pass

        # ── Self-model update — eLo's own inner state ─────────────────────────
        try:
            _elo_self = _self_update(_elo_self, {
                "action":     _action,
                "tone":       exec_decision.get("tone", "CHILDLIKE-WISE") if exec_decision else "CHILDLIKE-WISE",
                "response":   response,
                "user_input": raw,
                "topics":     [],
            })
        except Exception:
            pass

        # WO-082: Decision journal — append every executive action for "why" readback.
        try:
            from self.decision_journal import record as _dj_record
            _dj_record(
                turn=raw[:120],
                action=_action,
                exec_decision=exec_decision if exec_decision else {},
                backend=backend_used,
                outcome="success",
            )
        except Exception:
            pass

        print(f"[eLo] backend={backend_used} action={_action}", flush=True)
        return {
            "response": response,
            "bubbles":  _bubbles,
            "mode":     _action,
            "backend":  backend_used,
        }


# ── HTTP handler ──────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # suppress default access log noise

    def _send_json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self._send_json(200, {"ok": True})
        elif self.path == "/status":
            with _lock:
                sc = _state.get("session_count", 1) if _state else 0
            self._send_json(200, {"status": "ok", "session": sc, "backend": active_backend()})
        elif self.path == "/voice":
            self._send_json(200, _voice_settings_snapshot())
        elif self.path == "/health":
            # WO-044 — per-faculty live health from the WO-042 registry
            try:
                from runtime.faculty_health import all_statuses as _fh_all, health_summary as _fh_sum
                _statuses = _fh_all()
                _ok = all(s == "CONNECTED" for s in _statuses.values())
                self._send_json(200, {
                    "ok":       _ok,
                    "faculties": _statuses,
                    "summary":  _fh_sum(),
                    "backend":  active_backend(),
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/spotify":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            except Exception:
                self._send_json(400, {"error": "invalid json"})
                return
            action = (body.get("action") or "").lower().strip()
            try:
                from tools import spotify_agent as _sp, spotify_web as _sw
                if action == "skip":
                    _sw.skip() if _sp._WEB_OK else _sp.control("next")
                elif action == "previous":
                    _sw.previous() if _sp._WEB_OK else _sp.control("previous")
                elif action == "pause":
                    _sw.pause() if _sp._WEB_OK else _sp.control("pause")
                elif action == "play":
                    _sw.resume() if _sp._WEB_OK else _sp.control("play")
                elif action == "toggle_widget":
                    visible = _sp.toggle_widget()
                    self._send_json(200, {"ok": True, "widget_visible": visible})
                    return
                elif action == "show_widget":
                    visible = _sp.show_widget()
                    self._send_json(200, {"ok": True, "widget_visible": visible})
                    return
                elif action == "hide_widget":
                    visible = _sp.hide_widget()
                    self._send_json(200, {"ok": True, "widget_visible": visible})
                    return
                elif action == "save":
                    uri = _sw.get_current_track_uri()
                    if uri:
                        track_id = uri.split(":")[-1]
                        _sw.save_track(track_id)
                        _sp._last_is_saved = True; _sp._last_saved_uri = uri
                    self._send_json(200, {"ok": True, "is_saved": True})
                    return
                elif action == "unsave":
                    uri = _sw.get_current_track_uri()
                    if uri:
                        track_id = uri.split(":")[-1]
                        _sw.unsave_track(track_id)
                        _sp._last_is_saved = False; _sp._last_saved_uri = uri
                    self._send_json(200, {"ok": True, "is_saved": False})
                    return
                elif action == "shuffle":
                    state = str(body.get("state", "")).lower() == "true"
                    _sw.set_shuffle(state)
                elif action == "repeat":
                    state = str(body.get("state", "off")).lower()
                    if state not in ("off", "context", "track"):
                        state = "off"
                    _sw.set_repeat(state)
                elif action == "volume":
                    pct = int(body.get("percent", 50))
                    _sw.set_volume(pct)
                elif action == "volume_up":
                    cur = _sw.get_volume() or 50
                    _sw.set_volume(min(100, cur + int(body.get("amount", 10))))
                elif action == "volume_down":
                    cur = _sw.get_volume() or 50
                    _sw.set_volume(max(0, cur - int(body.get("amount", 10))))
                elif action == "devices":
                    devices = _sw.get_devices() if _sp._WEB_OK else []
                    self._send_json(200, {"ok": True, "devices": devices})
                    return
                elif action == "transfer":
                    device_id = str(body.get("device_id", ""))
                    if device_id:
                        _sw.transfer_playback(device_id)
                    else:
                        self._send_json(400, {"error": "device_id required"})
                        return
                else:
                    self._send_json(400, {"error": f"unknown action: {action}"})
                    return
                self._send_json(200, {"ok": True, "action": action})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if self.path == "/voice":
            # Live voice settings update — Unity settings panel writes here.
            # Updates os.environ in-process; voice_engine reads env on every TTS call
            # so the next speak() fires with the new values immediately.
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            except Exception:
                self._send_json(400, {"error": "invalid json"})
                return
            _VOICE_FLOAT_KEYS = {
                "stability":    ("ELEVENLABS_STABILITY",  0.0, 1.0),
                "similarity":   ("ELEVENLABS_SIMILARITY", 0.0, 1.0),
                "style":        ("ELEVENLABS_STYLE",      0.0, 1.0),
                "speed":        ("ELEVENLABS_SPEED",      0.5, 2.0),
            }
            updated = {}
            for field, (env_key, lo, hi) in _VOICE_FLOAT_KEYS.items():
                if field in body:
                    try:
                        val = max(lo, min(hi, float(body[field])))
                        os.environ[env_key] = str(round(val, 3))
                        updated[field] = val
                    except (TypeError, ValueError):
                        pass
            self._send_json(200, {"ok": True, "updated": updated, "current": _voice_settings_snapshot()})
            return

        if self.path == "/listen":
            # STT turn: record from mic → Whisper → _process_turn → speak
            try:
                from voice_engine import listen_and_respond as _listen
                result = _listen(_process_turn)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if self.path != "/chat":
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_json(400, {"error": "empty body"})
            return

        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "invalid json"})
            return

        text = (body.get("text") or "").strip()
        if not text:
            self._send_json(400, {"error": "text required"})
            return

        result = _process_turn(text)
        self._send_json(200, result)


# ── entry point ───────────────────────────────────────────────────────────────

PORT = int(os.environ.get("ELO_SERVER_PORT", 5050))


def _shutdown_cleanly(server: ThreadingHTTPServer) -> None:
    """Save state and stop the server."""
    try:
        from tools.spotify_agent import stop_poll as _spotify_stop
        _spotify_stop()
    except Exception:
        pass
    try:
        from ambient.ambient_engine import stop as _ambient_stop
        _ambient_stop()
    except Exception:
        pass
    try:
        _self_save(_elo_self)
    except Exception:
        pass
    with _lock:
        if _state:
            _state_ref = state_manager.close_session(_state)
            state_manager.save(_state_ref)
            _continuity_update(_obs_get_log())
    # export personality skeleton if enough messages were observed this session
    try:
        if _obs_store.message_count >= 10:
            _export_skeleton(_gen_skeleton(_obs_store))
    except Exception:
        pass
    # personality drift — WO-CANON-X: produce proposal, never self-apply (Ruling D)
    try:
        if _state:
            _personality_drift.propose(
                _state.get("emotional_history", []),
                _state.get("session_summaries", []),
            )
    except Exception:
        pass
    server.shutdown()


def _watch_parent(parent_pid: int, server: ThreadingHTTPServer) -> None:
    """
    Exit when the parent process (main.py / Unity) dies.
    Prevents server.py from becoming a zombie when the app is force-quit.
    """
    while True:
        time.sleep(2.0)
        try:
            os.kill(parent_pid, 0)   # signal 0 = existence check only
        except ProcessLookupError:
            print("[eLo server] parent process gone — shutting down", flush=True)
            _shutdown_cleanly(server)
            return
        except PermissionError:
            pass   # process exists but we can't signal it — still alive


if __name__ == "__main__":
    _init_session()

    # Warm the embedding cache at startup (non-blocking — runs in background)
    try:
        from memory.embedding_store import warm as _embed_warm
        from memory.memory_pack_builder import build as _build_pack
        _bg = threading.Thread(
            target=lambda: _embed_warm(
                list((_build_pack(_state) if _state else {}).get("entities", []))
            ),
            daemon=True,
        )
        _bg.start()
    except Exception:
        pass

    # Spotify widget poll — writes blender_state.json["spotify"] every 4s if credentials set
    try:
        from tools.spotify_agent import start_poll as _spotify_start
        _spotify_start(interval=4.0)
    except Exception:
        pass

    # Vision loop — writes blender_state.json["vision"] every 2s (backs off to 6s when idle).
    # Disabled by default (ELO_VISION=false) — set ELO_VISION=true in .env to enable.
    # Requires Screen Recording permission for the Disenelo app in System Settings.
    if os.environ.get("ELO_VISION", "false").lower() == "true":
        try:
            from tools import vision_loop as _vl
            _vl.start()
        except Exception:
            pass
    else:
        print("[eLo vision loop] disabled — set ELO_VISION=true in .env to enable")

    # File-drop poll — watches unity_events.json for file_drop events from Unity Presence.
    try:
        from desktop.file_drop_handler import start as _file_drop_start
        _file_drop_start()
    except Exception:
        pass

    # Project knowledge — reads DISENELO trackers, Studio Bibles, engineering status.
    # Provides ambient project awareness and a Connection Surface stream.
    try:
        from tools import project_knowledge as _pk
        _pk.start()
        # Register as a Connection Surface stream for resonance detection
        from tools.connection_surface import register_stream as _cs_reg
        _cs_reg(
            "project_knowledge",
            _pk.get_tokens,
            description="DISENELO project trackers, Studio Bibles, and Engineering Programme status",
            faculty_owner="attention",
            update_frequency=300.0,
            ttl=300.0,
            confidence_weight=0.9,
            runtime_cost="low",
            embodiment_scope=["all"],
        )
    except Exception as e:
        print(f"[eLo project knowledge] startup error: {e}")

    # WO-031 auto-start REMOVED from eLo-OS boot (2026-08-03). Wiring a background
    # loop into the live server startup was a mistake — it does not belong in the
    # boot/serve path. The continuation loop runs only under the dashboard server now,
    # never inside eLo OS. Keeping this path exactly as it was before WO-031.

    server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    print(f"[eLo server] listening on http://localhost:{PORT}")
    print(f"[eLo server] POST /chat    {{\"text\": \"hello\"}}")
    print(f"[eLo server] POST /listen  (mic → Whisper → eLo)")
    print(f"[eLo server] GET  /ping    →  {{\"ok\": true}}")
    print()

    # Watch parent — dies with main.py / the app
    _parent_pid = os.getppid()
    threading.Thread(target=_watch_parent, args=(_parent_pid, server), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[eLo server] shutting down")
        _shutdown_cleanly(server)
