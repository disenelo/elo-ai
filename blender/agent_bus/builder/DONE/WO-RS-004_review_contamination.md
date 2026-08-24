# WO-RS-004 — Stop Review Contamination
**Priority:** P1 (after WO-RS-002)
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`
**Date:** 2026-08-22

---

## Objective

Stop review/test questions from being written into persistent vault memory as though they were legitimate saves. Break the contamination loop at the write-intent decision.

## The problem

```
review question
      ↓
vault_write triggered
      ↓
review artefact saved as memory
      ↓
future retrieval
      ↓
wrong context injected
      ↓
wrong answer
```

## What to build

Implement `is_save_intent()` check at the vault write path. A review-mode question ("What are you uncertain about?") must not become a vault memory simply because `vault_write` was invoked.

The check is at write-intent, not at question content. WO-RS-002 (REVIEW_STATE blocks writes entirely) is the primary fix. This WO hardens the normal write path so genuine save intent is required even outside REVIEW_STATE.

## Acceptance

- Review question in REVIEW_STATE → no vault write (covered by WO-RS-002)
- Review question in normal mode without save intent → no vault write
- Legitimate save ("Remember that X") → vault write proceeds normally
- Existing vault contents unchanged

## Hard constraints — do NOT

- add question-specific patches or title matching
- add special-case RS test rules
- build new memory architecture
- modify WKG or SPG
- add a blacklist of review questions

The fix is at the write-intent gate, not at question recognition.

---

## CLOSED — 2026-08-23

**Status:** ✅ COMPLETE

**Implementation:** `memory/execution_context.py` — `is_save_intent()`, `apply_vault_write_guard()`, integrated into `apply_policy_gate()`.

**Acceptance results — `tests/test_hard01_rs003_rs004.py::TestWoRs004ReviewContamination`:**

| Test | Result |
|---|---|
| Review question is not save intent | ✅ PASS |
| Save phrases are save intent | ✅ PASS |
| Vault write blocked without save intent | ✅ PASS |
| Vault write proceeds with save intent | ✅ PASS |
| Trace records no-save-intent strip | ✅ PASS |
| REVIEW_STATE still blocks even with save intent | ✅ PASS |

**6/6 passed.** Hard boundary compliance: no question-specific patches, no blacklist, no new memory architecture, WKG/SPG untouched.
