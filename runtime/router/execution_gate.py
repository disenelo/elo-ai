"""
runtime/router/execution_gate.py — Stage 06+07: Execution Gate

Prevents system actions from firing without user confirmation.
Tracks one pending action at a time. Confirmation clears it.

WO-CANON-XXIII §A: scope-aware gate (LAW-017 B2).
  PERSON   — in-flow confirmation; _IMMEDIATE_SAFE allowed.
  COMPANY  — eLo read-only; routes through Executive + David L3 (no _IMMEDIATE_SAFE).
  RESERVED — structural denial; David is sole L3+LG-2; no _IMMEDIATE_SAFE, no in-chat confirm.

Authority never self-promotes: a PERSON "yes" cannot execute COMPANY or RESERVED.

Output: {execute, confirmation, why, reserved}
"""
from __future__ import annotations
from runtime.capabilities.capability import SCOPE_PERSON, SCOPE_COMPANY, SCOPE_RESERVED

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


def gate(action: str, arg: str, scope: str = SCOPE_PERSON) -> dict:
    """
    Evaluate whether a system action should execute immediately or wait for confirm.

    scope — authority scope from the capability registry (default SCOPE_PERSON).
    Authority never self-promotes: PERSON "yes" cannot resolve COMPANY or RESERVED.

    Returns:
        execute      — True = run now, False = wait for confirmation
        confirmation — Message for eLo to speak if waiting (empty for structural denial)
        why          — reason string
        reserved     — True if this is a structural denial (RESERVED scope)
    """
    # ── RESERVED: structural denial — no _IMMEDIATE_SAFE, no in-chat confirmation ──
    if scope == SCOPE_RESERVED:
        return {
            "execute":      False,
            "confirmation": "",
            "why":          "reserved_structural_denial",
            "reserved":     True,
        }

    # ── COMPANY: eLo read-only today; routes through Executive + David L3 ────────
    if scope == SCOPE_COMPANY:
        return {
            "execute":      False,
            "confirmation": "",
            "why":          "company_scope_escalation",
            "reserved":     False,
        }

    # ── PERSON: existing confirm-before-act behavior ─────────────────────────────
    if action in _IMMEDIATE_SAFE:
        return {"execute": True, "confirmation": "", "why": "safe_immediate", "reserved": False}

    desc = _describe(action, arg)
    _pending["action"] = action
    _pending["arg"]    = arg
    _pending["desc"]   = desc
    _pending["scope"]  = SCOPE_PERSON   # scope is PERSON at this point — explicit

    return {
        "execute":      False,
        "confirmation": desc,
        "why":          "requires_confirm",
        "reserved":     False,
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
    """
    Execute the pending system action and clear state.

    Scope guard: a PERSON confirmation cannot execute COMPANY or RESERVED.
    Authority never self-promotes (LAW-017 B6: no self-escalation).
    execute_pending() runs AND clears in one step — no replay.
    """
    if not _pending:
        return "Nothing pending."
    # Scope guard — belt-and-suspenders; RESERVED/COMPANY should never reach _pending
    if _pending.get("scope", SCOPE_PERSON) != SCOPE_PERSON:
        _pending.clear()
        return "That action requires elevated authorization — route it to David."
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
