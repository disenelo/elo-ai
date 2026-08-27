# INITIATIVE 01 — DISENELO Presence as eLo Company Operating Interface
## Board Audit Output
**Authority:** David L3 · Initiative 01 directive 2026-08-27  
**Seat:** Board / Lead Architect  
**Date:** 2026-08-27  
**Scope:** Audit ONLY per §12 — no implementation authorised by this document  

---

## 1. CURRENT STATE

`company_runtime/` package EXISTS and is running:
- `company_state_writer.py` — reads DISPATCH_BOARD.md → emits `blender/company_state.json` (live; last written 2026-08-27T02:28:32)
- `company_brain_state_writer.py` — emits `blender/company_brain_state.json` in EloBrainCluster schema (same visual language as eLo brain; divisions in vortex slots; no David founder core — per David direction)
- `company_graph.py`, `company_memory.py`, `company_knowledge.py`, `approval_faculty.py`, `scheduling_faculty.py`, `orchestration_faculty.py`, `dashboard_server.py`, `agent_bus.py`, `agent_poll.py`, `agent_refresh.py`

WO-EA2-1 status: **READY** (company_state_writer appears implemented/running; no formal MT verification on disk)  
WO-EA2-2 status: **READY** (Presence panel not started; depends on WO-EA2-1)

Cognitive Spine: `runtime/spine/spine.py` — fully operational. Pipeline: Language → Relationship → Capability → System → Executive → Conversation Faculty → CognitivePlan. eLo's One Brain controls all decisions.

company.* intents: test spec exists (`tests/test_ea2_2_company_intents.py`) but NOT wired into the capability/intent engine.

eLo spine does NOT read `company_state.json` — "how's the company today?" is not resolvable through the cognitive layer.

Post-LLM eLo response gate: NOT CONFIRMED IN CODEBASE. Pre-LLM gates exist (`claim_gate.py`, `identity_guard.py`, `memory_claim_guard.py` — all fire BEFORE the model). No post-LLM gate that intercepts the model's candidate result and routes it back through eLo for grounding, provenance and identity checking was found.

---

## 2. EXISTING ARCHITECTURE

**One Brain:** `runtime/spine/spine.py` — Executive decides; all faculties feed; produces one CognitivePlan. Frozen cognitive kernel (LAW-017 / FREEZE_V1_LOCK).

**Company Brain:** `company_runtime/` — additive package only; does not touch the frozen kernel. Reads DISPATCH_BOARD.md; emits `company_state.json` and `company_brain_state.json`. company_actions.json intake channel accepts action requests from Presence UI — writes requests only; eLo applies them (Amendment 7 / LAW-017 safety model).

**Presence (Unity):** polls `company_state.json` alongside `brain_state.json`. WO-EA2-2 specifies embedding DISENELO_Presence_Dashboard.html as a webview panel in Unity — fastest path confirmed in WO text.

**Safety gate:** L3 actor required for approvals; money/legal WOs refused without human_flag (company_state_writer.py:50–55).

**Pre-LLM gates (spine):** claim_gate → identity_guard → memory_claim_guard — all fire before the LLM is called.

**Post-LLM gate:** NOT IMPLEMENTED (see Gap D).

---

## 3. INTENT ALREADY SATISFIED

- `company_state.json` written from live board data — company_state_writer.py running ✅
- `company_brain_state.json` in EloBrainCluster schema — reuses eLo visual language ✅
- company_actions.json intake channel — action request flow exists ✅
- Safety gate: L3 actor, money/legal block, human_flag enforcement ✅
- Additive-only principle (LAW-017 respected) — company_runtime does not touch cognitive kernel ✅
- "No orange David founder core" — respected in company_brain_state_writer.py ✅
- company_state schema fields: `today_priorities · waiting_for_approval · blocked · money · roadmap · board · graph · seats_sample · voiced_briefing` — all present ✅

---

## 4. GAPS

**A. eLo cognitive pipeline cannot read company_state.**  
No faculty in `spine.py` or the capability registry reads `company_state.json`. "How's the company today?" produces a generic LLM response, not a read of live governed state.

**B. company.* intents not wired into capability/intent engine.**  
`company.briefing · company.board · company.approvals · company.approve · company.move` exist in test spec but are not registered as capabilities in the capability registry (`runtime/capabilities/registry`). The spine's capability_faculty cannot surface them.

**C. WO-EA2-2 (Presence panel) not started.**  
company_state.json is being written but not yet rendered in Unity as a Presence panel. The full David↔Presence↔Company Brain visual loop is incomplete.

**D. No post-LLM eLo response gate.**  
Model output reaches the final response without eLo intercepting it for grounding, provenance, identity and continuity checks. This is the primary Convergence Directive §6 gap. It is also the gap that causes the observed failures (unsupported claims, provider behaviour appearing as eLo).

**E. company_state content is STALE.**  
`voiced_briefing` shows: "1 item ready to pick up · 1 awaiting David approval · WO-074, WO-075, RD-4 in progress · 1 blocked" — this does not reflect current programme state (Wave 1 complete, WO-NAV-013 DONE, Unity-WO-B1/B2 DONE, etc.). `company_focus` still shows "post-Presentable audit + canon integration + One Brain." DISPATCH_BOARD.md header section last formally updated 2026-08-23. company_state_writer reads a stale source.

---

## 5. DRIFT

| Component | Classification | Evidence |
|---|---|---|
| company_state.json content | **DRIFTED** | voiced_briefing and company_focus are weeks out of date vs. current programme |
| DISPATCH_BOARD.md source | **STALE** | Header section 2026-08-23; company_state_writer reads this |
| company.* intents | **PARTIAL** | Test spec exists; not wired into runtime |
| Post-LLM response gate | **MISSING** | Pre-LLM gates exist; post-LLM gate absent |
| company_state → spine wiring | **MISSING** | No faculty reads company_state in cognitive turn |
| WO-EA2-1 | **IMPLEMENTED / UNVERIFIED** | company_state_writer running; no MT verification on disk |
| WO-EA2-2 | **NOT STARTED** | Status: READY; no implementation |

---

## 6. EXISTING SPEC / WO COVERAGE

| Gap | Existing WO / Spec |
|---|---|
| Company state writer + action intake | **WO-EA2-1** (READY — unverified) |
| Presence panel + company.* voice intents | **WO-EA2-2** (READY — awaiting WO-EA2-1) |
| company.* capability wiring (Python spine) | **WO-EA2-2** §2.3 covers voice intents with Builder — partially scoped |
| company_state → One Brain cognitive wiring | NOT COVERED — new WO required |
| Post-LLM eLo response gate | NOT COVERED — Convergence Directive §6 intent only; no WO issued |

---

## 7. GENUINELY NEW SPEC / GOVERNANCE

**NEW-A — Company Brain → One Brain cognitive wiring**  
A new WO is required to wire `company_state.json` reading into the cognitive spine so eLo can answer company-state questions through its own cognitive layer (not by passing voiced_briefing string directly as output). Intent: `"how's the company today?" → spine reads company_state → Executive understands state → eLo responds in its own identity`. This is the core §4 capability from Initiative 01. Not covered by EA2-1 or EA2-2.

**NEW-B — Post-LLM eLo response gate**  
A new WO is required to implement the FACULTY → CANDIDATE RESULT → eLo → GROUNDING / PROVENANCE / IDENTITY → ACCEPT/EDIT/REJECT → FINAL eLo RESPONSE chain from Convergence Directive §6. This gate must be able to: reject unsupported claims; refuse assumptions about David's current state; prevent model output from speaking as eLo without identity validation; distinguish FACULTY FAILURE / TOOL FAILURE / ROUTING FAILURE / MEMORY FAILURE / CONTEXT FAILURE / NO ANSWER.

These are the two items where genuinely new governed work is required before the existing architecture can fully realise Initiative 01.

**NEW-C — company_state freshness / DISPATCH_BOARD source repair**  
The company_state_writer reads DISPATCH_BOARD.md. The DISPATCH_BOARD header section is stale. A governed update is required to bring DISPATCH_BOARD current (2026-08-27 state) so company_state.json reflects live programme reality.

---

## 8. DISPATCH

Per §12: no implementation during this audit. The first governed action is verification of existing work.

**Dispatch: MT → verify WO-EA2-1**  
Run `python3 tests/test_ea2_1_company_state.py` and `python3 tests/test_ea2_2_company_intents.py`.  
Report: AT count · pass/fail · any defects.  
On PASS: WO-EA2-1 closes → Board dispatches WO-EA2-2 to Design.

---

## 9. VERIFICATION REQUIREMENTS

| Item | Verification |
|---|---|
| WO-EA2-1 | 5 ATs: company_state/v1 all keys present · approval_request L3 actor flips status · money WO refused · malformed request dropped · frozen kernel tests pass |
| WO-EA2-2 | David visual: panel renders live company_state.json · approve round-trip: tap→company_actions.json→EA2-1 re-emits→panel re-renders · move round-trip · voice "how's the company today" → voiced_briefing spoken |
| NEW-A (cognitive wiring) | "how's the company today?" → eLo reads company_state → response grounded in live board data, not LLM reconstruction |
| NEW-B (post-LLM gate) | Counterfactual: same input WITH gate → unsupported claim rejected; WITHOUT gate → passes through |
| NEW-C (Board freshness) | voiced_briefing reflects current programme state (navigation wave complete, etc.) |

---

## 10. NEXT SINGLE GOVERNED ITEM

**MT — verify WO-EA2-1** (`test_ea2_1_company_state.py` + `test_ea2_2_company_intents.py`)

Zero new implementation risk. Clears the gate for WO-EA2-2. Establishes whether the company state foundation is verified or has defects requiring repair before Design starts the Presence panel.

---

*Board / Lead Architect · 2026-08-27 · Authority: Initiative 01 §16*

---

## Addendum — 2026-08-27 (same session, post-Convergence implementation)

**Gap D / NEW-B status update:**  
`runtime/response_ownership.py` was implemented under the L3 Convergence Directive (commit `4688685`). This addresses Gap D and NEW-B: the post-LLM eLo response gate is now wired into `server.py` before `_sanitise()`. Three checks: explicit correction hold (R-3), tool claim provenance (R-1), ungrounded action claims (R-1). Gap D is now CLOSED. NEW-B does not require a separate WO — covered by the Convergence Directive.

**Revised gaps open:**  
- Gap A: eLo cognitive pipeline cannot read company_state — STILL OPEN  
- Gap B: company.* intents not wired into capability/intent engine — STILL OPEN  
- Gap C: WO-EA2-2 (Presence panel) not started — STILL OPEN  
- Gap E: company_state content stale — STILL OPEN  
- Gap D: POST-LLM GATE — CLOSED (commit 4688685)
