# FROM_BUILDER — WO-EXPRESSED-VERIFICATION-BATCH-001
**Status:** STRUCTURAL TRACE DONE — live expressed verification requires running server
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)
**Covers:** WO-CCM-PHILOSOPHY-EXPRESSED-001, WO-INNER-CHILD-EXPRESSED-001, WO-STABILITY-LAW-EXPRESSED-001, WO-AFFECTIVE-EXPRESSED-001

---

## WO-CCM-PHILOSOPHY-EXPRESSED-001

**Structural trace:**

1. `faculties/ccm/ccm_enricher.py` — `creative_philosophy` dim fires on persistence/creation signals
2. `runtime/spine/spine.py:1008-1013` — CCM enricher called per turn → `_ccm_context`
3. `server.py:2955` — `ccm_context` field in exec_decision
4. `runtime/prompt_builder.py:581` — **[:4] slice REMOVED this session** — `creative_philosophy` now in standard CCM injection path
5. `runtime/prompt_builder.py:587-592` — explicit injection also active: `"Shared philosophy active: {_creative_phil}. eLo holds these beliefs as resonant ground"`

**Before this session:** `creative_philosophy` was dim 12 — past the `[:4]` slice, never reached prompt (except via the explicit workaround at line 587).
**After this session:** Both the CCM items dump AND the explicit formatted inject will fire.

**Path is verified structural. Expressed test pending live server.**
**Expected trigger input:** "i keep starting things and not finishing" / "i don't know why I can't finish this" → persistence belief should surface.

---

## WO-INNER-CHILD-EXPRESSED-001

**Structural trace:**

1. `runtime/spine/spine.py:428`:
   ```python
   plan.cognitive_mode_inner_child = bool(_curiosity > 0.7 or (_is_play and _is_dream))
   ```
2. `server.py:2962` — `cognitive_mode_inner_child` in exec_decision
3. `runtime/prompt_builder.py:486-488`:
   ```python
   if exec_decision.get("cognitive_mode_inner_child"):
       directive_lines.append("mode: inner-child — wonder first; approach with curiosity, not conclusions")
   ```
4. Curiosity comes from `significance_faculty.py` WO-SP29-CONV-SIGNIFICANCE-001 (DONE) — creative/novel/wonder signals now score higher

**Expected trigger input:** Novel speculative questions ("what if eLo could dream in colour?"), playful creative prompts → curiosity > 0.7 → inner child directive fires.

**Path verified structural. Expressed test pending live server.**

---

## WO-STABILITY-LAW-EXPRESSED-001

**Structural trace:**

1. `runtime/spine/spine.py:394-409` — complexity scoring; P8/P9 gates
   - stability_law_active = True when turn is high-complexity (needs grounding)
   - leaf_on_water_active = True when turn is normal (fluid, adaptive)
2. `server.py:2963-2964` — both fields in exec_decision
3. `runtime/prompt_builder.py:504-507`:
   ```python
   if exec_decision.get("stability_law_active"):
       directive_lines.append("stability: reduce — one line only; compress to single action")
   elif exec_decision.get("leaf_on_water_active"):
       directive_lines.append("stability: leaf-on-water — gentle, present, no more than two thoughts")
   ```

**Expected behaviour:** When David redirects mid-conversation, `leaf_on_water_active` ensures eLo follows without resistance. eLo does not argue or correct — adapts.

**Path verified structural. Expressed test pending live server.**

---

## WO-AFFECTIVE-EXPRESSED-001

**Structural trace:**

AffectiveState is 13-dimensional (`runtime/contracts.py:106`): valence, arousal, safety, novelty, curiosity, confidence, uncertainty, attachment, tension, comfort, agency, significance.

**Where it feeds expressed output:**
- `runtime/prompt_builder.py:634-636`: when `_aff_curiosity > 0.6`, creative seed injection fires
- AffectiveState in exec_decision dict (need to confirm field name)

**Honest finding:** The 13D AffectiveState is built and calculated. But its full injection into the prompt directive block is not as explicit as stability_law or inner_child. The primary consumption is `_aff_curiosity` → creative seed path. Other dims (valence, safety, tension) do not have explicit prompt directives mapped.

**Gap:** AffectiveState → expressed output mapping is incomplete for non-curiosity dims. The structural wiring exists for curiosity; other dims need explicit directive mappings (separate WO needed from Board).

**Expressed test pending live server for curiosity dim specifically.**

---

## Summary

| WO | Structural verdict | Live test status |
|---|---|---|
| WO-CCM-PHILOSOPHY-EXPRESSED-001 | ✅ PATH WIRED ([:4] fix applied + explicit inject) | PENDING LIVE SERVER |
| WO-INNER-CHILD-EXPRESSED-001 | ✅ PATH WIRED (cognitive_mode_inner_child → directive) | PENDING LIVE SERVER |
| WO-STABILITY-LAW-EXPRESSED-001 | ✅ PATH WIRED (stability_law + leaf_on_water → directives) | PENDING LIVE SERVER |
| WO-AFFECTIVE-EXPRESSED-001 | ⚠️ PARTIAL (curiosity dim wired; other 12 dims lack explicit directives) | PENDING LIVE SERVER |

**Honest:** These WOs cannot be fully closed without live expressed output evidence. Structural wiring is verified. Live verification requires server running and David-style test turns.
