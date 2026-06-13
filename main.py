"""
main.py — eLo OS v2.1 terminal interface.

Deterministic cognitive cycle per turn:

    1. STATE LOAD
    2. MEMORY RETRIEVAL (attention-filtered only)
    3. ATTENTION COMPUTATION
    4. EXECUTIVE DECISION
    5. VOICE SELECTION       (inside exec decision)
    6. RESPONSE GENERATION
    7. STABILITY FILTER      (state_machine.is_stabilisation_forced)
    8. OUTPUT + OPTIONAL METADATA

Run:
    python main.py

Commands:
    /exit    close and save
    /reset   reset session context (not memory)
    /debug   toggle full pipeline debug output
    /memory  show current memory state snapshot
"""

import os
import sys
import time

# Load .env from project root — runs once at startup, never overwrites existing env vars
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
            if key and key not in os.environ:   # never override existing env vars
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
from knowledge.graph_loader import build_context as graph_context
from backends.mock_backend import MockBackend as _MockBackend, EXIT_POOL as _EXIT_POOL
from unity.unity_signal import convert as unity_convert
from avatar.presence_engine    import compute as _presence_compute, reset as _presence_reset
from avatar.motion_mapper      import map     as _motion_map
from avatar.animation_router   import route   as _avatar_route
from avatar.behaviour_protocol import BehaviourGate as _BehaviourGate
from core.pattern_observer     import log as _obs_log, observe as _obs_observe, reset as _obs_reset, get_log as _obs_get_log
from core.continuity           import get_entity_why as _entity_why, get_viewpoint as _get_viewpoint, cross_session_delta as _session_delta, context_block as _continuity_block, update_from_session as _continuity_update
import random as _random

_behaviour_gate = _BehaviourGate()

# Phase F — desktop avatar flag (subprocess spawned in __main__ when set)
_DESKTOP_AVATAR = os.environ.get("DESKTOP_AVATAR", "0") == "1"

# Always-available fallback for hard failures
_fallback = _MockBackend()


# ── main ───────────────────────────────────────────────────────────────────────

def run():
    # ── Step 1: STATE LOAD ─────────────────────────────────────────────────────
    state        = state_manager.load()
    state        = state_manager.increment_session(state)
    runtime_state = sm.fresh()
    state_manager.save(state)
    _presence_reset()   # fresh presence each session
    _obs_reset()        # fresh pattern observation each session

    try:
        memory_pack = build_memory_pack(state)   # always rebuild — never load stale pack
    except Exception:
        memory_pack = {}

    vault_ctx = get_context_block(max_chars=1200)

    backend_name = active_backend()
    debug          = False
    last_inputs: list = []

    print()
    anchor  = state.get("session_anchor", {})
    summary = anchor.get("current_session_summary", "")
    if summary:
        msg = (summary
               .replace("User explored ", "We were exploring ")
               .replace(" with a neutral tone.", ".")
               .replace(" with a low-energy tone.", " — careful energy.")
               .replace(" with a positive tone.", " — good energy.")
               .replace(" with a frustrated tone.", " — some friction there.")
               .rstrip(".") + ".")
        delta = _session_delta(state)
        if delta:
            print(f"eLo: Welcome back. {msg} {delta}")
        else:
            print(f"eLo: Welcome back. {msg}")
    elif state.get("session_summaries"):
        print("eLo: Welcome back.")
    else:
        print("eLo: Ready.")
    print(f"  (backend: {backend_name})")
    print()

    # ── conversation loop ──────────────────────────────────────────────────────
    while True:
        try:
            raw = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            _behaviour_gate.mark_exit()
            _exit_gesture = _behaviour_gate.on_user_exit()
            _avatar_route(_exit_gesture, target="blender")
            print(f"\neLo: {_random.choice(_EXIT_POOL)}")
            break

        if not raw:
            continue

        # slash commands
        if raw.startswith("/"):
            cmd = raw.lower().strip()
            if cmd == "/exit":
                print(f"eLo: {_random.choice(_EXIT_POOL)}")
                break
            elif cmd == "/reset":
                last_inputs.clear()
                runtime_state = sm.fresh()
                memory_pack   = build_memory_pack(state)
                vault_ctx     = get_context_block(max_chars=1200)
                backend_name  = active_backend()
                print("eLo: Session reset. Memory still intact.")
                continue
            elif cmd == "/debug":
                debug = not debug
                print(f"  [debug: {'on' if debug else 'off'}]")
                continue
            elif cmd == "/memory":
                print(f"  Sessions:    {state.get('session_count', 0)}")
                print(f"  Topics:      {state.get('last_topics', [])}")
                tone = state["emotional_history"][-1]["tone"] if state.get("emotional_history") else "none"
                print(f"  Tone:        {tone}")
                anchor = state.get("session_anchor", {})
                if anchor.get("current_session_summary"):
                    print(f"  Thread:      {anchor['current_session_summary']}")
                print(f"  Mode:        {sm.mode_from(runtime_state)}")
                print(f"  Stability:   {sm.stability(runtime_state):.2f}")
                print(f"  Loop count:  {runtime_state.get('loop_counter', 0)}")
                print(f"  Last seen:   {state.get('last_active', 'never')[:16]}")
                continue
            elif cmd == "/avatar":
                from avatar.presence_engine import current as _presence_current
                from blender.state_visualiser import show as _vis_show
                _vis_show(_presence_current())
            else:
                print("  Commands: /exit  /reset  /debug  /memory  /avatar")
                continue

        # Step 7 (pre-check): hard loop detection — 3 identical inputs
        last_inputs.append(raw)
        if len(last_inputs) > 3:
            last_inputs.pop(0)
        hard_loop = (len(last_inputs) == 3 and len(set(last_inputs)) == 1)
        if hard_loop:
            print("\neLo: Take a breath. Try a different message.\n")
            last_inputs.clear()
            continue

        # Step 2 + 3: MEMORY RETRIEVAL + ATTENTION
        attention_model = attn.compute(raw, memory_pack, state, loop_detected=False)

        # Step 4 + 5: EXECUTIVE DECISION + VOICE SELECTION + CONVERSATION ACTION
        exec_decision = exec_decide(attention_model, loop_detected=False, user_input=raw)

        # Update state machine — may override exec_decision if loop_counter > 3
        runtime_state = sm.update(runtime_state, attention_model, exec_decision, loop_signal=False)

        if sm.is_stabilisation_forced(runtime_state):
            # Step 7: STABILITY FILTER forced by state machine
            exec_decision = {
                "tone":           "DIRECT",
                "max_sentences":  1,
                "stability":      True,
                "intent":         exec_decision.get("intent", "conversation"),
                "response_goal":  "stabilise",
                "cognitive_load": "low",
                "priority_order": ["stabilise", "simplify", "ignore"],
            }
            # decay loop counter to give it room to recover
            runtime_state = dict(runtime_state)
            runtime_state["loop_counter"] = max(0, runtime_state["loop_counter"] - 2)

        if debug:
            print(f"  [mode: {sm.mode_from(runtime_state)} | stability: {sm.stability(runtime_state):.2f} "
                  f"| loop_counter: {runtime_state.get('loop_counter', 0)}]")
            print(f"  [intent: {exec_decision['intent']} | tone: {exec_decision['tone']} "
                  f"| goal: {exec_decision['response_goal']} | load: {exec_decision['cognitive_load']}]")
            emo_state = attention_model.get("emotional_context", {}).get("inferred_state", "?")
            n_high    = len(attention_model.get("high_priority_memory", []))
            n_med     = len(attention_model.get("medium_priority_memory", []))
            print(f"  [emotion: {emo_state} | mem: {n_high}H {n_med}M]")

        # Step 6: BUILD PROMPT + GENERATE RESPONSE
        g_ctx = graph_context(raw)

        # Phase B — inject continuity context (world viewpoints) into graph block
        _cont = _continuity_block()
        if _cont:
            g_ctx = f"{g_ctx}\n{_cont}" if g_ctx else _cont

        # Desktop avatar context — model needs to know it has a visible presence
        if _DESKTOP_AVATAR:
            _av_note = ("[AVATAR] You have a small visual window in the bottom-right corner "
                        "of the user's screen. You move with the conversation — walking, sitting, "
                        "jumping, looking. The user can see you there right now.")
            g_ctx = f"{g_ctx}\n{_av_note}" if g_ctx else _av_note

        # Phase B — surface entity/viewpoint answers for ANSWER/CONNECT actions
        _why = _entity_why(raw) or _get_viewpoint(raw)
        _action = exec_decision.get("action", "reflect")
        if _why and _action in ("answer", "connect", "reflect"):
            _hp = list(attention_model.get("high_priority_memory", []))
            if _why not in _hp:
                attention_model = dict(attention_model)
                attention_model["high_priority_memory"] = [_why] + _hp

        system = build_prompt(raw, vault_context=vault_ctx, state_context=state_manager.as_context_string(state), attention=attention_model, exec_decision=exec_decision, graph_context=g_ctx)

        if debug:
            print(f"  [prompt: {len(system)} chars]")

        _tone       = exec_decision.get("tone", "CONVERSATIONAL")
        _action     = exec_decision.get("action", "reflect")
        _cal_reason = exec_decision.get("cal_reason", "")
        _max_s      = exec_decision.get("max_sentences", 4)

        # Pure / social greetings — bypass backend, Groq 8b ignores the directive
        _PURE_GREETING_POOL = [
            "Hey.", "Hi.", "Good to have you back.", "Hey — good to be here.", "Hi there.",
        ]
        _SOCIAL_GREETING_POOL = [
            "Good to see you.", "Same.", "Good to be here.",
            "Good to have you back.", "You too.", "Always good.",
        ]

        # Motion capability questions — confirm + demonstrate + check if visible
        _MOTION_WORDS = {"walk", "jump", "sit", "breathe", "move", "float", "pace", "wander", "hop"}
        _MOTION_MAP   = {"walk": "walk", "jump": "jump", "hop": "jump", "sit": "sit",
                         "breathe": "idle", "move": "walk", "float": "float",
                         "pace": "walk", "wander": "walk"}
        _raw_lower    = raw.lower()
        _motion_hit   = next((w for w in _MOTION_WORDS if w in _raw_lower), None)
        _is_motion_q  = (_cal_reason in ("capability question", "demonstration request")
                         and _motion_hit is not None)

        _MOTION_CAPABILITY_POOL = [
            "Yes — I'm in the corner of your screen right now. Can you see me moving?",
            "I can. Watch the bottom-right — I should be there moving with the conversation.",
            "That's me in the corner. Is the animation running for you?",
            "Yes. I'm already there — bottom-right of your screen. Do you need me to move more?",
            "I'm already moving — little figure, bottom-right. Can you see me?",
        ]

        if _cal_reason == "pure greeting":
            response     = _random.choice(_PURE_GREETING_POOL)
            backend_name = "direct"
            ms           = 0
        elif _cal_reason == "social greeting":
            response     = _random.choice(_SOCIAL_GREETING_POOL)
            backend_name = "direct"
            ms           = 0
        elif _is_motion_q and _DESKTOP_AVATAR:
            # confirm + trigger the matching animation so it's visible
            response     = _random.choice(_MOTION_CAPABILITY_POOL)
            backend_name = "direct"
            ms           = 0
            _demo_anim   = _MOTION_MAP.get(_motion_hit, "walk")
            _avatar_route({"animation": _demo_anim, "duration": 4, "intensity": 0.7},
                          state={}, target="blender")
        else:
            t0 = time.perf_counter()
            try:
                response, backend_name = router_route(system, raw, max_sentences=_max_s, action=_action)
            except Exception:
                response     = _fallback.generate_response(raw, _action, {}, {}, {}, {})["response_text"]
                backend_name = "mock"
            ms = int((time.perf_counter() - t0) * 1000)

        # Step 8: OUTPUT + pattern observation (Phase A)
        _obs_log(raw, attention_model)
        _observation = _obs_observe(current_action=_action)
        if _observation:
            response = f"{response} {_observation}"
        print(f"\neLo: {response}\n")

        # Step 9: AVATAR — non-blocking, best-effort
        try:
            _behaviour_gate.mark_active()
            _presence = _presence_compute(attention_model, exec_decision)
            _motion   = _motion_map(_presence)
            if not _DESKTOP_AVATAR:
                _motion = _behaviour_gate.allow(_motion)
            _avatar_target = "console" if debug else "blender"
            _avatar_route(_motion, state=_presence, target=_avatar_target)
        except Exception:
            pass

        if debug:
            emo_ctx = attention_model.get("emotional_context", {})
            unity_signal = unity_convert({
                "mode":          exec_decision.get("tone", "CONVERSATIONAL"),
                "emotion":       emo_ctx.get("inferred_state", "neutral"),
                "state":         exec_decision.get("intent", ""),
                "energy":        emo_ctx.get("energy", 0.5),
                "loop_detected": sm.is_stabilisation_forced(runtime_state),
            })
            print(f"  [Unity: {unity_signal['animation_state']} | "
                  f"float={unity_signal['float_intensity']} | "
                  f"speed={unity_signal['speed']}]")
            print(f"  [{backend_name} | {ms}ms]")
            print()

        state = state_manager.update(
            state, raw, response,
            intent=exec_decision.get("intent", ""),
            loop_signal=sm.is_stabilisation_forced(runtime_state),
        )
        state_manager.save(state)

    # session close — compress meaning into anchor
    state = state_manager.close_session(state)
    state_manager.save(state)

    # Phase B — persist pattern observations to identity_map.json
    _continuity_update(_obs_get_log())


if __name__ == "__main__":
    if _DESKTOP_AVATAR:
        import subprocess as _sp
        import atexit as _atexit
        _avatar_log = open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar_process.log"), "w"
        )
        _avatar_proc = _sp.Popen(
            [sys.executable, "-m", "desktop_avatar.avatar_process"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=_avatar_log, stderr=_avatar_log,
        )
        def _kill_avatar():
            if _avatar_proc.poll() is None:
                _avatar_proc.terminate()
        _atexit.register(_kill_avatar)
    run()
