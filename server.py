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
from blender_bridge.state_writer import write as _state_write
from expression.expression_mapper import build_expression as _expr_build
from voice.voice_engine import speak as _voice_speak

# ── session state (shared across requests, protected by lock) ─────────────────

_lock            = threading.Lock()
_state           = None
_runtime_state   = None
_memory_pack     = {}
_vault_ctx       = ""
_last_inputs     = []
_last_avatar_cmd = None
_pscheduler      = _PresenceScheduler()
_behaviour_gate  = _BehaviourGate()
_fallback        = _MockBackend()

_PURE_GREETING_POOL = [
    "Hey.", "Hi.", "Good to have you back.", "Hey — good to be here.", "Hi there.",
]
_SOCIAL_GREETING_POOL = [
    "Good to see you.", "Same.", "Good to be here.",
    "Good to have you back.", "You too.", "Always good.",
]
_SELF_REF_TRIGGERS = ("how do you work", "how does elo work", "how are you built",
                      "what are you exactly", "how do you remember", "how do you think")
_SELF_REF_POOL = [
    "Attention layer first — I score what's relevant in memory. Then executive picks the response mode. Then I speak.",
    "I run a loop each turn: read what matters, decide what to do, respond. Each session connects to the last.",
    "I process what you say, find what's relevant, and respond. I keep what matters across sessions and drop the rest.",
]


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

        system = build_prompt(raw, vault_context=_vault_ctx,
                              state_context=state_manager.as_context_string(_state),
                              attention=attention_model, exec_decision=exec_decision,
                              graph_context=g_ctx)

        _is_self_ref = any(p in _raw_lower for p in _SELF_REF_TRIGGERS)
        backend_used = active_backend()

        if _cal_reason == "pure greeting":
            response, backend_used = random.choice(_PURE_GREETING_POOL), "direct"
        elif _cal_reason == "social greeting":
            response, backend_used = random.choice(_SOCIAL_GREETING_POOL), "direct"
        elif _is_self_ref:
            response, backend_used = random.choice(_SELF_REF_POOL), "direct"
        else:
            try:
                _enriched, _agent = _tool_enrich(raw)
                response, backend_used = router_route(system, _enriched, max_sentences=_max_s, action=_action)
                if _agent:
                    backend_used = f"{backend_used}+{_agent}"
            except Exception:
                response = _fallback.generate_response(raw, _action, {}, {}, {}, {})["response_text"]
                backend_used = "mock"

        # keyword-driven animation burst — fires async, never blocks response
        try:
            _keyword_motion_scan(raw)
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

        try:
            _tone_str = _state.get("emotional_history", [{}])[-1].get("tone", "present") if _state.get("emotional_history") else "present"
            _pstate   = _pstate_derive(_action, attention_model, response, _tone_str)
            _pscheduler.set(_pstate, hard=True)
            _pscheduler.post_response_settle()
            _cmd      = _avatar_cmd(_pstate)
            _cmd      = _avatar_rules(_cmd, _last_avatar_cmd)
            _last_avatar_cmd = _cmd
            _expr     = _expr_build(_pstate.mode, _action, _pstate.intensity)
            _state_write(_cmd, _expr, _presence)
        except Exception:
            pass

        _state = state_manager.update(
            _state, raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(_runtime_state),
        )
        state_manager.save(_state)

        # Speak response and drive lipsync blendshapes in a background thread
        try:
            _voice_speak(response)
        except Exception:
            pass

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
        from ambient.ambient_engine import stop as _ambient_stop
        _ambient_stop()
    except Exception:
        pass
    with _lock:
        if _state:
            _state_ref = state_manager.close_session(_state)
            state_manager.save(_state_ref)
            _continuity_update(_obs_get_log())
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
