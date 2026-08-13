# WP_F — Relationship Faculty Gap Analysis

**Status:** REVIEW COMPLETE — 2 gaps (MEDIUM)
**Proof document:** `engineering/proofs/05_relationship_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Rapport scored 0.0–1.0 | ✓ 5 tiers: new/acquaintance/familiar/trusted/close | ✓ Match |
| Trust accrues and decays with time | ✗ Volume-only scoring (interaction count, session count) | 🔴 GAP |
| Specific interaction types accelerate trust | ✗ No interaction-type multiplier | 🔴 GAP |
| Register detected by Language Faculty | ✗ Register detected here AND in executive.py | ⚠️ Debt (WP-C owns fix) |
| Relationship Faculty contributes, never decides | ✓ Pure context contributor | ✓ Match |
| Name inferred from history | ✓ `_infer_name()` reads session history | ✓ Match |
| Does not call LLM | ✓ Pure computation | ✓ Match |
| Does not modify session state | ✓ Confirmed | ✓ Match |

---

## Gaps requiring implementation

### GAP 1 — Trust score has no time decay (🔴 MEDIUM)

**What architecture expects:** Trust accrues over time but also decays when interaction lapses. A user absent for 6 months should feel less familiar than one active last week — not because they've changed, but because relationship warmth cools with silence.

**What exists:** `_score_rapport()` in `relationship_faculty.py` sums `interaction_count + len(emotional_history) + len(session_summaries)`. No timestamp component.

**Resolution:**
- Read `last_session` from session state
- Compute `days_since_last` = (today - last_session).days
- Apply exponential decay: `rapport *= exp(-0.005 * days_since_last)` (roughly half after 140 days)
- Clamp to minimum of 0.1 after first session (warmth never fully lost)
- Cap decay at 0.8× to prevent aggressive drop after a short break

**Implementation scope:** `runtime/spine/relationship_faculty.py` `_score_rapport()` (~10 lines)

---

### GAP 2 — No trust signal from high-significance interactions (🔴 MEDIUM)

**What architecture expects:** Deep emotional disclosure, creative breakthroughs, maintained commitments — these specific interaction types should accelerate trust beyond what volume alone reflects.

**What exists:** Trust is purely count-based. A session of 100 trivial exchanges scores higher than 1 deeply significant exchange.

**Resolution:**
- In `memory/significance_engine.py`, after scoring: when `score > 0.85` AND category is `emotional` or `creative`, append a `trust_signal: true` marker to the session state
- In `relationship_faculty.py` `_score_rapport()`: read `trust_signals` count from session state and apply a multiplier (each signal adds +0.05 rapport, cap at 3 signals = +0.15)
- The multiplier amplifies warmth from meaningful moments, not just frequency

**Implementation scope:** `memory/significance_engine.py` (~5 lines), `runtime/spine/relationship_faculty.py` (~8 lines), `memory/state_manager.py` (add `trust_signals` list to state schema)

---

## Register detection (WP-C dependency)

Register detection lives in `relationship_faculty.py:96–106`. This is a misassignment — it belongs in Language Faculty. The fix is tracked in WP-C GAP 1. When WP-C is implemented, relationship_faculty.py should be updated to read `language_result["register"]` rather than detecting it independently.

**No separate action needed here** — follow WP-C implementation.

---

## Implementation priority order

1. **GAP 1** — time decay. Simple, high value. Makes rapport honest across lapsed sessions.
2. **GAP 2** — trust signals. Requires state_manager schema change + significance_engine addition.

---

## Invariants unblocked

| Invariant | Status Now | Status After |
|---|---|---|
| Relationship Faculty boundary correct | ✓ Already correct | ✓ |
| Trust reflects actual relationship quality | ✗ Volume only | ✓ (after GAP 1 + GAP 2) |
