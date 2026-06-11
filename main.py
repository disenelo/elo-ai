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
from memory.memory_pack_builder import load as load_memory_pack, build as build_memory_pack
from core import attention as attn
from runtime.executive import decide as exec_decide
from runtime import state_machine as sm
from runtime.prompt_builder import build as build_prompt
from runtime.backend_router import route as router_route, active_backend, normalise
from knowledge.graph_loader import build_context as graph_context
from backends.mock_backend import MockBackend as _MockBackend, EXIT_POOL as _EXIT_POOL
from unity.unity_signal import convert as unity_convert
import random as _random

# Always-available fallback for hard failures
_fallback = _MockBackend()


# ── main ───────────────────────────────────────────────────────────────────────

def run():
    # ── Step 1: STATE LOAD ─────────────────────────────────────────────────────
    state        = state_manager.load()
    state        = state_manager.increment_session(state)
    runtime_state = sm.fresh()
    state_manager.save(state)

    try:
        memory_pack = load_memory_pack()
        if not memory_pack:
            memory_pack = build_memory_pack(state)
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
        # transform "User explored X with Y tone." → "We were exploring X."
        msg = (summary
               .replace("User explored ", "We were exploring ")
               .replace(" with a neutral tone.", ".")
               .replace(" with a low-energy tone.", " — careful energy.")
               .replace(" with a positive tone.", " — good energy.")
               .replace(" with a frustrated tone.", " — some friction there.")
               .rstrip(".") + ".")
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
            else:
                print("  Commands: /exit  /reset  /debug  /memory")
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
        g_ctx  = graph_context(raw)
        system = build_prompt(raw, vault_context=vault_ctx, attention=attention_model, exec_decision=exec_decision, graph_context=g_ctx)

        if debug:
            print(f"  [prompt: {len(system)} chars]")

        _tone      = exec_decision.get("tone", "CONVERSATIONAL")
        _action    = exec_decision.get("action", "reflect")   # conversation action for mock routing
        _max_s     = exec_decision.get("max_sentences", 4)
        t0 = time.perf_counter()
        try:
            response, backend_name = router_route(system, raw, max_sentences=_max_s, action=_action)
        except Exception:
            # hard fallback — pass action as mode so mock uses the right pool
            response   = _fallback.generate_response(raw, _action, {}, {}, {}, {})["response_text"]
            backend_name = "mock"
        ms = int((time.perf_counter() - t0) * 1000)

        # Step 8: OUTPUT + OPTIONAL METADATA
        print(f"\neLo: {response}\n")

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


if __name__ == "__main__":
    run()
