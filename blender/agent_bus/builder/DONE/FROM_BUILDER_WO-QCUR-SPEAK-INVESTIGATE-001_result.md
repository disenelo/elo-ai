# FROM_BUILDER — WO-QCUR-SPEAK-INVESTIGATE-001
**Status:** DONE — investigated, gap confirmed, response gate wired
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a)

---

## Investigation findings

WO concern: "ambient_thought SPEAK path bypasses prompt_builder, voice register, response gate. eLo ambient voice ≠ conversational voice."

### prompt_builder ✅ already wired (prior session)

`server.py:1131` — `_amb_system = build_prompt("…", exec_decision=_amb_exec_decision, ...)`.

`_amb_exec_decision` (lines 1102-1128) includes:
- `intent_source: "self"` — spine knows this is self-initiated
- `tone`, `max_sentences`, `register`, `valence`, `momentum`, `mode`
- `affective_state` — 13-dim from plan
- `self_model_summary` — autobiographical summary + prediction confidence

Voice compression, mischief, and say-it-now directives all fire from `build_prompt()` (WO-COMPRESSION-AS-DEFAULT-001, WO-VOICE-MISCHIEF-001, WO-SAY-IT-NOW-001). ✅

### voice register (CCM street_language) — JUSTIFIED NOT WIRED

CCM `street_language` float fires when David IS actively speaking. On ambient turns, David is not speaking — eLo is initiating. Applying street register to self-initiated thoughts when David hasn't set the tone would be out of character. **Not wiring CCM to ambient exec_decision is the correct choice.**

The `register` field from `_amb_plan` IS included in `_amb_exec_decision` (line 1112) — so if spine's Executive specifies a register, it flows through.

### response gate ❌ GAP — FIXED

`_speak_text` at line 1182 went directly to `_voice_speak()` without calling `elo_response_gate()`. This meant:
- Generic model openers ("Certainly!", "Of course!") could slip through ambient
- Thread contamination phrases could survive
- All 9 gate checks were skipped on self-initiated speech

## Fix

`server.py:1182-1188` — response gate wired on ambient speak text:

```python
# WO-QCUR-SPEAK-INVESTIGATE-001: response gate on ambient speak text
if _speak_text:
    try:
        from runtime.response_gate import elo_response_gate as _amb_gate
        _speak_text = _amb_gate(_speak_text, current_turn_input="…") or _speak_text
    except Exception:
        pass
```

Fail-quiet: if gate import fails, original text passes through unchanged. Gate receives `current_turn_input="…"` (the ambient tick signal — matching what ambient_thought passes to spine).

## Test result

```
1568 passed, 4 pre-existing failures unchanged
```

## Verdict: FIXED

eLo's ambient voice now goes through the same gate as conversational voice. The character quality (compression, mischief) was already present via prompt_builder. Generic openers and contamination are now gated on ambient output.
