# WO-CANON-XII — Perception: wire + verify

**Status:** DONE (verification — implementation was already in place)
**Closed:** 2026-08-27
**Seat:** SEAT-ENG-001 (Builder)

---

## Finding

WO-CANON-XV (LiveWorldState) DONE unblocked WO-CANON-XII. On inspection, the full
implementation was already in place:

- `perceive()` + `perceive_from_live_state()` produce one frozen `PerceptionResult` per turn
- Ch.3 §3.2 copy step: `assemble_world_state()` reads `perception` arg and copies fields into
  domain slices with `source="PerceptionFaculty"` and verbatim confidence
- Ch.4 §4.3: `partial: bool` field on `PerceptionResult`, `relations: tuple = ()` (no fabricated
  inter-object links)
- `tag_partial()` + WO-076 PERCEPTION RAIL in server.py for fidelity enforcement

## Evidence

```
~/miniconda3/bin/python3 tests/test_canon_xii_perception.py

  ✅ Ch.1/FT-1..ST-3: single frozen PerceptionResult, no fabrication
  ✅ Ch.2/FT-3..ST-4: confidence scaling, robot camera absent handled
  ✅ Ch.3/FT-4..ST-6: perception fields populate LiveWorldState; confidence not inflated
  ✅ Ch.4/AT-1..AT-3: partial=True when confidence<0.7 or primary modality absent
  ✅ AT-4: py_compile clean

WO-CANON-XII perception  15 passed  0 failed
```

Also: `test_wo076_perception_fidelity.py` 8/8 PASS · `test_wo009_perception_faculty.py` 7/7 PASS.

**WO-CANON-XII is DONE.**
