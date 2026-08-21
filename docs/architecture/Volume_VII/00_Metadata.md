---
volume: VII
title: "Executive Cortex"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  ARCHITECTURE_BIBLE.md (Volume VII scope) + DECISION_LOG ADR-Exec-001…006 +
  _intake/SOURCE_2026-08-08_self_model_becoming.md (VERBATIM) +
  _intake/SOURCE_2026-08-10_brain_body_brain_loop.md (VERBATIM) +
  SITUATED_SELF_v1_assembly.md + CANON_RULINGS_2026-08-10.md (Ruling C)
implementation: PARTIAL (runtime/executive.py live + FROZEN; the_moment.py + decision_journal.py live; assembly ORDER and dual-intent queue PENDING; live branch order + ingress boundary CANONIZED 2026-08-21 via card 0074)
Provenance: [ENGINEERING]
audit_status: POSITION_STATED (branch order + ingress boundary canonized 2026-08-21 in Ch.1 §1.3.1/§1.3.2/§1.6.1; L3 ratification pending David per card 0074 DOD; behaviour changes remain separate ruled cards)
canonical_path: docs/architecture/Volume_VII/
dependencies:
  - Volume V (CONTRACTS.md — envelope/lifecycle/base contract; Ch.1 — Cognitive Core, the eight laws, CognitiveState/CognitivePlan)
  - Volume VI (Working Memory & Attention — Executive-owned per D-G; Ch.4 §4.4 defers the Executive contract HERE)
  - Volume XVI (Multi-Faculty Coordination — Ch.1/Ch.2/Ch.4 each disclaim ownership: "a role of the Executive (Vol VII), NOT a new decider")
  - Volume XV (Unified World State — the `world` slice the Executive reads)
  - ADR-Exec-001 (Verified Executive Authority) · ADR-Exec-002 (Single Cognitive Truth) · ADR-Exec-003 (Embodied Truth / Situated Cognition / Affordance Before Action) · ADR-Exec-004 (Situated Self) · ADR-Exec-005 (Learning Through Verified Consequences) · ADR-Exec-006 (Executive Assembly)
  - CANON_RULINGS_2026-08-10.md Ruling C (assemble BEFORE decide; one name `UnifiedCognitiveState`)
priority: "Audit finding: THE hole — three volumes cite Vol VII as an authority that did not exist (AUDIT_INTENT_core_brain_2026-08-10.md §VOLUME VII)"
last_review: 2026-08-21
next_review: TBD
---

# Volume VII — Executive Cortex

> **Executive Authority** — the Executive is the sole authority for externally visible
> assertions. (`ARCHITECTURAL_PRINCIPLES.md`, Runtime Invariant #2.)

> *"The language model is the VOICE through which eLo expresses his assembled self, **not the
> place the self exists.**"* — `SITUATED_SELF_v1_assembly.md`, the Capstone Principle
> (David + Chief Architect, 2026-08-08).

## Why this volume exists

The `AUDIT_INTENT_core_brain_2026-08-10.md` finding, verbatim:

> **"1. Spec'd? NO. THE VOLUME DOES NOT EXIST.** No folder, no metadata, no chapters, no WO. …
> Volume XVI has quietly absorbed two of them (assembly in Ch.2, conflict resolution in Ch.4) while
> explicitly disclaiming ownership — both chapters label their contract *'a role of the Executive
> (Vol VII), NOT a new decider.'* **Coordination canon is standing in for cognition canon.**"

Three volumes defer to Vol VII (`Volume_VI` §4.6, `Volume_XVI` §1.5 and §4.4; also
`Volume_V/CONTRACTS.md` §1 and all three `Volume_XX` chapters). They pointed at
`09_executive_faculty.md`, which read in full: *"STATUS: PENDING — to be written in a dedicated
session."* Everything the Executive owns from David's verbatim material — epistemic tiers, the
dual-intent queue, the Situated Self Retrieval invariant, "why did I do that?", and the
`brain > body > brain` loop — had no canonical home. This volume is that home.

## Scope (from `ARCHITECTURE_BIBLE.md`, Volume VII)

> *"**VII — Executive Cortex.** Decision making, scheduling, conflict resolution, task
> orchestration, resource allocation, safety, interruptions, thinking modes, goal management,
> executive policies."*

**What Volume VII owns:**

| Owned here | Chapter |
|---|---|
| Executive Authority — the sole decider; one `CognitivePlan` per turn; the Conversation Action Layer | Ch.1 |
| Why the Executive is deterministic and the LLM is the voice, not the seat of self | Ch.1 |
| Ruling C — `UnifiedCognitiveState` assembled BEFORE the decision; the ordering contract | Ch.2 |
| The Moment — what the Executive must hold before it may think, act, or speak | Ch.2 |
| Epistemic tiers ("I know" / "I think" / "I don't have that"); the speech gate; ADR-Exec-001 enforcement | Ch.3 |
| The Situated Self Retrieval invariant | Ch.3 |
| The dual-intent queue (conversational vs body/action) + arbitration | Ch.4 |
| The decision journal — "why did I do that?", traced to real state, never confabulated | Ch.4 |
| `brain > body > brain` — the closed loop; the body never decides | Ch.5 |

**What Volume VII does NOT own (deliberate, Check-Before-Build):**

| Not here | Owner |
|---|---|
| The mechanics of composing the assembled object (push-not-pull, degradation, contract) | **Volume XVI Ch.2** — Vol VII states the *ordering law*; XVI states the *assembly mechanism* |
| The conflict-resolution ORDER + cross-embodiment projection | **Volume XVI Ch.4** (arbitration is an Executive *role*; the spec lives there and stays there) |
| The Faculty Bus envelope, routing, priority | **Volume XVI Ch.3** / `Volume_V/CONTRACTS.md §2` |
| The working-memory object and the attention competition | **Volume VI** (Executive-*owned* per D-G, but VI is the authoritative spec) |
| The world model | **Volume XV** |
| Cost tiers / provider escalation | **Volume XX** (a *policy* of the Executive) |
| Long-term memory, personality drift, narrative identity | **Volumes VIII · X · XXI** |
| RL / adaptation | **Volume XXVIII** (ADR-Exec-005 — sits *after* Verify, beneath Executive Authority) |

Volume VII is the **cognition** volume for the decider. Volume XVI is the **coordination** volume
for many faculties. Where they touch, XVI mechanises what VII legislates; neither restates the other.

## Anchors in live code (verified 2026-08-10 by reading the files)

| Anchor | What is actually there | Status |
|---|---|---|
| `runtime/executive.py` | `decide()` — the single deterministic decision function. Conversation Action Layer with nine actions (ANSWER · BUILD · CONNECT · CELEBRATE · REFLECT · GROUND · CHALLENGE · WITNESS · SILENCE) in a stated priority order; five tones; `_MAX_SENTENCES` per tone; the POSITIVE EMOTION RULE; loop-protection override. | **LIVE · FROZEN** (`FREEZE_V1_LOCK.md`; per `runtime/spine/executive_faculty.py` docstring: *"The identity/personality layer lives in runtime/executive.py and is protected by FREEZE_V1_LOCK.md. This module wraps it — never replaces it."*) |
| `runtime/cognitive_snapshot.py` | `CognitiveSnapshot` frozen dataclass (WO-052) + `UnifiedCognitiveState = CognitiveSnapshot` alias, comment-tagged *"WO-CANON-XVI / Ruling C: canonical name."* | **LIVE · PARTIAL** — Ruling C's *naming* half is done |
| `runtime/spine/spine.py` | `build_snapshot()` at the top of `run()`; `assemble_cognitive_state(...)` now runs **before** `_executive_faculty(...)`, tagged *"WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive"*; both pinned onto the one plan. | **LIVE · PARTIAL** — see the ordering gap below |
| `runtime/spine/executive_faculty.py` | Wraps the frozen decision into one `CognitivePlan`; computes the `EmotionalVector`. Docstring: *"The only entity permitted to make decisions… Produces ONE CognitivePlan."* | **LIVE** |
| `runtime/the_moment.py` (WO-079) | Compiles a per-turn verified self snapshot; writes `self/state/the_moment.json`; **carries an epistemic tier vocabulary** (`verified · inferred · last-known · live · unknown`) and a `[SITUATED SELF]` prompt block instructing *"Never invent; if a field is unknown say so — never claim unverified state."* | **LIVE** — the epistemic tiers exist in code |
| `self/decision_journal.py` (WO-082) | Append-only `self/journals/decision_journal.jsonl`; records `trigger`, `alternatives_rejected`, `overrides`, `outcome`, per-action reliability; `explain_last()` — *"Reads the real trace — never fabricates a motive."* | **LIVE** — "why did I do that?" exists |
| `runtime/faculty_health.py` · `runtime/affordances.py` · `runtime/working_memory.py` · `runtime/capabilities/registry.py` | Health registry, affordance table, WM + attention competition, capability registry — all read by the snapshot. | **LIVE** |

**Verified ordering gap (Ruling C is NOT closed).** `runtime/executive.py::decide()` is invoked from
`server.py:2322`, **before** `spine.run()` is called at `server.py:2888` — and the
`UnifiedCognitiveState` is assembled *inside* `spine.run()`. So although the ordering inside
`spine.py` is now correct (assembly at ~L448, Executive at ~L456), the actual decision was already
taken one layer up. `spine._executive_faculty()` reads a decision handed to it via
`attention["_exec_decision"]`; it does not re-decide. **Net: eLo still decides before he assembles.**
Ch.2 §2.3 states this as the outstanding build. Volume XVI Ch.2 §2.3's phrasing
(*"`assemble_cognitive_state(...)` runs after the decision in `spine.py`"*) is now **stale** and
should be corrected to the above — flagged as `OQ-VII-6`.

**Verified post-decision override sites.** `server.py` mutates `exec_decision` after `decide()`
returns, at three places: stabilisation-forced (L2335, sets `overridden_by_safety`), WO-020 Seam-A
imperative routing (L2360, sets `overridden_by_routing`), and WO-029 greeting family (L2383). These
are *recorded* honestly (the journal reads exactly those fields) but they are, structurally, edits to
the one decision made outside the Executive module. Ch.1 §1.6 defines the rule that legitimises or
retires them. Flagged as `OQ-VII-2`.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V7-CH01 | Chapter 1 | The Executive and One Plan Per Turn | READY FOR REVIEW |
| ELO-V7-CH02 | Chapter 2 | Executive Assembly and The Moment (Ruling C) | READY FOR REVIEW |
| ELO-V7-CH03 | Chapter 3 | Epistemic Tiers and Verified Speech | READY FOR REVIEW |
| ELO-V7-CH04 | Chapter 4 | The Intent Queue and "Why Did I Do That?" | READY FOR REVIEW |
| ELO-V7-CH05 | Chapter 5 | brain > body > brain — The Closed Loop | READY FOR REVIEW |

**Deliberately deferred to a later pass (named so they are not silently lost):** thinking modes,
interruption policy, goal management, and scheduling/resource allocation — all four are in the
Bible's Volume VII scope line and none has canon. Ch.1 §1.7 records them as the Ch.6–Ch.8 backlog
rather than inventing David's calls now.

## Definition of Done

- [x] Executive Authority + one-plan-per-turn stated as law, grounded in `runtime/executive.py` (Ch.1)
- [x] The Conversation Action Layer specified from the live nine-action table (Ch.1)
- [x] "The LLM is the voice, not the seat of self" canonised (Ch.1 §1.5)
- [x] Ruling C ordering law + `UnifiedCognitiveState` as the one name (Ch.2)
- [x] The Moment defined as the Executive's pre-decision precondition (Ch.2)
- [x] Epistemic tiers + the speech gate + the Situated Self Retrieval invariant (Ch.3)
- [x] Dual-intent queue + arbitration + the decision journal (Ch.4)
- [x] `brain > body > brain` canonised out of WO-086 so it survives that WO's closure (Ch.5)
- [x] Faculty contract + lifecycle + envelope + acceptance tests per chapter
- [x] **Live A/B/C/D branch order (28 dispatch points) enumerated in Ch.1 §1.3.1** (card 0074 test #1)
- [x] **Position on the routing order stated in Ch.1 §1.3.2** — live order IS canon; docstring priority retired (card 0074 test #3)
- [x] **Ingress-boundary rule stated in Ch.1 §1.6.1** — the three-part legitimacy test for pre-Executive early returns (card 0074 test #2, rule form)
- [ ] Open questions answered by CA / David (see below) — specifically OQ-VII-8 (David L3 ratifies §1.3.2 position)
- [ ] `WO-CANON-VII` authored and dispatched
- [ ] Architecture Agent can implement without inventing (pending REVIEW)
- [ ] Audit can mark COMPLETE

## Open Questions (for CA / David — flagged, NOT decided here)

```
OQ-VII-1  (Ch.3) Epistemic tier VOCABULARY MISMATCH — David's verbatim names six tiers
          (Verified · Inferred · Remembered · Possible · Unknown · Unavailable);
          runtime/the_moment.py ships five, and they are not the same five
          (verified · inferred · last-known · live · unknown — no "possible",
          no "unavailable"; "live" is not in David's list). One vocabulary must win.
          Recommend: David's six as canon, with `live` folded into `verified` and
          `last-known` = `remembered`. NOT decided here — David's call.

OQ-VII-2  (Ch.1) The three post-decision override sites in server.py (safety-stabilisation,
          Seam-A routing, WO-029 greeting). Are they (a) legitimate Executive policy that
          should move INSIDE the one decision, or (b) technical debt around a frozen module
          to be retired when FREEZE_V1_LOCK lifts? Recommend (a)-then-(b): declare them
          Executive policy now, fold them in when the freeze lifts. Owner: David + CA.

OQ-VII-3  (Ch.2) Ruling C closure sequencing — moving decide() to AFTER assembly means moving
          it from server.py into the spine. That is a Builder-lane change to a FROZEN module's
          call site. Confirm this is in scope before Presentable v1, or explicitly after it.

OQ-VII-4  (Ch.4) Dual-intent arbitration ORDER is INVENTED here (safety/boundary > external
          > commitment > internal urge > curiosity). Nothing in canon fixes it. Requires
          ratification. Touches D-PRESENCE, so it is arguably David L3.

OQ-VII-5  (Ch.5) Where is the reflex line? WO-086's Designer audit already draws one
          ("neutral aliveness jitter stays a Unity reflex; anything with intent/valence goes
          via the brain") and leaves EloEmojiReact as REVIEW. Ch.5 §5.4 proposes the general
          test; confirm it, and close the EmojiReact verdict.

OQ-VII-6  (Metadata) Volume XVI Ch.2 §2.3 now reads FALSE against the code ("assemble_cognitive_state
          runs after the decision in spine.py" — it no longer does; the real gap moved up to
          server.py). Correct XVI §2.3 to the verified finding above. Architect lane, no gate.

OQ-VII-7  (Scope) Thinking modes · interruptions · goal management · scheduling/resource
          allocation are Bible-scoped to VII and unwritten. Confirm they belong in Vol VII
          chapters 6–8 rather than being absorbed by XVI/XX, before anyone drafts them.

OQ-VII-8  (Ch.1 §1.3.2) The live A/B/C/D branch order (§1.3.1) has been stated as the
          canonical dispatch order; docstring priority at executive.py:149 retired from
          canon. Card 0074 DOD calls for a single David L3 ratification of this position.
          Awaiting David's rule — behaviour does not change until then, canon description
          holds now.

OQ-VII-9  (Ch.1 §1.3.1 B20) The `:227` duplicate `_SHORT_AFFIRM` branch is verified
          unreachable dead code. Behaviour-neutral cleanup card required; NOT authorised
          by 0074. Owner: David to authorise the cleanup card.

OQ-VII-10 (Ch.1 §1.6.1) The ingress-boundary rule (three-part legitimacy test) is stated.
          The classification of the 29 specific pre-Executive early returns as
          (a)/(b)/(c) is FINDING C1 audit work and remains NOT AUTHORISED as of 2026-08-21
          (David 2026-08-18: "Audit first. Correction second."). This OQ tracks the
          finding's own gate; VII does not re-open the finding here.
```

## Implementation status (grounded — do not overstate)

- **LIVE:** deterministic `decide()` with the nine-action Conversation Action Layer
  (`runtime/executive.py`, FROZEN); one `CognitivePlan` per turn
  (`runtime/spine/executive_faculty.py`); `UnifiedCognitiveState` name + frozen snapshot
  (`runtime/cognitive_snapshot.py`); epistemic tier markers + `[SITUATED SELF]` prompt gate
  (`runtime/the_moment.py`, WO-079); decision journal with `alternatives_rejected` and
  `explain_last()` (`self/decision_journal.py`, WO-082); faculty-health-gated capability list.
- **PARTIAL:** Ruling C — the *name* landed and the in-spine order was fixed, but the decision is
  still computed a layer above the assembly (`server.py:2322` vs `spine.run()`); the snapshot
  realises self / health / attention / body / intentions / affordances / perception-scope but the
  ADR-Exec-006 `narrative`, `reflection`, and `curiosity` components are not in the same frozen
  object.
- **PENDING (no code found):** the dual-intent queue (`pending_intentions` in the snapshot holds
  only body intents — today literally only `("sit","cursor")`; there is no internal-urge queue and
  no arbitration); a normative epistemic gate on *speech* (tiers annotate the prompt block; nothing
  blocks a claim); the `brain > body > brain` UP-relay rule as an enforced invariant (WO-086 is
  OPEN and awaiting David's greenlight); thinking modes; interruption policy; goal management.

- **CANONIZED 2026-08-21 (card 0074):** the live A/B/C/D branch order of `_conversation_action()`
  + pre-CAL + post-CAL + loop-guard (28 dispatch points) enumerated in Ch.1 §1.3.1 with
  source-line anchors; docstring priority at `executive.py:149` retired from canonical status in
  §1.3.2; B20 (`:227`) verified unreachable dead code; the three-part ingress-boundary legitimacy
  test stated in §1.6.1 as a corollary of ADR-Exec-001. **Behaviour unchanged** by this
  ratification (0074 boundary); L3 ratification of §1.3.2 position remains OQ-VII-8.
