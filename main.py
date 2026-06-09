"""
main.py — eLo AI entry point.

Usage:
    python main.py                    # start chat loop
    python main.py --export-memory    # write memory snapshot then exit
    python main.py --orb-cli          # run Core Orb CLI simulator

CLI commands during chat:
    /exit                 quit and save memory
    /mode studio          switch to Studio mode (building / planning)
    /mode companion       switch to Companion mode (reflection / conversation)
    /mode adventure       switch to Adventure mode (world logic / storytelling)
    /export               export memory snapshot mid-session
    /reload               reload config + long-term memory from disk
    /project              show active project registry
"""

import argparse
import sys

import os

from core.core_engine import CoreEngine, set_response_backend
from core.memory_engine import export_memory, load_registry
from plugins.hardware.orb_engine import OrbEngine, run_orb_cli
from backends.backend_router import (
    set_backend_mode, get_backend_mode,
    set_feel_test_mode,
    BACKEND_AUTO, BACKEND_CLAUDE, BACKEND_MOCK,
)

FEEL_TEST_MODE = False


def _auto_select_backend() -> str:
    """
    Set initial backend mode.
    Claude key present → auto (will try Claude, fall back to mock on failure).
    No key → mock (feel-testing mode).
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        set_backend_mode(BACKEND_AUTO)
        return "auto (Claude → mock fallback)"
    set_backend_mode(BACKEND_MOCK)
    return "mock (no API key)"


_VALID_COMMANDS = {"/mode", "/exit", "/export", "/project", "/reload", "/debug", "/backend", "/feel"}
_COMMANDS_HINT  = "type /mode studio|companion|adventure  /backend auto|claude|mock  /exit"


def _handle_command(raw: str, engine, debug_ref: list) -> bool:
    """
    Dispatch a slash command. Returns True to keep looping, False to exit.
    Only called when input starts with '/'.
    """
    cmd   = raw.split()[0].lower()
    rest  = raw[len(cmd):].strip()

    if cmd == "/exit":
        print("\neLo: Saving memory and session. Goodbye.")
        export_memory()
        engine.save_session()
        return False

    if cmd == "/mode":
        if rest in ("studio", "companion", "adventure"):
            engine.set_mode(rest)
        else:
            print("eLo: /mode takes studio, companion, or adventure.")
        return True

    if cmd == "/export":
        path = export_memory()
        print(f"  [memory saved → {path}]")
        return True

    if cmd == "/reload":
        engine.reload()
        print("  [config reloaded]")
        return True

    if cmd == "/project":
        registry = load_registry()
        print("  Active projects:")
        for pid, info in registry.get("active_projects", {}).items():
            print(f"    {pid}  ({info.get('status', '?')}) — {info.get('type', '')}")
        return True

    if cmd == "/backend":
        if rest in ("auto", "claude", "mock"):
            set_backend_mode(rest)
            print(f"  [backend: {rest}]")
        else:
            print(f"  [backend: {get_backend_mode()}]  (options: auto | claude | mock)")
        return True

    if cmd == "/feel":
        global FEEL_TEST_MODE
        FEEL_TEST_MODE = not FEEL_TEST_MODE
        set_feel_test_mode(FEEL_TEST_MODE)
        print(f"  [feel-test mode: {'on' if FEEL_TEST_MODE else 'off'}]")
        return True

    if cmd == "/debug":
        debug_ref[0] = not debug_ref[0]
        print(f"  [debug {'on' if debug_ref[0] else 'off'}]")
        return True

    # unknown slash command — show hint, do not pass to engine
    print(f"  Unknown command. {_COMMANDS_HINT}")
    return True


def _run_chat():
    backend = _auto_select_backend()
    orb     = OrbEngine(silent=True)
    engine  = CoreEngine(orb=orb)
    debug   = [False]

    # restore previous session if available
    info = CoreEngine.session_info()
    restored = engine.restore_session()

    print()
    if restored and info:
        print(f"eLo: Session restored  [state: {info.get('state','')}  mode: {info.get('active_mode','')}  turns: {info.get('turn_count',0)}]")
    else:
        print("eLo: Ready.")
    print(f"  (commands: {_COMMANDS_HINT})")
    print(f"  (backend: {backend})")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\neLo: See you out there.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            if not _handle_command(user_input, engine, debug):
                break
            continue

        # everything else is conversation
        try:
            response = engine.turn(user_input, debug=debug[0])
        except Exception as exc:
            print(f"\neLo: [something went wrong — {exc}]\n")
            continue

        print(f"\neLo: {response}\n")


def _run_export():
    path = export_memory()
    print(f"Memory exported to: {path}")


def main():
    parser = argparse.ArgumentParser(description="eLo AI — Creative Personality OS")
    parser.add_argument("--export-memory", action="store_true")
    parser.add_argument("--orb-cli",       action="store_true")
    args = parser.parse_args()

    if args.export_memory:
        _run_export()
    elif args.orb_cli:
        run_orb_cli()
    else:
        _run_chat()


if __name__ == "__main__":
    main()
