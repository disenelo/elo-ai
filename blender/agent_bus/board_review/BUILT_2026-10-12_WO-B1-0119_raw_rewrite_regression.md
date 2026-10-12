# Board Review — WO-B1-0119: Raw rewrite regression fix (eLo echoes user message)
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

eLo was echoing David's message back before responding — e.g. "what's the time?" triggered a response starting with "[WEB_SEARCH: ...] ... User asked: what's the time?". The cause was identified as 23 raw rewrite sites in `_process_turn` that overwrite `raw` with both the context block AND David's original message, making the user turn the enriched blob rather than David's words.

Secondary issue: casual/affective statements like "It's getting cold" returned "I don't have that recorded" — likely a side effect of the same pattern corrupting the user message the LLM receives.

---

## What was built

### Root cause

All 23 raw rewrite sites follow the pattern:

```python
raw = f"[CONTEXT_TAG]\n{ctx}\n\nUser asked: {_original_raw}"
```

This makes the LLM's user turn contain both the context block and David's original message. The LLM reads the context block as part of the user role, sometimes echoes "User asked: ..." verbatim, and applies memory guard instructions to context data rather than to David's actual statement.

### Fix

**`server.py`**

Introduced `_system_context_addenda: list[str] = []` and `_raw_augmented: bool = False` near `_original_raw` initialization (line ~2751).

All 23 rewrite sites changed from:
```python
raw = f"[TAG]\n{ctx}\n\nUser asked: {_original_raw}"
```
to:
```python
_system_context_addenda.append(f"[TAG]\n{ctx}")
```

`raw` stays `_original_raw` throughout the entire turn enrichment section. After both system-building branches (`build_from_plan` / `build_prompt`), addenda are injected:
```python
if _system_context_addenda:
    system = system + "\n\n" + "\n\n".join(_system_context_addenda)
```

Guard changes:
- `if raw == _original_raw:` (POP-CULTURE-PROBE gate) → `if not _raw_augmented:`
- Search intent path: `elif not _world_graph_hit and is_search_intent(raw):` → added `not _raw_augmented and` to prevent double web search when P0-REFERENCE already fired and set `_raw_augmented = True`

### Sites fixed (23 total)

FILE_AGENT_RESULT, IMAGE_GEN, MODEL_GEN, ACTION_AGENT, WORLD_KNOWLEDGE,
WEB_SEARCH (P0-REFERENCE, ws_command, search intent), POP-CULTURE-PROBE,
REMINDER_SET, DESKTOP_LIST, PROJECT_LIST, TODO_VAULT, SCREEN_CONTENT,
SCREEN_READ, APP_LIST, PROJECT_LINKS, CHROME_TABS, TRACKER_AGENT,
COMPANY_STATE, CULTURAL_FACT, MUSIC_MEMORY, DECISION_JOURNAL.

---

## What was NOT done

### FACT path misroute secondary fix

The "I don't have that recorded" response for casual statements like "It's getting cold" was investigated. Root cause trace:

- `_cap_classify("It's getting cold")` returns UNKNOWN (not FACT) — the FACT classifier correctly skips it
- The WKG graph lookup fires but returns no entity hits — `_world_graph_hit = False`
- The `is_complex("It's getting cold")` call returns **True** due to `\bit\b` matching "It" in "It's" via the anaphora pattern — so `is_complex()` cannot be used as a reliable guard here

**Working hypothesis:** the echo regression (raw rewrite) was causing the LLM to see enriched context in the user turn, and the `_MEMORY_GUARD` instruction in `build_from_plan` was being misapplied to that context. After the primary fix (raw stays clean), the LLM should see David's exact statement and respond naturally.

Board should verify whether "It's getting cold" still produces "I don't have that recorded" after this fix before requesting a separate FACT guard card.

---

## Verification

Live measurement deferred per standing rule: no tests against live server during active David session.

Board should verify on 3-5 real turns:
1. Web search: "what's the latest on eLo book?" — should NOT echo "[WEB_SEARCH: ...]..." in response
2. Screen read: "what's on my screen?" — should describe screen content, not echo context block
3. Casual statement: "It's getting cold" — should respond naturally, not "I don't have that recorded"
4. Reminder: "remind me to check the tracker" — should confirm reminder, not echo "[REMINDER_SET]..."

---

## Commits

`e7d2805` — WO-B1-0119 raw rewrite → system addenda

---

## Board decisions required

1. **FACT misroute follow-up**: after verifying the primary fix, determine whether "It's getting cold" → "I don't have that recorded" is resolved as a side effect. If not, open a new card for targeted `_MEMORY_GUARD` instruction refinement (cannot use `is_complex()` guard due to false-positive on "It's").

*Builder 1 · 2026-10-12*
