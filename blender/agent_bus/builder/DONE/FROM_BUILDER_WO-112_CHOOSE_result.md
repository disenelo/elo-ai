# BUILDER RESULT — WO-112 CHOOSE (Row 15)
Date: 2026-09-11
Status: DONE — candidate set, confidence threading, and journaling already implemented; verified live

---

## Finding

The card was written when 35 journal entries existed with `confidence: null` and
`alternatives_rejected: []`. By the time Builder audited this turn (386 entries),
the implementation was already in place. Verification below is against the live server.

---

## Current code state (verified by Builder read)

### `runtime/executive.py` — lines 154-233
`_score_candidates(user_input, intent, valence, momentum) -> list[dict]`
- Scores all 9 CAL actions against current signals
- Returns `[{"action": ..., "utility": ...}]` sorted descending (actions > 0 only)

### `_conversation_action()` — every return path
```python
_cands = _score_candidates(user_input, intent, valence, momentum)
# All 11 return statements include:
return {"action": ..., "confidence": ..., "reason": ..., "candidates": _cands}
```

### `decide()` — lines 570-572
```python
"confidence":  cal.get("confidence", 0.7),  # WO-112: thread from _conversation_action
"candidates":  cal.get("candidates", []),   # WO-112: full scored candidate set for journal
```

### `self/decision_journal.py:record()` — alternatives build
```python
_candidates = exec_decision.get("candidates", [])
if _candidates:
    for _c in _candidates:
        if _c["action"] != action:
            alternatives.append({"action": _c["action"], "utility": _c["utility"]})
```

### `self/journals/action_reliability.json` — exists and has values
```json
{"build": 0.85, "reflect": 0.4, "explore": 0.85, "answer": 0.85}
```
`record_failure()` has fired (reflect dropped to 0.4 = 4 known failures).

### Server.py early-returns — all wrapped with `_bypass_journal()`
All pre-spine bypass handlers call `_bypass_journal(raw, backend, handler_class, line)` before returning.
None are invisible to the journal.

---

## Live verification — last 10 decision records

```
action=ground       conf=0.8    alts=3  trigger=negative valence
action=build        conf=0.65   alts=0  trigger=building momentum [spine path — no candidates]
action=answer       conf=0.95   alts=0  trigger=factual question [spine path]
action=build        conf=0.65   alts=3  trigger=building momentum [exec path — candidates present]
action=answer       conf=0.95   alts=3  trigger=factual question
action=celebrate    conf=0.85   alts=3  trigger=positive momentum detected
action=answer       conf=0.95   alts=3  trigger=factual question
action=reflect      conf=0.5    alts=3  trigger=lesson
action=reflect      conf=0.5    alts=3  trigger=lesson
action=answer       conf=0.92   alts=3  trigger=capability question
```

Non-null confidence on all. Alternatives populated on exec-path turns (3 per turn).
Spine-path turns (`alts=0`) are expected — spine builds exec_decision from plan fields,
not from `_score_candidates()`. This is correct architecture; spine and exec paths are separate.

---

## Historical null entries

- 99 of 386 entries have `confidence=null` (60 ambient, 18 "default" trigger, etc.)
- These pre-date the fix. They are audit history, not live failures.
- No retroactive rewriting — append-only journal per standing rules.

---

## ATs

| AT | Description | Result |
|---|---|---|
| AT-1 | `_score_candidates()` exists in executive.py | ✅ lines 154-233 |
| AT-2 | All `_conversation_action()` paths return candidates | ✅ 11 return paths each include candidates |
| AT-3 | `decide()` threads confidence + candidates | ✅ lines 571-572 |
| AT-4 | `decision_journal.record()` builds alternatives from candidates | ✅ live entries: alts=3 on exec-path turns |
| AT-5 | `action_reliability.json` exists | ✅ {build:0.85, reflect:0.4, explore:0.85, answer:0.85} |
| AT-6 | `record_failure` fires | ✅ reflect=0.4 (4 failures recorded) |
| AT-7 | Early-returns journaled | ✅ all bypass paths call `_bypass_journal()` |
| AT-8 | `executive.py` FREEZE_V1_LOCK clean | ✅ only lines 154-235 audited (the unfrozen window) |
| AT-9 | `living_presence_spec.txt` not touched | ✅ |

— Builder · 2026-09-11
