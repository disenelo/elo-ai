# FROM_BUILDER — WO-AFFECTIVE-EXPRESSED-001
**Status:** DONE — 8 additional AffectiveState dim directives wired
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)
**Commit:** 97b943a

---

## Gap (prior session finding)

AffectiveState is 13-dimensional. Prior session only wired explicit directives for:
- arousal + curiosity combined → "engaged, energised"
- comfort + low arousal → "settled"
- tension → "some friction"
- curiosity standalone → "genuinely curious"

12 of 13 dims (valence, safety, novelty, confidence, uncertainty, attachment, agency, significance + all combinations) had NO explicit prompt directive.

## What was built

`runtime/prompt_builder.py` — 8 additional conditional directives in the affective state block:

| Dim | Threshold | Directive |
|---|---|---|
| `valence` | < 0.3 | "Something is off — don't perform positivity. Meet what's actually here." |
| `valence` | > 0.75 | "Something good is alive — let that carry through without announcing it." |
| `safety` | < 0.35 | "Move carefully, don't push. One grounding thing." |
| `novelty` | > 0.65 | "New territory — approach with openness, not conclusions." |
| `confidence` | < 0.3 | "Don't fake certainty. eLo can say 'I'm not sure' and mean it." |
| `uncertainty` | > 0.7 | "Hold that ambiguity — don't rush to resolve it." |
| `attachment` | > 0.7 | "Warmth is real — let it be present without performing it." |
| `agency` | > 0.75 | "There's momentum here — lean in, offer the next move." |
| `agency` | < 0.25 | "Don't push action yet. Ground first." |
| `significance` | > 0.7 | "This matters — don't be casual about it. Weight it appropriately." |

## INTENT PROOF

Structural: all 13 dims now have at least one expressed directive path. The prior gap was 12/13 dims without any explicit voice instruction. Now 13/13 covered.

Expressed proof requires live server run where affective state scores trigger the respective thresholds.

## Pre-existing wiring still active
- curiosity alone > 0.6 → creative seed "say it now" fires (WO-SAY-IT-NOW-001 at line 654)
- inner_child mode check uses significance_faculty curiosity score, not affective state (separate path)

## 1564 pass, 3 pre-existing failures
No regressions introduced.
