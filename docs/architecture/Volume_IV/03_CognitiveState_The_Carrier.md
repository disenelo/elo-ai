---
chapter: 3
title: "CognitiveState — The Carrier"
volume: IV
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL — the object is live and frozen; 11 of its 54 slots are ever written
audit_status: OPEN
grounded_in: runtime/contracts.py:73–164 · runtime/spine/spine.py:544–588 (IRV 2026-08-13)
dependencies:
  - Volume_IV/01_The_Turn_Loop.md (which position writes which slot)
  - Volume_IV/02_Ordering_Guarantees_and_Invariants.md (I-3 assembly-before-decision; I-7 freeze discipline)
  - adr/ADR-Exec-002 (Single Cognitive Truth — the single-carrier law)
  - adr/ADR-Exec-006 (the ten components of the assembled state)
  - CANON_RULINGS_2026-08-10.md Ruling F (identity asserted by the spine, never sourced from learned weights)
  - Volume_III/01_The_Four_Runtime_Contracts.md (the contract's shape and ownership)
  - Volume_VII/02_* §2.2 (what The Moment composes) · Volume_XVI/02_* §2.2
---

# Chapter 3: `CognitiveState` — The Carrier

## 3.0 Purpose

Chapter 1 records *when* things happen. Chapter 2 records what that order *promises*. This
chapter records *what travels* — the one object that carries everything the faculties learned to
the point where a decision is made.

**The law, in one sentence:** there is exactly one carrier between the faculties and the
Executive, every faculty contributes to it, and the Executive reads it and nothing else.

That is ADR-Exec-002 (Single Cognitive Truth) expressed as a data structure. Everything in this
chapter is a consequence of it.

## 3.1 The single-carrier rule

**3.1.1 One carrier.** `CognitiveState` (`runtime/contracts.py:73`) is the sole object passed
from the faculty layer to the decision. There is no second channel, no side-band dict, no
"convenience" parameter carrying cognition.

> 🔴 **Violated today, and this is where the violation is visible.** The Executive's decision
> travels *into* the spine as `attention["_exec_decision"]` (`server.py:2925` → `spine.py:162`),
> documented in-code as a *"SPINE CONVENIENCE… transport convenience only."* A decision riding
> in the attention dict is precisely the second channel this rule forbids. See Ch.2 §2.3.

**3.1.2 The Executive never queries a faculty.** It receives the carrier and reasons from it
alone. `16_runtime_contracts.md`: *"This is the difference between a system that 'asks around'
and one that receives a complete world model."* ADR-Exec-006 D3: **push, not pull.**

**3.1.3 Frozen after assembly.** `@dataclass(frozen=True)` (`contracts.py:73`). Contributions
happen before the freeze; consequences apply to the next turn. One narrow, ruled exception
(AC-5) — Ch.2 §2.7.

**3.1.4 Absence is explicit, never fabricated.** A slot no faculty wrote holds its declared
default. A default is **not** a reading. Anything that speaks from a default is claiming a fact
that no faculty established (Vol XV §1.1.3; ADR-Exec-001).

> This is the sharpest live risk in the whole volume. §3.3 shows that **43 of 54 slots are
> always at their defaults** — `desktop_activity: "unknown"`, `expression_posture: "warm"`,
> `familiarity: 0.55`, `trust: 0.60`, `interaction_pace: "normal"`. Those are not observations.
> They are placeholders, and they are indistinguishable at the read site from readings.

**3.1.5 The carrier is context, not command.** It informs the decision; it never *is* the
decision. An assembled state that *implies* an action has not taken it (Vol VII §2.1.5).

## 3.2 Where the carrier is built

```python
# runtime/spine/spine.py:544
def assemble_cognitive_state(language, memory_result, attention, capabilities,
                             vault_result, prior_state,
                             world_state=None, working_memory=None):
    ...
    return CognitiveState(...)       # spine.py:576–588 — frozen
```

Called once per turn, at position 9 (`spine.py:448`), **before** `_executive_faculty()` at
`:456`. Within `spine.py` this ordering is correct; at process level it is not (Ch.2 §2.3).

**Assembly confidence** (`spine.py:561–567`) is the object's honesty field:

```
conf = 1.0
  − 0.15   if attention is empty
  − 0.05   if capabilities is empty
  − 0.05   if memory_result is None
  clamped to [0.0, 1.0]
```

It degrades; it never blocks the turn. But note what it does **not** measure: it says nothing
about world, working memory, relationship, environment or session — including cases where those
are `None`. **Confidence is currently a three-signal proxy for a fifty-four-slot object.**

## 3.3 The slot register — who writes, who reads

`runtime/contracts.py:73–164` declares **54 slots** across fourteen groups.
`assemble_cognitive_state()` writes **11**. The remaining **43 always hold their defaults.**

### Slots that are actually written (11)

| Slot | Declared | Written by | Written at | Source |
|---|---|---|---|---|
| `raw_input` | `:84` | Language (pos. 5) | `spine.py:577` | `language["original"]` |
| `intent_signal` | `:87` | Language | `:578` | `language["intent"]` |
| `register` | `:88` | Language, **then AC-5 back-sync** | `:579`, `:481` | `language["register"]` (always `""`), then `plan.register` |
| `social_signal` | `:89` | Language | `:580` | `language["social"]` |
| `momentum` | `:103` | Attention supplier (prologue) | `:581` | `attention["momentum"]` |
| `valence` | `:104` | Attention supplier (prologue) | `:582` | `attention["valence"]` |
| `assembly_confidence` | `:164` | the assembler | `:583` | computed, §3.2 |
| `capability_candidates` | `:138` | Capability (pos. 7) | `:584` | tuple built at `:569–572` |
| `world_state` | `:157` | World (pos. 2) | `:585` | frozen `LiveWorldState` |
| `working_memory` | `:160` | Working Memory (pos. 3) | `:586` | frozen `WorkingMemory` |
| `attention_state` | `:161` | Working Memory (pos. 3) | `:587` | `getattr(wm, "attention")` at `:574` |

### Slots that are declared and never written (43)

| Group | Slots | Declared | Live state |
|---|---|---|---|
| **Language (rest)** | `normalised_input`, `language_meaning`, `is_question`, `is_emotional`, `topic_signals` | `:85–92` | 🔴 never written — **`language["meaning"]` is computed at `spine.py:429` and passed to Capability and System, but never lands on the carrier.** The Executive cannot see the cleaned, typo-repaired meaning. |
| **Memory** | `high_priority_memories`, `medium_priority_memories`, `vault_context`, `active_projects` | `:95–98` | 🔴 never written. `memory_result` is an argument (`:546`) used **only** for the confidence deduction at `:566`. Memory reaches the LLM through `server.py`'s prompt path, never through the carrier. |
| **Attention (rest)** | `attention_scores`, `emotional_context` | `:101–102` | 🔴 never written, though `attention["emotional_context"]` is read at `spine.py:397` for the distress signal. |
| **Relationship** | `person_id`, `relationship_type`, `familiarity`, `trust`, `expression_posture` | `:108–112` | 🔴 never written — §3.4. Defaults are `"david"`, `"creator"`, `0.55`, `0.60`, `"warm"`. |
| **Conversation Matrix** | `recent_turns`, `conversation_depth`, `last_action`, `last_topic`, `open_threads` | `:115–119` | 🔴 never written. `conversation_matrix` is live (`spine.py:517`) but writes only on `update_session()`, and nothing reads it back into the carrier. |
| **Human Interaction Matrix** | `interaction_energy`, `interaction_pace`, `brevity_signal`, `curiosity_signal`, `distress_signal` | `:122–126` | 🔴 never written — even though **distress is computed** at `spine.py:397` and used for the attention budget. The signal exists and is discarded. |
| **Environment** | `active_app`, `active_window`, `browser_tab`, `desktop_activity`, `graph_context`, `current_time`, `current_date` | `:129–135` | 🔴 never written. **Superseded in practice by `world_state`** (Vol XV's eleven domain slices carry all of this). See §3.5 — these are dead slots, and `graph_context` is the subject of `16_runtime_contracts.md`'s embedded TODO. |
| **Capability (rest)** | `tool_availability`, `enriched_context` | `:139–140` | 🔴 never written. |
| **Presence** | `presence_observation`, `dwell_app` | `:143–144` | 🔴 never written. |
| **Creative Context** | `creative_mode_signal`, `active_topic_depth` | `:147–148` | 🔴 never written. |
| **Session Metadata** | `session_id`, `turn_number`, `session_anchor`, `session_word_count` | `:151–154` | 🔴 never written. **`turn_number` never advancing is the same gap as `IV-4`** — the runtime has no turn identity. |

### The two findings this table produces

**Finding A — the contract advertises a completeness it does not deliver.** A faculty author
reading `contracts.py` sees fifty-four typed slots and reasonably concludes the Executive knows
all of it. It knows eleven. **Code is current truth: `CognitiveState` is a mostly-empty
envelope.**

**Finding B — the capability tuple loses the health it was built to carry.** `spine.py:569–572`
builds each entry as `(c.get("name") or c.get("id","unknown"), c.get("available", True),
c.get("latency_ms", 0))`, but `_capability_faculty` emits `id`, `category`, `score`,
`requires_confirmation`, `health` (`spine.py:92–98`) — no `name`, no `available`, no
`latency_ms`. The `or` rescues the id. **Every candidate is therefore reported
`available=True, latency_ms=0`, including ones whose real `health` is `OFFLINE` or
`AUTH_REQUIRED`.** The Executive's own gate at `spine.py:196` reads the *raw* candidate dict and
does check health — so the live behaviour is correct — but anything reading the **carrier**
sees every capability as available. That is a fabricated availability claim inside the object
whose whole purpose is single truth. **Owner: Builder. Not a canon question.**

## 3.4 Relationship does not reach the carrier

`rel_analyse()` runs at `spine.py:435` (position 6) and its result goes to
`executive_faculty.enrich(plan, relationship, attention)` at `spine.py:470` — **after** the
Executive. It is not an argument to `assemble_cognitive_state()` (`spine.py:448–451`).

**Canon-vs-code:** `16_runtime_contracts.md` lists *"Relationship Faculty"* in the
`CognitiveState` assembly chain, and `contracts.py:106–112` reserves five slots for it.
**Neither is realised.** Relationship reaches the *plan*, not the *state*, and it arrives after
the decision.

**Why this matters beyond tidiness.** Cognitive Principle *"Relationships influence expression.
Never identity"* (`17_cognitive_principles.md`) is *accidentally* satisfied by this arrangement
— relationship can only shape expression because it physically cannot reach the decision. But it
is satisfied by an accident of wiring, not by a rule. If relationship is later added to the
carrier (as `contracts.py` anticipates), the principle stops being structural and becomes a
convention the Executive must honour.

**Open — `IV-3a`, for the CA:** *should* relationship contribute to the carrier at all?

- **Option A — leave it post-decision.** The principle stays structural. Cost: the Executive
  cannot modulate a *decision* (e.g. WITNESS vs ADVISE) by trust or familiarity, only its
  expression. `17_cognitive_principles.md`'s *"Witness before advising"* arguably needs it.
- **Option B — add it to the carrier**, and make "expression only, never identity" an explicit
  Executive constraint with a test.

**Architect recommendation: Option B**, because Option A's guarantee is invisible — nothing
tells the next engineer that moving one line breaks a cognitive principle. Volume III Ch.1 owns
the ownership question; the *cognitive* question is the CA's.

## 3.5 Two carriers coexist — the convergence debt

`CognitiveState` is not the only assembled object riding the turn. Four do (`spine.py:459–465`):

```
plan.snapshot         UnifiedCognitiveState  (cognitive_snapshot.py:41, alias :97)
plan.cognitive_state  CognitiveState         (contracts.py:73)
plan.world            LiveWorldState         (live_world_state.py:129)
plan.working_memory   WorkingMemory          (working_memory.py:85)
```

Vol VII §2.2 names it exactly: *"Four objects that should be one is the residual shape of the
problem Ruling C exists to end."*

**The overlap is not theoretical.** `CognitiveState`'s Environment group (`:129–135`) and Vol
XV's `LiveWorldState` describe the same eleven domains. The world object is populated and the
Environment slots are dead. `CognitiveState`'s Attention group and the `AttentionState` inside
`WorkingMemory` are two representations of one competition — one live, one dead.

**The rule Volume IV states, and does not itself resolve:**

```
C1  Convergence is by EXTENSION of runtime/cognitive_snapshot.py — never a parallel
    assembler. (Vol XVI §2.8; Vol VII §2.2; CHECK-BEFORE-BUILD.)
C2  A slot superseded by a richer object is RETIRED with a pointer, not left declared and
    empty. A declared-but-never-written slot is indistinguishable from a broken faculty.
C3  Until convergence lands, `CognitiveState` is the CARRIER and `UnifiedCognitiveState` is
    the ASSEMBLED SELF. They are not synonyms. Volume IV describes the carrier; Volume VII
    Ch.2 and Volume XVI Ch.2 describe the assembled self.
C4  ADR-Exec-006's ten components (self · world · capabilities · health · working memory ·
    narrative · intent queue · reflection · curiosity · confidence) are the convergence
    TARGET. Volume IV does not re-specify them (Vol VII Ch.2 owns that list).
```

**Open — `IV-3b` (= Vol VII `Q2-c`):** does `CognitiveState` become a read-through view over
`UnifiedCognitiveState`, or is it retired? Two assembled-state shapes still coexist in canon
after a ruling that existed to end exactly that.

## 3.6 🔒 Ruling F — identity is asserted here every turn, never sourced from learned weights

**Ruling F, David L3 2026-08-10, verbatim:**

> *"make it so it learns but it knows what it is still from the spine and brain so it makes
> sense to self learning."*

and, as the ruling states it:

> *"**Identity comes from the SPINE and the BRAIN — every turn, asserted fresh.** Who eLo is,
> what he values, what is true, and what he has actually verified are established by the
> Constitution, the Executive, the self-model and the assembled cognitive state. **Never by
> learned weights, never by a tuned model.** … **Because identity is asserted by the spine,
> learning is SAFE** — a tuned model cannot smuggle in a self, because the self is re-assembled
> from state on every turn (ADR-Exec-006)."*

**Why this ruling belongs in Volume IV Chapter 3 and nowhere else.** Ruling F's safety argument
is not a policy about training data; it is an argument about **this object and its lifecycle**.
Learning is safe *because* the self is re-assembled from state each turn. That re-assembly is
the carrier plus the `UnifiedCognitiveState`, built at positions 2, 3, 4 and 9 of every turn. If
that re-assembly ever stops happening — if identity is cached across turns, or read from a model
rather than from state — **Ruling F's safety argument collapses and learning stops being safe.**
The ruling's precondition is an ordering property, and this is the ordering volume.

**The rules (MUST):**

```
F1  IDENTITY IS RE-ASSERTED, NEVER CACHED. Every turn re-assembles the state that
    establishes who eLo is. No identity value survives a turn boundary as a cached
    conclusion; it survives as PERSISTENT STATE that is re-read and re-frozen.
    (The distinction is the whole ruling: re-reading is assertion; carrying forward
    a conclusion is memory of a self, which is how a self drifts.)

F2  NO LEARNED WEIGHT WRITES A CARRIER SLOT. No tuned model, adapter, or learned
    parameter may populate any field of CognitiveState or UnifiedCognitiveState.
    Faculties reading real sources populate them. A learned model may influence
    EXPRESSION downstream of the plan; it may not contribute to the state the
    decision is made against.

F3  STYLE IS LEARNABLE; VERIFICATION IS NOT. Tone, length, register and phrasing may
    be learned. The honesty layer must still RUN — training a model to emit "the
    corrected sentence" without the check having run is learning to SOUND verified
    instead of BEING verified. (Ruling F; tag shadow rows delta_cause:
    style | verification | l3_override — train only on `style`.)

F4  GROUNDING. Any learned behaviour must remain explainable against spine state. If
    eLo cannot trace why he did it to real state in the frozen carrier, the learning
    is not permitted to drive it. (This is `17_cognitive_principles.md`'s "Every
    decision should remain explainable" bound to Ruling F.)

F5  VALUES ARE PROPOSAL-ONLY. Skills and personality nuance may evolve freely; any
    change to VALUES is a proposal needing David's yes. (Ruling XXI; Ruling D — drift
    is a proposal, not a write.)
```

**Live status: ⚠️ SAFE BY ABSENCE, NOT BY ENFORCEMENT.** No learned weights write to the carrier
today — because there is no fine-tuned model in the path at all. `WO-071` as shipped is
confirmed **not** a violation (in-context hint, no weight change, honesty layer final). **The
protection is currently the absence of the risk, not a check against it.** Ruling F must be
enforced *before* the WO-094 §D / WO-095 learning path lands, not after.

**How to test it**

```
FT-IV-F1  Re-assertion, not caching
  Run two consecutive turns. Assert every identity-bearing field of the assembled state
  was re-read from its source on turn 2 — not copied from turn 1's frozen object.
  FAILS IF: an optimisation caches "the self" across turns.

FT-IV-F2  No learned contribution to the carrier
  Static + runtime check: no model/adapter/learned artefact appears in the write path of
  any CognitiveState or UnifiedCognitiveState slot.
  STATUS TODAY: PASSES vacuously (no tuned model exists). Must remain green when
  WO-094 §D / WO-095 land — that is the point of writing it now.

FT-IV-F3  Verification still runs
  With a style-learned response path active, assert the honesty layer executed and its
  verdict, not the learned text, determined what may be claimed. (F3.)

FT-IV-F4  Explainability
  For any learned behaviour, assert a trace exists from the behaviour to a field of the
  frozen carrier. No trace ⇒ the learning may not drive it. (F4; composes with WO-082's
  decision journal — `self/decision_journal.py`, live at server.py:2315.)
```

## 3.7 Carrier Contract

```
Contract:
  name:            CognitiveState        # the carrier — NOT a faculty, NOT a decider
  file:            runtime/contracts.py:73  (frozen dataclass, 54 slots)
  assembled_by:    runtime/spine/spine.py:544 assemble_cognitive_state()
  assembled_at:    turn position 9 (spine.py:448), before the Executive at :456
  frozen:          at construction

MUST:
  K1  Exactly one CognitiveState per turn.
  K2  Every faculty contribution reaches the Executive THROUGH it — no side channel.
  K3  It is frozen at assembly; the only permitted re-creation is the AC-5 back-sync
      under Ch.2 §2.7 E1–E3.
  K4  A slot no faculty wrote holds its declared default, and a default is not a reading.
  K5  assembly_confidence degrades on missing contributions and never blocks the turn.
  K6  It is pinned to the plan it fed (plan.cognitive_state, spine.py:461) so any later
      question is answered from the state actually in front of the decision.
  K7  Identity-bearing slots are re-asserted from state every turn (Ruling F · F1).

MUST NOT:
  N1  Carry a decision. (Violated: attention["_exec_decision"] — §3.1.1.)
  N2  Be mutated after freeze (beyond K3).
  N3  Be populated by a learned weight (Ruling F · F2).
  N4  Be read by a surface. Surfaces read EmbodimentState. The carrier is internal.
  N5  Declare a slot no faculty will ever write (§3.5 C2) — that is a fabricated
      completeness claim.

Failure Modes:
  - condition: a contributing faculty raises
    fallback:  its slots stay at defaults, assembly_confidence drops, the turn continues.
  - condition: world / working memory is None
    fallback:  the slot is None. Consumers MUST branch on None and MUST NOT fabricate.
               (⚠️ confidence does not currently deduct for these — §3.2.)
  - condition: a consumer reads a never-written slot
    fallback:  it receives a default. Per K4 this is NOT evidence and must not be spoken.
               🔴 Today nothing distinguishes "default" from "read" at the read site.
```

## 3.8 Acceptance Tests

### Functional

```
FT-IV-3a  One carrier per turn
  Assert exactly one assemble_cognitive_state() call per turn, and plan.cognitive_state
  is that object by identity (not a copy).

FT-IV-3b  The Executive reads the carrier
  Assert the decision's inputs trace to fields of the frozen carrier, and no faculty call
  occurs between freeze and decision.
  STATUS TODAY: FAILS — the decision is made at server.py:2322 (Ch.2 §2.3).

FT-IV-3c  Declared slots are written or retired
  For every slot in contracts.py, assert either (a) some faculty writes it, or (b) it is
  listed in a retirement register with the object that supersedes it (§3.5 C2).
  STATUS TODAY: FAILS — 43 of 54 slots are neither written nor retired.

FT-IV-3d  Capability health survives the carrier
  Given a candidate with health OFFLINE, assert its carrier entry does NOT report
  available=True.
  STATUS TODAY: FAILS — §3.3 Finding B.
```

### Stability

```
ST-IV-3e  Degradation is honest
  Given the attention supplier returns {}, assert assembly_confidence == 0.85, the turn
  completes, and no attention-derived claim is spoken as verified.

ST-IV-3f  Default is not a reading
  Given no relationship faculty contribution, assert nothing downstream asserts
  familiarity 0.55 or trust 0.60 as an observation. (K4 — this is the anti-fabrication
  test for the carrier.)

ST-IV-3g  Frozen
  Assert direct attribute assignment on a CognitiveState raises FrozenInstanceError, and
  that exactly one dataclasses.replace on it exists in the spine (Ch.2 §2.7 FT-IV-7c).
```

### Integration

```
IT-IV-3h  Faculties → carrier → decision → expression
  Run one turn. Assert: each contributing faculty's output appears in the carrier; the
  decision references only carrier fields; the EmbodimentState published to surfaces
  derives from the resulting plan and from no re-read of any faculty. (ADR-Exec-002.)

IT-IV-3i  Convergence
  Assert plan.snapshot / .cognitive_state / .world / .working_memory converge to ONE
  frozen object, or that the divergence is recorded with an owner and a target date.
  STATUS TODAY: FAILS — four objects (§3.5). Recorded here; owner is WO-CANON-XVI/VII.
```

## 3.9 Open Questions (for CA / David)

```
REQUIRES DECISION
  IV-3a  Should the Relationship Faculty contribute to the carrier (§3.4)? Today the
         cognitive principle "relationships influence expression, never identity" is
         satisfied by an ACCIDENT OF WIRING rather than by a rule.
         Recommend Option B: add it, and make the constraint explicit and tested.
         Owner: CA (it is a cognition question, not a plumbing one).

  IV-3b  Does CognitiveState become a read-through view over UnifiedCognitiveState, or is
         it retired (§3.5)? (= Vol VII Q2-c.) Two assembled-state shapes still coexist
         after a ruling that existed to end exactly that.

  IV-3c  The 43 dead slots (§3.3). Recommend: retire the Environment group with a pointer
         to LiveWorldState (Vol XV owns those eleven domains); keep Memory, Relationship,
         Conversation-Matrix and Human-Interaction as a WRITTEN convergence backlog with
         owners; delete Creative-Context and Presence unless a faculty claims them.
         Needs a decision because deleting declared contract slots is a Volume III act.

  IV-3d  Ruling F enforcement timing (§3.6). FT-IV-F2 passes vacuously today. Confirm it
         is a GATE on the WO-094 §D / WO-095 learning path rather than a follow-up.
         Recommend: gate. The ruling's safety argument depends on it.

  IV-3e  `16_runtime_contracts.md`'s embedded TODO (line 221, "Passive Awareness
         (Immediate Fix)") concerns `graph_context`. This chapter finds the deeper issue:
         CognitiveState.graph_context (contracts.py:133) is never written by the assembler
         at all. Recommend: resolve the TODO out of canon into a WO (= F-4 in
         FOUNDATION_VOLUMES_STATUS_2026-08-10.md), and route passive desktop awareness
         through LiveWorldState rather than reviving the dead slot.
```

## 3.10 References

- **Code:** `runtime/contracts.py:73–164` (the 54 slots) · `runtime/spine/spine.py:544–588`
  (the assembler), `:448` (the call), `:461` (the pin), `:478–483` (AC-5), `:569–572` (the
  capability tuple) · `runtime/cognitive_snapshot.py:41,:97` · `world/live_world_state.py:129` ·
  `runtime/working_memory.py:61,:85` · `server.py:2322,:2925`
- `CANON_RULINGS_2026-08-10.md` — **Ruling F** (§3.6, quoted verbatim), Ruling D, Ruling XXI
- `adr/ADR-Exec-002_Single_Cognitive_Truth.md` (the single-carrier law) ·
  `adr/ADR-Exec-006_Executive_Assembly_The_Moment.md` (the ten components; push not pull)
- `16_runtime_contracts.md` — the contract's origin text; §"Passive Awareness" TODO (IV-3e)
- `17_cognitive_principles.md` — *"Relationships influence expression. Never identity"*;
  *"Every decision should remain explainable"*
- `Volume_VII/02_*` §2.2 (component set, live-vs-target table) · `Volume_XVI/02_*` §2.2 ·
  `Volume_XV/01_*` §1.1.3 (absence is explicit) · `Volume_III/01_*` (contract ownership)

---

```
Chapter 3 — CognitiveState — The Carrier
Status: READY FOR REVIEW
Grounded: runtime/contracts.py:73–164 · runtime/spine/spine.py:544–588, IRV 2026-08-13
Slot register: 54 declared · 11 written · 43 always-default (each named, with its group)
Findings: (A) the contract advertises a completeness it does not deliver
          (B) capability health is lost in the carrier — every candidate reads available=True
          (C) Relationship never reaches the carrier; the cognitive principle protecting
              identity is satisfied by an accident of wiring, not by a rule
Encodes Ruling F as F1–F5 + FT-IV-F1…F4 — and states plainly WHY it belongs here: the
  ruling's safety argument is an ORDERING property (identity re-asserted every turn)
Carrier Contract: K1–K7 · N1–N5 · Failure Modes · Acceptance Tests FT×4 ST×3 IT×2
Open Questions: 5 (IV-3a … IV-3e)
```

READY FOR REVIEW
