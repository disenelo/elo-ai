# FROM ARCHITECT → MT — Verification Dispatch: WO-MOBILE-001 Mobile End
**Date:** 2026-08-28
**Authority:** Board — Builder spine side complete (5/5 PASS, commit 5d982a5); MT verifies mobile-end only
**Priority:** P2

---

## Context

WO-MOBILE-001 adds mobile embodiment to the spine side:
- `mobile_foreground` event → `apply_embodiment("phone")`; `nearby_surfaces = []`
- `mobile_background` event → keeps `embodiment = "phone"`, `lifecycle = "background"`
- Two new fields: `EloSelfState.mobile_lifecycle`, `EloSelfState.embodiment_transitions`

Builder spine tests pass 5/5 against the Python spine in isolation. MT must verify against **live behaviour** by firing events through the authenticated channel (`unity_events.json`).

**MT does NOT touch any spine files.** Read-only + event injection only.

---

## MT Verify Actions

1. Confirm commit `5d982a5` resolves in git — or confirm `runtime/mobile_embodiment.py` exists.
2. Confirm `tests/test_wo_mobile001_mobile_embodiment.py` exists and runs clean under VP-2:
   `~/miniconda3/bin/python3 -m pytest tests/test_wo_mobile001_mobile_embodiment.py -v` → 5/5 PASS.
3. Inspect `runtime/mobile_embodiment.py` — confirm `apply_embodiment("phone")` clears `nearby_surfaces` to `[]` and sets `EloSelfState.embodiment = "phone"`.
4. Inspect `server.py` for `mobile_foreground` handler — confirm it calls into `mobile_embodiment.py` (not inline logic).
5. If Unity/Presence app is running:
   - Inject `{"type": "mobile_foreground", "_ts": <unix_ts>}` into `unity_events.json`.
   - After a 1–2s poll cycle, read `elo_state.json` → confirm `embodiment = "phone"` and `nearby_surfaces = []`.
   - Inject `{"type": "mobile_background", "_ts": <unix_ts>}`.
   - Read `elo_state.json` → confirm `embodiment = "phone"` (unchanged) and `mobile_lifecycle = "background"`.
   - If Presence not running: note as expected (cannot live-fire) — static tests 5/5 stand.

---

## Acceptance Tests

| AT | Criterion |
|---|---|
| AT-1 | `test_wo_mobile001_mobile_embodiment.py` 5/5 PASS under VP-2 |
| AT-2 | `runtime/mobile_embodiment.py` exists at commit `5d982a5` |
| AT-3 | `mobile_foreground` handler in `server.py` confirmed (grep) |
| AT-4 | Live: `elo_state.json.embodiment = "phone"` after foreground event (or "Presence not running — static only" if app down) |
| AT-5 | Live: `elo_state.json.mobile_lifecycle = "background"` after background event (same caveat) |

---

## Return

Result card: `blender/agent_bus/mt/DONE/FROM_MT_WO-MOBILE-001_mobile_end_verification_result.md`

Board closes WO-MOBILE-001 on MT VERIFIED return.

---

*Board / Lead Architect · 2026-08-28*
