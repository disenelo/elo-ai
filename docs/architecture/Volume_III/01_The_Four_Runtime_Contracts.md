---
chapter: 1
title: "The Four Runtime Contracts and the Loop"
volume: III
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL — 4 contracts typed; 1 produced twice, 1 never produced at all
audit_status: OPEN
origin_text: 16_runtime_contracts.md §"The Loop", §"The Four Contracts" (Canonical Reference v2.0, 2026-07-05)
grounded_in: runtime/contracts.py · runtime/spine/spine.py · runtime/spine/plan.py · blender_bridge/* (IRV 2026-08-13)
dependencies:
  - 16_runtime_contracts.md (ORIGIN TEXT — this chapter expands it; it is not superseded)
  - Volume_IV/01_The_Turn_Loop.md (the order these contracts are produced in)
  - Volume_IV/03_CognitiveState_The_Carrier.md (contract 1's slots — owned there, not here)
  - Volume_III/02_Process_and_Boundaries.md (where each contract crosses a process boundary)
  - UNITY_ELOOS_IO_CONTRACT.md (David L3 2026-08-06 — the DOWN/UP channels)
  - adr/ADR-Exec-002 (Single Cognitive Truth) · adr/ADR-Exec-003 (Embodied Truth)
---

# Chapter 1: The Four Runtime Contracts and the Loop

## 1.0 Purpose and relationship to the origin text

`16_runtime_contracts.md` (v2.0, 2026-07-05) defined the loop and the four contracts, and it did
so well enough that Vol XV, Vol V Ch.6 and the spine all took their vocabulary from it. **This
chapter cites it, does not copy it, and adds the four things it lacks:** volume form, the live
reconciliation, ownership/mutation discipline made testable, and the boundary at which the third
contract leaves the process.

**A precedence correction the origin text needs.** It opens:

> *"If code conflicts with this document, the document is right."*

That was the correct instinct in July, when the document led the code. It is no longer
straightforwardly true: the runtime has moved (WO-CANON-VI/XII/XV/XVI all landed after v2.0) and
the document did not. **Volume III's rule:**

```
Where this volume states an OWNERSHIP or MUTATION law → the law is right; divergence is a
  violation with an owner.
Where this volume DESCRIBES what the runtime does → the code is current truth and the
  description is dated, sourced, and re-verified.
Every disagreement is NAMED (§1.7), never silently reconciled in either direction.
```

## 1.1 The loop — as canon states it, and as it runs

**As `16_runtime_contracts.md` states it (quoted, not paraphrased):**

```
Observe → Faculties → CognitiveState → Executive → CognitivePlan → Execution →
EmbodimentState → [subscribers consume independently] → ExecutionReport →
Reflection Faculty → integrate_session() → updated memory/identity → next observation.
```

> *"This is a continuous loop, not a request-response pipeline."*

**As it runs (IRV 2026-08-13):**

```
Observe        ✅  perception (Vol IV §1.2.1) + world (§1.2.2) + working memory (§1.2.3)
Faculties      ✅  Language · Relationship · Capability · System (Vol IV §1.2.5–8)
CognitiveState ⚠️  assembled and frozen at spine.py:448 — 11 of 54 slots written (Vol IV Ch.3)
Executive      🔴  decides at server.py:2322, BEFORE the assembly (Vol IV Ch.2 §2.3)
CognitivePlan  🔴  produced at spine.py:456 — but from spine/plan.py:22, the MUTABLE class
EmbodimentState ⚠️ built at spine.py:503, before the utterance exists (Vol IV Ch.2 §2.6);
                   separately serialised to blender_state.json by embodiment_publisher.py
subscribers    ✅  Unity · voice · robot LED · island — each reads what it needs
ExecutionReport 🔴 NEVER PRODUCED. build_execution_report() exists (spine.py:614); nothing calls it.
Reflection     🔴  no producer feeds it
integrate_session() 🔴 does not exist; compress_session() was never renamed
next observation ⚠️ the loop is entered only from a request path (server.py:2926); there is
                   no idle caller, so it is a request-response pipeline in practice, which is
                   precisely what the origin text says it is not.
```

**The honest headline: the first half of the loop is real and the second half is not.**
Intention is produced every turn; reality is never measured; therefore the delta that the whole
learning architecture rests on is never computed. §1.5 and III-2.

## 1.2 Contract 1 — `CognitiveState`

| | |
|---|---|
| **Purpose** | Everything the runtime knows, before any decision is made. |
| **File** | `runtime/contracts.py:73` — `@dataclass(frozen=True)`, 54 slots |
| **Produced by** | `assemble_cognitive_state()` — `runtime/spine/spine.py:544`, called at `:448` |
| **Consumed by** | The Executive — **and only the Executive** |
| **Mutated by** | Nobody. Frozen at construction. One ruled exception (AC-5, `spine.py:481`). |
| **Freezes at** | construction — Vol IV turn position 9 |

**Origin-text principle, retained verbatim:** *"The Executive never directly queries any faculty.
It receives CognitiveState and reasons from it alone. This is the difference between a system
that 'asks around' and one that receives a complete world model."*

**Live status: ⚠️ the object is real; its completeness is not.** 11 of 54 slots are ever
written; Relationship reaches the plan rather than the state; capability health is lost in the
tuple. **All of this is specified in `Volume_IV/03_CognitiveState_The_Carrier.md` and is not
restated here** — the carrier is the spine's business. Volume III owns only the fact that the
contract exists, is frozen, and has exactly one producer.

**🔴 Ownership violation.** The origin text's *"Consumed by: the Executive — and only the
Executive"* is not enforceable today because the Executive does not read it (Vol IV Ch.2 §2.3).
Nothing consumes contract 1. That is the sharpest possible statement of the Ruling C gap.

## 1.3 Contract 2 — `CognitivePlan`

| | |
|---|---|
| **Purpose** | The single intention produced by the Executive for this turn. |
| **Canonical file** | `runtime/contracts.py:175` — `@dataclass(frozen=True)` |
| **LIVE file** | 🔴 `runtime/spine/plan.py:22` — plain `@dataclass`, **mutable** |
| **Produced by** | `_executive_faculty()` — `spine.py:456` (which transcribes `server.py:2322`) |
| **Consumed by** | every downstream system: LLM context, voice, avatar, desktop, Unity, robot, island |
| **Mutated by** | canon: *nobody, frozen at production*. Live: the spine, **ten times** |
| **Freezes at** | canon: production. Live: **never** |

**🔴 Finding — two `CognitivePlan` classes exist, and the runtime uses the wrong one.**

`spine.py:17` imports `from runtime.spine.plan import CognitivePlan`. After production at `:456`
the plan is mutated at `:459, :461, :463, :465` (pinning), `:470` (enrich), `:481` (register
sync), `:489` (light engine), `:497` (presence), `:503` (embodiment), `:509` (direct response).

`contracts.py:45–47` acknowledges the split and calls it transitional: *"CognitivePlan — expands
runtime/spine/plan.py (v1.x). The v2.0 contract supersedes it gradually."* The origin text's
Convergence Strategy Step 4 names the target: *"Executive outputs `CognitivePlan` (contracts.py)
only."*

**Volume III's ruling on the interim state:**

```
P1  The mutations are TOLERATED only because every one of them is a PROJECTION, never a
    RE-DECISION. Enrichment, light, presence, embodiment and direct-response EXPRESS the
    decision; none revises it. That is the letter of ADR-Exec-002.

P2  Any new mutation that CHANGES what was decided — action, objective, tone-as-decision,
    capability selection — is FORBIDDEN and is a second decider (Invariant #2).

P3  "Tolerated by convention" is a debt, not a design. It is recorded as III-1 with a
    convergence target, not left as an unmarked liberty.

P4  Until convergence, the LIVE contract is spine/plan.py:22 and canon says so plainly.
    The frozen contracts.py:175 class is the TARGET, not a description of the present.
```

**Origin-text principle, retained:** *"Everything downstream reads CognitivePlan. Nobody
re-decides. Voice derives speech from it. Presence derives posture. Unity derives animation. The
same intention becomes different expression across surfaces — but the intention is the same
object."* That principle **is** honoured today. The freeze is not.

## 1.4 Contract 3 — `EmbodimentState`

| | |
|---|---|
| **Purpose** | How `CognitivePlan` becomes visible — across every surface simultaneously. |
| **File** | `runtime/contracts.py:270` — `@dataclass(frozen=True)` |
| **Produced by** | `build_embodiment_state()` — `spine.py:591`, called at `:503` |
| **Serialised by** | `blender_bridge/embodiment_publisher.py` → `blender_bridge/state_writer.py` → `blender/blender_state.json` |
| **Consumed by** | Unity · Desktop Avatar · Robot · Dynamic Island · Voice · Lights — independently, non-blocking |
| **Mutated by** | Nobody. Published once. |
| **Freezes at** | construction |

**This is the contract that crosses a process boundary.** Contracts 1 and 2 live and die inside
the Python process. Contract 3 is the only one a *different* program reads — which is why it,
alone among the four, has a signed interface document (`UNITY_ELOOS_IO_CONTRACT.md`, David L3).
Ch.2 §2.4 owns the boundary; this section owns the object.

**Origin-text principle, retained verbatim:** *"CognitivePlan is internal intention.
EmbodimentState is distributed expression. They are not the same object. The plan is never
exposed to subscribers directly — only the embodiment is."*

**Live mapping (`spine.py:591–611`):** `presence_plan.emotional_state` → `emotional_state`;
`_LED_FROM_EMOTIONAL_STATE` (`spine.py:528–541`, 12 entries → 5 LED colours: teal · white ·
amber · coral · violet) → `robot_led_state`; `dict(presence_plan)` → `motion_command`;
`plan.direct_response` → `response_text` / `display_text` / `tts_text`; UTC ISO →
`published_at`.

**Two live findings:**

- 🔴 **The text fields are published empty on direct-response turns.** `build_embodiment_state`
  runs at `spine.py:503`; `_conversation_faculty` sets `direct_response` at `:509`. Full
  treatment: `Volume_IV/02` §2.6 (invariant I-6). Recorded here because contract 3's own
  guarantee — *"every surface receives the same intention"* — is what breaks.
- ⚠️ **The object and its serialisation are produced by different paths.**
  `build_embodiment_state()` builds the typed object onto the plan; `embodiment_publisher.py`
  independently assembles the plan into `blender_state.json`. `embodiment_publisher.py`'s own
  docstring states the right rule — *"Single authoritative publisher from CognitivePlan →
  blender_state.json… nothing else writes blender_state.json per-turn"* — but the authority runs
  from the **plan**, not from the typed `EmbodimentState`. **Two derivations of one expression
  is the same shape of problem ADR-Exec-002 exists to prevent, one layer down.**
  **Recommendation: the publisher should serialise the typed contract, not re-derive from the
  plan.** Builder lane; recorded, not ordered.

**Staleness discipline (origin text, retained):** each subscriber uses `published_at` and
`sequence_id` to handle staleness; no subscriber blocks another; the publisher never waits.
⚠️ Live: `sequence_id` defaults to `0` and is never incremented (`spine.py:592`, `:608`) — so the
staleness mechanism the origin text specifies is present in the type and inert in practice. Same
root cause as `IV-4` (no turn identity).

## 1.5 Contract 4 — `ExecutionReport`

| | |
|---|---|
| **Purpose** | What actually happened. Observed reality, not intention. |
| **File** | `runtime/contracts.py:342` — `@dataclass(frozen=True)`, fully typed |
| **Produced by** | `build_execution_report()` — `spine.py:614` |
| **Consumed by** | Reflection Faculty → `integrate_session()` |
| **Mutates** | Nothing. **Never touches `CognitivePlan`.** |

**Origin-text principle, retained verbatim:** *"The delta between `CognitivePlan.primary_objective`
and `ExecutionReport.completion_state` is the signal that drives growth… Reality is measured
separately from intention so that learning occurs through integration, not through mutation of
the plan."*

**🔴 Live status: NO PRODUCER. `build_execution_report()` is never called.**

The type is complete — tool results, surface delivery flags (`voice_delivered`, `unity_online`,
`robot_online`, `desktop_online`, `island_online`), interruption, capability gaps, timing, errors,
completion state. `build_execution_report()` even defaults sensibly (`spine.py:618–621`).
**Nothing invokes it in the live turn.**

**Consequences, stated plainly because they are load-bearing elsewhere:**

- The **delta is never computed.** Every statement in the canon about learning from the gap
  between intention and reality currently describes a value that is never produced.
- **ADR-Exec-005 / Vol XXVIII** — *"eLo improves from the consequences of verified actions"* —
  has no mechanism. There are no recorded consequences.
- **Ruling E's rationale is half-unrealised.** The ruling's core argument is that *"without the
  report, the learning loop cannot work at all — eLo cannot get better at routes he was never
  told he took."* The body's ACK does arrive (the sit chain, WO-041). But the ACK lands in the
  next assembly and is then **discarded**, because no `ExecutionReport` collects it into a
  measured outcome. The report arrives and nothing writes it down.
- `integrate_session()` does not exist; `compress_session()` was never renamed (origin text
  Convergence Step 7).

**This is III-2, and it is the highest-leverage unbuilt thing in Volume III's scope.**

## 1.6 The ownership register — producer · consumer · mutator · freeze

The discipline the origin text states in prose, made into a table that a test can read.
**Chapter 3 (not yet written) turns this into an enforceable check.**

| Contract | Sole producer | Legitimate consumers | May mutate | Freezes at | Live? |
|---|---|---|---|---|---|
| `CognitiveState` | `spine.py:544` | the Executive **only** | nobody (AC-5 excepted) | construction | ⚠️ produced; **not consumed** (Ch.1 §1.2) |
| `CognitivePlan` | the Executive, once | all downstream, read-only | canon: nobody · live: the spine ×10 | canon: production · live: never | 🔴 §1.3 |
| `EmbodimentState` | `spine.py:591` | all surfaces, independently | nobody | construction | ⚠️ §1.4 |
| `ExecutionReport` | `spine.py:614` | Reflection · `integrate_session()` | nobody | construction | 🔴 never produced |

**The four ownership MUSTs:**

```
O1  ONE PRODUCER. Each contract has exactly one construction site. A second constructor is
    a fork of the truth, not a convenience.
O2  NO NON-OWNER MUTATION. A component that did not produce a contract may not alter it.
    This is what stops future faculties writing into state they do not own.
O3  PROJECTION, NOT REVISION. Downstream may DERIVE new objects from a contract; it may
    never write back into one. (ADR-Exec-002: no modality invents private state.)
O4  REALITY NEVER MUTATES INTENTION. ExecutionReport informs the NEXT cognition through
    integration; it never edits the plan it reports on. (Origin text; ADR-Exec-005.)
```

## 1.7 The disagreement register — canon vs. code

Every divergence, named. **Silent reconciliation in either direction is forbidden.**

| # | Canon (origin text / `contracts.py`) | Live code | Current truth | Owner |
|---|---|---|---|---|
| 1 | `CognitiveState` consumed by the Executive alone | the Executive never reads it (`server.py:2322`) | **code** | Builder · IV-1 |
| 2 | `CognitivePlan` frozen at production | `spine/plan.py:22` mutable, mutated ×10 | **code** | Builder · III-1 |
| 3 | Relationship contributes to `CognitiveState` | it contributes to the plan, post-decision | **code** | CA · IV-3a |
| 4 | `ExecutionReport` produced after every turn | never produced | **code** | Builder · III-2 |
| 5 | `integrate_session()` replaces `compress_session()` | rename never happened | **code** | Builder |
| 6 | subscribers handle staleness via `sequence_id` | always `0` | **code** | Builder · IV-4 |
| 7 | *"a continuous loop, not a request-response pipeline"* | entered only from a request path | **code** | Vol IV Ch.5 (unwritten) |
| 8 | `prompt_builder.py` → `context_composer.py` (Step 5) | not renamed | **code** | Builder · cosmetic |
| 9 | `state_writer.py` becomes the `EmbodimentState` publisher (Step 6) | `embodiment_publisher.py` was added and derives from the **plan**, not the contract | **code** | Builder · §1.4 |
| 10 | *"Passive Awareness (Immediate Fix)"* — one line in `prompt_builder.py` | unconfirmed; and `CognitiveState.graph_context` is never written at all | **unknown** | **III-4 — needs David** |

**Seven of ten Convergence Strategy steps in the origin text are unstarted.** That is not a
failure to report as a scandal — it is a four-week-old plan measured honestly. What matters is
that it is now measured at all.

## 1.8 Acceptance Tests

### Functional

```
FT-III-1a  One producer per contract
  Static check: exactly one construction site for each of the four contracts.
  FAILS IF: a second assembler/publisher/report-builder appears. (O1.)

FT-III-1b  Non-owners do not mutate
  For each contract, assert no write occurs outside its producer, except the enumerated
  projection mutations on CognitivePlan (Vol IV Ch.1 §1.3 positions 11–15) and AC-5.
  (O2, O3.)

FT-III-1c  Every turn produces all four
  Run one turn. Assert a CognitiveState, a CognitivePlan, an EmbodimentState AND an
  ExecutionReport were produced.
  STATUS TODAY: FAILS — no ExecutionReport (§1.5). This is III-2's closure test.

FT-III-1d  Document and contracts.py agree on shape
  Assert every contract field named in this chapter exists in runtime/contracts.py, and
  every field in contracts.py is either described here or listed as retired.
  (The Vol IV I-8 discipline, applied to shapes rather than order.)
```

### Stability

```
ST-III-1e  Reality never mutates intention
  Given an ExecutionReport recording a failure, assert the CognitivePlan it reports on is
  byte-identical before and after. (O4.)

ST-III-1f  Subscriber independence
  Given one surface offline (Unity down), assert every other surface still receives the
  EmbodimentState and the turn completes. No subscriber blocks another.

ST-III-1g  Staleness is detectable
  Given two consecutive publishes, assert sequence_id strictly increases and published_at
  advances.
  STATUS TODAY: FAILS — sequence_id is always 0 (§1.4).
```

### Integration

```
IT-III-1h  The full loop, once
  Observe → CognitiveState → CognitivePlan → EmbodimentState → subscribers →
  ExecutionReport → Reflection → integrate_session().
  Assert every arrow is traversed exactly once and the delta between
  plan.primary_objective and report.completion_state is computed and stored.
  STATUS TODAY: FAILS after "subscribers". This is the loop-closure test and it is the
  single test whose passing would mean Volume III is real.
```

## 1.9 Open Questions

```
REQUIRES DECISION
  III-1  CognitivePlan convergence: frozen contracts.py version vs live mutable
         spine/plan.py:22 (§1.3). Recommend converging WITH the Ruling C call-site move
         (IV-1) — same code path, one intervention instead of two.
  III-2  ExecutionReport has no producer (§1.5). Recommend a Builder WO; not blocking for
         Presentable v1, blocking for anything called learning.
  III-3  Should embodiment_publisher.py serialise the typed EmbodimentState rather than
         re-derive from the plan (§1.4)? Recommend yes — two derivations of one expression
         is ADR-Exec-002's problem one layer down. Architect lane to spec; Builder to build.
  III-4  The embedded TODO at 16_runtime_contracts.md:221 (§1.7 row 10). NEEDS DAVID +
         Builder confirmation of whether it shipped.
```

## 1.10 References

- **`16_runtime_contracts.md` — ORIGIN TEXT.** §"The Loop", §"The Foundational Principle",
  §"The Four Contracts", §"Convergence Strategy", §"Renamed Concepts", §"Success Criteria",
  and the embedded TODO at line 221. Cited throughout; **not superseded**.
- `Volume_IV/01_The_Turn_Loop.md` (order) · `Volume_IV/02_*` (I-6, I-7) ·
  `Volume_IV/03_CognitiveState_The_Carrier.md` (contract 1's slots — owned there)
- `Volume_III/02_Process_and_Boundaries.md` (where contract 3 crosses out of the process)
- `UNITY_ELOOS_IO_CONTRACT.md` · `Volume_XI/01_*` (the motor half)
- `adr/ADR-Exec-002_Single_Cognitive_Truth.md` · ADR-Exec-003 · ADR-Exec-005
- Code: `runtime/contracts.py:73,:175,:270,:342` · `runtime/spine/plan.py:22` ·
  `runtime/spine/spine.py:448,:456,:503,:528–541,:544,:591,:614` ·
  `blender_bridge/embodiment_publisher.py` · `blender_bridge/state_writer.py`

---

```
Chapter 1 — The Four Runtime Contracts and the Loop
Status: READY FOR REVIEW
Origin text: 16_runtime_contracts.md — cited and expanded, never copied or replaced
Precedence rule stated: laws bind the code; descriptions defer to the code; every
  disagreement is NAMED (§1.7, 10 rows)
🔴 Contract 2 exists twice (frozen canon class vs live mutable class) — P1–P4 rule the interim
🔴 Contract 4 has NO PRODUCER — the loop's second half does not run; the learning delta is
  never computed (III-2)
⚠️ Contract 3 is derived twice (typed object vs blender_state.json serialisation) and its
  staleness mechanism (sequence_id) is inert
Ownership register: O1–O4 · Acceptance Tests FT×4 ST×3 IT×1
Open Questions: 4 (III-1 … III-4)
```

READY FOR REVIEW
