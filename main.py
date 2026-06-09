"""
main.py — eLo OS v2 terminal interface.

Cognitive cycle per turn (8 steps):
    1. Receive input
    2. Retrieve relevant memory (attention-filtered only)
    3. Compute attention model
    4. Compute executive function decision (tone + stability)
    5. Select voice tone (inside exec decision)
    6. Generate response
    7. Apply loop + safety filters
    8. Output response + optional Unity metadata

Run:
    python main.py

Commands:
    /exit    close and save
    /reset   reset session context (not memory)
    /debug   toggle debug output (includes Unity signals)
    /memory  show current state snapshot
"""

import os
import time

from memory import state_manager
from memory.obsidian_loader import get_context_block
from memory.memory_pack_builder import load as load_memory_pack, build as build_memory_pack
from core import attention as attn
from runtime.executive import decide as exec_decide
from runtime.prompt_builder import build as build_prompt
from backends.mock_backend import MockBackend as _MockBackend
from unity.unity_signal import convert as unity_convert

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
    # ── startup ────────────────────────────────────────────────────────────────
    state = state_manager.load()
    state = state_manager.increment_session(state)
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
    if state.get("session_summaries"):
        last = state["session_summaries"][-1]
        print(f"eLo: Welcome back. Last time we talked about '{last['user'][:50]}'")
    else:
        print("eLo: Ready.")
    print(f"  (backend: {backend_name})")
    print()

    # ── conversation loop ──────────────────────────────────────────────────────
    while True:
        # Step 1: receive input
        try:
            raw = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\neLo: Saving and closing.")
            break

        if not raw:
            continue

        # slash commands
        if raw.startswith("/"):
            cmd = raw.lower().strip()
            if cmd == "/exit":
                print("eLo: Saving. See you next time.")
                break
            elif cmd == "/reset":
                last_inputs.clear()
                memory_pack = build_memory_pack(state)
                print("eLo: Session reset. Memory still intact.")
                continue
            elif cmd == "/debug":
                debug = not debug
                print(f"  [debug: {'on' if debug else 'off'}]")
                continue
            elif cmd == "/memory":
                print(f"  Sessions:  {state.get('session_count', 0)}")
                print(f"  Topics:    {state.get('last_topics', [])}")
                tone = state["emotional_history"][-1]["tone"] if state.get("emotional_history") else "none"
                print(f"  Tone:      {tone}")
                anchor = state.get("session_anchor", {})
                if anchor.get("current_session_summary"):
                    print(f"  Thread:    {anchor['current_session_summary']}")
                print(f"  Last seen: {state.get('last_active', 'never')[:16]}")
                continue
            else:
                print("  Commands: /exit  /reset  /debug  /memory")
                continue

        # Step 7 (pre-check): hard loop detection
        last_inputs.append(raw)
        if len(last_inputs) > 3:
            last_inputs.pop(0)
        loop_detected = (len(last_inputs) == 3 and len(set(last_inputs)) == 1)
        if loop_detected:
            print("\neLo: Take a breath. Try a different message.\n")
            last_inputs.clear()
            continue

        # Step 2 + 3: memory retrieval + attention model
        attention_model = attn.compute(raw, memory_pack, state, loop_detected=False)

        # Step 4 + 5: executive function + voice tone
        exec_decision = exec_decide(attention_model, loop_detected=False)

        if debug:
            print(f"  [intent: {exec_decision['intent']} | tone: {exec_decision['tone']} "
                  f"| stability: {exec_decision['stability']}]")
            emo_state = attention_model.get("emotional_context", {}).get("inferred_state", "?")
            n_high    = len(attention_model.get("high_priority_memory", []))
            n_med     = len(attention_model.get("medium_priority_memory", []))
            print(f"  [emotion: {emo_state} | mem: {n_high}H {n_med}M]")

        # Step 6: build prompt + generate response
        system = build_prompt(raw, attention=attention_model, exec_decision=exec_decision)

        if debug:
            print(f"  [prompt: {len(system)} chars]")

        t0 = time.perf_counter()
        try:
            response = send(system, raw)
        except Exception:
            response = _fallback.generate_response(raw, "CONVERSATIONAL", {}, {}, {}, {})["response_text"]
        ms = int((time.perf_counter() - t0) * 1000)

        # Step 8: output response + optional Unity metadata
        print(f"\neLo: {response}\n")

        if debug:
            emo_ctx = attention_model.get("emotional_context", {})
            unity_signal = unity_convert({
                "mode":          exec_decision.get("tone", "CONVERSATIONAL"),
                "emotion":       emo_ctx.get("inferred_state", "neutral"),
                "state":         exec_decision.get("intent", ""),
                "energy":        emo_ctx.get("energy", 0.5),
                "loop_detected": False,
            })
            print(f"  [Unity: {unity_signal['animation_state']} | "
                  f"float={unity_signal['float_intensity']} | "
                  f"speed={unity_signal['speed']}]")
            print(f"  [{backend_name} | {ms}ms]")
            print()

        state = state_manager.update(state, raw, response)
        state_manager.save(state)

    # session close — compress experience into anchor
    state = state_manager.close_session(state)
    state_manager.save(state)


if __name__ == "__main__":
    run()
