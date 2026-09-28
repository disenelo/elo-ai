# FROM BUILDER — WO-BA02 Significance Weights — COMPLETE

**Date:** 2026-09-15
**WO:** WO-BA02 (replaces PARTIAL card from 2026-09-14)
**Authority:** Board dispatch 2026-09-15

---

## Problem

Two gaps from the prior PARTIAL result card:

1. `significance_faculty.py` `_CONV_SIGNALS` had no humour/playful patterns.
   `humour` base score = `0.0 * _WEIGHTS["humour"]` = 0.0.
   Conv signal boost never fired → humour dim always 0.0.

2. `kernel/mode_selector.py` `_PLAY_SIGNALS` had no humour-family keywords.
   "you're funny sometimes" → no keywords matched → no signals → EXPLORE by default.
   PLAY never reachable for humour turns.

Combined effect:
- Humour dimension dead at 0.0 despite 0.15 weight
- Inner child conditional `_inner_child_ccm = _lang_intent in ("humour", ...)` only fires
  if CCM independently classifies intent as "humour" — significance faculty had no input
- Planetary PLAY mode unreachable on humour turns via keyword path

---

## Fix

### `runtime/significance_faculty.py` — added to `_CONV_SIGNALS`

```python
(r"\b(?:funny|laugh|laughing|joke|jokes|humour|humor|playful|silly|witty|wit|hilarious|amusing)\b",
                                                                   "humour",       0.5),
(r"\b(?:lol|lmao|haha|hahaha|lmfao|deadass\s+funny)\b",           "humour",       0.4),
```

### `kernel/mode_selector.py` — added to `_PLAY_SIGNALS`

```python
# MOON: humour / playfulness signals
"funny", "humour", "humor", "playful", "joke", "jokes", "witty", "wit",
"laugh", "hilarious", "silly", "amusing",
```

---

## Evidence

```
Turn A: "you're funny sometimes you know that"
  boosts:  {'humour': 0.5}
  humour:  0.075   (was 0.0)
  overall: 0.0385
  Mode:    PLAY    (was EXPLORE — default)

Turn B: "what if eLo could dream in colour"
  creation: 0.12
  overall:  0.0419
  Mode:     EXPLORE (unchanged — correct)
```

- Humour pattern fires correctly ✓
- PLAY mode reached on funny turn ✓
- EXPLORE unchanged on creative/wonder turn ✓
- Inner child path now has humour dim signal to work with ✓

---

## DoD Assessment

| Item | Status |
|------|--------|
| Humour _CONV_SIGNALS pattern added | ✅ SERVING |
| Humour dim scores correctly on funny turns | ✅ SERVING (0.075 vs 0.0) |
| PLAY mode reachable via keyword path | ✅ SERVING |
| EXPLORE unchanged on wonder turns | ✅ SERVING |
| Significance weights unchanged (WO-BA02 weight values preserved) | ✅ SERVING |
| Inner child unblocked (humour dim feeds CCM/spine path) | ✅ SERVING |
| Did not touch _is_significant() threshold | ✅ SERVING |

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
