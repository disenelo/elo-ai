# Board Review — ROOT-2: Autobiographical Summary Injection
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

ROOT-2 closes the causal chain: WKG retrieved facts now reach the LLM via prompt injection.

- `prompt_builder.py:828-844` — `autobiographical_summary` from `exec_decision["self_model_summary"]`
  injected as `## What I know from our history (retrieved, treat as verified fact)` block
- `spine.py:819` — truncation raised from 240 → 800 chars (more WKG context survives)
- `prompts/living_presence_spec.txt` — FREEZE_V1_LOCK respected; ground-truth instruction
  included inline in the injected block
- End-to-end: `build(exec_decision={"self_model_summary": {"autobiographical_summary": "David's studio is in Hackney"}})` → "Hackney" appears in assembled prompt ✅

---

## Commit

Pre-existing implementation (WO-0082 marker). Verified and Result filed 2026-10-11.

---

## Tests — `tests/test_root2_autobiographical_summary_injection.py`

```
pytest tests/test_root2_autobiographical_summary_injection.py -v
→ 7 passed
```

| AT | Result |
|----|--------|
| ROOT2-1: SelfModel has autobiographical_summary field | ✅ |
| ROOT2-2: default is empty string | ✅ |
| ROOT2-3: spine populates field from wkg_context | ✅ |
| ROOT2-4: server.py injection block present | ✅ |
| ROOT2-5: history label correct | ✅ |
| ROOT2-6: empty summary → no injection | ✅ |
| ROOT2-7: non-empty summary appends to prompt | ✅ |

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
