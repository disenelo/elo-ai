# FROM ARCHITECT → RECORD — WO-FIX-112-AMBIENT Architectural Close
**Date:** 2026-08-28
**Authority:** Board / Lead Architect — source verification + live test
**Commit:** 6d06bc2

---

## WO-FIX-112-AMBIENT ✅ ARCHITECTURALLY CLOSED

**Claim:** `confidence: null` on ambient journal entries is fixed — `getattr(_amb_plan, "confidence", None)` is present in the ambient daemon journal call.

**Evidence:**
- `server.py:1038` — `"confidence": getattr(_amb_plan, "confidence", None)` — CONFIRMED LIVE
- Full surrounding context: `server.py:1027–1045` — ambient `_dj_record(...)` call includes confidence field in `exec_decision` dict
- Tests: `tests/test_wo_fix_112_ambient.py` written and run → **4/4 PASS** (commit 6d06bc2)
- AT-3: `executive.py` has 0 matches for "FIX-112-AMBIENT", "getattr.*_amb_plan", "ambient_confidence" — **FREEZE_V1_LOCK clean**
- AT-4: `decision_journal.record()` writes confidence from exec_decision — main-turn regression confirmed

**Note:** The fix was already present in server.py when the WO was dispatched. This close confirms it and adds a permanent regression test.

---

*Board / Lead Architect · 2026-08-28*
