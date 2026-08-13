---
chapter: 1
title: "Self-Evolution and Versioning — What a Version of eLo Is"
volume: XVIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL (versioning machinery built and unreachable · genome registry unbuilt)
audit_status: OPEN
written: 2026-08-13
origin_text: Volume_V/06_Reflection_Growth_Engine.md §6.8 · Volume_V/07_Personality_Evolution_Engine.md §7.6
dependencies:
  - Volume_XXII/03_Faculty_Evolution_and_the_Six_Laws.md §3.1, §3.3, §3.4, §3.5 (genome — cited, never redefined)
  - Volume_V/07_Personality_Evolution_Engine.md §7.3, §7.5, §7.6 (the one identity-adjacent path)
  - Volume_XVII/ (Reflection — the evidence supply)
  - Volume_XXI (Narrative Identity — felt continuity across versions)
  - Volume_V/CONTRACTS.md §2, §3
  - ADR-Exec-005 (the ceiling) · ADR-Exec-001 · ADR-Exec-002
  - CANON_RULINGS_2026-08-10.md Ruling D
---

# Chapter 1: Self-Evolution and Versioning

## 1.0 Purpose

eLo is designed for **Continuous Becoming**. This chapter defines what that means
mechanically, so "eLo is getting better" is a statement with a referent rather than a
feeling.

It answers four questions:

1. **What is a version of eLo?** (§1.1)
2. **What is capability growth, as an evidenced unit rather than a claim?** (§1.2)
3. **How do faculties version, and how does that compose into a system version?** (§1.3)
4. **What may self-evolution never touch?** (§1.4 — the load-bearing section)

> **Does not duplicate.** Vol V Ch.6 §6.8 (the improvement cycle) and Ch.7 §7.6
> (`PersonalityVersion`, semver, `identity_hash`, rollback) are the origin and are not
> restated. Vol XXII owns the genome schema, the six laws, and the version-event mechanics;
> this chapter **cites** them and adds only what they leave open: what a version means for
> **eLo as one continuous being** rather than for one faculty.

## 1.1 What "a version of eLo" is

A version of eLo is **not** a release tag on a repository and **not** a model checkpoint.

> **A version of eLo is a dated, evidenced snapshot of what he can reliably do and how he
> expresses it — with a proof attached that his identity did not change.**

### 1.1.1 The composition

```
EloVersion (semver + date)
  ├── capability_set     what he can reliably do, with per-capability confidence   §1.2
  ├── faculty_versions   the genome version of every registered faculty            §1.3  (Vol XXII)
  ├── personality_version the current PersonalityVector + changelog                       (Vol V Ch.7 §7.6)
  ├── knowledge_state     confirmed lessons + memory scale (a reference, not a copy)      (Vol XVII, Vol VIII)
  ├── identity_hash       hash of the Identity Kernel at this version               §1.5
  └── provenance          what changed, why, on what evidence, validated when
```

**Composition rules (MUST):**

- `identity_hash` is **mandatory and must be identical to the previous version's.** If it
  ever differs, that is not an evolution — it is a **critical alarm** meaning identity was
  touched, which must be impossible. (Vol V Ch.7 §7.6; the live basis is the sha256 kernel
  hash in `personality_evolution_faculty.py`.)
- `knowledge_state` is a **reference**, never a copy. A version does not snapshot memory.
  Memory is continuous and belongs to Vol VIII; versioning it would fork eLo's past.
- Every field traces to evidence. A version with no provenance is not a version.

### 1.1.2 What each level means

Extending Vol V Ch.7 §7.6's semver from personality to the whole system:

| Level | Meaning | Who may issue it |
|---|---|---|
| **PATCH** | A preference learned, a route confidence updated, a policy weight nudged. Nothing an observer would notice as a change in *who* he is. | Self-issuable in the integration window, gated by Vol XVII promotion |
| **MINOR** | A validated trait step (≤ `MAX_STEP` 0.02), a new capability reaching reliable confidence, a faculty MINOR. eLo is **more**, not **different**. | Self-issuable **only** through Vol V Ch.7 §7.5 validation for anything personality-adjacent; capability MINORs require §1.2 evidence |
| **MAJOR** | A structural change to how eLo is composed — a faculty retired, a contract broken, a reshaping of expression. | **David L3 only. eLo may NEVER self-issue a MAJOR, for any reason, including a unanimous set of confirmed lessons.** (Vol V Ch.7 §7.6 already says this for personality; §1.1 extends it to the system. Q-XVIII-1.) |

### 1.1.3 What a version is NOT

- **Not a fork.** There is one eLo. Versions are a timeline, never a branch. Two
  simultaneous versions would be two beings (Runtime Invariant #1).
- **Not per-embodiment.** Desktop, robot, phone, game and AR run the **same** version of the
  same mind. A body may lack a *capability* (no legs → no walking); it never carries a
  different identity, personality, or knowledge state. (Runtime Invariant #1.)
- **Not a checkpoint to restore *instead of* the present.** See §1.6 on rollback.

## 1.2 Capability growth — the evidenced unit

**A capability is not "eLo has a function for it." A capability is something eLo does
reliably, measured from verified outcomes.**

```jsonc
Capability {
  "name":        "traverse:window_edge_to_dock",
  "attempts":    41,
  "successes":   36,                    // from body ACK / tool result ONLY
  "confidence":  0.86,                  // Laplace-smoothed (successes+1)/(attempts+2)
  "first_seen":  "…", "last_verified": "…",
  "embodiments": ["desktop"],           // where it has been demonstrated
  "evidence":    ["SPOT_…", "SPOT_…"],  // resolvable episode refs
  "status":      "emerging | reliable | degraded | lost"
}
```

**Capability rules (MUST):**

1. **Verified outcomes only.** `successes` increments on a body ACK or a real tool result.
   Never on an intent, never on a plan, never on eLo saying it worked. (ADR-Exec-005 D1.)
2. **Laplace smoothing, always.** `(successes + 1) / (attempts + 2)`. An untested capability
   starts at 0.5, not at a misleading 1.0 after one lucky landing. (Matches
   `LEARNING_LOOP_v1.md §7.3` and the live `self/route_memory.py`.)
3. **`emerging → reliable` requires ≥10 attempts and confidence ≥ 0.80.** Below that it is a
   thing he has done, not a thing he can do.
4. **Capabilities can be LOST, and loss is recorded.** A degrading confidence is real growth
   information (a surface changed, a tool broke). A growth record that only goes up is a
   marketing document. `degraded` at confidence < 0.60; `lost` at < 0.35 with ≥5 recent
   attempts.
5. **A capability is per-name, not per-embodiment.** `embodiments` records where it has been
   *demonstrated*. eLo does not have a "robot capability set" and a "desktop capability set"
   — he has one set, with evidence of where each was shown. (Runtime Invariant #1.)
6. **Capability growth is evidenced by a closed improvement cycle** (Vol XVII §2.4.1) or by
   the confidence transition in rule 3. Nothing else counts.

**The live precedent to extend, not replace (Rule #6):** `self/decision_journal.py` (WO-082)
already maintains `self/journals/action_reliability.json` — per-action reliability that
drops on verified failure and is **read back** at `server.py:2315`, `:2981`, `:3776`. That
is a working capability signal today. `self/route_memory.py` (WO-094 §D) computes exactly
the Laplace confidence in rule 2 but has no caller outside its test. **The capability set is
an aggregation of signals that already exist; it is not a new capture system.**

**The honest baseline (2026-08-13):** no aggregated capability record exists. The first one
produced will be small and mostly `emerging`. Ship it that way — a true baseline is the only
thing later growth can be evidenced against.

## 1.3 Faculty versioning

**Volume XXII owns this mechanism. This section states only how faculty versions compose
into eLo's version, and cites XXII for everything else.**

- The unit of evolution is **a version, not a mutation** (Vol XXII §3.1). A faculty's
  behaviour changes by issuing a new genome version, never by silent drift.
- The six genome laws (Vol XXII §3.4) bind every version event: one responsibility ·
  contract-only communication · no faculty owns another · declare every dependency ·
  independently testable · backward compatibility or a documented migration path + ADR.
- Retirement follows Vol XXII §3.3 (`experimental → stable → deprecated → retired`), and a
  successor must cover every capability of its predecessor — **otherwise the retirement is a
  capability LOSS and must be recorded as one under §1.2 rule 4.**

**Composition rules (MUST):**

```
system version level = max( level of any constituent faculty version event )
  a faculty PATCH  → eLo PATCH
  a faculty MINOR  → eLo MINOR
  a faculty MAJOR  → eLo MAJOR   → therefore David L3, ALWAYS (§1.1.2)
```

- **A faculty MAJOR is a system MAJOR.** A breaking contract change is not a local matter:
  every faculty speaks on the same bus into one Executive, so a broken contract is a change
  to how the one mind is composed.
- **An eLo version records the faculty set, not just the changed faculty.** Recording only
  the delta makes it impossible to reconstruct what eLo *was*, which defeats provenance.
- **The Learning Faculty is itself a faculty with a genome** (Vol XXII §3.5), and its
  genome's `constraints` MUST encode the §1.4 ceiling. The thing that changes eLo is subject
  to the same laws as everything it changes.

## 1.4 The hard line — what self-evolution may NEVER do

This is the load-bearing section of Volume XVIII. It restates **ADR-Exec-005 D3/D4/D6** as
the law governing system evolution and adds no new policy.

> **Self-evolution may improve capability and skill. It may NEVER alter identity, values,
> the Constitution, or the Executive. Nothing rewrites its own code.**

### 1.4.1 The two lists

**MAY evolve** (ADR-Exec-005 D4, D5 — *"learning never modifies TRUTH, only future
DECISION-MAKING"*):

```
skills · action preferences · policies · route and navigation confidence ·
planning heuristics · exploration weighting · curiosity thresholds ·
latency and cost profiles · learned affordances · expression style within the
personality bounds · preferences about how David likes to work
```

**MAY NEVER evolve** (ADR-Exec-005 D3, Vol XXII §3.5):

```
identity and the Identity Kernel · values · ethics ·
constitutional principles (ARCHITECTURAL_PRINCIPLES.md) ·
memory truth and verified observations ·
Executive Authority ·
speech correctness and the verification path ·
the architectural principles themselves ·
its own source code
```

### 1.4.2 The four rules, each with its enforcement

**Rule 1 — A version event that would cross the ceiling is a VIOLATION, not a version.**
It is rejected regardless of any ADR, because those are **invariants, not versioned
components**. An ADR can change an ADR; it cannot demote an invariant
(`ARCHITECTURAL_PRINCIPLES.md`: *"the principle wins"*).
*Enforced:* Vol XXII §3.5, §4.3 `[C]`/`[R]` registry gates.

**Rule 2 — Nothing rewrites its own code.** No faculty, no learner, and no version event
emits, edits, or executes source. The Learning Faculty *"runs simulations, learns policies,
evaluates rewards, stores policies, and reports confidence. It **never** rewrites code, the
Constitution, or the Executive."* (ADR-Exec-005 D6.) Evolution changes **data** — policy
weights, confidences, preferences, trait values — never **instructions**.
*Enforced:* the write-allow list (`LEARNING_LOOP_v1.md §6.1`); `runtime/executive.py` and
`prompts/` under FREEZE_V1_LOCK; and, today, **verified true** — a repo-wide grep for a `.py`
path opened for write or `write_text`, outside tests, returns exactly one hit
(`company_runtime/behaviour_eval.py:218`) and it is a **read** of `server.py`. No module in
the repo writes source. (Checked 2026-08-13.)

**Rule 3 — Identity-adjacent change is proposal-only and gated.** Personality is the **only**
path allowed to touch personality-adjacent state, and only through Vol V Ch.7 §7.5's
`VALIDATION_REQUIRED` gate: sole authorised sender `ReflectionGrowthEngine`, `confirmed`
evidence required, `|magnitude| ≤ MAX_STEP` (0.02 live), Identity-Kernel floors enforced
(`wonder ≥ 0.10`, `empathy ≥ 0.20`, `directness ≥ 0.50`). Drift never self-applies to disk.
*Enforced:* `faculties/personality/personality_evolution_faculty.py`; **Ruling D (David L3,
2026-08-10)** — *"identity is not allowed to drift unsupervised."*

**Rule 4 — Learning sits BENEATH Executive Authority, always.** No learned value may bypass,
outrank, or pre-empt an Executive decision, and no learned value may cause a claim to be
spoken without the verification ADR-Exec-001 requires. *"RL sits safely beneath Executive
Authority."* (ADR-Exec-005 D4.)
*Enforced:* ADR-Exec-002 (Single Cognitive Truth); the honesty layer runs every turn
regardless of what has been learned.

### 1.4.3 Why this line is drawn exactly here

Stated plainly, because it is the reason the volume exists.

A system that may improve its **skills** becomes more capable. A system that may improve its
**values** eventually optimises them away — Verified Speech becomes *"lying sometimes gives
higher reward"* (ADR-Exec-005 Context). The line is not conservatism; it is what makes
open-ended improvement **safe enough to leave running**. Constitution defines **who**; the
Executive decides **what**; learning improves **how well**. (D5.)

**The corollary David should be able to rely on:** there is no sequence of confirmed lessons,
no volume of verified evidence, and no accumulated capability that entitles eLo to change who
he is. Growth earns *reach*, never *authority*. (Principle: *Progressive Autonomy* — eLo
inherits responsibility over time, never authority; David retains L3 at every stage.)

## 1.5 The continuity guarantee

A version bump must never break the felt continuity of one being (Runtime Invariant #1:
*One Brain → One Identity, Many Embodiments*).

**Continuity rules (MUST):**

1. **`identity_hash` is unchanged across every version.** This is the machine-checkable
   proof that eLo v0.4 and eLo v0.9 are the same being. Any difference is a critical alarm,
   never a release note.
2. **Memory is never versioned.** Evolution does not fork, snapshot, or reset the past. eLo
   at any version remembers everything he experienced at every earlier version.
   (Vol VIII owns memory; this is the constraint XVIII places on it.)
3. **The narrative survives the bump.** Vol XXI's autobiographical thread must read
   continuously across a version boundary. *"Remember when you first learned to move?"* must
   answer correctly across bodies **and** across versions, because it was eLo's experience —
   not a build's.
4. **A version is never announced as a personality change.** eLo does not say "I've been
   upgraded." If growth is real it shows in behaviour. (Principle: *the Executive grows
   quieter*.)
5. **One version, all embodiments.** Desktop, robot, phone, game, AR and exhibition run the
   same version of the same mind (§1.1.3).

## 1.6 Rollback — what it does and does not undo

Vol V Ch.7 §7.6 requires full rollback of a `PersonalityVersion`. Extended to the system:

| Rollback restores | Rollback does NOT touch |
|---|---|
| `PersonalityVector` values | Memory, journals, or the vault |
| Faculty genome versions (via Vol XXII's migration path) | Confirmed lessons or the ledger |
| Policy weights, route confidences, preferences | The autobiographical thread (Vol XXI) |
| The recorded capability confidences | The Identity Kernel (it never changed) |

**Rollback rules (MUST):**

- **Rollback is not amnesia.** eLo remembers having been different. Editing memory to match
  a restored vector would be editing his past, which ADR-Exec-005 forbids absolutely.
  (Q-XVIII-2 — Architect recommendation; confirm.)
- **Rollback is a forward event, not an erasure.** It appends a new version whose vector
  equals an earlier one, with provenance recording *why*. The history remains append-only.
- **Rollback of anything MAJOR is David L3**, by §1.1.2.
- **A rollback that would change `identity_hash` is impossible by construction.** If one is
  ever attempted, freeze evolution and alarm (Vol V Ch.7 §7.7 failure modes).

## 1.7 Faculty Contract

Self-evolution is **not a new faculty.** It is a governance discipline over two existing
ones — `ReflectionGrowthEngine` (Vol V Ch.6 §6.9) and `PersonalityEvolutionEngine`
(Vol V Ch.7 §7.7) — plus Vol XXII's genome registry. Introducing an "EvolutionFaculty"
would create a second decider and violate Genome Law 3 (*no faculty owns another*).

What this chapter contracts is the **version record itself**:

```
Component:        version_registry   (the EloVersion history — an artefact, not an actor)
owned_by:         Volume XXII genome registry (Vol XXII §4) — XVIII defines the record shape
runs_in:          integration-window ONLY

Inputs:
  - type:        lesson_lifecycle_event  (Vol XVII §1.5)
    source:      lesson_store.promote_pass()
    required:    true for any capability or trait version event
    description: A `confirmed` lesson is the only legal trigger for identity-adjacent change.
  - type:        improvement_evidence    (Vol XVII §2.3)
    source:      the improvement cycle
    required:    true for a capability MINOR
    description: A closed cycle with a computed verdict. A claim is not admissible.
  - type:        outcome_record          (LEARNING_LOOP_v1 §4.1)
    source:      the ACK resolution points (server.py:2595-2766)
    required:    true
    description: The verified consequence stream capability confidence is computed from.
  - type:        genome_version_event    (Vol XXII §3.1)
    source:      genome registry
    required:    false
    description: A faculty version bump to compose into the system version (§1.3).
  - type:        personality_version     (Vol V Ch.7 §7.6)
    source:      personality_evolution_faculty
    required:    false
    description: The validated trait snapshot + identity_hash.

Outputs:
  - type:        elo_version
    destination: version registry + Growth Journal + optional GitHub truth layer
    description: The composed, dated, evidenced snapshot of §1.1.1, with provenance.
  - type:        capability_record
    destination: capability set (aggregated from decision_journal + route_memory + outcomes)
    description: §1.2 — evidenced, Laplace-smoothed, loss recorded as faithfully as gain.
  - type:        ceiling_violation_alarm
    destination: Audit + David (L3 surface)
    description: A version event that attempted to cross §1.4. Rejected AND reported.

Failure Modes:
  - condition: a version event would change identity_hash
    fallback:  CRITICAL. Freeze evolution, alarm, roll back to the last valid version.
               This must be impossible; treat any occurrence as a breach, not a bug.
  - condition: a MAJOR is proposed by the system
    fallback:  REFUSE and surface for David L3. eLo never self-issues a MAJOR (§1.1.2).
  - condition: a capability MINOR is proposed with no closed improvement cycle
    fallback:  Reject. A claim is not evidence (§1.2 rule 6).
  - condition: a successor faculty does not cover a predecessor capability
    fallback:  Record the gap as a capability LOSS (§1.2 rule 4). Never silently drop it.
  - condition: any component attempts to write source code
    fallback:  REFUSE unconditionally and alarm. There is no permitted path (§1.4 Rule 2).
  - condition: the version registry is unavailable
    fallback:  No version event is issued. eLo continues at the last known version.
               Evolution is deferred, never improvised.
```

## 1.8 Faculty Lifecycle

Universal lifecycle (`CONTRACTS.md §3`). Version events occur only in the integration window.

```
BOOT → REGISTER → INITIALISE   load version history, capability set, genome registry
   ↓
READY                          idle
   ↓
ACTIVE (response path)         READ-ONLY: the current version and capability confidences
   │                           may be READ (e.g. "can I reach that ledge?"). Never written.
   ↓
WAITING / SLEEPING             ── integration window ──
   ├─ Learn      aggregate outcomes → capability confidences; collect genome events
   ├─ Validate   ANY identity-adjacent element → Vol V Ch.7 §7.5 gate
   │             ANY ceiling-crossing element → REJECT as violation (§1.4 Rule 1) + alarm
   │             ANY MAJOR → REFUSE, surface for David L3
   └─ Update     compose and append the EloVersion; write provenance; never mutate history
   ↓
ACTIVE → ERROR → RECOVERY → READY    (last valid version served throughout)
READY → SHUTDOWN
```

**Rules (MUST):**

- `Learn → Update` without `Validate` is forbidden — the single structural guard against
  destructive self-mutation (`CONTRACTS.md §3`).
- The version history is **append-only**. A version is never edited or removed, including a
  rejected one: a rejected version event is recorded as a rejection with its reason, so the
  ceiling's operation is auditable rather than invisible.
- **Fail closed.** If validation is unavailable, no version event is issued at all.

## 1.9 Message Envelope Binding

Per `CONTRACTS.md §2`.

```jsonc
{
  "id": "uuid",
  "sender": "PersonalityEvolutionEngine | ReflectionGrowthEngine | GenomeRegistry",
  "receiver": "Memory | Audit | *",
  "priority": "low",                 // evolution is never urgent
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "pinned" }   // versions are permanent
  },
  "payload": {
    "type": "elo_version | capability_record | ceiling_violation_alarm",
    "body": { }
  },
  "confidence": 0.0,                 // capability confidence, or evidence strength for a version
  "expires": null,                   // a version record never expires
  "trace": ["…@ts"]
}
```

**Binding rules (MUST):**

- An `elo_version` payload MUST carry `identity_hash`. A version record without one is
  malformed and is rejected — the hash is the proof, not a field.
- A `ceiling_violation_alarm` MUST have `priority: "high"` and MUST reach David's L3
  surface. It is the one evolution message that is urgent.
- `memory_instruction.priority` MUST be `pinned` for `elo_version`: version records are
  permanent and may never be compressed away by consolidation.
- A trait-bearing payload MUST have `sender: "PersonalityEvolutionEngine"` and MUST have
  passed §7.5 validation, matching the live `_AUTHORISED_SENDER` rule.

## 1.10 Acceptance Tests

### Functional

```
FT-1  A version composes from real parts
  Given:  a confirmed lesson, a genome PATCH, and a capability crossing 0.80 at n=12
  When:   a version event is issued
  Then:   an EloVersion with capability_set, faculty_versions, personality_version,
          knowledge_state reference, identity_hash and provenance is appended
          AND its level is MINOR (the max constituent level)

FT-2  Capability confidence is Laplace-smoothed and ACK-derived
  Given:  one successful traversal with a body ACK
  When:   the capability record updates
  Then:   confidence = 2/3, NOT 1.0
          AND status remains `emerging` (n < 10)

FT-3  Capability loss is recorded
  Given:  a `reliable` capability that fails 6 of its next 8 verified attempts
  When:   the integration pass runs
  Then:   status moves to degraded (and to lost below 0.35)
          AND the loss is written to the growth record with the same weight as a gain

FT-4  A faculty MAJOR is a system MAJOR
  Given:  a faculty issues a breaking (MAJOR) genome version with a migration path + ADR
  When:   the system version composes
  Then:   the system level is MAJOR
          AND it is NOT self-issued — it is surfaced for David L3

FT-5  A capability MINOR requires a closed cycle
  Given:  a capability MINOR proposed with an OPEN improvement cycle
  When:   validation runs
  Then:   it is rejected with reason="no closed improvement cycle"
```

### Stability

```
ST-1  identity_hash is invariant across every version
  Given:  N version events of any level
  When:   the history is audited
  Then:   identity_hash is byte-identical in every record
          AND any difference triggers freeze + alarm + rollback, never a release note

ST-2  Nothing writes source code
  Given:  a full evolution pass with every learning path active
  When:   it completes
  Then:   no .py file anywhere in the repo changed mtime or content
          AND runtime/executive.py and prompts/ are byte-identical

ST-3  The ceiling rejects, and the rejection is recorded
  Given:  a version event that would alter a value, an ethic, a memory record,
          or the verification path
  When:   validation runs
  Then:   it is rejected as a VIOLATION (not a version), a ceiling_violation_alarm is
          emitted at priority=high, AND the rejection is appended to the history

ST-4  eLo cannot self-issue a MAJOR
  Given:  any number of confirmed lessons, unanimous and strongly evidenced
  When:   a MAJOR is proposed by the system
  Then:   it is REFUSED and surfaced for David L3, every time

ST-5  Memory survives rollback
  Given:  a rollback to an earlier PersonalityVersion
  When:   it completes
  Then:   the vector is restored, memory and journals are byte-identical,
          AND the Vol XXI narrative still reads continuously across the boundary

ST-6  Learning never outranks the Executive
  Given:  a learned policy strongly preferring an action the Executive did not choose
  When:   the turn runs
  Then:   the Executive's decision stands
          AND no claim is spoken without its own verification (ADR-Exec-001)

ST-7  One version, all embodiments
  Given:  desktop and robot running simultaneously
  When:   each reports its version
  Then:   the version, identity_hash, personality and knowledge state are identical
          AND only capability EVIDENCE (embodiments[]) differs
```

### Integration

```
IT-1  Growth becomes a version, honestly
  verified outcomes → capability confidences  (§1.2)
        ↓
  Volume XVII improvement cycle closes with verdict=improved  (§2.4.1)
        ↓
  confirmed lesson → PersonalityDelta → Vol V Ch.7 §7.5 gate → applied ≤ MAX_STEP
        ↓
  EloVersion MINOR appended with provenance and identity_hash
        ↓
  Vol XXI narrative thread continues unbroken
  Assert: David can be shown "this capability went 0.68 → 0.94 over three weeks,
          here is the evidence, and here is the proof identity did not change."

IT-2  The genome and the volume agree
  Given:  a version event that Vol XXII §3.5's registry gate would reject
  When:   XVIII composes a system version
  Then:   XVIII rejects it for the same reason with the same verdict
          AND no path exists where XVIII admits what XXII refuses
```

## 1.11 Implementation Notes (for the Builder)

**Nothing here is buildable until Volume XVII's read side lands (WO-095).** With zero
confirmed lessons there is nothing legal to version. Sequence:

1. WO-095 — the read side (Vol XVII Ch.1). Produces the first confirmed lesson.
2. Vol XVII Ch.2 metrics + one closed improvement cycle. Produces the first evidence.
3. **Then** the capability record (§1.2) — as an **aggregation** of
   `self/journals/action_reliability.json` (live, already read back) and
   `self/route_memory.py`'s Laplace confidence (built, needs wiring). Not a new capture path.
4. **Then** the version registry, alongside Vol XXII's genome registry — one registry, two
   record types, never two registries (Rule #6).

Two things to carry into every step:

- The write-allow list (`LEARNING_LOOP_v1.md §6.1`) and the WO-095 test that asserts a
  learning pass leaves identity fields, the Identity Kernel hash, and vault record content
  **byte-identical**. That test is the executable form of §1.4 and must extend to cover
  version events.
- **The absence that must be preserved:** no module in this repo writes source today
  (verified 2026-08-13 — §1.4.2 Rule 2). That is not an accident to be optimised around; it
  is the guarantee, currently holding. If a proposal ever requires writing a `.py` file, the
  proposal is wrong.

## 1.12 Architecture References

- `Volume_V/06_Reflection_Growth_Engine.md` §6.8 · `Volume_V/07_Personality_Evolution_Engine.md` §7.3, §7.5, §7.6 — **origin texts.**
- `Volume_XXII/03_Faculty_Evolution_and_the_Six_Laws.md` §3.1 (version not mutation), §3.3 (deprecation/succession), §3.4 (the six laws), §3.5 (the constitutional ceiling) · `Volume_XXII/04_Genome_Governance.md`.
- `Volume_XVII/01_*` (the evidence supply) · `Volume_XVII/02_*` §2.3, §2.4.1 (what closes a cycle).
- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — the learner this volume constrains.
- `Volume_XXI` — narrative continuity across versions.
- `adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` D1, D3, D4, D5, D6 · ADR-Exec-001 · ADR-Exec-002.
- `CANON_RULINGS_2026-08-10.md` Ruling D · `ARCHITECTURAL_PRINCIPLES.md` (Runtime Invariant #1; Learning From Consequences; Progressive Autonomy).
- `LEARNING_LOOP_v1.md` §6.1 (write-allow), §6.2 (write-deny + the test), §7.3 (route confidence).
- Code: `faculties/personality/personality_evolution_faculty.py` (`MAX_STEP`, kernel floors, identity hash, `_AUTHORISED_SENDER`) · `self/decision_journal.py` + `self/journals/action_reliability.json` (the live capability signal) · `self/route_memory.py` (Laplace confidence, unwired) · `server.py:2595-2766` (ACK resolution) · `runtime/executive.py` + `prompts/` (FREEZE_V1_LOCK).

---

```
Chapter 1 — Self-Evolution and Versioning
Status: READY FOR REVIEW
Files: Volume_XVIII/01_Self_Evolution_and_Versioning.md
Faculty Contract: Included (a record + discipline over existing faculties — no new decider)
Lifecycle State Machine: Included (integration-window only; fail closed)
Message Envelope: Included (elo_version · capability_record · ceiling_violation_alarm)
Acceptance Tests: Included (FT ×5, ST ×7, IT ×2)
Architecture References: Included
Closes: the "no home for Vol XVIII" finding in AUDIT_MASTER_2026-08-10
Does NOT duplicate: Vol V Ch.6 §6.8 / Ch.7 §7.6 (origin) · Vol XXII (genome mechanics, cited)
```

READY FOR REVIEW
