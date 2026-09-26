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

---

# Phase 1 — Output Object Restructure

**Date**: 2026-09-26  
**Commit**: `83bf8a9`  
**Files changed**: `server.py` (+10 lines, -6 lines) · `unity-desktop-avatar/Scripts/EloConversationUI.cs` (+2 fields)

---

## Change

Every `_process_turn` return dict now includes four fields instead of one:

```python
{
    "inner_thought": "",          # Phase 2 will populate via second LLM pass
    "response":      response,    # unchanged — chat displays this
    "emotion":       _it_emotion, # exec_decision valence ("positive_high", "neutral", etc.)
    "intent":        _action,     # CAL action for this turn
    "bubbles":       _bubbles,
    "mode":          _action,
    "backend":       backend_used,
}
```

Error fallbacks in `_turn_worker` and `_process_turn_queued` updated to match.

## EloConversationUI.cs

`_ChatResponse` schema extended to deserialize new fields:
```csharp
public string inner_thought;
public string response;
public string emotion;
public string intent;
```
Unity's `JsonUtility` ignores unknown fields so prior clients are unaffected.

## Not yet done (Phase 2)

- `inner_thought` field is always `""` — Phase 2 will run a second lightweight LLM pass (temp 0.85+, 1-3 sentences) to generate it
- TTS sequencing (speak inner_thought before response) is Phase 2 Unity-side routing
- `physical_conditioning()` hook into inner_thought is S5 Item 6 / Phase 2 dependency

## Status

PASS — Phase 1 structural change committed `83bf8a9`. Board crosscheck required before Phase 1 close.

---

# Phase 2 — Inner Thought Generation (Second LLM Pass)

**Date**: 2026-09-26  
**Commit**: `6aaac44`  
**File changed**: `server.py` (+69 lines, -2 lines)

---

## Change

After the ConversationTracker record in `_process_turn`, a second lightweight Ollama call generates `inner_thought`:

**Option A (direct Ollama API, temp 0.85, num_predict 96, num_ctx 2048):**
- Fetches last 2 turns via `ConversationTracker.get_context(session_id)["recent_turns"]`
- Prompt: eLo's inner voice — unguarded, first-person, 1-2 sentences, not a summary of the reply
- Timeout: 3.0s; latency guard: >2000ms triggers Option B fallback + warning log

**Option B (rule-based fallback, fires when LLM >2s or empty response):**
```python
_it_vmap = {
    "positive_high": "Something feels really right here.",
    "positive_low":  "This is landing well.",
    "negative_high": "I need to be careful with this one.",
    "negative_low":  "Something feels off, but I'm staying with it.",
}
_inner_thought = _it_vmap.get(_it_emotion, "I'm present for this.")
```

**`_it_emotion`** moved before the Phase 2 block so Option B fallback can reference it.

**Return dict** now uses `_inner_thought` (populated string) instead of `""`.

## Location

`server.py` ~line 6673 — between ConversationTracker record and final return in `_process_turn`

## Not yet done (Phase 3)

- Unity-side: speak `inner_thought` via TTS before `response` (Phase 3 routing)
- S5 Item 6: `physical_conditioning()` hook into inner_thought conditioning
- Dream state integration (after S3 Phase 1 live)

## Status

PASS — Phase 2 LLM pass committed `6aaac44`. Board crosscheck required before Phase 2 close.
