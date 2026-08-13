# WO-CANON-XVI — Multi-Faculty Coordination: assemble-before-decide + priority scheduling on the bus

**Owner:** Builder (eLo OS — `runtime/spine/`, `runtime/executive.py`, `core/faculty_bus.py`). **Priority:** P2 —
Horizon-2 (post-Presentable v1), Tier A. **Status:** QUEUED — **gated on alignment ruling C** (CANON_REVIEW_QUEUE
2026-08-10, item 3) for the name/ordering call; the conflict-resolution order (§4.2) also touches David L3 (safety veto).
**Closes:** Audit gap #1 (Faculty Bus, highest).

**Canon refs:** Volume XVI — Ch.1 `01_Coordination_Under_One_Executive.md`, Ch.2 `02_Executive_Assembly_One_Plan.md`,
Ch.3 `03_Faculty_Bus_Routing_and_Priority.md`, Ch.4 `04_Conflict_Resolution_and_One_Brain_Across_Embodiments.md`.
Governing record: **ADR-Exec-006** (assemble-before-decide). Extend-do-not-fork.

## Problem / Goal
The single Executive, one `CognitivePlan`/turn, the `CognitiveSnapshot` (WO-052) and the Faculty Bus envelope+router
(`core/faculty_bus.py`, WO-001) are LIVE. Gaps: (a) `assemble_cognitive_state()` runs **after** the decision, but
ADR-Exec-006 says the unified state is assembled **before**; (b) a name clash — code `CognitiveSnapshot` vs canon
`UnifiedCognitiveState`; (c) the bus delivers FIFO and only the Attention→Executive proof pair is wired. Goal:
assemble-before-decide into one frozen object, converge the ADR-Exec-006 components, add priority-ordered delivery,
subscribe the real faculties.

## Scope to DoD (grounded in Ch.1–Ch.4; extend named live files, do not rebuild)
- **Assemble-before-decide (Ch.2, the core PENDING build):** move the read-only inputs earlier in
  `runtime/spine/spine.py::run()` so ASSEMBLE runs **before** DECIDE. Converge the ADR-Exec-006 components into the
  existing `runtime/cognitive_snapshot.py::build_snapshot` (add `world`, `narrative`, `working_memory`, `reflection`,
  `curiosity` beside the current self/health/attention/body/intent/affordances/perception) — do NOT build a parallel
  assembler. Freeze the assembled state; no faculty mutates post-freeze; each component independently degradable
  (a missing one lowers `confidence`, flags the gap, contributes a neutral default, never blocks the turn).
- **Name resolution (ruling C / D-XVI-A):** once ratified, adopt one canonical name for the assembled object
  (`UnifiedCognitiveState` per ADR-Exec-006 vs code `CognitiveSnapshot`), the other as alias. Do not proceed on the
  build's naming until ruling C lands.
- **One decision, one plan (`runtime/executive.py`):** `decide()` stays the single decision; Assembly only feeds it.
  Do NOT add a second decider. Emit `payload.type: unified_cognitive_state` with `expires` = turn TTL (perishable,
  never reused). PROJECT never re-opens the decision.
- **Faculty Bus (Ch.3) — do NOT rebuild `Envelope`/`FacultyBus`:** two remaining jobs — (a) subscribe the real
  faculties (Memory, Relationship, Capability, World, etc.) onto the bus (today only the Attention→Executive proof pair
  is wired; others use in-process call order) with behaviour-parity asserts per migration; (b) implement
  **priority-ordered delivery** (`critical` pre-empts) replacing FIFO `self._queues[faculty].append(...)`. Enforce
  validation in `is_valid()`/`publish()`: required `id/sender/receiver/priority/payload.type` else REJECTED to
  `_dropped`; `priority ∈ {low,normal,high,critical}`; `0.0≤confidence≤1.0` and `lower_confidence()` raises on attempt
  to raise; past-`expires` → DROPPED; `trace` append-only. Only the Executive sets `critical`/`high`; faculties may not
  self-escalate. Bus stays synchronous, non-blocking.
- **Conflict resolution + embodiment (Ch.4):** add the §4.2 resolution ORDER to the existing Executive decision (NOT a
  new faculty): SAFETY VETO > TRUTH/VERIFICATION > EXECUTIVE PRIORITY > CONFIDENCE > RELATIONSHIP/PRESENCE. Emit a
  `conflict_resolution` note on the one plan with **rationale logged** (never a silent overrule). Destructive/
  irreversible action under contradiction → never auto-execute; clarify; preserve relationship. Extend
  `build_embodiment_state()` / `_LED_FROM_EMOTIONAL_STATE` as a rendering table (no body re-decides; autonomous ==
  commanded path).

## Definition of Done
- One frozen unified state assembled BEFORE the decision each turn, carrying the ADR-Exec-006 components under one
  canonical name; Executive decides once → one `CognitivePlan`; projection re-decides nothing.
- Bus delivers by priority (critical pre-empts), rejects malformed, never raises confidence, drops expired, keeps an
  append-only trace; real faculties subscribed with output parity.
- Conflicts resolved by the ratified order with logged rationale; delete-all-files-style contradiction → clarify, never act.
- Audit can mark Vol XVI COMPLETE.

## Tests to write (`tests/test_canon_xvi_coordination.py`)
- Ch.1: Executive-only allocation, capability market, no voting, no bus bypass, prohibitions hold (LTM/personality
  write blocked), one mind end-to-end.
- Ch.2: one assembly per turn (frozen first), one plan out, degraded component explicit (narrative offline → neutral
  default + confidence drop), one component down never blocks, no mid-turn mutation, no second decider, assemble→decide→project.
- Ch.3: malformed rejected, broadcast + address, filtered subscription (Attention high/critical only), trace appended,
  confidence never raised, expired dropped, pull-and-clear, non-blocking, proof pair (LIVE), bus feeds Assembly.
- Ch.4: no vote, safety veto (delete-all → clarify), truth not arbitrated, rationale logged, one being across bodies,
  body-switch continuity, surface down, autonomous == commanded, resolve→project.

## Dependencies + blocked-by
- **Blocked by:** **alignment ruling C** (assemble-before-decide + name clash) — CA call; the §4.2 conflict order is
  flagged INVENTION and safety-veto changes remain **David L3**. Runs behind Presentable v1. Soft-blocked by
  WO-CANON-XV (the `world` component needs `LiveWorldState`).
- Cross-volume: Vol V CONTRACTS.md (bus/envelope/lifecycle authoritative), Vol XXII (Faculty Genome — capability
  schema; XXII depends on this volume for Executive selection), Vol XXI (narrative continuity across body-switch),
  D-F/D-G.
- **Gate:** ruling C (CA) + David L3 on safety-veto ordering.

## Lane
Builder (Python — spine reorder, snapshot convergence, executive resolution order, bus priority + subscription).
Architect coordinates + relays ruling C / David L3 on safety order.
