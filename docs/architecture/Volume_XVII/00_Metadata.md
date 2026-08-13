---
volume: XVII
title: "The Reflection Engine — Lessons, Evidence, and Measured Growth"
status: REVIEW — spec drafted 2026-08-13; awaiting CA first-pass + David L3. NOT RATIFIED.
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL
audit_status: OPEN
canonical_path: docs/architecture/Volume_XVII/
origin_text: Volume_V/06_Reflection_Growth_Engine.md  # remains the origin; XVII is the permanent home
dependencies:
  - Volume V Ch.6 (Reflection & Growth Engine — ORIGIN TEXT, not superseded)
  - Volume V Ch.5 (Significance Engine — which episodes clear the reflection threshold)
  - Volume V Ch.7 / Volume X (Personality Evolution — the only consumer of a trait-scoped lesson)
  - Volume VIII (Memory Architecture — where lessons and journals persist; episode_ref resolution)
  - Volume XXI (Narrative Identity — the autobiographical thread reflection feeds)
  - Volume XVIII (Self-Evolution — the sibling; XVII measures, XVIII versions)
  - ADR-Exec-005 (Learning Through Verified Consequences — the ceiling)
  - ADR-Exec-001 (Verified Speech — a claim needs an ACK)
  - LEARNING_LOOP_v1.md (the near-term buildable spec; XVII must not contradict it)
priority: "David's headline ask — 'get the brain to think more, learn.' Read side is P0 (WO-095)."
last_review: null
next_review: TBD
---

# Volume XVII — The Reflection Engine

## Why this volume exists

Volume XVII has been cited across the canon since 2026-07-27 and **has never had a
directory**. Its content lived inside `Volume_V/06_Reflection_Growth_Engine.md`, which is
a *chapter of another volume* — so nothing ever caused Volume XVII to be built, audited,
or given a work order. `AUDIT_MASTER_2026-08-10.md:11-12` names this directly:

> *"**XVII (Reflection)**, **XVIII (Self-Evolution)** … The Canon Index marked them
> '✅ Live (code)' so they were never written."*

This volume creates the home. It does **not** rewrite Ch.6.

## Relationship to Volume V Chapter 6 (read this before anything else)

**Volume V Ch.6 is the ORIGIN TEXT. Volume XVII is the PERMANENT HOME going forward.**

| | Volume V Ch.6 | Volume XVII (this volume) |
|---|---|---|
| Role | The origin text — where reflection was first specified (2026-07-26) | The permanent home — where reflection is specified, audited, and built from now on |
| Status | **Stays exactly as it is.** Not deprecated, not deleted, not summarised. | Additive. Extends Ch.6 where Ch.6 stopped. |
| Owns | The growth loop, the cadences, `Experience` extraction, the two behaviour channels, the faculty contract for `ReflectionGrowthEngine` | The **read side** (Ch.1), the **lesson lifecycle as numbers** (Ch.1), **Growth Metrics + the Improvement Cycle made buildable** (Ch.2) |
| Duplication | **None.** XVII references Ch.6 by section; it never restates it. | If a rule already exists in Ch.6, XVII cites it (`Vol V Ch.6 §6.4`) and adds only what was missing. |

**Rule for every future author (MUST):** new reflection canon is written **here**, in
`Volume_XVII/`. Ch.6 is amended only to add a pointer, never to grow. Where XVII and Ch.6
say the same thing, Ch.6 is the origin and XVII is the operative text. Where XVII adds a
number, threshold, or mechanism Ch.6 left in prose, **XVII is authoritative**.

**Rule for LEARNING_LOOP_v1 (MUST):** `docs/architecture/LEARNING_LOOP_v1.md` is the
*near-term buildable spec* (it binds WO-095). XVII is the *volume*. They must agree.
Where they touch — lesson identity, promotion thresholds, evidence rules, the reward
boundary — **XVII restates LEARNING_LOOP_v1's numbers unchanged and cites the section**.
XVII never invents a competing threshold. If a threshold is tuned during the build, it is
changed in LEARNING_LOOP_v1 §3.4 and XVII is updated to match — one number, two homes,
never two numbers.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V17-CH01 | Chapter 1 | Reflection and the Lesson Ledger | READY FOR REVIEW |
| ELO-V17-CH02 | Chapter 2 | Growth Metrics and the Improvement Cycle | READY FOR REVIEW |

## Scope

- **In scope:** what reflection *is* as a faculty; the lesson lifecycle
  (candidate → confirmed → demoted → retired) with its numeric transitions; the **read
  side** (recall, promotion, the path back into a turn); evidence rules; growth metrics;
  the improvement cycle that closes a period.
- **Out of scope (owned elsewhere):**
  - The growth loop's origin statement, cadences, and `Experience` extraction — **Vol V Ch.6**.
  - Trait application and the identity gate — **Vol V Ch.7 / Vol X**.
  - Where lessons and journals physically persist, and SPOT resolution — **Vol VIII**.
  - Reinforcement learning, policy optimisation, LoRA — **Vol XXVIII**.
  - Faculty/system versioning and what "a version of eLo" means — **Vol XVIII**.
  - The autobiographical narrative built from journals — **Vol XXI**.

## Implementation state — PARTIAL (verified 2026-08-13, Rule #2)

Counts re-run directly against the live repo today. They have grown since
`AUDIT_MASTER_2026-08-10.md` and `LEARNING_LOOP_v1.md §1`; the finding is unchanged.

| Artefact | State | Evidence |
|---|---|---|
| `self/lessons_ledger.jsonl` | **377 lessons** | `wc -l` 2026-08-13 |
| Confirmed lessons | **0 of 377.** All `candidate`. Zero, ever. | status tally |
| Distinct statements | **4.** 374 are the identical sentence *"Completed a capability milestone — reinforce this pattern."* | statement tally |
| Scopes produced | `capability` ×376, `behaviour` ×1. `preference`, `relationship`, `creative` have **never** been produced. | scope tally |
| `self/journals/growth_journal.jsonl` | **822 entries** | `wc -l` |
| `self/failure_log.jsonl` | **2 entries** | `wc -l` |
| The only writer | `runtime/reflection_faculty.py:29` (`_LESSON_LOG`), `:149` (growth journal) | grep |
| **Readers of either file** | **NONE.** Repo-wide grep for `lessons_ledger`/`growth_journal` over non-test `.py` returns only that writer. | grep 2026-08-13 |
| `self/lesson_store.py` | **Does not exist.** WO-095 builds it. | `ls self/` |
| `faculties/personality/personality_evolution_faculty.py` | Exists and is correct — and is imported by **nothing** except `tests/test_wo007_personality_evolution.py` | grep |
| Growth Metrics (§6.7) | **0%.** No `growth_metrics`, `intention_realisation`, `repeat_failure_rate`, `identity_stability`, `reinforcement_ratio` anywhere in the repo. | grep |
| Improvement Cycle (§6.8) | **0%.** | grep |

**The one-line summary: the loop is write-only.** eLo captures and never reads. Nothing
in 377 lessons or 822 journal entries has ever changed a single turn.

**A working precedent already exists and should be copied, not re-invented:**
`self/decision_journal.py` (WO-082) writes `action_reliability.json` **and is read back**
in `server.py:2315` (`explain_last`), `:2981` (`record_failure`), `:3776` (`record`).
That is a closed capture→read loop in the same directory. Reflection needs the same shape.
(Rule #6, Check-Before-Build.)

**A written-but-unwired artefact:** `self/route_memory.py` (WO-094 §D) implements
ACK-gated route recall correctly, and grep finds **no caller outside its test**. It is
capture built, read not connected — the same failure one layer down.

## Definition of Done

- [x] Reflection defined as a faculty with a stated relationship to its origin text (Vol V Ch.6)
- [x] Lesson lifecycle defined with numeric transitions, not prose (candidate → confirmed → demoted → retired)
- [x] The **read side** specified — recall, promotion, and the path back into a turn
- [x] Evidence rules bound to ADR-Exec-005 (verified consequences only)
- [x] Growth Metrics defined to a buildable level (Vol V Ch.6 §6.7, previously 0%)
- [x] Improvement Cycle defined with a closing condition (Vol V Ch.6 §6.8, previously 0%)
- [x] Faculty contract + lifecycle + envelope binding + acceptance tests (both chapters)
- [ ] Consistency check against `LEARNING_LOOP_v1.md` re-run after WO-095 lands
- [ ] CA first-pass
- [ ] David L3 (see Open Questions)
- [ ] Audit can mark COMPLETE

## Invariants this volume must never break

1. **Reflection never runs in the response path and never answers a user.** (Vol V Ch.6 §6.0)
2. **Language alone is never evidence.** (ADR-Exec-005 D1)
3. **A lesson may inform a decision; it may never assert a fact.** Recalled lessons enter
   the prompt as labelled heuristics, never as truth. (ADR-Exec-001)
4. **Reflection proposes; it never applies.** Trait change goes through Vol V Ch.7's
   validation gate or it does not happen. (CONTRACTS.md §3 — no `Learn → Update` without `Validate`)
5. **Nothing is ever deleted.** Retired lessons stay with `retired_at` + `reason`.

## Open Questions — needs David (flagged, not decided)

- **Q-XVII-1 — Does creating Volume XVII change Volume V's status?** Vol V is marked
  `L3 RATIFIED 2026-08-03` while Ch.6's promotion, recall, metrics, and improvement cycle
  are unbuilt. This is the same question `LEARNING_LOOP_v1.md §10 D4` raises. **Architect
  recommendation:** leave Vol V ratified (its *specification* is sound) and record the
  implementation gap against **Volume XVII**, which is where the build now lives. Revoking
  a ratification is a governance act and is David's call, not the Architect's.
- **Q-XVII-2 — The 377 existing lessons.** Same as `LEARNING_LOOP_v1.md §10 D3`. Archive
  to `lessons_ledger_pre_v1.jsonl` (recommended, non-destructive) or mark in place as
  `retired / pre-v1 template artefact`. Either way nothing is deleted. Restated here so
  the volume does not silently depend on an unanswered question.
- **Q-XVII-3 — Canon Index correction.** The Index row for XVII currently reads
  `📝 · canon spec: Volume_V/06_*`. It should read `Volume_XVII/` with implementation
  `PARTIAL`. Editing the Index is in-lane for the Architect; flagged so the change is
  visible rather than quiet.

## References

- `docs/architecture/Volume_V/06_Reflection_Growth_Engine.md` — **the origin text.**
- `docs/architecture/LEARNING_LOOP_v1.md` — the near-term buildable spec; binds WO-095.
- `docs/architecture/adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md`
- `docs/architecture/AUDIT_MASTER_2026-08-10.md` · `AUDIT_INTENT_learning_growth_2026-08-10.md`
- `engineering/work_orders/WO-095_Learning_Loop_Close_The_Read_Side.md`
- Code: `runtime/reflection_faculty.py` · `self/lessons_ledger.jsonl` ·
  `self/journals/growth_journal.jsonl` · `self/failure_log.jsonl` ·
  `self/decision_journal.py` (the working precedent) · `self/route_memory.py` (unwired) ·
  `faculties/personality/personality_evolution_faculty.py` (the dead validator)
