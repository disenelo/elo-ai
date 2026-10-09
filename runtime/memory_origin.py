"""
runtime/memory_origin.py — Memory Origin Classification

Every memory entry must carry an origin tag. The origin determines:
    - Whether the memory is eligible for automatic long-term storage
    - Whether it goes to the main vault or the dream journal
    - How it is weighted during consolidation

The canonical distinction (Four-Layer Identity Model, 2026-08-31):

    REAL_EXPERIENCE     → episodic trace → consolidation → long-term memory
    DREAM_SIMULATION    → simulated experience → reflection → optional retention

A DREAM_SIMULATION entry becomes DREAM_INSIGHT ONLY after explicit
significance assessment returns a score above the retention threshold.
It MUST NOT automatically become factual memory or self-model truth.
"""
from enum import Enum


class MemoryOrigin(str, Enum):
    REAL_EXPERIENCE  = "real_experience"   # from actual conversation / events
    EPISODIC_TRACE   = "episodic_trace"    # short-term, not yet consolidated
    CONSOLIDATED     = "consolidated"       # passed through consolidation; long-term
    DREAM_SIMULATION = "dream_simulation"  # internally generated; guarded from auto-storage
    DREAM_INSIGHT    = "dream_insight"     # dream-derived insight that earned significance
    SELF_MODEL       = "self_model"        # eLo's understanding of itself
    SEMANTIC         = "semantic"          # abstract knowledge, not tied to a specific event
    # WO-CAP-EMB-051 — the embodiment distinction. "This is non-negotiable."
    SIMULATED_EXPERIENCE = "simulated_experience"  # a body did it — a simulated one
    PHYSICAL_EXPERIENCE  = "physical_experience"   # the physical body actually did it


# ── WO-CAP-EMB-051: simulated vs physical experience ──────────────────────────
#
# Verbatim source §51:
#     SIMULATED EXPERIENCE
#     PHYSICAL EXPERIENCE
#     eLo can remember both.
#     But they must be labelled differently.
#     Otherwise:
#     I already know how this works.
#     could mean:
#     I tested it in Unity.
#     when it has never physically done it.
#
# REAL_EXPERIENCE above does not carry this distinction — an action in the
# Unity desktop avatar and an action by the robot were both "real". eLo can
# remember both, so neither is excluded from storage; the point is that they
# are LABELLED differently and a simulated memory can never be the basis for
# a claim of physical capability.

SIMULATED_EMBODIMENTS: frozenset[str] = frozenset({
    "desktop", "unity", "terminal", "alexa", "phone", "ios", "ipad", "sim",
})
PHYSICAL_EMBODIMENTS: frozenset[str] = frozenset({
    "robot", "pi", "pi5", "raspberry_pi", "animatronic", "body",
})


def current_embodiment(default: str = "desktop") -> str:
    """
    Which body eLo is in right now, read from the live state the server
    writes. Not declared — observed.
    """
    import json
    import os

    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "blender", "blender_state.json",
    )
    try:
        with open(path, encoding="utf-8") as f:
            value = json.load(f).get("embodiment")
        return str(value).strip().lower() if value else default
    except Exception:
        return default


def origin_for_embodiment(embodiment: str | None = None) -> MemoryOrigin:
    """
    The origin an experience in this body should carry.

    An unrecognised embodiment is treated as SIMULATED. Defaulting the other
    way would let a new body silently claim physical experience it has not
    had, which is the exact failure §51 forbids.
    """
    name = (embodiment or current_embodiment()).strip().lower()
    if name in PHYSICAL_EMBODIMENTS:
        return MemoryOrigin.PHYSICAL_EXPERIENCE
    return MemoryOrigin.SIMULATED_EXPERIENCE


def is_physical(origin: MemoryOrigin | str) -> bool:
    """True only for experience a physical body actually had."""
    try:
        return MemoryOrigin(origin) is MemoryOrigin.PHYSICAL_EXPERIENCE
    except Exception:
        return False


def can_claim_physical_experience(origin: MemoryOrigin | str) -> bool:
    """
    May eLo say "I have done this" on the strength of a memory with this
    origin?

    Only a physical body earns that. Simulated experience, dreams, semantic
    knowledge and the self-model all answer False — "I tested it in Unity"
    is not "I have physically done it".
    """
    return is_physical(origin)


# The canonical significance threshold for promoting DREAM_SIMULATION → DREAM_INSIGHT.
# Anything below this must NOT enter the main memory vault.
# Lowered 0.72 -> 0.65 on David's ruling 2026-10-09: "0 of 216 retained is not
# acceptable. Lower it until dreams are being retained and the retained content
# is good. It can always be raised again."
#
# Board proposed 0.65 on the basis that the observed max was 0.700, so
# "something should land immediately". Measured before changing: that 0.700 is
# a single historical outlier. The last twelve dreams score 0.260-0.560, so at
# 0.65 nothing retains GOING FORWARD and the ruling is not met.
#
# 0.45 instead, because the scores are not a curve. 82 of 103 scored dreams sit
# at exactly 0.4000 -- 0.40 x dream_intensity(1.0), with all three other terms
# contributing zero. 0.45 clears that degenerate floor by 0.05 and so admits
# ONLY dreams where a second signal actually fired (emotion or recurrence):
# 4 of 103 historically, and the better recent dreams.
#
# This is a deliberate deviation from the Board's number, serving David's
# ruling ("lower it until dreams are being retained") over an arithmetic guess
# built on a figure I supplied. One line to put back. Filed 2026-10-09 with
# the term-by-term evidence; the scorer, not the threshold, is the real defect.
DREAM_RETENTION_THRESHOLD: float = 0.45


def is_auto_storable(origin: MemoryOrigin) -> bool:
    """
    Returns True when a memory origin may be written to the main vault automatically.
    DREAM_SIMULATION is explicitly excluded — it requires a significance gate.
    """
    return origin != MemoryOrigin.DREAM_SIMULATION
