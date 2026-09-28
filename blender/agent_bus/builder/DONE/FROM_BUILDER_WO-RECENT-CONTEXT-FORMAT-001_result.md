# BUILDER RESULT — WO-RECENT-CONTEXT-FORMAT-001: Prior session label fix
Date: 2026-09-11
Status: DONE — verified, music contamination eliminated

---

## Root cause

`memory/state_manager.py:161` (now :162) — `as_context_string()` included the last `session_summaries` entry as:
```
Last exchange: 'i have been working on music all day'
```

The label "Last exchange" caused the LLM to treat a prior session's last turn as the current conversation thread. When David opened a new session with "yo what you been up to", the prompt context said "Last exchange: 'i have been working on music all day'" — LLM generated music-themed responses to an unrelated greeting.

---

## Fix — `memory/state_manager.py`

Changed line 161:
```python
# Before
lines.append(f"Last exchange: '{last['user'][:60]}'")

# After
# WO-RECENT-CONTEXT-FORMAT-001: label as prior session so LLM treats it as
# historical context, not the current conversation thread (prevents cross-session bleed)
lines.append(f"Prior session: '{last['user'][:60]}'")
```

---

## Evidence — 3-turn verification

| Input | Response | Music contamination |
|---|---|---|
| "what should i work on this afternoon" | "send it" | ABSENT ✅ |
| "i keep starting things and not finishing them" | "Holding onto too many ideas, and it's hard to let go of the ones that don't fit." | ABSENT ✅ |
| "what do you think i should build next" | "You've been holding onto many ideas." | ABSENT ✅ |

Before fix: these same inputs produced "I love working on the game, the start menu cinematic is incomplete i love making music, it has always been part of who i am" on T1, T2, T6 of the expressed audit.

---

## DoD

- [x] Root cause identified (`state_manager.py:161` label "Last exchange")
- [x] One-line fix: "Last exchange" → "Prior session"
- [x] 3/3 verification turns: no music contamination in any response
- [x] `state_manager.as_context_string()` now outputs "Prior session:" label (verified via unit check)

---

## Files changed

| File | Change |
|---|---|
| `memory/state_manager.py` | Line 161: label changed from "Last exchange" to "Prior session" |

FREEZE check:
- `runtime/executive.py`: NO ✅
- `prompts/living_presence_spec.txt`: NO ✅

— Builder · 2026-09-11
