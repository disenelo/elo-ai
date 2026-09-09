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
from presence.presence_engine    import derive as _pstate_derive
from presence.presence_scheduler import PresenceScheduler as _PresenceScheduler
from avatar.avatar_controller    import build_command as _avatar_cmd
from avatar.avatar_rules         import apply as _avatar_rules
from blender_bridge.state_writer import write as _state_write
from expression.expression_mapper import build_expression as _expr_build
import random as _random

_pscheduler = _PresenceScheduler()

_behaviour_gate = _BehaviourGate()

# Phase F — desktop avatar flag (subprocess spawned in __main__ when set)
_DESKTOP_AVATAR = os.environ.get("DESKTOP_AVATAR", "0") == "1"

# Dataset collection flag — passive capture, no behaviour change
_ELO_COLLECT = os.environ.get("ELO_COLLECT", "false").lower() == "true"

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

    # Dataset collection — passive, no behaviour change
    _collector = None
    if _ELO_COLLECT:
        try:
            from training.collector import Collector as _Collector
            _collector = _Collector(
                base_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasets")
            )
        except Exception:
            pass

    vault_ctx = get_context_block(max_chars=1200)

    backend_name     = active_backend()
    debug            = False
    last_inputs: list = []
    _last_avatar_cmd: dict | None = None

    print()
    try:
        from continuity.continuity_engine  import from_state  as _cont_from_state
        from continuity.continuity_summary import startup_message as _cont_startup
        _cont_state = _cont_from_state(state)
        _greeting   = _cont_startup(_cont_state)
    except Exception:
        _cont_state = None
        anchor  = state.get("session_anchor", {})
        summary = anchor.get("current_session_summary", "")
        if summary:
            msg = (summary
                   .replace("User explored ", "We were exploring ")
                   .replace(" with a neutral tone.", ".")
                   .rstrip(".") + ".")
            _greeting = f"Welcome back. {msg}"
        elif state.get("session_summaries"):
            _greeting = "Welcome back."
        else:
            _greeting = "Ready."

    if _cont_state and not _cont_state.is_empty():
        delta = _session_delta(state)
        if delta:
            print(f"eLo: {_greeting} {delta}")
        else:
            print(f"eLo: {_greeting}")
    else:
        print(f"eLo: {_greeting}")
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

        # Relationship layer — 1 observation + 1 connection + 1 viewpoint max
        try:
            from relationships.relationship_engine import inject as _rel_inject
            _rel_ctx = _rel_inject(raw)
            if _rel_ctx:
                g_ctx = f"{g_ctx}\n{_rel_ctx}" if g_ctx else _rel_ctx
        except Exception:
            pass

        # Desktop shadow mode (STEP 07) — observe what's open, inject if meaningful
        try:
            from desktop.desktop_presence import shadow_context as _shadow_ctx
            _dctx = _shadow_ctx()
            if _dctx:
                g_ctx = f"{g_ctx}\n{_dctx}" if g_ctx else _dctx
        except Exception:
            pass

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

        _raw_lower = raw.lower()

        # Self-referential "how do you work" questions — deterministic bypass, mock can't answer these
        _SELF_REF_TRIGGERS = ("how do you work", "how does elo work", "how are you built",
                              "what are you exactly", "how do you remember", "how do you think")
        _SELF_REF_POOL = [
            "Attention layer first — I score what's relevant in memory. Then executive picks the response mode. Then I speak.",
            "I run a loop each turn: read what matters, decide what to do, respond. Each session connects to the last.",
            "I process what you say, find what's relevant, and respond. I keep what matters across sessions and drop the rest.",
        ]
        _is_self_ref = any(p in _raw_lower for p in _SELF_REF_TRIGGERS)

        # Motion capability questions — confirm + demonstrate + check if visible
        _MOTION_WORDS = {"walk", "jump", "sit", "breathe", "move", "float", "pace", "wander", "hop"}
        _MOTION_MAP   = {"walk": "walk", "jump": "jump", "hop": "jump", "sit": "sit",
                         "breathe": "idle", "move": "walk", "float": "float",
                         "pace": "walk", "wander": "walk"}
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
        elif _is_self_ref:
            response     = _random.choice(_SELF_REF_POOL)
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

        # WKG write — fire when turn content matches meaningful categories
        _spg_wkg_cats: list = []
        try:
            from core.memory_engine import _classify_memory_categories as _wkg_cat_classify
            _wkg_content = (raw + " " + response)[:1000]
            _spg_wkg_cats = _wkg_cat_classify(_wkg_content)
            if _spg_wkg_cats:
                from runtime.wkg_faculty import (
                    search_entities as _wkg_search, create_entity as _wkg_create,
                    record_claim as _wkg_record_claim, _load as _wkg_load,
                )
                _wkg_david = _wkg_search("David Charles")
                _wkg_david_id = _wkg_david[0]["entity_id"] if _wkg_david else _wkg_create(
                    "PERSON", "David Charles", aliases=["David"],
                    description="Creator of eLo and DISENELO")["entity_id"]
                _wkg_label = _spg_wkg_cats[0].replace("_", " ")
                _wkg_topic = _wkg_search(_wkg_label)
                _wkg_topic_id = _wkg_topic[0]["entity_id"] if _wkg_topic else _wkg_create(
                    "CONCEPT", _wkg_label,
                    description=f"Topic from conversation: {raw[:80]}")["entity_id"]
                if "ASSOCIATED_WITH" in _wkg_load("relationship_types"):
                    _wkg_record_claim(
                        subject_entity_id=_wkg_david_id,
                        relationship_type="ASSOCIATED_WITH",
                        object_entity_id=_wkg_topic_id,
                        epistemic_class="SOURCE_ATTRIBUTED",
                        source_id="main_loop",
                        confidence=0.7,
                    )
        except Exception:
            pass

        # WO-SPG-HOOKS-001: SPG tap — memory_write after WKG write
        # WO-SPG-SIGNIFICANCE-001: compute significance before write so entries aren't hollow
        try:
            from memory.spg_capture import get_capture as _spg_get
            _spg_sig: dict = {}
            try:
                from runtime.significance_faculty import compute_significance as _spg_sig_compute
                _spg_sig = _spg_sig_compute({}, text_input=(raw + " " + response)[:500])
            except Exception:
                pass
            _spg_get().log(
                "memory_write",
                memory_keys=_spg_wkg_cats[:1],
                context_tags=_spg_wkg_cats[:2],
                embodiment="terminal",
                significance=_spg_sig,
            )
        except Exception:
            pass

        # WO-112: decision journal — record every turn with confidence + candidates
        try:
            from self.decision_journal import record as _dj_record
            _dj_record(
                turn=raw,
                action=_action,
                exec_decision=exec_decision,
                backend=backend_name,
                outcome="success",
                trigger_source="user_message",
            )
        except Exception:
            pass

        # Step 9: AVATAR — non-blocking, best-effort
        _presence = {}
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

        # Presence Runtime (STEP 03) + Avatar Core (STEP 04) + Blender bridge (STEP 05)
        try:
            _tone   = state.get("emotional_history", [{}])[-1].get("tone", "present") if state.get("emotional_history") else "present"
            _pstate = _pstate_derive(_action, attention_model, response, _tone)
            _pscheduler.set(_pstate, hard=True)
            _pscheduler.post_response_settle()
            _cmd    = _avatar_cmd(_pstate)
            _cmd    = _avatar_rules(_cmd, _last_avatar_cmd)
            _last_avatar_cmd = _cmd
            _expr   = _expr_build(_pstate.mode, _action, _pstate.intensity)
            _state_write(_cmd, _expr, _presence)
        except Exception:
            pass

        # Passive dataset capture — after presence is computed, before state update
        if _collector is not None:
            try:
                _collector.record(raw, response, backend_name, exec_decision,
                                  attention_model, _presence)
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

    if _collector is not None:
        try:
            _summary = _collector.close()
            if _summary.get("turns", 0) > 0:
                print(f"  [dataset: {_summary['turns']} turns saved]")
        except Exception:
            pass


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
