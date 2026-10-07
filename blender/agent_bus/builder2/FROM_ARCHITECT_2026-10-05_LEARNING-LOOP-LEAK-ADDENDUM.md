# ADDENDUM — Learning Loop leak: statement string also surfacing (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-05
**Adds to:** FROM_ARCHITECT_2026-10-05_LEARNING-LOOP-JSON-LEAK.md

---

## Second variant observed

Previous brief covered the full dict leaking as response:
`{'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75', 'statement': 'Partial progress...'}`

New variant — the statement field leaking as plain text:

```
eLo  Partial progress on reflect — check dependencies before next attempt.
```

The lesson's `statement` string is appearing verbatim in eLo's spoken response. This is the same leak, different surface — somewhere the lesson statement is being passed as a string to the response field instead of just the dict.

---

## Guard must catch both

The output guard needs to block:
1. Any response that starts with `{` or contains `'id':` / `'lesson_key':` — full dict
2. Any response that matches `Partial progress on [word] — check dependencies before next attempt` — lesson statement pattern
3. More generally: any response that comes from `learning/` pipeline output rather than `backend_router.py` LLM generation

The lesson object and its fields must never reach any output field. When the guard catches one, it should: discard the lesson output from the response, log it silently, and let the turn proceed with eLo's actual LLM response.
