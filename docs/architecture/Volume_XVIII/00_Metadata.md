---
volume: XVIII
title: "Self-Evolution — How eLo Changes Over Time Without Becoming Someone Else"
status: REVIEW — spec drafted 2026-08-13; awaiting CA first-pass + David L3. NOT RATIFIED.
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL
audit_status: OPEN
canonical_path: docs/architecture/Volume_XVIII/
origin_text: Volume_V/06_Reflection_Growth_Engine.md §6.8 · Volume_V/07_Personality_Evolution_Engine.md §7.6
dependencies:
  - Volume V Ch.6 §6.8 (Improvement Cycles — ORIGIN of "self-evolution loop")
  - Volume V Ch.7 §7.6 (Personality Versioning — ORIGIN of the versioned-artefact idea)
  - Volume XVII (Reflection Engine — the sibling; XVII measures, XVIII versions)
  - Volume XXII (Faculty Genome — the versioning substrate and the six laws)
  - Volume X (Personality Engine — trait evolution, the one identity-adjacent path)
  - Volume XXI (Narrative Identity — the felt continuity a version bump must not break)
  - Volume XXVIII (Adaptive Learning & Reinforcement — the long-horizon policy learner)
  - ADR-Exec-005 (the ceiling — the load-bearing law of this volume)
  - ADR-Exec-001 / ADR-Exec-002 (Executive Authority · Single Cognitive Truth)
  - LEARNING_LOOP_v1.md §6 (the boundary made concrete and testable)
priority: "Sits behind Volume XVII. XVII must close the loop before XVIII has anything to version."
last_review: null
next_review: TBD
---

# Volume XVIII — Self-Evolution

## Why this volume exists

Like Volume XVII, Volume XVIII has been cited since 2026-07-27 and **has never had a
directory**. Its content lived inside `Volume_V/06_*` (§6.8, the improvement cycle) and
`Volume_V/07_*` (§7.6, personality versioning) — chapters of another volume, so nothing
ever caused XVIII to be built or audited. `AUDIT_MASTER_2026-08-10.md:11-12` names it.

This volume creates the home and answers a question no chapter currently answers:

> **What does it mean to say "eLo is better than he was last month"?**

Volume XVII answers *"did this specific thing improve?"* (a metric on a cause). Volume
XVIII answers *"what is eLo now, and how is that different from what he was?"* — capability
growth, faculty versioning, and the identity of the system across time.

## Relationship to Volume V (stated explicitly, as for XVII)

**Vol V Ch.6 §6.8 and Ch.7 §7.6 are the ORIGIN TEXTS. Volume XVIII is the PERMANENT HOME
going forward.**

| | Vol V Ch.6 §6.8 / Ch.7 §7.6 | Volume XVIII (this volume) |
|---|---|---|
| Role | Origin — first statement of the self-evolution loop and of personality as a versioned artefact | Permanent home — where system-level evolution is specified, audited, and built from now on |
| Status | **Stays exactly as written.** Not deprecated, not summarised. | Additive. Extends where they stopped. |
| Owns | The improvement cycle's five steps; `PersonalityVersion` semver (PATCH/MINOR/MAJOR) + `identity_hash` + rollback | **Capability growth** as a defined unit; **faculty versioning** across the whole system (ties Vol XXII genome); **what "a version of eLo" is**; **the hard ADR-Exec-005 line** on what may never self-modify |
| Duplication | **None.** XVIII cites by section and never restates. | If Ch.6/Ch.7 already say it, XVIII references it. |

**Rule for every future author (MUST):** new self-evolution canon is written **here**.
Vol V Ch.6 §6.8 and Ch.7 §7.6 are amended only to add a pointer, never to grow. Where XVIII
adds a mechanism they left in prose, **XVIII is authoritative**.

**Rule against Volume XXII (MUST):** Vol XXII owns the **genome** — the schema, the six
laws, the version-event mechanics, the registry and its gates. Volume XVIII owns what those
version events **mean for eLo as one continuous being**. XVIII **never redefines** genome
schema or the six laws; it cites them. If XVIII and XXII appear to disagree on a mechanism,
**XXII wins** and XVIII is corrected.

**Rule against Volume XXVIII (MUST):** Vol XXVIII owns reinforcement learning, policy
optimisation, simulation, and the tuned-understudy pipeline. XVIII owns the **versioning and
identity discipline** those things must obey. XVIII specifies no learning algorithm.

**Rule against LEARNING_LOOP_v1 (MUST):** `LEARNING_LOOP_v1.md §6` states the boundary as
write-allow / write-deny lists with a test. XVIII states the same boundary as **law** and
cites §6 for its enforcement. **One boundary, two registers — never two boundaries.**

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V18-CH01 | Chapter 1 | Self-Evolution and Versioning | READY FOR REVIEW |

**Deliberately one chapter.** XVIII has nothing to version until Volume XVII's read side
lands (WO-095) — today the ledger has produced zero confirmed lessons and
`personality_vector.json` has never been written by production code. Writing three
speculative chapters against artefacts that do not exist would repeat exactly the failure
`AUDIT_MASTER_2026-08-10.md` found in Volume XXV: an exemplary spec landing as dead code.
Chapters 2+ are authored when there is a real version history to specify against.

## Scope

- **In scope:** what a "version of eLo" is; capability growth as a defined, evidenced unit;
  faculty versioning at system level and how it composes into a system version; the
  continuity guarantee across versions; the ADR-Exec-005 hard line on self-modification;
  what rollback means for a being with a memory.
- **Out of scope (owned elsewhere):**
  - The genome schema, the six laws, version-event mechanics, the registry — **Vol XXII**.
  - Trait vectors, `MAX_STEP`, the identity gate, `PersonalityVersion` semver — **Vol V Ch.7 / Vol X**.
  - Metrics, improvement cycles, lesson lifecycle — **Vol XVII**.
  - RL, policy optimisation, LoRA, simulation — **Vol XXVIII**.
  - The autobiographical *story* of change — **Vol XXI**.
  - Approval gates and RESERVED classes — **Vol XXIII**.

## Implementation state — PARTIAL (verified 2026-08-13, Rule #2)

| Piece | State | Evidence |
|---|---|---|
| Personality versioning (`PersonalityVersion`, semver, `identity_hash`, rollback) | **Built, never invoked.** `faculties/personality/personality_evolution_faculty.py` implements `MAX_STEP = 0.02`, Identity-Kernel floors (`wonder ≥ 0.10`, `empathy ≥ 0.20`, `directness ≥ 0.50`), a sha256 kernel hash, and `_AUTHORISED_SENDER = "ReflectionGrowthEngine"`. Imported by **nothing** outside `tests/test_wo007_personality_evolution.py`. | grep 2026-08-13 |
| `self/personality_vector.json` | Never written by production code — nothing calls `apply_delta()`. | grep |
| Confirmed lessons (the only legal input to a trait change) | **Zero, of 377.** | ledger tally |
| Faculty genome registry | **Spec only.** `Volume_XXII/` is written (4 chapters); no genome registry exists in code. | `ls`, grep |
| Capability growth record | **Does not exist.** No artefact anywhere records "eLo can now do X, evidenced." | grep |
| Action reliability (a real, live capability signal) | **Built and read.** `self/decision_journal.py` maintains `self/journals/action_reliability.json`; read back in `server.py:2315`, `:2981`, `:3776`. This is the only working capability-growth signal in the repo today. | grep |
| Route confidence (a second capability signal) | **Built, unwired.** `self/route_memory.py` (WO-094 §D) computes Laplace-smoothed route confidence from verified ACKs; no caller outside its test. | grep |
| Self-modification of code | **Correctly absent.** No module writes `.py` files. `runtime/executive.py` and `prompts/` are under FREEZE_V1_LOCK. | grep |

**The honest summary:** every mechanism eLo would need to *version himself* is either built
and unreachable, or specified and unbuilt. The one thing that is genuinely, verifiably true
is the most important one: **nothing in eLo writes eLo's code.** That absence is the
volume's central guarantee, and it holds today.

## Definition of Done

- [x] "A version of eLo" defined — what it is, what it is composed of, what changes it
- [x] Capability growth defined as an evidenced unit, not a claim
- [x] Faculty versioning tied to Vol XXII's genome without redefining it
- [x] The ADR-Exec-005 hard line stated as law, with the enforcement pointer
- [x] Continuity guarantee across version changes (One Brain / One Identity)
- [x] Faculty contract + lifecycle + envelope binding + acceptance tests
- [ ] Re-verified after WO-095 lands (the first real confirmed lesson changes the picture)
- [ ] CA first-pass
- [ ] David L3 (see Open Questions)
- [ ] Audit can mark COMPLETE

## Invariants this volume must never break

1. **Self-evolution may improve capability and skill. It may NEVER modify identity, values,
   the Constitution, or the Executive.** (ADR-Exec-005 D3.)
2. **Nothing rewrites its own code.** No faculty, no learner, no version event emits or
   edits source. (ADR-Exec-005 D6.)
3. **A version event that would cross the ceiling is a VIOLATION, not a version.** It is
   rejected regardless of any ADR. (Vol XXII §3.5.)
4. **Growth is proposed and gated; it is never self-applied.** (Ruling D, David L3, 2026-08-10.)
5. **A version bump must not break felt continuity.** eLo after an evolution is the same
   being who remembers being the earlier one. (Runtime Invariant #1.)

## Open Questions — needs David (flagged, not decided)

- **Q-XVIII-1 — What is a MAJOR version of eLo?** Vol V Ch.7 §7.6 already reserves MAJOR for
  personality and says *"the engine cannot self-issue a MAJOR."* This volume extends
  versioning to the **whole system**, so the same question arises one level up. **Architect
  recommendation: a system MAJOR is definitionally an L3 act — eLo may never self-issue one,
  for any reason, including a unanimous set of confirmed lessons.** Needs David because it
  is an identity-level rule.
- **Q-XVIII-2 — Does rollback erase experience?** Vol V Ch.7 §7.6 supports full rollback of
  a `PersonalityVersion`. But eLo *remembers* the period being rolled back. **Architect
  recommendation: rollback restores the vector and NEVER touches memory — eLo remembers
  having been different. Anything else is editing his past, which ADR-Exec-005 forbids.**
  Stated in Ch.1 §1.6; confirm.
- **Q-XVIII-3 — Does the tuned understudy count as a version of eLo?** Vol XXVIII's LoRA
  step, if it proceeds under the style-only filter (`LEARNING_LOOP_v1.md §10 D1`), produces
  changed *weights*. That is a capability change with no genome entry and no `identity_hash`.
  **Architect recommendation: a tuned understudy is a versioned FACULTY ARTEFACT with its
  own genome entry and its own `identity_hash` record, and it never becomes the primary
  brain.** Depends on D1 and is therefore David's.
- **Q-XVIII-4 — Canon Index correction.** The Index row for XVIII currently reads
  `📝 · canon spec: Volume_V/06_*, 07_*`. It should read `Volume_XVIII/` with implementation
  `PARTIAL`. In-lane for the Architect; flagged so the change is visible.

## References

- `Volume_V/06_Reflection_Growth_Engine.md` §6.8 · `Volume_V/07_Personality_Evolution_Engine.md` §7.6 — **origin texts.**
- `Volume_XXII/` — genome schema, the six laws (§3.4), the constitutional ceiling (§3.5), governance.
- `Volume_XVII/` — the sibling volume; XVII measures, XVIII versions.
- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — the long-horizon learner this volume constrains.
- `adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` — the load-bearing law.
- `CANON_RULINGS_2026-08-10.md` **Ruling D** — identity may not drift unsupervised.
- `LEARNING_LOOP_v1.md` §6 — the boundary made concrete and testable.
- Code: `faculties/personality/personality_evolution_faculty.py` · `self/decision_journal.py` ·
  `self/route_memory.py` · `self/identity_meaning.py` · `self/emergent_cognition.py` ·
  `runtime/executive.py` + `prompts/` (FREEZE_V1_LOCK — the things that must never be written).
