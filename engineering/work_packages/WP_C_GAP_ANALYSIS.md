# WP_C — Language Faculty Gap Analysis

**Status:** REVIEW COMPLETE — 1 gap
**Proof document:** `engineering/proofs/02_language_proof.md`
**Next stage:** Implementation Plan

---

## What the architecture expects vs. what exists

| Architecture Expectation | Current Reality | Gap? |
|---|---|---|
| Input normalised before any other faculty | ✓ meaning_engine.normalise() first | ✓ Match |
| Typo repair in Language Faculty | ✓ typo_engine.repair() | ✓ Match |
| Intent classification owned by Language layer | ✓ intent_engine.detect() | ✓ Match |
| Register detection owned by Language Faculty | ✗ Split: relationship_faculty.py + executive.py | 🔴 GAP |
| Language Faculty does not call LLM | ✓ Pure string/regex operations | ✓ Match |
| Language Faculty does not modify session state | ✓ Confirmed | ✓ Match |
| Language Faculty does not route traffic | ✓ Confirmed | ✓ Match |

---

## Gaps requiring implementation

### GAP 1 — Register detection not in Language Faculty (🔴 MEDIUM)

**What architecture expects:** Register detection (South London, Patois, Cockney signals) is a language interpretation step. It belongs in the Language Faculty and should be computed once before downstream faculties run.

**What exists:**
- `runtime/spine/relationship_faculty.py:96–106` — detects South London + Patois
- `runtime/executive.py:305–323` — detects same signals + Cockney (FROZEN — cannot touch)

**Problem:**
- Register is detected twice per turn
- The copy in executive.py is frozen and cannot be removed
- Relationship Faculty reads register signals it shouldn't own

**Resolution:**
- Add `_detect_register()` to `runtime/spine/spine.py` `_language_faculty()` output
- Populate `result["register"]` before returning from language faculty
- Remove the call from `relationship_faculty.py` — have it read `language_result["register"]` instead
- Leave executive.py untouched (frozen) — it will continue detecting register independently, but the authoritative source is now language faculty

**Implementation scope:** `runtime/spine/spine.py` (~10 lines), `runtime/spine/relationship_faculty.py` (~5 lines removed)

---

## What already satisfies the architecture

- Input normalisation: Clean
- Typo repair: Clean
- Intent classification: Clean
- Social signal detection: Clean
- Language Faculty does not decide: Clean
- No LLM calls in Language Faculty: Clean

---

## Invariants unblocked after gap resolved

| Invariant | Status Now | Status After |
|---|---|---|
| Language Faculty boundary (implicit in Invariant 06) | ⚠️ Partial | ✓ |
