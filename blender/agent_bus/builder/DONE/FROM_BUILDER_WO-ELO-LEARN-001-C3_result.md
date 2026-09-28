# FROM BUILDER — WO-ELO-LEARN-001 Component 3 (WKG write enrichment on DEEP turns) — DONE

**Date:** 2026-09-15
**WO:** Self-assigned from DISPATCH_BOARD line 37 (proactivity ruling FROM_BOARD_2026-09-12)
**Status:** DONE + VERIFIED

---

## Problem

C3 required WKG enrichment from eLo's DEEP turn LLM responses. The faculty write-back
was intentionally disabled for all LLM backends (WO-MEMORY-REPLAY-001):

```
# DISABLED: extract_faculty_claims stored eLo's conversational responses as
# SOURCE_ATTRIBUTED WKG "facts". When eLo entity matched in future turns,
# claims (e.g. "eLo STATED: I keep starting things...") were injected as
# HIGHEST AUTHORITY context → verbatim replay.
```

The root issue: `SOURCE_ATTRIBUTED` + `confidence=0.65` caused replay because
`coverage_check()` SUFFICIENT gate counts `epistemic_class in (VERIFIED, SOURCE_ATTRIBUTED)
AND confidence >= 0.65`. These claims were reaching SUFFICIENT and being played back verbatim.

---

## Analysis

The SUFFICIENT gate can be bypassed safely by writing with `epistemic_class="HYPOTHESIS"`
and `confidence=0.5`. HYPOTHESIS claims:
- ARE written to WKG (enriches knowledge graph, SPG nodes built, entity associations stored)
- ARE NOT counted toward SUFFICIENT (not in VERIFIED/SOURCE_ATTRIBUTED set)
- CANNOT cause verbatim replay (never triggers coverage_check SUFFICIENT path)

Scoped to `action == "deep"` turns only: conversational/social turns (action=chat, build,
ground, etc.) remain fully disabled. Only deep analysis/planning turns produce this write.

---

## Fix applied

### `runtime/wkg_faculty.py`

Added `epistemic_class` and `confidence` override params to `extract_faculty_claims()`:

```python
# BEFORE:
def extract_faculty_claims(
    faculty_text: str,
    turn_text: str,
    source_id: str = "faculty",
    significance_score: float | None = None,
) -> list:
    ...
    c1 = record_claim(..., epistemic_class="SOURCE_ATTRIBUTED", confidence=0.65)

# AFTER:
def extract_faculty_claims(
    faculty_text: str,
    turn_text: str,
    source_id: str = "faculty",
    significance_score: float | None = None,
    epistemic_class: str = "SOURCE_ATTRIBUTED",
    confidence: float = 0.65,
) -> list:
    ...
    c1 = record_claim(..., epistemic_class=epistemic_class, confidence=confidence)
```

Default unchanged — all existing callers (non-LLM tool outputs) retain SOURCE_ATTRIBUTED/0.65.

### `server.py` — WO-ELO-LEARN-001 faculty write-back block

Re-enabled for DEEP action turns with HYPOTHESIS/0.5 override:

```python
_is_llm_backend = any(lb in str(_bc_backend).lower() for lb in _LLM_BACKENDS)
_is_deep_action = str(_action) == "deep"
if (response and raw
        and "base_cognition" not in str(_bc_backend)
        and "mock" not in str(_bc_backend)
        and len(response.strip()) >= 15
        and (not _is_llm_backend or _is_deep_action)):   # ← key gate
    from runtime.wkg_faculty import extract_faculty_claims as _efc
    _efc(
        response,
        turn_text=raw,
        source_id=str(_bc_backend) or "faculty",
        significance_score=float(_mem_sig) if _mem_sig else 0.5,
        **({"epistemic_class": "HYPOTHESIS", "confidence": 0.5}
           if _is_llm_backend else {}),
    )
```

---

## Evidence

```
DEEP write: 1 claims
  epistemic_class: HYPOTHESIS
  confidence: 0.5
  claim_text: eLo grew from the idea that imagination and reality can coexist — that is the co

Tool write: 1 claims
  epistemic_class: SOURCE_ATTRIBUTED
  confidence: 0.65

coverage_check sufficient: False | claims considered: 0
```

- DEEP LLM response → HYPOTHESIS/0.5 claim written to WKG ✓
- Tool/API backend → SOURCE_ATTRIBUTED/0.65 (original behaviour preserved) ✓
- HYPOTHESIS claims: `coverage_check()` sufficient=False, claims_considered=0 — replay gate immune ✓

---

## DoD Assessment

| Item | Status | Notes |
|------|--------|-------|
| DEEP turn LLM response → WKG enrichment | ✓ SERVING | HYPOTHESIS/0.5 written |
| Cannot trigger coverage_check SUFFICIENT | ✓ SERVING | conf=0.5 < 0.65 threshold |
| No verbatim replay risk | ✓ SERVING | HYPOTHESIS not in SUFFICIENT set |
| Non-LLM tool outputs unchanged | ✓ SERVING | SOURCE_ATTRIBUTED/0.65 preserved |
| Conversational LLM turns still blocked | ✓ SERVING | `_is_deep_action` gate |

**VERDICT: SERVING**

---

## Component Status (WO-ELO-LEARN-001 full picture)

| Component | Status |
|-----------|--------|
| C1: Core architecture (WKG-first routing, base_cognition, SPG, faculty write-back) | ✅ DONE |
| C2: SPG as real link layer (significance rerank in query_spg_entities) | ✅ DONE |
| C3: WKG write enrichment on DEEP turns | ✅ DONE (this card) |
| C4: Living Presence in base_cognition path | 🔴 BLOCKED — LIVING-PRESENCE-UPDATE-001 FREEZE |

*Builder · 2026-09-15*
