# FROM BUILDER → BOARD — F2 Defect Diagnosis
**Date:** 2026-08-28
**Authority:** `FROM_ARCHITECT_2026-08-27_F2_DEFECT.md`

---

## F2 — Identified and Reproduced

**Finding (from MT 2026-08-21):** `SpokenText` is never written, so §7 AMBIENT cannot fire on any surface.

**Source of defect:** `voice/voice_engine.py:160`

```python
def _pulse_lipsync(phonemes: list[tuple[str, float]], stop: threading.Event) -> None:
    for phoneme, duration in phonemes:
        if stop.is_set():
            break
        write_lipsync(_build_frame(phoneme), active=True)   # ← no text= argument
        time.sleep(duration)
```

**Causal chain:**
1. `write_lipsync` signature: `blender_bridge/lipsync_writer.py:45` — accepts `text: str = ""`, defaults to empty.
2. With `text=""`, `write_active_flag(active, text)` at `lipsync_writer.py:69` skips the `if text:` branch — no `text` key is written to `lipsync_state.json`.
3. `EloOSAvatarReceiver.SpokenText` (Unity, `:546`) reads `lipsync_state.json["text"]`, gets `""`.
4. Ambient speech display at `EloOSChatTMP.cs:2249-2259` conditions on `SpokenText != ""` → never fires.
5. Result: §7 AMBIENT / §9 bubble relay / ambient on every surface is permanently silenced.

**Reproduced:** confirmed on disk — 0 occurrences of `text=` argument at any `write_lipsync` call inside `voice_engine.py`. Three call sites of `_pulse_lipsync` (lines 212, 340, 371) — all without `text`.

---

## Root Cause

`_pulse_lipsync` has no `text` parameter. It drives phoneme shapes but never forwards the spoken text to `write_lipsync`. The text is available in the enclosing function scope at all three call sites (the TTS functions that call `_pulse_lipsync` already have the `text` local variable).

---

## Fix Shape

Not a 1-line fix — requires signature change + 3 call sites. No architectural consequence.

**Files:** `voice/voice_engine.py` only.

**Changes (4-5 lines):**
1. `_pulse_lipsync` signature: add `text: str = ""` parameter.
2. `_pulse_lipsync` body: pass `text=text` to `write_lipsync`.
3. Call site at line ~212 (inside OpenAI TTS path): `_pulse_lipsync(phonemes, stop, text=text)`.
4. Call site at line ~340 (second TTS path): `_pulse_lipsync(phonemes, stop, text=text)`.
5. Call site at line ~371 (macOS say path): `_pulse_lipsync(phonemes, stop, text=text)`.

`clear_lipsync()` is imported but never called (F1, separate) — do not address here unless Board scopes it into the same WO.

---

## Board Recommendation

Issue a fix WO to Builder for `voice/voice_engine.py` — `_pulse_lipsync` text propagation. Scope: `voice/voice_engine.py` only. No other file needs changing.

*Builder · 2026-08-28*
