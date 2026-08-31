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


# The canonical significance threshold for promoting DREAM_SIMULATION → DREAM_INSIGHT.
# Anything below this must NOT enter the main memory vault.
DREAM_RETENTION_THRESHOLD: float = 0.72


def is_auto_storable(origin: MemoryOrigin) -> bool:
    """
    Returns True when a memory origin may be written to the main vault automatically.
    DREAM_SIMULATION is explicitly excluded — it requires a significance gate.
    """
    return origin != MemoryOrigin.DREAM_SIMULATION
