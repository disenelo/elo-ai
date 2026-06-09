"""
main.py — eLo OS v1.0 terminal interface.

Run:
    python main.py

Commands during session:
    /exit    close and save
    /reset   reset session context (not memory)
    /debug   toggle debug logging
    /memory  show current memory state
"""

import os
import sys
import time

from memory import state_manager
from memory.obsidian_loader import get_context_block
from runtime.prompt_builder import build as build_prompt
from backends.mock_backend import MockBackend as _MockBackend

# Always-available fallback — used when Claude fails mid-session
_fallback = _MockBackend()


# ── backend setup ──────────────────────────────────────────────────────────────

def _pick_backend():
    """Return (backend_name, send_fn). send_fn(system, user_input) -> str."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            # smoke-test: verify the key works before committing to Claude
            client.models.list()

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

    # fallback mock
    def send_mock(system_prompt: str, user_input: str) -> str:
        result = _fallback.generate_response(user_input, "CONVERSATIONAL", {}, {}, {}, {})
        return result["response_text"]

    return "mock", send_mock


# ── main ───────────────────────────────────────────────────────────────────────

def run():
    state = state_manager.load()
    state = state_manager.increment_session(state)
    state_manager.save(state)

    vault_ctx    = get_context_block(max_chars=1200)
    backend_name, send = _pick_backend()
    debug        = False
    last_inputs: list = []   # loop detection — last 3 inputs

    print()
    if state.get("session_summaries"):
        last = state["session_summaries"][-1]
        print(f"eLo: Welcome back. Last time we talked about '{last['user'][:50]}'")
    else:
        print("eLo: Ready.")
    print(f"  (backend: {backend_name})")
    print()

    while True:
        try:
            raw = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\neLo: Saving and closing.")
            break

        if not raw:
            continue

        if raw.startswith("/"):
            cmd = raw.lower().strip()
            if cmd == "/exit":
                print("eLo: Saving. See you next time.")
                break
            elif cmd == "/reset":
                vault_ctx = get_context_block(max_chars=1200)
                last_inputs.clear()
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

        # lightweight loop detection — 3 identical inputs in a row
        last_inputs.append(raw)
        if len(last_inputs) > 3:
            last_inputs.pop(0)
        if len(last_inputs) == 3 and len(set(last_inputs)) == 1:
            print("\neLo: Take a breath. Try a different message.\n")
            last_inputs.clear()
            continue

        state_ctx = state_manager.as_context_string(state)
        system    = build_prompt(raw, state_ctx, vault_ctx)

        if debug:
            print(f"  [prompt: {len(system)} chars | vault: {len(vault_ctx)} chars]")

        t0 = time.perf_counter()
        try:
            response = send(system, raw)
        except Exception:
            # Claude failed mid-session — use mock for this turn, stay in loop
            response = _fallback.generate_response(raw, "CONVERSATIONAL", {}, {}, {}, {})["response_text"]
        ms = int((time.perf_counter() - t0) * 1000)

        if debug:
            print(f"  [{backend_name} | {ms}ms]")

        print(f"\neLo: {response}\n")

        state = state_manager.update(state, raw, response)
        state_manager.save(state)

    # close session — compress experience into session anchor
    state = state_manager.close_session(state)
    state_manager.save(state)


if __name__ == "__main__":
    run()
