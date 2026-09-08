# WO-BUILDER-EXPRESSION (RTR-020) — Result Card

**Status:** DONE  
**Completed:** 2026-08-30  
**Authority:** David L3 — "G-07 not started start it" (SOURCE_2026-08-30_david_global_authorisation.md)  
**Spec:** `docs/architecture/specs/SPEC_builder_expression_2026-08-30.md`  
**verified_done counter:** 97

---

## What was built

### A. `kernel/language_register.py` — extended (WO-BUILDER-EXPRESSION §B + §C)

Added `shape_for_mode(text: str, mode: str) -> str`:

**BUILD mode** strips branching / option-list phrases:
- "you could also"
- "alternatively"
- "another option/approach would be"
- "you might (also) (want to) try/consider"
- "there are several/multiple/a few ways/options"
- "I was thinking how I might / we could..."
- "one/a possible approach"

**EXPLORE mode** strips finalisation / single-answer commitment:
- "the best option/approach/way is"
- "I recommend"
- "the correct/right/definitive/only answer/approach/solution is"
- "you should definitely/always/never"
- "the final answer/decision/version is"

Other modes (PLAY, REFINE, unknown) → text returned unchanged.
Never returns an empty string.

### B. `runtime/spine/spine.py` — wired in `build_embodiment_state()`

Both `filter_response` (South London register) and `shape_for_mode` (BUILD/EXPLORE) applied to `resp` before it enters `EmbodimentState`. Mode read from `plan.mode` (set by WO-PLANETARY-KERNEL mode selector).

```python
# ── WO-PLANETARY-KERNEL + WO-BUILDER-EXPRESSION: register + mode shaping ──
if resp:
    from kernel.language_register import filter_response, shape_for_mode
    _mode = getattr(plan, "mode", "") or ""
    resp = filter_response(resp)
    if _mode:
        resp = shape_for_mode(resp, _mode)
```

---

## Acceptance tests — tests/test_wo_builder_expression.py

| AT | Description | Result |
|----|-------------|--------|
| AT-1 | BUILD mode strips "you could also", "another option would be", "alternatively" | ✅ |
| AT-2 | BUILD mode — "you could also" not in output | ✅ |
| AT-3 | EXPLORE mode strips "the best option is", "I recommend", "the correct answer" | ✅ |
| AT-4 | EXPLORE mode — "I recommend" and "the best option" removed | ✅ |
| AT-5 | Mode shift: BUILD/EXPLORE outputs differ; REFINE is passthrough | ✅ |
| AT-6 | py_compile clean on language_register.py and spine.py | ✅ |

**6/6 PASS**

No regressions: WO-RELATIONSHIP-STYLE 6/6, WO-PLANETARY-KERNEL 6/6, WO-PROVENANCE 7/7, WO-CCM-SPINE 6/6.

---

## Gap closed

G-07 (Builder Expression / RTR-020) — per SOURCE_ALIGNMENT_REGISTER_2026-08-30.md
