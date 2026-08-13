# Phase 03 — Architecture Review

**Phase:** Semantic World Model
**Status:** 📐 ARCHITECTURE PHASE — implementation blocked until Phase 2.5 FROZEN
**Date:** 2026-07-10
**Decision:** DESIGN APPROVED — implementation pending validation gate

---

## Phase Objective

Phase 3 replaces eLo's flat keyword→cluster lookup with a traversable conceptual fabric. The goal is not better keyword matching — it is semantic understanding of concept families.

The difference:
- Phase 2: `"blender" → "creation"`. `"servo" → "embodiment"`. They share no relationship.
- Phase 3: blender, rig, IK, FK, skeleton, animation, avatar, servo, robot, motion are one family. They are understood to be related, with distances between them.

This is the Semantic World Model — not a memory system and not a knowledge graph in the AI sense. It is the conceptual fabric that makes eLo's attention coherent rather than coincidental.

---

## Architecture Constants Check

| Constant | Status | Notes |
|---|---|---|
| One Brain | ✅ COMPLIANT | Semantic World Model is a subsystem of Attention Faculty |
| One Executive | ✅ COMPLIANT | No Executive modification planned |
| Faculties Observe | ✅ COMPLIANT | SWM produces concept families for scoring; it does not decide |
| FREEZE_V1_LOCK | ✅ COMPLIANT | No frozen files touched |
| Silence is Valid | ✅ COMPLIANT | If no family membership found, `_to_concepts()` returns empty — same as Phase 2 |
| Evidence Gates | ⚠️ GATE | Implementation must not begin until Phase 2.5 is FROZEN |

---

## What Phase 3 Changes

### Inside connection_surface.py

**`_to_concepts(tokens)` — internal replacement:**

Phase 2: `token → keyword_dict → cluster_name`

Phase 3: `token → graph node → traverse neighbors → collect family memberships`

The function signature and return type remain identical: `set[str] → set[str]`. The internals change. The interface does not.

**`_score_pair(concepts_a, concepts_b)` — internal enhancement:**

Phase 2: shared cluster check → `(shared_concept, raw_score) | None`

Phase 3: semantic distance between concept families → richer scoring. Two concepts in the same family but far apart score lower than two concepts that are direct neighbors.

The return type remains identical: `(str, float) | None`. The scoring becomes more semantically meaningful.

### New file: `memory/journal_router.py`

```python
def recent_topics(n_sessions: int = 3) -> list[str]:
    # Reads last n journal filenames + extracts date + title tokens
    # Returns: ["2026-07-10 robot IK chain", "2026-07-08 book narrative", ...]
```

This API feeds the memory stream in connection_surface.py with richer, date-anchored context.

### Concept families (the core data model)

Not a flat dict. A graph where each concept has:
- Cluster membership (same as Phase 2 — backward compatible)
- Neighbors (directly related concepts)
- Semantic distance to other concepts (0.0 = same, 1.0 = unrelated)

Example family (embodiment):
```
robot ─── servo ─── motor
  │          │
avatar ─── rig ─── skeleton ─── bones
              │
          animation ─── IK ─── FK
                    │
                   walk ─── motion ─── gesture
```

All nodes in this family are "embodiment" cluster members. But `robot` and `walk` are further apart than `rig` and `skeleton`.

---

## Memory Components (from original Phase 3 definition)

These are retained and explicitly part of Phase 3:

- Importance Evolution — memories gain/lose weight over time
- Memory Decay — old memories fade unless reinforced
- Journal Routing — `journal_router.py` with `recent_topics()`
- Memory Retrieval — surface specific memories with session reference
- Memory Confidence — how certain eLo is about a memory

The `memory_reference` and `concept_path` fields in `AttentionSnapshot` are populated in Phase 3.

---

## Risks

1. **Graph traversal performance** — If the concept graph is large and traversal is exhaustive, `get_observation()` could become slow. Mitigation: limit traversal depth (max 2 hops); cache family membership per token.

2. **Phase 2.5 findings may change the design** — Validation results could reveal that Phase 2's concept clustering is less accurate than designed, requiring more aggressive redesign than planned. Dependency on Phase 2.5 freeze is therefore critical.

3. **Memory decay and importance are complex** — These subsystems are well-defined in theory but may behave unexpectedly in practice. Phase 3 validation must include a memory-specific test suite.

---

## Recommendation

**DESIGN APPROVED.** Architecture is sound and extends Phase 2 correctly. Implementation blocked until Phase 2.5 FROZEN.

When Phase 2.5 freezes, return here to begin Step 02 (Current State Audit) of the Phase 3 lifecycle.
