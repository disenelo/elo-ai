---
id: WO-031
title: "Auto-start the continuation loop with eLo OS — always-on, event-driven (no clock), so the board self-refreshes wherever David is"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P1
reason: "David 2026-08-02: 'I work all the time — I want it to run, not on a set timescale.' The continuation loop is event-driven (reacts to board changes + light tick) but only runs inside the dashboard server. Make it start with eLo OS so it's always reactive, no cron."
review_required: L1 → L3
risk: medium (touches eLo OS startup — runtime path). BRANCH + David smoke-test before merge (WO-026 lesson).
status: READY
created: 2026-08-02
---

# WO-031 — auto-start the continuation loop with eLo OS

## Goal
The continuation loop (`company_runtime.continuation.watch` / `start_thread`) reacts to board changes
instantly + a 5s tick — event-driven, no schedule. Today it only runs when the dashboard server is up.
Make it **start automatically as a background daemon thread when eLo OS boots**, so it's always on and
reactive wherever David is, with no cron and no manual launch.

## Requirements
1. On eLo OS startup, start `continuation.start_thread()` as a **daemon thread** (non-blocking, dies with
   the process) — same pattern the dashboard server already uses.
2. **Guard it:** single instance only (don't start twice if dashboard server also starts it — use a
   module-level flag/lock so only one continuation thread runs); `DISENELO_NO_AUTOLOOP=1` disables.
3. It must **never block or slow eLo OS boot or turn-handling** — pure background; failures log and are
   swallowed, never crash the runtime.
4. Additive only — no frozen-kernel edits. Wire at the eLo OS entry point (server.py boot) behind the
   guard, or a small `runtime` startup hook.

## Safety (WO-026 lesson — this touches the runtime path)
- Do it on a **branch**; `py_compile` clean; David smoke-tests eLo boots + responds normally with the
  loop running before merge. A background thread must not be able to wedge the response path.

## Acceptance
1. Launch eLo OS (no dashboard server) → continuation loop is running (board change → state refresh within
   seconds), confirmed via `blender/company_state.json` updating on a board edit.
2. Only ONE continuation thread runs even if the dashboard server is also started.
3. eLo boots + responds with no added latency; `DISENELO_NO_AUTOLOOP=1` cleanly disables.
4. `tests/test_wo031_autostart.py` (thread starts once, guard works, non-blocking). py_compile clean.

## Notes
- This is the "always-on, event-driven, no clock" David asked for — replaces the (now disabled) hourly
  cron sweep. The loop reacts to activity; the dashboard is current whenever he looks.
