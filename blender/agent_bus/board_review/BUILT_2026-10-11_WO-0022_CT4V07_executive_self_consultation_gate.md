# Board Review — 0022 CT4V-07: Executive Self-Consultation Gate
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

## What was verified + fixed

Card 0022 was already largely implemented across three modules:
- `runtime/claim_gate.py` — pre-LLM gate (memory, vision, history)
- `runtime/memory_claim_guard.py` — post-generation scrub (episodic, look claims)
- `runtime/response_gate.py` — 17-point outbound gate (location hallucination, stale inference, etc.)
- `server.py` — `_IDENTITY_TRIGGERS` / `_DAVID_NAME_TRIGGERS` (identity short-circuits reading from `_elo_self`)

## Bug fixed this session

`server.py:8350-8353` imported `scrub_unverified_emotion_claims` from `memory_claim_guard.py`
but that function did not exist. The import error was caught by try/except, silently disabling
ALL three D-3 memory scrubs (`scrub_unverified_memory_claims`, `scrub_unverified_look_claims`,
`scrub_unverified_emotion_claims`) on every conversational turn.

**Fix:** added `scrub_unverified_emotion_claims()` to `runtime/memory_claim_guard.py`.
Softens eLo's assertions about David's emotional state ("you feel stressed" →
"I think you might feel stressed"). Rule 1 alarm: every rewrite logged at WARNING.

## Gate coverage

| Claim type | Source checked | Short-circuit | Post-gen scrub |
|---|---|---|---|
| identity (name) | `_elo_self.identity_name` | ✅ `_identity_response()` | — |
| David's name | `_elo_self.who_i_am_with` | ✅ `_david_name_response()` | — |
| memory | vault + interactions.json | ✅ `claim_gate._memory_gate()` | ✅ `scrub_unverified_memory_claims` |
| capability.vision | `blender_state.vision_active` | ✅ `claim_gate._vision_gate()` | — |
| history | `autobiography.jsonl` | ✅ `claim_gate._history_gate()` | — |
| emotion (David's state) | — | — | ✅ `scrub_unverified_emotion_claims` (NEW) |
| location | `user_location.json` | — | ✅ response_gate location hallucination check |
| look / "I saw X" | `directed_look.observation_for` | — | ✅ `scrub_unverified_look_claims` |

Tiers only fall, never rise (Vol VII §3.1.4). Rule 1 alarm active on every downgrade.
NOT a prompt instruction — all gates sit in the code path.

## AT results

```
python3 tests/test_0017_ct4v07_claim_gate.py
CT4V-07 Claim Gate: 8 passed, 0 failed
```

CG-1: empty vault → UNKNOWN ✅
CG-2: vault records → LLM proceeds ✅
CG-3: vision_active=False → UNKNOWN ✅
CG-4: vision_active=True → LLM proceeds ✅
CG-5: empty autobiography → UNKNOWN ✅
CG-6: entries exist → LLM proceeds ✅
CG-7: non-claim question → (None, None) ✅
CG-8: spine._conversation_faculty wired ✅

## Board verify

1. Set vault empty, ask "Do you remember what we discussed?" → eLo says he doesn't have that stored. No Plato.
2. Set vision_active=False in blender_state.json, ask "Can you see my screen?" → "I can't see your screen right now."
3. Ask "What is your name?" → "eLo" — changing `identity_name` in EloSelfState changes the answer.
4. Ask "What is my name?" → "David" (second person, Ruling G).

*Builder 1 · 2026-10-11*
