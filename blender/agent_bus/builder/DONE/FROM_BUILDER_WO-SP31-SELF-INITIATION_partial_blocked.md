# FROM BUILDER — WO-SP31 Self-Initiation — PARTIAL / BLOCKED

**WO:** WO-SP31-SELF-INITIATION  
**Date:** 2026-08-30  
**Status:** IMPLEMENTATION VERIFIED — ACTIVATION BLOCKED

---

## Verification: 13/13 PASS

```
tests/test_sp31_sp32_self_initiation.py → 13/13 PASS
```

## Significance + relationship context gate confirmed

`runtime/self_initiation.py`:
- `SELF_INIT_THRESHOLD = 0.72` — verbal gate floor (ATTENDING)
- `EXCEPTIONAL_THRESHOLD = 0.90` — verbal gate when not attending
- `is_enabled()` reads `ELO_SELF_INITIATION` env var
- Low-significance (< 0.72) → `ambient_only` (no spine call) ✓
- Hard-quiet and dismiss-quiet windows respected ✓

## Blocker

**`.env` write BLOCKED by auto-mode classifier.**

The standing rule `DO NOT EDIT .env — superseded only by David's direct instruction` is enforced in session. The WO card (Board/LA) is not sufficient to override the classifier — David must state in the conversation:

> **"Set `ELO_SELF_INITIATION=1` in `.env`"**

Once David says that directly, the `.env` edit is one line:

```
ELO_SELF_INITIATION=1
```

## AT-3 status

AT-3: `ELO_SELF_INITIATION=1` confirmed active in runtime config — NOT YET ACTIVE. Flag absent from `.env`. `is_enabled()` returns False.

AT-1, AT-2, AT-4: Pass via SP31/SP32 test suite.

WO remains OPEN until flag is set and AT-3 re-confirmed.

*Builder / Board — 2026-08-30*
