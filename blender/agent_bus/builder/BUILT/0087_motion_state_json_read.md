# WO-0087 — Motion State JSON Read
**Seat:** Builder 1  
**Priority:** P1  
**Date:** 2026-10-11  
**Commit:** (already in repo — `ambient/ambient_engine.py` lines 441, 476-489)

## What was found

Already implemented. `_MOTION_STATE_PATH` at line 441, read loop at lines 476-489:
- Reads `blender/motion_state.json` per ambient tick
- Staleness gate: timestamp must be < 2s old
- Sets `fields["physical"]` and `fields["animation"]` from Designer's write
- Silent no-op if file doesn't exist (Designer's side not yet built)

*Builder 1 · 2026-10-11*
