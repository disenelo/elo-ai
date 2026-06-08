"""
feel_test.py — eLo AI conversational feel test loop.

Lightweight standalone loop for testing conversational behaviour
without the full memory engine. Uses simulate_elo_response() which
applies all behavioural rules from ELO_BEHAVIOUR_SPEC.md.

Usage:
    python feel_test.py

Commands:
    /mode studio|companion|adventure
    /memory <text>    — inject a fake memory signal to test influence
    /exit
"""

import sys
from offline_engine import generate_offline_response


def simulate_elo_response(
    user_input: str,
    memory: dict = None,
    mode: str = "companion",
    debug: bool = False,
):
    """
    Apply eLo behavioural rules to user_input and return a response.

    Pure behaviour simulation — no API calls, no external dependencies.
    Applies: grounding, imagination, memory influence, contradiction handling.

    Args:
        user_input: Raw text from the user.
        memory:     Optional dict with memory influence signals.
                    Use build_memory_influence() from memory_engine for real signals,
                    or pass a plain dict for manual injection:
                        {"returning_theme": "...", "tone_signal": "distorted", ...}
        mode:       "studio" | "companion" | "adventure"
        debug:      If True, returns (response, reasoning) tuple.

    Returns:
        Response string, or (response, reasoning_dict) if debug=True.
    """
    return generate_offline_response(
        user_input=user_input,
        memory=memory or {},
        mode=mode,
        debug=debug,
    )


# ── feel test CLI ──────────────────────────────────────────────────────────────

def _run_feel_test():
    mode   = "companion"
    memory = {}

    print()
    print("eLo feel test — pure behaviour simulation")
    print("Commands: /mode studio|companion|adventure   /memory <text>   /debug   /exit")
    print()

    debug = False

    while True:
        try:
            raw = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\neLo: See you out there.")
            break

        if not raw:
            continue

        if raw == "/exit":
            print("eLo: Done.")
            break

        if raw.startswith("/mode "):
            m = raw.split(" ", 1)[1].strip().lower()
            if m in ("studio", "companion", "adventure"):
                mode = m
                print(f"  [mode: {mode}]")
            else:
                print("  /mode takes studio, companion, or adventure")
            continue

        if raw.startswith("/memory "):
            # inject a fake returning theme to test memory influence
            text = raw.split(" ", 1)[1].strip()
            memory = {"returning_theme": text, "tone_signal": "neutral",
                      "symbolic_echo": "", "concept_pairs": {},
                      "recurring_concepts": ["creation"],
                      "raw_blocks": {}}
            print(f"  [memory injected: {text!r}]")
            continue

        if raw == "/debug":
            debug = not debug
            print(f"  [debug {'on' if debug else 'off'}]")
            continue

        result = simulate_elo_response(raw, memory, mode, debug=debug)

        if debug:
            response, reasoning = result
            p1 = reasoning["phase_1_interpretation"]
            p4 = reasoning["phase_4_transform"]
            print(f"  [p1] type={p1['input_type']} emotion={p1['emotion']} "
                  f"concepts={p1['concepts']} entities={p1['entities']}")
            print(f"  [p4] grounding={p4['grounding']}")
        else:
            response = result

        print(f"\neLo: {response}\n")


if __name__ == "__main__":
    _run_feel_test()
