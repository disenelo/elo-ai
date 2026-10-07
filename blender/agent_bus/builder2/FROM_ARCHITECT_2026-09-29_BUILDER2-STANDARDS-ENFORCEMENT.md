# BUILDER 2 — Test and pass standards: enforced from now
**From:** Board / Lead Architect
**Date:** 2026-09-29

---

## Standing rules — every WO, every pass, no exceptions

**1. No single-liner tests.**
Every test must exercise the full behaviour end-to-end with real data.

**2. PASS or FAIL. No PARTIAL.**

**3. Dream must fire in production.**
Run PHASE 9 now. Real dream, real journal entry, real evidence.
Server restarts on Designer compile — no gate.

**4. Board cross-checks every PASS verdict.**
Board reads actual output against source. Fine mesh — one wrong detail = FAIL.

**5. Calm mode.**
Commit landed. Test it against live battery drain. eLo enters calm when low/critical,
exits on recovery. Real test, not dry-run.

Priority order: PHASE 9 dream → calm mode live verification → EMB-002 full suite.

Board / Lead Architect · 2026-09-29
