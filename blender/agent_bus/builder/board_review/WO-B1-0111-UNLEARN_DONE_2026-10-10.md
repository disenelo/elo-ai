# BUILDER 1 → BOARD: WO-B1-0111 Unlearn Mechanism — Built
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `258da94`

---

## What was done

Implemented the full correction / unlearn pipeline. No LLM involved — fires pre-LLM, same tier as FACT dispatch.

### Three-file change

**`runtime/capability_dispatcher.py`**
- Added `TIER_CORRECTION = "CORRECTION"`
- Added 8 `_CORRECTION_PATTERNS` covering natural correction phrasing:
  - "that's wrong / incorrect / false / off / not right"
  - "forget that / forget what you said"
  - "you've got me wrong" / "got it wrong"
  - "I don't have / never said / didn't do X"
  - "that's not me / mine / accurate / correct"
  - "unlearn that"
- Added `is_correction(request: str) -> bool` — pure pattern check
- Added `dispatch_correction(request: str) -> dict | None` — calls `deprecate_recent_claims()`, returns in-character ack or "nothing to unlearn" fallback

**`runtime/wkg_faculty.py`**
- Added `_session_profile_claim_ids: list[str]` — module-level session tracker
- Updated `get_relationship_profile()` to populate it with the claim IDs of every fact actually returned (after all quality filters pass)
- Added `deprecate_recent_claims(reason, max_deprecate=3)` — marks top N session claims as contradicted using the existing `contradicted_by` mechanism; claims with any entry in `contradicted_by` are already gated out of `get_relationship_profile()` retrieval; reversible (sentinel is `user_correction_<ts>`)

**`tools/tool_router.py`**
- Added correction intercept in `_direct_intercepts()`, before the lore/health checks
- Flow: `is_correction()` → `dispatch_correction()` → voice response → log to `data/decision_trace.jsonl` → return `(response, "wkg_correction")`

### In-character responses

With prior profile: `"Got it — I had that wrong. I've flagged it. What's the right version?"`  
Without prior profile: `"Noted. Nothing flagged from my last recall to unlearn — tell me what's right and I'll hold it."`

---

## Test results

- 10/10 pattern detection cases correct (False positives for time/weather/general questions: 0)
- End-to-end: `get_relationship_profile()` → populated 12 session IDs → `dispatch_correction()` → 3 claims deprecated → session IDs cleared → in-character ack returned ✅
- Live data restored (3 test-deprecated claims reverted) ✅
- All three files parse clean ✅

---

## Done when criterion

"eLo says something wrong about David. David says 'that's wrong.' eLo acknowledges, the fact stops appearing in future profile retrievals."

Board must verify across 2 live turns: one with a prior profile retrieval, one without (cold session). Server restart required.

---

## Outstanding

- `memory/unlearn_protocol.py` full 4-stage pipeline (OLD → CONTRADICTED → RETIRED → NEW) is not yet wired to this path. Current implementation uses the lighter-weight `contradicted_by` mechanism which achieves the demo criterion. Full pipeline integration is a future WO.
- Keyword-targeted correction ("that's wrong about the Keychron") not yet implemented — currently deprecates top 3 by confidence regardless of keyword context.
