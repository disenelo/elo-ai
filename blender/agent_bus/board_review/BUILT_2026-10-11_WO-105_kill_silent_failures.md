# Board Review — WO-105: Kill the Silent Failures
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## Card scope

Convert 20 silent-failure sites (bare `except: pass` and `_log.debug`-only swallows)
across `runtime/spine/spine.py`, `server.py`, `runtime/shadow_capture.py` and
`world/live_world_state.py` to one of three legitimate outcomes (raise / degrade
explicitly / ignore deliberately with comment). Add lint enforcement (CI fails on new
violations).

---

## Implementation status

Core work already landed in prior commits. The WO-105 lint test
(`tests/test_wo105_no_silent_failures.py`) was established with per-file violation
baselines, and was passing until a new file (`runtime/pre_ack.py`) was added with
a `_log.debug`-only swallow that the lint caught.

**This session:** fixed the one remaining open violation in `runtime/pre_ack.py`:
- `_log.debug("pre_ack.emit failed (non-fatal): …")` → `_log.warning(…)` with
  an inline WO-105 Rule 3 justification comment explaining why swallowing is safe here.

---

## Commit

- `b15a4dc` — WO-105: fix pre_ack.py silent failure — debug → warning

---

## Tests — `tests/test_wo105_no_silent_failures.py`

```
python3 -m pytest tests/test_wo105_no_silent_failures.py -v
→ 1 passed in 0.49s
```

Lint enforces: new files must have 0 violations; existing files may only decrease.

---

## Real bugs the new noise exposed

None new from this session. The broader lint baseline captures 461 legacy violations
across 60+ files — visible for gradual tightening per card.

**Pre-existing unrelated failure flagged:** `test_0020_ct0033_bypass_handlers.py::test_bh2_count_31`
expects 56 `_bypass_journal` calls in `server.py` but finds 59. This predates WO-105
and is unrelated to the `pre_ack.py` change. Report to board as a separate issue.

---

## Board decisions required

None. FREEZE_V1_LOCK files untouched.

*Builder 1 · 2026-10-11*
