# Board Review — 0060: DRIFT EMERGENCY — eLo jammed in GROUND
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

- §C: fallback backends (Cerebras/Ollama) skipped eLo's voice guards — PLAIN BUG
- §D: world-knowledge injection stored as David's words in session_summaries — PLAIN BUG
- §A/§B: routing order change — DAVID L3 REQUIRED (routing table produced, no implementation)

---

## §C — Fallback backends skip voice guards

**Status: ✅ DONE in prior session (F-3 remediation, 2026-08-21)**

`_finish()` now updates `_last_responses[action]` and applies `_is_duplicate` on the Cerebras and Ollama paths — same guards as the Groq path. A second near-identical generation via any backend raises `ValueError("duplicate")` before it reaches the caller.

---

## §D — World-knowledge injection stored as David's words

**Status: ✅ DONE in prior session (2026-08-23)**

`session_summaries` now persists `user_input` (David's raw utterance) not the assembled context block. One contaminated entry (`memory/interactions.json` index 915) was found and cleaned. 

Sweep count: 1 confirmed `[WORLD_KNOWLEDGE` prefix in `user` field, now cleaned. No others found.

---

## §A/§B — Routing table (David L3 required)

The before/after routing table for David's 8 turns is in the card body (§A/§B section). Summary:

- **BEFORE (old gate):** `executive.py:219` unconditionally routed `negative_low` valence → GROUND before any intent check. Turn 8 ("I don't want you to drift too much") hit this gate. Live session compounded it: each GROUND response fed back as `low-energy` history, pushing subsequent turns' valence negative and chaining more GROUND calls.
- **AFTER (F-3 fix):** GROUND now gated on `intent in ("emotional", "stabilise") AND valence negative`, or `momentum == "stuck"`. Negative valence alone is not sufficient. "Food wise, are you defaulting to Cerebas?" now routes to `answer` in isolation.
- **David's ruling still needed:** Whether the canonical dispatch order (ANSWER > BUILD > CONNECT > CELEBRATE > REFLECT > GROUND) should be explicitly enforced in code structure, or whether F-3 is sufficient. Current code follows the intent; docstring reflects it.

---

## Tests — `tests/test_wo_drift001_register.py`

```
tests/test_wo_drift001_register.py::test_t1_david_turns_not_all_ground PASSED
tests/test_wo_drift001_register.py::test_t2_food_question_routes_to_answer PASSED
tests/test_wo_drift001_register.py::test_t3_duplicate_guard_fires PASSED
tests/test_wo_drift001_register.py::test_t4_finish_updates_last_responses PASSED
tests/test_wo_drift001_register.py::test_t5_shopping_sentence_not_negative_low PASSED
tests/test_wo_drift001_register.py::test_t6_consecutive_duplicate_via_finish PASSED

6 passed in 0.15s
```

All 6 green. Tests include the regression guard (T6: `ValueError` on duplicate via `_finish()`) and the F-3 routing check (T1/T2: negative valence alone does not jam the gate).

---

## Board decisions required

1. **§A/§B canonical dispatch order:** David to confirm F-3 is sufficient or request explicit function-structure ordering. The routing table in the card body is the evidence.
2. No other blockers.

*Builder 1 · 2026-10-11*
