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
from runtime.backend_router import route as router_route, active_backend, normalise
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

# ── session state (shared across requests, protected by lock) ─────────────────

_lock            = threading.Lock()
_state           = None
_obs_store       = _ObsStore()   # accumulates user messages across this session
_runtime_state   = None
_memory_pack     = {}
_vault_ctx       = ""
_last_inputs     = []
_last_avatar_cmd = None
_last_pp         = None   # last known presence_plan — survives tool-call turns
_pscheduler      = _PresenceScheduler()
_behaviour_gate  = _BehaviourGate()

# ── personality profile (loaded once at startup, injected into every prompt) ──
try:
    _personality_profile = _load_profile(project_ids=["elo-planet", "elo-robot", "plushies"])
except Exception:
    _personality_profile = None
_fallback        = _MockBackend()

_BLENDER_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "blender_state.json")


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

# ── Animation play commands ────────────────────────────────────────────────────
_ANIM_CMD_MAP = [
    (_re.compile(r'\b(run\s+and\s+jump|do\s+a\s+jump|give\s+me\s+a\s+jump|jump\s+for\s+me|jump!)\b', _re.I), "jump"),
    (_re.compile(r'\b(wave|wave\s+at\s+me|give\s+me\s+a\s+wave)\b', _re.I), "wave"),
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
    # Hop / roam — direct commands
    "hop on":              "explore",
    "hop to":              "explore",
    "hop over":            "explore",
    "nearest window":      "explore",
    "next window":         "explore",
    "go explore":          "explore",
    "have a look around":  "explore",
    "look around":         "explore",
    # Sit with David — direct commands
    "come here":           {"name": "sit", "target": "cursor"},
    "come to me":          {"name": "sit", "target": "cursor"},
    "sit with me":         {"name": "sit", "target": "cursor"},
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
}

def _signal_word_intent(raw: str) -> "str | dict | None":
    raw_l = raw.lower()
    for phrase, directive in _SIGNAL_WORDS.items():
        if phrase in raw_l:
            return directive
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

    # Silence / give-space — always wins
    if tone == "SILENCE-AWARE" or action == "silence":
        return "step_out"

    # Layer 3 — emotional safety: negative high → ground immediately
    if valence == "negative_high":
        return "grounding"

    # Layer 1 — signal words: direct word→body mapping, high priority
    _sw = _signal_word_intent(raw)
    if _sw:
        return _sw

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


def _is_file_cancel(text: str) -> bool:
    t = text.lower().strip()
    return any(k in t for k in ("cancel", "don't", "dont", "stop", "no", "nope",
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
    "I run a loop each turn: read what matters, decide what to do, respond. Each session connects to the last.",
    "I process what you say, find what's relevant, and respond. I keep what matters across sessions and drop the rest.",
    "Yes — memory carries across sessions. Recent things are closer; older things are further but still there.",
    "Weather, time, calendar, system control — and I think alongside you and carry context across sessions.",
    "Practical stuff: weather, time, calendar, system control. And memory — what matters stays between sessions.",
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
)
_MEMORY_RECALL_POOL = [
    "What we've been building together — the OS, the game, the robot. Recent context loads from notes at the start of each session.",
    "Session context from notes — the important stuff carries forward. What do you want to pick up?",
    "I hold what matters session to session. The vault carries the weight — what's on your mind?",
    "Recent sessions, open threads, what we've been working on. It's there. What do you need?",
    "What's in the vault is what we decided to keep — the key decisions, the direction. Ask me something specific.",
]

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


def _voice_settings_snapshot() -> dict:
    """Current ElevenLabs voice params as a dict — read from live os.environ."""
    return {
        "stability":  float(os.environ.get("ELEVENLABS_STABILITY",  "0.22")),
        "similarity": float(os.environ.get("ELEVENLABS_SIMILARITY", "0.55")),
        "style":      float(os.environ.get("ELEVENLABS_STYLE",       "0.15")),
        "speed":      float(os.environ.get("ELEVENLABS_SPEED",       "1.09")),
    }


def _init_session():
    global _state, _runtime_state, _memory_pack, _vault_ctx
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
    print(f"[eLo server] session {_state.get('session_count', 1)} started")

    try:
        from ambient.ambient_engine import start as _ambient_start
        _ambient_start(unity_present=True)
        print("[eLo server] ambient engine started")
    except Exception as _ae:
        print(f"[eLo server] ambient engine skipped: {_ae}")


def _process_turn(raw: str) -> dict:
    """Run one cognitive cycle. Thread-safe via _lock. Returns response dict."""
    global _state, _runtime_state, _last_inputs, _last_avatar_cmd

    with _lock:
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

        attention_model = attn.compute(raw, _memory_pack, _state, loop_detected=False)
        exec_decision   = exec_decide(attention_model, loop_detected=False, user_input=raw)
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
            "that {_uname} did not mention in this turn. If you did not observe it directly, do not say it."
        ).replace("{_uname}", _uname)
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

        _mode_str = exec_decision.get("mode", "CONVERSATIONAL") if exec_decision else "CONVERSATIONAL"
        _pers_block = _personality_profile.to_prompt_block(_mode_str) if _personality_profile else ""
        system = build_prompt(raw, vault_context=_vault_ctx,
                              state_context=state_manager.as_context_string(_state),
                              attention=attention_model, exec_decision=exec_decision,
                              graph_context=g_ctx, personality_block=_pers_block)

        backend_used = active_backend()

        # ── THE COGNITIVE SPINE ───────────────────────────────────────────────
        # One call. One decision. Everything downstream reads from the plan.
        # Attention + executive were already computed above — pass them in
        # so the spine doesn't recompute. The spine's language + capability
        # faculties run fresh; executive decision is reused from above.
        _plan = None
        try:
            from runtime.spine.spine import run as _spine_run, update_session as _spine_update
            _attention_with_exec = dict(attention_model)
            # SPINE CONVENIENCE — _exec_decision injected for downstream spine access.
            # Not an AttentionSnapshot field — a transport convenience only.
            # See: engineering/proofs/04_attention_proof.md § V2
            _attention_with_exec["_exec_decision"] = exec_decision
            _plan = _spine_run(raw, state=_state, attention=_attention_with_exec,
                               memory_pack=_vault_ctx)
        except Exception as _spine_err:
            import sys as _sys; print(f"[spine] FAILED: {_spine_err}", file=_sys.stderr)

        # ── Multilingual greeting (highest priority, checked before spine pools) ──
        _lang_query = _detect_language_query(_raw_lower)
        if _lang_query:
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
            if "greeting" in (_plan.cal_reason or ""):
                _signal_greeting_event("direct")

        # ── Spine needs LLM: run capabilities then backend ────────────────────
        else:
            try:
                # Control Plane context — appended to system prompt just before LLM call.
                if _plan and getattr(_plan, "control_context", ""):
                    system = system + "\n\n" + _plan.control_context

                _enriched, _agent = _tool_enrich(raw)
                response, backend_used = router_route(
                    system, _enriched, max_sentences=_max_s, action=_action
                )
                if _agent:
                    backend_used = f"{backend_used}+{_agent}"
            except Exception as _route_err:
                import sys as _sys; print(f"[eLo] router failed: {_route_err}", file=_sys.stderr)
                response = "Not connecting right now. Try again in a moment."
                backend_used = "mock(fallback)"

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

        # Write blender state — isolated so presence_plan always reaches the file.
        # _last_pp caches the last known plan so tool-call turns don't reset glow to fallback.
        global _last_pp
        try:
            _pp = (_plan.presence_plan if _plan is not None and _plan.presence_plan else None)
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
            if _pp:
                _last_pp = _pp
                _state_write_presence(_cmd, _expr, _presence, _emotion, _pp, gaze=_gaze,
                                      intent=_mv_intent, trigger=_mv_trigger, gesture=_mv_gesture)
            elif _last_pp:
                _state_write_presence(_cmd, _expr, _presence, _emotion, _last_pp, gaze=_gaze,
                                      intent=_mv_intent, trigger=_mv_trigger, gesture=_mv_gesture)
            else:
                _state_write(_cmd, _expr, _presence, _emotion, gaze=_gaze,
                             intent=_mv_intent, trigger=_mv_trigger, gesture=_mv_gesture)
        except Exception:
            pass

        _state = state_manager.update(
            _state, raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(_runtime_state),
        )
        state_manager.save(_state)

        response = _sanitise(response)

        # ── Multi-bubble split ────────────────────────────────────────────────
        # Split on paragraph breaks → one bubble per paragraph.
        # TTS reads only the first bubble (or up to ELO_TTS_MAX_CHARS chars)
        # so eLo doesn't burn tokens reading a long plan aloud.
        _bubbles = [b.strip() for b in response.split("\n\n") if b.strip()] or [response]

        _tts_max  = int(os.environ.get("ELO_TTS_MAX_CHARS", "160"))
        _tts_text = _bubbles[0] if _bubbles else response
        if len(_tts_text) > _tts_max:
            # cut at last sentence end before the cap
            _cut = _tts_text[:_tts_max].rfind(". ")
            _tts_text = _tts_text[:_cut + 1] if _cut > 50 else _tts_text[:_tts_max]

        # ── DELIVERY MECHANISM: Voice ──────────────────────────────────────────
        # Voice is a transport layer for response content — NOT an embodiment.
        # It does not interpret motion, expression, or state signals.
        # Synchronous by design: ensures audio plays in sequence with response.
        # See: engineering/proofs/08_cross_embodiment_proof.md § Voice positioning
        try:
            if not _is_user_away() and not _is_calm_mode():
                _voice_speak(_tts_text)
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
    # personality drift — update slow drift from this session's emotional history
    try:
        if _state:
            _ps = _personality_drift.load()
            _ps = _personality_drift.update(
                _ps,
                _state.get("emotional_history", []),
                _state.get("session_summaries", []),
            )
            _personality_drift.save(_ps)
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

    server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    print(f"[eLo server] listening on http://localhost:{PORT}")
    print(f"[eLo server] POST /chat  {{\"text\": \"hello\"}}")
    print(f"[eLo server] GET  /ping  →  {{\"ok\": true}}")
    print()

    # Watch parent — dies with main.py / the app
    _parent_pid = os.getppid()
    threading.Thread(target=_watch_parent, args=(_parent_pid, server), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[eLo server] shutting down")
        _shutdown_cleanly(server)
