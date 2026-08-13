---
chapter: 2
title: "Ordering Guarantees and Invariants — What the Sequence Promises"
volume: IV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL — 5 of 8 invariants hold at runtime; 2 are VIOLATED; 1 is unenforced
audit_status: OPEN
grounded_in: runtime/spine/spine.py · server.py · runtime/contracts.py (IRV 2026-08-13)
dependencies:
  - Volume_IV/01_The_Turn_Loop.md (the order these invariants constrain)
  - CANON_RULINGS_2026-08-10.md Ruling C (assemble before decide) · Ruling E (shared ownership + mandatory reporting)
  - adr/ADR-Exec-006 (D4 — assembly precedes decision) · adr/ADR-Exec-002 (single cognitive truth) · adr/ADR-Exec-001 (verified speech)
  - Volume_VII/02_* (the ordering law) · Volume_VII/05_* (brain > body > brain) · Volume_XVI/02_* · Volume_XV/01_* · Volume_VI/*
  - ARCHITECTURAL_PRINCIPLES.md (Invariants #1 #2 #3 #4 #5; Embodied Truth)
---

# Chapter 2: Ordering Guarantees and Invariants

## 2.0 Purpose

Chapter 1 records the order. This chapter states what that order **promises** — and makes each
promise **falsifiable**.

An ordering guarantee that lives only as a sequence of lines is not a guarantee; it is a
coincidence that has held so far. Volume XV can say *"assembled once, at the top of the turn,
before faculties reason"* only because `spine.py:366` happens to sit above `spine.py:429`. Move
one, and the sentence becomes false with nothing to notice.

Each invariant below carries four things:

1. **The invariant** — one sentence, in MUST form.
2. **Who depends on it** — the named volumes/ADRs whose core guarantee is *this* ordering.
3. **Live status** — ✅ holds / 🔴 violated / ⚠️ unenforced, with the file+line evidence.
4. **How to test it** — a test that **fails if the sequence changes**. This is the mechanism
   whose absence let the drift happen.

**Precedence:** unlike Chapter 1, this chapter **is** law. Where the code diverges from an
invariant here, the code is a **violation with an owner**, not an amendment.

---

## 2.1 I-1 — PERCEPTION BEFORE WORLD STATE

> **MUST.** `PerceptionResult` is produced and frozen before `LiveWorldState` is assembled. The
> world is assembled *from* perception; it never re-senses.

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **Volume XII** | Perception *transforms* raw sensation; it does not decide and it does not assemble. It must therefore complete first, or the world has nothing transformed to copy. |
| **Volume XV §1.4** | *"Assembly reads, never triggers: it does not kick off a screenshot or a network call inline."* The world can only *read* if perception has already *sensed*. |
| **Volume XV §1.2.2** | The Spatial Faculty MUST NOT re-sense — geometry reaches it *through* the world object and Vol XII. That is only possible if perception precedes assembly. |
| **Vol VII §5.1.4** | Every body perception relays UP and lands in the *next* assembly. Perception-then-assembly is the shape of "lands in the assembly." |

**Live status: ✅ HOLDS.** `spine.py:357` (`_perception = _perceive()`) precedes `spine.py:366`
(`_assemble_world(..., perception=_perception)`), and the perception object is passed as an
argument — a *structural* dependency, not merely a positional one, which is the stronger form.

**⚠️ Attached gap.** Perception is not pinned to the plan (Ch.1 §1.2.1 — the comment at
`spine.py:462` promises it; `:463` stores only `plan.world`). The invariant holds; the
*evidence* of it is discarded at the end of the turn. Nothing downstream can answer "what did
eLo actually perceive this turn?"

**How to test it**

```
FT-IV-1a  Structural order
  Read runtime/spine/spine.py. Assert the first call to perceive_from_live_state(
  precedes the first call to assemble_world_state(.
  FAILS IF: the two lines are swapped.

FT-IV-1b  Structural dependency (the stronger test)
  Assert assemble_world_state is invoked with a perception= argument bound to the value
  produced by the perception call — not None, not a re-read.
  FAILS IF: someone "simplifies" by having the world sense for itself.

ST-IV-1c  Perception absent
  Given perceive_from_live_state() raises, Then _perception is None, the world still
  assembles, and the turn completes. No fabricated perception appears downstream.
```

---

## 2.2 I-2 — WORLD STATE BEFORE ATTENTION / WORKING MEMORY, AND BOTH BEFORE ANY FACULTY

> **MUST.** `LiveWorldState` is frozen before the attention competition runs, and both the world
> and the frozen `WorkingMemory` exist before the first faculty (Language, position 5) executes.

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **Volume XV §1.1.1** | *"One world per turn… No faculty re-queries a sensor mid-turn. If it isn't in `LiveWorldState`, the faculty does not know it this turn."* Only true if the world is complete before faculties run. |
| **Volume XV §1.1.2 / FT-4 / ST-3** | *"The world does not change underneath a turn"*; two faculties reading the frontmost app read the identical value. |
| **Volume VI · Ruling B** | Working memory's competition is the **sole** attention driver. If a faculty ran before the competition, it would reason against pre-competition attention — a second answer to "what is eLo attending to." |
| **Volume XVI §2.1.1** | *"If a fact is not in the assembled state, the Executive does not know it this turn."* The assembly can only carry world + WM if both were built first. |
| **Volume VII §2.1.3** | No mid-decision reach-back, no late sensor read. |

**Live status: ✅ HOLDS.** `spine.py:366` (world) → `:398` (`run_attention_competition`) →
`:406–416` (WM re-frozen) → `:429` (Language, the first faculty). The ordering comments at
`:361` and `:370` state the intent; the line order delivers it.

**How to test it**

```
FT-IV-2a  Top-of-turn ordering
  Assert, in spine.py source order:
    assemble_world_state(  <  run_attention_competition(  <  _language_faculty(
  FAILS IF: any faculty is hoisted above world or working-memory assembly.

FT-IV-2b  One world, read twice, identical
  Run one turn with two faculties that both read world.desktop.active_app.
  Assert byte-identical values, even with a background poll firing mid-turn.

FT-IV-2c  One attention winner
  Assert exactly one call to run_attention_competition() per turn, and that the
  AttentionState carried in CognitiveState is that call's result — not a value derived
  from core/attention.py directly. (Ruling B: supplier, not rival decider.)

ST-IV-2d  No mid-turn mutation
  Mutate the world source after freeze. Assert faculties still read the frozen snapshot.
```

---

## 2.3 🔴 I-3 — ASSEMBLY BEFORE DECISION  *(the one that is currently VIOLATED)*

> **MUST.** Exactly one `UnifiedCognitiveState` is assembled and frozen **before** the Executive
> decides, **at process level — not merely within one module**, and the frozen object **is** the
> decision's input.

**Source of law:** ADR-Exec-006 **D4** and **Ruling C** (David L3, 2026-08-10), verbatim:

> *"The unified cognitive state is assembled **BEFORE** the Executive decides… Current code
> assembles* after *the decision — that makes the 'self' a post-hoc description instead of the
> thing that chose. Rationale: the self is ASSEMBLED, not generated — assembly must precede
> choice or eLo is narrating, not being."*

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **ADR-Exec-006 D1/D3/D4** | One object, one truth; push not pull; assembly precedes choice. |
| **ADR-Exec-002** | The Executive ASSEMBLES and FREEZES, then all expression derives from that one frozen state. |
| **Volume VII §2.1.1 / A2** | *"A decision taken before assembly is, by canon's own definition, narration."* |
| **Volume XVI §2.1.1–2.1.3** | One assembled state → one decision → one plan. |
| **Volume VII §2.5** | Degradation is *epistemic*: a degraded component constrains what the Executive may **claim**. Impossible if the Executive never saw the assembled object. |
| **Invariant #5 (Situated Self)** | *"Every decision begins from a VERIFIED model of itself."* |

**Live status: 🔴 VIOLATED.** IRV 2026-08-13:

```
server.py:2321   attention_model = attn.compute(...)
server.py:2322   exec_decision   = exec_decide(...)     ◄── THE DECISION. Nothing assembled yet.
      ⋮          (~600 lines)
server.py:2925   _attention_with_exec["_exec_decision"] = exec_decision   ◄── smuggled in
server.py:2926   _spine_run(raw, ..., attention=_attention_with_exec, ...)
      spine.py:424   build_snapshot(...)               ◄── assembles (too late)
      spine.py:448   assemble_cognitive_state(...)     ◄── assembles (too late)
      spine.py:456   _executive_faculty(...)           ◄── does NOT decide:
                       spine.py:162 → exec_out = attention.get("_exec_decision", {})
                                      it TRANSCRIBES the decision from :2322
```

**Three precise statements, so this is not over- or under-claimed:**

1. **Inside `spine.py` the order is correct** — `:448` precedes `:456`, under the comment
   *"WO-CANON-XVI / ADR-Exec-006: Assemble unified cognitive state BEFORE Executive."*
2. **`_executive_faculty()` is not the Executive.** The Executive is `runtime/executive.py:262
   decide()`, invoked at `server.py:2322`. `_executive_faculty` copies its output onto the plan
   (`spine.py:161–175`).
3. **Therefore the assembled state is a description of the decision, not an input to it.** The
   in-file ordering is correct and **not load-bearing**.

**The `_exec_decision` transport is itself the tell.** `server.py:2922–2924` documents it as a
*"SPINE CONVENIENCE — transport convenience only… Not an `AttentionSnapshot` field."* A decision
riding inside an attention dict is a decision that has no legitimate seat in the turn order.

**The closure (spec, Builder lane — not the Architect's to write):** move the `decide()` call
site so it runs **after** `assemble_cognitive_state()` inside `spine.run()`, taking the frozen
object as its input; delete the injection (`server.py:2925`) and the read-back (`spine.py:162`)
with it. `runtime/executive.py` itself is under `FREEZE_V1_LOCK` — **this is a change to where
and with what it is called, not to its logic.** Everything `server.py` does with `exec_decision`
between `:2322` and `:2925` (stabilisation override, imperative override) moves with it or reads
from the returned plan. Sequencing is `IV-1` / `OQ-VII-3`. **Needs David.**

**How to test it — and the trap to avoid**

```
🔴 THE TRAP — do not accept this as the test.
  tests/test_canon_xvi_coordination.py AT-1 locates the first assemble_cognitive_state(
  call in spine.py and asserts it precedes the Executive. That assertion is TRUE and the
  invariant is VIOLATED. It is a true assertion about the wrong file. A source-order check
  scoped to one module can never detect a cross-module ordering violation.

FT-IV-3a  Assembly precedes decision — at PROCESS level (the closure test)
  Instrument the turn. Assert the frozen UnifiedCognitiveState carrying THIS turn's turn_id
  existed, and its assembled_ts < the timestamp at which executive.decide() was entered.
  STATUS TODAY: FAILS. This is the Ruling C closure test. (= Vol VII FT-1.)

FT-IV-3b  The decision's input IS the frozen object
  Assert executive.decide() receives the assembled object as an argument.
  STATUS TODAY: FAILS — decide() receives attention_model (server.py:2322).

FT-IV-3c  No decision transport through the attention channel
  Assert no key named "_exec_decision" (or any decision payload) appears on the attention
  dict passed into spine.run().
  STATUS TODAY: FAILS by construction (server.py:2925). This test going green is the
  single clearest signal that Ruling C has closed.

FT-IV-3d  Exactly one decider
  Assert exactly one call to executive.decide() per turn, anywhere in the process, and
  exactly one _executive_faculty() call in the spine. (Invariant #2 — no committee.)
  STATUS TODAY: PASSES.
```

---

## 2.4 I-4 — MEMORY READ BEFORE, MEMORY WRITE AFTER

> **MUST.** All memory reads for a turn complete before the decision. The only memory write
> occurs after the response exists. A turn never reads memory it wrote in the same turn.

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **Invariant #7 (Memory Ownership)** | *"One permanent-memory writer."* One write point is what makes one writer checkable. |
| **ADR-Exec-005 · Vol XXVIII** | Learning happens in the **integration window**, never inside the turn. A mid-turn write is a mid-turn learn. |
| **Vol VII §2.1.4** | *"Reality Informs, Never Mutates"* — consequences apply to the *next* assembly. |
| **`16_runtime_contracts.md`** | `ExecutionReport → Reflection → integrate_session()` — reality feeds forward, never sideways. |
| **Ruling F** | Style learning is permitted **because** identity is re-asserted from state each turn (Ch.3 §3.6). A same-turn write-then-read would let learned content re-enter the same turn's identity assertion. |

**Live status: ✅ HOLDS — with a boundary caveat.**

- **Read:** `_memory_pack` / `_vault_ctx` are built in `server.py` upstream of `:2321` and
  handed in as `spine.run(..., memory_pack=_vault_ctx)` (`server.py:2927`). The spine performs
  **no memory read of its own** — verified: no memory import in `spine.run()`.
- **Write:** `update_session()` (`spine.py:514–520` → `conversation_matrix.push`) is called at
  `server.py:3346`, **after** `response` exists. It is the spine's only write.
- **Caveat:** because the read happens in the prologue (§1.1), Volume IV cannot today assert the
  read discipline over the whole turn — only that the spine adds no reads. That is the same
  boundary problem as `IV-3`; closing IV-1 closes both.

**How to test it**

```
FT-IV-4a  No memory read inside the spine
  Static check: runtime/spine/spine.py imports no memory module inside run(). Memory
  arrives only via the memory_pack parameter.
  FAILS IF: a faculty starts reading memory directly mid-turn.

FT-IV-4b  Single write, and it is last
  Instrument the memory writer. Assert exactly one write per turn, and its timestamp is
  after the response was produced.

ST-IV-4c  Write-then-read is impossible within a turn
  Write a distinctive marker via update_session(). Assert it appears in turn N+1's
  memory_pack and NOT in turn N's assembled state.
```

---

## 2.5 I-5 — ACK BEFORE BELIEF  *(Ruling E — the body reports, and the brain believes only what was reported)*

> **MUST.** The brain does not believe an action occurred until the body reports it. A commanded
> state that is not ACKed is **pending**, never true. Belief precedes speech; the ACK precedes
> belief. **Movement that is not reported did not happen** as far as the brain is concerned.

**Source of law — Ruling E, David L3 2026-08-10, verbatim:**

> *"Shared ownership, the body does the movement, all of it is connected, so it's fine to make
> for the Ruling, it needs to communicate."*

and, as the ruling states it:

> *"**THE BINDING OBLIGATION — the body must COMMUNICATE.** … whatever the body does, it
> **reports UP**: the goal it pursued · the route it actually took · which legs it used ·
> whether it arrived · whether it fell/missed · the cost. **Movement that is not reported did
> not happen** as far as the brain is concerned."*

**Why this is an ORDERING invariant and belongs in Volume IV.** Ruling E is usually read as an
ownership rule — body owns movement, brain owns intent, one connected system, not
master/servant. That half lives in Volume III §2 and Volume XI. But the ruling's *binding
obligation* is a statement about **sequence**: report → assemble → believe → speak. It
constrains the turn order, so the turn order's volume must carry it.

**The chain (Vol VII §5.5, ADR-Exec-003):**

```
intention → capability check → command (DOWN) → body acts → ACK (UP) → pose update →
self-model update → THEN speech
```

- Before ACK: *"I'm attempting to sit…"* — tier `POSSIBLE`.
- After ACK: *"I'm sitting with you."* — tier `VERIFIED`.
- On fail/timeout: *"I tried to sit, but my movement system didn't confirm it."*

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **Ruling E** | The report is what makes it one brain — *"the brain doesn't need to micro-plan every step to be one mind — it needs to KNOW."* |
| **ADR-Exec-001 / Invariant #3** | Verified Speech: speech is a sensor, not an actuator. |
| **ADR-Exec-003 · Embodied Truth** | *Thought → Decision → Body → Confirmation → Belief → Speech.* |
| **Vol VII §5.1.6, §5.5, Ch.3** | ACK is what promotes a claim to VERIFIED. |
| **Vol XI §1.1.3** | Never speak-then-hope-the-body-follows. |
| **Vol XXVIII / ADR-Exec-005** | *"Without the report, the learning loop cannot work at all — eLo cannot get better at routes he was never told he took."* An unreported movement is not a verified consequence, so it is not learnable. |

**The two ordering sub-rules Volume IV owns:**

- **I-5a — the ACK lands in the NEXT assembly, never mid-turn.** An ACK is a report, and
  reports go UP through the normal channel. *"There is no special ACK back-door that skips
  assembly"* (Vol VII §5.5). This is I-2 and I-3 applied to the body: a mid-turn ACK injection
  would be a late sensor read.
- **I-5b — belief is written from the ACK, not from the command.** The self-model updates on
  confirmation. `pose_tier: "verified" if pose_acked else "last-known"`
  (`runtime/the_moment.py`) is correct *because* of this ordering, not decoratively.

**Live status: ⚠️ PARTIAL / UNENFORCED.**

- ✅ The ACK chain exists for the sit path (WO-041): `BodySchema` carries `pending_sit`,
  `sit_pending_since`, `queued_intent` (`runtime/cognitive_snapshot.py`), and `pending_sit`
  is threaded into the spine as a parameter (`spine.py:326`, consumed at `:424`). So the spine
  **does** carry pending-vs-confirmed body state into the assembly, in the right position.
- 🔴 **Nothing enforces the reporting obligation.** Vol VII §5.6 states it plainly: *"The
  UP-relay rule is not enforced anywhere. There is no test, no bus rule, and no review gate."*
  Volume IV adds the ordering test below; the *coverage* rule (every perception relays) remains
  Vol VII's and is still unbuilt.
- 🔴 **The robot body is not in the loop at all yet.**

**How to test it**

```
FT-IV-5a  Pending until ACKed
  Command sit. Before the ACK, assert the assembled state shows the pose pending and no
  VERIFIED claim is sayable. After the ACK, assert verified.
  FAILS IF: belief is written at command time.

FT-IV-5b  The ACK enters through assembly, not a side door
  Inject an ACK mid-turn. Assert it does NOT alter the current turn's frozen state, and
  DOES appear in turn N+1's assembly.
  FAILS IF: anyone adds a fast path "so the response feels snappier".

FT-IV-5c  Unreported movement did not happen (Ruling E, literally)
  Have the body execute a movement and suppress its report. Assert the brain's next
  assembled state contains no record of it, AND eLo does not claim it.
  FAILS IF: the brain infers the movement from having commanded it.

ST-IV-5d  Timeout is honest, not silent
  Command, then withhold the ACK past timeout. Assert the state stays pending and eLo
  reports the non-confirmation. Never a claim, never silence.
```

---

## 2.6 🔴 I-6 — EXPRESSION AFTER UTTERANCE  *(the second live violation)*

> **MUST.** `EmbodimentState` is built **after** the turn's utterance is resolved. What is
> published to the surfaces must contain what eLo actually says.

**Who depends on it**

| Dependant | The guarantee it rests on |
|---|---|
| **ADR-Exec-002 (Invariant #4)** | *"Every word, posture, voice cue and action derives from ONE verified executive state"* — and every outward expression references the **same** snapshot. An `EmbodimentState` whose text is empty while the chat panel shows a response is two states, not one. |
| **`16_runtime_contracts.md` §3** | Subscribers (Voice, Unity, Island, Robot) read `tts_text`, `response_text`, `display_text` from `EmbodimentState`. |
| **Vol VII §5.6** | The DOWN leg: one plan → `EmbodimentState` → surfaces. |
| **Vol XI §1.1.2** | New content is a **field inside an existing channel**; surfaces must be able to trust those fields. |

**Live status: 🔴 VIOLATED.**

```
spine.py:503   plan.embodiment_state = build_embodiment_state(plan)   ← runs FIRST
spine.py:509   plan = _conversation_faculty(plan)                     ← sets direct_response
spine.py:599   resp = getattr(plan, "direct_response", "") or ""      ← reads it, too early
```

On every turn the Conversation Faculty handles — greetings, thank-yous, farewells, identity
questions, system confirmations, Rasta affirmations — `EmbodimentState.response_text`,
`.display_text` and `.tts_text` are published **empty**. The emotional/LED/motion fields are
correct (they derive from `presence_plan`, resolved at `:497`); only the utterance is missing.

**This is not a canon question. It is a two-line reorder** (`spine.py:503` must follow `:509`),
and it is silently degrading every direct-response turn. Flagged to David as **IV-2**. The
Architect does not touch product code (Rule #3) — this is the Builder's.

**How to test it**

```
FT-IV-6a  Structural order
  Assert, in spine.py source order: _conversation_faculty(  <  build_embodiment_state(.
  STATUS TODAY: FAILS.

FT-IV-6b  Published expression carries the utterance
  Run a pure-greeting turn. Assert plan.direct_response is non-empty AND
  plan.embodiment_state.tts_text == plan.direct_response.
  STATUS TODAY: FAILS (tts_text == "").

FT-IV-6c  One state, not two
  Assert the text the chat panel renders and the text in EmbodimentState are the same
  string for every turn type (direct, system, LLM). (ADR-Exec-002.)
```

---

## 2.7 I-7 — FREEZE DISCIPLINE: WHAT IS FROZEN, AND WHEN

> **MUST.** Once a contract is frozen it is not mutated. Contributions happen before the freeze;
> consequences apply to the next turn.

**What is actually frozen in the live turn**

| Object | Frozen? | Evidence |
|---|---|---|
| `PerceptionResult` | ✅ yes | `perception_faculty.py:157` frozen dataclass |
| `LiveWorldState` | ✅ yes | `live_world_state.py:129` |
| `WorkingMemory` / `AttentionState` | ✅ yes | `working_memory.py:85` / `:61`; re-frozen at `spine.py:406–416` |
| `UnifiedCognitiveState` (snapshot) | ✅ yes | `cognitive_snapshot.py:41`, alias `:97` |
| `CognitiveState` | ⚠️ frozen, **one documented exception** | `contracts.py:73`; re-created via `dataclasses.replace` at `spine.py:481` |
| `EmbodimentState` | ✅ yes | `contracts.py:270` |
| `ExecutionReport` | ✅ yes | `contracts.py:342` |
| **`CognitivePlan`** | 🔴 **NO** | `runtime/spine/plan.py:22` is a plain `@dataclass`; mutated at `spine.py:459, :461, :463, :465, :470, :481, :489, :497, :503, :509` |

**🔴 Two `CognitivePlan` classes exist.** `contracts.py:175` declares a **frozen** one;
`spine/plan.py:22` declares a **mutable** one. **The spine imports the mutable one**
(`spine.py:17`). `16_runtime_contracts.md` says the plan is *"frozen at production"* and
`contracts.py:35` says *"produced once by Executive. Never modified."* Neither is true of the
object the runtime actually uses. **Code is current truth: the live plan is mutable and is
mutated ten times after the decision.**

Volume IV's position: this is **tolerable only because every mutation is a projection, never a
re-decision** — enrichment, light, presence, embodiment and direct-response all *express* the
decision rather than revise it. That is the letter of ADR-Exec-002. But "tolerable by
convention" is exactly the state Volume IV exists to end. **Recorded as a gap with an owner
(Volume III Ch.1 owns contract ownership and mutation).**

**The AC-5 exception, ruled.** `spine.py:478–483` re-creates the frozen `CognitiveState` to
back-fill `register` after `enrich()` supplied a richer value. **Volume IV permits this as a
narrow, named exception** on three conditions, and forbids its generalisation:

```
E1  It uses dataclasses.replace — a NEW frozen object, never in-place mutation.
E2  It only fills a field that was EMPTY ("" / None). It never overwrites a value the
    assembly established. (Live code satisfies this: `and not plan.cognitive_state.register`.)
E3  It is a SYNC, not a decision — it copies a value already on the plan.

Any fourth case must be a canon amendment, not a second precedent.
```

**How to test it**

```
FT-IV-7a  Frozen means frozen
  For each frozen contract, assert attribute assignment raises FrozenInstanceError.

FT-IV-7b  No overwrite in the AC-5 path
  Assemble with a non-empty register, then run enrich with a different one.
  Assert the assembled value survives. (E2.)

FT-IV-7c  The replace-count is bounded
  Static check: exactly ONE dataclasses.replace on a frozen contract in spine.py.
  FAILS IF: a second precedent is added without a canon amendment.

FT-IV-7d  One plan class
  Assert the spine's CognitivePlan and contracts.CognitivePlan are the same class, or that
  the divergence is recorded in Volume III with an owner and a convergence date.
  STATUS TODAY: FAILS — two classes, divergence now recorded here and in Vol III §1.
```

---

## 2.8 I-8 — THE DOCUMENT AND THE CODE AGREE  *(the meta-invariant)*

> **MUST.** The turn order stated in `Volume_IV/01_The_Turn_Loop.md` and the turn order
> executed by `runtime/spine/spine.py` are the same order. A change to one without the other
> fails the build.

**Who depends on it: every volume in this chapter, and the canon as a system.**

This is the invariant whose *absence* produced the hole Volume IV exists to fill. Volumes XII,
XV, VI and XVI state guarantees that are true only because of a line order nothing checked.
Writing this chapter does not fix that; **this test does.**

**How to test it**

```
IT-IV-8  Canon-vs-code ordering check  ← the highest-value test in the canon
  Machine-read the ordered position table from Volume_IV/01 §1.3 (the one-block order).
  For each position, locate its call site in runtime/spine/spine.py.
  Assert: (a) every position exists, (b) they appear in the stated relative order,
          (c) no UNLISTED faculty call has been inserted between two listed positions.
  FAILS IF: a faculty is added, removed, or moved without amending Volume IV.

  Design notes for the owning seat:
    - Match on call sites, not line numbers. Line numbers drift (Ch.1 §1.6); order does not.
    - (c) is the important clause. (a) and (b) catch reordering; only (c) catches the
      quiet insertion of a new decider into the middle of the turn.
    - Failure message MUST name the invariant broken (I-1 … I-7), not just "order changed" —
      the point is to tell the next engineer WHICH volume they just falsified.
    - This test is Volume IV's Definition-of-Done item and is NOT yet built.
```

---

## 2.9 The register — status of all eight invariants

| # | Invariant | Status | Evidence | Owner of the gap |
|---|---|---|---|---|
| **I-1** | Perception before world | ✅ holds | `spine.py:357` → `:366` | — (⚠️ perception not pinned) |
| **I-2** | World + WM before faculties | ✅ holds | `:366` → `:398` → `:429` | — |
| **I-3** | **Assembly before decision** | 🔴 **VIOLATED** | `server.py:2322` vs `spine.py:448` | Builder · IV-1 / OQ-VII-3 · **needs David** |
| **I-4** | Memory read before / write after | ✅ holds | prologue read; `server.py:3346` write | — (boundary caveat, IV-3) |
| **I-5** | **ACK before belief** (Ruling E) | ⚠️ partial · unenforced | sit chain live; no relay test; robot absent | Builder + Designer · Vol VII §5.6 |
| **I-6** | **Expression after utterance** | 🔴 **VIOLATED** | `spine.py:503` vs `:509` | Builder · IV-2 · two-line reorder |
| **I-7** | Freeze discipline | ⚠️ holds with one ruled exception; plan is mutable | `contracts.py` vs `spine/plan.py:22` | Volume III Ch.1 |
| **I-8** | Document and code agree | 🔴 **not built** | no such test exists | Builder · Vol IV DoD |

**Five hold. Two are violated at runtime. One is the test that would have caught both.**

## 2.10 Open Questions (for CA / David)

```
REQUIRES DECISION
  IV-1   Ruling C closure sequencing (§2.3). Moving decide() into the spine, post-assembly,
         around a FREEZE_V1_LOCK module. Before or after Presentable v1?
         Recommend: after; first deliverable of WO-CANON-IV; sequenced WITH WO-CANON-XVI.
         (Duplicates OQ-VII-3 — one decision, recorded in both homes.)

  IV-2   The empty-EmbodimentState defect (§2.6). Not a canon question, but it is
         identity-adjacent: every surface is handed an empty utterance on direct turns.
         Recommend: Builder WO, ahead of IV-1. Two-line reorder.

  IV-7a  [INVENTED — flag] The AC-5 exception conditions E1–E3 (§2.7) are the Architect's
         construction, derived from what the live code happens to do. Confirm them as the
         rule, so the next back-sync is judged by rule rather than precedent.

  IV-7b  Do the two CognitivePlan classes converge, and when? (§2.7 FT-IV-7d.) The frozen
         contracts.py version is canon; the mutable spine/plan.py version is what runs.
         Recommend: Volume III Ch.1 owns the answer; it is a convergence date, not a rewrite.

  IV-8   Who owns building IT-IV-8 (§2.8)? It is the mechanism that prevents this entire
         class of drift recurring anywhere in the canon, and it is currently nobody's.
         Recommend: Builder, as part of WO-CANON-IV, before the Ch.4/Ch.5 chapters.
```

## 2.11 References

- `CANON_RULINGS_2026-08-10.md` — **Ruling C** (§2.3, quoted), **Ruling E** (§2.5, quoted), Ruling B, Ruling F
- `adr/ADR-Exec-006_Executive_Assembly_The_Moment.md` D1–D7 · `adr/ADR-Exec-002_Single_Cognitive_Truth.md` · `adr/ADR-Exec-001` (via Vol VII Ch.3)
- `ARCHITECTURAL_PRINCIPLES.md` — Invariants #1–#7; Embodied Truth; Reality Before Narrative
- `Volume_VII/02_*` (ordering law · A1–A7 · FT-1) · `Volume_VII/05_*` (L1–L5 · N1–N5 · M1–M5 · §5.5 · §5.6)
- `Volume_XVI/02_*` §2.3 (the same finding, with now-stale line numbers) · `Volume_XV/01_*` §1.1, §1.4 · `Volume_XI/01_*` §1.1
- `tests/test_canon_xvi_coordination.py` — **AT-1 is the trap named in §2.3**: a true assertion about the wrong file
- Code: `runtime/spine/spine.py` · `runtime/spine/plan.py:22` · `runtime/contracts.py` · `runtime/executive.py:262` · `server.py:2322,:2925,:2926,:3346`

---

```
Chapter 2 — Ordering Guarantees and Invariants
Status: READY FOR REVIEW
Invariants: 8 (I-1 … I-8), each with dependants, live status, and a failing-on-reorder test
Live status: 5 hold · 2 VIOLATED (I-3 assemble-before-decide · I-6 expression-after-utterance)
             · 1 unenforced (I-5 ACK/report) · I-8 (canon-vs-code check) NOT BUILT
Encodes Ruling E as an ORDERING invariant: report → assemble → believe → speak;
  "movement not reported did not happen" is FT-IV-5c
Names the TRAP: tests/test_canon_xvi_coordination.py AT-1 passes while I-3 is violated
Flagged INVENTION: the AC-5 exception conditions E1–E3 (IV-7a)
Open Questions: 5 (IV-1, IV-2, IV-7a, IV-7b, IV-8)
```

READY FOR REVIEW
