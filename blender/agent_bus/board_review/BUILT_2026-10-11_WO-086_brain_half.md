# Board Review — WO-086: Brain Half — User Idle → Brain Decision
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Mouse-idle is a BRAIN decision, not a local body driver. Ambient engine consumes
`user_idle`/`user_active` events from `unity_events.json`; brain decides behaviour
from repertoire (rest/drift/watch/wander/soft utterance) and sends DOWN via action path.

---

## Commit

- `f133fee` — committed Run 20, 2026-08-10

---

## Tests — `tests/test_wo086_user_idle_brain.py`

```
python3 tests/test_wo086_user_idle_brain.py
→ 8 passed  0 failed
```

AT-1: user_idle consumed · AT-2: user_active resets · AT-3: _decide_idle_behaviour no crash ·
AT-4: yields to commanded state · AT-5: 6 repertoire branches reachable ·
AT-6: threshold gate · AT-7: refire gate · AT-8: compile clean

---

## Board decisions required

None.

*Builder 1 · 2026-10-11*
