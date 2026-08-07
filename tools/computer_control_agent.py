"""
tools/computer_control_agent.py — Computer control via macOS Quartz APIs.

All actions require explicit confirmation before execution. eLo describes
what it's about to do, waits for a "yes" / "go" / "do it", then acts.

Supported actions:
    click         — left/right/double click at x, y
    move          — move cursor to x, y (no click)
    type          — type a string of text
    key           — press a key combo (cmd+c, escape, return, etc.)
    scroll        — scroll at x, y by amount
    screenshot    — capture screen or region
    open          — open a macOS application by name

Config (.env):
    ELO_COMPUTER_CONTROL=1   Enable computer control (default: disabled for safety)

Public API:
    parse_intent(text)      → dict | None     Parse natural language → action dict
    describe(action)        → str             Human-readable confirm string
    execute(action)         → str             Execute confirmed action, return result
    has_pending()           → bool
    get_pending()           → dict | None
    set_pending(action)     → None
    clear_pending()         → None
    is_enabled()            → bool
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# ── Safety gate ───────────────────────────────────────────────────────────────

def is_enabled() -> bool:
    """Computer control is opt-in. Set ELO_COMPUTER_CONTROL=1 in .env to enable."""
    return os.environ.get("ELO_COMPUTER_CONTROL", "").strip() in ("1", "true", "yes", "on")


# ── Pending confirmation store ────────────────────────────────────────────────

_pending: Optional[dict] = None


def has_pending() -> bool:
    return _pending is not None


def get_pending() -> Optional[dict]:
    return _pending


def set_pending(action: dict) -> None:
    global _pending
    _pending = action


def clear_pending() -> None:
    global _pending
    _pending = None


# ── Action parser ─────────────────────────────────────────────────────────────

# Coord patterns: "at 500, 300" / "500 300" / "x=500 y=300"
_COORD_RE = re.compile(
    r'(?:at\s+)?'
    r'(?:x\s*[=:]?\s*)?(\d+)\s*[,\s]\s*(?:y\s*[=:]?\s*)?(\d+)',
    re.I,
)

# Key combo: "cmd+c", "command c", "ctrl+v", etc.
_KEY_RE = re.compile(
    r'\b(?:press|hit|hold|keyboard|key)\b[\s:]+(.+)',
    re.I,
)

# Type: "type 'hello world'" / type hello world
_TYPE_RE = re.compile(
    r"\btype\s+['\"]?(.+?)['\"]?$",
    re.I,
)

# Scroll
_SCROLL_RE = re.compile(
    r'\bscroll\b\s*(up|down|left|right)?(?:\s+(\d+))?(?:\s+(?:at|on)\s+(\d+)[,\s]+(\d+))?',
    re.I,
)

# Screenshot
_SS_RE = re.compile(
    r'\b(?:take\s+a?\s*)?(?:screenshot|screen\s+capture|screen\s+shot)\b',
    re.I,
)

# Open app: "open Spotify" / "open the Notes app"
_OPEN_RE = re.compile(
    r'\bopen\s+(?:-a\s+)?(?:the\s+)?([A-Za-z][A-Za-z0-9\s]+?)(?:\s+app)?\s*$',
    re.I,
)

# Click patterns
_CLICK_RE = re.compile(
    r'\b(right[\s-]?click|double[\s-]?click|click)\b(?:\s+(?:on\s+)?)?(.+)?',
    re.I,
)


def _parse_coord(text: str) -> Optional[tuple[int, int]]:
    m = _COORD_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _normalise_keys(raw: str) -> list[str]:
    """Normalise key names to Quartz-compatible strings."""
    _ALIASES = {
        "command": "cmd", "control": "ctrl", "option": "opt", "alternate": "opt",
        "alt": "opt", "delete": "del", "backspace": "del", "return": "return",
        "enter": "return", "escape": "esc", "space": "space", "tab": "tab",
        "up": "up", "down": "down", "left": "left", "right": "right",
    }
    parts = re.split(r'[\s+\-]+', raw.strip().lower())
    return [_ALIASES.get(p, p) for p in parts if p]


# Valid key tokens after normalisation — prevents "press on with that" being parsed as a key combo.
# F1 — F1: "press on with that? needs my attention" triggered this (WO-039-F1).
_VALID_KEY_OUTPUTS = frozenset([
    "cmd", "ctrl", "opt", "shift", "fn",
    "esc", "return", "space", "tab", "del",
    "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
])
_VALID_KEY_TOKEN_RE = re.compile(r'^([a-z0-9]|f\d{1,2})$')


def _is_valid_key_combo(keys: list[str]) -> bool:
    """Return True only when every token looks like an actual keyboard key."""
    return bool(keys) and all(
        k in _VALID_KEY_OUTPUTS or bool(_VALID_KEY_TOKEN_RE.match(k))
        for k in keys
    )


def parse_intent(text: str) -> Optional[dict]:
    """
    Parse natural-language text into an action dict. Returns None if not recognised.

    Action dict shapes:
        {"type": "click",  "x": int, "y": int, "button": "left"|"right", "count": 1|2}
        {"type": "move",   "x": int, "y": int}
        {"type": "type",   "text": str}
        {"type": "key",    "keys": [str, ...]}
        {"type": "scroll", "x": int, "y": int, "direction": "up"|"down"|"left"|"right", "amount": int}
        {"type": "screenshot"}
        {"type": "open",   "app": str}
    """
    m = _OPEN_RE.search(text)
    if m:
        return {"type": "open", "app": m.group(1).strip()}

    if _SS_RE.search(text):
        return {"type": "screenshot"}

    m = _TYPE_RE.search(text)
    if m:
        return {"type": "type", "text": m.group(1).strip()}

    m = _KEY_RE.search(text)
    if m:
        keys = _normalise_keys(m.group(1))
        if _is_valid_key_combo(keys):
            return {"type": "key", "keys": keys}

    m = _SCROLL_RE.search(text)
    if m:
        direction = (m.group(1) or "down").lower()
        amount    = int(m.group(2) or 3)
        coord = _parse_coord(text) if m.group(3) else None
        x, y  = coord if coord else (None, None)
        return {"type": "scroll", "direction": direction, "amount": amount, "x": x, "y": y}

    m = _CLICK_RE.search(text)
    if m:
        verb    = m.group(1).lower().replace(" ", "").replace("-", "")
        rest    = (m.group(2) or "").strip()
        button  = "right" if "right" in verb else "left"
        count   = 2 if "double" in verb else 1
        coord   = _parse_coord(rest)
        if coord:
            x, y = coord
        elif rest and _looks_like_target(rest):
            # Vision-based target — return a special "find_and_click" action
            return {"type": "find_and_click", "target": rest, "button": button, "count": count}
        else:
            coord = _parse_coord(text)
            x, y = coord if coord else (None, None)
        return {"type": "click", "x": x, "y": y, "button": button, "count": count}

    return None


def _looks_like_target(text: str) -> bool:
    """True if text looks like a UI element name rather than raw coordinates."""
    if re.fullmatch(r'\d+[\s,]+\d+', text.strip()):
        return False
    return bool(re.search(r'[a-zA-Z]', text))


# ── Human-readable describe ───────────────────────────────────────────────────

def describe(action: dict) -> str:
    t = action.get("type")
    if t == "click":
        btn  = action.get("button", "left")
        cnt  = action.get("count", 1)
        x, y = action.get("x"), action.get("y")
        verb = "double-click" if cnt == 2 else ("right-click" if btn == "right" else "click")
        if x is not None and y is not None:
            return f"{verb} at ({x}, {y})"
        return f"{verb}"
    if t == "find_and_click":
        target = action.get("target", "?")
        btn    = action.get("button", "left")
        cnt    = action.get("count", 1)
        verb   = "double-click" if cnt == 2 else ("right-click" if btn == "right" else "click")
        return f"{verb} on '{target}' (I'll use the camera to find it)"
    if t == "move":
        return f"move cursor to ({action.get('x')}, {action.get('y')})"
    if t == "type":
        txt = action.get("text", "")
        preview = txt[:40] + ("…" if len(txt) > 40 else "")
        return f"type: '{preview}'"
    if t == "key":
        return f"press {'+'.join(action.get('keys', []))}"
    if t == "scroll":
        d = action.get("direction", "down")
        n = action.get("amount", 3)
        return f"scroll {d} {n} clicks"
    if t == "screenshot":
        return "take a screenshot"
    if t == "open":
        return f"open {action.get('app', '?')}"
    return str(action)


# ── Quartz execution ──────────────────────────────────────────────────────────

def _quartz_click(x: int, y: int, button: str = "left", count: int = 1) -> None:
    import Quartz
    btn_map = {
        "left":  (Quartz.kCGMouseButtonLeft,
                  Quartz.kCGEventLeftMouseDown,
                  Quartz.kCGEventLeftMouseUp),
        "right": (Quartz.kCGMouseButtonRight,
                  Quartz.kCGEventRightMouseDown,
                  Quartz.kCGEventRightMouseUp),
    }
    btn_id, down_type, up_type = btn_map.get(button, btn_map["left"])
    pt = Quartz.CGPoint(x, y)

    for _ in range(count):
        dn = Quartz.CGEventCreateMouseEvent(None, down_type, pt, btn_id)
        up = Quartz.CGEventCreateMouseEvent(None, up_type,   pt, btn_id)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, dn)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def _quartz_move(x: int, y: int) -> None:
    import Quartz
    Quartz.CGWarpMouseCursorPosition(Quartz.CGPoint(x, y))


_KEY_CODES: dict[str, int] = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7,
    "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15,
    "y": 16, "t": 17, "1": 18, "2": 19, "3": 20, "4": 21, "6": 22,
    "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28, "0": 29,
    "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "return": 36,
    "l": 37, "j": 38, "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43,
    "/": 44, "n": 45, "m": 46, ".": 47, "tab": 48, "space": 49,
    "`": 50, "del": 51, "esc": 53, "up": 126, "down": 125, "left": 123, "right": 124,
    "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97,
    "f7": 98, "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
}
_MODIFIER_FLAGS: dict[str, int] = {
    "cmd":   0x100000,  # kCGEventFlagMaskCommand
    "ctrl":  0x040000,  # kCGEventFlagMaskControl
    "opt":   0x080000,  # kCGEventFlagMaskAlternate
    "shift": 0x020000,  # kCGEventFlagMaskShift
}


def _quartz_key(keys: list[str]) -> None:
    import Quartz
    modifiers = [k for k in keys if k in _MODIFIER_FLAGS]
    primary   = next((k for k in keys if k not in _MODIFIER_FLAGS), None)
    if primary is None:
        return
    key_code = _KEY_CODES.get(primary)
    if key_code is None:
        return

    flags = 0
    for mod in modifiers:
        flags |= _MODIFIER_FLAGS[mod]

    dn = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
    up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)
    if flags:
        Quartz.CGEventSetFlags(dn, flags)
        Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, dn)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def _quartz_scroll(x: Optional[int], y: Optional[int],
                   direction: str = "down", amount: int = 3) -> None:
    import Quartz
    if x is not None and y is not None:
        _quartz_move(x, y)
    dx, dy = 0, 0
    if direction == "down":  dy = -amount
    if direction == "up":    dy =  amount
    if direction == "left":  dx = -amount
    if direction == "right": dx =  amount
    evt = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 2, dy, dx)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, evt)


def _type_text_applescript(text: str) -> None:
    """Use AppleScript to type text — handles unicode better than raw key events."""
    safe = text.replace('"', '\\"').replace("\\", "\\\\")
    subprocess.run(
        ["osascript", "-e", f'tell application "System Events" to keystroke "{safe}"'],
        check=False, capture_output=True,
    )


def _take_screenshot() -> Path:
    out = Path(tempfile.mktemp(suffix=".png"))
    subprocess.run(["screencapture", "-x", str(out)], check=True)
    return out


def _find_and_click_with_vision(target: str, button: str = "left", count: int = 1) -> str:
    """Take a screenshot, use vision to find target coordinates, then click."""
    try:
        from tools.vision_agent import _describe_openai
    except ImportError:
        return "Vision not available — give me exact coordinates instead."

    ss_path = _take_screenshot()
    raw = ss_path.read_bytes()
    prompt = (
        f"Find the UI element described as '{target}' on this screen. "
        "Reply with ONLY 'x=NNN y=NNN' where NNN are the pixel coordinates of its centre. "
        "If you cannot find it, reply with 'NOT_FOUND'."
    )
    result = _describe_openai(raw, prompt)
    ss_path.unlink(missing_ok=True)

    if not result or "NOT_FOUND" in result:
        return f"Couldn't find '{target}' on screen."

    m = re.search(r'x\s*=\s*(\d+)\s+y\s*=\s*(\d+)', result, re.I)
    if not m:
        return f"Couldn't parse coordinates from vision result: {result}"

    x, y = int(m.group(1)), int(m.group(2))
    _quartz_click(x, y, button=button, count=count)
    verb = "double-clicked" if count == 2 else ("right-clicked" if button == "right" else "clicked")
    return f"{verb} on '{target}' at ({x}, {y})."


# ── Public execute ────────────────────────────────────────────────────────────

def execute(action: dict) -> str:
    """Execute a confirmed action. Returns a short result string."""
    if not is_enabled():
        return "Computer control is disabled. Set ELO_COMPUTER_CONTROL=1 in .env to enable."

    t = action.get("type")

    if t == "find_and_click":
        return _find_and_click_with_vision(
            action["target"], action.get("button", "left"), action.get("count", 1)
        )

    if t == "click":
        x, y = action.get("x"), action.get("y")
        if x is None or y is None:
            return "No coordinates — where should I click?"
        _quartz_click(x, y, button=action.get("button", "left"), count=action.get("count", 1))
        verb = "Double-clicked" if action.get("count", 1) == 2 else \
               ("Right-clicked" if action.get("button") == "right" else "Clicked")
        return f"{verb} at ({x}, {y})."

    if t == "move":
        _quartz_move(action["x"], action["y"])
        return f"Cursor at ({action['x']}, {action['y']})."

    if t == "type":
        _type_text_applescript(action.get("text", ""))
        txt = action.get("text", "")
        preview = txt[:40] + ("…" if len(txt) > 40 else "")
        return f"Typed: '{preview}'."

    if t == "key":
        _quartz_key(action.get("keys", []))
        return f"Pressed {'+'.join(action.get('keys', []))}."

    if t == "scroll":
        _quartz_scroll(
            action.get("x"), action.get("y"),
            action.get("direction", "down"), action.get("amount", 3),
        )
        return f"Scrolled {action.get('direction', 'down')}."

    if t == "screenshot":
        path = _take_screenshot()
        try:
            from blender_bridge.state_writer import patch as _patch
            _patch({"hud_image": str(path)})
        except Exception:
            pass
        return f"Screenshot saved — {path.name}."

    if t == "open":
        app_name = action.get("app", "")
        if not app_name:
            return "No app name — what should I open?"
        result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Opened {app_name}."
        return f"Couldn't open '{app_name}' — check the app name."

    return f"Unknown action type: {t}"
