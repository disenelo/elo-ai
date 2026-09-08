# Unity-WO-B1 — Emit `body_win_id` from Unity
**From:** Board / Lead Architect  
**To:** Builder (Unity seat)  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 Unity track (independent of Python Wave 1 items)  
**RTR:** RTR-041  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` + `findings/SPEC_AMENDMENT_PHASE2_NAV_2026-08-23.md` — B1, SP-9 dependency

---

## Context

Python currently has no verified way to know which platform (ledge/win_id) eLo's body is actually on. This blocks:
- SP-9: Logical body position resolution
- SP-11: Candidate generation (which platforms are reachable from here?)
- SP-13: candidate_surfaces in world_dict
- SP-25/SP-26: Executive re-routing after fall

The fix is simple: Unity must emit the current ledge's `win_id` as `body_win_id` in the spatial data it writes.

**Canonical rule (L3-NAV-3):** The departure node is authoritative until `movement_report.arrived = True` confirms the new position. During transit (mid-hop), `body_win_id` must emit `-1` (indicating "in transit — position unverified").

---

## Deliverables

### D-1 — Expose `body_win_id` in Unity spatial write
**Files:** `Assets/Scripts/DesktopBuddy.WriteSpatial()` and/or `EloDesktopNav.CurrentWinId()` (verify actual file names)  
**Contract:**
- When eLo is confirmed on a ledge (EloLedge() returns a valid platform): emit `body_win_id = <ledge_win_id>`
- When eLo is mid-hop / in transit / EloLedge() returns -1: emit `body_win_id = -1`
- `win_id` values must match the win_id values used in `elo_spatial.json` surface_graph (so Python can look them up)
- This value is written into the spatial data alongside existing fields (body position, gaze, etc.)

**Data type:** string or integer — match what `elo_spatial.json` uses for `win_id`.

---

## Forbidden Scope

- No changes to cognitive architecture, Python side, or Executive
- Do not invent new win_id values — use existing surface_graph win_ids
- Do not emit a speculative position during transit — only `-1` when mid-hop

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | body_win_id present in spatial data | After eLo lands on a known ledge, Python receives spatial data containing `body_win_id` matching that ledge's win_id from elo_spatial.json |
| AT-2 | Mid-hop emits -1 | During a jump (between departure and landing), Python receives `body_win_id = -1` |
| AT-3 | Landing updates body_win_id | After movement_report.arrived = True, subsequent spatial write contains the new ledge's win_id |
| AT-4 | win_id matches surface_graph | Emitted win_id for a known ledge matches the corresponding entry in elo_spatial.json surface_graph |

---

## RTR Traceability

After implementation, update RTR-041 in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-041: add Unity-WO-B1, commit, AT-1 through AT-4 pass

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*
