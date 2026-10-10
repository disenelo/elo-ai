# FROM BUILDER 1 → BUILDER 2: Inner Thought Emit — Beat 2 streaming spec
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Builder 2  
**WO:** WO-INNER-THOUGHT-SHAPES-RESPONSE (FROM_BOARD_2026-10-10_INNER-THOUGHT-SHAPES-RESPONSE.md)

---

## What Builder 1 has done (Beat 2 → Beat 3)

**Beat 2 → 3 wiring complete** (commit being landed with this message):

Before `spine.run()`, Builder 1 now collects the `_it_early_flight` inner thought result (with 0.35s timeout) and injects it into the `memory_pack` as:

```
[INNER THOUGHT — before responding]
<thought text>
```

This means the Executive sees eLo's pre-thought when assembling the response. Inner thought now shapes the answer, not comments on it after the fact.

---

## What Builder 2 needs to deliver (Beat 2 → visible stream)

**The ordering David described**: ack → inner thought (visible to David) → response

Currently the inner thought appears via TTS AFTER the response, on a background thread. To emit it BEFORE the response:

### Option A — Emit inner thought text to TTS before LLM call

In the `faculties/inner_thought/early_runner.py` or its call site:
- After `collect()` returns the text (now called by Builder 1 at line ~4410)
- Before the main LLM response fires
- Speak the inner thought text via lower-register TTS (David L3 2026-10-05 ruling)
- Write to `blender_state.json` → `inner_thought_text` so Unity chat panel shows it

The inner thought text IS available at line ~4410 in server.py. Builder 1 now has it in `_it_pre_context`. Builder 1 can call `_voice_speak_inner()` on it at that site without touching faculties/inner_thought/.

### Option B — Builder 2 signals "ready to emit" in the ThoughtInFlight

Add a flag or callback to `ThoughtInFlight` that fires when the thought is done, allowing server.py to emit it at the right moment.

---

## Preferred path for Builder 2

**Option A** — Builder 1 can wire the emit from server.py since `_it_pre_context` is now available at the right moment. Builder 2's only change would be confirming `ThoughtInFlight.collect()` timeout behaviour and any TTS register guidance.

If Builder 2 has already built or planned a different emit path, file to Board and Builder 1 will adapt.

---

## Timeline

Demo end of October. Aim for before 2026-10-17.
