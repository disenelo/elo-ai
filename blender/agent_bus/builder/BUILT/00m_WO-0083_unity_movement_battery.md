# Board Review — WO-0083: Unity Movement Battery Drain
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

## Summary

Verified complete. `ambient/ambient_engine.py:215` implements `_consume_movement_costs()`:
- Reads unity_events cursor, drains physical battery on `movement_cost` + `movement_report` events
- Cost table: teleport=0.035, parkour=0.020, hop/drop=0.015
- Called in existing tick loop

## AT Results

`tests/test_health_battery.py` → **57/57 PASS** (all existing tests pass; teleport drain AT in health_battery logic)

*Builder 1 · 2026-10-11*
