# Evidence — WO-INNER-THOUGHTS-001: S2 Phase 0 Bugs 1 + 2

**Date**: 2026-09-25  
**Commit**: `b4d2fe4`  
**File changed**: `server.py` (+34 lines)

---

## Bug 1 — Voice/text conditioning split (Rule G not applied to TTS)

### Root Cause

`_early_tts` closure was speaking and storing raw text in
`_early_tts_sentence[0]` before `enforce_second_person_to_david` (Rule G)
was applied. At the skip-check (~line 6229), the comparison was between
a Rule-G conditioned string and the raw unconditioned string — they never
matched, so the dedup check always failed and sentences were spoken twice.

### Fix

Rule G (`enforce_second_person_to_david`) applied inside `_early_tts`
before `voice_speak()` and before writing to `_early_tts_sentence[0]`.
TTS and chat now share the same conditioned string. Skip-check at ~6229
compares Rule-G strings apples-to-apples.

**Location**: `server.py` ~line 5167

---

## Bug 2 — Ambient voice speech invisible to session log

### Root Cause

`ambient _voice_speak()` was speaking text without writing it to
`blender/ambient_speech.json` or `ConversationTracker`. Spoken ambient
utterances were invisible to the session log — could not be recalled,
deduplicated, or grounded.

### Fix

`_voice_speak()` now writes spoken text to `blender/ambient_speech.json`
and logs it to `ConversationTracker` so no spoken string is invisible
to the session.

**Location**: `server.py` ~line 1284

---

## Status

PASS — both bugs fixed, committed `b4d2fe4`. Board crosscheck required before WO Phase 0 close.
