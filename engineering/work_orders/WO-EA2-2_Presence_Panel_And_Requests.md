---
id: WO-EA2-2
title: "Presence company panel (render) + action-request channel + company.* intents"
owner_seat: SEAT-ENG-004 (Unity / Avatar — Designer UI Agent)
occupant: Designer UI Agent (Unity) + Builder (intent hook)
priority: P1
reason: "Presence must render the company dashboard/Company-Brain as a panel and let David show/move/approve by voice or tap — as REQUESTS through the Executive (Amendment 7). EA-3 / Presence-Integration spec."
roadmap_tag: PROJ-ELOOS · Evolution Phase II (Executive Partner)
depends_on: [WO-EA2-1]
inputs: "**PRIMARY: Output/DISENELO_COMPANY_BRAIN_UI_SPEC.md** (§1 data schema · §2 Figma auto-layout + layer naming · §3 Unity C# skeleton) · DISENELO_Presence_Dashboard.html (working reference) · DISENELO_PRESENCE_ELO_INTEGRATION.md · blender/company_state.json (from EA2-1, LIVE) · Figma file UdpnVgHT7qWOiyzk0MIgLU (MoodPalette vars + Company Brain frame) · existing unity_bridge_server.py / unity_events.json pattern"
review_required: L2 → L3 (David visual + approve round-trip)
canonical_docs: [EA-3, DISENELO_PRESENCE_ELO_INTEGRATION.md, WORK_ORDER_SPEC]
risk: "low — observer surface; must not write state directly (LAW-017 Amendment 7)"
status: READY
lane: DISENELO Presence (Unity)
created: 2026-07-29
---

# WO-EA2-2 — Presence company panel + request channel (Designer UI Agent)

## 1. Objective
Give DISENELO Presence a **company panel** that renders `company_state.json` and lets David **show, move,
organise, and approve** — every action emitted as a **request through the Executive**, never a direct
state write.

## 2. Exactly what to build
1. **Render the panel from state.** Read **`blender/company_state.json`** (same polling pattern Presence
   uses for `brain_state.json`) and render the surfaces:
   - **Briefing · Company Brain (connectome) · Board (kanban) · Approvals**.
   - **Fastest path:** embed `DISENELO_Presence_Dashboard.html` in a Presence **webview** panel pointed at
     the file (it already renders all four + the mood-palette connectome). Native Unity port can follow.
   - Wire the **eLo orb → Company Brain** (already in the HTML); colours come from the MoodPalette (canon).
2. **Action requests (the DO path).** On tap/drag/voice, **write a request to
   `blender/company_actions.json`** (mirror `unity_events.json`) — never edit `company_state.json`:
   - **Approve** button / *"approve WO-043"* → `{type:"approval_request", work_order, actor:"David (L3)"}`.
   - **Drag a card** / *"move WO-043 to review"* → `{type:"move", work_order, to_status}`.
   - *"re-prioritise…"* → `{type:"reorder", ...}`.
   - After writing, show an optimistic "requested…" state; **re-render only when EA2-1 re-emits state**
     (proves the Executive, not the UI, made the change).
3. **`company.*` voice intents** (with Builder): `company.briefing · company.board · company.approvals ·
   company.approve · company.move` → route to the panel surface + speak the summary
   (`company_state.json.voiced_briefing`).

## 3. Constraints (MUST)
- **Observer only.** The panel MUST NOT mutate `company_state.json` or the board. It writes *requests*;
  eLo applies them (Amendment 7 / LAW-017). This is the whole safety model — do not shortcut it.
- Colours strictly from the MoodPalette (per canon) — do not introduce new hues.
- Additive to Presence; reuse the existing bridge server / polling.

## 4. Acceptance tests (David visual + round-trip)
- Panel renders all four surfaces from a live `company_state.json`; orb opens Company Brain; nodes clickable.
- **Approve round-trip:** tap Approve → request lands in `company_actions.json` → (EA2-1) flips the WO →
  Presence re-renders the card as DONE. Prove the UI did **not** change state itself.
- **Move round-trip:** drag/say-move → card reflows only after eLo re-emits state.
- Voice: *"how's the company today"* → Briefing + spoken summary; *"show me how it connects"* → Company Brain.
- Builds/plays 0 errors; short screen capture + commit → `COMPLETION_LOG.md`.

## 5. Handback
Commit + capture → `COMPLETION_LOG.md`. Pairs with WO-EA2-1. This is the slice David runs as the first
real "talk to eLo → it shows and approves" test on Presence (Evolution Phase II validation).
