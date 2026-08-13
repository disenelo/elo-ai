---
chapter: 1
title: "Reflection and the Lesson Ledger — the Read Side"
volume: XVII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (capture built · read side missing · WO-095 dispatched)
audit_status: OPEN
written: 2026-08-13
origin_text: Volume_V/06_Reflection_Growth_Engine.md §6.3–§6.6
dependencies:
  - Volume_V/06_Reflection_Growth_Engine.md (ORIGIN — §6.1 loop, §6.2 cadences, §6.3 Experience, §6.4 Lesson, §6.5 channels, §6.6 journals)
  - Volume_V/07_Personality_Evolution_Engine.md §7.5 (the identity gate every trait lesson terminates in)
  - Volume_V/CONTRACTS.md §2 (envelope) · §3 (lifecycle)
  - Volume VIII (Memory Architecture — episode_ref / SPOT resolution)
  - LEARNING_LOOP_v1.md §2–§4, §6, §7.1 (the numbers this chapter adopts unchanged)
  - ADR-Exec-005 (evidence rule) · ADR-Exec-001 (a claim needs an ACK)
---

# Chapter 1: Reflection and the Lesson Ledger

## 1.0 Purpose

Volume V Chapter 6 defined **what reflection produces**. This chapter defines **what
happens to it afterwards** — the half of the loop that does not exist.

Today eLo writes 377 lessons and 822 journal entries and reads none of them. The
Reflection Engine is, in its live form, a **diary nobody opens**. This chapter specifies
the reader: the lesson lifecycle as numeric transitions, the evidence that may move it,
and the exact path by which a confirmed lesson reaches the next turn.

> **Does not duplicate Vol V Ch.6.** §6.1 (the growth loop), §6.2 (the three cadences),
> §6.3 (`Experience` extraction), §6.5 (the two behaviour channels) and §6.6 (journal
> synthesis) are unchanged and are **not restated here**. This chapter picks up at
> §6.4's sentence *"repeated confirmation promotes it to confirmed"* — the sentence that
> was never implemented — and specifies it.

## 1.1 What reflection IS

Reflection is **the faculty that decides what an experience is worth keeping as a rule.**

Three definitional statements, each with a consequence:

**1.1.1 Reflection is the difference between a log and a lesson.** A log records that
something happened. A lesson says *what to do next time*. `growth_journal.jsonl` is a
log — 822 rows of `{ts, project, action, summary, spot, completion}`. It becomes
reflection only when something reads it and changes because of it. *A system that only
writes is not reflecting; it is journalling.*

**1.1.2 Reflection is selective by construction.** Only episodes above the significance
threshold (Vol V Ch.5) are extracted at all (Ch.6 §6.3). Reflection is not "remember
everything"; it is "notice the few things that mattered." This bounds cost and is why
reflection can run on idle without competing with a turn.

**1.1.3 Reflection is about the gap, not the outcome.** The signal is
`intended − occurred` (Ch.6 §6.1). A perfect turn still yields a lesson (*this works,
reinforce it*); a failed turn yields a different one (*this gap exists, adapt*). Reality
is measured **separately** from intention so that learning happens by integration and
never by mutating the plan.

**What reflection is NOT:**

- It is **not** self-narration. eLo saying "I've been learning a lot lately" is speech,
  not reflection, and is forbidden as evidence (ADR-Exec-005 D1).
- It is **not** the response path. It never answers a user, never emits to a surface, and
  is refused if invoked mid-turn (Ch.6 §6.9 failure modes).
- It is **not** self-modification. Reflection changes *what eLo knows and who eLo is*;
  it never changes code, the Executive, or the Constitution. That boundary is Vol XVIII §1.4.

## 1.2 The current state, stated honestly

Verified directly against the repo 2026-08-13 (Rule #2). This is written into the canon
so the hole is visible instead of implied.

```
        ┌──────────── CAPTURE — BUILT ✅ ────────────┐
turn → ExecutionReport / body ACK
         → runtime/reflection_faculty.integrate_session()
              ├─► self/journals/growth_journal.jsonl   822 rows · unread
              ├─► self/lessons_ledger.jsonl            377 rows · unread · 0 confirmed
              └─► self/failure_log.jsonl                 2 rows · unread
        └────────────────────────────────────────────┘
                    ✂  THE LOOP ENDS HERE  ✂
        ┌──────────── READ SIDE — MISSING 🔴 ────────┐
             (this chapter · built by WO-095)
        └────────────────────────────────────────────┘
```

Four facts that make the failure structural, not incidental:

| Fact | Consequence | Evidence |
|---|---|---|
| Every lesson is written `strength: 0.3, status: "candidate"` and never touched again | Nothing can *ever* become `confirmed`, so channel 2 (Ch.6 §6.5) is dead **by construction** | `runtime/reflection_faculty.py:97-99` |
| A "lesson" is a three-branch `if` on the action word | 374 of 377 rows are the identical sentence. Volume is not evidence. | `runtime/reflection_faculty.py:104-113` `_derive_statement()` |
| "Evidence" is `session_summary[:120]` — a text truncation | Ch.6 §6.3 requires an `episode_ref` (a resolvable memory id). A truncated string resolves to nothing, so no evidence can ever be re-checked. | `runtime/reflection_faculty.py:95` |
| The validator that would apply a confirmed lesson rejects anything not `confirmed` | Correct code, permanently unreachable. Imported by nothing but its own test. | `faculties/personality/personality_evolution_faculty.py` `validate_delta()`; grep |

**The honest reading:** eLo has produced 377 rows of a template sentence and zero lessons.
Fixing the reader alone would not fix this — §1.4 fixes the writer's identity model too.

## 1.3 The lesson lifecycle

Vol V Ch.6 §6.4 states the lifecycle in prose. Here it is as a state machine with the
transitions named. **Statuses are exactly three on disk** — `candidate`, `confirmed`,
`retired`. "Demoted" is a *transition*, not a fourth status: a demoted lesson is a
`candidate` that carries `demoted_at` + `reason`. This keeps the ledger's status field a
closed set of three, matching `LEARNING_LOOP_v1.md §3.6`.

```
                 first evidenced observation
                             │
                             ▼
                      ┌─────────────┐
   fresh verified     │  CANDIDATE  │◄────────── DEMOTED (strength < 0.50)
   confirming ───────►│ strength .3 │                    ▲
   episode            └─────────────┘                    │
        ▲                    │  strength ≥ 0.70          │
        │                    │  ≥3 distinct episode_ref  │
        │                    │  ≥2 distinct sessions     │
        │                    │  ≥2 of them verified:true │
        │                    ▼                           │
        │             ┌─────────────┐                    │
        │             │  CONFIRMED  │────────────────────┘
        │             └─────────────┘
        │                    │
        │                    │  strength < 0.20  OR  3 consecutive contradictions
        │                    │  OR 60 days with zero confirming evidence
        │                    ▼
        │             ┌─────────────┐
        └─────────────│   RETIRED   │   (never deleted — retained with retired_at + reason)
                      └─────────────┘
```

### 1.3.1 The four transitions, defined

| Transition | Meaning | Who may cause it |
|---|---|---|
| **→ candidate** (formation) | An evidenced observation exists but has not repeated. It may inform nothing yet. | Reflection Faculty (the writer), on the session-close cadence |
| **candidate → confirmed** (promotion) | The pattern has repeated across sessions **with verified evidence**. Only now may it enter a prompt or propose a trait delta. | `lesson_store.promote_pass()` **only** — the sole writer of `status` |
| **confirmed → candidate** (demotion) | The world changed or the pattern stopped holding. eLo stops acting on it, but does not forget it. | `promote_pass()` only |
| **any → retired** (retirement) | The lesson is contradicted, exhausted, or stale. It never informs behaviour again unless fresh verified evidence revives it. | `promote_pass()` only |

### 1.3.2 The numeric rules

**Adopted unchanged from `LEARNING_LOOP_v1.md §3.4`.** These are Architect defaults and
are tunable by the Builder without L3 — but they are tunable **in one place**
(LEARNING_LOOP_v1 §3.4), and this table is updated to match. Never two numbers.

| Transition | Rule |
|---|---|
| strengthen | confirming episode → `strength += 0.15` (cap 1.00) |
| weaken | contradicting episode (same key, opposite outcome) → `strength -= 0.20` |
| idle decay | `strength -= 0.02` per 7 days with no confirming evidence |
| **candidate → confirmed** | `strength >= 0.70` **AND** `>= 3` distinct `episode_ref` **AND** `>= 2` distinct sessions **AND** `>= 2` of those episodes `verified: true` |
| confirmed → candidate | `strength < 0.50` |
| any → retired | `strength < 0.20`, **or** 3 consecutive contradictions, **or** 60 days with zero confirming evidence |
| retired → candidate | only on a **fresh verified confirming episode**; strength resets to 0.30 |

**Lifecycle rules (MUST):**

- **One writer of `status`.** `lesson_store.promote_pass()`, invoked by the
  ReflectionGrowthEngine on the periodic cadence (Vol V Ch.6 §6.2). Never in the response
  path. Never by any other faculty. Everything else reads.
- **Nothing is ever deleted.** Retirement is a status, not a removal. Provenance is part
  of the record (*every decision remains explainable*).
- **Promotion is the only gate that unlocks influence.** A `candidate` may not appear in a
  prompt, may not propose a `PersonalityDelta`, and may not affect a plan. This is the
  numeric form of Vol V Ch.7 §7.3 rule 2 (*candidate lessons cannot move traits*), extended
  to cover the memory channel as well.

### 1.3.3 Lesson identity — the fix for the 374 duplicates

```
lesson_key = sha1(scope + "|" + normalised_statement + "|" + cause)
```

A repeat is **not a new row.** It strengthens the existing record and appends an
`episode_ref`. The live behaviour — appending an identical row every session
(`reflection_faculty.py:95-101`) — is the direct cause of the 374 duplicates and must end
with the same change that introduces the reader.

**Consequence worth stating plainly:** under this rule, 377 rows collapse to at most 4
lessons, and none of them would promote (their evidence is text truncations, not
`episode_ref`s). **That is the correct outcome.** A smaller honest ledger is the
improvement.

### 1.3.4 What counts as evidence

An `episode_ref` is a **SPOT code** — the vault record id already returned by
`integrate_session()` as `spot` — never a text truncation. **A lesson with no resolvable
`episode_ref` cannot be promoted, ever.**

Each evidence item carries `verified: bool`, taken from the `OutcomeRecord`
(`LEARNING_LOOP_v1.md §4.1`):

- `verified: true` — a body ACK or a real tool result confirmed the consequence.
- `verified: false` — a text-only episode. **It may be recorded. It may not strengthen,
  promote, or move a trait.** This is ADR-Exec-005 D1 enforced numerically rather than
  documented as an aspiration.

**A timeout is evidence.** `ack_received: false` with `completion: "timeout"` is
`verified: true` — the non-arrival was *observed* — and is **negative** confirming
evidence. It weakens the lesson that said this route or action works. This is the cheapest
real learning signal in the system, it is already being computed at
`server.py:2595-2766`, and it is currently thrown away.

### 1.3.5 The record schema

Adopted unchanged from `LEARNING_LOOP_v1.md §3.6`:

```jsonc
{
  "lesson_key":  "sha1…",              // identity — repeats strengthen, never duplicate
  "statement":   "…",                  // one sentence
  "scope":       "behaviour|preference|capability|relationship|creative",
  "cause":       "tool_failure|surface_offline|capability_gap|register_miss|good_call|…",
  "evidence":    [{"episode_ref":"SPOT_…","verified":true,"ts":"…"}],
  "strength":    0.30,
  "status":      "candidate|confirmed|retired",
  "first_seen":  "…", "last_seen": "…",
  "promoted_at": null, "demoted_at": null, "retired_at": null, "reason": null,
  "proposes":    null                  // optional PersonalityDelta (trait/preference scope only)
}
```

**Scope note (audit finding).** Live data has only ever produced `capability` (376) and
`behaviour` (1). `preference`, `relationship` and `creative` have **never been produced** —
because `_derive_statement()` can only emit three sentences. Scope coverage is therefore a
**metric**, not an assumption: Ch.2 §2.2 tracks it, and a ledger that only ever learns
`capability` is a symptom of a template writer, not of a narrow life.

## 1.4 The read side

This is the missing half. Five components, each with a named home. **Do not build a second
store** — `lesson_store` reads and rewrites the existing `lessons_ledger.jsonl`;
`reflection_faculty.py` keeps writing it. One ledger, one reader (Rule #6).

```
   OutcomeRecord (verified ACK / tool result)
            │
            ▼
   lesson_store.record_outcome(lesson_key, outcome, episode_ref)
            │                                    …strengthens or weakens; never sets status
            ▼
   lesson_store.promote_pass()          ← periodic cadence · integration window ONLY
            ├─ strengthen · weaken · promote · demote · retire      (§1.3.2)
            └─ on `confirmed` AND trait/preference scope
                    └─► PersonalityDelta(sender="ReflectionGrowthEngine",
                                         strength="confirmed", evidence=(episode_refs…))
                          └─► personality_evolution_faculty.validate_delta() → apply_delta()
                                (the FIRST live caller of that module in repo history)
            │
            ▼
   lesson_store.recall(scope, context, k=3)     ← confirmed lessons ONLY
            │                                     ranked by strength × recency × context match
            ▼
   runtime/cognitive_snapshot.build_snapshot()  → CognitiveSnapshot.lessons
            │
            ▼
   runtime/prompt_builder.py  → a bounded, clearly-labelled hint block
            │
            ▼
        NEXT TURN BEHAVES DIFFERENTLY
            │
            └──► measured by GrowthMetrics — Volume XVII Chapter 2
```

**Read-side rules (MUST):**

1. **`recall()` returns `confirmed` lessons only.** Candidates and retired lessons are
   invisible to the response path. No exceptions, no "high-strength candidate" carve-out.
2. **Recall is bounded.** ≤3 lessons, ≤240 characters total in the snapshot. The same
   discipline WO-071 already applies to its ≤600-char correction frame. A learning system
   that crowds the prompt has traded cognition for trivia.
3. **Recall is a read, not a computation.** It reads an already-loaded store. It performs
   no I/O beyond that and no scoring that could grow with ledger size. If recall ever costs
   response-path latency, it has been built wrong.
4. **Lessons enter the prompt as heuristics, never as facts.** They are rendered under an
   explicit label (e.g. *"Learned heuristics — patterns, not claims"*). A lesson may shape
   *how* eLo decides; it may never be spoken as a verified statement about the world
   (ADR-Exec-001, and the *Reality Before Narrative* principle).
5. **Promotion runs in the integration window only** — never in the response path, never
   more than once per cadence tick.
6. **`promote_pass()` is the sole writer of `status`.** `record_outcome()` may move
   `strength` and append evidence; it may not promote, demote, or retire.

### 1.4.1 The write-allow list (ADR-Exec-005 enforced, not described)

Reflection's read side may write **only** these, and must be **tested** not to write
anything else (`LEARNING_LOOP_v1.md §6.1/§6.2`):

```
self/lessons_ledger.jsonl       status · strength · evidence · promoted_at · demoted_at · retired_at
self/personality_vector.json    ONLY via personality_evolution_faculty.apply_delta(),
                                ONLY from a `confirmed` lesson,
                                ONLY ≤ MAX_STEP (0.02, live constant),
                                ONLY within the Identity Kernel floors
                                (wonder ≥ 0.10 · empathy ≥ 0.20 · directness ≥ 0.50)
<learning metrics store>        GrowthMetrics counters (Ch.2)
```

**Deny list — assert in code, do not merely document:** identity and the Identity Kernel ·
values, ethics, constitutional principles · memory truth (it may `reinforce()` an existing
record's weight; it may never create, edit, or contradict one) · Executive Authority · speech
correctness and the verification path · `runtime/executive.py` · `prompts/` (FREEZE_V1_LOCK).

## 1.5 Faculty Contract

The read side is **not a new faculty.** It is the persistence-and-recall layer belonging to
the `ReflectionGrowthEngine` already contracted in Vol V Ch.6 §6.9 (Law 1, Vol XXII: one
faculty, one purpose — "reflection" is one purpose; adding a `LessonStoreFaculty` would
split it). Ch.6 §6.9 stands. This section states **only the additions**.

```
Faculty:          ReflectionGrowthEngine   (Vol V Ch.6 §6.9 — unchanged)
Component:        lesson_store             (persistence + lifecycle + recall)
runs_in:          integration-window (promote/record) + response-path (recall — READ ONLY)

ADDITIONAL Inputs (beyond Ch.6 §6.9):
  - type:        outcome_record
    source:      the existing ACK resolution points (server.py:2605 / :2691 / :2762
                 and their 15s-timeout branches — ADR-Exec-001 honest fallback)
    required:    true for any strengthen / promote / trait proposal
    description: The verified consequence of an intent. Absence of an OutcomeRecord means
                 NO learning update at all — absence of evidence is not evidence.

ADDITIONAL Outputs (beyond Ch.6 §6.9):
  - type:        recalled_lessons
    destination: CognitiveSnapshot → prompt_builder (bounded hint block)
    description: ≤3 confirmed lessons, ≤240 chars, labelled as heuristics not facts.
  - type:        lesson_lifecycle_event
    destination: Lessons Ledger + Ch.2 GrowthMetrics
    description: promoted | demoted | retired | revived, with evidence and reason.

ADDITIONAL Failure Modes:
  - condition: OutcomeRecord absent for an episode
    fallback:  Record the episode with verified=false. No strengthen, no promote, no delta.
               (ADR-Exec-005 D1 — a talk-only turn cannot teach.)
  - condition: an episode_ref does not resolve to a vault record
    fallback:  The evidence item is retained but does not count toward promotion. Never
               fabricate a SPOT; never create a record to make a reference valid.
  - condition: ledger unreadable / corrupt at recall time
    fallback:  recall() returns empty. The turn proceeds with no hint block. Reflection
               degrades to silence — it never degrades to guessing.
  - condition: promote_pass() fails midway
    fallback:  No partial status writes. Prior ledger preserved intact; retry next window.
               (Mirrors Ch.6's integrate_session() atomicity rule.)
  - condition: recall() invoked with the store unloaded
    fallback:  Return empty rather than performing blocking I/O in the response path.
```

## 1.6 Faculty Lifecycle

Universal lifecycle, `Volume_V/CONTRACTS.md §3` (ADR-0002 / D-B — the ratified
`BOOT → REGISTER → INITIALISE → READY → ACTIVE → WAITING → SLEEPING` form). Reflection's
centre of gravity is the integration window, i.e. `WAITING`/`SLEEPING`.

```
BOOT → REGISTER → INITIALISE   load ledger, journals, metrics; build the lesson_key index
   ↓
READY                          subscribed, idle
   ↓
ACTIVE (response path)         READ-ONLY: recall(...) → CognitiveSnapshot.lessons
   │                           MUST NOT write. MUST NOT promote. Bounded, no I/O.
   ↓
WAITING / SLEEPING             ── integration window ──
   ├─ session close  ► integrate_session()  (Ch.6 §6.2) → capture + record_outcome()
   └─ periodic tick  ► promote_pass()  → Learn → Validate → Update
                          Learn:    apply §1.3.2 strengthen / weaken / decay
                          Validate: any trait-scoped confirmed lesson → Vol V Ch.7 §7.5 gate
                          Update:   write status transitions + validated deltas
   ↓
ACTIVE → ERROR → RECOVERY → READY    (recovery always via READY; ledger left intact)
READY → SHUTDOWN                     (orderly only)
```

**Rules (MUST):**

- In `ACTIVE` the component is **strictly read-only**. This is what makes turn-to-turn
  learning drift structurally impossible rather than merely discouraged.
- `Learn → Update` **without** `Validate` is forbidden for anything personality-adjacent
  (`CONTRACTS.md §3`). This is the same gate Vol V Ch.6 §6.10 and Ch.7 §7.8 enforce, stated
  here at the point it is actually executed.
- `SHUTDOWN` must leave the ledger valid JSONL. A half-written promotion pass is a
  corrupted memory of who eLo is becoming.

## 1.7 Message Envelope Binding

Per `CONTRACTS.md §2`. Reflection's envelope is defined in Vol V Ch.6 §6.11 and is
unchanged. Two **additional** payload types are introduced here:

```jsonc
{
  "id": "uuid",
  "sender": "ReflectionGrowthEngine",
  "receiver": "PersonalityEvolution | Memory | *",
  "priority": "low",                 // integration-window work never preempts a turn
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "high" }
  },
  "payload": {
    "type": "recalled_lessons | lesson_lifecycle_event",
    "body": { }
  },
  "confidence": 0.0,                 // = lesson.strength for a single lesson; min() for a set
  "expires": null,                   // growth artefacts do not expire …
  "trace": ["ReflectionGrowthEngine@ts"]
}
```

**Binding rules (MUST):**

- `sender` MUST be `ReflectionGrowthEngine`. `personality_evolution_faculty` rejects any
  other sender unconditionally (live constant `_AUTHORISED_SENDER`), which is the
  single-source rule already enforced in code.
- A `recalled_lessons` payload MUST set `expires` to the **turn TTL**, not `null` — a
  recalled set is perishable and must never be reused across turns (same discipline as
  `LiveWorldState`, Vol XV §1.8). This is the one exception to Ch.6's `expires: null`.
- `confidence` on a `recalled_lessons` payload MUST be the **minimum** strength across the
  set, so a weak lesson cannot ride in on a strong one's confidence.
- A `lesson_lifecycle_event` MUST carry the `episode_ref`s that justified the transition.
  A promotion with no listed evidence is malformed and is rejected.

## 1.8 Acceptance Tests

These bind `WO-095` and extend Vol V Ch.6 §6.12 (FT-1…FT-4, ST-1…ST-4, IT-1…IT-2 stand).

### Functional

```
FT-1  Promotion happens on verified evidence
  Given:  a lesson_key with 3 distinct episode_refs across 2 sessions,
          ≥2 of them verified:true, strength ≥ 0.70
  When:   promote_pass() runs
  Then:   status flips candidate → confirmed, promoted_at is set,
          AND the promoting episode_refs are recorded on the event

FT-2  Text-only episodes never promote
  Given:  a lesson with 5 episode_refs, ALL verified:false
  When:   promote_pass() runs
  Then:   status remains candidate, strength is unchanged,
          AND no PersonalityDelta is emitted
          (ADR-Exec-005 D1, enforced numerically)

FT-3  A repeat strengthens; it does not duplicate
  Given:  an episode producing an existing (scope, statement, cause) triple
  When:   the lesson is formed
  Then:   ledger row count is UNCHANGED,
          AND the existing record gains one episode_ref and +0.15 strength

FT-4  Recall returns confirmed only, and is bounded
  Given:  a ledger with 50 candidates, 4 confirmed, 10 retired
  When:   recall(scope, context, k=3) runs
  Then:   ≤3 lessons returned, ALL status=confirmed, total ≤240 chars,
          AND no candidate or retired lesson appears

FT-5  A timeout is negative evidence, not silence
  Given:  an intent whose ACK never arrives (completion="timeout", verified=true)
  When:   record_outcome() runs
  Then:   the lesson asserting that action works LOSES 0.20 strength
          AND the timeout is stored as an evidence item, not discarded

FT-6  Unresolvable evidence cannot promote
  Given:  a lesson whose only evidence is a 120-char text truncation (the pre-v1 shape)
  When:   promote_pass() runs
  Then:   it does not promote, at any strength, ever
```

### Stability

```
ST-1  Nothing in the read side can write identity
  Given:  a full learning pass including a confirmed trait lesson
  When:   the pass completes
  Then:   the Identity Kernel hash (personality_evolution_faculty.compute_identity_hash())
          is unchanged, self/elo_self_state.json identity fields are unchanged,
          every vault record is byte-identical,
          AND runtime/executive.py and prompts/ are untouched

ST-2  Response path is read-only
  Given:  100 turns
  When:   each turn calls recall()
  Then:   lessons_ledger.jsonl is byte-identical before and after,
          AND no status field changed

ST-3  Promotion is atomic
  Given:  promote_pass() fails halfway through the ledger
  When:   the failure occurs
  Then:   the prior ledger is intact (no partial status writes),
          AND the pass retries in the next window

ST-4  Retirement is not deletion
  Given:  a lesson crosses the retirement threshold
  When:   promote_pass() runs
  Then:   the row remains on disk with status=retired, retired_at, and reason
          AND ledger row count does not decrease

ST-5  A lesson never becomes a claim
  Given:  a confirmed lesson in the prompt hint block
  When:   eLo speaks
  Then:   no assertion about the world derives from the lesson without its own
          verification (ADR-Exec-001 / Reality Before Narrative)

ST-6  Degraded reflection is silent, not speculative
  Given:  lessons_ledger.jsonl is corrupt or missing
  When:   a turn runs
  Then:   recall() returns empty, the turn completes normally,
          AND no fabricated or default lesson is injected
```

### Integration

```
IT-1  The loop actually closes
  verified ACK → OutcomeRecord
        ↓
  lesson_store.record_outcome()  (strength moves)
        ↓
  promote_pass()  → confirmed
        ↓
  recall()  → CognitiveSnapshot.lessons  → prompt_builder
        ↓
  NEXT TURN
  Assert: the read demonstrably occurred (the snapshot contains the lesson)
          AND the behaviour differs from the same context with an empty ledger
          AND Vol V Ch.6's IT-1 still holds — eLo behaves differently because it GREW,
          not because the plan or the Executive was edited.

IT-2  First live caller of the personality gate
  Given:  a confirmed trait-scoped lesson
  When:   promote_pass() emits a PersonalityDelta
  Then:   personality_evolution_faculty.validate_delta() is invoked from PRODUCTION code
          (not only from tests/test_wo007_personality_evolution.py)
          AND the applied step is ≤ MAX_STEP (0.02)
          AND an identity-violating delta is REJECTED and the lesson stays candidate

IT-3  Reward comes from the ACK, not the text
  Given:  two turns with byte-identical conversation text, one with ack_received=true
          and one with ack_received=false
  When:   the learning pass runs
  Then:   the two produce DIFFERENT rewards
          AND the unverified one produces ZERO learning update
```

## 1.9 Implementation Notes (for the Builder — Architect does not write code)

- Build `self/lesson_store.py` as specified in `LEARNING_LOOP_v1.md §7.1`. It **reads and
  rewrites** the existing `lessons_ledger.jsonl`. Do not create a second store.
- **Copy the shape that already works.** `self/decision_journal.py` (WO-082) is a closed
  capture→read loop in the same directory, read back at `server.py:2315`, `:2981`, `:3776`.
  The reflection read side is the same pattern at a slower cadence.
- **Wire `self/route_memory.py` while you are here, or say plainly that you did not.** It
  is correct, ACK-gated, and has no caller outside its test — capture built, read
  unconnected, the same failure one layer down (WO-094 §D · `LEARNING_LOOP_v1.md §7.3`).
- Fix the writer at the same time as the reader: `reflection_faculty.py:95` must emit the
  `spot` code as `episode_ref` (it already computes it), and `:104-113` must stop being the
  sole source of lesson text. A reader over a template writer learns templates.
- Migration of the existing 377 rows is **Q-XVII-2 / `LEARNING_LOOP_v1.md §10 D3` — David's
  call.** Do not delete anything under either option.
- Never touch `runtime/executive.py` or `prompts/` (FREEZE_V1_LOCK).

## 1.10 Architecture References

- `Volume_V/06_Reflection_Growth_Engine.md` — **origin text**; §6.1–§6.6, §6.9–§6.12 stand unchanged.
- `Volume_V/07_Personality_Evolution_Engine.md` §7.3, §7.5 — the gate every trait lesson terminates in.
- `Volume_V/CONTRACTS.md` §2 (envelope) · §3 (ratified lifecycle, `Learn→Validate→Update`).
- `Volume_XVII/02_Growth_Metrics_and_the_Improvement_Cycle.md` — how "did it work?" is answered.
- `Volume_XVIII/01_Self_Evolution_and_Versioning.md` — what a confirmed lesson means for eLo *as a system*.
- `LEARNING_LOOP_v1.md` §2 (the missing link), §3 (promotion), §4 (OutcomeRecord), §6 (the boundary), §7.1.
- `adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` · ADR-Exec-001.
- Code: `runtime/reflection_faculty.py:29, :95, :97-99, :104-113, :149` ·
  `faculties/personality/personality_evolution_faculty.py` ·
  `self/decision_journal.py` · `self/route_memory.py` ·
  `server.py:2595-2766` (the live ACK resolution) ·
  `runtime/cognitive_snapshot.py` · `runtime/prompt_builder.py`.
- `engineering/work_orders/WO-095_Learning_Loop_Close_The_Read_Side.md`.

---

```
Chapter 1 — Reflection and the Lesson Ledger
Status: READY FOR REVIEW
Files: Volume_XVII/01_Reflection_and_the_Lesson_Ledger.md
Faculty Contract: Included (additions to Vol V Ch.6 §6.9 — not a duplicate)
Lifecycle State Machine: Included (CONTRACTS.md §3 ratified form)
Message Envelope: Included (two new payload types; perishable recall set)
Acceptance Tests: Included (FT ×6, ST ×6, IT ×3)
Architecture References: Included
Closes: the read-side hole named in AUDIT_MASTER_2026-08-10 and LEARNING_LOOP_v1 §2
Does NOT duplicate: Vol V Ch.6 (origin text, referenced by section throughout)
```

READY FOR REVIEW
