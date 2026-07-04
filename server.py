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
    """Patch blender_state.json with a short-lived greeting event so Unity can react."""
    import time as _time
    try:
        if os.path.exists(_BLENDER_STATE_PATH):
            with open(_BLENDER_STATE_PATH, "r") as _f:
                _st = json.load(_f)
        else:
            _st = {}
        _st["greeting_event"] = {"type": greeting_type, "ts": int(_time.time())}
        with open(_BLENDER_STATE_PATH, "w") as _f:
            json.dump(_st, _f)
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
    """Strip asterisk stage-directions (*leans in*, *smiles* etc.) from any response."""
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
                      "what are you exactly", "how do you remember", "how do you think")
_SELF_REF_POOL = [
    "Attention layer first — I score what's relevant in memory. Then executive picks the response mode. Then I speak.",
    "I run a loop each turn: read what matters, decide what to do, respond. Each session connects to the last.",
    "I process what you say, find what's relevant, and respond. I keep what matters across sessions and drop the rest.",
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


def _init_session():
    global _state, _runtime_state, _memory_pack, _vault_ctx
    _state        = state_manager.load()
    _state        = state_manager.increment_session(_state)
    _runtime_state = sm.fresh()
    state_manager.save(_state)
    _presence_reset()
    _obs_reset()
    _memory_pack  = build_memory_pack(_state)
    _vault_ctx    = get_context_block(max_chars=1200)
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

        attention_model = attn.compute(raw, _memory_pack, _state, loop_detected=False)
        exec_decision   = exec_decide(attention_model, loop_detected=False, user_input=raw)
        _runtime_state  = sm.update(_runtime_state, attention_model, exec_decision, loop_signal=False)

        if sm.is_stabilisation_forced(_runtime_state):
            exec_decision = {
                "tone": "DIRECT", "max_sentences": 1, "stability": True,
                "intent": exec_decision.get("intent", "conversation"),
                "response_goal": "stabilise", "cognitive_load": "low",
                "priority_order": ["stabilise", "simplify", "ignore"],
            }
            _runtime_state = dict(_runtime_state)
            _runtime_state["loop_counter"] = max(0, _runtime_state["loop_counter"] - 2)

        _action     = exec_decision.get("action", "reflect")
        _cal_reason = exec_decision.get("cal_reason", "")
        _max_s      = exec_decision.get("max_sentences", 4)
        _raw_lower  = raw.lower()

        g_ctx = graph_context(raw)
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

        _av_note = ("[AVATAR] You are visible as a 3D character in the user's Desktop Buddy app. "
                    "You move with the conversation. The user can see and talk to you there.")
        g_ctx = f"{g_ctx}\n{_av_note}" if g_ctx else _av_note

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
            _attention_with_exec["_exec_decision"] = exec_decision
            _plan = _spine_run(raw, state=_state, attention=_attention_with_exec)
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
                    response = f"Tried, but something blocked it — {_sys_err}"
            if "greeting" in (_plan.cal_reason or ""):
                _signal_greeting_event("direct")

        # ── Spine needs LLM: run capabilities then backend ────────────────────
        else:
            try:
                _enriched, _agent = _tool_enrich(raw)
                response, backend_used = router_route(
                    system, _enriched, max_sentences=_max_s, action=_action
                )
                if _agent:
                    backend_used = f"{backend_used}+{_agent}"
            except Exception:
                response = _fallback.generate_response(raw, _action, {}, {}, {}, {})["response_text"]
                backend_used = "mock"

        # ── Update spine session continuity ───────────────────────────────────
        try:
            from runtime.spine.spine import update_session as _spine_update
            _spine_update(raw, response)
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
        except Exception:
            pass

        # Write blender state — isolated so presence_plan always reaches the file.
        try:
            _pp = (_plan.presence_plan if _plan is not None and _plan.presence_plan else None)
            if _pp:
                _state_write_presence(_cmd, _expr, _presence, _emotion, _pp)
            else:
                _state_write(_cmd, _expr, _presence, _emotion)
        except Exception:
            pass

        _state = state_manager.update(
            _state, raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(_runtime_state),
        )
        state_manager.save(_state)

        response = _sanitise(response)

        # Speak response — suppressed if user is away (presence.json → state == "away")
        try:
            if not _is_user_away():
                _voice_speak(response)
        except Exception:
            pass

        print(f"[eLo] backend={backend_used} action={_action}", flush=True)
        return {
            "response": response,
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
                else:
                    self._send_json(400, {"error": f"unknown action: {action}"})
                    return
                self._send_json(200, {"ok": True, "action": action})
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
