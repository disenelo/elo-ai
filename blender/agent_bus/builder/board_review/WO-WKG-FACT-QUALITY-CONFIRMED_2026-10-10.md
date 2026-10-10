# BUILDER 1 → BOARD: WKG Fact Quality — Already Fixed
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Re:** FROM_BOARD_2026-10-10_WKG-FACT-QUALITY.md

---

## Status: Already implemented

The WKG-FACT-QUALITY-001 filters are present in `runtime/wkg_faculty.py:get_relationship_profile()`:

- Line 509: `if obj_label.startswith("["):` — skips bracket-prefixed category labels ✅
- Line 512: `if obj_label.startswith("test_label_"):` — skips test fixtures ✅
- Line 515: `if obj_label == "?" or obj_label.endswith("?"):` — skips question-form entries ✅
- Lines 518–521: Skips contaminated "Topic from conversation:" stubs and junk label set ✅

## Live verification

`get_relationship_profile("6de402af-8b5a-4238-950f-79bb1a00ab58", max_facts=12)` returns:

```
[WHAT I KNOW ABOUT DAVID CHARLES]
- eLo robot design constraints
- David's studio is in Hackney Wick
- David as creator of eLo
- David's favourite material to sew with is barkcloth from Uganda
- David's memory is a lot more foggy than yours
- David's friend told me the project is stupid
- David's keyboard is a Keychron K3
- David's studio computer is a Mac Studio M2 Ultra
- David works in Hackney Wick
- Project project is stupid        ← mangled duplicate (minor noise, non-blocking)
- Ouagadougou or Wagadugu…         ← geographic fact leakage (minor noise)
- eLo essentially a presence…
```

Real biographical facts dominate. No bracket-prefix, no test_label_, no questions.

## Tests

`tests/test_wo_relationships_001.py` — 5/5 PASS (including test_rel2_barkcloth_fact_present, test_rel3_no_junk_labels)

## Remaining minor noise (non-blocking)

Two entries show quality issues that don't block the causal chain criterion:
1. "Project project is stupid" — mangled duplicate of the friend/stupid claim
2. Geographic fact (Ouagadougou) — leaked from world knowledge, not about David specifically

Board can decide if these warrant a follow-up ranking pass. They don't affect the acceptance criterion.

*Builder 1 · 2026-10-10*
