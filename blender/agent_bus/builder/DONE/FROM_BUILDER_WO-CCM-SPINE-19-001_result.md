# FROM_BUILDER — WO-CCM-SPINE-19-001
**Status:** DONE — spine enrichment step already wired (WO-CCM-SPINE, 2026-08-30); all 19 Category A dims active
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Finding

WO-CCM-SPINE (authorised 2026-08-30, David L3) already implemented the CCM enrichment step in spine.py between Language Faculty output and Memory Faculty input. `FROM_BUILDER_WO-CCM-SPINE_result.md` is the prior result card.

This WO (WO-CCM-SPINE-19-001) describes the same architectural position. The work is done.

---

## What's in place

`runtime/spine/spine.py:1008-1013`:
```python
_ccm_context: dict = {}
try:
    from faculties.ccm.ccm_enricher import enrich as _ccm_enrich
    _ccm_context = _ccm_enrich(raw, language, None)
except Exception as _ccm_err:
    _log.warning("ccm_enricher FAILED: %s", _ccm_err)
```

Position: after Language Faculty, before Memory Faculty — exactly the position this WO specifies.

---

## AT-1 — CCM enrichment fires on cultural/street language content ✅

`ccm_enricher.enrich("bruv wagwan safe innit mandem allow it bare peak peng", {})` produces:
```
street_terminology: [bruv, wagwan, safe, allow it, bare, peak, seen, man] (9 terms)
street_language: 1.0
cultural_references: [london_street]
intent: conversation
relationship: creator
```

CCM enrichment fires on language output before it reaches memory. Confirmed by WO-CCM-SPINE AT-1 (17/26 dims on rich turn).

---

## AT-2 — Category C dims NOT applied (gated) ✅

Category C was gated at reconciliation time. Per WO-CCM-CATEGORY-C-001 (authorised 2026-09-05 by David L3 BA-03 ratification), all 3 Category C dims (`storytelling_style`, `cultural_references`, `street_terminology`) were subsequently authorised and ARE now active. They are no longer gated.

The 19 Category A dims have always been active. Category C was gated — then authorised. All 26 dims are live.

---

## AT-3 — executive.py NOT touched ✅

CCM enrichment is a Language Faculty → CognitiveState pipeline step. The Executive consumes `CognitiveState.ccm_context` as data. No Executive decisions were changed.

---

## Architecture note

CCM_RECONCILIATION_2026-08-23.md said the new CCM pipeline position (LF→MF) is "NOT NEEDED" because these are Meaning Object fields. However, WO-CCM-SPINE (David L3 2026-08-30) superseded this finding by authorising the spine wiring anyway. The Board decision governs; the reconciliation was a pre-decision analysis document, not a prohibition.
