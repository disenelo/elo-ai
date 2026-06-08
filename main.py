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

from core.core_engine import CoreEngine
from core.memory_engine import export_memory, load_registry
from plugins.hardware.orb_engine import OrbEngine, run_orb_cli


_VALID_COMMANDS = {"/mode", "/exit", "/export", "/project", "/reload", "/debug"}
_COMMANDS_HINT  = "type /mode studio|companion|adventure  /project  /export  /exit"


def _handle_command(raw: str, engine, debug_ref: list) -> bool:
    """
    Dispatch a slash command. Returns True to keep looping, False to exit.
    Only called when input starts with '/'.
    """
    cmd   = raw.split()[0].lower()
    rest  = raw[len(cmd):].strip()

    if cmd == "/exit":
        print("\neLo: Saving memory. Goodbye.")
        export_memory()
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

    if cmd == "/debug":
        debug_ref[0] = not debug_ref[0]
        print(f"  [debug {'on' if debug_ref[0] else 'off'}]")
        return True

    # unknown slash command — show hint, do not pass to engine
    print(f"  Unknown command. {_COMMANDS_HINT}")
    return True


def _run_chat():
    orb    = OrbEngine(silent=True)   # orb transitions are internal
    engine = CoreEngine(orb=orb)
    debug  = [False]

    # eLo opens the conversation — not a banner listing commands
    print()
    print("eLo: Ready.")
    print(f"  (commands: {_COMMANDS_HINT})")
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
