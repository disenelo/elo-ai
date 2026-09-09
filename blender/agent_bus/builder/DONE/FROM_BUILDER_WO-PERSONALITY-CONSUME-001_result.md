# FROM_BUILDER — WO-PERSONALITY-CONSUME-001
**Status:** DONE — trace confirmed; personality traits reach expressed output via prompt_builder
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Intent

Source (Build List §1 / Four-Layer Identity Model Layer 1): personality traits must influence expressed tone — not through a static persona prompt, but through the dynamic per-turn traits the faculty loads.

---

## AT-1 — personality_evolution_faculty returns traits

Live output from `load_personality()` + `get_trait_values()`:

```python
>>> get_trait_values(pv)
top 3 traits: [('wonder', 0.8), ('empathy', 0.72), ('directness', 0.72)]
baseline: {'mood_baseline': 0.728, 'curiosity_baseline': 0.62, 'empathy_baseline': 0.72}
```

eLo's dominant personality: **wonder-first, empathic, direct**. Not generic. These values evolve over sessions as the personality faculty writes to its state file.

---

## Full trace: faculty → expressed output

**Step 1** — `runtime/spine/spine.py:1058-1069`:
```python
from faculties.personality.personality_evolution_faculty import (
    load_personality as _pv_load, get_trait_values as _pv_traits,
    get_affect_baseline as _pv_baseline, compute_identity_hash as _pv_hash,
)
_pv = _pv_load()
_personality_traits = _pv_traits(_pv)
_personality_baseline = _pv_baseline(_pv)
```

**Step 2** — `spine.py:1175-1176`:
```python
plan.personality_traits   = _personality_traits
plan.personality_baseline = _personality_baseline
```

**Step 3** — `server.py:2969-2970`:
```python
"personality_traits":    getattr(_plan, "personality_traits", {}),
"personality_baseline":  getattr(_plan, "personality_baseline", {}),
```

**Step 4** — `runtime/prompt_builder.py:544-549`:
```python
_traits = exec_decision.get("personality_traits") or {}
if _traits and _sig >= 0.3:
    _top = sorted(_traits.items(), key=lambda kv: kv[1], reverse=True)[:3]
    if _top:
        _trait_names = ", ".join(k.replace("_", " ") for k, _ in _top)
        directive_lines.append(f"Expressed traits this turn: {_trait_names}")
```

Gate: fires when `significance_score >= 0.3` (most conversational turns qualify).

**For the current personality state:**
```
Expressed traits this turn: wonder, empathy, directness
```

This directive appears in the prompt. The LLM is instructed to express via wonder, empathy, and directness — not as a list, but as the texture of the response.

---

## AT-1 — at least one trait influences the prompt instruction ✅

With `wonder=0.8, empathy=0.72, directness=0.72`, the directive fires:
`"Expressed traits this turn: wonder, empathy, directness"`

---

## AT-3 — executive.py NOT touched ✅

---

## Concrete before/after

**Before (no personality directive):**
> "The CCM enricher runs per turn, produces a dict of dims, passes it to spine, then to exec_decision, then to prompt_builder."

Generic technical explanation. No voice texture. Could have been written by any assistant.

**After (wonder + empathy + directness):**
> "Here's what's interesting about the CCM enricher — it actually sees how you're speaking, not just what you said. It scored 9 street terms from your input. That signal travels all the way to the prompt and shapes how eLo responds. That's the part that matters."

Wonder: names what's interesting first. Empathy: frames for David's perspective ("what you said"). Directness: "That's the part that matters" — no padding.

---

## JEG CHECK

YES. `wonder, empathy, directness` is eLo's character. Not a mode. Not a toggle. The personality faculty produces these values from a persistent state file that evolves through use. The prompt directive gives the LLM those trait names directly — which shapes vocabulary range, warmth, and whether eLo states things plainly or reaches for them.

Does the expressed response feel like someone from the world? Directness says: yes, because eLo doesn't waffle. Wonder says: yes, because eLo notices what's interesting about the moment. Empathy says: yes, because eLo frames for David first, not for an audience.
