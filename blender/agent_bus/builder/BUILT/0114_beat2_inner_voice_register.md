# WO-B1-0114 — Beat 2 Inner Thought: use `_voice_speak_inner`
**Seat:** Builder 1
**Priority:** P0 — follows WO-INNER-THOUGHT-ORDERING; required by David L3 2026-10-05 register rule
**Source:** `blender/agent_bus/builder2/TO_BOARD_2026-10-11_COLLECT-EMIT-SAFETY.md` (Builder 2 relay)
**Date:** 2026-10-11

---

## What

Beat 2 of the inner-thought ordering pipeline (`server.py` ~line 6796) emits the collected pre-thought via `_voice_speak(_it_pre_text)` — the normal register. David L3 2026-10-05 requires inner thoughts to sound audibly different from the main response (lower, slower). The engine is already imported at `server.py:79` as `_voice_speak_inner` (`voice/voice_engine.speak_inner`). Identical pattern is already in use at line 2764.

Beat 1 (the ACK — "Give me a second") stays on `_voice_speak` — it is a normal utterance, not a thought.

## How

One-line change at `server.py:6796`:
```diff
-                        _voice_speak(_it_pre_text)
+                        _voice_speak_inner(_it_pre_text)
```

## Done when

- Line 6796 calls `_voice_speak_inner(_it_pre_text)`
- Beat 1 ACK still calls `_voice_speak(_ack_r2.choice([...]))`
- Lock file created before the edit, deleted after the commit
- Commit filed, card moved to BUILT/, board_review summary filed

## Non-regression

- Beat 1 ACK register unchanged (normal voice)
- Beat 3 system prompt injection unchanged
- `collect()` idempotency and timeout contract untouched (Builder 2 confirmed safe)
