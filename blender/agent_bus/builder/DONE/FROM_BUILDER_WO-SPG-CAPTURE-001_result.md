# FROM_BUILDER — WO-SPG-CAPTURE-001 Result Card
**Date:** 2026-09-05  
**WO:** WO-SPG-CAPTURE-001 — SPG Passive Memory Link Signal Logger  
**Priority:** P2 · Authority: David L3 2026-09-05  
**Executed by:** Builder seat  

---

## Prior SPG work found

`_to_delete/_spg_e1_summaries.json` — archived data only, no production code. Nothing to duplicate.

## Deliverables

| Item | Status |
|---|---|
| `memory/spg_capture.py` — `SPGCapture` class | CHANGED (NEW) |
| `data/spg_signals.jsonl` append-only signal log | CREATED ON FIRST WRITE |
| 7 signal types: memory_write, memory_read, significance_spike, relationship_shift, continuity_link, embodiment_transition, creation_event | CHANGED |
| 10MB rotation → `spg_signals_<date>.jsonl.gz` | CHANGED |
| 30-day purge of rotated files | CHANGED |
| `get_capture()` module-level singleton | CHANGED |
| No integration into spine.py, executive.py, capability_registry.py | UNCHANGED |

## Hook points (D-3 verification)

| Hook | Status |
|---|---|
| After WKG write → `memory_write` | DEFERRED — no clean post-write hook point without spine mutation |
| After SP-29 score > 0.6 → `significance_spike` | DEFERRED — no post-score hook point without spine mutation |
| After relationship faculty update → `relationship_shift` | DEFERRED — no clean post-update hook |
| After ExecutionReport written → signal log | DEFERRED — ExecutionReport path needs post-write callback |

**All D-3 hook points deferred per WO instruction:** "If a hook point doesn't exist cleanly, do NOT add a hook that mutates the spine." Passive capture API is ready — callers can be wired once clean hook points are established by a future WO.

## Acceptance tests

| AT | Result |
|---|---|
| AT-1: `from memory.spg_capture import SPGCapture; SPGCapture()` imports cleanly | PASS |
| AT-2: grows by ≥1 entry per `log()` call | PASS |
| AT-3: entry contains `ts`, `turn_id`, `signal_type`, `embodiment` | PASS |
| AT-4: non-blocking (failures silently logged, not raised) | PASS |
| AT-5: no forbidden imports (spine, executive, capability_registry) | PASS |
| AT-6: rotation at 10MB (`_MAX_BYTES = 10 * 1024 * 1024`) | PASS |

*Builder seat · 2026-09-05 · WO-SPG-CAPTURE-001*
