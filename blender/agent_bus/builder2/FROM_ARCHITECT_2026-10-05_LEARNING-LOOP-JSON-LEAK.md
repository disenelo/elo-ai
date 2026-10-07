# CRITICAL — Learning Loop lesson JSON leaking into eLo's spoken response (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-05
**Priority:** P0 — Kickstarter critical
**Source:** David's debug session log — live 2026-10-05

---

## Observed (verbatim from log)

```
eLo  {'id': 'L-20261005151905', 'lesson_key': '7d20ac65e9f2aa75', 'statement': 'Partial progress on witness — check dependencies before next attempt.', 'evidence': [], 'scope': 'behaviour', 'cause': 'partial', 'strength': 0.3, 'delta': 'partial', 'status': 'candidate', 'first_seen': '2026-10-05T15:19:05+00:00', 'last_seen': '2026-10-05T15:19:05+00:00', 'promoted_at': None, 'retired_at': None, 'reason':
```

A raw Python dict — a Learning Loop lesson record — is appearing in eLo's spoken/chat response field. This is going to TTS and the chat display. David hears or reads a raw data structure.

---

## Root cause — find one of these

The lesson record is reaching the response field via one of:

1. The lesson object being passed as a string to `elo_final` or `response` instead of being handled separately
2. The lesson pipeline writing to the response field instead of a lessons store
3. A `str()` or `repr()` call on the lesson object somewhere in the output assembly path
4. A logging or debug statement that feeds into the output buffer

---

## Fix

The lesson record must NEVER appear in conversation output. It must not appear in:
- `response` field
- `inner_thought` field
- `bubbles` field
- Any field that reaches Unity, TTS, or the chat log

The Learning Loop processes lessons silently in the background. Its output is stored to the lessons store (`engineering/cap_wos/` or wherever the learning pipeline writes). Nothing from the lesson object enters any output field.

Add an output guard: before `response` or `elo_final` is assembled, check for dict-like or JSON-like content in the string. If it starts with `{` or contains `'id':` / `'lesson_key':` — reject and regenerate. Do not pass raw data structures to output.

---

## Evidence
One session where the learning pipeline runs silently — no lesson JSON appears in any output field, David sees no raw data structures in conversation.
