# WO-043 Faculty Bus Isolation — Result Card

**Builder:** Builder 1
**Date:** 2026-10-04
**Status:** COMPLETE — 5/5 ATs pass; already implemented in prior session

---

## What was verified

`server.py`:
- Old "use it naturally if the moment feels right" ambient phrase removed
- Ambient injection uses "CURIOUS FACT" framing (not bare "FACT AVAILABLE")
- ANTI-FABRICATION block covers area-level weather/forecast facts
- ANTI-FABRICATION block explicitly bans "X in your studio" style assertions

## ATs

- AT-1 ✅ old ambient phrase removed from server.py
- AT-2 ✅ ambient injection uses "CURIOUS FACT" framing
- AT-3 ✅ ANTI-FABRICATION block covers area-level weather facts
- AT-4 ✅ ANTI-FABRICATION block bans "X in your studio" assertions
- AT-5 ✅ py_compile clean on server.py

**Run:** `python3 tests/test_wo043_bus_isolation.py` → **5/5 passed**
