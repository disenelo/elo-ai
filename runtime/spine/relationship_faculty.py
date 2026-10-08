"""
runtime/spine/relationship_faculty.py — eLo OS v1.4 Relationship Faculty

Answers: WHO is speaking?

Provides relationship context to the Executive Faculty.
Never makes decisions. Only provides enriched context.

Pipeline position: after Attention, before Capability.

Architecture spec: docs/architecture/05_relationship_faculty.md
"""
from __future__ import annotations
import os
import json
import logging
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RelationshipContext:
    """
    Output of the Relationship Faculty.
    Passed to the Executive. Read-only by all downstream.

    Relationship affects expression posture only.
    Never alters reasoning, memory retrieval, or capability selection.
    """
    # Identity
    person_id:          str   = "david"       # primary user identifier
    relationship_type:  str   = "creator"     # creator | collaborator | friend | stranger

    # Familiarity: 0.0 = stranger, 1.0 = deeply established creative partner
    familiarity:        float = 0.55

    # Trust: 0.0 = guarded, 1.0 = full open expression
    trust:              float = 0.60

    # Register preference detected for this relationship
    # Persists as relationship context, not just turn-level detection
    register:           str   = ""            # SOUTH_LDN_MODE | PATOIS_MODE | HYBRID_MODE | ""

    # Active DISENELO projects mentioned this turn
    active_projects:    list  = field(default_factory=list)

    # Shared language markers specific to this relationship
    shared_markers:     list  = field(default_factory=list)

    # Expression posture hint for the Executive
    # close | warm | open | careful | neutral
    # Never changes reasoning — only warmth and register of expression
    expression_posture: str   = "warm"

    # WO-RELATIONSHIP-STYLE: relational developmental stage
    # new | developing | established | in_conflict | post_conflict
    relationship_mode:  str   = "developing"

    # Confidence in this relationship model (0.0–1.0)
    confidence:         float = 0.85


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL SETS
# ─────────────────────────────────────────────────────────────────────────────

_SOUTH_LDN_SIGNALS = frozenset({
    "wagwan", "innit", "mandem", "bruv", "blud", "fam", "bare", "peak",
    "wavey", "peng", "proper", "nang", "buff", "sketchy", "roadman",
    "ting", "gassed", "butters", "moist", "marvin", "neek", "wasteman",
    "on road", "dutty", "linking", "moving mad", "allow it", "don't watch that",
    "safe", "laters", "in a bit", "big up", "mandem", "ends", "yard",
})
_PATOIS_SIGNALS = frozenset({
    "jah", "rastafari", "irie", "zion", "blessed", "give thanks",
    "bless up", "one love", "the most high", "jah bless", "selassie",
    "ini", "ital", "jah guide", "greetings", "rasta",
})
_CREATOR_PROJECT_SIGNALS = {
    "elo os":       ["elo os", "the os", "elo-ai", "server.py", "spine", "cognitive"],
    "game":         ["the game", "elo planet", "elo-planet", "unity", "player", "weapon", "enemy"],
    "book":         ["the book", "elo book", "the story", "narrative", "4-act"],
    "robot":        ["the robot", "raspberry pi", "neopixel", "servo", "animatronic"],
    "plushies":     ["plushies", "sewing", "pattern", "blender addon", "uv island"],
    "retargeter":   ["retargeter", "mixamo", "auto-rig", "nla strip"],
    "disenelo":     ["disenelo", "kickstarter", "the brand", "vinyl", "art"],
}


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _detect_register(raw_lower: str) -> str:
    words = set(raw_lower.split())
    patois_hits   = len(words & _PATOIS_SIGNALS)
    south_ldn_hits = len(words & _SOUTH_LDN_SIGNALS)
    if patois_hits > 0 and south_ldn_hits > 0:
        return "HYBRID_MODE"
    if patois_hits > 0:
        return "PATOIS_MODE"
    if south_ldn_hits > 0:
        return "SOUTH_LDN_MODE"
    return ""


def _detect_active_projects(raw_lower: str) -> list[str]:
    found = []
    for name, signals in _CREATOR_PROJECT_SIGNALS.items():
        if any(s in raw_lower for s in signals):
            found.append(name)
    return found


def _compute_familiarity(session_count: int, profile: dict) -> float:
    """
    Familiarity grows with sessions. Creator relationship starts elevated.
    Caps at 0.98 — never claims complete knowledge.
    """
    base = 0.55                                          # creator baseline
    session_bonus = min(session_count * 0.008, 0.35)    # saturates ~44 sessions → +0.35
    depth_bonus   = 0.05 if profile.get("patterns", {}).get("compression_expansion") else 0
    return min(base + session_bonus + depth_bonus, 0.98)


def _expression_posture(familiarity: float) -> str:
    if familiarity >= 0.82:
        return "close"
    if familiarity >= 0.62:
        return "warm"
    return "open"


# Conflict/repair signal sets for _derive_relationship_mode
_CONFLICT_SIGNALS = frozenset({
    "that's wrong", "thats wrong", "you're wrong", "youre wrong",
    "you keep doing this", "stop doing this", "i'm frustrated", "im frustrated",
    "this is frustrating", "you never", "you always", "why do you keep",
    "this is wrong", "wrong again", "you got it wrong", "incorrect",
    "that was wrong",
})
_REPAIR_SIGNALS = frozenset({
    "it's fine", "its fine", "let's move on", "lets move on",
    "i forgive", "we're good", "were good", "no worries", "forget it",
    "it's okay", "its okay", "all good", "apology accepted",
    "nevermind", "never mind",
})


def _derive_relationship_mode(raw: str, familiarity: float) -> str:
    """Derive relationship mode from raw input and familiarity score.

    Priority: repair signal → post_conflict; conflict signal → in_conflict;
    then familiarity thresholds: ≥0.55 → established, else → new.
    """
    raw_lower = raw.lower()
    if any(sig in raw_lower for sig in _REPAIR_SIGNALS):
        return "post_conflict"
    if any(sig in raw_lower for sig in _CONFLICT_SIGNALS):
        return "in_conflict"
    if familiarity >= 0.55:
        return "established"
    return "new"


def _load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

def relationship_faculty_prompt_block(raw: str) -> str:
    """
    Build a compact prompt block from relationship context.

    Returns "" on any error (non-blocking).
    """
    try:
        ctx = analyse(raw)
        if not ctx:
            return ""
        lines = ["[RELATIONSHIP CONTEXT — who is speaking]"]
        lines.append(f"  Familiarity: {ctx.familiarity:.2f} / 1.0")
        lines.append(f"  Trust: {ctx.trust:.2f} / 1.0")
        lines.append(f"  Expression posture: {ctx.expression_posture}")
        if ctx.register:
            lines.append(f"  Register: {ctx.register.replace('_', ' ').lower()}")
        if ctx.active_projects:
            lines.append(f"  Active projects mentioned: {', '.join(ctx.active_projects[:3])}")
        return "\n".join(lines)
    except Exception:
        return ""


def analyse(raw: str, memory_pack: dict | None = None) -> RelationshipContext:
    """
    Analyse who is speaking and build relationship context.

    Args:
        raw:         raw user input (unchanged)
        memory_pack: pre-built memory context (may contain relationship hints)

    Returns: RelationshipContext — read-only context enriched for the Executive.

    This function never modifies state. It only reads and returns.
    """
    raw_lower = raw.lower().strip()

    profile       = _load_json(os.path.join(_ROOT, "memory", "user_profile.json"))
    state         = _load_json(os.path.join(_ROOT, "elo_state.json"))
    session_count = state.get("session_count", 0)

    register         = _detect_register(raw_lower)
    active_projects  = _detect_active_projects(raw_lower)
    familiarity      = _compute_familiarity(session_count, profile)
    trust            = min(familiarity + 0.10, 0.98)
    posture          = _expression_posture(familiarity)

    shared_markers = []
    if register:
        shared_markers.append(register.lower().replace("_mode", ""))
    shared_markers.extend(active_projects[:3])

    return RelationshipContext(
        person_id          = "david",
        relationship_type  = "creator",
        familiarity        = round(familiarity, 3),
        trust              = round(trust, 3),
        register           = register,
        active_projects    = active_projects,
        shared_markers     = shared_markers,
        expression_posture = posture,
        confidence         = 0.90,
    )
