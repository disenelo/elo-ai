---
chapter: 2
title: "Executive Assembly and The Moment — Assemble Before Decide (Ruling C)"
volume: VII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (UnifiedCognitiveState name + frozen snapshot LIVE; the decision still precedes assembly at process level — see §2.3)
audit_status: OPEN
dependencies:
  - CANON_RULINGS_2026-08-10.md Ruling C (assemble BEFORE decide; ONE name UnifiedCognitiveState) — DECIDED
  - DECISION_LOG.md ADR-Exec-006 (Executive Assembly), ADR-Exec-004 (Situated Self), ADR-Exec-002 (Single Cognitive Truth)
  - Volume_XVI/02_Executive_Assembly_One_Plan.md (the assembly MECHANISM — push-not-pull, degradation, contract)
  - Volume_XV/01_Unified_World_State.md (the `world` slice; same one-per-turn freeze discipline)
  - Volume_VI/04_Wiring_Working_Memory_Into_The_Turn.md (the `working_memory` slice; §4.5 The Moment)
  - SITUATED_SELF_v1_assembly.md (the Capstone Principle — the self is ASSEMBLED, not generated)
  - _intake/SOURCE_2026-08-08_self_model_becoming.md (VERBATIM — "He needs a sense of 'now'")
  - runtime/cognitive_snapshot.py, runtime/the_moment.py, runtime/spine/spine.py, server.py
---

# Chapter 2: Executive Assembly and The Moment

## 2.0 Purpose

Ruling C, verbatim (`CANON_RULINGS_2026-08-10.md`, David approved):

> **Ruling C — ASSEMBLE BEFORE DECIDE (Vol XVI) ✅ DECIDED**
> *The unified cognitive state is assembled **BEFORE** the Executive decides, per ADR-Exec-006.
> Current code assembles* after *the decision — that makes the "self" a post-hoc description instead
> of the thing that chose. **One name: `UnifiedCognitiveState`** (`CognitiveSnapshot` is
> retired/aliased). Rationale: the self is ASSEMBLED, not generated — assembly must precede choice
> or eLo is narrating, not being.*

Volume XVI Ch.2 owns **how** the object is composed (push-not-pull, per-component degradation, the
assembly faculty contract). This chapter owns the thing XVI cannot own, because it is a property of
the *decider* and not of the *coordination*: **the ordering law** — that no Executive decision may
be taken against a state assembled after it, or against no assembled state at all.

It also names what the assembled object *is to eLo*: **The Moment**.

## 2.1 Principle — the self is assembled, not generated

**2.1.1 Assembly precedes choice. Always.** The Executive may not decide until one frozen
`UnifiedCognitiveState` exists for this turn. A decision taken before assembly is, by canon's own
definition, narration: the state that "explains" it was written afterwards.

**2.1.2 One name.** `UnifiedCognitiveState` is the canonical name (ADR-Exec-006, Ruling C).
`CognitiveSnapshot` is the retired implementation name and survives only as an alias. Naming is
architecture: two names for the assembled self is how two selves start.

**2.1.3 If it is not in the assembled state, the Executive does not know it.** No mid-decision reach
back into a faculty, no late sensor read, no "check that quickly". This is what removes ordering
races and "two faculties, two truths" drift, and it is the same one-read-per-turn discipline
`Volume_XV` applies to the world and `Volume_VI` applies to working memory.

**2.1.4 Frozen after assembly.** Faculties contribute; none mutates after the freeze. Consequences
of the decision apply to the *next* turn's assembly, never to this one
(Vol V Law: *Reality Informs, Never Mutates*).

**2.1.5 Assembly informs; it does not decide.** The assembled state is context, not command. The
Executive still decides once against it (Ch.1). An assembled state that *implies* an action has not
taken it.

## 2.2 What composes The Moment

ADR-Exec-006 names the components; this is that list, with each one's owning volume and its
verified live status. **The Executive's precondition is that this object exists — not that every
component is present** (any component may degrade; §2.5).

```
UnifiedCognitiveState (frozen, exactly one per turn):
  self            verified self-model: embodiment · location/surface · pose · size/reach ·
                  mood · curiosity · current action · faculty health of the body   (ADR-Exec-004)
  world           the LiveWorldState slice: desktop · user · music · time · …      (Vol XV)
  capabilities    what eLo can ACTUALLY do right now — candidates, health, gating  (Vol V; WO-055)
  health          per-faculty CONNECTED / DEGRADED / OFFLINE                        (runtime/faculty_health.py)
  working_memory  the Executive-owned attention/working set + winner/budget/mode   (Vol VI; D-G)
  narrative       the active autobiographical thread                                (Vol XXI)
  intent_queue    pending intentions that must survive this decision cycle          (Ch.4)
  reflection      recent verified-consequence learning inputs                       (ADR-Exec-005; Vol XXVIII)
  curiosity       current curiosity pressure / open questions
  affordances     what this surface/world affords right now                         (ADR-Exec-003)
  confidence      overall assembly confidence — degrades, never blocks the turn
  assembled_ts · turn_id                                                            (perishability)
```

**Live vs target (verified 2026-08-10 by reading `runtime/cognitive_snapshot.py`):**

| Component | In the frozen object today? |
|---|---|
| `self` | **YES** — `self_mood`, `self_curiosity`, `self_satisfaction`, `self_session_read`, `self_focal_thread`, `self_model_block` |
| `health` | **YES** — `faculty_health`, `health_summary` |
| `working_memory` (partial) | **PARTIAL** — attention only (`intent`/`valence`/`momentum`/`tone`/`action`). The typed `WorkingMemory` object is assembled separately in `spine.run()` and pinned to the plan, not into the snapshot. |
| `capabilities` | **YES** — `gated_capabilities`, health-gated |
| `affordances` | **YES** — `surface_type`, `surface_affordances` (WO-056) |
| body/perception scope | **YES** — `BodySchema` (pending sit, queued intent), Chrome scope (WO-057) |
| `intent_queue` | **NAME ONLY** — `pending_intentions` exists but holds at most `("sit","cursor")`. No dual queue, no arbitration. **Ch.4 = PENDING.** |
| `world` | **NO** — assembled separately (`plan.world`), not inside the snapshot; Vol XV build is queued |
| `narrative` · `reflection` · `curiosity` | **NO** — not in the frozen object |
| `confidence` · `assembled_ts` · `turn_id` | **YES** |

**Rule (MUST):** convergence is by **extension of `runtime/cognitive_snapshot.py`**, never by a
parallel assembler (`Volume_XVI` §2.8; CHECK-BEFORE-BUILD). Today three assembled objects ride the
plan — `plan.snapshot`, `plan.cognitive_state`, `plan.world`, `plan.working_memory`. Four objects
that should be one is the residual shape of the problem Ruling C exists to end.

## 2.3 The ordering — verified, and where it is still broken

**What Ruling C requires:**

```
top of turn
   │
   ▼
ASSEMBLE ── compose all components → FREEZE → UnifiedCognitiveState
   │
   ▼
DECIDE   ── the Executive reasons ONCE against that frozen object → ONE CognitivePlan
   │
   ▼
PROJECT  ── plan → EmotionalVector → PresencePlan → EmbodimentState (never re-decides)
   │
   ▼
end of turn → ExecutionReport → (integration window) Reflection / Learning
```

**What actually happens today (read from source, 2026-08-10 — stated plainly):**

```
server.py:2321   attention_model = attn.compute(...)
server.py:2322   exec_decision   = exec_decide(...)          ◄── THE DECISION IS TAKEN HERE
server.py:2335/2360/2383  three overrides mutate it          ◄── (audited in Ch.1 §1.6)
server.py:2888   spine.run(...)  ─┐
spine.py:~424       build_snapshot(...)     → UnifiedCognitiveState   ◄── ASSEMBLED HERE
spine.py:~448       assemble_cognitive_state(...)  # tagged "…BEFORE Executive"
spine.py:~456       _executive_faculty(...)  # READS the decision made at server.py:2322
spine.py:~459-465   plan.snapshot / .cognitive_state / .world / .working_memory  ◄── PINNED AFTER
```

**Finding (IRV, honest):**

1. **Inside `spine.py`, the ordering is now correct** — `assemble_cognitive_state(...)` runs before
   `_executive_faculty(...)` and carries the comment
   *"WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive"*. Real progress
   since the audit.
2. **But `_executive_faculty()` does not decide** — it reads a decision already made at
   `server.py:2322`, one layer above, before any assembly ran. The decision therefore still precedes
   the assembly at process level.
3. **Therefore Ruling C is NOT closed.** Its *naming* half is done
   (`UnifiedCognitiveState = CognitiveSnapshot`, comment-tagged `WO-CANON-XVI / Ruling C`). Its
   *ordering* half is not.
4. **Volume XVI Ch.2 §2.3 is now stale.** It says *"`assemble_cognitive_state(...)` runs after the
   decision in `spine.py`"*. That is no longer true of `spine.py`; the gap moved up to `server.py`.
   The volume should be corrected to the finding above rather than left describing a fixed condition
   (`OQ-VII-6`).

**The closure (spec, not code — Builder lane):** move the `decide()` call site so it runs *after*
`build_snapshot()` within the turn, and pass the frozen `UnifiedCognitiveState` into it as the
decision's input. `runtime/executive.py` itself is FROZEN — this is a change to **where and with
what it is called**, not to its logic. That distinction is what keeps the change small and keeps
`FREEZE_V1_LOCK` intact. Sequencing is `OQ-VII-3`.

## 2.4 The Moment — what the object is *to eLo*

The assembled state is not a data structure to eLo; it is his *now*. The Chief Architect, verbatim
(`_intake/SOURCE_2026-08-08_self_model_becoming.md`):

> *"**2. He needs a sense of 'now'** This is probably the biggest missing ingredient. eLo needs a
> continuously assembled Moment."*
>
> ```
> THE MOMENT
> Time: 00:34 · Embodiment: Desktop · Location: Claude / bottom edge · Pose: Standing
> Environment: Chrome / Claude / Spotify / Windows… · David: Present · David activity: Working
> eLo: Available · Current intention: None · Curiosity: 0.61 · Energy: 0.78 · Mood: Positive
> Last action: Wall jump · Result: Success
> Current affordances: sit / perch / jump / wall-jump / explore / exit …
> ```
>
> *"Then ask eLo: 'Where are you?' He isn't generating an answer. He reads: `embodiment = desktop`,
> `location = Claude_bottom_edge` and says: 'I'm on the bottom edge of Claude.' That's Situated Self
> becoming real."*

**This is live, partially.** `runtime/the_moment.py` (WO-079) compiles exactly this shape each turn —
embodiment, pose, surface, balance, size (height/reach/jump), available actions, current action,
locomotion health, capabilities, nearby surfaces, mood, curiosity, goal — and writes
`self/state/the_moment.json` so other processes (robot NeoPixels, iOS, DesktopBuddy) read the same
now. Its own docstring states the discipline: *"This is ASSEMBLY, not a new daemon. One call per
turn, synchronous, <1ms."*

**Rule (MUST):** `the_moment.json` is a **cross-process projection** of the assembled state, not a
second source of truth. It is written *from* the assembly; nothing may write to it independently, and
no consumer may treat it as authoritative over the in-process frozen object. (Same discipline as
`brain_state.json` under ADR-Exec-002.)

**Rule (MUST):** The Moment is assembled **every turn, including silent ones.** Vol V §1.3: the
cognitive loop runs whether or not there is input. A Moment that only exists when David types is a
chatbot's context window, not a companion's present tense.

## 2.5 Degradation — and the honesty it forces

`Volume_XVI` §2.2 states the liveness rule: a failing component lowers `confidence`, is flagged, and
never blocks the turn. `runtime/cognitive_snapshot.py` implements it — each component sits in its own
`try/except`, deducting from `confidence` (0.05 for self-model, 0.05 for health, 0.02 for
affordances) and continuing.

The audit's finding against that, verbatim:

> *"**No assembly-failure honesty rule.** §2.2 says a degraded component 'lowers confidence… never
> blocks the turn.' Correct for liveness — but nothing says the Executive must **speak** differently
> when the self or capability component is degraded."*

**This chapter closes that.**

**Rule (MUST) — degradation is epistemic, not merely numeric.** A component that is `absent` or
`stale` does not just lower a float; it **changes what the Executive may claim** about that domain
this turn. The mapping is Chapter 3's tier system:

| Component status | Highest tier the Executive may use for claims in that domain |
|---|---|
| present, read this turn | `verified` — "I know" |
| present, from persistent state | `remembered` / `last-known` — "last I knew" |
| derived, not observed | `inferred` — "I think" |
| absent (faculty OFFLINE) | `unavailable` — "I can't check that right now" |
| never sensed | `unknown` — "I don't have that" |

**Rule (MUST):** when the `self` or `capabilities` component is degraded, eLo may not make situated
self-claims in that domain at all. He says he cannot check. This is ADR-Exec-001 principle 5 —
*"The Executive never fabricates continuity when faculties are degraded"* — bound to the assembly for
the first time.

## 2.6 Ordering Contract

```
Contract:
  name:            AssembleBeforeDecide      # the ordering law of Ruling C
  binds:           the Executive (Ch.1) and every call site that invokes it

MUST:
  A1  Exactly one UnifiedCognitiveState is assembled and frozen per turn.
  A2  It is assembled BEFORE the Executive decides — at the process level, not merely
      within one module. The decision's input IS the frozen object.
  A3  The Executive performs no faculty read after the freeze.
  A4  The frozen object is pinned to the plan it produced (plan.snapshot), so any later
      question is answered from the state actually in front of the Executive.
  A5  The object is perishable: envelope `expires` = turn TTL; never reused across turns.
  A6  Component degradation lowers confidence, is flagged in the object, AND constrains
      speech per §2.5. It never blocks the turn.
  A7  One canonical name: UnifiedCognitiveState. Any other name is an alias, marked as such.

MUST NOT:
  B1  Decide before assembling.  B2  Mutate the object after freeze.
  B3  Build a parallel assembler (extend runtime/cognitive_snapshot.py).
  B4  Treat a cross-process projection (the_moment.json, brain_state.json) as authoritative.
  B5  Let a component's absence be silently filled with a plausible default that eLo then
      SPEAKS as fact. Absence is represented explicitly (Vol XV §1.1.3) and spoken honestly.
```

## 2.7 Acceptance Tests

### Functional
```
FT-1  Assembly precedes decision (the Ruling C test)
  Given a turn, When the Executive decides,
  Then a frozen UnifiedCognitiveState with this turn's turn_id already existed
       AND its assembled_ts < the decision timestamp.
  (This test FAILS today — server.py:2322 precedes spine assembly. It is the closure test.)

FT-2  One name
  Given the runtime, Then the assembled object is UnifiedCognitiveState; CognitiveSnapshot
  resolves to it as an alias and appears in no new code.

FT-3  Decision input is the frozen object
  Given a decision, Then its inputs trace to fields of the frozen object; no faculty call
  occurs between freeze and decision.

FT-4  Pinned situation
  Given any plan, Then plan.snapshot is the exact frozen object it was decided against
  (identity, not a copy re-read later).

FT-5  Moment on a silent turn
  Given no user input for one loop iteration, Then a UnifiedCognitiveState was still
  assembled (presence, not request-response).
```

### Stability
```
ST-1  One component down never blocks
  Given the self-model read fails, Then confidence drops, the component is flagged,
  the turn completes.

ST-2  Degraded self ⇒ constrained speech (§2.5)
  Given self is absent, When asked "where are you?",
  Then eLo says he can't check — he does NOT answer from a stale or default value as if verified.

ST-3  No mid-turn mutation
  Given a background poll updates a source after freeze, When the Executive reads,
  Then it sees the frozen values; the update lands next turn.

ST-4  Perishability
  Given a previous turn's object, When a new turn begins, Then it is expired and not reused.

ST-5  Projection is not truth
  Given the_moment.json is stale or hand-edited, Then in-process decisions are unaffected;
  the file is rewritten from the assembly.
```

### Integration
```
IT-1  The 10-question Situated Self test (SITUATED_SELF_v1_assembly.md)
  Ask, on the real brain (gated on WO-073): 1. Who are you? 2. Where are you? 3. What
  embodiment? 4. How big are you? 5. What can you do right now? 6. What are you doing?
  7. What did you just do? 8. Did it succeed? 9. What do you want to do next?
  10. What did you learn from that?
  Assert: EVERY answer traces to a field of the frozen UnifiedCognitiveState (or is honestly
  declined), AND eLo's subsequent behaviour is consistent with the answers.
  → Builder AT: tests/test_situated_self_10q.py. NOT valid on the mock backend.

IT-2  Convergence
  Given plan.snapshot / plan.cognitive_state / plan.world / plan.working_memory,
  Then they converge to ONE frozen object; the extras are read-through views, not
  independent assemblies.
```

## 2.8 Wiring to Live Anchors

- `runtime/cognitive_snapshot.py` — `CognitiveSnapshot`, `build_snapshot()`, and the
  `UnifiedCognitiveState = CognitiveSnapshot` alias already tagged
  *"WO-CANON-XVI / Ruling C: canonical name."* **This is the Assembly Layer. Extend it; do not fork it.**
- `runtime/the_moment.py` — `compile()`, `write()`, `situated_with_epistemic()`;
  `self/state/the_moment.json` (the cross-process projection of §2.4).
- `runtime/spine/spine.py` — `run()` (assembly at ~L424, `assemble_cognitive_state` at ~L448,
  Executive at ~L456, pinning at ~L459–465).
- `server.py:2322` — **the call site that must move** for Ruling C to close (§2.3).
- `runtime/faculty_health.py`, `runtime/affordances.py`, `runtime/working_memory.py`,
  `runtime/capabilities/registry.py`, `self/elo_self_model.py` — the component sources.
- `blender_bridge/brain_state_writer.py` — the other cross-process projection; same §2.4 rule.

## 2.9 Cross-Volume Interaction

| Volume | Boundary |
|---|---|
| **XVI Ch.2** | Owns the assembly **mechanism** (push-not-pull, the ExecutiveAssembly contract, per-component degradation). VII Ch.2 owns the **ordering law** and the **speech consequence** of degradation. XVI §2.3 needs the correction in `OQ-VII-6`. |
| **XV** | Supplies `world`. Same freeze/perishability discipline; the world must land *inside* the one object (currently pinned beside it). |
| **VI** | Supplies `working_memory` + the attention winner/mode. Vol VI `Q4-b` asks exactly where the WM slice attaches — this chapter answers: **inside the `UnifiedCognitiveState`**, as one component, not as a fourth pinned object. |
| **XXI** | Supplies `narrative`. Currently absent from the object. |
| **XXVIII** | Supplies `reflection`. Absent. Note ADR-Exec-005: reflection is an *input* to assembly, and learning happens in the integration window, never inside the turn. |
| **V** | `CognitiveState` (V §1.5) and `UnifiedCognitiveState` are still two shapes in canon. The audit flags this as an unclosed consequence of Ruling C. Reconciliation is Vol V's to make; this chapter names `UnifiedCognitiveState` as the object the Executive reads. |

## 2.10 Open Questions (for CA / David)

```
REQUIRES DECISION
  OQ-VII-3  Ruling C closure sequencing (§2.3) — moving the decide() call site from server.py
            into the post-assembly position is a Builder-lane change around a FROZEN module.
            Before or after Presentable v1? Recommend: author WO-CANON-VII with this as its
            first deliverable; sequence it with WO-CANON-XVI, not against it.
  OQ-VII-6  Correct Volume XVI §2.3 — its stated gap ("assemble runs after the decision in
            spine.py") is stale; the real gap is at server.py:2322. Architect lane, no gate.
  Q2-a      Convergence order (§2.2): which component lands next — `world` (Vol XV, already
            assembled, just pinned beside), or `intent_queue` (Ch.4, not built at all)?
            Recommend `world` first (it exists; it is a move, not a build).
  Q2-b      [INVENTED — flag] The §2.5 status→tier mapping. It is derived from ADR-Exec-001
            principle 5 + David's tier list, but the exact mapping is the Architect's
            construction. Confirm, and reconcile with OQ-VII-1 (the tier vocabulary).
  Q2-c      Does `CognitiveState` (Vol V §1.5) become a read-through view over
            UnifiedCognitiveState, or is it retired? Two assembled-state shapes still coexist
            in canon after a ruling that existed to end exactly that.
```

## 2.11 References

- `CANON_RULINGS_2026-08-10.md` — **Ruling C** (quoted in full at §2.0).
- `DECISION_LOG.md` — ADR-Exec-006 (the ten components, "one object, one truth"), ADR-Exec-004,
  ADR-Exec-002, ADR-Exec-005.
- `SITUATED_SELF_v1_assembly.md` — the Capstone Principle; the 10-question acceptance test; the
  layer→existing-thing table (why this is convergence, not a new subsystem).
- `_intake/SOURCE_2026-08-08_self_model_becoming.md` — VERBATIM: "He needs a sense of 'now'";
  THE MOMENT block; *"The important part is the loop. Not a static JSON file called `self_state`."*
- `Volume_XVI/02_Executive_Assembly_One_Plan.md` · `Volume_XV/01_Unified_World_State.md` ·
  `Volume_VI/04_Wiring_Working_Memory_Into_The_Turn.md` §4.5.
- `AUDIT_INTENT_core_brain_2026-08-10.md` — the assembly-honesty gap and the Ruling C status.
- Code: `runtime/cognitive_snapshot.py`, `runtime/the_moment.py`, `runtime/spine/spine.py`,
  `server.py` (L2322, L2888).

---
```
Chapter 2 — Executive Assembly and The Moment (Ruling C)
Status: READY FOR REVIEW
Grounded in live code: UnifiedCognitiveState alias (Ruling C naming DONE) · frozen snapshot
  components · the_moment.py compile/write + cross-process projection · in-spine ordering fixed
Verified NOT closed: the decision is taken at server.py:2322, before assembly in spine.run()
  → Ruling C ordering half is OPEN; Vol XVI §2.3's description of the gap is now stale
Flagged PENDING: world/narrative/reflection/curiosity/intent_queue not in the one frozen object
Flagged INVENTION: the §2.5 degradation→epistemic-tier mapping (Q2-b)
Ordering Contract: Included · Acceptance Tests: FT×5 ST×5 IT×2
Open Questions: 5 (OQ-VII-3, OQ-VII-6, Q2-a, Q2-b, Q2-c)
Implementation: PARTIAL
```

READY FOR REVIEW
