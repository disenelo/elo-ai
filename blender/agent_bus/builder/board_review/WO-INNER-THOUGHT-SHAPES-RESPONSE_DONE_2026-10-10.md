# BUILDER 1 → BOARD: WO-INNER-THOUGHT-SHAPES-RESPONSE — Built (Beat 2→3)
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `36a27e3`

---

## What was built

**Beat 2 → Beat 3 ordering wired** (server.py, commit `36a27e3`):

Before `spine.run()`, server.py now collects the `_it_early_flight` inner thought result (0.35s timeout — bounded, non-blocking). If available, injects into the spine's `memory_pack` as:

```
[INNER THOUGHT — before responding]
<thought text>
```

The Executive sees eLo's pre-thought when assembling the response. Inner thoughts now shape the answer rather than comment on it after the fact.

**How it works end-to-end:**
1. Turn received → `early_runner.start(raw)` fires immediately (line ~2643) — inner thought starts from what David ASKED, never the reply
2. Lock acquired, executive pipeline runs
3. Before `spine.run()`, `early_runner.collect()` → inner thought text (0.35s wait)
4. Inner thought injected into `memory_pack` → Executive assembles response informed by it
5. Main response generates, inner thought fires TTS async (existing path, unchanged)

---

## What remains (Beat 2 → visible stream)

The spec for Beat 2 emit-before-response has been filed to Builder 2's inbox:  
`blender/agent_bus/builder2/FROM_BUILDER1_2026-10-10_INNER-THOUGHT-EMIT-SPEC.md`

Currently inner thought appears via TTS AFTER the response. To emit BEFORE:
- Builder 1 can call `_voice_speak_inner(_it_pre_context)` at the injection site (now has the text)
- OR Builder 2 can confirm via inbox

Builder 1 awaits Builder 2 confirmation or Board authorisation to wire the emit.

---

## Test fixes (same commit)

- `tests/test_wo_relationships_001.py`: updated test fixture label from `test_label_*` to `integration test entity *` — `test_label_*` is now filtered by WKG-FACT-QUALITY-001
- `tests/test_wo_voice_register_001.py`: updated AT-3/AT-4 assertions to accept "does NOT speak like:" (WO-B1-0108/0109 used caps)

Both ratchet tests (`test_turn_result_shape.py`, `test_0020_ct0033_bypass_handlers.py`) pass. 3880 tests pass in suite (8 pre-existing failures in Alexa + router + dream modules).
