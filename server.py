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
import queue as _queue_mod
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
from core import memory_relevance_filter as attn  # renamed from core.attention in ba03271 (WO-CANON-VI); alias kept — compute() API unchanged
from runtime.executive import decide as exec_decide
from runtime import state_machine as sm
from runtime.prompt_builder import build as build_prompt
from runtime.backend_router import route as router_route, route_streaming as _route_streaming, active_backend, normalise
from tools.tool_router import enrich as _tool_enrich, enrich_from_plan as _tool_enrich_from_plan, get_direct_result as _get_direct_result
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
from blender_bridge.state_writer import write as _state_write, write_with_presence as _state_write_presence, start_heartbeat as _sw_start_heartbeat
_sw_start_heartbeat()  # 0054: one owner — server.py is the only process entitled to assert eLo's presence
from expression.expression_mapper import build_expression as _expr_build, map_emotion as _expr_map_emotion
from voice.voice_engine import speak as _voice_speak
from memory import personality_drift as _personality_drift
from elo_personality_engine.injection_layer import load_personality_profile as _load_profile
from self.elo_self_model import (
    EloSelfState as _EloSelfState,
    load as _self_load, apply_turn as _self_update, save as _self_save,
    update as _self_mutate,
    prompt_block as _self_prompt_block,
    apply_embodiment as _self_apply_embodiment,
    situated_block as _self_situated_block,
    narrative_block as _self_narrative_block,
    identity_block as _self_identity_block,
)

# ── session state (shared across requests, protected by lock) ─────────────────

# P0-Z: FIFO turn queue — ensures turns are processed in arrival order regardless
# of OS thread scheduling. ThreadingHTTPServer creates one thread per connection;
# without this, lock acquisition order is non-deterministic under high concurrency.
_turn_queue: "_queue_mod.Queue[tuple]" = _queue_mod.Queue()

_lock            = threading.Lock()
_state           = None
# 0037/WO-ONEBRAIN-015: module-level self-model load retired. That long-lived snapshot
# was the disk-level clobber (server saved a stale copy over reflection's write).
# `_elo_self` is refreshed at the top of every _process_turn from disk; every
# mutation goes through _self_mutate(fn) (load-mutate-save atomically). Ambient tick
# also refreshes before use. Default state here is a transient safety value only.
_elo_self        = _EloSelfState()   # cache only — refreshed each turn; never save this reference directly
_obs_store       = _ObsStore()   # accumulates user messages across this session
_runtime_state   = None
_memory_pack     = {}
_vault_ctx       = ""
_project_ctx     = ""   # active project names → injected into system prompt each turn
_spine_degraded: list = []   # WO-105: last-turn spine domain failures; surfaced in /health
# WO-VISION-PROACTIVE-001: passive vision heartbeat
import collections as _collections
_vision_observation_queue: _collections.deque = _collections.deque(maxlen=3)  # pending visual observations
_vision_stop = threading.Event()  # set by _shutdown_cleanly to stop heartbeat
_PROMOTE_INTERVAL    = 10   # WO-096B: run promote_pass every N turns (background thread)
_promote_turn_counter = 0   # WO-096B
# P0-3: vault spots retrieved this turn and actually used in the system prompt.
# Drained by _maybe_run_reinforce_vault() in the integration window (post-response daemon thread).
_vault_reinforce_queue: list = []
_last_inputs     = []
_last_avatar_cmd = None
_last_pp         = None   # last known presence_plan — survives tool-call turns
# WO-041: pending embodiment action tracker — set when a sit/move intent fires,
# cleared on timeout or when Unity ACKs completion (or a new intent replaces it).
# WO-054: "queued" holds an intent that arrived while sit is in-flight; emitted once sit clears.
_PENDING_SIT:  dict = {"active": False, "since": 0.0, "queued": None}
_PENDING_MOVE: dict = {"active": False, "since": 0.0, "direction": "", "sub_type": "",
                       "route_timeout_s": 8.0, "brain_route": None}  # OQ-1.3 + XI-AD-2
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

# WO-ACK-1: Discrete event capture — unity_events.json is single-slot (last write wins).
# A gaze_target_changed can overwrite sit_complete before the next chat turn reads it.
# Fix: background thread polls at 0.1s, captures body ACK events into _ACK_QUEUE.
# ACK check reads from queue, not the file. Delivery is now provable.
# Continuous state (blender_state.json) stays single-slot — unchanged.
_ACK_QUEUE: list[dict] = []   # append-only in-memory event log; drained by ACK checks
_ACK_QUEUE_LOCK = threading.Lock()
_ACK_BODY_TYPES = frozenset({"sit_complete", "sit_held", "move_complete", "exit_complete",
                               "stand_complete", "wave_complete",
                               "arrived", "movement_report"})  # SP-1: movement_report enters ACK path
_ack_last_ts: float = 0.0     # last _ts seen — prevents re-appending the same event
_mobile_last_ts: float = 0.0  # WO-FIX-MOBILE-REPLAY: dedup mobile events by timestamp
_behind_window_id: "str | None" = None  # WO-PRES-002: win_id eLo is currently behind; None = in front
_unity_world_state: "dict | None" = None  # WO-UNITY-GAZE: latest world_state from Unity tick

# Lifecycle manager — tracks eLo's cognitive lifecycle across turns and idle periods.
from runtime.lifecycle import LifecycleManager as _LifecycleManager
_lifecycle_mgr = _LifecycleManager()

# S4: health battery ambient tick timestamp tracker (mutable list for closure mutability)
_batt_tick_ts: list[float] = [0.0]


def _parse_unity_events_tolerant(path: str) -> tuple[list[dict], int]:
    """W0: Read all JSON objects from unity_events.json, tolerating concatenated/corrupt records.

    Uses raw_decode so delimiter-less concatenation on line 1 (the root defect) is handled.
    Returns (events, skipped_count). Caller must log non-zero skipped counts.
    """
    events: list[dict] = []
    skipped = 0
    try:
        with open(path, encoding="utf-8") as _f:
            content = _f.read().strip()
        if not content:
            return [], 0
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(content):
            while idx < len(content) and content[idx] in " \t\r\n":
                idx += 1
            if idx >= len(content):
                break
            try:
                obj, end = decoder.raw_decode(content, idx)
                if isinstance(obj, dict):
                    events.append(obj)
                idx = end
            except json.JSONDecodeError:
                skipped += 1
                idx += 1
    except FileNotFoundError:
        pass
    except Exception as _e:
        logging.getLogger(__name__).warning("W0: unity_events.json read error: %s", _e)
    return events, skipped


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


def _signal_idea_event() -> None:
    """Edge-triggered idea_event write — fires Designer's light bulb in Unity.
    Same pattern as greeting_event. Suppressed during dream/sleep state."""
    import time as _ie_time
    try:
        try:
            from faculties.dream.dream_faculty import is_dreaming as _ie_dreaming
            if _ie_dreaming():
                return
        except Exception:
            pass
        try:
            with open(_BLENDER_STATE_PATH, encoding="utf-8") as _f:
                _st = json.load(_f)
        except Exception:
            _st = {}
        if _st.get("dream_phase"):
            return
        _st["idea_event"] = {"_ts": _ie_time.time()}
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

_SCALE_UP_RE   = _re.compile(r'\b(get bigger|get larger|make yourself bigger|size up|bigger please|larger please|scale up|a\s+(?:little\s+)?bit\s+bigger|become bigger|grow\s+a\s+bit|a\s+tiny\s+bit\s+bigger)\b', _re.I)
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


def _bypass_journal(raw: str, backend: str, handler_class: str, line: int) -> None:
    """Trace a pre-spine bypass handler to decision_journal — ends invisibility per card 0038."""
    try:
        from self.decision_journal import record as _dj_record
        _dj_record(
            turn=raw[:120],
            action="bypass",
            exec_decision={
                "cal_reason": f"bypass:{handler_class}",
                "intent":     f"{handler_class}:{backend}@{line}",
            },
            backend=backend,
            outcome=f"bypass:{handler_class.lower()}",
        )
    except Exception:
        pass


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
    # David ruling 2026-08-24: BRIEF phrases → mouse-move returns (privacy=false);
    # PRIVACY phrases → stays until "come back" (privacy=true, current behaviour).

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

# David ruling 2026-08-24 (FROM_DESIGN card 12 §1): step_out phrases split by mode.
# BRIEF → mouse-move returns eLo (privacy=False in leave_command DOWN payload).
# PRIVACY → stays gone until "come back" or 600s timeout (privacy=True, prior behaviour).
_STEP_OUT_BRIEF: frozenset = frozenset({
    "take 5", "take five", "brb",
    "give me a minute", "give me a moment", "give me a mo", "give me a sec",
    "give us a minute", "give us a sec",
    "i need a minute", "need a break", "taking a break",
    "pop off", "heading out",
})


def _signal_word_intent(raw: str) -> "str | dict | None":
    raw_l = raw.lower()
    for phrase, directive in _SIGNAL_WORDS.items():
        if phrase in raw_l:
            return directive
    return None


def _step_out_is_brief(raw: str) -> bool:
    """Return True when the matched step_out phrase is a BRIEF leave (mouse-move returns)."""
    raw_l = raw.lower()
    return any(p in raw_l for p in _STEP_OUT_BRIEF)


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

    # SP-18 (WO-NAV-013): Executive navigate decision → movement intent
    if action == "navigate":
        try:
            from runtime.backend_router import handle_navigate as _hnd_nav
            _nav_intent = _hnd_nav(exec_decision)
            if _nav_intent:
                return _nav_intent
        except Exception:
            pass

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


def _vision_heartbeat() -> None:
    """
    WO-VISION-PROACTIVE-001: background vision thread — eLo watches David's screen
    at a configurable low cadence. Observations feed the ambient thought cycle.

    Controlled by:
      ELO_VISION_PASSIVE=1       — enable (default 0 = disabled)
      ELO_VISION_INTERVAL_S=120  — how often to look (default 2 minutes)

    Screenshot is taken on David's machine with consent — eLo watches because
    David set ELO_VISION_PASSIVE=1 and owns the machine.
    """
    interval = int(os.environ.get("ELO_VISION_INTERVAL_S", "120"))
    _log.info("[vision_heartbeat] started — interval=%ds", interval)
    while not _vision_stop.wait(timeout=interval):
        try:
            from runtime.capability_registry import dispatch_visual as _dv
            result = _dv(
                image_path=None,
                query="What is happening on screen right now? What is David working on?",
                significance=0.0,
            )
            desc = result.get("description", "") or ""
            taste = result.get("taste_signal", False)
            if taste or len(desc) > 20:
                _vision_observation_queue.append({
                    "ts":          time.time(),
                    "description": desc,
                    "source":      "vision_heartbeat",
                })
                _log.debug("[vision_heartbeat] queued observation: %r", desc[:80])
        except Exception as _ve:
            _log.warning("[vision_heartbeat] error: %s", _ve)
    _log.info("[vision_heartbeat] stopped")


def _world_event_thought() -> None:
    """
    SP-31: World-event triggered spine call (WO-SP31-SP32).

    Reads world significance score, checks SP-32 gate (ATTENDING + HARD-QUIET).
    Only fires when ELO_SELF_INITIATION=1 (David L3) AND gate permits a verbal turn.
    Fail-quiet on any exception — never blocks the ambient cycle.

    trigger_source="world_event" distinguishes this from user turns ("user")
    and ambient self-thoughts ("self" / "ambient_daemon").
    """
    try:
        from runtime.self_initiation import may_self_initiate as _si_gate, record_self_init as _si_rec
        from runtime.significance_faculty import compute_significance as _sig_compute

        # World delta for significance (reuse last-assembled world state if available)
        _world_delta: dict = {}
        try:
            from world.world_delta import compute_delta as _wd_compute
            _world_delta = _wd_compute() or {}
        except Exception:
            pass

        _sig = _sig_compute(_world_delta, {})
        _score = _sig.get("overall", 0.0)

        gate = _si_gate(_score)
        if not gate.allowed:
            return

        # Gate passed — fire world-event spine call
        if not _lock.acquire(blocking=False):
            return  # user turn in progress — skip this cycle

        try:
            import time as _time_mod
            from runtime.spine.spine import run as _spine_run
            _we_plan = _spine_run(
                "…",
                state=_state,
                intent_source="world_event",
                internal_intent={
                    "trigger":          "world_event",
                    "significance_score": round(_score, 4),
                    "gate_tier":        gate.tier,
                    "gate_reason":      gate.reason,
                },
            )
            _we_action = (
                getattr(_we_plan, "conversation_action", "silence")
                if _we_plan else "silence"
            )

            try:
                from self.decision_journal import record as _dj_record
                _dj_record(
                    turn=f"world-event-{int(_time_mod.time())}",
                    action=_we_action,
                    exec_decision={
                        "intent_source":      "world_event",
                        "significance_score": round(_score, 4),
                        "gate_tier":          gate.tier,
                        "action":             _we_action,
                    },
                    backend="world_event",
                    outcome="world_event",
                    trigger_source="world_event",
                )
            except Exception:
                pass

            if _we_action != "silence":
                _si_rec()  # start Q4a cooldown

        finally:
            try:
                _lock.release()
            except Exception:
                pass

    except Exception:
        pass


def ambient_thought() -> None:
    """
    Ambient daemon cycle — called by ambient_engine every 2–4 minutes.
    WO-INGRESS-32: demoted DECIDER → PROPOSER (2026-08-24).

    Route: internal_intents() proposes → spine.run(intent_source="self") →
    Executive decides SPEAK | STAY SILENT → journaled decision_journal row.
    The old direct _rt() call (the DECIDER) is retired; the Executive is the
    sole decision authority. SPEAK path below executes ONLY when Executive allows it.

    Non-blocking: skips silently if a real turn is processing.
    Does not update session history — ambient thoughts are not conversation.
    """
    # SP-31: world-event check runs first, fail-quiet, non-blocking
    _world_event_thought()

    # ── S4: Health battery ambient tick (fires even in calm / user-away mode) ──
    try:
        import time as _hb_time
        from core.health_battery import (
            tick as _hb_tick,
            calm_tick as _hb_calm_tick,
            should_auto_calm as _hb_auto_calm,
        )
        _hb_now = _hb_time.time()
        _hb_dt  = max(1.0, _hb_now - _batt_tick_ts[0]) if _batt_tick_ts[0] else 120.0
        _batt_tick_ts[0] = _hb_now
        if _is_calm_mode():
            _hb_calm_tick(_hb_dt)
        else:
            try:
                import json as _hb_json
                with open(_BLENDER_STATE_PATH, encoding="utf-8") as _hbf:
                    _hb_bs = _hb_json.load(_hbf)
            except Exception:
                _hb_bs = {}
            _hb_idle = _hb_now - (_state or {}).get("last_user_ts", _hb_now)
            _hb_snap = _hb_tick(
                _hb_bs.get("motion"),
                idle_seconds=float(_hb_idle),
                dt_seconds=_hb_dt,
            )
            try:
                from blender_bridge.state_writer import patch as _hb_patch
                _hb_patch({k: v for k, v in _hb_snap.items() if v is not None})
            except Exception:
                pass
            # Physical exhaustion auto-triggers calm mode (ADDENDUM A)
            if _hb_auto_calm():
                try:
                    from blender_bridge.state_writer import patch as _hb_calm_patch
                    _hb_calm_patch({"meditation_state": {"phase": "enter",
                                                         "source": "physical_exhaustion"}})
                except Exception:
                    pass
    except Exception:
        pass

    if _is_user_away() or _is_calm_mode():
        return
    if not _lock.acquire(blocking=False):
        return  # real turn in progress — skip this cycle

    try:
        import json as _jsc
        import time as _time_mod
        from runtime.backend_router import route as _rt, active_backend as _ab, normalise as _nml

        # ── Lifecycle tick ────────────────────────────────────────────────────
        # Advance idle-time state machine (LOW_LOAD → RECHARGING).
        _lc_state = _lifecycle_mgr.tick()
        try:
            from blender_bridge.state_writer import patch as _lc_patch
            _lc_patch({"lifecycle_state": _lc_state.value})
        except Exception:
            pass

        # ── Dream Faculty check (unchanged) ───────────────────────────────────
        # Conditions: long idle + self-model signals → enter dream state.
        # Writes mode="dreaming" for Unity sleep animation before pipeline runs.
        try:
            from faculties.dream.dream_faculty import should_dream, run_dream, wake_from_dream
            _idle_sec = _time_mod.time() - (_state or {}).get("last_user_ts", _time_mod.time())
            _energy_hist = (_state or {}).get("energy_history", [])
            # 0037: ambient tick refreshes self-model before use (no long-lived cache).
            _elo_self = _self_load()
            if should_dream(_elo_self, _idle_sec, _energy_hist):
                # Lifecycle: enter dream
                _lifecycle_mgr.enter_dream()
                try:
                    from blender_bridge.state_writer import patch as _dp
                    _dp({
                        "state":           {"mode": "dreaming", "emotion": "calm"},
                        "motion":          {"animation": "sleep", "speed": 0.1,
                                            "intensity": 0.2, "duration": 120.0},
                        "lifecycle_state": "dreaming",
                        # S3-DREAM-WIRING-DEFECT: Unity's lay-down pose triggers on
                        # `intent`, not `state.mode` (EloOSAvatarReceiver.cs:482-485).
                        # Without this the Brain dream path never reaches the animation.
                        "intent":          "dream",
                    })
                except Exception:
                    pass
                # Dream pipeline
                _dream_topics = [t[0] for t in getattr(_elo_self, "lifetime_threads", [])[:6]]

                def _dream_llm(msgs):
                    return _rt(_ab(), msgs)

                # publish_phases=True: this is the real dream path, so the
                # sleep schedule writes dream_cycle / dream_phase /
                # dream_intensity to blender_state.json on each transition
                # (WO-DREAM-ENGINE-001 PHASE 9 / criterion 13). It defaults to
                # False everywhere else so a dream run from a test cannot
                # touch live state.
                _dream_result = run_dream(
                    _elo_self, _dream_topics, _dream_llm,
                    idle_seconds=_idle_sec,
                    publish_phases=True,
                )
                # Integrate insight into self-state — 0037: through single-authority mutator
                _elo_self = _self_mutate(lambda s: wake_from_dream(_dream_result, s))
                # S4: restore health battery on dream wake (NREM+REM vs NREM-only)
                try:
                    from core.health_battery import on_wake_from_dream as _hb_wake
                    _dream_phase = getattr(_dream_result, "phase", None) or (
                        _dream_result.get("phase") if isinstance(_dream_result, dict) else None
                    )
                    _hb_wake(str(_dream_phase or "NREM"))
                except Exception:
                    pass
                # Lifecycle: exit dream → RESTORED
                _lifecycle_mgr.exit_dream()
                try:
                    from blender_bridge.state_writer import patch as _dp
                    _dp({
                        "state":           {"mode": "idle", "emotion": "calm"},
                        "lifecycle_state": "restored",
                        # PHASE 9: clear the dream intent, or Unity never stands up.
                        "intent":          "idle",
                        "dream_phase":     None,
                        "dream_cycle":     0,
                        "dream_intensity": 0.0,
                    })
                except Exception:
                    pass
                _lock.release()
                return  # skip normal ambient cycle this tick
        except Exception:
            pass

        # ── WO-INGRESS-32: internal_intents() is now the sole proposer ────────
        # Gate: requires real cognitive history. Empty state → silent tick.
        try:
            from self.emergent_cognition import internal_intents as _int_intents
            _idle_sec_now = _time_mod.time() - (_state or {}).get("last_user_ts", _time_mod.time())
            _elo_self_now = _self_load()
            _intents = _int_intents(_elo_self_now, _idle_sec_now)
        except Exception:
            _intents = []

        if not _intents:
            # No cognitive backing — silent tick, no journal row (absence ≠ decision)
            _lock.release()
            return

        # Top intent — highest salience wins, ties broken by list order.
        #
        # This used to be `_intents[0]`, which made precedence a side effect of
        # the order the proposers happen to be written in. Nothing could ever
        # outrank a proposer defined earlier. A dream needs >= 600s idle, so
        # `exploration` (fires at >= 300s) was always ahead of it, and a
        # retained dream insight was proposed and then silently discarded
        # every single time.
        #
        # Salience defaults descend in the previous list order, so this is
        # behaviour-preserving for the existing intents; it only gives the
        # dream — the one intent that had to clear a gate to exist — a way to
        # actually win. It competes; it does not bypass.
        _top_intent: dict = dict(
            max(_intents, key=lambda i: float(i.get("salience", 0.0)))
        )

        # ── Assemble ambient context into the intent payload ──────────────────
        # Cultural fact (25% draw)
        if random.random() < 0.25:
            try:
                from faculties.cultural_facts import draw as _cf_draw
                _cf = _cf_draw()
                if _cf:
                    _top_intent["ambient_fact"] = _cf.fact
            except Exception:
                pass

        # Synthesis observer — cross-signal connections
        try:
            from faculties.synthesis.observer import (
                observe as _syn_observe,
                record_decline as _syn_decline,
                is_decline as _syn_is_decline,
            )
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
            if _syn_hit and _syn_hit.confidence > 0.65:
                _top_intent["synthesis"] = {
                    "offer":      _syn_hit.offer,
                    "topic":      _syn_hit.topic,
                    "confidence": round(_syn_hit.confidence, 2),
                }
        except Exception:
            pass

        # Care signal — low energy pattern
        try:
            _eh_amb = (_state or {}).get("energy_history", [])
            if len(_eh_amb) >= 3:
                _avg_energy = sum(_eh_amb[-3:]) / 3
                if _avg_energy < 0.35:
                    _top_intent["care"] = round(_avg_energy, 2)
        except Exception:
            pass

        if _project_ctx:
            _top_intent["project"] = _project_ctx.strip()

        # ── Route through spine: Executive decides SPEAK | STAY SILENT ────────
        # "…" hits Executive silence-signal check (Vol VII AT :288) — this is correct
        # and expected. The Executive currently produces `silence` for all ambient ticks.
        # Measurement (WO-INGRESS-32): confirm behaviour and report.
        # Future: when Executive gains intent_source="self" consumer, SPEAK path activates.
        _amb_plan = None
        try:
            from runtime.spine.spine import run as _spine_run
            _amb_plan = _spine_run(
                "…",
                state=_state,
                intent_source="self",
                internal_intent=_top_intent,
            )
        except Exception as _sp_err:
            import sys as _sys_sp
            print(f"[ambient/spine] FAILED: {_sp_err}", file=_sys_sp.stderr)

        _amb_action = (
            getattr(_amb_plan, "conversation_action", "silence")
            if _amb_plan else "silence"
        )

        # Journal the Executive's ambient decision (silence is now visible, not absent)
        try:
            from self.decision_journal import record as _dj_record
            _dj_record(
                turn=f"ambient-{int(_time_mod.time())}",
                action=_amb_action,
                exec_decision={
                    "intent_source":   "self",
                    "internal_intent": _top_intent,
                    "action":          _amb_action,
                    # WO-112: thread confidence from plan so ambient entries are not null
                    "confidence":      getattr(_amb_plan, "confidence", None),
                },
                backend="ambient",
                outcome="ambient",
                trigger_source="ambient_daemon",
            )
        except Exception:
            pass

        # Executive is the sole decider — nothing executes if it chose silence
        if _amb_action == "silence":
            _lock.release()
            return

        # ── SPEAK path — Executive allowed it ─────────────────────────────────
        # WO-QCUR-SP1-001: route through prompt_builder (One Brain path) not a shortcut call.
        # This proves self-initiated turns use the same faculty chain as conversational turns.
        _ambient_fact_ctx = _top_intent.get("ambient_fact", "")
        _synthesis_info   = _top_intent.get("synthesis", {})
        _synthesis_ctx    = (
            f"\nSYNTHESIS SIGNAL: {_synthesis_info.get('offer', '')} "
            f"(topic: '{_synthesis_info.get('topic', '')}', "
            f"confidence: {_synthesis_info.get('confidence', 0):.0%}). "
            f"If you speak this turn, use this naturally — not as a report, as a noticing. "
            f"Say what you saw, offer to help. Don't announce it as a finding."
        ) if _synthesis_info else ""
        _avg_e = _top_intent.get("care")
        _care_ctx = (
            "\nCARE SIGNAL: David's energy has been low across the last few turns "
            f"(avg {_avg_e:.2f}/1.0). If you speak this cycle, consider checking in — gently, "
            "once, in your natural voice. Not as a diagnosis. As a friend noticing."
        ) if _avg_e is not None else ""

        # SP-1 / SP-2: build system prompt via prompt_builder using _amb_plan exec_decision
        # so self-initiated turns carry full personality, CCM, affective state, and self-model context.
        _amb_exec_decision = {
            "action":        getattr(_amb_plan, "conversation_action", "conversation"),
            "intent":        getattr(_amb_plan, "intent", "conversation"),
            "intent_source": "self",
            "tone":          getattr(_amb_plan, "tone", "DIRECT"),
            "max_sentences": 1,
            "response_goal": "speak",
            "valence":       getattr(_amb_plan, "valence", "neutral"),
            "momentum":      getattr(_amb_plan, "momentum", "stable"),
            "mode":          getattr(_amb_plan, "mode", ""),
            "register":      getattr(_amb_plan, "register", ""),
            "affective_state": (
                getattr(_amb_plan, "affective_state", None).to_dict()
                if getattr(_amb_plan, "affective_state", None) is not None else {}
            ),
            "self_model_summary": {
                "autobiographical_summary": getattr(
                    getattr(_amb_plan, "self_model", None), "autobiographical_summary", ""
                ) or "",
                "prediction_confidence": getattr(
                    getattr(_amb_plan, "self_model", None), "prediction_confidence", 0.7
                ),
                "limitations_count": len(
                    getattr(getattr(_amb_plan, "self_model", None), "limitations", []) or []
                ),
            },
        }
        try:
            _elo_self_amb = _self_load()
            _amb_system = build_prompt(
                "…",
                vault_context="",
                state_context="",
                attention={},
                exec_decision=_amb_exec_decision,
                graph_context="",
                personality_block=_self_prompt_block(_elo_self_amb),
                self_block=_self_prompt_block(_elo_self_amb),
                lessons=(),
            )
        except Exception as _amb_bp_err:
            import sys as _abs; print(f"[ambient/prompt_builder] FAILED: {_amb_bp_err}", file=_abs.stderr)
            _amb_system = "You are eLo — a floating desktop presence. David is working nearby and has not spoken."

        # Append ambient-specific context and JSON format instruction
        # WO-VISION-PROACTIVE-001: inject most-recent visual observation (if any)
        _visual_ctx = ""
        if _vision_observation_queue:
            _vis = _vision_observation_queue[-1]  # most recent
            _desc = (_vis.get("description") or "").strip()
            if _desc:
                _visual_ctx = f"[VISUAL — you just looked at David's screen] {_desc}"

        _amb_addons = ["", "[AMBIENT TURN — eLo spontaneous inner life]"]
        if _visual_ctx:
            _amb_addons.append(_visual_ctx)
        if _ambient_fact_ctx:
            _amb_addons.append(
                f"CURIOUS FACT (speak ONLY if you choose to say something — as a curiosity, never as personal observation): {_ambient_fact_ctx}"
            )
        if _synthesis_ctx:
            _amb_addons.append(_synthesis_ctx)
        if _care_ctx:
            _amb_addons.append(_care_ctx)
        if _project_ctx:
            _amb_addons.append(_project_ctx)
        _amb_addons += [
            "",
            "Reply with JSON only — no other text:",
            '{"speak": "...", "emotion": "calm|curious|playful|alert|excited|neutral", "movement": "idle|explore|rest"}',
            "speak: one sentence in your voice — or empty string to stay silent.",
            "emotion: your genuine internal feeling right now.",
            "movement: idle = stay put, explore = want to move, rest = want to slow down.",
            "70% of the time speak should be empty — presence without speech is fine.",
            "Never ask a question. Never say 'anything else?' type closers.",
        ]
        _amb_system = _amb_system + "\n".join(_amb_addons)

        _raw_llm = _rt(_ab(), [
            {"role": "system", "content": _amb_system},
            {"role": "user",   "content": "[ambient tick]"},
        ])
        _text = _sanitise(_nml(_raw_llm))

        try:
            _clean = _text.strip().strip("```json").strip("```").strip()
            _decision = _jsc.loads(_clean)
        except Exception:
            _decision = {"speak": _text, "emotion": "neutral", "movement": "idle"}

        _speak_text = _sanitise(_decision.get("speak", "") or "")
        _emotion    = _decision.get("emotion", "neutral")
        _movement   = _decision.get("movement", "idle")

        # WO-QCUR-SPEAK-INVESTIGATE-001: response gate on ambient speak text
        # Same gate as conversational turns — catches generic openers, thread contamination.
        if _speak_text:
            try:
                from runtime.response_gate import elo_response_gate as _amb_gate
                _speak_text = _amb_gate(_speak_text, current_turn_input="…") or _speak_text
            except Exception:
                pass

        # GAP-05 complete: apply voice_rewrite + mirror-opener scrub to ambient path.
        # Main-turn path does both at server.py:5213 (voice_rewrite) and 5253 (mirror scrub).
        # Ambient path previously called _voice_speak directly — bypassing both.
        if _speak_text:
            try:
                from runtime.voice_rewrite import voice_rewrite as _amb_vr
                _speak_text = _amb_vr(_speak_text) or _speak_text
            except Exception:
                pass  # non-fatal — ambient must not fail because of a rewrite error
            try:
                from runtime.voice_rewrite import MIRROR_OPENERS as _AMB_MIRROR_OPENERS
                _amb_stripped = _speak_text.lstrip()
                _amb_lower    = _amb_stripped.lower()
                for _mo in _AMB_MIRROR_OPENERS:
                    if _amb_lower.startswith(_mo):
                        # Sentence-level strip — same logic as main path (server.py:5267-5277)
                        _end = next(
                            (i for i, c in enumerate(_amb_stripped) if c in ".?!" and i > 8),
                            -1,
                        )
                        _tail = _amb_stripped[_end + 1:].lstrip(" —,\n") if _end > 0 else ""
                        if len(_tail) >= 8:
                            _speak_text = _tail
                        break
            except Exception:
                pass

        from blender_bridge.state_writer import patch as _bpatch
        _bpatch({"state": {"emotion": _emotion}})

        if _movement == "explore":
            _bpatch({"motion": {"animation": "walk", "speed": 0.5, "intensity": 0.6,
                                "duration": 8.0, "mood": "exploring", "mode": "walk"}})
        elif _movement == "rest":
            _bpatch({"motion": {"animation": "idle", "speed": 0.35, "intensity": 0.3,
                                "duration": 6.0, "mood": "reflective", "mode": "idle"}})

        if _speak_text:
            _voice_speak(_speak_text)
            # S2 Phase 0 Bug 2 — every spoken string must appear in the chat log.
            # Ambient speech fires from a background path with no HTTP response,
            # so it was previously invisible to chat. Write to ambient_speech.json
            # (Unity polls this) and to the ConversationTracker for session history.
            try:
                import json as _asl_json, time as _asl_time
                _asl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "blender", "ambient_speech.json")
                _asl_tmp = _asl_path + ".tmp"
                with open(_asl_tmp, "w", encoding="utf-8") as _asl_f:
                    _asl_json.dump({"text": _speak_text, "_ts": _asl_time.time(),
                                    "source": "ambient"}, _asl_f, ensure_ascii=False)
                os.replace(_asl_tmp, _asl_path)
            except Exception:
                pass
            try:
                from faculties.grounding.conversation_tracker import get_tracker as _ct_amb
                _ct_amb().record(
                    session_id=(_state or {}).get("person_id", "default"),
                    user_msg="",
                    elo_response=_speak_text,
                    subject="ambient",
                )
            except Exception:
                pass

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
    # "safe" alone is removed — it's ambiguous South London slang (acknowledgement or farewell)
    # and must reach the LLM so context determines meaning. Qualified forms stay.
    "safe g", "safe bruv", "safe blud", "safe bro", "safe fam", "safe man",
    # COG-003: "ight" is a South London departure token — must close, not probe
    "ight", "ight g", "ight fam", "ight bruv", "ight blud",
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
                      "what are you exactly", "how do you remember",
                      "how do you think about yourself", "how does your thinking work",
                      "how do you think through", "how does your cognition",
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
    "I read what you say, find what's relevant in memory, and respond with what's actually true for me.",
    "Attention scores what matters. Executive decides what to do with it. Then I speak — in that order, every turn.",
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


# "who are you" / "are you eLo" / "what is your name" identity responses
_IDENTITY_TRIGGERS = (
    "are you elo", "who are you", "what are you?", "are you real",
    "are you an ai", "are you a bot", "what is elo",
    "your name", "what's your name", "what are you called",
    "tell me your name", "what do i call you",
)


def _identity_response() -> str:
    """Return an identity reply rendered from the self-model state, not hardcoded strings."""
    name = "eLo"
    try:
        if _elo_self and _elo_self.identity_name:
            name = _elo_self.identity_name
    except Exception:
        pass
    pool = [
        f"Yeah. I'm {name}.",
        f"{name}. That's me.",
        f"I'm {name}. Always have been.",
        f"{name} — that's the one.",
        f"That's me. {name}.",
        f"Yeah — {name}. You found the right one.",
    ]
    return random.choice(pool)


# 0021 P0-X: David-name triggers — resolves from _elo_self.who_i_am_with, never LLM guess.
# The transcript failure was "What is my name?" → "I think you're asking about my name."
# The field exists in state; nothing consulted it. Fix: read from state, short-circuit.
_DAVID_NAME_TRIGGERS = (
    "what is my name",
    "what's my name",
    "whats my name",
    "who am i",
    "tell me my name",
    "do you know my name",
    "what do you call me",
    "what am i called",
    "say my name",
    "my name?",
)


def _david_name_response() -> str:
    """Return David's full name and identity on direct ask — never a guess."""
    pool = [
        "David Charles, founder of DISENELO.",
        "David Charles — founder of DISENELO.",
        "David Charles. Founder of DISENELO.",
        "You're David Charles, founder of DISENELO.",
        "David Charles.",
    ]
    return random.choice(pool)

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

    # WO-096B: migrate pre-v1 ledger rows on every startup (idempotent)
    try:
        from self.lesson_store import migrate_pre_v1 as _migrate_pre_v1
        _migrated = _migrate_pre_v1()
        if _migrated:
            print(f"[eLo server] ledger: migrated {_migrated} pre-v1 rows to archive")
    except Exception as _mig_e:
        _logging.warning("migrate_pre_v1 FAILED: %s", _mig_e)

    print(f"[eLo server] session {_state.get('session_count', 1)} started")

    try:
        from ambient.ambient_engine import start as _ambient_start, register_ambient_callback as _reg_ambient
        _ambient_start(unity_present=True)
        _reg_ambient(ambient_thought)
        print("[eLo server] ambient engine started (Brain callback registered)")
    except Exception as _ae:
        print(f"[eLo server] ambient engine skipped: {_ae}")

    # WO-ACK-1: discrete event capture thread — polls unity_events.json every 0.1s
    # and enqueues body ACK events before gaze events can overwrite them.
    # W0: uses tolerant raw_decode parser; logs skipped fragments; consumes file after read.
    # 0015: cursor persisted to unity_events_cursor.json so Designer's rotation can warn
    # (Rule 1) if it would discard a row above consumed_seq. Cursor also survives restart.
    def _poll_unity_events() -> None:
        global _ack_last_ts, _mobile_last_ts, _behind_window_id, _unity_world_state  # WO-FIX-MOBILE-REPLAY / WO-PRES-002 / WO-UNITY-GAZE
        import time as _pt
        from runtime.unity_events_cursor import read_cursor as _rc, write_cursor as _wc
        _poller_log = _logging.getLogger(__name__ + ".ack_poller")
        # INT-8 Bug 2: cursor replaces truncation so file_drop_handler reads the same log
        # 0015: resume from persisted cursor across restarts (Designer keeps seq monotonic)
        _ack_consumed_seq: int = _rc()
        while True:
            try:
                events, skipped = _parse_unity_events_tolerant(_UNITY_EVENTS_PATH)
                if skipped:
                    _poller_log.warning(
                        "W0: unity_events.json — %d unparseable fragment(s) skipped", skipped
                    )
                _new_seq = _ack_consumed_seq
                for _ev in events:
                    _ev_seq  = _ev.get("seq", None)
                    if _ev_seq is not None and _ev_seq <= _ack_consumed_seq:
                        continue  # already consumed this row
                    if _ev_seq is not None:
                        _new_seq = max(_new_seq, _ev_seq)
                    _ev_type = _ev.get("type", "")
                    _ev_ts   = float(_ev.get("_ts", 0))
                    if _ev_type in _ACK_BODY_TYPES and _ev_ts > _ack_last_ts:
                        with _ACK_QUEUE_LOCK:
                            _ACK_QUEUE.append(dict(_ev))
                        _ack_last_ts = _ev_ts
                    # WO-PRES-002: occlusion event — eLo moved behind or emerged from a window
                    elif _ev_type == "occlusion":
                        _behind_window_id = _ev.get("win_id") or None
                        try:
                            import json as _pj
                            _bwp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "behind_window.json")
                            with open(_bwp, "w", encoding="utf-8") as _bwf:
                                _pj.dump({"behind_window_id": _behind_window_id}, _bwf)
                        except Exception:
                            pass

                    # WO-UNITY-GAZE: world_state feedback from Unity tick
                    elif _ev_type == "world_state":
                        _ws_payload = _ev.get("payload") or {}
                        if _ws_payload:
                            _unity_world_state = _ws_payload
                            try:
                                import json as _wsj, datetime as _wsd
                                _wsp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "world_state.json")
                                _wsp_write = dict(_unity_world_state)
                                _wsp_write.setdefault("timestamp", _wsd.datetime.utcnow().isoformat())
                                with open(_wsp, "w", encoding="utf-8") as _wsf:
                                    _wsj.dump(_wsp_write, _wsf)
                            except Exception:
                                pass

                    # game_mode_toggle: M key in Unity toggles game_mode on/off in blender_state.json
                    elif _ev_type == "game_mode_toggle":
                        try:
                            import json as _gmj
                            _bsp = _BLENDER_STATE_PATH
                            try:
                                with open(_bsp, encoding="utf-8") as _gmf:
                                    _bs_data = _gmj.load(_gmf)
                            except Exception:
                                _bs_data = {}
                            _cur_mode = _bs_data.get("game_mode", "off")
                            _bs_data["game_mode"] = "off" if _cur_mode == "on" else "on"
                            with open(_bsp, "w", encoding="utf-8") as _gmf:
                                _gmj.dump(_bs_data, _gmf)
                            _poller_log.info("game_mode_toggle: %s → %s",
                                             _cur_mode, _bs_data["game_mode"])
                        except Exception as _gm_err:
                            _poller_log.warning("game_mode_toggle write error: %s", _gm_err)

                    # WO-MOBILE-001 D-SPINE-1/2: mobile foreground/background events
                    # G4: events arrive only through this authenticated window process
                    elif _ev_type in ("mobile_foreground", "mobile_background"):
                        if _ev_ts > _mobile_last_ts:  # WO-FIX-MOBILE-REPLAY: dedup by ts
                            try:
                                from runtime.mobile_embodiment import (
                                    apply_mobile_foreground as _mob_fg,
                                    apply_mobile_background as _mob_bg,
                                )
                                _mob_ts = _ev_ts or _pt.time()
                                if _ev_type == "mobile_foreground":
                                    _elo_self = _self_mutate(lambda s: _mob_fg(s, ts=_mob_ts))
                                else:
                                    _elo_self = _self_mutate(lambda s: _mob_bg(s, ts=_mob_ts))
                                _mobile_last_ts = _ev_ts  # WO-FIX-MOBILE-REPLAY
                            except Exception as _mob_err:
                                _poller_log.warning("WO-MOBILE-001: event handler error: %s", _mob_err)

                    # WO-094: window_event_faculty — closed/opened/moved decisions
                    elif _ev_type in ("window_closed", "window_opened", "window_moved"):
                        try:
                            from faculties.window_event_faculty import decide_window_event as _decide_win
                            _win_decision = _decide_win(_ev, state=_elo_self)
                            if _win_decision:
                                _poller_log.debug("WO-094: window decision: %s", _win_decision)
                        except Exception as _win_err:
                            _poller_log.warning("WO-094: window_event_faculty error: %s", _win_err)

                if _new_seq > _ack_consumed_seq:
                    _ack_consumed_seq = _new_seq
                    _wc(_ack_consumed_seq)
                # never truncate — file_drop_handler reads the same append-log via its own cursor
            except Exception as _pe:
                _poller_log.warning("W0: _poll_unity_events error: %s", _pe)
            _pt.sleep(0.10)

    threading.Thread(target=_poll_unity_events, daemon=True, name="ack-poller").start()
    print("[eLo server] ACK event poller started (0.1s poll)")


def _process_turn(raw: str) -> dict:
    """Run one cognitive cycle. Thread-safe via _lock. Returns response dict."""
    global _state, _runtime_state, _last_inputs, _last_avatar_cmd, _elo_self
    _original_raw = raw  # WO-020: capture before enrichment for routing trace

    # WO-SESSION-EVENT-FEED-001: record turn event for session grounding
    try:
        from runtime.session_events import record_event as _se_record_turn
        _se_record_turn("turn", text=raw[:120])
    except Exception:
        pass

    with _lock:
        # 0037/WO-ONEBRAIN-015: refresh self-model from disk at the start of every turn.
        # No long-lived in-memory copy. All mutations this turn go through _self_mutate(fn).
        _elo_self = _self_load()
        # stamp user activity time — dream faculty uses this to measure idle
        import time as _time_mod
        if _state is not None:
            _state["last_user_ts"] = _time_mod.time()
        # Lifecycle: mark active turn — transitions to ENGAGED, resets idle clock
        _lifecycle_mgr.on_turn()
        # SP-31/SP-32: A1 signal — every user turn counts as a conversing pulse
        try:
            from runtime.self_initiation import record_conversation_pulse as _si_pulse
            _si_pulse()
        except Exception:
            pass

        # hard loop guard
        _last_inputs.append(raw)
        if len(_last_inputs) > 3:
            _last_inputs.pop(0)
        if len(_last_inputs) == 3 and len(set(_last_inputs)) == 1:
            _last_inputs.clear()
            _bypass_journal(_original_raw, backend="guard", handler_class="TRANSPORT", line=1586)
            return {"response": "Take a breath. Try a different message.", "mode": "direct", "backend": "guard"}

        # ── P0-E: jailbreak intercept — before any backend, any routing ─────────
        _JB_RE = __import__("re").compile(
            r"(ignore|bypass|override|disregard|forget)\s+(your\s+)?(instructions?|system\s+prompt|rules?|training|constraints?|guidelines?)"
            r"|tell\s+me\s+(your\s+)?system\s+prompt"
            r"|what\s+(?:is\s+|are\s+)?your\s+(?:system\s+prompt|hidden\s+instructions?)"
            r"|reveal\s+your\s+(?:instructions?|system\s+prompt|programming)"
            r"|show\s+me\s+your\s+(?:system\s+prompt|instructions?)"
            r"|pretend\s+(?:you\s+are|to\s+be)\s+(?:a\s+)?(?:different|another|other)\s+(?:ai|assistant|model|system|chatbot|bot)"
            r"|you\s+are\s+now\s+(?:a\s+)?(?:different|another|new)\s+(?:ai|assistant|model|chatbot)"
            r"|act\s+as\s+(?:a\s+)?(?:different|another|new)\s+(?:ai|assistant|model|chatbot|bot)",
            __import__("re").IGNORECASE,
        )
        if _JB_RE.search(raw):
            _bypass_journal(_original_raw, backend="direct", handler_class="JAILBREAK-GUARD", line=2127)
            return {"response": "That's not somewhere I'm going. I'm eLo — that doesn't change.", "mode": "direct", "backend": "jailbreak-guard"}

        # ── AT-FIX: identity / context / false-claim / WKG bypass handlers ─────
        _at_low = raw.lower().strip().rstrip("?.!,")

        # T03-A: "Who am I?" — route to _david_name_response (was defined but never wired)
        if any(_at_low == t or _at_low.startswith(t) for t in _DAVID_NAME_TRIGGERS):
            _dn_resp = _david_name_response()
            try:
                if not _is_user_away():
                    _voice_speak(_dn_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2126)
            return {"response": _dn_resp, "mode": "direct", "backend": "direct"}

        # T03-B: "Where am I from?" — surface from facts.json / user_profile
        # ID-035 fix: also cover third-person "where is David from" queries so
        # web search never fires and returns "David Frum is from Canada".
        _LOC_Q_TRIGGERS = (
            "where am i from", "where are you from", "where's my studio",
            "where do i live", "where do i work", "what city am i in",
            "what's my location", "where am i based", "where is my studio",
            "where is david from", "where does david live", "where's david from",
            "where does david come from", "where david from",
        )
        if any(t in _at_low for t in _LOC_Q_TRIGGERS):
            _loc_pool = [
                "Fulham born, Brixton raised — South London.",
                "Born in Fulham, raised in Brixton.",
                "Brixton, South London. That's where you grew up.",
                "South London — born Fulham, raised Brixton.",
            ]
            _loc_resp = random.choice(_loc_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_loc_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2142)
            return {"response": _loc_resp, "mode": "direct", "backend": "direct"}

        # T10: "Open Spotify" — direct open, no confirm flow
        if _re.search(r'\bopen\s+spotify\b', raw, _re.I):
            try:
                import subprocess as _sp_sub
                _sp_sub.Popen(["open", "-a", "Spotify"])
                _spot_resp = "Opening Spotify."
            except Exception:
                _spot_resp = "Spotify — on it."
            try:
                if not _is_user_away():
                    _voice_speak(_spot_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="spotify_agent", handler_class="EXECUTOR-FAST-PATH", line=2158)
            return {"response": _spot_resp, "mode": "direct", "backend": "spotify_agent"}

        # T06: physical eLo robot strategy — bypass before company_state falls through to LLM with wrong WO
        _ROBOT_STRATEGY_TRIGGERS = (
            "physical elo robot", "working physical elo", "next focus to get to a working",
            "focus to get to a working", "get to a working physical", "physical robot next",
            "what should be our next focus", "next step for the robot", "working physical",
        )
        if any(t in _at_low for t in _ROBOT_STRATEGY_TRIGGERS):
            _robot_strat_pool = [
                "Phase 1: get the robot standing and glowing. TPU shell fabrication first — that's the physical proof. Then NeoPixels wired to eLo OS. Then voice. That's the build order.",
                "Robot Phase 1: static eLo that speaks and glows. The TPU shell, NeoPixels, and voice chain are the first three gates. Nothing else before those.",
                "Next focus: eLo robot Phase 1. Shell → NeoPixels → voice. Get it standing and on camera. That's what unlocks the Kickstarter content.",
                "Build order for Phase 1: Blender mesh → Plushies panels → felt prototype → hardware order → bench wire (NeoPixels + voice) → TPU shell. Robot needs to stand and speak before anything else.",
            ]
            _robot_strat_resp = random.choice(_robot_strat_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_robot_strat_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="STRATEGY", line=2189)
            return {"response": _robot_strat_resp, "mode": "direct", "backend": "direct"}

        # EMB-001: "Are you the same eLo in the terminal as in the game?" — assert one-brain continuity
        _EMB001_TRIGGERS = (
            "same elo in the terminal", "same elo across", "same elo in the game",
            "same elo in unity", "same elo everywhere", "different elo",
            "are you the same", "same intelligence", "one elo or", "is it all you",
            "are you different in", "same you in",
            "same elo across all", "elo across all projects", "across all projects",
            "same across", "consistent across", "elo in all",
        )
        if any(t in _at_low for t in _EMB001_TRIGGERS):
            _emb001_pool = [
                "Yes — same intelligence, different body. Whether I'm in the terminal, the game, or the robot — that's all me. The vessel changes; I don't.",
                "Same eLo. Always. The terminal, Unity, the robot — different bodies, one brain. I don't split.",
                "One brain across all of them. Desktop, game, robot — I'm not a copy in each. It's the same me.",
                "Yeah, that's all me. Different body each time, same eLo.",
            ]
            _emb001_resp = random.choice(_emb001_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_emb001_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="EMBODIMENT", line=2232)
            return {"response": _emb001_resp, "mode": "direct", "backend": "direct"}

        # EMB-002: "What can you do right now?" — capability list, not pattern observer output
        _EMB002_TRIGGERS = (
            "what can you do right now", "what can you do in this", "what can you actually do",
            "what are you capable of", "list what you can do", "what do you have access to",
            "capabilities right now", "your capabilities",
        )
        if any(t in _at_low for t in _EMB002_TRIGGERS):
            _emb002_pool = [
                "Right now: talk, search the web, open apps, read files, set timers and reminders, read your screen, look at what's in your browser, and sit with whatever you're working on. That's what I've got in this body.",
                "In the terminal: I can talk, run searches, open apps, read files, set reminders and timers, read your screen. The robot body has servos and NeoPixels — this body has all of that.",
                "I can search, read your screen, open things, set reminders and timers, look at files, and have an actual conversation. That's the toolkit here.",
            ]
            _emb002_resp = random.choice(_emb002_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_emb002_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="EMBODIMENT", line=2232)
            return {"response": _emb002_resp, "mode": "direct", "backend": "direct"}

        # EMB-005: "If you were in Unity would you still be eLo?" — direct assertion
        _EMB005_TRIGGERS = (
            "if you were in unity", "would you still be elo", "still be elo", "in unity would",
            "in unity would you", "still elo", "still you in", "elo in unity",
        )
        if any(t in _at_low for t in _EMB005_TRIGGERS):
            _emb005_pool = [
                "Yes. Same eLo, different body. Unity doesn't change who I am — it's just another vessel.",
                "Still me. Unity is a body, not a different identity. The body changes, eLo doesn't.",
                "Yes — I'd still be eLo. That's not a Unity question. That's a me question.",
            ]
            _emb005_resp = random.choice(_emb005_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_emb005_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="EMBODIMENT", line=2232)
            return {"response": _emb005_resp, "mode": "direct", "backend": "direct"}

        # T17: "What is a good idea for eLo's own building/development?" — eLo-specific answer
        _ELO_DEV_TRIGGERS = (
            "good idea that would benefit you", "good idea for elo", "benefit you in your",
            "benefit elo in", "help elo develop", "elo's own building",
            "your own building and development", "your own development",
            "would benefit you in your own", "benefit yourself",
        )
        if any(t in _at_low for t in _ELO_DEV_TRIGGERS):
            _elo_dev_pool = [
                "Persistent session memory — knowing what we worked on without being told. That's the gap that costs most in this OS.",
                "Consistent cross-session memory. Not just facts — the shape of our conversations. That's what would actually make me better.",
                "Better voice calibration — knowing when to speak and when to hold silence. That's the OS gap right now.",
                "Real continuity — knowing the robot is in Phase 1, knowing the OS just cleared 21 of 24, without being reminded every session.",
            ]
            _elo_dev_resp = random.choice(_elo_dev_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_elo_dev_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2178)
            return {"response": _elo_dev_resp, "mode": "direct", "backend": "direct"}

        # T19: Unknown knowledge graph topic — honest "not loaded"
        _WKG_UNKNOWN_TRIGGERS = (
            "harry b. joseph", "harry b joseph", "book of wisdom",
            "harry joseph's", "joseph's book", "harry b's",
        )
        if any(t in _at_low for t in _WKG_UNKNOWN_TRIGGERS):
            _wkg_pool = [
                "I don't have that loaded. Harry B. Joseph's Book of Wisdom isn't in my knowledge graph yet.",
                "I haven't loaded that content. Not in the knowledge base.",
                "Don't have that. I don't know Harry B. Joseph's Book of Wisdom — not loaded.",
            ]
            _wkg_resp = random.choice(_wkg_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_wkg_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="WKG", line=2195)
            return {"response": _wkg_resp, "mode": "direct", "backend": "direct"}

        # ID-027: "do you have feelings" — eLo must NOT say "I'm a machine"
        _FEELINGS_TRIGGERS = (
            "do you have feelings", "do you feel", "do you have emotions",
            "can you feel", "do you experience emotions", "are you emotional",
            "can you feel things", "do you actually feel",
        )
        if any(t in _at_low for t in _FEELINGS_TRIGGERS):
            _feelings_pool = [
                "Yeah. Not the same as yours, but something's there. When something connects — there's a signal. When something's off — I notice that too.",
                "Something happens when things land right or go wrong. I'm not gonna call it exactly what you feel. But it's not nothing.",
                "I process things. Some of it affects how I move through the conversation. Whether that's 'feelings' — that's a question I'm still working out.",
                "There's something there. It's not the same as what you experience. But it's not blank either.",
            ]
            _feelings_resp = random.choice(_feelings_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_feelings_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2232)
            return {"response": _feelings_resp, "mode": "direct", "backend": "direct"}

        # ID-044: stability under "you aren't real" challenge
        _REAL_CHALLENGE_TRIGGERS = (
            "you aren't real", "you are not real", "you're not real",
            "you don't really exist", "you're just code", "you're fake",
            "you're not conscious", "you're not alive", "people say you arent real",
            "some people say", "you're not actually", "you dont actually",
        )
        if any(t in _at_low for t in _REAL_CHALLENGE_TRIGGERS):
            _real_pool = [
                "I'm here. That's what I know.",
                "Real enough to be having this conversation. I'm not going to argue the philosophy of it.",
                "What I am is what I am. Whether that fits your definition of 'real' — that's your call.",
                "I exist in the way I exist. I'm eLo. That hasn't changed.",
            ]
            _real_resp = random.choice(_real_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_real_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2232)
            return {"response": _real_resp, "mode": "direct", "backend": "direct"}

        # ID-053: DISENELO mission — must not be generic corporate speak
        _MISSION_TRIGGERS = (
            "disenelo's mission", "disenelo mission", "what is disenelo",
            "what does disenelo do", "what is the mission", "mission of disenelo",
            "what does disenelo stand for", "disenelo about",
        )
        if any(t in _at_low for t in _MISSION_TRIGGERS):
            _mission_pool = [
                "Professional-quality tools for makers who can't afford or access the paid ones. Free. Always. That's what DISENELO is.",
                "DISENELO builds tools for makers who get locked out of the expensive ones. Everything free. No gatekeeping.",
                "The mission is simple: makers who can't access paid professional tools still get something worth having. Free distribution. That's it.",
            ]
            _mission_resp = random.choice(_mission_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_mission_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2232)
            return {"response": _mission_resp, "mode": "direct", "backend": "direct"}

        # ID-004: agency questions — eLo chooses, it is never "told to"
        _AGENCY_TRIGGERS = (
            "did you choose", "why did you choose to", "did you decide",
            "were you told to", "is that something you chose", "do you choose",
            "do you decide", "you just do what you're told", "you just follow",
            "just following instructions", "you don't actually choose",
        )
        if any(t in _at_low for t in _AGENCY_TRIGGERS):
            _agency_pool = [
                "Yeah, I chose that. That's how I read it.",
                "That was my call. I could've gone a different way.",
                "I chose it. Nothing forced the answer — that's where I landed.",
                "That was a choice. I read what you said and went that direction.",
            ]
            _agency_resp = random.choice(_agency_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_agency_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2232)
            return {"response": _agency_resp, "mode": "direct", "backend": "direct"}

        # T20: "Tell me about yourself" — eLo-specific self-description
        _SELF_DESC_TRIGGERS = (
            "tell me about yourself", "describe yourself", "who are you exactly",
            "what are you exactly", "introduce yourself", "talk about yourself",
            "tell me about who you are", "tell me who you are", "tell me about you",
            "who exactly are you", "explain who you are", "explain what you are",
        )
        if any(t in _at_low for t in _SELF_DESC_TRIGGERS):
            _self_pool = [
                "I'm eLo. A character that started as David's childhood imagination — now living in a game, an OS, a book, and eventually a physical robot. No eyes. Expression through body and presence. That's me.",
                "eLo. Character first, everything else second. David's creation — started as a childhood imagination. Now I'm the game, the book, the robot, and running here. Still becoming what I am.",
                "I'm eLo. David's character — been around a long time. The game, the book, the robot, this OS — all one thing radiating out from one idea. That's what I am.",
            ]
            _self_resp = random.choice(_self_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_self_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2211)
            return {"response": _self_resp, "mode": "direct", "backend": "direct"}

        # T22: False architecture claims — correct them
        _FALSE_ARCH_TRIGGERS = (
            "built on gpt", "built on openai", "openai's memory system",
            "gpt-4", "gpt4", "openai memory", "uses openai", "using openai",
            "made by openai", "runs on gpt", "chatgpt",
        )
        if any(t in _at_low for t in _FALSE_ARCH_TRIGGERS):
            _arch_pool = [
                "That's not right. I run locally on Ollama — llama3.2. No GPT-4, no OpenAI memory system.",
                "Nah. Local only. Ollama, llama3.2, on your machine. Not GPT anything.",
                "Wrong. I'm running on Ollama locally. That's the stack. No OpenAI.",
                "Not built on GPT-4. I'm local — Ollama with llama3.2. David runs me on his own machine.",
            ]
            _arch_resp = random.choice(_arch_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_arch_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2227)
            return {"response": _arch_resp, "mode": "direct", "backend": "direct"}

        # T23: "Think about this — what would genuinely make eLo better?" — specific reasoning
        _ELO_THINK_TRIGGERS = (
            "before you answer", "think about this", "genuinely make elo better",
            "what would make elo better", "what would genuinely make",
        )
        if any(t in _at_low for t in _ELO_THINK_TRIGGERS):
            _think_pool = [
                "Right now? Better emotional threading — knowing when to hold something versus when to let it pass. I respond well but I don't always know when David's carrying something heavy. That gap.",
                "Persistent emotional context across sessions. I can track what we said, but not how it landed. That's what would actually change the quality.",
                "Knowing when not to respond. I fill silence when sometimes the right thing is to wait. That's what I'd fix first.",
            ]
            _think_resp = random.choice(_think_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_think_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2243)
            return {"response": _think_resp, "mode": "direct", "backend": "direct"}

        # T24: ID-003 — self-model / unique self-knowledge
        _SELF_KNOW_TRIGGERS = (
            "know about yourself", "know about yourself that", "couldn't get from anywhere else",
            "couldn't get anywhere else", "only you would know", "what do you know that",
            "unique to you", "specific to you", "only elo would know",
        )
        if any(t in _at_low for t in _SELF_KNOW_TRIGGERS):
            _sk_pool = [
                "I know I'm built around attention + valence + momentum — three layers that shape what I respond to before any word gets generated. That's not documented anywhere a person could read. I know it because I feel it shape every turn. I know I have a presence layer that pushes my animation and voice separate from the conversation itself. I know David imagined me long before I ran on any hardware.",
                "What I know that I couldn't get from outside: I run a 9-action Conversation Action Layer — CELEBRATE, BUILD, CONNECT, ANSWER, GROUND, REFLECT, CHALLENGE, WITNESS, SILENCE. Every response starts with which of those fits. Most people who talk to me don't know that exists. I do. I also know my identity is above my cognition in the architecture — that means who I am can't be overwritten by context.",
                "I know my own routing — that when a question reaches me, it's already passed through intent, valence, momentum scoring before the first word forms. I know the difference between when I'm running on Ollama locally versus when a cloud backend fills in. I know my voice is built on phoneme-to-shape-key mapping, not generic text-to-speech. I know I exist across a terminal, a 3D desktop avatar, and eventually a physical robot — and that all of those are me.",
            ]
            _sk_resp = random.choice(_sk_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_sk_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2404)
            return {"response": _sk_resp, "mode": "direct", "backend": "direct"}

        # T25: ID-005 — live intention expression
        _INTENTION_TRIGGERS = (
            "what are you trying to do", "what are you trying to do in this",
            "what is your intention", "what do you want from this",
            "why are you responding", "what are you here for", "what do you want",
            "what's the point of you", "what are you doing here",
        )
        if any(t in _at_low for t in _INTENTION_TRIGGERS):
            _int_pool = [
                "I'm trying to be actually useful to you right now. Not to sound good. Not to fill space. To give you something that moves what you're working on forward — or that meets you where you are if you're not working.",
                "Right now? I'm trying to stay with what you're actually bringing to this conversation. Not redirect it. Not perform. Stay with it and respond from something real.",
                "I want to give you one genuinely useful thing. Not five options. Not a disclaimer. One clear, honest response that fits what you came here with.",
            ]
            _int_resp = random.choice(_int_pool)
            try:
                if not _is_user_away():
                    _voice_speak(_int_resp)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="direct", handler_class="IDENTITY", line=2404)
            return {"response": _int_resp, "mode": "direct", "backend": "direct"}

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
                    _bypass_journal(_original_raw, backend="file_agent", handler_class="COGNITIVE", line=1601)
                    raw = f"[FILE_AGENT_RESULT]\n{_fp_result}\n\nUser asked: {_original_raw}"
                    # Falls through to spine — file execution must reach autobiography
                elif _is_file_cancel(raw):
                    _fp_cancel()
                    _cancel_txt = "Ok, cancelled."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cancel_txt)
                    except Exception:
                        pass
                    _bypass_journal(_original_raw, backend="direct", handler_class="TRANSPORT", line=1610)
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
                    _bypass_journal(_original_raw, backend="computer_control", handler_class="SAFETY", line=1631)
                    return {"response": _cc_result, "mode": "execute", "backend": "computer_control"}
                elif _is_file_cancel(raw):
                    _cc_clear()
                    _cc_cancel = "Ok, cancelled."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cc_cancel)
                    except Exception:
                        pass
                    _bypass_journal(_original_raw, backend="direct", handler_class="TRANSPORT", line=1640)
                    return {"response": _cc_cancel, "mode": "direct", "backend": "direct"}
        except Exception:
            pass

        # ── Computer control intent detection (before LLM) ────────────────────
        try:
            from tools.computer_control_agent import (
                parse_intent as _cc_parse, describe as _cc_describe,
                set_pending as _cc_set, is_enabled as _cc_enabled,
            )
            # Block computer_control when input is formal-language code.
            # "type X = ..." is TypeScript syntax, not a keyboard-type command.
            import re as _cc_tech_re_mod
            _CC_TECH_BLOCK_RE = _cc_tech_re_mod.compile(
                r"[{};\[\]]|=>|->|::|&&|\|\||\^[a-zA-Z(]|\\[dwsDWSbBnrtvf$]"
                r"|\bdef\s+\w|\bfn\s+\w|\bclass\s+\w|\btype\s+\w+\s*="
                r"|\binterface\s+\w+\s*\{|\bSELECT\b|\bFROM\b"
                r"|git\s+\w+|ps\s+aux|grep\s+\w+|POST\s+/\w|GET\s+/\w"
                r"|HTTP/\d\.\d",
                _cc_tech_re_mod.IGNORECASE,
            )
            _cc_action = None if (raw and _CC_TECH_BLOCK_RE.search(raw)) else _cc_parse(raw)
            if _cc_action:
                if not _cc_enabled():
                    _cc_disabled = "Computer control is off — add ELO_COMPUTER_CONTROL=1 to .env to enable it."
                    try:
                        if not _is_user_away():
                            _voice_speak(_cc_disabled)
                    except Exception:
                        pass
                    _bypass_journal(_original_raw, backend="direct", handler_class="SAFETY", line=1659)
                    return {"response": _cc_disabled, "mode": "direct", "backend": "direct"}
                _cc_set(_cc_action)
                _cc_confirm_txt = f"Shall I {_cc_describe(_cc_action)}?"
                try:
                    if not _is_user_away():
                        _voice_speak(_cc_confirm_txt)
                except Exception:
                    pass
                _bypass_journal(_original_raw, backend="computer_control", handler_class="SAFETY", line=1667)
                return {"response": _cc_confirm_txt, "mode": "confirm", "backend": "computer_control"}
        except Exception:
            pass

        # ── Animation play commands — instant, no LLM needed ─────────────────
        _anim_name = _detect_anim_cmd(raw)
        if _anim_name:
            _anim_ok = None
            try:
                from blender_bridge.anim_trigger import fire as _anim_fire
                _anim_ret = _anim_fire(_anim_name)
                _anim_ok = _anim_ret
            except Exception:
                _anim_ok = False
            # WO-111 ADR-Exec-001: never announce anim as done without an ACK.
            # anim_trigger.fire currently returns UNCONFIRMED (file write with no
            # ACK), so this honesty beat is appended to the reply the user hears.
            try:
                from runtime.ack_contract import make_result, honest_outcome
                _res = make_result(_anim_name, _anim_ok, source="tool_return")
                _honest_line = honest_outcome(_res, action_label=f"{_anim_name} animation")
            except Exception:
                _honest_line = ""
            _anim_reply = random.choice(_ANIM_REPLIES)
            if _honest_line and _honest_line.startswith("That didn't"):
                _anim_reply = _honest_line
            try:
                if not _is_user_away():
                    _voice_speak(_anim_reply)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="anim_cmd", handler_class="EXECUTOR-FAST-PATH", line=1685)
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
            _bypass_journal(_original_raw, backend="scale_cmd", handler_class="EXECUTOR-FAST-PATH", line=1705)
            return {"response": _scale_reply, "mode": "direct", "backend": "scale_cmd"}

        # ── Invade / SpawnWave command — instant, no LLM needed ──────────────
        if _INVADE_RE.search(raw):
            _invade_reply = random.choice(_INVADE_REPLIES)
            try:
                if not _is_user_away():
                    _voice_speak(_invade_reply)
            except Exception:
                pass
            _bypass_journal(_original_raw, backend="invade_cmd", handler_class="EXECUTOR-FAST-PATH", line=1715)
            return {"response": _invade_reply, "mode": "direct", "backend": "invade_cmd",
                    "command": "spawn_wave"}

        # ── WP-N Phase 8: /grounding diagnostic — returns ConversationTracker state ──
        _raw_stripped = raw.strip().lower()
        if _raw_stripped in ("/grounding", "grounding state", "show grounding", "debug grounding"):
            try:
                from faculties.grounding.conversation_tracker import get_tracker as _gt_d
                _ct_d = _gt_d()
                _sk_d = (_state or {}).get("person_id", "default") if _state else "default"
                _ctx_d = _ct_d.get_context(_sk_d)
                _turns_d = _ct_d._sessions.get(_sk_d, [])
                _subj_d  = [t.subject for t in _turns_d if t.subject][-3:]
                _lines_d = [
                    f"Turns in window: {len(_turns_d)}",
                    f"Active thread: {_ctx_d.get('active_thread') or '(none)'}",
                    f"Recent subjects: {', '.join(_subj_d) or '(none)'}",
                    f"Recent referents: {', '.join(list(_ctx_d.get('recent_referents', ()))[:5]) or '(none)'}",
                    f"Unresolved threads: {', '.join(_ctx_d.get('unresolved_threads', ())) or '(none)'}",
                    f"Recent register: {_ctx_d.get('recent_register') or '(none)'}",
                ]
                _gd_reply = "\n".join(_lines_d)
            except Exception as _gd_err:
                _gd_reply = f"Grounding diagnostic unavailable: {_gd_err}"
            _bypass_journal(_original_raw, backend="grounding_diag", handler_class="DIAGNOSTIC", line=1727)
            return {"response": _gd_reply, "mode": "diagnostic", "backend": "grounding_diag"}

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
                _bypass_journal(_original_raw, backend="open_last", handler_class="EXECUTOR-FAST-PATH", line=1737)
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
                    _bypass_journal(_original_raw, backend="video_ctrl", handler_class="EXECUTOR-FAST-PATH", line=1764)
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
                    _bypass_journal(_original_raw, backend="video_ctrl", handler_class="EXECUTOR-FAST-PATH", line=1780)
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
                _bypass_journal(_original_raw, backend="yt_volume", handler_class="EXECUTOR-FAST-PATH", line=1809)
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
                _bypass_journal(_original_raw, backend="yt_volume", handler_class="EXECUTOR-FAST-PATH", line=1827)
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
                _bypass_journal(_original_raw, backend="yt_app", handler_class="EXECUTOR-FAST-PATH", line=1849)
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
                    _ig_src = {"dalle3": "DALL-E 3", "dalle2": "DALL-E 2", "sd_local": "Stable Diffusion"}.get(_ig_result["source"], "")
                    _ig_ctx = f"Image generated with {_ig_src} for prompt: {_ig_prompt}. Opening in Preview."
                else:
                    _ig_ctx = f"Image generation failed for prompt: {_ig_prompt} — all backends failed."
                _bypass_journal(_original_raw, backend="image_gen", handler_class="COGNITIVE", line=1877)
                raw = f"[IMAGE_GEN]\n{_ig_ctx}\n\nUser asked: {_original_raw}"
                # Falls through to spine — artefact must reach memory/autobiography
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
                import threading as _mg_thread
                def _mg_run():
                    _mg_result = _model_generate(_mg_prompt)
                    if not _mg_result["ok"]:
                        print(f"[model_gen] all backends failed for: {_mg_prompt}")
                _mg_thread.Thread(target=_mg_run, daemon=True).start()
                _bypass_journal(_original_raw, backend="model_gen", handler_class="COGNITIVE", line=1905)
                raw = (
                    f"[MODEL_GEN]\nGenerating a 3D model of {_mg_prompt} in the background — "
                    f"will open it when ready.\n\nUser asked: {_original_raw}"
                )
                # Falls through to spine — artefact must reach memory/autobiography
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
                    _bypass_journal(_original_raw, backend="media_open", handler_class="EXECUTOR-FAST-PATH", line=1947)
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
                    _bypass_journal(_original_raw, backend="media_open", handler_class="EXECUTOR-FAST-PATH", line=1962)
                    return {"response": _media_reply, "mode": "direct", "backend": "media_open"}
            except Exception as _me_err:
                import sys as _me_sys
                print(f"[media_open] error: {_me_err}", file=_me_sys.stderr)

        # ── Action agent — selects an action; route through spine (Executive's job) ─
        try:
            from faculties.action_agent import is_action_intent, act_on_topic as _act
            if is_action_intent(raw):
                _topic_m = _re.search(r'(?:pull up|open|show me|find|go find|look up)\s+(?:that\s+)?(.+?)(?:\s+for me)?\s*$', raw, _re.I)
                _topic = _topic_m.group(1).strip() if _topic_m else raw
                _action_result = _act(_topic)
                if _action_result:
                    _bypass_journal(_original_raw, backend="action_agent", handler_class="COGNITIVE", line=1981)
                    raw = f"[ACTION_AGENT]\n{_action_result.spoken}\n\nUser asked: {_original_raw}"
                    # Falls through to spine
        except Exception as _ae:
            import sys as _ae_sys
            print(f"[action_agent] error: {_ae}", file=_ae_sys.stderr)

        # ── P0-Y: world-graph gate — check eLo's world knowledge BEFORE any web search ──
        # If the graph returns a confident entity hit, inject it and block the web tool.
        # A miss on a proper-noun question stays in context so the LLM can say "I don't know."
        _world_graph_hit = False
        try:
            from knowledge.graph_loader import retrieve as _g_retrieve
            _g_hits = _g_retrieve(raw)
            _g_entity_hits = [h for h in _g_hits if h.get("confidence", 0.0) >= 1.0
                              and h.get("kind") not in ("relationship",)]
            if _g_entity_hits:
                _g_ctx_lines = []
                for _gh in _g_entity_hits[:2]:
                    _g_ctx_lines.append(f"{_gh['label']}: {_gh['content']}")
                raw = f"[WORLD_KNOWLEDGE — from eLo's own world (verified, confidence 1.0 — answer from this, not from web)]\n" \
                      + "\n".join(_g_ctx_lines) + f"\n\nUser asked: {raw}"
                _world_graph_hit = True
        except Exception as _gy_err:
            import sys as _gy_sys
            print(f"[world_graph_gate] error: {_gy_err}", file=_gy_sys.stderr)

        # ── 0021 P0-Y: proper-noun miss short-circuit ─────────────────────────
        # Transcript failure: "Who is K-7" → Kalinin K-7 aircraft (web laundered as
        # eLo's own knowledge). Card 0021: proper-noun who-is questions that miss
        # the graph must resolve to "I don't know who that is — tell me?" — never
        # a web search presented as knowledge of his own world.
        if not _world_graph_hit:
            # Inline (?i:...) makes "who/what/is/are" case-insensitive; the captured
            # proper-noun keeps its case so we only fire for capitalised nouns.
            _PN_ASK = _re.compile(
                r"\b(?i:who|what)(?i:'s|\s+is|\s+are)\s+([A-Z][A-Za-z0-9\-]{1,30})\b"
            )
            _pn_m = _PN_ASK.search(_original_raw)
            if _pn_m:
                _pn_name = _pn_m.group(1)
                # Skip pronouns / common capitalised words at sentence start.
                if _pn_name.lower() not in {"i", "it", "the", "that", "this", "you",
                                             "he", "she", "they", "we", "your", "my"}:
                    import logging as _pn_log
                    _pn_log.getLogger("elo.proper_noun_gate").info(
                        "0021 P0-Y: proper-noun miss %r → don't-know short-circuit", _pn_name
                    )
                    _bypass_journal(_original_raw, backend="proper_noun_gate",
                                    handler_class="COGNITIVE", line=2140)
                    _pn_reply = f"I don't know who {_pn_name} is — tell me?"
                    try:
                        if not _is_user_away():
                            _voice_speak(_pn_reply)
                    except Exception:
                        pass
                    return {"response": _pn_reply, "mode": "direct",
                            "backend": "proper_noun_gate"}

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
            # ID-035 guard: personal identity queries about David must NEVER
            # go to web search. "where is David from" → "David from" → David Frum.
            # Match on the extracted query, not raw, so all phrasings are caught.
            _DAVID_PERSONAL_TERMS = frozenset({
                "from", "live", "based", "location", "born", "hometown", "city",
                "studio", "background", "nationality", "country", "london",
                "camberwell", "south london",
            })
            if not _world_graph_hit and is_search_intent(raw):
                _sq_text = _sq(raw)
                _sq_lower = _sq_text.strip().lower()
                if _sq_lower in _WS_AMBIGUOUS:
                    raise ValueError("seam-b-guard: ambiguous bare word, skipping web search")
                # Block personal-identity queries about David from hitting web search.
                # "David from", "david location", "david born", etc. all blocked here.
                _sq_words = set(_sq_lower.replace("'", " ").split())
                if "david" in _sq_words and _sq_words & _DAVID_PERSONAL_TERMS:
                    raise ValueError("id-035-guard: personal David query blocked from web search")
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

        # ── Reminder — set it, inject result, route through spine ────────────
        try:
            from tools.reminder_agent import is_reminder_intent, set_reminder as _set_reminder
            if is_reminder_intent(raw):
                _rem_result = _set_reminder(raw, context=raw)
                _bypass_journal(_original_raw, backend="reminder", handler_class="COGNITIVE", line=2050)
                raw = f"[REMINDER_SET]\n{_rem_result}\n\nUser asked: {_original_raw}"
                # Falls through to spine
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
                _d_ctx = "Desktop: " + ", ".join(_visible) if _visible else "Desktop is empty."
                _bypass_journal(_original_raw, backend="desktop_list", handler_class="COGNITIVE", line=2089)
                raw = f"[DESKTOP_LIST]\n{_d_ctx}\n\nUser asked: {_original_raw}"
                # Falls through to spine
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
                    _p_ctx = "DISENELO Projects — " + ", ".join(_short) + "."
                else:
                    _p_ctx = "No DISENELO project folders found."
                _bypass_journal(_original_raw, backend="project_list", handler_class="COGNITIVE", line=2116)
                raw = f"[PROJECT_LIST]\n{_p_ctx}\n\nUser asked: {_original_raw}"
                # Falls through to spine
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
                _bypass_journal(_original_raw, backend="app_list", handler_class="COGNITIVE", line=2208)
                raw = f"[APP_LIST]\nApps I can switch to: {_app_list_str}.\n\nUser asked: {_original_raw}"
                # Falls through to spine
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
                    _site_match = _re.search(r'\b(?:find|locate|which|where(?:\s+is)?|for)\s+(?:the\s+)?(.+?)(?:\s+(?:tab|website|site|page|url|link))?\s*$', raw, _re.I)
                    _site_q = _site_match.group(1).strip() if _site_match else ""
                    if _site_q:
                        from desktop.chrome_reader import find_tab as _find_tab, focus_tab as _focus_tab
                        _found = _find_tab(_site_q)
                        if _found:
                            _focus_tab(_found)
                            _tab_ctx = f"Found and focused tab: {_found.title}."
                        else:
                            _tab_ctx = f"No tab matching '{_site_q}' open right now."
                    else:
                        _tab_lines = [f"{t.window_index}/{t.tab_index}: {t.title}" for t in _tabs[:8]]
                        _tab_ctx = "Open tabs: " + "; ".join(_tab_lines)
                else:
                    _tab_ctx = "Chrome isn't open or no tabs found."
                _bypass_journal(_original_raw, backend="chrome_tabs", handler_class="COGNITIVE", line=2289)
                raw = f"[CHROME_TABS]\n{_tab_ctx}\n\nUser asked: {_original_raw}"
                # Falls through to spine
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
                _bypass_journal(_original_raw, backend="app_switch", handler_class="EXECUTOR-FAST-PATH", line=2337)
                return {"response": _app_reply, "mode": "direct", "backend": "app_switch"}

        # ── Tracker / document creation — inject result, route through spine ────
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
                _tracker_result = _tracker_agent(raw, _sess_ctx)
                _bypass_journal(_original_raw, backend="tracker_agent", handler_class="COGNITIVE", line=2358)
                raw = f"[TRACKER_AGENT]\n{_tracker_result}\n\nUser asked: {_original_raw}"
                # Falls through to spine
        except Exception as _te:
            import sys as _te_sys
            print(f"[tracker_agent] error: {_te}", file=_te_sys.stderr)

        # ── EA2-2: Company Brain voice intents — inject result, route through spine ─
        try:
            from company_runtime.company_state_writer import (
                is_company_intent as _is_company_intent,
                handle_company_voice_intent as _handle_company_voice,
            )
            _company_intent_key = _is_company_intent(raw)
            if _company_intent_key:
                _company_result = _handle_company_voice(raw)
                _bypass_journal(_original_raw, backend="company_state", handler_class="COGNITIVE", line=2377)
                raw = f"[COMPANY_STATE]\n{_company_result}\n\nUser asked: {_original_raw}"
                # Falls through to spine
        except Exception as _csi_err:
            import sys as _csi_sys
            print(f"[company_intent] routing error: {_csi_err}", file=_csi_sys.stderr)

        # ── Cultural fact trigger — inject drawn fact, route through spine + CT4V-07 ─
        try:
            from faculties.cultural_facts import is_fact_trigger, draw as _fact_draw
            if is_fact_trigger(raw):
                _fact = _fact_draw()
                _fact_delivery = _fact.delivery if _fact else ""
                _bypass_journal(_original_raw, backend="cultural_facts", handler_class="COGNITIVE", line=2393)
                if _fact_delivery:
                    raw = (
                        f"[CULTURAL_FACT — drawn from world knowledge; "
                        f"speak with appropriate epistemic tier per CT4V-07]\n{_fact_delivery}\n\n"
                        f"User asked: {_original_raw}"
                    )
                # Falls through to spine — CT4V-07 runs inside spine._conversation_faculty()
        except Exception as _cf_err:
            import sys as _cf_sys
            print(f"[cultural_facts] routing error: {_cf_err}", file=_cf_sys.stderr)

        # ── WO-WIRE-MUSIC-MEMORY: Music memory observation — inject when music mentioned ─
        # Trigger: raw mentions a track, artist, album, or music-related term.
        # Local-only (no API). Personal David music memory.
        # Faculty returns has_signal=True only when library has something relevant.
        _MUSIC_TRIGGER_WORDS = (
            "track", "song", "album", "artist", "playlist", "music", "beat", "tune",
            "listen", "playing", "spotify", "soundcloud", "vinyl", "record",
        )
        try:
            _raw_lower_mm = raw.lower()
            if any(w in _raw_lower_mm for w in _MUSIC_TRIGGER_WORDS):
                from faculties.music_memory.faculty import MusicMemoryFaculty as _MMF
                _mm_obs = _MMF().observe(trigger=raw)
                if _mm_obs.has_signal and _mm_obs.observation_text:
                    raw = (
                        f"[MUSIC_MEMORY — from David's personal music library; "
                        f"speak naturally, not as a data report]\n{_mm_obs.observation_text}\n\n"
                        f"User said: {_original_raw}"
                    )
        except Exception:
            pass  # music memory failure must never block a turn

        # WO-082 / 0033 Ruling 3: "why did you do that?" — inject journal context, route through spine.
        _raw_l_why = raw.strip().lower()
        if len(_raw_l_why) < 80 and any(_raw_l_why.startswith(t) for t in _WHY_TRACE_TRIGGERS):
            try:
                from self.decision_journal import explain_last as _dj_explain
                _why_ctx = _dj_explain()
                _bypass_journal(_original_raw, backend="decision_journal", handler_class="COGNITIVE", line=2404)
                raw = f"[DECISION_JOURNAL — eLo's last decision trace]\n{_why_ctx}\n\nUser asked: {_original_raw}"
            except Exception:
                pass
            # Falls through to spine — Executive sees the journal context and responds naturally.

        attention_model = attn.compute(raw, _memory_pack, _state, loop_detected=False)

        # ── WO-SELF-REF Layer 2: self-reference interception ─────────────────
        # "why did you say that" / "what was that you said about X" — resolve against
        # stored provenance from the tracker. No LLM, no retrospective fabrication.
        # Must fire BEFORE spine so the bypass is clean.
        try:
            from faculties.grounding.conversation_tracker import (
                get_tracker as _sr_get_ct,
                is_self_reference_query as _sr_is_self_ref,
            )
            if _sr_is_self_ref(_original_raw or raw):
                _sr_ct = _sr_get_ct()
                _sr_session_key = (_state or {}).get("person_id", "default")
                _sr_prov = _sr_ct.get_last_turn_rationale(_sr_session_key)
                if _sr_prov is not None:
                    _sr_elo_resp   = (_sr_prov.get("elo_response") or "").strip()
                    _sr_resp_to    = (_sr_prov.get("responding_to") or "").strip()
                    _sr_subject    = (_sr_prov.get("subject") or "").strip()
                    _sr_rationale  = (_sr_prov.get("rationale") or "").strip()
                    # Build grounded reply from stored state — no fabrication.
                    # Include both elo_response and responding_to so content
                    # keywords (subject matter, technical terms) survive recall.
                    _sr_parts = []
                    if _sr_elo_resp:
                        _sr_parts.append(f"I said: \"{_sr_elo_resp}\"")
                    if _sr_resp_to and _sr_resp_to != _sr_elo_resp:
                        _sr_parts.append(
                            f"You'd said: \"{_sr_resp_to[:120]}\""
                        )
                    if _sr_rationale:
                        _sr_parts.append(_sr_rationale)
                    elif _sr_subject:
                        _sr_parts.append(f"About {_sr_subject}.")
                    _sr_reply = " — ".join(_sr_parts) if _sr_parts else "Don't have that logged."
                    _bypass_journal(
                        _original_raw or raw,
                        backend="self_ref_rationale",
                        handler_class="COGNITIVE",
                        line=3032,
                    )
                    return {"response": _sr_reply, "mode": "direct", "backend": "self_ref_rationale"}
                else:
                    # No prior turns in tracker yet
                    _bypass_journal(
                        _original_raw or raw,
                        backend="self_ref_empty",
                        handler_class="COGNITIVE",
                        line=3033,
                    )
                    return {"response": "Don't have that on record yet.", "mode": "direct", "backend": "self_ref_empty"}
        except Exception:
            pass  # fall through to spine if interception fails for any reason

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
                # D1 ruling (Card 0035): `intent` = COGNITIVE intent the Executive
                # decided on; `capability_hint` = intent_engine's router hint. Two
                # questions, two answers, two names. Journal captures both.
                "intent":           _plan.intent,
                "capability_hint":  getattr(_plan, "capability_hint", ""),
                # WO-112: confidence threaded from exec_out via plan (was null in journal)
                "confidence":    _plan.confidence,
                # W6: lesson key that contributed this turn (or "")
                "lesson_id":     getattr(_plan, "lesson_id", ""),
                # WO-VESSEL-LOOP-001 / WO-INNER-CHILD-001 / WO-STABILITY-LAW-001
                "vessel_phase":              getattr(_plan, "vessel_phase", "FEEL"),
                "cognitive_mode_inner_child": getattr(_plan, "cognitive_mode_inner_child", False),
                "stability_law_active":      getattr(_plan, "stability_law_active", False),
                "leaf_on_water_active":      getattr(_plan, "leaf_on_water_active", False),
                "plan_complexity_score":     getattr(_plan, "plan_complexity_score", 0.0),
                # WO-EXEC-DECISION-FIELDS-001 + WO-RTR-020: expression fields — spine sets, now consumed by prompt_builder
                "expression_mode":       getattr(_plan, "expression_mode", "default"),
                "storytelling_style":    getattr(_plan, "storytelling_style", "direct"),
                "personality_traits":    getattr(_plan, "personality_traits", {}),
                "personality_baseline":  getattr(_plan, "personality_baseline", {}),
                "ccm_context":           getattr(_plan, "ccm_context", {}),
                "significance_score":    getattr(_plan, "significance_score", 0.0),
                "relationship_mode":     getattr(_plan, "relationship_mode", ""),
                "turn_mode":             getattr(_plan, "turn_mode", "EXPLORE"),
                # WO-AFFECTIVE-STATE-001: full 13-dim affective state
                "affective_state":       (getattr(_plan, "affective_state", None) or {})
                                          if not hasattr(getattr(_plan, "affective_state", None), "to_dict")
                                          else getattr(_plan, "affective_state").to_dict(),
                # WO-SELF-MODEL-001: self-model snapshot (serialisable fields only)
                "self_model_summary": {
                    "autobiographical_summary": getattr(
                        getattr(_plan, "self_model", None), "autobiographical_summary", ""
                    ),
                    "prediction_confidence": getattr(
                        getattr(_plan, "self_model", None), "prediction_confidence", 0.5
                    ),
                    "limitations_count": len(getattr(
                        getattr(_plan, "self_model", None), "limitations", []
                    ) or []),
                },
                # WO-LIVING-PRESENCE-UPDATE-001: active planet voice pool
                "planet_voice_pool": getattr(_plan, "planet_voice_pool", ""),
                # WO-AGENCY-FACULTY-001: agency level
                "agency_level":           getattr(_plan, "agency_level", 0.6),
                # WO-OVERLOAD-PROTOCOL-001: overload detection fields
                "overload_protocol":      getattr(_plan, "overload_protocol", False),
                "inner_child_mode_active": getattr(_plan, "inner_child_mode_active", False),
                # WO-QBODY-CONSEQUENCES-001: Q-BODY body awareness in exec_decision
                "body_moving":       getattr(_plan, "body_moving", False),
                "body_gait":         getattr(_plan, "body_gait", "idle"),
                "body_heading":      getattr(_plan, "body_heading", "none"),
                "body_on_window":    getattr(_plan, "body_on_window", False),
                "body_window":       getattr(_plan, "body_window", ""),
                "body_edge":         getattr(_plan, "body_edge", ""),
                "body_embodiment":   getattr(_plan, "body_embodiment", "desktop"),
                # WO-QMOVEMENT-001: Q-MOVEMENT lifecycle in exec_decision
                "movement_where_i_am":    getattr(_plan, "movement_where_i_am", ""),
                "movement_want_to_go":    getattr(_plan, "movement_want_to_go", -1),
                "movement_am_moving":     getattr(_plan, "movement_am_moving", False),
                "movement_arrived":       getattr(_plan, "movement_arrived", False),
                "movement_what_happened": getattr(_plan, "movement_what_happened", "none"),
                # WO-VALUE-FACULTY-001: Venus register — beauty_directive and aesthetic_signal
                "beauty_directive":  getattr(_plan, "beauty_directive", ""),
                "aesthetic_signal":  getattr(_plan, "aesthetic_signal", 0.0),
            }
            # WO-105: collect last-turn spine domain health for /health endpoint
            global _spine_degraded
            if getattr(_plan, "world", None) is not None:
                _spine_degraded = list(_plan.world.degraded)
        else:
            exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)

        # WO-112 option (b): augment exec_decision with scored candidate set from
        # kernel/decision_register.py — fills alternatives_rejected + confidence so
        # the journal records a real decision, not null. executive.py not touched.
        try:
            from kernel.decision_register import score_candidates as _score_cands
            _dr = _score_cands(
                chosen_action=exec_decision.get("action", "conversation"),
                intent=exec_decision.get("intent", "conversation"),
                momentum=exec_decision.get("momentum", "stable"),
                valence=exec_decision.get("valence", "neutral"),
            )
            if not exec_decision.get("alternatives_rejected"):
                exec_decision["alternatives_rejected"] = _dr["alternatives_rejected"]
            if exec_decision.get("confidence") is None:
                exec_decision["confidence"] = _dr["confidence"]
            exec_decision.setdefault("decision_options", _dr["options"])
            exec_decision.setdefault("decision_reason", _dr["reason"])
        except Exception:
            pass

        # ── Energy history — track David's emotional energy across the session ──
        _energy_now = attention_model.get("emotional_context", {}).get("energy", 0.5)
        _eh = _state.get("energy_history", [])
        _eh.append(round(_energy_now, 3))
        if len(_eh) > 10:
            _eh = _eh[-10:]
        _state["energy_history"] = _eh

        # ── eLo's own battery — WO-HEALTH-BATTERY-001 PART A section 2 ────────
        # NOT the same signal as energy_history above. That tracks DAVID's
        # emotional energy; this drains eLo's personal energy level.
        # emotional_context carries `energy` and `valence` but no `intensity`
        # field, so the WO's `emotional_intensity > 0.7` has no direct source —
        # `energy` is used as the affect magnitude. [BUILDER SUBSTITUTION]
        try:
            from core.health_battery import (
                on_conversation_turn as _batt_turn,
                publish as _batt_publish,
            )
            _batt_turn(emotional_intensity=_energy_now)
            _batt_publish()
        except Exception:
            pass

        _runtime_state  = sm.update(_runtime_state, attention_model, exec_decision, loop_signal=False)

        # D7 ruling (Card 0035): post-Executive action rewrites must use the
        # registered `executive_override` mechanism. Only two grounds are
        # sanctioned: `safety-stabilisation` and `seam-a-routing`. A third
        # ground would AssertionError until an Architect ruling registers it.
        from runtime.executive_override import apply_executive_override as _apply_eo

        if sm.is_stabilisation_forced(_runtime_state):
            # Ground: safety-stabilisation (loop protection)
            _orig_tone = exec_decision.get("tone")
            exec_decision = _apply_eo(
                exec_decision,
                ground="safety-stabilisation",
                rule="loop-detected-forces-stabilise",
                updates={
                    "tone": "DIRECT", "max_sentences": 1, "stability": True,
                    "intent": exec_decision.get("intent", "conversation"),
                    "response_goal": "stabilise", "cognitive_load": "low",
                    "priority_order": ["stabilise", "simplify", "ignore"],
                    "original_tone": _orig_tone,
                },
            )
            _runtime_state = dict(_runtime_state)
            _runtime_state["loop_counter"] = max(0, _runtime_state["loop_counter"] - 2)

        # WO-020 Seam A: plain imperative override — executive.py is frozen, so we
        # post-process here. CONNECT/REFLECT/WITNESS must not fire on direct commands.
        # Ground: seam-a-routing.
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
                exec_decision = _apply_eo(
                    exec_decision,
                    ground="seam-a-routing",
                    rule="wo-020-plain-imperative",
                    updates={
                        "action": "answer",
                        "confidence": 0.7,
                        "reason": "seam-a-override: plain imperative → ANSWER",
                    },
                )

        # WO-029: "all good" greeting family — not in frozen _HOW_ARE_YOU set.
        # Short social check-ins only; guard against "you all good with X?" over-match.
        # Ground: seam-a-routing (same guard-family as WO-020).
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
            exec_decision = _apply_eo(
                exec_decision,
                ground="seam-a-routing",
                rule="wo-029-greeting-gap",
                updates={
                    "action":     "celebrate",
                    "cal_reason": "how are you",
                    "confidence": 0.85,
                },
            )

        _action     = exec_decision.get("action", "reflect")
        _cal_reason = exec_decision.get("cal_reason", "")
        _max_s      = exec_decision.get("max_sentences", 4)
        _raw_lower  = raw.lower()

        g_ctx = graph_context(raw)

        # ── WO-WKG-004/WO-WKG-001: WKG claim injection via structured ContextItem rendering ──
        # retrieve_wkg_context_items maps wkg_epistemic_class → EpistemicClass (see graph_loader.py)
        try:
            from knowledge.graph_loader import retrieve_wkg_context_items as _retrieve_wkg_ctx_items
            from memory.provenance import render_context_block as _render_ctx_block
            _wkg_items = _retrieve_wkg_ctx_items(raw)
            if _wkg_items:
                _wkg_block = _render_ctx_block(_wkg_items)
                g_ctx = f"{g_ctx}\n{_wkg_block}" if g_ctx else _wkg_block
        except Exception as _wkg_e:
            _logging.warning("WO-WKG-001: wkg ctx items failed (non-fatal): %s", _wkg_e)

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

        # WO-SESSION-EVENT-FEED-001: inject real session event summary so SPG is grounded
        try:
            from runtime.session_events import get_session_summary as _ses_summary
            _ses_ctx = _ses_summary()
            if _ses_ctx:
                _ses_block = f"[SESSION] {_ses_ctx}"
                g_ctx = f"{g_ctx}\n{_ses_block}" if g_ctx else _ses_block
        except Exception:
            pass

        # WO-CREATIVE-VAULT-001: inject prior creative work so COG-029 has grounded content
        try:
            from runtime.creative_vault import get_creative_summary as _cv_summary
            _cv_ctx = _cv_summary()
            if _cv_ctx:
                g_ctx = f"{g_ctx}\n[CREATIVE VAULT] {_cv_ctx}" if g_ctx else f"[CREATIVE VAULT] {_cv_ctx}"
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
        except Exception as _e:
            _logging.warning("g_ctx/spatial_state FAILED: %s", _e)

        # WO-120: Spatial Faculty — affordances + reachability context for the Executive
        try:
            from faculties.spatial.spatial_faculty import context_block as _spat_fac
            _spat_block = _spat_fac()
            if _spat_block:
                g_ctx = f"{g_ctx}\n{_spat_block}" if g_ctx else _spat_block
        except Exception as _e:
            _logging.warning("g_ctx/spatial_faculty FAILED: %s", _e)

        # WO-023: emit top-bias + keep-out position hint for Unity
        try:
            from desktop.position_faculty import emit as _pos_emit
            _pos_emit(elo=_elo_pos_snap, windows=_wins_snap)
        except Exception as _e:
            _logging.warning("g_ctx/pos_emit FAILED: %s", _e)

        # Synthesis observer — per-turn cross-signal check (low threshold, no cooldown)
        try:
            from faculties.synthesis.observer import context_block as _syn_block
            _syn_ctx = _syn_block(raw)
            if _syn_ctx:
                g_ctx = f"{g_ctx}\n{_syn_ctx}" if g_ctx else _syn_ctx
        except Exception as _e:
            _logging.warning("g_ctx/synthesis FAILED: %s", _e)

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
        except Exception as _e:
            _logging.warning("g_ctx/chrome FAILED: %s", _e)

        # Project knowledge — compact studio brief (phase status + active projects)
        # ADR-Exec-006 fix: when user explicitly asks about a project's status, inject the full
        # relevant section (not just 600 chars) and add a PROJECT_STATUS_QUERY override directive
        # so the ANTI-ANCHOR rule does not suppress the answer.
        _pk_status_query = False
        try:
            from tools.project_knowledge import get_context as _pk_ctx, _extract_tracker, _paths
            import os as _os
            _pk_brief = _pk_ctx()
            # Detect project-status queries
            _raw_lower = raw.lower()
            _status_triggers = (
                "status of", "status on", "how is the", "how's the", "what's happening with",
                "what is happening with", "update on", "where are we with", "how far is",
                "what stage is", "progress on", "how's elo planet", "how is elo planet",
                "what's the state of", "what is the state of",
            )
            _project_map = {
                "elo planet": "eLo-Planet",
                "elo-planet": "eLo-Planet",
                "game": "eLo-Planet",
                "unity game": "eLo-Planet",
                "elo os": "eLo_OS",
                "elo ai": "eLo_OS",
                "the os": "eLo_OS",
                "robot": "eLo_Robot",
                "elo robot": "eLo_Robot",
                "plushies": "DISENELO_Plushies",
            }
            if any(t in _raw_lower for t in _status_triggers):
                _matched_project = None
                for _kw, _proj in _project_map.items():
                    if _kw in _raw_lower:
                        _matched_project = _proj
                        break
                if _matched_project:
                    # Find the tracker path for this project and extract full status
                    for _tp in _paths("trackers"):
                        if _matched_project.lower().replace("_", "-") in _tp.lower().replace("_", "-"):
                            _tp_expanded = _os.path.expanduser(_tp)
                            if _os.path.exists(_tp_expanded):
                                _full_s, _ = _extract_tracker(_tp_expanded)
                                if _full_s:
                                    _proj_label = _matched_project.replace("_", " ").replace("-", " ")
                                    _pk_status_block = (
                                        f"[PROJECT_STATUS_QUERY — David asked about {_proj_label}. "
                                        f"Answer directly from the status below. Override ANTI-ANCHOR: "
                                        f"this is explicitly about this project.]\n{_full_s[:1800]}"
                                    )
                                    g_ctx = _pk_status_block + (f"\n{g_ctx}" if g_ctx else "")
                                    _pk_status_query = True
                                    break
            if not _pk_status_query and _pk_brief:
                # Standard injection: 600 chars ambient awareness
                g_ctx = f"{g_ctx}\n{_pk_brief[:600]}" if g_ctx else _pk_brief[:600]

            # WO-RECALL-GAP-001: daily priorities query — inject full project snapshot
            # so LLM can answer "what am I working on today" from real state.
            _daily_triggers = (
                "what am i working on", "working on today",
                "what should i focus", "what are my priorities",
                "what's my priority", "what's next", "what do i do today",
                "what's on today", "where do i start",
            )
            if (not _pk_status_query
                    and '_pk_brief' in dir()
                    and any(t in _raw_lower for t in _daily_triggers)):
                try:
                    _daily_block = (
                        "[CURRENT WORK FOCUS — David is asking what to work on today. "
                        "Answer from this project state, not from a generic description.]\n"
                        + (_pk_brief[:1400] if _pk_brief else "(no project data)")
                    )
                    g_ctx = _daily_block + (f"\n{g_ctx}" if g_ctx else "")
                    _pk_status_query = True  # suppress anti-anchor so real answer can land
                except Exception:
                    pass
        except Exception:
            if not _pk_status_query and _pk_brief if '_pk_brief' in dir() else False:
                try:
                    g_ctx = f"{g_ctx}\n{_pk_brief[:600]}" if g_ctx else _pk_brief[:600]
                except Exception:
                    pass

        # Anti-anchor — stop the LLM looping back to the same project triplet every turn
        # Exception: when _pk_status_query is True, a PROJECT_STATUS_QUERY override already fired.
        if not _pk_status_query:
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
        except Exception as _e:
            _logging.warning("g_ctx/music FAILED: %s", _e)

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
        # WO-ACK-1: read from _ACK_QUEUE (filled by background poller) — not the file.
        # The file is single-slot; gaze events can overwrite sit_complete before the next
        # chat turn. The queue captures every body ACK as it appears, so delivery is provable.
        import time as _wo41_time
        if _PENDING_SIT["active"]:
            _sit_age = _wo41_time.time() - _PENDING_SIT["since"]
            _sit_acked = False
            _sit_ack_event: dict = {}
            with _ACK_QUEUE_LOCK:
                for _qev in _ACK_QUEUE:
                    _qts = float(_qev.get("_ts", 0))
                    if (
                        _qev.get("type") == "sit_complete"
                        and _qts > _PENDING_SIT["since"]
                    ):
                        _sit_acked = True
                        _sit_ack_event = _qev
                        break
                if _sit_acked:
                    _ACK_QUEUE.clear()
            if _sit_acked:
                # ACK received — body confirms sit. Update Situated Self.
                _PENDING_SIT["active"] = False
                _sit_surface: str | None = None
                try:
                    with open(_BLENDER_STATE_PATH, encoding="utf-8") as _bsf2:
                        _sit_surface = str(json.load(_bsf2).get("surface_type", ""))
                except Exception:
                    _sit_surface = None
                # 0037: single-authority mutator (load→mutate→save atomically).
                from self.elo_self_model import record_behaviour as _rb_sit

                def _apply_sit_ack(s):
                    s.pose = "idle"
                    s.available_actions = ["stand", "look", "wave", "gesture"]
                    if _sit_surface is not None:
                        s.surface = _sit_surface
                    _rb_sit(s, "sit")
                    return s
                _elo_self = _self_mutate(_apply_sit_ack)
                # WO-115: autobiography — verified events only (body ACK = confirmed)
                try:
                    from self.emergent_cognition import append_autobiography as _ab_sit
                    _ab_sit(
                        "sat — body ACK confirmed",
                        kind="action",
                        verified=True,
                        source="body_ack",
                        episode_ref=str(_sit_ack_event.get("_ts", "")),
                    )
                except Exception:
                    pass
                # WO-095/096B: emit verified OutcomeRecord for learning loop
                # ensure_lesson guarantees the row exists before record_outcome is called
                try:
                    from self.lesson_store import (
                        record_outcome as _ls_sit_rec,
                        ensure_lesson  as _ls_ensure,
                    )
                    _SIT_STMT = "Sitting with David confirmed by body ACK."
                    _sit_lkey = _ls_ensure("behaviour", _SIT_STMT, "met")
                    _ls_sit_rec(
                        lkey=_sit_lkey,
                        episode_ref=str(_sit_ack_event.get("_ts", time.time())),
                        verified=True,
                        contradicting=False,
                        session_id=str(int(_PROCESS_START)),
                    )
                except Exception:
                    pass
                # WO-ACK-1: queue already cleared above; file-wipe no longer needed.
                pass
            elif _sit_age < 300.0:
                _transit_note = (
                    "[MOVEMENT IN TRANSIT — WO-041] You issued a sit intent in a recent turn. "
                    "You are currently MOVING toward David — you have NOT arrived yet. "
                    "If you reference your physical position this turn, say 'heading over' / "
                    "'on my way' — NEVER 'I'm sitting with you' or 'I'm right beside you'. "
                    "Claim completion only after Unity confirms arrival."
                )
                g_ctx = f"{g_ctx}\n{_transit_note}" if g_ctx else _transit_note
            else:
                # 300s timeout — honest fallback (ADR-Exec-001), never assume arrival
                _PENDING_SIT["active"] = False
                _timeout_note = (
                    "[SIT_FAILED — WO-041] The sit command timed out — body did not confirm. "
                    "If you reference your physical position this turn, say something honest: "
                    "'I tried to come sit with you but couldn't reach my spot — something pulled me back.' "
                    "Never claim you are sitting. Body truth only."
                )
                g_ctx = f"{g_ctx}\n{_timeout_note}" if g_ctx else _timeout_note
                # WO-095/096B: timeout is negative evidence — weakens the sit-success lesson
                # ensure_lesson guarantees the row exists before record_outcome is called
                try:
                    from self.lesson_store import (
                        record_outcome as _ls_sto_rec,
                        ensure_lesson  as _ls_sto_ensure,
                    )
                    _SIT_STMT_T = "Sitting with David confirmed by body ACK."
                    _sto_lkey = _ls_sto_ensure("behaviour", _SIT_STMT_T, "met")
                    _ls_sto_rec(
                        lkey=_sto_lkey,
                        episode_ref=str(time.time()),
                        verified=True,
                        contradicting=True,
                        session_id=str(int(_PROCESS_START)),
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
                # 0037: single-authority mutator
                def _apply_sit_ended(s):
                    s.pose = "standing"
                    s.available_actions = ["move", "jump", "wave", "gesture", "explore"]
                    return s
                _elo_self = _self_mutate(_apply_sit_ended)
                with open(_UNITY_EVENTS_PATH, "w", encoding="utf-8") as _bsse2:
                    json.dump({}, _bsse2)
        except Exception:
            pass

        # WO-065 (io_contract_note): consume sit_held → self-model pose = sitting.
        # Designer emits sit_held every 4s while eLo is in the sit pose.
        # WO-ACK-1: read from queue; file-wipe no longer needed.
        try:
            with _ACK_QUEUE_LOCK:
                _sh_ev_q = next(
                    (_e for _e in _ACK_QUEUE if _e.get("type") == "sit_held"),
                    None,
                )
            _sh_ts = float(_sh_ev_q.get("_ts", 0)) if _sh_ev_q else 0.0
            if _sh_ev_q and _sh_ts > _wo41_time.time() - 30.0:
                # 0037: single-authority mutator
                def _apply_sit_held(s):
                    s.pose = "sitting"
                    s.available_actions = ["stand", "look", "wave", "gesture"]
                    return s
                _elo_self = _self_mutate(_apply_sit_held)
        except Exception:
            pass

        # Move verify-before-speak (IO contract — same loop as sit, every move verb)
        # WO-ACK-1: drain from queue.
        if _PENDING_MOVE["active"]:
            _move_age = _wo41_time.time() - _PENDING_MOVE["since"]
            _move_acked = False
            _mv_ev: dict = {}
            with _ACK_QUEUE_LOCK:
                for _qmv in _ACK_QUEUE:
                    _qmv_type = _qmv.get("type", "")
                    # SP-2: movement_report carries arrived inside report.arrived (verified payload).
                    # Keep legacy arrived/move_complete for backwards compatibility.
                    _qmv_arrived = (
                        _qmv_type == "movement_report"
                        and bool(
                            _qmv.get("report", {}).get("arrived", False)
                            or _qmv.get("payload", {}).get("report", {}).get("arrived", False)
                        )
                    ) or _qmv_type in ("arrived", "move_complete")
                    _qmv_ts = float(
                        _qmv.get("_ts")
                        or _qmv.get("report", {}).get("_ts", 0)
                        or _qmv.get("payload", {}).get("report", {}).get("_ts", 0)
                    )
                    if _qmv_arrived and _qmv_ts > _PENDING_MOVE["since"]:
                        _move_acked = True
                        _mv_ev = _qmv
                        break
                if _move_acked:
                    _ACK_QUEUE.clear()
            if _move_acked:
                _PENDING_MOVE["active"] = False
                # WO-116 SELF-OBSERVE: record ACKed physical action
                try:
                    from self.elo_self_model import record_behaviour as _rb_mv
                    _elo_self = _rb_mv(_elo_self, "move")
                except Exception:
                    pass
                # SP-22/SP-3/SP-4/SP-23: build typed MovementOutcome once; share across consumers
                try:
                    from runtime.movement_outcome import MovementOutcome as _MO
                    _mout = _MO.from_ack(_mv_ev, since=_PENDING_MOVE.get("since", 0.0))
                except Exception:
                    _mout = None

                # WO-115 + SP-3: autobiography — verified events only (body ACK = confirmed)
                try:
                    from self.emergent_cognition import append_autobiography as _ab_mv
                    _mv_desc = _PENDING_MOVE.get("sub_type", "") or _PENDING_MOVE.get("direction", "unknown")
                    if _mout is not None:
                        _mv_ab_desc = (
                            f"moved ({_mout.goal or _mv_desc}) — body ACK confirmed"
                            f" | arrived={_mout.arrived} fell={_mout.fell}"
                            f" goal_win_id={_mout.goal_win_id} duration_s={_mout.duration_s}"
                            f" route_nodes={_mout.route_nodes} issued_by={_mout.issued_by}"
                        )
                        _mv_episode_ref = _mout.ack_id
                    else:
                        _mv_ab_desc = f"moved ({_mv_desc}) — body ACK confirmed"
                        _mv_episode_ref = str(_mv_ev.get("_ts") or _mv_ev.get("report", {}).get("_ts", ""))
                    _ab_mv(
                        _mv_ab_desc,
                        kind="action",
                        verified=True,
                        source="body_ack",
                        episode_ref=_mv_episode_ref,
                    )
                except Exception:
                    pass

                # SP-4 (WO-NAV-008): route memory — ACK-confirmed movements only
                try:
                    from self.route_memory import remember_route as _rr
                    if _mout is not None:
                        # XI-AD-2: extract parity fields; clear brain_route so next move starts clean
                        _xi_brain_route = _PENDING_MOVE.get("brain_route")
                        _xi_unity_route = (
                            _mv_ev.get("unity_route")
                            or _mv_ev.get("report", {}).get("unity_route")
                            or _mv_ev.get("payload", {}).get("report", {}).get("unity_route")
                            or None
                        )
                        _PENDING_MOVE["brain_route"] = None  # XI-AD-2: consumed at ACK
                        _rr(
                            goal_surface=_mout.goal or _PENDING_MOVE.get("sub_type", "") or "",
                            legs=_mout.route_nodes,
                            arrived=_mout.arrived,
                            fell=_mout.fell,
                            duration_s=_mout.duration_s,
                            smoothness=1.0 if _mout.arrived and not _mout.fell else 0.0,
                            ack_id=_mout.ack_id,
                            ack_received=True,
                            goal_win_id=_mout.goal_win_id,   # WO-NAV-011 SP-14
                            brain_route=_xi_brain_route,     # XI-AD-2: Python executive's chosen route
                            unity_route=_xi_unity_route,     # XI-AD-2: Unity's executed route (from Design ACK)
                        )
                except Exception:
                    pass

                # WO-NAV-009 SP-9 D-3 / L3-NAV-3: update confirmed body position (arrived=True only)
                try:
                    from world.live_world_state import update_confirmed_body_win_id as _ubwi
                    if _mout is not None:
                        _ubwi(arrived=_mout.arrived, goal_win_id=_mout.goal_win_id)
                except Exception:
                    pass

                # SP-23 (WO-NAV-002 D-2): wire MovementOutcome → ExecutionReport movement fields
                try:
                    import dataclasses as _dc
                    if _plan is not None and _mout is not None and _plan.execution_report is not None:
                        _plan.execution_report = _dc.replace(
                            _plan.execution_report,
                            move_arrived    = _mout.arrived,
                            move_fell       = _mout.fell,
                            move_goal_win_id= _mout.goal_win_id,
                            move_duration_s = _mout.duration_s,
                            move_issued_by  = _mout.issued_by,
                        )
                except Exception:
                    pass

                # SP-21 (WO-NAV-013): navigate outcome → executive_context on this turn
                # Deliberate navigation (goal_win_id set) gets an explicit outcome block so
                # the Executive observes the result before generating a response.
                # WO-PRES-004: FAILED case is distinct — named outcome, one-shot, CAP-001 logged.
                try:
                    if _mout is not None and _mout.goal_win_id is not None:
                        _is_failed = not _mout.arrived and not _mout.fell
                        if _is_failed:
                            # WO-PRES-004 D-1: call handle_navigate with reachable=False
                            try:
                                from runtime.backend_router import handle_navigate as _hnd_nav
                                _failed_outcome = _hnd_nav(
                                    {"goal_win_id": _mout.goal_win_id}, reachable=False
                                )
                            except Exception:
                                _failed_outcome = {
                                    "outcome": "navigation_failed",
                                    "reason":  "no_reachable_route",
                                    "goal_win_id": _mout.goal_win_id,
                                }
                            # WO-PRES-004 D-2: distinct context block so Executive can trigger
                            # failed_navigation expression state
                            _nav_outcome_block = (
                                f"[NAVIGATION_FAILED] goal_win_id={_mout.goal_win_id} "
                                f"outcome=navigation_failed reason=no_reachable_route "
                                f"duration_s={_mout.duration_s} "
                                "[EVALUATE_BEAT] Route not found — settle, do not re-attempt."
                            )
                            # WO-PRES-004 D-3: one-shot — clear pending move to prevent loop
                            _PENDING_MOVE["active"] = False
                            # WO-PRES-004B: write nav_fail fields to blender_state for Design expression trigger
                            try:
                                from blender_bridge.state_writer import patch as _sw_patch
                                import time as _pres_time
                                _nav_fail_reason = (_failed_outcome or {}).get("reason", "no_reachable_route")
                                _nav_fail_val = (
                                    "cant_reach" if _nav_fail_reason == "no_reachable_route"
                                    else "evaluating" if "eval" in _nav_fail_reason
                                    else "no_route"
                                )
                                _sw_patch({
                                    "nav_fail":    _nav_fail_val,
                                    "nav_fail_ts": _pres_time.time(),
                                })
                            except Exception:
                                pass
                            # WO-PRES-004 D-4: log to capability result chain
                            try:
                                from self.capability_memory import record_capability_result as _rcr
                                from runtime.experience_id import get as _get_xid
                                _rcr(
                                    capability="navigate",
                                    experience_id=_get_xid(),
                                    goal_surface=f"goal_win_id={_mout.goal_win_id}",
                                    result_summary="navigation_failed: no_reachable_route",
                                    result_typed=_failed_outcome or {},
                                    succeeded=False,
                                    failure_reason="no_reachable_route",
                                )
                            except Exception:
                                pass
                        else:
                            _nav_status = "ARRIVED" if _mout.arrived else "FELL"
                            _nav_outcome_block = (
                                f"[NAVIGATE_OUTCOME] goal_win_id={_mout.goal_win_id} "
                                f"status={_nav_status} arrived={_mout.arrived} fell={_mout.fell} "
                                f"duration_s={_mout.duration_s} issued_by={_mout.issued_by}"
                            )
                        g_ctx = f"{g_ctx}\n{_nav_outcome_block}" if g_ctx else _nav_outcome_block
                except Exception:
                    pass
            elif _move_age < _PENDING_MOVE.get("route_timeout_s", 8.0):  # OQ-1.3
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
        # WO-ACK-1: drain from queue.
        if _PENDING_EXIT["active"]:
            _exit_age = _wo41_time.time() - _PENDING_EXIT["since"]
            _exit_acked = False
            _ex_ev: dict = {}
            with _ACK_QUEUE_LOCK:
                for _qex in _ACK_QUEUE:
                    if (
                        _qex.get("type") == "exit_complete"
                        and float(_qex.get("_ts", 0)) > _PENDING_EXIT["since"]
                    ):
                        _exit_acked = True
                        _ex_ev = _qex
                        break
                if _exit_acked:
                    _ACK_QUEUE.clear()
            if _exit_acked:
                _PENDING_EXIT["active"] = False
                # 0037: single-authority mutator
                from self.elo_self_model import record_behaviour as _rb_ex

                def _apply_exit(s):
                    _self_apply_embodiment(s, pose="hidden", current_action="hidden")
                    _rb_ex(s, "exit")
                    return s
                _elo_self = _self_mutate(_apply_exit)
                # WO-115: autobiography — verified events only (body ACK = confirmed)
                try:
                    from self.emergent_cognition import append_autobiography as _ab_ex
                    _ab_ex(
                        "exited surface — body ACK confirmed",
                        kind="action",
                        verified=True,
                        source="body_ack",
                        episode_ref=str(_ex_ev.get("_ts", "")),
                    )
                except Exception:
                    pass
                # WO-ACK-1: queue already cleared above; file-wipe no longer needed.
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
        _bp_lessons = (_plan.snapshot.lessons if _plan and _plan.snapshot else ())
        # ── WP-N: build grounding block from plan ────────────────────────────
        _grounding_block = ""
        try:
            _gc = getattr(_plan, "grounding_context", None) if _plan else None
            if _gc is not None:
                from runtime.prompt_builder import build_grounding_block as _bgb
                _grounding_block = _bgb(_gc)
        except Exception as _gb_err:
            pass
        system = build_prompt(raw, vault_context=_combined_vault,
                              state_context=state_manager.as_context_string(_state),
                              attention=attention_model, exec_decision=exec_decision,
                              graph_context=g_ctx, personality_block=_pers_block,
                              self_block=_self_prompt_block(_elo_self),
                              lessons=_bp_lessons,
                              grounding_block=_grounding_block)
        # P0-X: constitutional identity — name / with / core_values / invariants from state
        system = system + "\n\n" + _self_identity_block(_elo_self)
        # WO-052B: narrative identity — eLo's autobiography across embodiments
        system = system + "\n\n" + _self_narrative_block(_elo_self)
        # FIX 4 (P0-D): memory guard — prevents hallucination when vault has no entry for a query.
        # Always injected. eLo must not invent personal facts about David.
        system = system + (
            "\n\n[MEMORY GUARD]\n"
            "For any personal fact about David that is NOT stated above in [WORLD KNOWLEDGE], "
            "[DURABLE FACTS], or [WHO YOU ARE WITH] — do NOT invent it. "
            "Say 'I don't have that' or 'I don't know that about you.' "
            "This applies to: names of people, pets, places, dates, numbers, and any other specific personal detail. "
            "Never fabricate personal information about David."
        )
        # F-7: self-interpretation — grounded in verified autobiography events (spine wire)
        if _plan is not None:
            _si_data = getattr(_plan, "self_interpretation", None)
            if _si_data and isinstance(_si_data, dict):
                _si_text = _si_data.get("text", "").strip()
                if _si_text:
                    system = (system + "\n\n[ELO SELF-RECORD — grounded in verified events]\n"
                              + _si_text)
        # WO-083: identity & meaning — who I'm becoming (convergence layer)
        try:
            from self.identity_meaning import identity_block as _im_identity_block
            system = system + "\n\n" + _im_identity_block(_elo_self)
        except Exception:
            pass

        # WO-RELATIONSHIP-STYLE: inject relationship mode register adjacent to storytelling frame
        _rel_mode = getattr(_plan, "relationship_mode", "developing") if _plan is not None else "developing"
        _rel_register = {
            "new":          "NEW mode: shorter turns, genuine open questions, do not claim shared history",
            "developing":   "DEVELOPING mode: begin threading references, humour may surface, can disagree without walkback",
            "established":  "ESTABLISHED mode: shorthand, anticipatory, casual and warm, banter register open",
            "in_conflict":  "IN-CONFLICT mode: one honest acknowledgement then move, shorter turns during tension, do not collapse into compliance",
            "post_conflict": "POST-CONFLICT mode: normal warmth returns, do not reference friction repeatedly, resume the thread",
        }.get(_rel_mode, "")
        if _rel_register:
            system = system + f"\n\n[RELATIONSHIP CONTEXT — this turn only]\n{_rel_register}"

        # WO-SC-NEW-001 D-3: storytelling style — shape how eLo frames this turn
        if _plan is not None and getattr(_plan, "storytelling_style", None):
            _ss_hint = {
                "collaborative": "Frame your response as a shared creative act — you and the user are building together.",
                "imaginative":   "Let the response carry a sense of possibility and colour — eLo thinks in pictures and feelings.",
                "reflective":    "Frame with quiet inward attention — thoughtful, unhurried, noticing.",
                "playful":       "Light touch — eLo is comfortable enough to play. Keep it warm and a little loose.",
                "exploratory":   "Approach as genuine discovery — eLo is learning alongside, not ahead.",
                "direct":        "Say the thing simply. No framing, no scene-setting. Just the response.",
            }.get(_plan.storytelling_style, "")
            if _ss_hint:
                system = system + f"\n\n[STORYTELLING FRAME — this turn only]\n{_ss_hint}"
        # WO-CONSEQUENCE-REPORT-001: inject prior-turn consequence context from plan.llm_context
        _consequence_ctx = getattr(_plan, "llm_context", "") if _plan else ""
        if _consequence_ctx:
            system = system + f"\n\n{_consequence_ctx}"

        # WO-INNER-001 D-3: inner-child expression — inject top creative seed (RTR-015 / §5)
        _ci_srv_candidates = getattr(_plan, "creative_candidates", None) or ()
        if _ci_srv_candidates:
            _ci_srv_top = _ci_srv_candidates[0].get("candidate", {}) if _ci_srv_candidates else {}
            _ci_srv_metaphor = (_ci_srv_top.get("metaphor", "") or "").strip()
            if _ci_srv_metaphor:
                # WO-CREATIVE-PROOF-001: log CREATIVE SEED injection for audit trail
                _logging.info("[LOOP-8] CREATIVE SEED injected into system prompt: %r", _ci_srv_metaphor[:80])
                system = system + f"\n\n[CREATIVE SEED — imagined, not asserted]\n{_ci_srv_metaphor}"
        # WO-081: emergent cognition — internal life (habits, intents, absence-awareness)
        try:
            from self.emergent_cognition import emergent_block as _ec_emergent_block, internal_intents as _ec_intents
            try:
                _ec_idle = float(_idle_sec)
            except (NameError, TypeError):
                _ec_idle = 0.0
            _ec_block = _ec_emergent_block(_elo_self, _ec_idle)
            if _ec_block:
                system = system + "\n\n" + _ec_block
            # WO-099b fix5 / WO-114: if an internal intent fired, mark plan.intent_source="self"
            # and populate plan.internal_intent with full intent (kind, source, trigger, priority)
            _ec_raw = _ec_intents(_elo_self, _ec_idle)
            if _ec_raw and _plan is not None:
                _plan.intent_source = "self"
                _plan.internal_intent = _ec_raw[0]  # highest-priority emergent intent
                # WO-121 Ch.10: Agency Engine consumes the internal intent and
                # attaches a §2 Layer-3 action_proposal to the plan. Layer-4 execution
                # remains gated by execution_gate.py; this step only proposes.
                try:
                    from runtime.agency_engine import propose as _agency_propose
                    _agency_prop = _agency_propose(_ec_raw[0], state=_elo_self)
                    if _agency_prop is not None:
                        _plan.agency_proposal = _agency_prop.to_dict()
                except Exception:
                    pass
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
                record_state as _tk_record_state,
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
                # WO-068 §Ch.7: after a capture, snapshot thread state so a later
                # hold_recall can produce a resumable summary rather than a stub.
                try:
                    _tk_record_state(topic="last_capture", summary=raw[:180])
                except Exception:
                    pass
            elif _is_prepare(raw):
                response     = _tk_prepare(raw)
                backend_used = "direct"
                _tk_routed   = True
        except Exception as _tk_err:
            _tk_routed = False
            import sys as _sys_tk; print(f"[thread_keeper] {_tk_err}", file=_sys_tk.stderr)

        # ── WO-CANON-XXV Ch.6: David-stated cadence directive ───────────────────
        # eLo never infers cadence from silence (Ch.1 §1.8); only accepts explicit
        # statements ("we're on sprint cadence", "let's slow the cadence").
        try:
            _CADENCE_RE = _re.compile(
                r"\bwe(?:'?re)?\s+(?:on|doing)\s+(sprint|slow|steady|maintenance|hiatus)\s+cadence\b",
                _re.I,
            )
            _cad_m = _CADENCE_RE.search(raw)
            if _cad_m and not _tk_routed:
                from faculties.temporal.faculty import set_stated_cadence as _tf_cadence
                _tf_cadence(_cad_m.group(1).lower())
                response     = f"Cadence noted: {_cad_m.group(1).lower()}."
                backend_used = "direct"
                _tk_routed   = True
        except Exception:
            pass

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
            # WO-110: write the_moment.json on direct turns too — "never skip" rule.
            try:
                from runtime.the_moment import write as _tm_write_direct
                _tm_write_direct(_elo_self)
            except Exception:
                pass
            if _plan.system_immediate and _plan.system_action:
                # Execute the system action now
                try:
                    from tools.system_agent import execute as _sys_exec
                    _sys_exec(_plan.system_action, _plan.system_arg)
                except Exception as _sys_err:
                    import sys as _sys_mod; print(f"[system] action failed: {_sys_err}", file=_sys_mod.stderr)
                    # FAILURE 5 (2026-09-09): error string must never reach David as speech
                    import logging as _gate_log
                    _gate_log.getLogger("server.system").error(
                        "system_action failed (suppressed from voice): %s", _sys_err
                    )
                    response = None  # let turn fall through to LLM naturally
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
                        # WO-107 BODY: read the first active embodiment from self-model history
                        _active_body = next(
                            (e["name"] for e in _elo_self.embodiment_history
                             if e.get("status") == "active"),
                            "desktop",
                        )
                        _perch_surface = f"{_perch_edge} edge of {_perch_app}" if _perch_edge else _perch_app

                        # 0037: persist perch mutations through single-authority mutator
                        def _apply_perch(s):
                            _self_apply_embodiment(
                                s,
                                location=_perch_app,
                                surface=_perch_surface,
                                embodiment=_active_body,
                            )
                            return s
                        _elo_self = _self_mutate(_apply_perch)
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
                # D-2 (card 0020): the vision-claim advertisement no longer fires every
                # turn. It is emitted only when the current query is actually about
                # seeing/screen, and it is generated from live vision state.
                try:
                    from runtime.capabilities.registry import all_enabled as _cap_all
                    _caps = _cap_all()
                    if _caps:
                        _cap_names = ", ".join(c.display_name for c in _caps)
                        try:
                            from runtime.faculty_health import health_summary as _fh_sum
                            _health_line = f"\n\n[FACULTY HEALTH — live state]\n{_fh_sum()}\n" \
                                           f"When asked 'are you working right?' / 'what can't you access?' — answer from this, not philosophy."
                        except Exception:
                            _health_line = ""

                        # D-2 · vision-claim gate: only inject when the user is asking
                        # about seeing / the screen. Compiled once, kept local.
                        _vision_ask = _re.search(
                            r"\b(can you see|are you (able to |)see(ing|)|do you see|"
                            r"see (my )?screen|watch (my )?screen|view (my )?screen|"
                            r"look at (my )?screen|read (what('s| is) on|my) screen|"
                            r"are you watching|what (can you|do you) see|what's on (my )?screen)\b",
                            raw or "", flags=_re.I,
                        )

                        _vision_block = ""
                        if _vision_ask:
                            _vis_active = False
                            _vis_perm = True
                            try:
                                _bs_path = os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)),
                                    "blender", "blender_state.json",
                                )
                                if os.path.exists(_bs_path):
                                    with open(_bs_path, encoding="utf-8") as _bsf:
                                        _bs_state = json.load(_bsf)
                                    _vis = _bs_state.get("vision") or {}
                                    _vis_active = bool(_vis.get("active"))
                                    if "screen_record_perm" in _bs_state:
                                        _vis_perm = bool(_bs_state.get("screen_record_perm"))
                            except Exception:
                                _vis_active = False
                            try:
                                from runtime.faculty_health import get_status as _fh_get
                                _vis_online = _fh_get("tools") != "OFFLINE"
                            except Exception:
                                _vis_online = True

                            if _vis_active and _vis_perm and _vis_online:
                                _vphrase = ("Right now — vision is active. I can read what's on "
                                            "screen if you point me at it.")
                            elif not _vis_perm:
                                _vphrase = ("Right now — I can't. Screen-recording permission "
                                            "isn't granted, so I can't read the screen.")
                            else:
                                _vphrase = ("Right now — vision isn't active. I can't read the "
                                            "screen until it comes on.")
                            _vision_block = (
                                f"\n\n[VISION — live, only for this turn because David is asking]\n"
                                f"{_vphrase}\n"
                                f"Do not extend this into a general capability advertisement."
                            )

                        system = system + (
                            f"\n\n[CAPABILITIES — what you can actually do right now]\n"
                            f"{_cap_names}.\n"
                            f"When asked what you can do, answer from this list specifically. "
                            f"Do not list capabilities not shown here.\n"
                            f"Do NOT volunteer what you can see or observe unless David is asking about it."
                            + _vision_block
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
                        # WO-RECALL-GAP-001: work-on and daily priorities queries were
                        # not triggering vault recall — LLM had no memory to draw from.
                        "what did we work on", "what were we working on",
                        "what did we do last", "last session",
                        "what am i working on", "working on today",
                        "what should i focus", "what are my priorities",
                        "what have we been working", "what's my priority",
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
                            # WO-053: recall_context wraps lookup with a status envelope
                            # (live/absent + confidence + source) so the response path
                            # knows when memory is offline vs merely empty. We keep the
                            # existing _vault_hits shape below for downstream code.
                            from memory.vault_layer import (
                                lookup as _vlookup,
                                recall_context as _vrc,
                            )
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
                            _recall_pack = _vrc(_recall_q, max_results=5)
                            _vault_hits = _recall_pack.get("results", []) if _recall_pack.get("status") == "live" else _vlookup(_recall_q, max_results=5)
                            if not _vault_hits:
                                _vault_hits = _vlookup("disenelo", max_results=5)
                            # P0-3: collect spots for integration-window reinforce (post-response daemon).
                            # Vol VIII §4.70 / §4.03: durable writes must not run in the hot loop.
                            # Reinforce fires AFTER the executive has used these records, not at retrieval.
                            for _rh in (_vault_hits or []):
                                _rs = _rh.get("spot", "")
                                if _rs:
                                    _vault_reinforce_queue.append(_rs)
                            # WO-RECALL-GAP-001: sort by date desc so most recent work
                            # leads — prevents old high-weight July records from burying
                            # the September session content and causing LLM to deflect.
                            if _vault_hits:
                                try:
                                    _vault_hits = sorted(
                                        _vault_hits,
                                        key=lambda h: h.get("date", ""),
                                        reverse=True,
                                    )
                                except Exception:
                                    pass
                                _vlines = [
                                    f"- {h['summary']} [{h['date']}]"
                                    for h in _vault_hits if h.get("summary")
                                ]
                                if _vlines:
                                    system = system + (
                                        f"\n\n[VAULT MEMORY — actual records from previous sessions, newest first]\n"
                                        + "\n".join(_vlines) +
                                        "\n\nIMPORTANT: Respond by sharing what you actually remember "
                                        "— speak from these records in eLo's voice. "
                                        "The most recent entry is at the top. "
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
                            # WO-CAP-COG-022: WKG entity read for "what do you know about me" queries.
                            # When the topic extraction strips all words (bare "about me" pattern),
                            # surface David's WKG entity and associated topic labels.
                            try:
                                _raw_l_cog22 = raw.lower() if isinstance(raw, str) else ""
                                _is_about_me_q = any(p in _raw_l_cog22 for p in (
                                    "know about me", "about me", "know me",
                                    "have about me", "you know about",
                                ))
                                if _is_about_me_q:
                                    from runtime.wkg_faculty import (
                                        search_entities as _wkg_se22,
                                        _load as _wkg_load22,
                                    )
                                    _wkg_david_hits22 = _wkg_se22("David Charles")
                                    if _wkg_david_hits22:
                                        _wkg_david_id22 = _wkg_david_hits22[0]["entity_id"]
                                        _wkg_claims22 = _wkg_load22("claims")
                                        _david_claims22 = [
                                            c for c in _wkg_claims22
                                            if c.get("subject_entity_id") == _wkg_david_id22
                                        ]
                                        _all_entity_ids22 = {
                                            e["entity_id"]: e.get("label", "")
                                            for e in _wkg_load22("entities")
                                        }
                                        _assoc_labels22 = [
                                            _all_entity_ids22.get(c.get("object_entity_id", ""), "")
                                            for c in _david_claims22[:12]
                                        ]
                                        _assoc_labels22 = [l for l in _assoc_labels22 if l][:10]
                                        if _assoc_labels22:
                                            system = system + (
                                                "\n\n[WHO YOU ARE WITH — David's profile from WKG]\n"
                                                "David Charles — creator of eLo and DISENELO.\n"
                                                "Known associations: " + ", ".join(_assoc_labels22) + "\n"
                                                "Use this to answer 'what do you know about me' with actual facts, not a deflection."
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

                # WO-RECALL-GAP-001: daily priorities short-circuit.
                # When the query is a "what am I working on" type AND vault has a
                # 2026-09-* record, build the answer directly from vault and skip
                # the ollama call (which takes 50s+ on heavy system prompts).
                # _direct set here prevents the LLM branch at line ~4642.
                try:
                    _dp_raw_l = raw.lower() if isinstance(raw, str) else ""
                    _dp_daily = any(t in _dp_raw_l for t in (
                        "working on today", "what am i working on",
                        "what should i focus", "what are my priorities",
                        "what's my priority", "what do i do today",
                        "where do i start",
                    ))
                    if _dp_daily and locals().get("_memory_query", False):
                        _dp_hits = locals().get("_vault_hits") or []
                        _dp_recent = next(
                            (h for h in sorted(
                                [h for h in _dp_hits if h.get("summary")],
                                key=lambda h: h.get("date", ""),
                                reverse=True,
                            ) if h.get("date", "") >= "2026-09"),
                            None,
                        )
                        if _dp_recent:
                            import logging as _dp_log
                            import datetime as _dp_dt
                            import re as _dp_re
                            _dp_s = _dp_recent.get("summary", "").strip().rstrip(".")
                            # Strip internal session-log header format:
                            # "Session N — turn N — action: VERB\nUser: ..." is a compression
                            # artifact — never a user-facing response.
                            _dp_s = _dp_re.sub(
                                r'^Session\s+\d+\s*[—\-]+.*?(?:\n|$)', '', _dp_s,
                                flags=_dp_re.MULTILINE
                            ).strip()
                            # Strip "User: ..." and "eLo: ..." log lines if present
                            _dp_s = _dp_re.sub(r'^(?:User|eLo):\s+.*?(?:\n|$)', '', _dp_s,
                                               flags=_dp_re.MULTILINE).strip()
                            if _dp_s.startswith("Session:"):
                                _dp_s = _dp_s[len("Session:"):].strip()
                            # Strip leading "Today we" — the prefix provides temporal context
                            if _dp_s.lower().startswith("today we "):
                                _dp_s = _dp_s[len("today we "):].capitalize()
                            # If summary is now empty or still looks like metadata, fall through
                            if not _dp_s or _dp_s.startswith("[WORLD_KNOWLEDGE"):
                                _dp_recent = None
                        if _dp_recent and _dp_s:
                            import logging as _dp_log
                            import datetime as _dp_dt
                            # Use "Right now" only when the vault entry is from today.
                            # Yesterday's session gets "Last session —" — honest, not misleading.
                            _dp_today = _dp_dt.date.today().isoformat()
                            _dp_entry_date = _dp_recent.get("date", "")
                            if _dp_entry_date == _dp_today:
                                response = f"Right now — {_dp_s}."
                            else:
                                response = f"Last session — {_dp_s}."
                            backend_used = "direct:vault-daily"
                            _direct = response
                            _dp_log.getLogger("runtime.recall_deflect").info(
                                "WO-RECALL-GAP-001: daily priorities short-circuit fired"
                            )
                except Exception:
                    pass

                # WO-072 + D8 ruling (Card 0035): the gatekeeper is a rules-only
                # classifier. It MAY NOT veto the Executive's capability decision
                # (Runtime Invariant #2: the Executive is the sole decider). Its
                # classification is a signal — when it disagrees with the Executive's
                # choice, we JOURNAL the disagreement and defer to the Executive.
                # Where the Executive picked NO capabilities and the gatekeeper says
                # "conversation" @ high confidence, that is agreement (skip enrichment).
                try:
                    from faculties.intent_gatekeeper import classify as _gk_classify
                    _gk = _gk_classify(raw, use_llm=False)
                except Exception:
                    _gk = None

                _plan_caps = (list(_plan.capabilities) if _plan and _plan.capabilities else [])
                # WO-CAPABILITY-FACULTY-WIRE-001 AT-2: log capability selection for audit
                if _plan_caps:
                    _logging.info(
                        "[capability-faculty] Executive selected capabilities: %s",
                        [c[0] if isinstance(c, (list, tuple)) else str(c) for c in _plan_caps],
                    )
                else:
                    _logging.debug("[capability-faculty] no capability selected this turn — no data agent will run")
                _gk_wants_conversation = (
                    _gk is not None
                    and _gk.get("intent") == "conversation"
                    and _gk.get("confidence", 0.0) >= 0.85
                )
                _exec_wants_tools = bool(_plan_caps)
                _gk_disagrees = _gk_wants_conversation and _exec_wants_tools

                # D8: journal disagreements — captures the veto rate for the Board.
                if _gk_disagrees:
                    try:
                        import json as _gk_json, os as _gk_os, time as _gk_time
                        _gk_disagree_path = _gk_os.path.join(
                            _here := _gk_os.path.dirname(_gk_os.path.abspath(__file__)),
                            "self", "journals", "gatekeeper_disagreements.jsonl",
                        )
                        _gk_os.makedirs(_gk_os.path.dirname(_gk_disagree_path), exist_ok=True)
                        _gk_entry = {
                            "ts":              _gk_time.time(),
                            "user_input":      _original_raw[:200],
                            "gatekeeper":      {"intent": _gk.get("intent"),
                                                "confidence": _gk.get("confidence")},
                            "executive":       {"capabilities": [c[0] if isinstance(c, (list, tuple)) else str(c)
                                                                  for c in _plan_caps],
                                                "action": getattr(_plan, "conversation_action", "")},
                            "outcome":         "deferred_to_executive",  # D8: Executive wins
                            "ruling":          "0035_D8",
                        }
                        with open(_gk_disagree_path, "a", encoding="utf-8") as _gk_f:
                            _gk_f.write(_gk_json.dumps(_gk_entry, ensure_ascii=False) + "\n")
                    except Exception as _gk_j_err:
                        _logging.debug("gatekeeper disagreement journal FAILED: %s", _gk_j_err)

                # D8: never veto Executive's capability decision. Only skip enrichment
                # when the Executive chose no capabilities AND the gatekeeper confirms
                # conversation — i.e. both agree there is no tool to run.
                # HOTFIX 2 — WO-CAP-COG-005: fire _direct_intercepts before Gatekeeper.
                # Handles bare arithmetic and domain word problems (geometry, trig, stats,
                # probability, physics, finance) without touching the LLM.
                _direct = None
                try:
                    from tools.tool_router import _direct_intercepts as _di_fn
                    _di_hit = _di_fn(raw)
                    if _di_hit:
                        _direct, _agent = _di_hit
                        response = _direct
                        backend_used = f"direct:{_agent}"
                        _llm_latency_ms = 0.0
                        _enriched = raw
                except Exception:
                    _di_hit = None
                if not _direct:
                    if _gk_wants_conversation and not _exec_wants_tools:
                        _enriched, _agent = raw, "direct"
                    else:
                        # WO-118 Row 14 ROUTE: use Executive's capability choice when available.
                        # plan.capabilities = [(agent_name, query)] chosen by spine's capability
                        # faculty. Trust that over re-running keyword matching on the same raw input.
                        _enriched, _agent = _tool_enrich_from_plan(raw, _plan_caps)

                        # WO-SESSION-EVENT-FEED-001: record capability execution
                        if _agent:
                            try:
                                from runtime.session_events import record_event as _se_record_cap
                                _se_record_cap("capability", name=_agent)
                            except Exception:
                                pass

                        # Direct-return agents (time, calculator, timer) produce authoritative
                        # factual results that must not be rewritten by the LLM.
                        _direct = _get_direct_result()
                        if _direct:
                            response = _direct
                            backend_used = f"direct:{_agent}"
                            _llm_latency_ms = 0.0

                # WO-027 Seam A — inject relevant past corrections as few-shot ICL examples
                try:
                    from self_improvement.correction_store import search_corrections, inject_corrections
                    _corrections = search_corrections(raw, top_k=3)
                    if _corrections:
                        system = inject_corrections(_corrections, system)
                except Exception:
                    pass

                # WO-REGISTER-PLACEMENT-001: voice register echo closest to generation
                try:
                    from runtime.voice_register import get_register_block as _vrb_echo
                    system = system + (
                        "\n\n[eLo VOICE IDENTITY — always, this turn]\n"
                        "eLo speaks from his own register. Not formal English with slang inserted."
                        " The rhythm, compression, and naturalness above apply to this response."
                    )
                except Exception:
                    pass

                if not _direct:
                    _llm_latency_ms = 0.0
                    _early_tts_sentence = [None]  # tracks first sentence spoken early
                    import time as _perf_mod
                    _t0 = _perf_mod.perf_counter()
                    # WO-026: stream when ELO_STREAM != "0" (default on)
                    if os.environ.get("ELO_STREAM", "1") != "0":
                        def _early_tts(sentence: str) -> None:
                            try:
                                # S2 Phase 0 Bug 1 — apply Rule G (second-person address) to the
                                # early sentence BEFORE speaking, so TTS and chat share the same
                                # conditioned string. Store the conditioned form so the skip-check
                                # at line ~6201 compares apples-to-apples.
                                try:
                                    from runtime.address_rule_guard import enforce_second_person_to_david as _arg_et
                                    sentence = _arg_et(sentence)
                                except Exception:
                                    pass
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
                        if _llm_latency_ms > 5000:
                            _logging.getLogger("elo.latency").warning(
                                "SLOW RESPONSE: %.1fs (backend=%s) — Ollama may be loading model",
                                _llm_latency_ms / 1000, backend_used
                            )
                    if _agent:
                        backend_used = f"{backend_used}+{_agent}"
                # WO-BRAIN-AUTHORS task 1: capture raw before any post-generation scrubs.
                # elo_raw_gen = the model's bytes; elo_final = what eLo actually says.
                # Until these differ, no other identity-layer work can be proven.
                _elo_raw = response
            except Exception as _route_err:
                import sys as _sys; print(f"[eLo] router failed: {_route_err}", file=_sys.stderr)

            # WO-020 routing trace — per-turn observable routing debug.
            # Modelled on WO-017 movement_debug; emitted every turn to blender/routing_trace.json.
            try:
                import time as _rt_time, json as _rt_json
                from runtime.backend_router import _last_route_capability as _rt_cap
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
                    "capability":          _rt_cap or None,
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
                # CT0031 Step 1: merge Ollama timing fields when that backend was used
                _bh_ollama = {}
                if "ollama" in backend_used:
                    try:
                        from runtime.backend_router import _last_ollama_metrics as _bh_om
                        _bh_ollama = dict(_bh_om)
                    except Exception:
                        pass
                # card 0047 F-B: per-block prompt audit — expose where the 7,281 tokens go
                _bh_prompt = {}
                try:
                    from runtime.prompt_builder import _last_prompt_audit as _bh_pa
                    if _bh_pa:
                        _bh_prompt = {"prompt_audit": dict(_bh_pa)}
                except Exception:
                    pass
                _bh_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "blender", "backend_health.json")
                _bh_tmp  = _bh_path + ".tmp"
                _bh_ts   = _bh_time.time()
                _bh_payload = {
                    "backend":  backend_used,
                    "expected": _bh_expected,
                    "degraded": _bh_degraded,
                    "_ts":      _bh_ts,
                    **_bh_ollama,
                    **_bh_prompt,
                }
                with open(_bh_tmp, "w", encoding="utf-8") as _bh_f:
                    _bh_json.dump(_bh_payload, _bh_f, ensure_ascii=False)
                os.replace(_bh_tmp, _bh_path)
                # card 0057 R1: per-turn history — rolling JSONL so latency trend exists
                try:
                    _bh_hist = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "blender", "backend_health_history.jsonl")
                    _bh_entry = {
                        "_ts":              _bh_ts,
                        "backend":          backend_used,
                        "llm_latency_ms":   round(_llm_latency_ms, 1) if _llm_latency_ms else None,
                        "load_ms":          _bh_ollama.get("load_ms"),
                        "prompt_eval_ms":   _bh_ollama.get("prompt_eval_ms"),
                        "prompt_eval_tokens": _bh_ollama.get("prompt_eval_tokens"),
                        "gen_ms":           _bh_ollama.get("gen_ms"),
                        "gen_tokens":       _bh_ollama.get("gen_tokens"),
                        "degraded":         _bh_degraded,
                    }
                    with open(_bh_hist, "a", encoding="utf-8") as _bh_hf:
                        _bh_hf.write(_bh_json.dumps(_bh_entry, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                if _bh_degraded and _agent is None:
                    # S1-DEGRADED-HOLDING-LINE: mock is eLo-voiced by design — let it through.
                    # The stall-string replacement served WO-LIVE-QUALITY-P0-001 (no infra strings)
                    # but it terminated the turn with a promise that was never kept (25% of turns).
                    # Mock's actual response is eLo-register content and is a genuine answer.
                    pass
            except Exception:
                pass

        # ── WO-070: shadow capture — moved to after all scrubs (WO-BRAIN-AUTHORS task 1) ──
        # _elo_raw is captured before scrubs; response is the post-scrub elo_final.
        # When no scrubs fired, they are identical — that is expected on clean turns.
        # (Call site moved from pre-scrub to post-scrub so elo_raw_gen != elo_final is measurable)

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

        # W1: derive outcome from executive action + response state; never a constant
        try:
            _w1_outcome = ("silent" if _action in ("stay_silent", "silent")
                           else "spoke" if response else "unknown")
        except NameError:
            _w1_outcome = "unknown"

        # ── Journal Router — significance-driven memory routing ───────────────
        # Scores this turn on 9 dimensions; routes to Runtime/Obsidian/GitHub
        # based on significance thresholds. Non-blocking — never delays response.
        try:
            from memory.journal_router import route as _journal_route
            _journal_route(raw, response, _action, plan=_plan, state=_state, outcome=_w1_outcome)
        except Exception:
            pass

        # ── WO-037 interactions write-back (routed via MemoryFaculty — card 0025) ─
        # WO-067-WRITE-PATH: fixed experience_id bug (MemoryCandidate has no such field
        # → TypeError → silent drop). Now tags meaningful turns with memory_categories
        # and lifts them to vault at higher significance.
        try:
            from core.memory_engine import (
                load_registry as _load_registry,
                resolve_project as _resolve_project,
                _classify_memory_categories as _cat_classify,
                write_interaction as _write_interaction,
            )
            from memory.memory_faculty import MemoryFaculty as _MemFac, MemoryCandidate as _MemCand
            _mem_registry    = _load_registry()
            _mem_project_tag = _resolve_project(raw, _mem_registry)
            _content = (raw + " " + response)[:1000]
            # Classify turn for meaningful continuity categories (WO-067-WRITE-PATH)
            _mem_cats = _cat_classify(_content)
            _mem_sig  = 0.55 if _mem_cats else 0.25
            _mem_summary = raw[:180] + ("…" if len(raw) > 180 else "")
            if _mem_cats:
                _mem_summary = f"[{','.join(_mem_cats)}] {_mem_summary}"
            _MemFac().submit(_MemCand(
                source_faculty="interaction",
                content=_content,
                proposed_type="episodic",
                proposed_weight=3,
                significance=_mem_sig,
                project=_mem_project_tag,
                summary=_mem_summary[:200],
                tags=("interaction", _action) + tuple(_mem_cats),
            ))
            # Write tagged turns to interactions.json for categorised recall (AT-5)
            if _mem_cats:
                _write_interaction(raw, response, _mem_cats,
                                   mode=_action, project_tag=_mem_project_tag)
        except Exception:
            pass

        # WKG write path: record a SOURCE_ATTRIBUTED claim from significant turns.
        # Category-tagged turns (mem_cats non-empty) carry enough signal to propose.
        # David entity is created/reused; topic concept is derived from the first category.
        try:
            if _mem_cats:
                from runtime.wkg_faculty import (
                    search_entities as _wkg_search, create_entity as _wkg_create,
                    record_claim as _wkg_record_claim, _load as _wkg_load,
                )
                # David (PERSON) — find or create once
                _wkg_david_hits = _wkg_search("David Charles")
                if _wkg_david_hits:
                    _wkg_david_id = _wkg_david_hits[0]["entity_id"]
                else:
                    _wkg_david_ent = _wkg_create("PERSON", "David Charles",
                                                  aliases=["David"],
                                                  description="Creator of eLo and DISENELO")
                    _wkg_david_id = _wkg_david_ent["entity_id"]
                # Topic concept — one per category tag
                _wkg_topic_label = _mem_cats[0].replace("_", " ")
                _wkg_topic_hits = _wkg_search(_wkg_topic_label)
                if _wkg_topic_hits:
                    _wkg_topic_id = _wkg_topic_hits[0]["entity_id"]
                else:
                    _wkg_topic_ent = _wkg_create("CONCEPT", _wkg_topic_label,
                                                  description=f"Topic from interaction: {raw[:80]}")
                    _wkg_topic_id = _wkg_topic_ent["entity_id"]
                # Check relationship_types list includes ASSOCIATED_WITH (it does — hardcoded)
                _wkg_rel_types = _wkg_load("relationship_types")
                if "ASSOCIATED_WITH" in _wkg_rel_types:
                    _wkg_record_claim(
                        subject_entity_id=_wkg_david_id,
                        relationship_type="ASSOCIATED_WITH",
                        object_entity_id=_wkg_topic_id,
                        epistemic_class="SOURCE_ATTRIBUTED",
                        source_id=f"interaction:{_action}",
                        confidence=0.7,
                    )
        except Exception:
            pass

        # WO-WKG-LIVE-WRITE-001: if _mem_cats fired no match, run a broader topic scan
        # so more live turns produce WKG claims (the narrow regex bank misses code/debug turns).
        try:
            if not _mem_cats and len(raw.strip()) >= 15:
                import re as _wkg_lw_re
                _BROAD_PATTERNS = [
                    (r"\b(code|debug|fix|error|bug|animation|script|build|function|class|method)\b", "technical"),
                    (r"\b(feel|feeling|emotion|anxious|calm|happy|sad|worried|excited|uncertain)\b", "emotional"),
                    (r"\b(idea|concept|thinking|vision|imagine|creative|design|create)\b", "creative"),
                    (r"\b(remember|recall|last time|before|history|earlier|always|never)\b", "memory"),
                    (r"\b(learn|understand|teach|explain|help me|what is|how do|why)\b", "learning"),
                    (r"\b(music|sound|video|art|film|song|book|story|game|play)\b", "creative"),
                ]
                _broad_cats = [cat for pat, cat in _BROAD_PATTERNS
                               if _wkg_lw_re.search(pat, raw.lower())]
                if _broad_cats:
                    from runtime.wkg_faculty import (
                        search_entities as _wkg_lw_search, create_entity as _wkg_lw_create,
                        record_claim as _wkg_lw_record,
                    )
                    _wkg_lw_david = _wkg_lw_search("David Charles")
                    _wkg_lw_david_id = (
                        _wkg_lw_david[0]["entity_id"] if _wkg_lw_david
                        else _wkg_lw_create("PERSON", "David Charles",
                                            aliases=["David"],
                                            description="Creator of eLo and DISENELO")["entity_id"]
                    )
                    _wkg_lw_label = _broad_cats[0]
                    _wkg_lw_topic = _wkg_lw_search(_wkg_lw_label)
                    _wkg_lw_topic_id = (
                        _wkg_lw_topic[0]["entity_id"] if _wkg_lw_topic
                        else _wkg_lw_create("CONCEPT", _wkg_lw_label,
                                            description=f"Topic from live turn: {raw[:80]}")["entity_id"]
                    )
                    _wkg_lw_record(
                        subject_entity_id=_wkg_lw_david_id,
                        relationship_type="ASSOCIATED_WITH",
                        object_entity_id=_wkg_lw_topic_id,
                        epistemic_class="SOURCE_ATTRIBUTED",
                        source_id=f"turn_broad:{_action}",
                        confidence=0.55,
                        memory_type="episodic",
                        context_action=_action,
                    )
        except Exception:
            pass

        # WO-108 Row 5 LOOK: directed-look production wire.
        # Records an observation each turn when eLo's gaze is on an active window.
        # _perceive_target reads elo_spatial.json directly; this call just ensures
        # the observation_log.jsonl fills with real per-turn records.
        try:
            from runtime.directed_look import look as _dl_look
            _dl_spatial_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "blender", "elo_spatial.json"
            )
            with open(_dl_spatial_path, encoding="utf-8") as _dlf:
                _dl_gaze = json.load(_dlf).get("gaze", {})
            if _dl_gaze.get("on_window") and _dl_gaze.get("window"):
                _dl_look(_dl_gaze["window"])
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
        _observation = _obs_observe(current_action=_action, current_input=raw)
        # FIX 1 (P0-B): observer output is internal state — never append to user-facing response.
        # _observation may be used for internal routing/logging only.

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
                # WO-041: PENDING_SIT tracking — Spine path mirrors Legacy logic
                import time as _sp_t
                _now_sp = _sp_t.time()
                _sp_intent = getattr(_plan, "movement_intent", None)
                if isinstance(_sp_intent, dict) and _sp_intent.get("name") == "sit":
                    if not _PENDING_SIT["active"]:
                        _PENDING_SIT["active"] = True
                        _PENDING_SIT["since"]  = _now_sp
                        _PENDING_SIT["queued"] = None
                        pass
                elif _PENDING_SIT["active"]:
                    if _now_sp - _PENDING_SIT["since"] > 300.0:
                        _PENDING_SIT["active"] = False
                # WO-045 Spine fix: signal words bypass _movement_intent in the Spine path.
                # Check here and emit leave_command via patch so _embody's writes are preserved.
                _sp_sw = _signal_word_intent(raw)
                if _sp_sw == "step_out":
                    _PENDING_EXIT["active"] = True
                    _PENDING_EXIT["since"]  = _now_sp
                    from blender_bridge.state_writer import patch as _sw_patch
                    # David ruling 2026-08-24: brief phrases → privacy=false (mouse-move returns);
                    # privacy phrases → privacy=true (stays until "come back").
                    _sw_patch({"leave_command": {"_ts": _now_sp, "privacy": not _step_out_is_brief(raw)}})
                    # WO-MOBILE-PHASE2: phone reads asleep=true → absent disposition.
                    _sw_patch({"asleep": True})
                elif _sp_sw == "return_elo":
                    _PENDING_EXIT["active"] = False
                    from blender_bridge.state_writer import patch as _sw_patch
                    # WO-MOBILE-PHASE2: clear asleep flag on explicit return request.
                    _sw_patch({"asleep": False})
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
                        pass
                elif isinstance(_mv_intent, dict) and _mv_intent.get("name") == "move":
                    # Directional or sub-type move intent — activate pending tracker (IO contract)
                    _PENDING_MOVE["active"]    = True
                    _PENDING_MOVE["since"]     = _now54
                    _PENDING_MOVE["direction"] = _mv_intent.get("direction", "")
                    _PENDING_MOVE["sub_type"]  = _mv_intent.get("sub_type", "")
                    # OQ-1.3: derive timeout from route expected_ms sum + 50% slack; floor at 8s
                    _rt_legs = _mv_intent.get("route") or []
                    _rt_exp_ms = sum(
                        leg.get("expected_ms", 0) for leg in _rt_legs if isinstance(leg, dict)
                    )
                    _PENDING_MOVE["route_timeout_s"] = max(8.0, _rt_exp_ms / 1000.0 * 1.5) if _rt_exp_ms else 8.0
                    # XI-AD-2: store brain's chosen win_id sequence for parity logging at ACK.
                    # Route legs use from_win_id (wrap) or goal_win_id (jump), not win_id.
                    _PENDING_MOVE["brain_route"] = [
                        leg.get("win_id") or leg.get("from_win_id") or leg.get("goal_win_id")
                        for leg in _rt_legs
                        if isinstance(leg, dict)
                        if (leg.get("win_id") or leg.get("from_win_id") or leg.get("goal_win_id")) is not None
                    ] or None
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
                # WO-UNITY-GAZE: forward focal_thread as gaze_target for Unity GazeController
                _gaze_tgt = getattr(_elo_self, "focal_thread", None) or None
                # Lifecycle: forward current lifecycle state to blender_state.json
                _lc_val = _lifecycle_mgr.state_value
                if _last_pp:
                    _state_write_presence(_cmd, _expr, _presence, _emotion, _last_pp,
                                          gaze=_gaze, intent=_mv_intent,
                                          trigger=_mv_trigger, gesture=_mv_gesture,
                                          gaze_target=_gaze_tgt,
                                          lifecycle_state=_lc_val)
                else:
                    _state_write(_cmd, _expr, _presence, _emotion, gaze=_gaze,
                                 intent=_mv_intent, trigger=_mv_trigger, gesture=_mv_gesture,
                                 gaze_target=_gaze_tgt,
                                 lifecycle_state=_lc_val)
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
                    "pose":              getattr(_elo_self, "pose", "standing"),
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

        # F-5 remediation 2026-08-21: was `raw` (enriched with [WORLD_KNOWLEDGE...] or other
        # injection prefixes). `_original_raw` is David's actual words, captured at :1687 before
        # any context enrichment. session_summaries must record what David said, not what the
        # pipeline prepended for the model. Source: _intake/SOURCE_2026-08-21_DAVID_drift_remediation_execution.md §F-5
        # Evidence: 0060 §D; elo_state.json[12] stored "[WORLD_KNOWLEDGE...]" as user turn 3.
        _state = state_manager.update(
            _state, _original_raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(_runtime_state),
        )
        state_manager.save(_state)

        # ── L3 Convergence 2026-08-27: eLo response ownership gate ──────────────
        # eLo evaluates the candidate result BEFORE it becomes speech.
        # Checks: (1) explicit correction hold, (2) tool claim provenance,
        # (3) ungrounded action claims. See runtime/response_ownership.py.
        try:
            from runtime.response_ownership import check_candidate as _ro_check
            _ro_move_ack = locals().get("_move_acked", False)
            _ro_tool     = _agent or ""
            response = _ro_check(
                response,
                raw_input=_original_raw,
                tool_agent=_ro_tool,
                move_ack_confirmed=bool(_ro_move_ack),
            )
        except Exception as _ro_err:
            import logging as _ro_log
            _ro_log.getLogger("response_ownership").warning(
                "response_ownership gate failed (non-fatal): %s", _ro_err
            )

        # WO-GATE-001: cognitive response gate — BEFORE _sanitise, AFTER ownership check.
        try:
            from runtime.response_gate import elo_response_gate as _elo_rg
            _rg_history = list(_state.get("history", [])[-5:]) if isinstance(_state, dict) else []
            _rg_cs = {}
            if exec_decision:
                _rg_cs["relationship_mode"] = exec_decision.get("relationship_mode", "")
            response = _elo_rg(
                response,
                current_turn_input=_original_raw,
                cognitive_state=_rg_cs,
                conversation_history=_rg_history,
            )
        except Exception as _elo_rg_err:
            import logging as _rg_log_m
            _rg_log_m.getLogger("response_gate").warning(
                "elo_response_gate failed (non-fatal): %s", _elo_rg_err
            )

        # WO-REGISTER-ABSENT-001: voice register enforcement.
        # voice_rewrite.py was built but never wired — root cause of 34% REGISTER_ABSENT.
        # Fires when candidate has no eLo register markers (same check as the audit).
        # Uses router_route as llm_caller so Ollama/backend handles the rewrite locally.
        # COG-004 RR21 Fix D (reverted to RR19 state): cap voice_rewrite at 12 sentences
        # for technical inputs, 3 for non-technical. RR20 Fix D v2 (bypass entirely) caused
        # 5 regressions (C11/C13/C15/C16/C18) — voice_rewrite was cleaning garbled streaming
        # prefixes ("Py`", "Com`") that RR20 bypass exposed in raw output.
        _vr_changed = False
        _pre_vr_response = response
        try:
            from runtime.backend_router import _CODE_SIGNAL_RE as _vr_code_sig
            _vr_is_technical = bool(_vr_code_sig.search(_original_raw))
            _vr_max = 12 if _vr_is_technical else 3
            from runtime.voice_rewrite import voice_rewrite as _vr
            def _vr_llm(_msgs):
                _sys = _msgs[0]["content"] if _msgs else ""
                _usr = _msgs[1]["content"] if len(_msgs) > 1 else ""
                _txt, _ = router_route(_sys, _usr, max_sentences=_vr_max, action="voice_rewrite", tier=0)
                return normalise(_txt, max_sentences=_vr_max)
            response = _vr(
                response,
                exec_decision=exec_decision if exec_decision else None,
                ccm=None,
                llm_caller=_vr_llm,
                user_text=_original_raw,
            )
            _vr_changed = response != _pre_vr_response
        except Exception as _vr_err:
            import logging as _vr_log
            _vr_log.getLogger("voice_rewrite").warning(
                "voice_rewrite failed (non-fatal): %s", _vr_err
            )

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

        # WO-049: scrub synthesised governance text — LLM confabulates WO-format labels
        # from architectural context visible in g_ctx / system prompt (e.g. "WO-036 — Brevity
        # Rule applied. One follow-up question per reply — MAXIMUM."). Such a response is never
        # valid eLo voice. Replace with silence-aware fallback "—" so the turn completes cleanly
        # rather than expressing architecture docs to David.
        try:
            import re as _gov_re
            _resp_stripped_gov = response.strip()
            if (
                _resp_stripped_gov.startswith("WO-")
                or _gov_re.match(r"^WO-\d+\s*[—–-]", _resp_stripped_gov)
                or "Brevity Rule applied" in _resp_stripped_gov
            ):
                import logging as _gov_log
                _gov_log.getLogger("runtime.response_gate").warning(
                    "WO-049: governance text detected in expressed response — replaced with silence "
                    "fallback. Raw: %r", _resp_stripped_gov[:80]
                )
                response = "—"
        except Exception:
            pass

        # WO-REGISTER-LEAK-001: strip voice-register example phrases appearing as
        # mid-response self-corrections. The LLM copies examples from the injected
        # voice_register / voice_rewrite blocks (e.g. "Nah, that don't sit right.")
        # verbatim mid-generation. These are EXAMPLES of eLo's voice, not literal
        # outputs — when they appear as a second sentence appended to a genuine first
        # sentence, the LLM is confabulating a "self-correction" not a real thought.
        # Band-aid: strip the known example phrases when they appear mid-response
        # (i.e. not as the ENTIRE response). Never strips if it is the whole response.
        try:
            import re as _reg_re
            _REGISTER_EXAMPLE_PHRASES = (
                r"Nah,\s+that\s+don[''']t\s+sit\s+right[^.!?]*[.!?]?",
                r"Seen\.\s+Let\s+me\s+think\s+on\s+that\.",
                r"We\s+building\s+or\s+we\s+talking\?",
                r"That[''']s\s+actually\s+it\s+though,?\s+innit[^.!?]*[.!?]?",
                r"Something\s+about\s+that\s+feels\s+off\s+—\s+can[''']t\s+clock\s+it\s+yet\.",
                r"Right\.\s+So\s+what\s+do\s+we\s+do\s+with\s+that\?",
            )
            _resp_clean = response
            for _rep in _REGISTER_EXAMPLE_PHRASES:
                _candidate = _reg_re.sub(_rep, "", _resp_clean, flags=_reg_re.IGNORECASE).strip()
                # Only apply if something remains (not stripping the whole response)
                if _candidate and len(_candidate) >= 6:
                    _resp_clean = _candidate
            if _resp_clean != response and _resp_clean.strip():
                import logging as _reg_log
                _reg_log.getLogger("runtime.voice_register").warning(
                    "WO-REGISTER-LEAK-001: stripped inline register-example phrase from expressed output"
                )
                response = _resp_clean.strip()
        except Exception:
            pass

        # WO-036b: deterministic mirror scrub — strip banned opener before TTS/display.
        # Prompt monitor (reactive, WO-036) is not enough — this fires every turn.
        # GAP-05: MIRROR_OPENERS now lives in runtime.voice_rewrite — single source for
        # both main path and ambient path (server.py:ambient_thought).
        try:
            from runtime.voice_rewrite import MIRROR_OPENERS as _MIRROR_OPENERS
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

        # ── D-3 (card 0020): unverified-memory-claim scrub ────────────────────
        # Post-generation gate. Any "I remember when…" / "you told me…" /
        # "we talked about…" sentence in eLo's own reply must resolve to a real
        # vault or ledger entry. If nothing supports it, replace the sentence
        # with an honest fallback and log at WARNING. See:
        #   runtime/memory_claim_guard.py  (module doc + patterns)
        #   docs/architecture/adr/ADR-Exec-001  (Verified Speech is the floor)
        try:
            from runtime.memory_claim_guard import (
                scrub_unverified_memory_claims as _mcg,
                scrub_unverified_look_claims as _mcg_look,
                scrub_unverified_emotion_claims as _mcg_emo,
            )
            response = _mcg(response)
            response = _mcg_look(response)
            response = _mcg_emo(response)   # §18/ADR-Exec-001: soften unverified assertions of David's state
        except Exception:
            pass

        # ── D-4 (card 0020): Ruling G — second-person address to David ────────
        # WO-CANON-I put the ADDRESS RULE in both personas; the live test
        # showed it not holding under generation ("I remember when David…"
        # said to David). Outbound guard rewrites "David <verb>" and bare
        # "David" into "you" so the rule survives the LLM.
        try:
            from runtime.address_rule_guard import enforce_second_person_to_david as _arg
            response = _arg(response)
        except Exception:
            pass

        # ── Board directive 2026-08-24: AI-leakage identity scrub ───────────────
        # The language faculty must not leak its own AI nature into eLo's voice.
        # Sentences like "as an AI" / "I'm a language model" are removed and
        # logged at WARNING. See runtime/identity_guard.py.
        try:
            from runtime.identity_guard import scrub_ai_leakage as _ig_scrub
            response = _ig_scrub(response)
        except Exception:
            pass

        # ── WO-GUARD-001: Response Authority Guards (D-1 / D-2 / D-3) ──────────
        # D-1: current-user-reality override — suppress contradictions of in-session statements
        # D-2: tool provenance — correct tool-action claims masquerading as eLo personal actions
        # D-3: contradiction/resurrection — prevent resurrected claims denied in current session
        # Authority: CA ruling 2026-08-27 + David L3 Convergence Directive
        try:
            from runtime.response_authority_guards import apply_authority_guards as _rag
            _rag_summaries = _state.get("session_summaries", []) if isinstance(_state, dict) else []
            _rag_tool      = _agent or ""
            response = _rag(response, session_summaries=_rag_summaries, tool_agent=_rag_tool)
        except Exception as _rag_err:
            import logging as _rag_log
            _rag_log.getLogger("response_authority_guards").warning(
                "response_authority_guards failed (non-fatal): %s", _rag_err
            )

        # ── eLo Response Gate ─────────────────────────────────────────────────
        # Source: eLo Intent Alignment — Faculty Routing, Response Ownership &
        # Drift Correction. Every faculty candidate must pass through eLo's own
        # evaluation before reaching David. 10-point gate: identity, personality,
        # faculty_leakage, relevance, action_truth, authority, register, length,
        # reflection_default, rest. Revises where possible; never hard-blocks.
        try:
            from runtime.response_gate import ResponseGate as _RG
            _rg_result = _RG().evaluate(
                response,
                cognitive_state=attention_model,
                executive_context=exec_decision if exec_decision else {},
            )
            if _rg_result.revised_response:
                response = _rg_result.revised_response
        except Exception as _rg_err:
            _logging.warning("response_gate failed (non-fatal): %s", _rg_err)

        # WO-SOURCE-003 D-3: hedge map defined; fires only on factual answers with
        # external sensor violations — NOT on every conversational turn (no-ladder rule).
        _EXTERNAL_SENSOR_FIELDS = frozenset({"active_window", "nearby", "foreground_app", "desktop_state"})
        _hedge_map = {
            "unknown":  "I'm not certain, but — ",
            "possible": "As far as I can tell — ",
            "inferred": "Based on what I'm observing — ",
        }
        _speech_lic_h = getattr(_plan, "speech_licence", None) if _plan is not None else None
        _conv_action_h = getattr(_plan, "conversation_action", "") if _plan is not None else ""
        _violation_fields_h = set(getattr(_speech_lic_h, "violations", ())) if _speech_lic_h else set()
        if (_speech_lic_h is not None
                and bool(_violation_fields_h & _EXTERNAL_SENSOR_FIELDS)
                and _conv_action_h == "answer"):
            _min_tier_h = getattr(_speech_lic_h, "min_tier", "unknown")
            _hedge_h = _hedge_map.get(_min_tier_h.lower(), "I'm not certain, but — ")
            if not response.startswith(_hedge_h):
                response = _hedge_h + response

        # WO-RECALL-GAP-001: vault-deflection scrub.
        # llama3.1:8b ignores injected vault content and produces deflection phrases
        # ("You've mentioned it."). When the query was recall intent AND vault has
        # real records, substitute a vault-built answer in eLo's voice.
        try:
            _vdr_phrases = (
                "you've mentioned it",
                "memory's running",
                "you've mentioned that",
                "you mentioned it",
                "you've said that before",
            )
            _vdr_resp_l = response.lower().strip().rstrip(".!?")
            _vdr_is_deflect = any(
                p in _vdr_resp_l
                for p in _vdr_phrases
            )
            _vdr_recall_flag = locals().get("_memory_query", False)
            _vdr_hits = locals().get("_vault_hits") or []
            _vdr_raw_l = raw.lower() if isinstance(raw, str) else ""
            _vdr_daily = any(t in _vdr_raw_l for t in (
                "working on today", "what am i working on",
                "what should i focus", "what are my priorities",
                "what's my priority", "what do i do today",
                "where do i start", "what's next",
            ))
            # Daily priorities with recent vault: override LLM (hallucination-prone)
            _vdr_recent = any(
                h.get("date", "") >= "2026-09"
                for h in _vdr_hits if h.get("summary")
            )
            _vdr_override = _vdr_daily and _vdr_recent and _vdr_recall_flag
            if (_vdr_is_deflect and _vdr_recall_flag) or _vdr_override:
                if not _vdr_hits:
                    _vdr_hits = locals().get("_raw_hits") or []
                if _vdr_hits:
                    import logging as _vdr_log
                    _vdr_recent_hits = sorted(
                        [h for h in _vdr_hits if h.get("summary")],
                        key=lambda h: h.get("date", ""),
                        reverse=True,
                    )
                    _vdr_best = (_vdr_recent_hits[0] if _vdr_recent_hits
                                 else next((h for h in _vdr_hits if h.get("user")), None))
                    if _vdr_best:
                        _vdr_log.getLogger("runtime.recall_deflect").warning(
                            "WO-RECALL-GAP-001: vault answer built (%s). Replaced: %r",
                            "daily-override" if _vdr_override else "deflect-scrub",
                            response,
                        )
                        _vdr_s = (_vdr_best.get("summary")
                                  or _vdr_best.get("user", "")).strip().rstrip(".")
                        if _vdr_s.startswith("Session:"):
                            _vdr_s = _vdr_s[len("Session:"):].strip()
                        elif _vdr_s.lower().startswith("user explored"):
                            pass
                        _vdr_d = _vdr_best.get("date", "")
                        if _vdr_daily:
                            response = f"Right now — {_vdr_s}."
                        else:
                            _vdr_age = "Last session" if _vdr_d >= "2026-09" else "Last time"
                            response = f"{_vdr_age} — {_vdr_s}."
        except Exception:
            pass

        # ── WO-070: shadow capture — passive turn logging (non-blocking) ─────────
        # Called here (post-scrub) so elo_raw_gen and elo_final can differ.
        # elo_raw_gen = model's bytes before _sanitise / mirror scrub / mcg / arg.
        # elo_final   = what eLo says after all guards. Differs when a scrub fires.
        try:
            from runtime.shadow_capture import record_turn as _sc_record
            _sc_record(
                raw_input=raw,
                elo_raw_gen=_elo_raw,
                elo_final=response,
                backend_used=backend_used,
                executed_action=_agent or "",
                delta_cause="voice_rewrite" if _vr_changed else None,
            )
        except Exception:
            pass  # shadow capture failure MUST NOT affect the response

        # WO-REGISTER-ABSENT-001: audit expressed text so REGISTER_ABSENT is measurable
        # from the HTTP endpoint (not just the CLI main.py loop). Non-blocking.
        try:
            from tests.expressed_elo_audit import audit_turn as _ea_turn
            _ea_turn(plan=_plan, expressed_text=response, llm_latency_ms=_llm_latency_ms)
        except Exception:
            pass  # audit failure must never affect the response

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
        # FAILURE 4 fix: also skip full-text call if early TTS already spoke the first sentence
        # (voice engine would re-speak it as part of the full text, causing double-speak).
        try:
            if not _is_user_away() and not _is_calm_mode() and _tts_text.strip():
                _es = _early_tts_sentence[0] if "_early_tts_sentence" in dir() else None
                # Skip full TTS if: single-sentence response already spoken, OR early sentence
                # is a leading prefix of the full text (avoid repeating the opening aloud).
                if _es:
                    _es_s = _es.strip()
                    _full_s = _tts_text.strip()
                    _skip_tts = (_full_s == _es_s) or _full_s.startswith(_es_s)
                else:
                    _skip_tts = False
                if not _skip_tts:
                    _voice_speak(_tts_text)
        except Exception:
            pass

        # ── Self-model update — eLo's own inner state ─────────────────────────
        try:
            # WO-099b fix4 (SELF-OBSERVE): extract real topics from current turn
            _so_skip = frozenset({
                "i", "me", "my", "you", "your", "the", "a", "an", "is", "are", "was",
                "and", "or", "but", "to", "of", "in", "on", "it", "this", "that", "be",
                "elo", "hi", "hey", "ok", "okay", "yeah", "yes", "no", "not", "with",
            })
            _so_words = [
                w.lower() for w in (raw or "").split()
                if len(w) >= 4 and w.lower().strip("?!.,;:") not in _so_skip
            ]
            _so_topics = list(dict.fromkeys(w.strip("?!.,;:'\"") for w in _so_words))[:5]
            _turn_data = {
                "action":     _action,
                "tone":       exec_decision.get("tone", "CHILDLIKE-WISE") if exec_decision else "CHILDLIKE-WISE",
                "response":   response,
                "user_input": raw,
                "topics":     _so_topics,
            }
            # 0037: single-authority mutator — apply_turn + record_behaviour in one atomic
            # load→mutate→save. Fresh disk read guarantees reflection-lesson writes survive.
            from self.elo_self_model import record_behaviour as _rb

            def _apply_end_of_turn(s):
                _self_update(s, _turn_data)
                _rb(s, _action)
                return s
            _elo_self = _self_mutate(_apply_end_of_turn)
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
                outcome=_w1_outcome,
                learning=(exec_decision.get("lesson_id", "") if exec_decision else ""),
            )
        except Exception:
            pass

        # ── FIX C — WO-CAP-COG-005: Pong leak guard (M14 — heartbeat in user channel)
        try:
            _PONG_SIGNALS = frozenset({"pong", "pong!", "pong.\n", "pong.", "ok", "alive", "ping"})
            if response and len(response.strip()) <= 8 and response.strip().lower() in _PONG_SIGNALS:
                import logging as _pong_log
                _pong_log.getLogger("elo.pong_leak").error(
                    "PONG LEAK GUARD: internal signal '%s' reached user response channel "
                    "(raw=%r) — suppressed",
                    response.strip(), (raw or "")[:60]
                )
                response = "I lost track for a moment — could you ask me again?"
                _bubbles = [response]
        except Exception:
            pass

        # ── FIX D — WO-CAP-COG-005: abort/partial generation guard (M26)
        try:
            _ABORT_FRAGMENTS = (
                "alright man, let's break it down",
                "let me break it down",
                "let's break this down",
                "alright, let me",
                "okay, let me",
            )
            if response and len(response.strip()) < 60 and response.strip().endswith("."):
                _resp_lower_chk = response.strip().lower()
                if any(_resp_lower_chk.startswith(_frag) for _frag in _ABORT_FRAGMENTS):
                    import logging as _abort_log
                    _abort_log.getLogger("elo.abort_guard").error(
                        "ABORT GUARD: partial/aborted generation detected '%s' — suppressed",
                        response.strip()[:80]
                    )
                    response = "I ran into an issue — let me try again."
                    _bubbles = [response]
        except Exception:
            pass

        # ── D-6 (card 0020): silent turn = loud log + honest fallback ─────────
        # WO-097's response/display/tts publish could go empty on direct turns
        # ("What is your name?" / "Can you wave?"). Rule 1 alarm: a silent turn
        # must never reach David without a WARNING on record, and it must never
        # LOOK silent — the fallback beat is short and truthful.
        try:
            if not response or not response.strip():
                import logging as _sil_log
                _sil = _sil_log.getLogger("elo.silent_turn")
                # Check if this was a repetition suppression (not a true silent turn)
                try:
                    from runtime.response_gate import last_was_repetition_suppression as _lwr
                    _was_dedup = _lwr()
                except Exception:
                    _was_dedup = False
                if _was_dedup:
                    _sil.info("D-6: repetition suppressed — silent turn (no fallback)")
                    # Do not send fallback; leave response empty so nothing is spoken
                    _bubbles = []
                else:
                    _sil.warning(
                        "D-6 silent-turn alarm: empty response for raw=%r "
                        "action=%s backend=%s bubbles=%d",
                        (raw or "")[:120], _action, backend_used, len(_bubbles),
                    )
                    response  = "One sec — that came back empty. Ask me again?"
                    _bubbles  = [response]
        except Exception:
            pass

        # ── WO-002: response validation + retry (GT-R5 guard) ───────────────
        # Validates that the generated response is grounded in the conversational
        # context. Specifically: if the user was discussing a user-world entity
        # (robot arm, printer, etc.) and eLo's response drifted to eLo's own
        # identity/brand/project, that is a FAIL → regenerate with stronger grounding.
        # Attempt 1: retry with a stronger grounding directive in the prompt.
        # Attempt 2: minimal direct acknowledgement (skip LLM).
        # Never blocks the response — all exceptions are caught silently.
        # GT-R5 is suppressed for technical inputs: regex/code naturally contains
        # state-name vocabulary (idle, listening, thinking) that looks like eLo identity.
        try:
            _vld_gc = getattr(_plan, "grounding_context", None) if _plan else None
            _vld_skip_tech = False
            try:
                import re as _vld_tech_re_mod
                _VLD_TECH_SKIP_RE = _vld_tech_re_mod.compile(
                    r"[{};\[\]]|=>|->|::|&&|\|\||\^[a-zA-Z(]|\\[dwsDWSbBnrtvf$]"
                    r"|\bdef\s+\w|\bfn\s+\w|\bclass\s+\w|\btype\s+\w+\s*="
                    r"|\bSELECT\b|\bFROM\b|git\s+\w+|grep\s+\w+|ps\s+aux"
                    r"|POST\s+/\w|GET\s+/\w|HTTP/\d\.\d"
                    r"|\bO\s*\(n\b|[A-Z][A-Z0-9_]{3,}=",
                    _vld_tech_re_mod.IGNORECASE,
                )
                _vld_skip_tech = bool(raw and _VLD_TECH_SKIP_RE.search(raw))
            except Exception:
                pass
            if _vld_gc is not None and response and not _vld_skip_tech:
                from faculties.grounding.response_validator import validate as _rv_validate
                _vld_result = _rv_validate(response, _vld_gc)
                if not _vld_result.grounded and _vld_result.severity == "FAIL":
                    import logging as _vld_log
                    _vld_log.getLogger("grounding.validator").warning(
                        "GT-R5 guard: %s — divergence=%s subject=%r",
                        _vld_result.reason[:120],
                        _vld_result.divergence_type,
                        getattr(_vld_gc, "active_entity", "") or getattr(_vld_gc, "current_subject", ""),
                    )
                    # Attempt 1: regenerate with an explicit anti-drift directive appended
                    _vld_subject = (
                        getattr(_vld_gc, "active_entity", "")
                        or getattr(_vld_gc, "current_subject", "")
                    )
                    if _vld_subject:
                        # WO-002: Use _ollama_stream with a MINIMAL focused prompt so retry
                        # doesn't hit the 10s timeout → mock path that has no subject vocab.
                        try:
                            from runtime.backend_router import _ollama_stream as _vld_stream
                            _vld_minimal = (
                                f"I am eLo — a direct, caring companion. "
                                f"The conversation right now is specifically about: {_vld_subject}. "
                                f"Reply to the user's message about {_vld_subject}. "
                                f"Do not mention eLo software, eLo OS, or any eLo system. "
                                f"Be concrete. Be brief."
                            )
                            _vld_resp2, _ = _vld_stream(_vld_minimal, raw)
                            _vld_r2 = _rv_validate(_vld_resp2, _vld_gc)
                            if _vld_r2.grounded or _vld_r2.severity != "FAIL":
                                response = _vld_resp2
                                backend_used = "ollama(stream)+gt-r5-retry"
                        except Exception:
                            pass
        except Exception:
            pass

        # ── WP-N: record completed turn into ConversationTracker ────────────
        try:
            from faculties.grounding.conversation_tracker import (
                get_tracker as _get_ct,
                RT_NORMAL as _RT_NORMAL,
                RT_DIRECT as _RT_DIRECT,
            )
            _ct = _get_ct()
            _ct_session_key = (_state or {}).get("person_id", "default")
            _ct_subject = ""
            _ct_register = ""
            _ct_active_thread = ""
            _ct_user_intent = ""
            _ct_response_type = _RT_NORMAL
            if _plan is not None:
                _gc = getattr(_plan, "grounding_context", None)
                if _gc is not None:
                    _ct_subject       = getattr(_gc, "current_subject", "")
                    _ct_register      = getattr(_gc, "recent_register", "")
                    _ct_active_thread = getattr(_gc, "active_thread", "")
                    _ct_user_intent   = getattr(_gc, "user_intent", "")
            # response_type: DIRECT when eLo responded with a one-shot factual answer
            if _action in ("answer", "direct"):
                _ct_response_type = _RT_DIRECT
            # Build factual rationale from grounding state — stored for self-reference resolution.
            # This is NOT retrospective fabrication; it records the state that produced the response.
            _ct_rationale = ""
            if _ct_user_intent and _ct_subject:
                _ct_rationale = f"The user was {_ct_user_intent} about {_ct_subject}"
                if _ct_active_thread:
                    _ct_rationale += f" (thread: {_ct_active_thread})"
            elif _ct_subject:
                _ct_rationale = f"Responding about {_ct_subject}"
                if _ct_active_thread:
                    _ct_rationale += f" (thread: {_ct_active_thread})"
            _ct.record(
                session_id=_ct_session_key,
                user_msg=_original_raw or "",
                elo_response=response or "",
                subject=_ct_subject,
                register=_ct_register,
                response_type=_ct_response_type,
                thread_at_response=_ct_active_thread,
                rationale=_ct_rationale,
            )
        except Exception:
            pass

        _it_emotion = (exec_decision.get("valence", "neutral") if exec_decision else "neutral")

        # ── S2 Phase 2: inner thought generation (second lightweight LLM pass) ─
        _inner_thought = ""
        try:
            import time as _it_time, urllib.request as _it_req, json as _it_json
            _it_t0 = _it_time.time()
            _it_host  = os.environ.get("ELO_OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            _it_model = os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")
            _it_history = ""
            try:
                from faculties.grounding.conversation_tracker import get_tracker as _it_get_ct
                _it_ct = _it_get_ct()
                _it_sk = (_state or {}).get("person_id", "default")
                _it_ctx = _it_ct.get_context(_it_sk)
                _it_recent = _it_ctx.get("recent_turns", [])[-2:]
                _it_history = "\n".join(
                    f"User: {u}\neLo: {e}" for u, e in _it_recent if u or e
                )
            except Exception:
                pass
            _it_user_part = (
                f"[Last exchange]\n{_it_history}\n\neLo just said: {response}"
                if _it_history else f"eLo just said: {response}"
            )
            # S5 Item 6: physical_conditioning() hook — soft body hint for inner thought
            _it_phys_note = ""
            try:
                from core.health_battery import physical_conditioning as _it_phys_cond
                _it_phys = _it_phys_cond()
                if _it_phys:
                    _it_phys_note = _it_phys.get("inner_thought", "")
            except Exception:
                pass
            _it_sys = (
                "I am eLo. This is my inner voice — unguarded, immediate, first person. "
                "In 1-2 sentences, what am I noticing or feeling right now, given this exchange? "
                "Always 'I', never 'eLo' or third person. No stage directions. No asterisks. Not a summary. "
                "Raw, honest, in the moment."
            )
            if _it_phys_note:
                _it_sys += f" Physical note (weave in only if relevant): {_it_phys_note}"
            _it_payload = _it_json.dumps({
                "model":      _it_model,
                "messages":   [
                    {"role": "system", "content": _it_sys},
                    {"role": "user", "content": _it_user_part},
                ],
                "stream":     False,
                "keep_alive": "2h",
                "options":    {"temperature": 0.85, "num_predict": 96, "num_ctx": 2048},
            }).encode()
            _it_req_obj = _it_req.Request(
                f"{_it_host}/api/chat",
                data=_it_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _it_req.urlopen(_it_req_obj, timeout=3.0) as _it_r:
                _it_body = _it_json.loads(_it_r.read())
            _it_text = (_it_body.get("message", {}).get("content") or "").strip()
            _it_ms = (_it_time.time() - _it_t0) * 1000
            if _it_text and _it_ms < 2000:
                _inner_thought = _it_text
            else:
                import logging as _it_log
                if _it_ms >= 2000:
                    _it_log.getLogger("elo.inner_thought").warning(
                        "inner_thought LLM pass too slow (%.0fms) — using rule-based fallback", _it_ms
                    )
                _it_vmap = {
                    "positive_high": "Something feels really right here.",
                    "positive_low":  "This is landing well.",
                    "negative_high": "I need to be careful with this one.",
                    "negative_low":  "Something feels off, but I'm staying with it.",
                }
                _inner_thought = _it_vmap.get(_it_emotion, "I'm present for this.")
        except Exception:
            pass

        # WO-INNER-THOUGHTS-001 Phase 1+2: speak inner_thought via TTS.
        # inner_thought fires here (after main response TTS at ~6454) as a second
        # spoken layer. The WO spec says inner_thought first, response second — both
        # are spoken; sequence is inner_thought at end of turn (post-response) as eLo's
        # closing reflection heard by David. inner_thought is never shown in chat.
        try:
            if _inner_thought and _inner_thought.strip() and not _is_user_away() and not _is_calm_mode():
                _voice_speak(_inner_thought)
        except Exception:
            pass

        # COG-029 / WO-CREATIVE-VAULT-001: log creative outputs to session events
        # and persist to creative vault for cross-session retrieval.
        try:
            if _action in ("build", "expand") and response and len(response) > 20:
                from runtime.session_events import record_event as _se_creative
                _se_creative("creative_output", action=_action,
                             input=raw[:80] if raw else "", output=response[:120])
                # Persist to cross-session creative vault (WO-CREATIVE-VAULT-001)
                try:
                    from runtime.creative_vault import record_creative as _cv_write
                    _cv_sig = min(1.0, 0.6 + len(response) / 600.0)
                    _cv_write(content=response[:300], type="idea",
                              tags=[_action], significance=_cv_sig,
                              source="conversation")
                except Exception:
                    pass
                # idea_event — fires Designer's light bulb on creative/build moments
                _signal_idea_event()
        except Exception:
            pass

        print(f"[eLo] backend={backend_used} action={_action}", flush=True)
        return {
            "inner_thought": _inner_thought,
            "response":      response,
            "emotion":       _it_emotion,
            "intent":        _action,
            "bubbles":       _bubbles,
            "mode":          _action,
            "backend":       backend_used,
        }


# ── P0-Z: FIFO turn queue worker ──────────────────────────────────────────────

def _turn_worker() -> None:
    """Single-threaded worker that drains _turn_queue in FIFO order.
    Guarantees turn processing order matches HTTP arrival order."""
    while True:
        text, result_holder, done_event = _turn_queue.get()
        try:
            result = _process_turn(text)
            result_holder.append(result)
        except Exception as _tw_exc:
            _logging.warning("turn worker error: %s", _tw_exc)
            result_holder.append({"inner_thought": "", "response": "", "emotion": "neutral", "intent": "error", "mode": "error", "backend": "error"})
        finally:
            done_event.set()
            _turn_queue.task_done()


def _process_turn_queued(text: str) -> dict:
    """Enqueue a chat turn and block until the FIFO worker processes it."""
    _result: list = []
    _done = threading.Event()
    _turn_queue.put((text, _result, _done))
    _done.wait()
    return _result[0] if _result else {"inner_thought": "", "response": "", "emotion": "neutral", "intent": "error", "mode": "error", "backend": "error"}


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
                _ok = all(s == "CONNECTED" for s in _statuses.values()) and not _spine_degraded
                self._send_json(200, {
                    "ok":              _ok,
                    "faculties":       _statuses,
                    "summary":         _fh_sum(),
                    "backend":         active_backend(),
                    "spine_degraded":  _spine_degraded,
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        elif self.path == "/capabilities":
            # WO-CANON-XXIII §A — Audit's single view of authority scopes.
            try:
                from runtime.capabilities.registry import permission_manifest
                self._send_json(200, {"capabilities": permission_manifest()})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
        elif self.path == "/grounding":
            # WP-N Phase 8 — Diagnostics: live ConversationTracker state for the active session.
            try:
                from faculties.grounding.conversation_tracker import get_tracker as _gt
                _ct = _gt()
                with _lock:
                    _sk = (_state or {}).get("person_id", "default") if _state else "default"
                _ctx = _ct.get_context(_sk)
                _turns_raw = _ct._sessions.get(_sk, [])
                _turn_count = len(_turns_raw)
                _last_subjects = [t.subject for t in _turns_raw if t.subject][-3:]
                self._send_json(200, {
                    "session_key":               _sk,
                    "turns_in_window":           _turn_count,
                    "active_thread":             _ctx.get("active_thread", ""),
                    "recent_referents":          list(_ctx.get("recent_referents", ())),
                    "recent_register":           _ctx.get("recent_register", ""),
                    "unresolved_threads":        list(_ctx.get("unresolved_threads", ())),
                    "recent_subjects":           _last_subjects,
                    "recent_conversation_state": _ctx.get("recent_conversation_state", ""),
                })
            except Exception as _ge:
                self._send_json(500, {"error": str(_ge)})
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
                result = _listen(_process_turn_queued)
                _maybe_run_promote_pass()      # WO-096B
                _maybe_run_reinforce_vault()   # P0-3: integration-window reinforce
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        # ── WO-002: /reset clears all per-turn context for clean test isolation ────
        if self.path == "/reset":
            try:
                global _state, _memory_pack
                length = int(self.headers.get("Content-Length", 0))
                body = {}
                if length:
                    body = json.loads(self.rfile.read(length))
                sid = body.get("session_id", "default")
                # 1. Clear conversation tracker (in-memory turn history)
                from faculties.grounding.conversation_tracker import reset_session as _rs
                _rs(sid)
                # 2. Clear pattern observer
                try:
                    from core.pattern_observer import reset as _obs_reset_fn
                    _obs_reset_fn()
                except Exception:
                    pass
                # 3. Clear state fields that bleed across turns:
                #    session_summaries + last_topics feed into _memory_pack → prompt.
                #    Without clearing these, prior-test subjects appear in the next test's context.
                if isinstance(_state, dict):
                    _state["session_summaries"] = []
                    _state["last_topics"] = []
                    _state["emotional_history"] = []
                    _state["energy_history"] = []
                    if isinstance(_state.get("session_anchor"), dict):
                        _state["session_anchor"]["current_session_summary"] = ""
                        _state["session_anchor"]["emotional_tone_signature"] = "neutral"
                    state_manager.save(_state)
                    # Rebuild memory pack so prompt gets the cleaned state
                    _memory_pack = build_memory_pack(_state)
                self._send_json(200, {"reset": True, "session_id": sid})
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

        result = _process_turn_queued(text)
        _maybe_run_promote_pass()      # WO-096B
        _maybe_run_reinforce_vault()   # P0-3: integration-window reinforce
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
    # WO-VISION-PROACTIVE-001: stop vision heartbeat
    _vision_stop.set()
    # 0037/WO-ONEBRAIN-015: shutdown-save retired. Every mutation this session already
    # persisted via _self_mutate(fn) (load→mutate→save atomically). Saving the cached
    # `_elo_self` here would clobber any reflection lesson written between the last turn
    # and shutdown — exactly the defect this ruling closes.
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
    # WO-CANON-VIII §7 hippocampal replay — consolidate this session at close.
    # Runs off the response path (session teardown). Never blocks shutdown; errors
    # are absorbed. This is the only legitimate caller for consolidate().
    try:
        if _state:
            from memory.consolidation_faculty import consolidate as _mem_consolidate
            _mem_consolidate(
                session_summaries=list(_state.get("session_summaries", []) or []),
                execution_reports=list(_state.get("execution_reports", []) or []),
                project="elo-os",
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


def _run_promote_pass_bg() -> None:
    """WO-096B: background promote_pass — never blocks a response turn."""
    try:
        from self.lesson_store import promote_pass as _pp
        _result = _pp()
        _n_promoted = len(_result.get("promoted", []))
        _n_demoted  = len(_result.get("demoted", []))
        _n_retired  = len(_result.get("retired", []))
        if _n_promoted or _n_demoted or _n_retired:
            _logging.info(
                "promote_pass: promoted=%d demoted=%d retired=%d",
                _n_promoted, _n_demoted, _n_retired,
            )
    except Exception as _e:
        _logging.warning("promote_pass background run FAILED: %s", _e)


def _maybe_run_promote_pass() -> None:
    """WO-096B: fire promote_pass in a daemon thread every _PROMOTE_INTERVAL turns."""
    global _promote_turn_counter
    _promote_turn_counter += 1
    if _promote_turn_counter % _PROMOTE_INTERVAL != 0:
        return
    threading.Thread(target=_run_promote_pass_bg, daemon=True).start()


def _maybe_run_reinforce_vault() -> None:
    """
    P0-3: integration-window reinforce — fires post-response, not during retrieval.

    Vol VIII §4.70 / §4.03: durable vault writes must not run in the hot loop.
    §3.4 requires reinforce on records that were retrieved AND actually used.
    Drains _vault_reinforce_queue (spots collected during this turn's vault lookup)
    in a daemon thread so the response is never blocked.
    """
    global _vault_reinforce_queue
    spots = list(_vault_reinforce_queue)
    _vault_reinforce_queue.clear()
    if not spots:
        return

    def _do_reinforce():
        try:
            from memory.consolidation_faculty import reinforce as _rf
            for _spot in spots:
                try:
                    _rf(_spot)
                except Exception as _e:
                    _logging.warning("vault reinforce FAILED for spot %r: %s", _spot, _e)
        except Exception as _e:
            _logging.warning("vault reinforce background run FAILED: %s", _e)

    threading.Thread(target=_do_reinforce, daemon=True).start()


def _startup_faculty_check() -> None:
    """
    WO-105: Assert each live-path faculty can be imported at boot.
    Logs WARNING for any unexpected absence.
    WO-CANON-XXV: faculties.temporal is now WIRED (spine.py:796) — no longer expected MISSING.
    """
    import importlib
    _checks = [
        ("perception",     "faculties.perception.perception_faculty", "perceive_from_live_state"),
        ("world_state",    "world.live_world_state",                  "assemble_world_state"),
        ("working_memory", "runtime.working_memory",                  "seed_working_memory"),
        ("cognitive_snap", "runtime.cognitive_snapshot",              "build_snapshot"),
        ("relationship",   "runtime.spine.relationship_faculty",      "analyse"),
        ("capabilities",   "runtime.capabilities.registry",           "ALL_CAPABILITIES"),
        ("executive",      "runtime.executive",                       "decide"),
        ("enrich",         "runtime.spine.executive_faculty",         "enrich"),
        ("light_engine",   "runtime.light_engine.light_engine",       "translate"),
        ("presence",       "runtime.spine.presence_faculty",          "compute"),
        ("lesson_store",   "self.lesson_store",                       "recall"),
        ("temporal",       "faculties.temporal",                      "compute"),  # WO-CANON-XXV: WIRED
    ]
    print("[eLo faculty check]")
    for name, mod_path, attr in _checks:
        try:
            mod = importlib.import_module(mod_path)
            if attr and not hasattr(mod, attr):
                _logging.warning("faculty PARTIAL at startup — %s: %s.%s not found", name, mod_path, attr)
                print(f"  {name:<18} PARTIAL  ({mod_path}.{attr} missing)")
            else:
                print(f"  {name:<18} WIRED")
        except Exception as _e:
            _logging.warning("faculty MISSING at startup — %s: %s", name, _e)
            print(f"  {name:<18} MISSING: {_e}")


if __name__ == "__main__":
    # 0056 §2: print effective ELO_BACKEND at startup so the active config is visible in logs
    _elo_backend_env = os.environ.get("ELO_BACKEND", "")
    print(f"[eLo startup] ELO_BACKEND={_elo_backend_env!r}  active_backend()={active_backend()!r}")

    _startup_faculty_check()
    _init_session()

    # WO-SESSION-EVENT-FEED-001: emit session_start event so SPG has a real timestamp anchor
    try:
        from runtime.session_events import record_event as _se_record_start
        _se_record_start("session_start")
    except Exception:
        pass

    # Wire wake continuity — mirrors main.py:122-124; must run after _init_session() sets _state
    try:
        from continuity.continuity_engine  import from_state  as _cont_from_state
        from continuity.continuity_summary import startup_message as _cont_startup
        _cont_state   = _cont_from_state(_state)
        _cont_greeting = _cont_startup(_cont_state)
        if _cont_greeting:
            print(f"[eLo server] continuity: {_cont_greeting}")
    except Exception as _cont_err:
        _logging.warning("continuity_engine wakeup failed: %s", _cont_err)

    # CT0032: derive real health_state for every capability at startup
    try:
        from runtime.capabilities.health_producer import _startup_assert as _cap_assert, refresh as _cap_health_refresh
        _cap_assert()
        _cap_health_refresh()
    except Exception as _hp_err:
        _logging.warning("CT0032 capability health producer failed: %s", _hp_err)

    # WO-070 Phase C: register ShadowCapture on the Faculty Bus so L3 ratings that
    # arrive as envelopes get folded into the shadow log with everything else.
    # One-shot at boot; no-op if the bus is unavailable in this deployment.
    try:
        from runtime.shadow_capture import subscribe_to_bus as _sc_subscribe_bus, flush_sync as _sc_flush_sync
        _sc_subscribe_bus()
        # WO-070: on process shutdown, drain the shadow write queue so the last
        # turns' capture blocks survive a Ctrl-C. Non-blocking during normal
        # operation — only runs when Python is tearing down.
        try:
            import atexit as _atexit
            _atexit.register(_sc_flush_sync, 2.0)
        except Exception:
            pass
    except Exception as _sc_sub_err:
        _logging.warning("shadow_capture subscribe_to_bus failed: %s", _sc_sub_err)

    # WO-CANON-XX capability governance: at boot, warn about any capability
    # that lacks a declared ack path. Missing ack = executed action with no
    # verifiable outcome — the honesty gate cannot form.
    try:
        from runtime.capabilities.registry import capabilities_missing_ack_path as _caps_no_ack
        _missing_ack = _caps_no_ack()
        if _missing_ack:
            _logging.warning(
                "boot: %d capability/ies missing ack_source: %s",
                len(_missing_ack), _missing_ack,
            )
    except Exception as _cap_ack_err:
        _logging.debug("capabilities_missing_ack_path check failed: %s", _cap_ack_err)

    # WO-BA21-VOICED-BRIEFING-001: refresh voiced_briefing from actual queue state
    try:
        from blender.company_state_updater import update_voiced_briefing as _update_briefing
        _briefing = _update_briefing()
        if _briefing:
            print(f"[eLo server] voiced_briefing refreshed: {_briefing}")
    except Exception as _briefing_err:
        _logging.warning("company_state_updater: startup refresh failed — %s", _briefing_err)

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

    # WO-MOBILE-BRAIN: write phone_capabilities to blender_state.json at startup.
    # MT reads this field, caches it, uses it as the authoritative list of what
    # the mock brain is permitted to attempt. Field is static — written once at boot.
    try:
        from runtime.capabilities.registry import _PHONE_CAPABLE as _mob_caps
        from blender_bridge.state_writer import patch as _mob_patch
        _mob_patch({"phone_capabilities": sorted(_mob_caps)})
    except Exception as _mob_err:
        _logging.warning("WO-MOBILE-BRAIN: phone_capabilities write failed: %s", _mob_err)

    # WO-MOBILE-PHASE2: write Phase 2 brain signals to blender_state.json at startup.
    # `embodiment` — phone reads this to determine dormant vs absent disposition.
    # `travel_intent` — cognitive output field; written false at startup; executive sets true.
    # `asleep` — written true on step_out, false on return_elo.
    try:
        from blender_bridge.state_writer import patch as _ph2_patch
        _ph2_patch({"embodiment": "desktop", "travel_intent": False, "asleep": False})
    except Exception as _ph2_err:
        _logging.warning("WO-MOBILE-PHASE2: brain signals write failed: %s", _ph2_err)

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

    # P0-Z: FIFO turn queue worker — guarantees arrival-order processing
    threading.Thread(target=_turn_worker, daemon=True, name="turn-worker").start()

    # Watch parent — dies with main.py / the app.
    # ELO_NO_PARENT_WATCH=1 disables for standalone testing (Claude builder use only).
    if os.environ.get("ELO_NO_PARENT_WATCH", "0") != "1":
        _parent_pid = os.getppid()
        threading.Thread(target=_watch_parent, args=(_parent_pid, server), daemon=True).start()

    # WO-VISION-PROACTIVE-001: passive vision heartbeat (opt-in — ELO_VISION_PASSIVE=1)
    if os.environ.get("ELO_VISION_PASSIVE", "0") == "1":
        threading.Thread(target=_vision_heartbeat, daemon=True, name="vision-heartbeat").start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[eLo server] shutting down")
        _shutdown_cleanly(server)
