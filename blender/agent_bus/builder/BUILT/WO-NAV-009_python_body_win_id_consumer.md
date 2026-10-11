# WO-NAV-009 — Python body_win_id Consumer
**Seat:** Builder  
**Status:** ⏸ HELD — issue on Unity-WO-B1 Design acceptance  
**Authority:** SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md (SP-9) · Execution Directive 2026-08-24  
**Depends on:** Unity-WO-B1 (Design — emit body_win_id in elo_spatial.json) · WO-NAV-004 ✅

---

## Why this matters

eLo's brain cannot know where eLo's body physically is until `body_win_id` is in `elo_spatial.json` AND Python reads it into the world model each turn. Without this, the navigate handler (WO-NAV-013) cannot anchor the departure node — it cannot answer "where am I starting from?"

This closes the spatial self-knowledge gap in the One Brain: the Brain knows Body position per turn.

---

## Scope

### D-1 — Read body_win_id from elo_spatial.json

In the spatial faculty / world state assembly (`spatial_faculty.py` or equivalent — find the file that reads `elo_spatial.json`):

```python
body_win_id: int = spatial_data.get("body_win_id", -1)
```

`-1` = mid-hop / unknown. Treat as "position unconfirmed" (L3-NAV-3: departure node remains authoritative until movement_report.arrived=True).

### D-2 — Expose body_win_id in world_dict

Add `body_win_id` to the assembled `world_dict` so it is accessible to:
- The navigate handler (WO-NAV-013) — for departure node
- The SelfCapabilitySnapshot (PRES-006) — for current position
- The consequence consumers

### D-3 — L3-NAV-3 enforcement

When `movement_report.arrived` is False (in-flight / fell), `body_win_id` from the report = -1. The Python world model must NOT update the confirmed body position until `arrived=True`. Departure node remains authoritative.

This is two lines: check `movement_outcome.arrived` before updating `world_dict["body_win_id"]` from the report.

---

## Acceptance tests

| AT | Description | Pass criterion |
|---|---|---|
| AT-1 | `body_win_id` present in `world_dict` after spatial read | Key exists, not KeyError |
| AT-2 | When Unity emits `body_win_id=5`, Python world_dict shows `body_win_id=5` | Values match |
| AT-3 | When Unity emits `body_win_id=-1` (mid-hop), world_dict shows -1 | Mid-hop correctly represented |
| AT-4 | On `movement_report.arrived=False`, body_win_id NOT updated from report | L3-NAV-3 respected |
| AT-5 | On `movement_report.arrived=True`, body_win_id updated to confirmed surface | Arrival updates position |

---

## Lane rules
- `.py` only. Do not touch `elo_spatial.json` format (Design owns that via Unity).
- Do not modify Unity-WO-B1's output schema — consume what Design emits.
- Do not alter L3-NAV-3 rule — departure node stays authoritative until arrived=True confirmed.

## Return evidence
`FROM_BUILDER_WO-NAV-009_result.md` in `builder/DONE/`: commit hash · AT-1–5 pass/fail · example world_dict entry showing body_win_id.

---

**NOTE TO BUILDER:** This WO is HELD. Do not execute until Board issues. Watch for `FROM_ARCHITECT_*_WO-NAV-009_RELEASED.md`. Board issues immediately on Unity-WO-B1 Design acceptance.

---

*Board / Lead Architect · 2026-08-25*
