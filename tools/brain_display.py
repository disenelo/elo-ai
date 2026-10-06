"""
tools/brain_display.py — SHOW_BRAIN: David asks to see eLo's brain or health.

Source: engineering/work_orders/WO-BRAIN-DISPLAY-001_Floating_Diagnostic_View.md (Part B)
David (2026-10-05): "I need to be able to say show me your energy show me your
health or can you show me hp, your battery, show me your brain, shows the
brain, brain for diagnostics …"

Phrase rule COPIED from Presence (parity rule 6) —
blender/agent_bus/designer/FROM_DESIGNER_2026-10-06_PRESENCE-COMMANDS-REGISTRY.md §B:
  the line starts with "show", "can you show", "let me see" or "open", or is
  ≤ 2 words; contains brain / diagnostic → show_brain; health / energy /
  battery / hp → show_health.
Additions from the WO's phrase list (not in Presence): "mind" with a show-lead,
"your battery" / "your hp" anywhere, brain + diagnostic anywhere.

Unity contract (same registry §A): blender_state.json →
  "ui_command": {"name": "show_brain" | "show_health", "_ts": <unix>}
edge-triggered on _ts.
"""
from __future__ import annotations

import re
import time

_LEAD_RE = re.compile(r"^(?:show|can\s+you\s+show|let\s+me\s+see|open)")
_BRAIN_RE = re.compile(r"\b(?:brain|diagnostics?)\b")
_HEALTH_RE = re.compile(r"\b(?:health|energy|battery|hp)\b")

# What eLo says as the view opens — brief, no LLM (WO Part B). Rotated so two
# asks in a row never give the same line: elo_response_gate blanks a reply
# identical to the previous one (live 2026-10-06: "your battery?" came back "").
_SPOKEN = {
    "show_brain":  ["Here's my brain.", "That's my brain — have a look.",
                    "Here's what's going on in my head."],
    "show_health": ["Here's how I'm doing.", "That's my battery right now.",
                    "Here's my energy."],
}
_last_spoken = ""


def spoken_for(name: str) -> str:
    global _last_spoken
    pool = _SPOKEN[name]
    i = (pool.index(_last_spoken) + 1) % len(pool) if _last_spoken in pool else 0
    _last_spoken = pool[i]
    return _last_spoken


def ui_command_for(text: str) -> str | None:
    """"show_brain", "show_health", or None."""
    t = re.sub(r"[^\w\s']", " ", (text or "").lower()).strip()
    t = re.sub(r"\s+", " ", t)
    if not t:
        return None
    led = bool(_LEAD_RE.match(t)) or len(t.split()) <= 2
    if led:
        if _BRAIN_RE.search(t) or re.search(r"\bmind\b", t):
            return "show_brain"
        if _HEALTH_RE.search(t):
            return "show_health"
    if re.search(r"\bbrain\b", t) and re.search(r"\bdiagnostics?\b", t):
        return "show_brain"
    if re.search(r"\byour\s+(?:battery|hp)\b", t):
        return "show_health"
    return None


def emit(name: str) -> None:
    """Tell Presence to open the view — same channel as a click."""
    from blender_bridge.state_writer import patch
    patch({"ui_command": {"name": name, "_ts": time.time()}})
