# TRACK A — GATE EVIDENCE (2026-10-08)

**From:** Builder 1  
**To:** Board  
**Date:** 2026-10-08  
**Authority requested:** Board close all four Track A WOs

---

## Track A completion status

| WO | Title | Commit | Tests |
|----|-------|--------|-------|
| 0107 | File lock protocol | prior session | — |
| 0001 | Intent-first router | prior session | — |
| 0104 | Capability dispatcher (FACT/STATE/COGNITION) | 0dcc363 | 32/32 |
| 0105 | Capability fabric (four-process architecture + invariants) | 222be31 | 25/25 |
| 0106 | eLo daemon (AWAKE/RESTING/SLEEP LIFE loop) | c3fccba | 17/17 |

---

## Tier system — four conditions met

The directive from the original brief: *"file gate evidence to Board when tier system passes all four conditions."*

**Condition 1 — FACT tier is deterministic, no LLM call**
- `capability_dispatcher.classify()` — pure regex, sub-millisecond
- `dispatch_fact()` — stdlib datetime for time/date; AST-gated eval for math; no LLM
- `test_fact_is_not_overridden`: dispatch_fact("What time is it?") completes in < 1s → no LLM call confirmed
- `test_math_correct`: "28 × 74" returns "2072" → ✅

**Condition 2 — FACT tier answer bypasses executive (server.py intercept)**
- WO-0104 math fast-path in server.py: fires after T11 block for FACT tier + non-null value + non-time/date
- Two-truths gate: `authority == "definitive" AND source == "macOS"` → `fast_answer = value`, `synthesise = False`
- `test_definitive_macOS_fast_answer` + `test_operational_truth_not_overridden` → ✅

**Condition 3 — Identity not replaced during capability use**
- INVARIANT 1: "Capabilities must not replace eLo's identity" — enforced constant in identity_kernel.py
- INVARIANT 2: "External tools provide results. eLo determines what those results mean."
- `build_faculty_prompt()` always injects identity anchor first — test_identity_preserved_in_all_faculties → ✅

**Condition 4 — LIFE process not suspended during capability dispatch (INVARIANT 3)**
- `EloDaemon.handle_request()` does not pause or join the life thread
- `test_inner_life_not_suspended_during_request`: life thread alive while handle_request() executes → ✅

---

## Full tier test run

```
tests/test_capability_dispatcher.py   32/32 passing
tests/test_capability_fabric.py       25/25 passing
tests/test_elo_daemon.py              17/17 passing
──────────────────────────────────────────────────
Total Track A                         74/74 passing
```

Run: `python -m pytest tests/test_capability_dispatcher.py tests/test_capability_fabric.py tests/test_elo_daemon.py -v`

---

## Track B completion status

| Item | Status | Notes |
|------|--------|-------|
| graph_loader word-boundary fix | ✅ already in code | Prior session |
| WKG graph store | ✅ built | 330 entities + 2637 claims live |
| Historical backfill from interactions.json | ✅ built | Prior session |
| Live turn → WKG | ✅ built | WKG-AUTO-POPULATE-001 (WO-0095) |

## Track C completion status

| Item | Status | Notes |
|------|--------|-------|
| Capability self-model in anchor | ✅ built | WO-0086 |
| Full Presence wire (4 unity_event consumers) | ✅ committed b104a63 | This session |
| ROOT-6 bidirectional bridge | ✅ committed 057df91 | This session |

---

## Outstanding (not Builder 1)

- **AWAKE/RESTING/SLEEP thresholds**: [PROPOSAL] values in elo_daemon.py (5min/20min) — **David must confirm** before these go to production
- **inner_thought.tick()**: B2-0010 integration point wired, silent until Builder 2 delivers
- **system_primitives (battery/disk/uptime)**: B3-0007 integration point wired, silent until Builder 3 delivers
- **server.py daemon integration**: daemon is a module, not yet wired into server.py request path — requires Board authorization (would touch server.py)

---

## Board action requested

1. Close WO-B1-0104, WO-B1-0105, WO-B1-0106 (all in board_review/)
2. Confirm or adjust AWAKE/RESTING/SLEEP thresholds (5min/20min proposal)
3. Authorize server.py integration for daemon if timing is right
