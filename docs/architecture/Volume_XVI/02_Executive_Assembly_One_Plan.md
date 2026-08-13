---
chapter: 2
title: "Executive Assembly — One Assembled State, One Plan Per Turn"
volume: XVI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_XVI/01_Coordination_Under_One_Executive.md (the coordination law this mechanises)
  - Volume_V/CONTRACTS.md (CognitiveState freeze, envelope, lifecycle)
  - Volume_V/02_Faculty_System.md (Kernel assembles + freezes; Executive decides once)
  - Volume_XV/01_Unified_World_State.md (World slice — sibling assembly, one-per-turn discipline)
  - DECISION_LOG.md ADR-Exec-006 (Executive Assembly), ADR-Exec-002 (Single Cognitive Truth)
  - runtime/cognitive_snapshot.py (CognitiveSnapshot — WO-052 "The Moment", live)
  - runtime/spine/spine.py (one CognitivePlan per turn, live)
---

# Chapter 2: Executive Assembly — One Assembled State, One Plan Per Turn

## 2.0 Purpose

Chapter 1 states the *law*: one Executive directs its own faculties, and if faculties
disagree the Executive decides. This chapter defines the **mechanism** that makes that
law true every turn — the single point where "many faculties" collapses into "one mind."

The mechanism is **Executive Assembly** (ADR-Exec-006): the Executive **never queries
faculties one at a time**. Once per turn an Assembly Layer composes ONE verified state,
and the Executive reasons **once** against that single object, emitting exactly **one**
`CognitivePlan`. One object in, one plan out. That single-decision guarantee is what makes
eLo one brain rather than a committee — and it is the direct runtime expression of
Invariant #1 (One Brain → One Identity) and ADR-Exec-002 (Single Cognitive Truth).

This is the *threshold shift* the Vision Spine names: from **adding** faculties to
**assembling** them. (`00_DAVIDS_VISION_SPINE.md` — "Convergence over expansion.")

## 2.1 Principle — Assemble Once, Decide Once

Three rules govern the turn. They bind the Executive and every faculty.

**2.1.1 One assembled state per turn.** At the top of the turn, before any decision, the
Assembly Layer composes one object from all contributing faculties and **freezes** it. The
Executive reads *that* — it does not reach back into faculties mid-decision. If a fact is
not in the assembled state, the Executive does not know it this turn. (This is the same
one-per-turn discipline the World State follows in `Volume_XV`; the assembled state is the
superset that *includes* the World slice.)

**2.1.2 Push, not pull.** Faculties contribute *into* the assembly; the Executive is
*handed* the finished object. There is no request-per-faculty round-trip during the
decision. This is what removes ordering races and "two faculties, two truths" drift.
(Live: `runtime/cognitive_snapshot.py` — "Push (assembled and delivered) not pull (queried
mid-turn).")

**2.1.3 One decision, one plan.** The Executive produces exactly one `CognitivePlan` per
turn. No faculty produces a second, competing plan; no downstream surface re-decides. Every
word, posture, LED colour, motion, and action derives from that one plan (ADR-Exec-002).

## 2.2 The Assembled State (ADR-Exec-006)

ADR-Exec-006 names the components the Assembly Layer composes into one verified object:

```
UnifiedCognitiveState (frozen, one per turn):
  self          — verified self-model: embodiment, pose, mood, curiosity, focal thread   (ADR-Exec-004)
  world          — the LiveWorldState slice (Volume_XV): desktop, user, music, time, …
  capabilities   — what eLo can actually do right now (candidates + health + gating)
  health         — per-faculty CONNECTED / DEGRADED / OFFLINE
  working_memory — the Executive-owned attention/working set (Vol VI; D-G)
  narrative      — the active autobiographical thread (Vol XXI)
  intent_queue   — pending intentions that must survive this decision cycle
  reflection     — recent verified-consequence learning inputs (ADR-Exec-005)
  curiosity      — current curiosity pressure / open questions
  confidence     — overall assembly confidence (degrades; never blocks the turn)
```

> One object, one truth. The Executive reasons ONCE against this — never against ten
> separate faculty replies. (ADR-Exec-006, David L3 + Chief Architect 2026-08-06.)

**Object rules (MUST):**

- The assembled state is **frozen** after assembly. Faculties contribute; none mutates it
  after the freeze (mirrors `CognitiveState` in `16_runtime_contracts.md` and the World
  State freeze in `Volume_XV`).
- Each component is **independently degradable**. One component failing (e.g. narrative
  unavailable) lowers `confidence` and is flagged, but never blocks the turn.
- The assembled state is **context, not command** — it informs the decision; it never *is*
  the decision. The Executive still decides once against it (One Brain).

## 2.3 Live Ground vs. Target

> ⚠️ **CORRECTED 2026-08-10 against Ruling C** (`CANON_RULINGS_2026-08-10.md` — *ASSEMBLE
> BEFORE DECIDE*). The previous text said *"`assemble_cognitive_state(...)` runs after the
> decision in `spine.py`"*. **That is now out of date, and its replacement is not simply "fixed"
> — the truth is more specific and worse.** An Independent Runtime Verification on 2026-08-10
> read the live call sites. What follows is what they actually do.

**What exists today (grounded — IRV 2026-08-10):**

- `runtime/cognitive_snapshot.py` builds a **`CognitiveSnapshot`** — one frozen read
  assembled at the top of `spine.run()` (`spine.py:423`) and pushed toward the Executive
  (WO-052, "The Moment"). It carries: `self_*` (self-model), `faculty_health`, attention
  (`intent/valence/momentum`), `body` schema, `pending_intentions`, affordances (WO-056), and
  a Chrome/capability perception scope (WO-057), plus `assembled_ts`, `turn_id`, and a
  degrading `confidence`.
- ✅ **Inside `spine.py` the ordering is now CORRECT.** `assemble_cognitive_state(...)` is
  called at **`spine.py:448`** under the comment *"WO-CANON-XVI / ADR-Exec-006: Assemble
  unified cognitive state BEFORE Executive"*, and `_executive_faculty(...)` follows at
  **`spine.py:456`**. World and working-memory are passed into that assembly
  (`world_state=_world, working_memory=_wm`). Read in isolation, `spine.py` satisfies Ruling C.

**🔴 The remaining break — the decision happens before the spine is ever entered:**

`spine.py`'s ordering is correct but **not load-bearing**, because the Executive does not
actually decide inside the spine:

```
server.py:2321   attention_model = attn.compute(raw, _memory_pack, _state, ...)
server.py:2322   exec_decision   = exec_decide(attention_model, loop_detected=False, user_input=raw)
                 ▲ THE REAL EXECUTIVE DECISION — runtime/executive.py decide()
                 │ Nothing has been assembled yet at this point in the turn.
                 ⋮  (~580 lines of turn handling: stabilisation override, imperative override, …)
server.py:2905   _attention_with_exec["_exec_decision"] = exec_decision
server.py:2906   _plan = _spine_run(raw, state=_state, attention=_attention_with_exec, ...)
                 │
                 ├─ spine.py:423  build_snapshot(...)               ← assembles
                 ├─ spine.py:448  assemble_cognitive_state(...)     ← assembles
                 └─ spine.py:456  _executive_faculty(...)           ← does NOT decide:
                                    spine.py:162 → exec_out = attention.get("_exec_decision", {})
                                    it *reads back* the decision made at server.py:2322
```

`_executive_faculty()` (`spine.py:139–175`) copies `action`, `tone`, `max_sentences`,
`response_goal`, `valence`, `momentum`, `mode` and `register` out of the injected
`_exec_decision` dict onto the plan. **It transcribes a decision; it does not make one.**

**Therefore: eLo still decides before he assembles.** The assembled state at `spine.py:448` is
built *after* the choice was already made and is pinned to the plan afterwards
(`plan.cognitive_state = _cognitive_state`, `spine.py:461`) — which is precisely the failure
Ruling C names: *"that makes the 'self' a post-hoc description instead of the thing that
chose."* The assembly is currently a **description of the decision**, not an **input to it**.

**The remaining fix — one named change (owning seat, not the Architect):**

> **Move the `decide()` call site.** `exec_decide(...)` must be called **from inside
> `spine.run()`, after `assemble_cognitive_state(...)`**, reading the assembled state — not from
> `server.py:2322` before the spine is entered. Delete the `_exec_decision` injection
> (`server.py:2905`) and the read-back (`spine.py:162`) with it; the spine returns the decision
> rather than receiving it. Everything server.py does with `exec_decision` between lines 2322
> and 2905 (stabilisation override, imperative override) must move with it or read from the
> plan.

Until that call site moves, **Ruling C is satisfied on paper inside `spine.py` and violated in
the live turn.** A test that only inspects `spine.py`'s internal ordering will pass while the
violation stands — noted here so the ordering check is not mistaken for the fix.
(`tests/test_canon_xvi_coordination.py` locates the first `assemble_cognitive_state(` call in
`spine.py` and asserts it precedes the Executive — a true assertion about the wrong file.)

**Other gaps (PENDING — mark, do not claim done):**

- `CognitiveSnapshot` realises *some* of the ADR-Exec-006 component set (self, health,
  attention, body, intent, affordances, perception scope). `assemble_cognitive_state` now
  additionally takes **world** and **working-memory**. The **narrative**, **reflection**, and
  **curiosity** components named by ADR-Exec-006 are **not yet unified into the same frozen
  object**. Converging these into one pre-decision assembled object remains outstanding work of
  ADR-Exec-006. **Status: PARTIAL.**
- **Naming — ✅ DECIDED by Ruling C:** *"One name: `UnifiedCognitiveState` (`CognitiveSnapshot`
  is retired/aliased)."* This closes **D-XVI-A** (§2.9). Code still uses `CognitiveSnapshot`;
  the rename is the seat's work, not an open question.

## 2.4 The Turn (assembly → decision → projection)

```
top of turn
   │
   ▼
ASSEMBLE  ── compose {self, world, capabilities, health, working_memory,
   │          narrative, intent_queue, reflection, curiosity} → freeze
   ▼
DECIDE    ── Executive reasons ONCE against the frozen state → ONE CognitivePlan
   │          (runtime/executive.py decide() + spine _executive_faculty)
   ▼
PROJECT   ── the one plan enriches into expression: EmotionalVector → PresencePlan
   │          → EmbodimentState (Ch.4 covers cross-embodiment projection)
   ▼
end of turn (ExecutionReport feeds Reflection — integration window, not this turn)
```

**Turn rules (MUST):**

- ASSEMBLE runs **before** DECIDE, always. A faculty that has nothing to add contributes a
  neutral default (lower confidence), never nothing that stalls the turn.
- DECIDE happens **exactly once**. Loop-protection and stability overrides (live in
  `executive.decide()`) are *part of* that one decision, not a second decider.
- PROJECT never re-opens the decision. Surfaces render the plan; they do not re-interpret
  the world (ADR-Exec-002 — no modality invents private state).

## 2.5 Faculty Contract (the Assembly role)

```
Faculty:
  name:            ExecutiveAssembly     # a role of the Executive layer, NOT a new decider
  version:         0.1.0
  purpose:         Compose one frozen UnifiedCognitiveState per turn from all contributing
                   faculties and hand it to the Executive, so eLo reasons once against one
                   truth (ADR-Exec-006).
  contributes_to:  CognitiveState (assembly, pre-decision)
  runs_in:         response-path (top of turn, before any decision)

Inputs:
  - type: faculty_contribution   source: self-model, world, capability, memory, health,
                                          narrative, reflection, curiosity faculties
    required: false (each individually — the set degrades gracefully)
    description: Each faculty's typed contribution to the assembled state.

Outputs:
  - type: unified_cognitive_state  destination: Executive (frozen)
    description: One frozen object; the sole input the Executive reasons against this turn.

Dependencies:
  - faculty: all contributing faculties (soft each — one absent degrades confidence, never blocks)
  - faculty: FacultyBus (hard — contributions arrive as envelopes; Ch.3)

Failure Modes:
  - condition: a component faculty times out / errors
    fallback:  neutral default for that component, lower assembly confidence, flag it, continue.
  - condition: assembly exceeds turn budget
    fallback:  freeze with whatever is ready; missing components marked absent; turn proceeds.
  - condition: a faculty tries to mutate the state after freeze
    fallback:  rejected; the frozen object is read-only (One Brain — no mid-turn drift).
```

## 2.6 Lifecycle & Envelope

Ratified lifecycle (`CONTRACTS.md §3`, D-B). Assembly is a **response-path** role that runs
in `ACTIVE`; a component fault sends only that component's faculty through
`ERROR → RECOVERY → READY` (neutral default), never the whole turn. No `LEARNING`/`UPDATING`
occurs here — reflection/adaptation runs in the integration window (ADR-Exec-005).

Envelope (`CONTRACTS.md §2`): contributions arrive as envelopes with
`payload.type: cognitive_state_delta`; the assembled result is broadcast to the Executive
with `payload.type: unified_cognitive_state` and an `expires` set to the turn TTL (a snapshot
is perishable — never reused across turns, matching the World State rule in `Volume_XV`).

## 2.7 Acceptance Tests

### Functional
```
FT-1  One assembly per turn
  Given a turn begins, When the Executive decides,
  Then exactly one UnifiedCognitiveState was assembled and frozen first,
       AND the Executive did not query any faculty individually after freeze.

FT-2  One plan out
  Given the assembled state, When the Executive reasons,
  Then exactly one CognitivePlan is produced; no competing plan exists.

FT-3  Degraded component is explicit
  Given the narrative faculty is offline, When assembly runs,
  Then narrative = neutral default, confidence is lowered and the gap is flagged,
       AND no fabricated narrative appears downstream.
```

### Stability
```
ST-1  One component down never blocks the turn
  Given the world slice times out, Then it degrades (absent/stale), confidence drops,
       all other components present, the turn completes within budget.

ST-2  No mid-turn mutation
  Given a faculty updates its state after freeze, When the Executive reads,
  Then it still sees the frozen snapshot (update applies next turn).

ST-3  No second decider
  Given the assembled state, Then only the Executive emits a plan; no surface re-decides.
```

### Integration
```
IT-1  Assemble → Decide → Project (one mind end-to-end)
  Contributing faculties → ExecutiveAssembly (freeze) → Executive (ONE CognitivePlan)
       → projection (EmotionalVector → PresencePlan → EmbodimentState).
  Assert: exactly one decision per turn; removing a faculty's direct pre-decision read and
  routing it through the assembled state changes no correct output (only removes drift).
```

## 2.8 Claude Implementation Notes

- **Extend, do not fork.** `runtime/cognitive_snapshot.py` (`build_snapshot`) is the live
  Assembly Layer seed. Converge the ADR-Exec-006 components into it (add world / narrative /
  working-memory / reflection / curiosity), rather than building a parallel assembler. This
  binds CHECK-BEFORE-BUILD.
- **Corrected 2026-08-10:** the ordering *inside* `spine.run()` is already right
  (`assemble_cognitive_state` at `spine.py:448` precedes `_executive_faculty` at `456`). **The
  outstanding change is the `decide()` CALL SITE, not the spine's internal order** —
  `exec_decide(...)` is invoked at `server.py:2322`, long before `spine.run()` is entered at
  `server.py:2906`, and `_executive_faculty` merely reads the result back out of
  `attention["_exec_decision"]` (`spine.py:162`). Move `decide()` into the spine, after
  assembly, so the Executive reasons against the assembled object. See §2.3.
- Keep the post-plan `CognitiveState` / `EmbodimentState` as *projections*, not re-decisions.
- Do not add a second decider. `runtime/executive.py decide()` stays the single decision;
  Assembly only feeds it. Moving the call site must not leave a second `decide()` behind in
  `server.py`.
- **Rename to `UnifiedCognitiveState`** (Ruling C, 2026-08-10) — `CognitiveSnapshot` is
  retired/aliased. One name.

## 2.9 Open Decisions

```
D-XVI-A: ✅ DECIDED — Ruling C, 2026-08-10 (David).
         "One name: UnifiedCognitiveState (CognitiveSnapshot is retired/aliased)."
         No longer an open decision. The rename is implementation work for the owning seat.

REQUIRES DECISION — 1 item
  D-XVI-B: Confirm the ADR-Exec-006 component set (10 named components) is the complete
           target for the assembled state, and that world/narrative/working-memory/
           reflection/curiosity converge into the SAME frozen object pre-decision.
           Recommend: accept as the convergence target for WO-052 completion.  OPEN.
```

## 2.10 References
- `DECISION_LOG.md` — ADR-Exec-006 (Executive Assembly), ADR-Exec-002 (Single Cognitive
  Truth), ADR-Exec-004 (Situated Self).
- `00_DAVIDS_VISION_SPINE.md` — "Convergence over expansion" (= The Moment, WO-052).
- `Volume_V/CONTRACTS.md` — CognitiveState freeze, envelope, lifecycle.
- `Volume_XV/01_Unified_World_State.md` — the World slice; same one-per-turn / freeze discipline.
- Code: `runtime/cognitive_snapshot.py` (live Assembly seed), `runtime/spine/spine.py`
  (one plan per turn), `runtime/spine/plan.py` (`CognitivePlan`), `runtime/executive.py`
  (`decide()` — the single decision).

---
```
Chapter 2 — Executive Assembly — One Assembled State, One Plan Per Turn
Status: READY FOR REVIEW
Grounds: ADR-Exec-006 (Executive Assembly) · ADR-Exec-002 (Single Cognitive Truth)
Live code cited: runtime/cognitive_snapshot.py (PARTIAL), runtime/spine/spine.py, executive.py,
  server.py:2322 / 2906 (IRV 2026-08-10)
Faculty Contract: Included · Lifecycle/Envelope: Included · Acceptance Tests: FT×3 ST×3 IT×1
DECIDED 2026-08-10 (Ruling C, David): assemble BEFORE decide; ONE name UnifiedCognitiveState
  (CognitiveSnapshot retired/aliased) — closes D-XVI-A.
Open Decisions: 1 (D-XVI-B component-set convergence)
Implementation: PENDING (assembly is PARTIAL — see §2.3)
🔴 Ruling C NOT yet satisfied at runtime: spine.py's internal order is correct, but exec_decide()
  is called at server.py:2322 before spine.run(); _executive_faculty only transcribes it
  (spine.py:162). Remaining fix = move the decide() call site into the spine, after assembly.
```

READY FOR REVIEW
