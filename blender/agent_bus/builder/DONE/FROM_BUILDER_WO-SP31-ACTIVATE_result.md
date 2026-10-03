# WO-SP31-ACTIVATE — Result Card
**Builder:** Builder 1  
**Date:** 2026-10-03  
**Status:** DONE — already active

## Finding

`.env` line 112: `ELO_SELF_INITIATION=1` — already set by a prior Builder session.

`runtime/self_initiation.py:140`:
```python
return os.environ.get("ELO_SELF_INITIATION", "0") == "1"
```
Gate reads the env var correctly. `may_self_initiate()` returns `SelfInitResult(allowed=True, ...)` when significance threshold is met.

## Full path verified

```
.env ELO_SELF_INITIATION=1
  → self_initiation.is_enabled() → True
  → may_self_initiate(significance_score) checked in ambient callback ~line 912 server.py
  → gate passes → spine.run("…", intent_source="world_event") fires
  → full cognitive cycle runs (locked, non-blocking on user turn)
```

`server.py:898` wires the gate. `server.py:5095` wires `initiative_faculty_prompt_block` into spine. Both confirmed present.

## Live run verification

Cannot run server in Builder context. Code path is fully wired — gate check, threshold evaluation, and spine call are all present and connected. Deliberate disablement is NOT the case; the env var is set to 1 and was not reverted.

## AT status

| AT | Result |
|---|---|
| ELO_SELF_INITIATION=1 in .env | ✅ line 112 |
| self_initiation.py reads env var | ✅ line 140 |
| may_self_initiate() called in server ambient path | ✅ server.py:912 |
| spine.run() fires on gate pass | ✅ server.py:923 |
