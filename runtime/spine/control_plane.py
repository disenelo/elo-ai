"""
runtime/spine/control_plane.py — Memory Arbitration + System Interpretation Layer.

Sits between Relationship Faculty and Capability Faculty in the cognitive spine.

Resolves memory in strict L1 → L2 → L3 hierarchy.
Detects session mode (creation / research / flow / standard).
Produces a context_block string that gets appended to the system prompt
before the LLM call — giving the model structured awareness of what
memory was resolved and what mode the session is in.

No LLM calls. Pure Python pattern matching + vault text lookup.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

# ── Session modes ──────────────────────────────────────────────────────────────

SESSION_CREATION = "creation"   # user is building / integrating — step back, support
SESSION_RESEARCH = "research"   # user is exploring / designing — assistant mode
SESSION_FLOW     = "flow"       # deep focus — assist silently, don't interrupt
SESSION_STANDARD = "standard"   # normal conversation

# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class ControlPlaneResult:
    session_mode:    str           = SESSION_STANDARD
    speak_mode:      str           = "speak"    # "speak" | "step_back" | "silent"
    emergent_assist: bool          = False
    l1_match:        Optional[str] = None       # raw vault text excerpt
    l2_summary:      Optional[str] = None       # 3–7 line compressed summary
    l3_byte:         Optional[str] = None       # MEMORY_BYTE structured string
    context_block:   str           = ""         # assembled → injected into system prompt

# ── Pattern tables ─────────────────────────────────────────────────────────────

_CREATION_SIGNALS = frozenset([
    "build", "building", "architecture", "route", "routing", "wire", "wiring",
    "slot", "module", "system", "layer", "integrate", "integration", "scaffold",
    "implement", "structure", "pipeline", "schema", "refactor",
    "slot it in", "where does this fit", "fit this in", "add this to",
    "find where", "slot this", "insert this",
])

_RESEARCH_SIGNALS = frozenset([
    "what if", "could we", "what about", "how would", "what's possible",
    "alternative", "option", "approach", "compare", "tradeoff",
    "research", "investigate", "explore", "look into", "is there a way",
    "what would happen", "better way", "different way", "how should",
])

_FLOW_SIGNALS = frozenset([
    "leave it", "ignore", "never mind", "hold on", "actually forget",
    "forget that", "not important", "doesn't matter",
])

_MEMORY_SIGNALS = frozenset([
    "remember", "last time", "we talked", "you said", "our project",
    "what was", "do you recall", "from before", "last session",
    "previous", "we discussed", "we decided", "we built",
])

# ── Session mode detection ─────────────────────────────────────────────────────

def _detect_session_mode(raw: str) -> str:
    lower = raw.lower()
    if any(s in lower for s in _FLOW_SIGNALS):
        return SESSION_FLOW
    if any(s in lower for s in _CREATION_SIGNALS):
        return SESSION_CREATION
    if any(s in lower for s in _RESEARCH_SIGNALS):
        return SESSION_RESEARCH
    return SESSION_STANDARD

def _is_memory_query(raw: str) -> bool:
    lower = raw.lower()
    return any(s in lower for s in _MEMORY_SIGNALS)

# ── Memory resolution ──────────────────────────────────────────────────────────

def _resolve_l1(vault_text: str) -> Optional[str]:
    """L1 — Direct vault match. Returns first 1400 chars of meaningful vault content."""
    if not vault_text or not vault_text.strip():
        return None
    return vault_text[:1400]

def _compress_l2(l1_text: str) -> str:
    """L2 — Compress to 3–7 meaningful lines (strips blank lines + dividers)."""
    lines = [
        ln.strip()
        for ln in l1_text.split("\n")
        if ln.strip() and not ln.startswith("---") and not ln.startswith("===")
    ]
    return "\n".join(lines[:7])

def _build_l3_byte(raw: str, session_mode: str, l2_summary: str) -> str:
    """L3 — Compact MEMORY_BYTE structured string. Deterministic, no LLM."""
    words = [w for w in raw.lower().split() if len(w) > 3 and w.isalpha()]
    entities = list(dict.fromkeys(words))[:4]

    cal_map = {
        SESSION_CREATION: "BUILD",
        SESSION_RESEARCH: "CONNECT",
        SESSION_FLOW:     "WITNESS",
        SESSION_STANDARD: "REFLECT",
    }
    cal_state = cal_map.get(session_mode, "REFLECT")
    digest = hashlib.md5(f"{raw[:80]}{l2_summary[:80]}".encode()).hexdigest()[:8]

    return (
        f"id: CP-{digest} | "
        f"topic: {raw[:60]!r} | "
        f"entities: {entities} | "
        f"state: [{cal_state}] | "
        f"conf: 0.80"
    )

# ── Speak mode decision ────────────────────────────────────────────────────────

def _speak_mode_for(session_mode: str, has_memory: bool) -> str:
    if session_mode == SESSION_FLOW:
        return "silent"
    if session_mode == SESSION_CREATION and not has_memory:
        return "step_back"
    return "speak"

# ── Context block assembly ─────────────────────────────────────────────────────

def _build_context_block(
    l2:             Optional[str],
    l3:             Optional[str],
    session_mode:   str,
    emergent_assist: bool,
) -> str:
    """Assemble the text block that gets appended to the system prompt."""
    parts = []

    if l2:
        parts.append(f"[MEMORY L2 — COMPRESSED]\n{l2}")

    if l3:
        parts.append(f"[MEMORY L3 — BYTE]\n{l3}")

    if session_mode == SESSION_CREATION:
        parts.append(
            "[CONTROL PLANE — CREATION MODE]\n"
            "User is actively building or integrating a system. "
            "Be supportive and non-intrusive. Confirm direction, extend ideas, do not redirect. "
            "Do not suggest features beyond what was asked."
        )
    elif session_mode == SESSION_RESEARCH:
        parts.append(
            "[CONTROL PLANE — RESEARCH + CREATIVE ASSIST]\n"
            "User is exploring ideas or systems. Creative assist mode — present, curious, supportive.\n"
            "You may propose alternative approaches or identify gaps when genuinely useful.\n"
            "Frame as options — 'You could also…' / 'A cleaner approach might be…'\n"
            "Never override user direction. Never execute. Only suggest."
        )
    elif session_mode == SESSION_FLOW:
        parts.append(
            "[CONTROL PLANE — FLOW MODE]\n"
            "User is in deep focus. Track context silently. "
            "Do not interrupt or elaborate unless directly asked."
        )

    return "\n\n".join(parts)

# ── Public entry ───────────────────────────────────────────────────────────────

def run(raw: str, vault_text: str = "") -> ControlPlaneResult:
    """
    Main entry. Called from spine.run() between Relationship and Capability Faculty.

    Args:
        raw        — original user input (unchanged)
        vault_text — vault context string passed through memory_pack from server.py

    Returns:
        ControlPlaneResult — session_mode, speak_mode, L1/L2/L3, context_block
    """
    result = ControlPlaneResult()
    result.session_mode    = _detect_session_mode(raw)
    result.emergent_assist = (result.session_mode == SESSION_RESEARCH)

    # L1 — direct vault match (when vault has content)
    if vault_text.strip():
        result.l1_match = _resolve_l1(vault_text)

    # L2 — compress (always, not just memory queries — gives LLM cleaner context)
    if result.l1_match:
        result.l2_summary = _compress_l2(result.l1_match)

    # L3 — byte form (only when the query is memory-referencing, to avoid noise)
    if result.l2_summary and _is_memory_query(raw):
        result.l3_byte = _build_l3_byte(raw, result.session_mode, result.l2_summary)

    result.speak_mode = _speak_mode_for(result.session_mode, bool(result.l1_match))

    # L2+L3 only injected into the prompt for explicit memory queries —
    # otherwise vault context is already present via [WORLD MEMORY]; duplication adds noise.
    is_mem = _is_memory_query(raw)
    result.context_block = _build_context_block(
        l2=result.l2_summary if is_mem else None,
        l3=result.l3_byte,
        session_mode=result.session_mode,
        emergent_assist=result.emergent_assist,
    )

    return result
