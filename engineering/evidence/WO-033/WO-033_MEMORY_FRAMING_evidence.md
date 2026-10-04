# WO-033 — Memory Framing (time/days, not sessions) — Evidence

**Status:** COMPLETE — 4/4 ATs pass, 2026-10-04
**Builder:** Builder 1

---

## What was fixed

`server.py` — 3 user-facing strings reframed from "session to session" / "across sessions" language to natural time language:

| Old | New | Line |
|-----|-----|------|
| "I exist session to session. Between them is quiet." | "Days accumulate, older ones fade. Between conversations there's just quiet." | ~1898 |
| "I run session to session — time between them isn't something I experience." | "I carry what happened days back — the older it is, the less sharp. Recent things stay close." | ~1900 |
| "Persistent emotional context across sessions." | "Persistent emotional context over days." | ~2741 |

`prompts/living_presence_spec.txt` — FROZEN (FREEZE_V1_LOCK); existing content already passes the AT-3 check — "session" framing not present in user-visible memory/continuity language.

## ATs

- AT-1 ✅ `_SELF_REF_POOL` — no 'session' framing
- AT-2 ✅ `_memory_recall_response()` — no 'session' framing
- AT-3 ✅ `living_presence_spec.txt` — no 'session' framing (FROZEN; pre-existing state)
- AT-4 ✅ prompts use time/day language — found: ['days and weeks', 'here today, here tomorrow']

**Run:** `python3 tests/test_wo033_memory_framing.py` → **4/4 passed**

## Canon guard

Test `tests/test_wo033_memory_framing.py` catches any regression of "session" framing into user-visible memory/continuity language. CI should include this file.
