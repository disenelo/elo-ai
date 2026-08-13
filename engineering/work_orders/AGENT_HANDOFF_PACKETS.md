# Agent Handoff Packets
### Exactly what files to pass to each agent

For David (or the CEO Agent): when you brief an agent, hand it **its packet below** — the
files it needs and nothing else. Each agent also gets its section of `AGENT_BRIEFINGS.md`
(role + rules) and its Work Orders from `DISPATCH_BOARD.md`.

Paths: `A/` = `~/elo-ai/` · `O/` = `~/Desktop/Output/` · `D/` = `~/Downloads/`.

---

## 🟦 BUILDER (Python — eLo OS)
Pass:
- `A/docs/architecture/ARCHITECTURE_BIBLE.md` · `A/docs/architecture/DECISION_LOG.md` (law)
- `A/docs/architecture/Volume_V/CONTRACTS.md`
- Spec volumes: `A/docs/architecture/Volume_V/` · `Volume_VI/` · `VIII/` · `IX/` · `X/` · `XII/` · `XV/` · `XVI/` · `XX/` · `XXII/`
- `A/docs/architecture/16_spine_runtime.md` · `17_memory_update.md`
- Work packages: `A/engineering/work_packages/WP_C,D,E,G,H_*.md`
- `A/CO_WORKING_GUIDE.md`
- Its briefing section + `A/engineering/work_orders/DISPATCH_BOARD.md`
Work orders: **WO-005 → WO-001 → WO-004 → WO-002 → WO-011 → WO-009 → WO-012 → WO-008** (+ WO-006/007 when unblocked).
**Scope (D-I): edit `~/elo-ai/` ONLY — never the DISENELO apps in `~/Desktop/Output/` (file those to the Architect).**

## 🟩 UI / AVATAR (Unity)
Pass:
- `A/CO_WORKING_GUIDE.md` (§4 the `blender_state.json` contract)
- `A/docs/architecture/ARCHITECTURE_BIBLE.md` (Vol XI Motor, Vol XIII Presence)
- `A/docs/architecture/Volume_IX/02_Symbol_Engine_and_DeepDream.md` (dream visuals)
- `A/handovers/` — `EloOS_Wiring_Spec.md`, `EloBlendShapes_Handover.md`, `UNITY_AGENT_HANDOVER_S15/S16/S17.md`, `OS_AGENT_HANDOVER_S16.md`
- Project: `O/DISENELO-eLoDesktopBuddy/`
Work orders: **WO-010 · INT-6**.

## 🟧 CO-CREATIVE (Weavy · Higgsfield · Figma)
Pass:
- `O/DISENELO_CREATIVE_PRODUCTION_HOUSE.md`
- Creative canon: `D/Disenelo_Studio_Bible.pdf` · `D/eLo_Creative_Universal_Bible.pdf` · `D/DISENELO_Studio_Library_Volume_01_Universe_Bible_v1.docx` · `D/DISENELO_Studio_Library_Volume_02_...docx` · `D/DISENELO_Emotional_Colour_Visual_Language_Bible_v1.docx`
- `O/DISENELO_PRODUCT_INTERCONNECTION_MAP.md`
Work orders: **CR-1 · CR-2 · CR-3**. (Outputs from Weavy/Higgsfield → `A/docs/architecture/_intake/`.)

## 🟦 MARKETING
Pass:
- `O/DISENELO_CREATIVE_PRODUCTION_HOUSE.md` · `O/DISENELO_COMPANY_OPERATING_MODEL.md`
- `D/DISENELO_Marketing_Strategy.docx` (in `O/` too) · `D/DISENELO_market_system_EXPANDED.pdf`
- `D/Disenelo_Master_Roadmap.pdf` · `D/DISENELO_Tracker_System/roadmap.md`
Work orders: **MK-1 · MK-2**.

## 🧵 DESIGN / FASHION HOUSE
Pass:
- `O/DISENELO_FASHION_HOUSE.md`
- `D/Disenelo_Studio_Bible.pdf` (Sewing/Fashion ladder) · visual + colour bibles (as Co-Creative) · `D/Disenelo_Glow_eLo_Vinyl_System.pdf`
- Apps: `O/DISENELO-Plushies/` (pattern engine) · `O/DISENELO-CompositionDesigner/` · `O/DISENELO-Sketchbook/`
- Tool: `D/Snapmaker Luban.app` (plotter/cutter/printer)
Work orders: **FH-1 … FH-7**.

## 🟪 PLANNING (Gemini / ChatGPT)
Pass:
- `A/docs/architecture/ARCHITECTURE_BIBLE.md` · `Volume_V/CONTRACTS.md` · the specific volume they're helping
- `A/docs/architecture/_intake/README.md`
Output → `A/docs/architecture/_intake/` (intake, not canon).

## 🟥 DEBUG  *(after WO-001)*
Pass:
- `A/docs/architecture/Volume_V/CONTRACTS.md` (§2 the `trace` field) · `A/CO_WORKING_GUIDE.md`
- Live signals: `A/logs/behaviour_audit.jsonl` · `A/dashboard/` · Unity console · `A/blender/blender_state.json`
- `A/engineering/proofs/` · `A/docs/architecture/ARCHITECTURE_AUDIT.md`

## 🟫 CEO AGENT
Pass:
- `A/engineering/work_orders/DISPATCH_BOARD.md` · `AGENT_BRIEFINGS.md` · `CEO_AGENT.md` · this file
- `A/docs/architecture/DECISION_LOG.md` · `ARCHITECTURE_AUDIT.md` · `00_CANON_INDEX.md`
- `O/DISENELO_MASTER_INDEX.md` (the whole-studio map)

---

## ⚙️ COMPANY RUNTIME — BUILDER  *(WO-EA2-1)*
Goal: the eLo/Python side of the Presence company bridge — an **additive `company_runtime/` package**
(never touch frozen core — LAW-017). Writes `company_state.json`; accepts action requests; stubs `company.approve`.
Pass:
- `O/DISENELO_UNIVERSAL_RUNTIME_EA3.md` (LAW-017 · one Executive · faculties · envelope-neutral · migration+validation)
- `O/DISENELO_PRESENCE_ELO_INTEGRATION.md` (the bridge: state file + action channel + request contract)
- `O/DISENELO_EA2_ELOAI_ALIGNMENT_REVIEW.md` (what's reused vs. new — CA-011)
- `O/WORK_ORDER_SPEC.md` · `O/DISENELO_CONSTITUTION.md`
- Pattern files to clone/observe: `A/blender_bridge/brain_state_writer.py` · `A/dashboard/event_bus.py` · `A/dashboard/server.py` · `A/runtime/executive.py` · `A/core/faculty_bus.py` · reverse-channel precedent `A/blender/unity_events.json`
- Its Work Order: `A/engineering/work_orders/WO-EA2-1_Company_State_Writer.md`
Emits: `A/blender/company_state.json` · reads `A/blender/company_actions.json`.
**Rules:** additive ONLY (no `core/`, `runtime/spine/`, or `FREEZE_V1_LOCK` edits) · envelope stays universal (context in `payload`) · observer→Executive only · tests + frozen-kernel-green before DONE.

## 🖥️ COMPANY RUNTIME — DESIGNER UI AGENT (Presence)  *(WO-EA2-2)*
Goal: the Presence panel that renders the company + Company Brain and lets David show/move/organise/approve —
every action a **request through the Executive**, never a direct state write (EA-3 Amendment 7).
Pass:
- `O/DISENELO_Presence_Dashboard.html` (the built panel — embed in a Presence webview first)
- `O/DISENELO_PRESENCE_ELO_INTEGRATION.md` (render path + request channel + contract)
- `O/DISENELO_UNIVERSAL_RUNTIME_EA3.md` (§7 dashboards observe, never control)
- `A/CO_WORKING_GUIDE.md` (§4 the JSON-bridge/polling contract) · MoodPalette source `A/runtime/light_engine/light_engine.py` (colours are canon — do not invent hues)
- Its Work Order: `A/engineering/work_orders/WO-EA2-2_Presence_Panel_And_Requests.md`
Reads: `A/blender/company_state.json` (from EA2-1) · writes: `A/blender/company_actions.json` (requests only).
**Rules:** observer only — never mutate `company_state.json`/the board · colours from MoodPalette only · re-render only after eLo re-emits state (proves the Executive acted). Depends on WO-EA2-1.

---

*Give an agent its packet + its briefing section + its Work Orders. That's a complete
hand-off. — Lead Architect, 2026-07-27 (Company Runtime packets added 2026-07-29).*
