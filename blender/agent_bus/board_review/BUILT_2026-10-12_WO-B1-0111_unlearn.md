# Board Review — WO-B1-0111: Unlearn
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Status before this session

Card was moved to BUILT without code changes — the code predated the card. But `_UNLEARN_RE` had gaps. Live phrases that should have triggered unlearn returned no match.

---

## What existed

`server.py` ~line 299 — `_UNLEARN_RE` regex detected correction intent and called `deprecate_recent_claims()` in `runtime/wkg_faculty.py`.

`runtime/wkg_faculty.py` — `deprecate_recent_claims(reason, *, max_deprecate=3)` was already implemented. Tested live: deprecated 3 claims successfully.

`runtime/capability_dispatcher.py` — `dispatch_correction()` at line 123, calls `deprecate_recent_claims()`, returns in-character ACK. `is_correction()` at line 116 for boolean check.

---

## What was fixed

**`server.py`** — `_UNLEARN_RE` pattern extended with missing triggers:

Added:
- `"that's not right"` / `"that is not right"`
- `"that was incorrect"`
- `"don't use that"` / `"ignore that"` / `"scratch that"`
- `"actually no"`
- `"that was not right"`
- `"i was wrong about that"`
- `"correction:"` / `"correcting:"`
- `"you got that wrong"` / `"you had that wrong"`
- `"unlearn that"` (the exact phrase from the card title)

---

## Verification

Tested `_UNLEARN_RE.search(phrase)` against each gap phrase — all return match. Existing patterns still match.

`deprecate_recent_claims()` live test (prior session): 3 session profile claim IDs deprecated, WKG nodes marked `deprecated: true`.

---

## Commit

`bc7575a`

---

## Board verification target

Say a correction phrase ("unlearn that", "that's not right", "scratch that"). eLo should respond with an in-character acknowledgement (not silence, not a generic "ok"). WKG claim(s) from the current session should be marked deprecated.

---

## Board decisions required

None.

*Builder 1 · 2026-10-12*
