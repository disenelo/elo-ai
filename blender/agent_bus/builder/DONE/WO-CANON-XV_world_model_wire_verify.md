# WO-CANON-XV — World Model: COMPLETE + WIRE + VERIFY

**Status:** DONE (Builder scope — consumer migration note below)
**Closed:** 2026-08-27
**Seat:** SEAT-ENG-001 (Builder)

---

## What was done this session

### Part A — Assembly bug fix (degraded[] reconciliation)
Added reconciliation sweep in `assemble_world_state()` before the frozen dataclass is
created. Every domain whose `domain_health[d]['status'] ∈ {absent, stale}` is now added
to `degraded[]` if missing. Fixes the long-standing bug where browser/files/internet/
calendar/weather were marked absent in `domain_health` but never appeared in `degraded`.

### Part B — Envelope binding (Vol V §2 / Ch.1 §1.8)
Added `sender: str = "WorldStateFaculty"` and `expires: str = ""` fields to `LiveWorldState`.
`assemble_world_state()` now sets `expires = assembled_ts + 30s` (ISO-8601). The 30-second
TTL matches the turn budget — a world snapshot is perishable and must not be reused across turns.

Note: The broken import (`get_active_window`) described in the WO's IRV was already fixed
before this session (desktop assembly uses `_ws_mod.get()` correctly).

### RT-1..RT-6 tests added
Extended `tests/test_canon_xv_world_state.py` with 6 new tests:
- RT-1: import sanity — `desktop.window_state.get` exists; domain health always present
- RT-2: no bare `except:` clauses in assembly path
- RT-3: temporal faculty reads `world_state`, not direct sensors
- RT-4: envelope — `sender='WorldStateFaculty'`, `expires` set and after `assembled_ts`
- RT-5: `set(degraded) == {d for d,h in domain_health.items() if h['status'] in (absent, stale)}`
- RT-6: no spatial reasoning functions in `live_world_state.py` (Vol XIII boundary)

## Evidence

```
~/miniconda3/bin/python3 tests/test_canon_xv_world_state.py

  [FT-1..AT-4: 14 existing tests — all PASS]
  ✅ RT-1: desktop.window_state.get exists; desktop domain always has health entry
  ✅ RT-2: no bare except: clauses — code errors cannot be silently converted to absent
  ✅ RT-3: temporal faculty reads world_state; _build_temporal_state succeeds
  ✅ RT-4: envelope bound — sender='WorldStateFaculty', expires=...+00:00
  ✅ RT-5: degraded == domain_health absent/stale set (6 domains)
  ✅ RT-6: Vol XIII boundary — no spatial reasoning functions

WO-CANON-XV world state  20 passed  0 failed
```

**Commit:** `415203d`

## DoD status

| Item | Status | Note |
|---|---|---|
| Assembly bugs fixed | ✅ | broken import pre-fixed; degraded reconciliation done |
| Envelope binding (sender + expires) | ✅ | done |
| Consumer migration (≥1 faculty) | ✅ | temporal faculty reads world_state.time/calendar |
| pre-spine tool_router.py migration (3 sites) | ⚠️ DEFERRED | requires WO-CANON-VII first (pre-spine decision closes) |
| 20 ATs pass | ✅ | |
| Vol XV metadata update | ⚠️ ARCHITECT | Architect must update Volume_XV/00_Metadata.md — Builder lane ends here |

**WO-CANON-XV Builder scope: DONE.**
The Architect must sign off and update `Volume_XV/00_Metadata.md` before this is canonical.
