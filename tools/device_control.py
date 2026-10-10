"""
tools/device_control.py — WO-B3-0011 Company Control, v1: eLo runs David's
device Shortcuts.

Anything David can control from the Home app (lights, plugs, speakers, Hue,
HomeKit…) can be a macOS Shortcut; eLo runs it locally with `shortcuts run`.
No cloud, no brand-specific API. The existing Hue agent (capabilities/
lights_agent.py) has no bridge configured, so it never ran a light.

Only shortcuts on the allow-list can be run by eLo (data/device_shortcuts.json,
default: the device shortcuts found on this Mac 2026-10-10). A sentence can
never trigger an unrelated shortcut ("Download file").

    match(text)        -> shortcut name or None
    run(name)          -> {success, result: {shortcut, line}, error}
    controllable()     -> allow-listed shortcuts that exist on this Mac
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ALLOW_FILE = os.path.join(_ROOT, "data", "device_shortcuts.json")
_DEFAULT_ALLOW = ["Lights On", "Lights Out", "Design Mode", "Living Room Sounds"]

# Spoken forms → the shortcut they mean (lower-case, after normalising).
_ALIASES = {
    "lights on": ("turn on the lights", "turn the lights on", "lights on", "switch the lights on",
                  "switch on the lights", "put the lights on"),
    "lights out": ("turn off the lights", "turn the lights off", "lights off", "lights out",
                   "switch the lights off", "switch off the lights", "kill the lights"),
    "design mode": ("design mode",),
    "living room sounds": ("living room sounds",),
}
_ACT = re.compile(r"\b(?:turn|switch|put|kill|run|start|do|set|activate|trigger|lights?|mode|sounds?)\b")

_QUESTION_WORDS = {"what", "which", "why", "how", "when", "did", "is", "are", "were", "was", "does"}

_cache = {"ts": 0.0, "names": []}


def _all_shortcuts() -> list[str]:
    if time.time() - _cache["ts"] < 60 and _cache["names"]:
        return _cache["names"]
    try:
        out = subprocess.run(["shortcuts", "list"], capture_output=True, text=True, timeout=10).stdout
        names = [l.strip() for l in out.splitlines() if l.strip()]
    except Exception:
        names = []
    _cache.update(ts=time.time(), names=names)
    return names


def allow_list() -> list[str]:
    try:
        with open(_ALLOW_FILE, encoding="utf-8") as f:
            names = json.load(f).get("shortcuts")
        if isinstance(names, list) and names:
            return [str(n) for n in names]
    except Exception:
        pass
    return list(_DEFAULT_ALLOW)


def controllable() -> list[str]:
    have = {n.lower(): n for n in _all_shortcuts()}
    return [have[a.lower()] for a in allow_list() if a.lower() in have]


def _norm(text: str) -> str:
    t = re.sub(r"[^\w\s']", " ", (text or "").lower())
    t = re.sub(r"\b(?:please|elo|can you|could you|would you|for me|now|the shortcut|shortcut)\b", " ", t)
    return " ".join(t.split())


def match(text: str) -> str | None:
    """The allow-listed shortcut this sentence asks eLo to run, else None."""
    t = _norm(text)
    first = t.split()[0].split("'")[0] if t else ""          # "what's" → "what"
    if not t or not _ACT.search(t) or first in _QUESTION_WORDS:  # "are the lights on?" isn't a command
        return None
    names = controllable()
    by_lower = {n.lower(): n for n in names}
    for key, phrases in _ALIASES.items():
        if key in by_lower and any(p in t for p in phrases):
            return by_lower[key]
    for n in sorted(names, key=len, reverse=True):          # "run Design Mode", "do living room sounds"
        if n.lower() in t:
            return n
    return None


def run(name: str) -> dict:
    from tools.capability_status import tool_result, record_result
    if name not in controllable():
        return record_result("devices", tool_result(False, {"line": f"“{name}” isn't one I'm allowed to run."},
                                                    "not allow-listed"))
    try:
        r = subprocess.run(["shortcuts", "run", name], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Your “{name}” shortcut didn't finish in time."}, "timeout"))
    if r.returncode != 0:
        err = (r.stderr or r.stdout or f"exit {r.returncode}").strip()[:200]
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Your “{name}” shortcut didn't run — {err}."}, err))
    # The shortcut ran; eLo can't see the lights, so he says what he did, not what happened.
    return record_result("devices", tool_result(True, {"shortcut": name, "line": f"Ran your “{name}” shortcut."}))
