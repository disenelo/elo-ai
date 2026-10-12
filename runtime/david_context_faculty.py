"""
runtime/david_context_faculty.py — WO-B1-0140

Detects what David is doing at his Mac and derives whether he is in a
creative/coding flow state, so eLo can move himself to desktop mode without
being asked.

Signals:
    active_app          — frontmost application name (str)
    app_category        — creative_tool | code | browser | communication | other
    conversation_gap_s  — seconds since eLo last responded (0.0 = never this session)
    in_flow             — True when app_category is creative_tool/code AND
                          conversation_gap_s >= IN_FLOW_THRESHOLD_S (default 180 s)

Side-effect when in_flow=True:
    Calls blender_bridge.state_writer.patch({"state": {"mode": "desktop"}}).
    This is intentional: the faculty doubles as the MODE_DESKTOP trigger.
    Only emitted once per in_flow transition (not every turn while flowing).

Thread safety: single-threaded server; module-level state is safe.
"""

from __future__ import annotations

import logging
import os
import time

_log = logging.getLogger("elo.david_context_faculty")

# ── Paths ──────────────────────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLENDER_STATE_PATH = os.path.join(_ROOT, "blender", "blender_state.json")

# ── App categorisation ─────────────────────────────────────────────────────────

_CREATIVE_APPS: frozenset[str] = frozenset({
    "figma", "logic pro x", "logic pro", "procreate", "blender",
    "adobe illustrator", "illustrator", "photoshop", "adobe photoshop",
    "sketch", "adobe xd", "affinity designer", "affinity photo",
    "davinci resolve", "final cut pro", "adobe premiere pro", "premiere pro",
    "adobe after effects", "after effects", "garageband", "ableton live",
    "cinema 4d", "maya", "zbrush", "substance painter", "aseprite",
    "pixelmator pro", "pixelmator", "inkscape", "audacity",
})

_CODE_APPS: frozenset[str] = frozenset({
    "visual studio code", "code", "xcode", "pycharm", "intellij idea",
    "webstorm", "sublime text", "atom", "cursor", "nova",
    "terminal", "iterm2", "iterm", "warp", "hyper",
    "claude code", "android studio",
})

_BROWSER_APPS: frozenset[str] = frozenset({
    "safari", "google chrome", "chrome", "firefox", "arc",
    "brave browser", "brave", "microsoft edge", "edge", "opera",
})

_COMMUNICATION_APPS: frozenset[str] = frozenset({
    "slack", "discord", "messages", "mail", "zoom",
    "microsoft teams", "teams", "whatsapp", "telegram", "signal",
    "facetime", "skype",
})

# ── Flow threshold ─────────────────────────────────────────────────────────────

IN_FLOW_THRESHOLD_S: float = 180.0   # 3 minutes of silence → in_flow

# ── Module-level state ─────────────────────────────────────────────────────────

_last_result:         dict  = {}
_was_in_flow:         bool  = False   # tracks last emission to avoid repeat patches


# ── Public API ────────────────────────────────────────────────────────────────

def get_frontmost_app() -> str:
    """Return the name of David's frontmost application via AppKit.NSWorkspace."""
    try:
        from AppKit import NSWorkspace  # type: ignore[import]
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is not None:
            name = app.localizedName()
            if name:
                return str(name)
    except Exception as exc:
        _log.debug("NSWorkspace unavailable: %s", exc)
    return ""


def categorize_app(app_name: str) -> str:
    """Map an application name to one of the canonical category strings."""
    key = app_name.lower().strip()
    if key in _CREATIVE_APPS:
        return "creative_tool"
    if key in _CODE_APPS:
        return "code"
    if key in _BROWSER_APPS:
        return "browser"
    if key in _COMMUNICATION_APPS:
        return "communication"
    return "other"


def compute() -> dict:
    """
    Read David's active context and return the david_context dict.

    Side-effect: when in_flow transitions False→True, patches blender_state.json
    with state.mode=desktop so eLo's presence surface sees the signal.

    Returns:
        {
            "active_app":         str,
            "app_category":       str,
            "conversation_gap_s": float,
            "in_flow":            bool,
        }
    """
    global _last_result, _was_in_flow

    active_app = get_frontmost_app()
    app_category = categorize_app(active_app)

    # ── conversation gap ──────────────────────────────────────────────────────
    try:
        from runtime.conversation_state import get_last_response_time as _grt
        last_at = _grt()
        conversation_gap_s = (time.time() - last_at) if last_at > 0.0 else 0.0
    except Exception:
        conversation_gap_s = 0.0

    # ── in_flow derivation ────────────────────────────────────────────────────
    in_flow = (
        app_category in {"creative_tool", "code"}
        and conversation_gap_s >= IN_FLOW_THRESHOLD_S
    )

    # ── MODE_DESKTOP side-effect — emit only on False→True transition ─────────
    if in_flow and not _was_in_flow:
        try:
            from blender_bridge.state_writer import patch as _patch
            _patch({"state": {"mode": "desktop"}})
            _log.info(
                "WO-B1-0140: MODE_DESKTOP emitted — %s (%s), gap=%.0fs",
                active_app, app_category, conversation_gap_s,
            )
        except Exception as exc:
            _log.warning("WO-B1-0140: state_writer.patch failed: %s", exc)

    _was_in_flow = in_flow

    result = {
        "active_app":         active_app,
        "app_category":       app_category,
        "conversation_gap_s": round(conversation_gap_s, 1),
        "in_flow":            in_flow,
    }
    _last_result = result
    return result


def get_last_result() -> dict:
    """Return the most recent compute() result without re-reading NSWorkspace."""
    return dict(_last_result)


def reset() -> None:
    """Clear flow state at session boundary."""
    global _last_result, _was_in_flow
    _last_result  = {}
    _was_in_flow  = False
