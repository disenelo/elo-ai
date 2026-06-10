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

from memory import state_manager
from memory.obsidian_loader import get_context_block
from memory.memory_pack_builder import load as load_memory_pack, build as build_memory_pack
from core import attention as attn
from runtime.executive import decide as exec_decide
from runtime import state_machine as sm
from runtime.prompt_builder import build as build_prompt
from backends.mock_backend import MockBackend as _MockBackend, EXIT_POOL as _EXIT_POOL
from unity.unity_signal import convert as unity_convert
import random as _random

# Always-available fallback — used when Claude fails mid-session
_fallback = _MockBackend()


# ── backend setup ──────────────────────────────────────────────────────────────

def _pick_backend():
    """Return (backend_name, send_fn). Falls back to mock if Claude unavailable."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            client.models.list()   # smoke-test key validity

            def send_claude(system_prompt: str, user_input: str) -> str:
                msg = client.messages.create(
                    model      = os.environ.get("ELO_MODEL", "claude-sonnet-4-5"),
                    max_tokens = 512,
                    system     = system_prompt,
                    messages   = [{"role": "user", "content": user_input}],
                )
                return msg.content[0].text.strip()

            return "claude", send_claude
        except Exception:
            pass

    def send_mock(system_prompt: str, user_input: str) -> str:
        result = _fallback.generate_response(user_input, "CONVERSATIONAL", {}, {}, {}, {})
        return result["response_text"]

    return "mock", send_mock


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

    backend_name, send = _pick_backend()
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

        # Step 4 + 5: EXECUTIVE DECISION + VOICE SELECTION
        exec_decision = exec_decide(attention_model, loop_detected=False)

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
        system = build_prompt(raw, attention=attention_model, exec_decision=exec_decision)

        if debug:
            print(f"  [prompt: {len(system)} chars]")

        _tone = exec_decision.get("tone", "CONVERSATIONAL")
        t0 = time.perf_counter()
        try:
            if backend_name == "mock":
                # pass the exec_decision tone so mock uses the right response pool
                response = _fallback.generate_response(raw, _tone, {}, {}, {}, {})["response_text"]
            else:
                response = send(system, raw)
        except Exception:
            response = _fallback.generate_response(raw, _tone, {}, {}, {}, {})["response_text"]
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
