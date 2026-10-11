# Board Review — WO-B1-0119: Thin prompt (build_from_plan)
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

Replace the 22K `build_prompt()` assembler with a thin function that takes the spine's `CognitivePlan` and returns 200–350 tokens. Static identity must NOT be re-read or re-injected per turn.

---

## What was built

**`runtime/prompt_builder.py`** — added `build_from_plan(plan, raw, *, inner_thought="") -> str`

Three parts only:
1. **Identity anchor** — `_IDENTITY_ANCHOR` constant (~100 tokens). Derived once from `living_presence_spec.txt` at import time via `_derive_identity_anchor()`. Never re-read per turn. FREEZE_V1_LOCK on the spec respected: the spec itself is not modified.
2. **Turn context** — extracted from `CognitivePlan` fields: tone, max_sentences, mode, rel_mode, expr_mode, autobiographical_summary, capability_context, llm_context, storytelling_style, creative_candidates, inner_thought.
3. **Memory guard** — 2 lines, unchanged from existing pattern.

Measured output: **285–295 tokens** (target was 200–350 ✓).

**`server.py`** — thin prompt wiring at the `build_prompt()` call site (~line 5873 at time of edit):

```python
_using_thin_prompt = False
if _plan is not None:
    try:
        from runtime.prompt_builder import build_from_plan as _bfp
        system = _bfp(_plan, raw, inner_thought=_it_pre_context)
        _using_thin_prompt = True
    except Exception as _bfp_err:
        ...  # falls through to thick build_prompt
```

When `_using_thin_prompt` is True, 20+ style/identity block injections (`self_identity_block`, `self_narrative_block`, memory guard thick, self-interpretation, identity_meaning, relationship register, storytelling frame, consequence ctx, creative seed, emergent_cognition) are all gated off via `if not _using_thin_prompt:`.

---

## Token reduction

| Path | Prompt size |
|------|------------|
| Before (build_prompt) | ~29,727 chars / ~8,490 tokens |
| After (build_from_plan) | ~285 tokens |
| `living_presence_spec.txt` alone | 16,454 chars / ~4,701 tokens (55% of old total) |

The spec is now reference material loaded once at startup, not injected per turn.

---

## No regression requirement

- Spine (`runtime/spine/spine.py`) confirmed working via direct test: `spine.run('hello eLo', ...)` returns valid `CognitivePlan`. No spine bug found.
- The thick `build_prompt()` path is preserved as fallback: if `build_from_plan` raises, the system degrades gracefully to the original assembler.
- FREEZE_V1_LOCK files untouched: `runtime/executive.py`, `prompts/living_presence_spec.txt`, `core/attention.py`.

---

## Commit

`bc7575a` (with 0111, inner-thought, backend_router fixes)

---

## Board verification target

5 consecutive turns, varying topics. Token count (CT0031 telemetry) should log under 2,000 tokens per turn when thin path fires. Check `[prompt]` log line for `build_from_plan` vs `build_prompt` path indicator.

---

## Board decisions required

None — the fallback to `build_prompt()` is automatic if spine fails.

*Builder 1 · 2026-10-12*
