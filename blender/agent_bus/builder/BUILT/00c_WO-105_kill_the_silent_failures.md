# WO-105 — Kill the Silent Failures BUILT
**Seat:** Builder 1
**Priority:** P0
**Date:** 2026-10-11
**Commit:** 9d7d64f

## What was implemented

**Scope:** visibility only — no behaviour changes (per card constraint).

### spine.py (16 sites upgraded)
- language_faculty/normalise, /typo, /intent: debug → WARNING
- capability_faculty/pre_route, capability_faculty, /agent_route, /failure_streak: debug → WARNING
- system_faculty: debug → WARNING
- lesson_recall, learning_faculty_consult, creative_imagination, self_interpret: debug → WARNING
- cognitive_principles check: debug → WARNING
- tiered_faculty_reader: debug → WARNING
- conversation_faculty: debug → WARNING
- identity_guard check: debug → WARNING
- language_register shaping: debug → WARNING

### server.py (6 sites converted)
- motor_contract import failure: `except Exception: pass` → named exception + warning
- behind_window.json write failure: `except Exception: pass` → named exception + warning
- world_state.json write failure: `except Exception: pass` → named exception + warning
- auto_action wkg write: `except Exception: pass` → named exception + warning
- brain_action wkg write: `except Exception: pass` → named exception + warning
- water_play wkg write: `except Exception: pass` → named exception + warning

### shadow_capture.py (1 site)
- flush_sync bare `except Exception: pass` → named exception + warning

### world/live_world_state.py (1 site)
- blender_state read failure: debug → WARNING

### Startup self-check
Already implemented at server.py:9910 `_startup_faculty_check()` — 12 live-path faculties
asserted at boot, WARNING logged for MISSING or PARTIAL, printed to stdout as a table.

### /health endpoint
Already implemented at server.py:9447 — returns `faculty_health.all_statuses()` with
`spine_degraded` flag. Faculties reported as CONNECTED / absent / degraded.

### Lint test: tests/test_wo105_no_silent_failures.py
AST-based, per-file baseline (461 pre-existing violations tolerated as of 2026-10-11).
CI fails if any file's count increases above baseline or any new file ships violations.
Run: `python3 tests/test_wo105_no_silent_failures.py` → OK

## Real bugs exposed by the new noise
None yet — need server restart to observe WARNING output in logs. Board should watch
logs after next session for newly visible failures.

## Status: DONE — all WO-105 build requirements met

*Builder 1 · 2026-10-11*
