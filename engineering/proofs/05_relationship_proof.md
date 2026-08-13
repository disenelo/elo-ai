# WP-F Relationship Faculty — Current Reality Review

**Status:** REVIEW COMPLETE — 2 gaps found
**Audit date:** 2026-07-12

---

## Faculty location

| File | Responsibility |
|---|---|
| `runtime/spine/relationship_faculty.py` | Sole faculty file — rapport, trust, register detection |
| `core/attention.py` | Reads relationship context (read-only consumer) |
| `memory/state_manager.py` | Stores `rapport_score`, `interaction_count` |

---

## What Relationship Faculty does

- Scores rapport (0.0–1.0) from interaction count, emotional_history, session_summaries
- Classifies relationship tier (new / acquaintance / familiar / trusted / close)
- Detects register (South London / Patois signals, Cockney)
- Infers name from history (`_infer_name()`)
- Returns: `{rapport, tier, interaction_count, last_session, register, name}`

---

## Invariant compliance

**Invariant 06 — Relationship Faculty contributes context, never decides:** ✓ COMPLIANT

- Does not call LLM ✓
- Does not modify session state ✓
- Does not route traffic ✓
- Does not generate text ✓
- Output consumed by Executive (via spine), not by LLM directly ✓

---

## Violations Found

### V1 — Register detection duplicated (MEDIUM)

Same register signals detected in three places:
- `runtime/spine/relationship_faculty.py:96–106` — South London + Patois
- `runtime/executive.py:305–323` — same signals + Cockney (frozen file)
- `runtime/router/meaning_engine.py` — social/greeting signals (partial overlap)

Register is a language interpretation concern (belongs in Language Faculty, per WP-C finding). Its presence in Relationship Faculty is a boundary misassignment.

**Fix:** Move to Language Faculty (when WP-C is implemented). Relationship Faculty should consume the pre-computed register from Language Faculty output rather than re-detecting it.

---

## Gaps Found

### G1 — Trust score has no time decay (MEDIUM)

`rapport_score` is computed from `interaction_count + emotional_history length + session_summaries count`. No time component. A user who had 100 interactions 6 months ago and then was absent has the same trust score as one who spoke yesterday.

The architecture doc for WP-F specifies: "trust accrues and decays with time, not interaction count alone."

**Fix:** Incorporate a decay factor in `_score_rapport()`:
- Read `last_session` timestamp from state
- Apply exponential decay over weeks of silence
- Clamp result floor (trust never goes to zero after first session — some warmth preserved)

### G2 — No independent trust signal (MEDIUM)

Current trust is purely computed from volume (count of interactions, count of sessions). There is no mechanism for eLo to receive an explicit trust signal from the user or from a high-significance event (e.g., a deep emotional disclosure, a maintained commitment).

Architecture intent: "specific interaction types can accelerate trust" (emotional disclosure, creative breakthrough, maintained commitment).

**Fix:** In `significance_engine.py`, when score > 0.85 and category is `emotional` or `creative`, write a `trust_signal` to elo_state.json. Relationship Faculty reads this as a multiplier.

---

## Summary Table

| Expectation | Reality | Match? |
|---|---|---|
| Rapport scored | ✓ 0.0–1.0, 5 tiers | ✓ |
| Register detected | ✓ (but duplicated in executive.py + here) | ⚠️ |
| Does not decide | ✓ Pure context contributor | ✓ |
| Trust decays over time | ✗ No time component | 🔴 |
| Trust accelerated by interaction type | ✗ Volume only | 🔴 |
| Name inferred | ✓ `_infer_name()` reads history | ✓ |
