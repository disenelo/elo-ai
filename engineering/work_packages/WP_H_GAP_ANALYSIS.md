# WP_H — Spine Gap Analysis

**Status:** REVIEW COMPLETE — 4 violations (3 HIGH, 1 MEDIUM)
**Proof document:** `engineering/proofs/07_spine_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Spine assembles, never decides | ✗ `_select_capabilities()` is a decision in spine | 🔴 GAP |
| All faculties called per turn via spine | ✗ Memory Faculty missing from spine call sequence | 🔴 GAP |
| Faculty call order documented and consistent | ✗ Header, docstring, and code all disagree | 🔴 GAP |
| CognitivePlan structure correct | ✓ Matches spec | ✓ Match |
| Embodiment delivery correct | ✓ CognitivePlan consumed correctly | ✓ Match |
| Executive fragmentation resolved | ✗ Three files own Executive logic | 🔴 GAP |

---

## Gaps requiring implementation

### GAP 1 — Spine makes a capability decision (🔴 HIGH)

**What exists:** `_select_capabilities(intent, agents)` in `spine.py:194–204` — a decision-making function inside the assembly layer.

**Resolution:** Move to `runtime/spine/executive_extension.py` (created by WP-G GAP 2). Update spine.py to call `executive_extension.select_capabilities()` after `_executive_faculty()`.

**Dependency:** WP-G GAP 2 must be implemented first.

**Implementation scope:** `runtime/spine/spine.py` (~5 lines changed after WP-G creates executive_extension.py)

---

### GAP 2 — Memory Faculty missing from spine (🔴 HIGH)

**What exists:** No `_memory_faculty()` function in spine.py. Memory is loaded at session start in server.py and injected as a static parameter.

**Resolution:** Add `_memory_faculty(user_input, session_state, current_pack)` to spine.py:
- Checks if a significant vault write occurred this turn (`significance > 0.70`)
- If yes: calls `memory_pack_builder.rebuild_partial()` or `obsidian_loader.load_recent()`
- Returns updated memory pack to downstream faculties (attention.compute receives fresh pack)

**Dependency:** Coordinate with WP-D implementation (same fix, approached from the spine side).

**Implementation scope:** `runtime/spine/spine.py` (~20 lines), placed after language faculty call, before attention faculty call.

---

### GAP 3 — Faculty call order inconsistency (🔴 MEDIUM)

**Three conflicting sources:**
1. Spine.py header docstring: `Language → Attention → Memory → Relationship → Executive → Capability → Embodiment`
2. Spine.py function comments: `Language → Meaning → Attention → Relationship → Executive → Embodiment`
3. Actual code: `Language → Attention → Relationship → Executive → Capabilities → Embodiment`

**Resolution:**
- Pick the **correct authoritative order**: Language → Attention → Memory → Relationship → Executive → Capabilities → Embodiment
- Update `spine.py` header docstring to match this order
- Remove the conflicting function comment block
- Reorder actual calls if needed (Memory should come after Attention since attention needs the pack)

**Implementation scope:** `runtime/spine/spine.py` docstring + comments only, no logic change (unless reorder needed)

---

### GAP 4 — Executive responsibility fragmented across three files (🔴 HIGH)

**Three files that contain Executive logic:**
1. `runtime/executive.py` (core: tone, action, sentences) — FROZEN
2. `server.py` (stabilisation override)
3. `spine.py` (capability selection, `_executive_faculty()` wrapper)

**Resolution:**
- GAP 1 above moves capability selection to `executive_extension.py`
- WP-G GAP 1 fixes the stabilisation override in `server.py`
- After both are done: `executive_extension.py` becomes the documented extension point for all Executive-layer logic that cannot go into the frozen file
- Add a comment to `runtime/executive.py` header: "Extensions in runtime/spine/executive_extension.py"

**Dependency:** WP-G GAP 1 + GAP 2.

---

## Implementation priority order (within WP-H)

1. **GAP 3 first** — docstring fix. Zero-risk, no logic change.
2. **GAP 1** — move capability selection out of spine (after WP-G creates executive_extension.py).
3. **GAP 2** — add `_memory_faculty()` (coordinate with WP-D).
4. **GAP 4** — resolved automatically by GAP 1 + WP-G GAP 1.

---

## Cross-WP dependencies

| Gap | Depends On |
|---|---|
| GAP 1 (capability out of spine) | WP-G GAP 2 (executive_extension.py created) |
| GAP 2 (memory faculty in spine) | WP-D GAP 1 (memory_pack refresh exposed) |
| GAP 4 (fragmentation) | WP-G GAP 1 (stabilisation fix) |

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| 14 — Spine assembles, never decides | ✗ VIOLATED | ✓ (after GAP 1) |
| All faculties called per turn | ✗ Memory missing | ✓ (after GAP 2) |
| Faculty order documented correctly | ✗ Inconsistent | ✓ (after GAP 3) |
