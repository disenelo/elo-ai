# Phase 2.5 — Architecture Review

**Phase:** Cognitive Validation
**Date:** 2026-07-10
**Decision:** PROCEED (no implementation — validation only)

---

## Phase Objective

Phase 2.5 is not an implementation phase. It is an evidence phase.

Phase 2 built the Connection Surface, AttentionSnapshot, StreamDefinition, ring buffer, multi-signal confidence, hybrid cooldown, and session references — all theoretically correct. Phase 2.5 proves they are correct in practice, under real conditions.

Five validations must pass. Until they do, Phase 3 implementation does not begin.

---

## Architecture Constants Check

| Constant | Status | Notes |
|---|---|---|
| One Brain | ✅ COMPLIANT | No new faculties, no new decision paths — observation only |
| One Executive | ✅ COMPLIANT | Executive untouched |
| Faculties Observe | ✅ COMPLIANT | Validation is observational; nothing new decides |
| FREEZE_V1_LOCK | ✅ COMPLIANT | Frozen files untouched |
| Silence is Valid | ✅ COMPLIANT | Validation 3 tests that silence is the dominant behaviour |
| Evidence Gates | ✅ COMPLIANT | This phase IS the evidence gate |

---

## What This Phase Delivers

1. **Unit tests** for Phase 2 components (resolves Phase 2 Exception 1)
2. **5 runtime validation reports** (resolves Phase 2 Exception 2)
3. **Cooldown calibration** findings (resolves Phase 2 Exception 3)
4. **Phase 2 final freeze upgrade** from CONDITIONAL → FROZEN ✅

After Phase 2.5 freezes, Phase 2 becomes FROZEN ✅ and Phase 3 implementation can begin.

---

## What Phase 2.5 Does NOT Include

- No new code (except unit tests for Phase 2 components)
- No changes to connection_surface.py
- No changes to vision_loop.py
- No new cognitive streams
- No new concept clusters

If a validation reveals a bug, the bug is fixed in Phase 2 code. Phase 2.5 itself contains only tests and validation protocols.

---

## Risks

1. **Validation 3 fails (Connection Surface too eager)** — cooldown needs tightening. Fix: increase `ELO_CS_COOLDOWN_SEC` via env var. No code change.

2. **Validation 4 fails (Executive responds to observation)** — the g_ctx injection is weighted too heavily against the explicit conversation. Fix: review how the Executive prompt weights ambient vs. explicit context. Note: this may require a careful look at prompts/ without modifying them.

3. **Validation 5 is subjective** — "does this feel like someone sharing the space" has no binary pass. Findings feed into Phase 3 tuning requirements. Not a hard blocker.

---

## Recommendation

PROCEED — run the validations in order. Write the unit tests first (they're fast). Then do the runtime validations during a real 2-3 hour work session.
