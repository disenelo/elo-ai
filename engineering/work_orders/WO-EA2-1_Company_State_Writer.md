---
id: WO-EA2-1
title: "Company State writer + company.approve intake (company_runtime, additive)"
owner_seat: SEAT-ENG-013 (Data) + SEAT-ENG-001 (Builder)
occupant: Builder (Claude Code / Python)
priority: P1
reason: "Phase II Executive Partner needs a live company_state.json (twin of brain_state.json) and an action-request intake so Presence can show + approve. EA-3 / CA-011 / Presence-Integration spec."
roadmap_tag: PROJ-ELOOS · Evolution Phase II (Executive Partner)
depends_on: []
inputs: "DISENELO_PRESENCE_ELO_INTEGRATION.md · DISENELO_UNIVERSAL_RUNTIME_EA3.md · existing blender_bridge/brain_state_writer.py (pattern) · dashboard/event_bus.py · runtime/executive.py"
review_required: L2 (touches runtime wiring) → L3
canonical_docs: [EA-3, WORK_ORDER_SPEC, DISENELO_PRESENCE_ELO_INTEGRATION.md]
risk: "low — ADDITIVE ONLY; must not modify frozen kernel (LAW-017 / FREEZE_V1_LOCK)"
status: READY
lane: company_runtime (NEW additive package — NOT eLo cognitive core)
created: 2026-07-29
---

# WO-EA2-1 — Company State writer + action intake (Builder)

## 1. Objective
Stand up the **eLo-side** of the Presence company bridge, as a new **additive** package
`company_runtime/` that observes/reuses eLo primitives and **never edits the frozen cognitive kernel**
(LAW-017). Two deliverables: (a) write `company_state.json`; (b) accept action requests from Presence.

## 2. Exactly what to build
1. **`company_runtime/company_state_writer.py`** — clone the shape of `blender_bridge/brain_state_writer.py`.
   - Reads the source of truth (the dispatch board / work-order files + seat records) and emits
     **`blender/company_state.json`** (schema `company_state/v1`, matching the fields the Presence
     dashboard already consumes: `today_priorities · waiting_for_approval · blocked · money · roadmap ·
     board[] · graph{} · seats_sample · voiced_briefing`).
   - Callable once per cycle (like `brain_state_writer.publish()`), plus a one-shot CLI for testing.
2. **Action intake** — a watcher on **`blender/company_actions.json`** (mirror the existing
   `unity_events.json` / `listen_trigger.json` reverse-channel pattern).
   - On a new request, wrap it as a **Faculty Bus Envelope** (runtime-neutral; context in `payload`:
     `runtime:"company", type:"approval_request"|"move"|"reorder", work_order, to_status, actor`).
   - Hand to the Executive path. For this WO, a **stub Approval handler** is acceptable: apply
     `company.approve` by flipping the WO's status in the board file and re-emitting `company_state.json`
     (the full Approval/Scheduling/Orchestration faculties are EA2-4/5/6). Enforce: nothing DONE without
     an L3 `actor`; safety/money/legal WOs → require human flag (log + refuse if absent).
3. **`company.approve` CAL hook (minimal)** — register the intent name so EA2-2 can call it (full intent
   set = EA2-2, Designer/Builder split).

## 3. Constraints (MUST)
- **Additive package only.** No edits to `core/`, `runtime/spine/`, or anything under `FREEZE_V1_LOCK`.
  Reuse by import/observe (like `dashboard/` does — it states it modifies no kernel file).
- **Envelope stays universal** — company context in `payload`, never new envelope fields (EA-3 §5).
- Observer→Executive only — the writer/intake never lets Presence mutate state directly (Amendment 7).

## 4. Acceptance tests (evidence gate)
- `tests/test_ea2_1_company_state.py`:
  - writer emits valid `company_state/v1` with all consumed keys; Presence dashboard renders from it.
  - action intake: an `approval_request` with an L3 actor flips the target WO → DONE and re-emits state.
  - a money/legal WO approval **without** a human flag is refused + logged (safety gate).
  - malformed request → dropped with a trace note, no crash.
- **Frozen kernel tests stay green** (additive-only proof) — paste the run.

## 5. Handback
Commit hash + `tests/` output → `COMPLETION_LOG.md`. Architect verifies (additive + tests) → David L3.
Unblocks EA2-4/5/6 (real faculties) and pairs with **WO-EA2-2** (Presence side).
