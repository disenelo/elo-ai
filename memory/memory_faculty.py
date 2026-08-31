"""
memory/memory_faculty.py — MemoryFaculty: single logical writer (WO-CANON-VIII)

Routes all durable memory writes through one decision owner.
Decides {write | reinforce | drop} for every incoming MemoryCandidate.
Physical writer stays vault_layer.write_memory — sole bytes writer, unchanged.

Spec: Volume VIII Ch.4 §4.1.2
Decision Log: D-F (Memory Faculty sole LTM writer, RATIFIED)
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ── MemoryCandidate ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MemoryCandidate:
    """
    Carries everything a faculty wants to persist.
    proposed_weight is a REQUEST — MemoryFaculty sets the final weight.
    proposed_type: episodic | semantic | procedural | emotional
    significance:  0.0–1.0 normalised score (from significance_engine or weight/9)
    verified:      True if the caller has fact-checked the content
    """
    source_faculty:  str   = ""          # "reflection" | "music" | "consolidation" | ...
    content:         str   = ""          # full memory body (deep_text)
    proposed_type:   str   = "episodic"  # episodic | semantic | procedural | emotional
    proposed_weight: int   = 5           # 0–9, REQUEST only — clamped to [1, 9]
    significance:    float = 0.0         # 0.0–1.0 normalised significance
    verified:        bool  = False       # fact-checked by caller?
    project:         str   = "general"   # vault domain label
    summary:         str   = ""          # one-sentence summary (≤200 chars after compress)
    tags:            tuple = field(default_factory=tuple)   # frozen tag list
    experience_id:   str   = ""          # WO-XDNA-001: per-turn identity minted by spine


# ── Constants ────────────────────────────────────────────────────────────────

_DROP_THRESHOLD = 0.15   # significance below this → drop (no write, no reinforce)

_TYPE_TO_MEMORY_TYPE: dict[str, str] = {
    "episodic":   "conversation",
    "semantic":   "learn",
    "procedural": "build",
    "emotional":  "connect",
}


# ── MemoryFaculty ────────────────────────────────────────────────────────────

class MemoryFaculty:
    """
    Single logical writer for all durable memory.

    submit() receives a MemoryCandidate and decides:
      DROP     — significance below threshold or empty content
      REINFORCE — existing record with matching summary found → strengthen it
      WRITE     — new vault record via vault_layer.write_memory (sole bytes call)

    Errors in reinforce or lookup never block a write — the fallback is always WRITE.
    """

    def submit(self, candidate: MemoryCandidate) -> dict:
        """
        Decide {write | reinforce | drop} and act.

        Returns:
            {
              "action": "write" | "reinforce" | "drop",
              "spot":   str | None,   # spot code if written or reinforced
              "reason": str,
            }
        """
        # ── DROP gate ─────────────────────────────────────────────────────────
        if not candidate.content.strip():
            return {"action": "drop", "spot": None, "reason": "empty content"}

        if candidate.significance < _DROP_THRESHOLD:
            return {
                "action": "drop",
                "spot":   None,
                "reason": (
                    f"significance {candidate.significance:.2f} "
                    f"below threshold {_DROP_THRESHOLD}"
                ),
            }

        # ── REINFORCE gate: existing record with matching summary? ────────────
        # A duplicate candidate for the same memory strengthens the existing
        # record rather than creating a second copy.
        if candidate.summary:
            try:
                from memory.vault_layer import lookup
                hits = lookup(candidate.summary[:60], max_results=1)
                if hits:
                    existing_spot = hits[0].get("spot", "")
                    if existing_spot:
                        from memory.consolidation_faculty import reinforce
                        reinforced = reinforce(existing_spot)
                        if reinforced:
                            return {
                                "action": "reinforce",
                                "spot":   existing_spot,
                                "reason": "existing record reinforced (duplicate candidate)",
                            }
            except Exception:
                pass  # lookup/reinforce failure → fall through to WRITE

        # ── WRITE ─────────────────────────────────────────────────────────────
        try:
            from memory.vault_layer import write_memory
            memory_type = _TYPE_TO_MEMORY_TYPE.get(candidate.proposed_type, "conversation")
            spot = write_memory(
                project=candidate.project,
                memory_type=memory_type,
                summary=candidate.summary or candidate.content[:200],
                deep_text=candidate.content,
                weight=max(1, min(9, candidate.proposed_weight)),
                tags=list(candidate.tags),
                experience_id=candidate.experience_id,
            )
            return {"action": "write", "spot": spot, "reason": "new record written"}
        except Exception as exc:
            return {"action": "drop", "spot": None, "reason": f"vault error: {exc}"}
