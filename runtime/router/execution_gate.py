"""
runtime/router/execution_gate.py — Stage 06+07: Execution Gate

Prevents system actions from firing without user confirmation.
Tracks one pending action at a time. Confirmation clears it.

Output: {execute, confirmation, why}
"""
from __future__ import annotations

# ── Pending action state ──────────────────────────────────────────────────────
_pending: dict = {}   # {action, arg, description}

# ── Confirmation / cancel vocabulary ─────────────────────────────────────────
_CONFIRM = frozenset({
    "yes", "yeah", "yep", "yup", "go ahead", "do it", "sure", "ok", "okay",
    "go", "do that", "proceed", "confirm", "let's go", "do it then", "aight",
    "safe", "yes please", "yeah do it", "go for it",
})
_CANCEL = frozenset({
    "no", "nah", "nope", "cancel", "stop", "forget it", "don't", "never mind",
    "actually no", "leave it", "abort", "don't do it", "not now",
})

# ── Actions that are safe to execute immediately (read-only / reversible) ─────
_IMMEDIATE_SAFE = frozenset({
    "folder_list", "folder_organise", "screenshot",
    "dark_mode", "light_mode",
    "window_focus",   # non-destructive
    "volume",         # reversible — user can undo with next command; no confirmation needed
    "brightness",     # reversible — same reasoning
})

# ── Human-readable descriptions for confirmation prompts ─────────────────────
_DESCRIPTIONS: dict[str, str] = {
    "volume":            "turn the volume {arg}",
    "brightness":        "change brightness {arg}",
    "app_open":          "open {arg}",
    "app_quit":          "quit {arg}",
    "window_fullscreen": "make {arg} full screen",
    "window_close":      "close the front window of {arg}",
    "folder_open":       "open {arg} in Finder",
    "file_copy":         "copy {arg}",
    "file_move":         "move {arg}",
    "file_rename":       "rename {arg}",
    "file_delete":       "trash {arg}",
}


def _describe(action: str, arg: str) -> str:
    template = _DESCRIPTIONS.get(action, f"{action} {arg}")
    return template.format(arg=arg)


def gate(action: str, arg: str) -> dict:
    """
    Evaluate whether a system action should execute immediately or wait for confirm.

    Returns:
        execute      — True = run now, False = wait for confirmation
        confirmation — Message for eLo to speak if waiting
        why          — reason string
    """
    if action in _IMMEDIATE_SAFE:
        return {"execute": True, "confirmation": "", "why": "safe_immediate"}

    desc = _describe(action, arg)
    _pending["action"] = action
    _pending["arg"]    = arg
    _pending["desc"]   = desc

    return {
        "execute":      False,
        "confirmation": desc,
        "why":          "requires_confirm",
    }


def is_confirm(text: str) -> bool:
    return text.lower().strip().rstrip(".,!?") in _CONFIRM


def is_cancel(text: str) -> bool:
    return text.lower().strip().rstrip(".,!?") in _CANCEL


def has_pending() -> bool:
    return bool(_pending)


def get_pending_desc() -> str:
    return _pending.get("desc", "")


def execute_pending() -> str:
    """Execute the pending system action and clear state."""
    if not _pending:
        return "Nothing pending."
    try:
        from tools.system_agent import execute
        result = execute(_pending["action"], _pending["arg"])
        _pending.clear()
        return result
    except Exception as e:
        _pending.clear()
        return f"Couldn't do that — {e}"


def cancel_pending() -> None:
    _pending.clear()


def should_execute(text: str) -> bool:
    """True if text is a confirmation of the pending action."""
    return has_pending() and is_confirm(text)


def should_cancel(text: str) -> bool:
    return has_pending() and is_cancel(text)
