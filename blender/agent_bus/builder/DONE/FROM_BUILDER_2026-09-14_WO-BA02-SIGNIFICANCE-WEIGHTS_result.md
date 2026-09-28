# FROM BUILDER → BOARD — WO-BA02: SP-29 Significance Weights Set
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-BA02-SIGNIFICANCE-WEIGHTS-SET.md
**Authority:** Board derivation — David L3 standing intent

---

## Change Applied

`runtime/significance_faculty.py` — `_WEIGHTS` dict replaced (uniform 0.1 → source-derived):

```python
_WEIGHTS = {
    "learning":      0.20,   # [SPEC ELO_OS_AI_SOURCE] LEARN = first layer.
    "creation":      0.20,   # [SPEC FOUR-LAYER MODEL] CREATE = second major layer.
    "relationship":  0.20,   # [SPEC ELO_OS_AI_SOURCE] BE layer.
    "humour":        0.15,   # [SPEC natal chart] Moon Aries = THE SPARK.
    "novelty":       0.15,   # [SPEC ELO_OS_AI_SOURCE] Venus Aquarius = THE EXPLORER.
    "logic":         0.10,   # [SPEC natal chart] Mercury Capricorn = THE ARCHITECT.
    "continuity":    0.10,   # [SPEC FOUR-LAYER] LEARN layer — threading.
    "presence":      0.10,   # [SPEC LIVE architecture]
    "embodiment":    0.10,   # [SPEC LIVE architecture]
    "system_change": 0.05,   # [ESTIMATE] secondary
    "reward":        0.05,   # [ESTIMATE] secondary
    "safety":        0.05,   # [ESTIMATE] floor
    "efficiency":    0.05,   # [ESTIMATE] lowest
}
```

Docstring updated: removed `[ESTIMATE]` from header, replaced with WO-BA02 source attribution.

---

## Evidence (real Python — same server environment)

**`_score_text_signals()` results per turn:**

| Turn | Input | Signals fired | Boosted dimension |
|---|---|---|---|
| A (curiosity) | "what do you think happens when we dream" | `dream` matches | creation=0.5 |
| B (humour) | "you are funny sometimes you know that" | (none) | — |
| C (build) | "ok lets fix the CCM enricher" | (none) | — |

**Significance scores with new weights:**

| Turn | overall | learning | creation | relationship | humour |
|---|---|---|---|---|---|
| A | 0.0404 | 0.1000 | 0.1000 | 0.1000 | 0.0 |
| B | 0.0327 | 0.1000 | 0.0000 | 0.1000 | 0.0 |
| C | 0.0327 | 0.1000 | 0.0000 | 0.1000 | 0.0 |

**Impact vs. old uniform weights (all 0.10):**
- learning/relationship/creation baselines: 0.05 → 0.10 (doubled)
- humour: 0.0 → 0.0 (no change — signal not fired for these inputs; weight applies only when signal fires)
- novelty: 0.0 → 0.0 (no world delta for these turns)

**Live turn results (mode):**
```
TURN A (curiosity "what do you think happens when we dream"): mode=answer, backend=ollama(stream)
TURN B (humour "you are funny sometimes you know that"): mode=reflect, backend=ollama(stream)
TURN C (build "ok lets fix the CCM enricher"): mode=build, backend=ollama(stream)  ← CORRECT
```

---

## Gap — Board ruling requested

**Turn B evidence cannot be produced as specified.**

WO requires: `humour` + `relationship` elevated on Turn B. `humour` weight is 0.15 but base rate is hardcoded `0.0 * _WEIGHTS["humour"]` in `compute_significance()` and no `_CONV_SIGNALS` pattern matches "funny", "humour", "joke", "laugh". Weight change takes effect only when signal fires.

WO constraint: "Do NOT touch the `_CONV_SIGNALS` boosts."

**Ruling requested:** Authorize adding `r"\b(?:funny|joke|laugh|humour|humor)\b"` → `("humour", 0.5)` to `_CONV_SIGNALS` so Turn B evidence is producible. Otherwise Turn B evidence is structurally unachievable with the current constraint.

**Mode selection gap:** Significance `overall` scores (0.033-0.040) are too low to influence mode selection. Mode is primarily driven by Executive intent classification. The weight change correctly encodes eLo's character but requires overall score calibration before affecting mode routing.

---

## DoD Status

- [x] _WEIGHTS set from source derivation (not uniform) ✓
- [x] Top four `[ESTIMATE]` tags replaced with `[SPEC]` + source citations ✓
- [x] Turn A: creation + learning elevated ✓
- [x] Turn C: mode=BUILD (correct) ✓
- [ ] Turn B: humour elevated — **BLOCKED** (needs _CONV_SIGNALS authorization)
- [ ] Mode differentiation (EXPLORE/PLAY/BUILD) — **BLOCKED** (overall significance too low)

**VERDICT: PARTIAL — weights set correctly; Turn B evidence and mode routing require Board ruling**

---

*Builder · 2026-09-14*
