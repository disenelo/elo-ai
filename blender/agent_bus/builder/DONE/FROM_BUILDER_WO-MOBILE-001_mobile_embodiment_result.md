# FROM BUILDER → BOARD — WO-MOBILE-001 Result Card
**Date:** 2026-08-27
**Commit:** 5d982a5
**Seat:** Builder (spine side only — MT handles mobile end)

---

## Deliverables

| D | File | Description | Status |
|---|---|---|---|
| D-SPINE-1 | `server.py` + `runtime/mobile_embodiment.py` | mobile_foreground event → apply_embodiment("phone") | ✅ |
| D-SPINE-2 | `runtime/mobile_embodiment.py` | mobile_background → keeps "phone", sets lifecycle="background" | ✅ |
| D-SPINE-3 | `runtime/mobile_embodiment.py` | nearby_surfaces cleared on mobile switch | ✅ |
| Schema | `self/elo_self_model.py` | `mobile_lifecycle: str` + `embodiment_transitions: list` fields | ✅ |

## Governed Design Decisions (as built)

**D1 — Vocabulary string "phone":** Used. `EloSelfState.embodiment = "phone"`.

**D2 — Background behaviour:** `apply_mobile_background()` keeps `embodiment = "phone"`. Sets `mobile_lifecycle = "background"`. Embodiment and lifecycle are separate dimensions — no revert to "desktop".

**D3 — `nearby_surfaces` clear:** `apply_mobile_foreground()` sets `state.nearby_surfaces = []` and logs at WARNING. Desktop surface state cannot leak into mobile.

## Guardrails (CA-validated)

**G2:** Events arrive only via authenticated `_poll_unity_events` loop — no unauthenticated trigger path.

**G4:** `mobile_foreground` / `mobile_background` events handled only inside the server's `_poll_unity_events` loop — the authenticated window process.

**G5:** `nearby_surfaces` cleared on transition — no desktop win_id semantics on mobile.

**G9:** Smallest authorised change — only added two fields to EloSelfState, one module, and one event handler branch.

## Acceptance tests — 5/5 PASS

```
~/miniconda3/bin/python3 -m pytest tests/test_wo_mobile001_mobile_embodiment.py -q
.....
5 passed in 0.06s
```

| AT | Description | Result |
|---|---|---|
| AT-1 | foreground event → current_embodiment = "phone" | ✅ PASS |
| AT-2 | embodiment_scope filters phone correctly via spine._capability_faculty | ✅ PASS |
| AT-3 | embodiment_transitions contains timestamped transition record | ✅ PASS |
| AT-4 | background event → embodiment stays "phone", lifecycle="background" | ✅ PASS |
| AT-5 | nearby_surfaces cleared to [] on mobile switch | ✅ PASS |

## Constraints obeyed

- `executive.py` not touched (FREEZE_V1_LOCK)
- `living_presence_spec.txt` not touched
- No new capability system, no parallel registry, no desktop replication
- `_self_mutate()` used for atomic load-mutate-save

## MT dispatch amendment

MT mobile end: fire `{"type": "mobile_foreground", "_ts": <unix_ts>}` through unity_events.json (the authenticated window process). Confirm AT-1 through AT-5 against live spine behaviour. MT does NOT touch spine files.

## Board/LA close criteria

Board/LA confirms: `current_embodiment = "phone"` in world_dict after foreground event. `nearby_surfaces` cleared. `executive.py` diff empty. Frozen kernel untouched.

**Builder does not self-close. Board/LA closes.**

---

*Builder · 2026-08-27*
