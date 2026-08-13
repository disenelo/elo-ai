---
chapter: 2
title: "Growth Metrics and the Improvement Cycle — Evidencing Improvement"
volume: XVII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: NONE (0% — verified 2026-08-13)
audit_status: OPEN
written: 2026-08-13
origin_text: Volume_V/06_Reflection_Growth_Engine.md §6.7 (Growth Metrics) · §6.8 (Improvement Cycles)
dependencies:
  - Volume_XVII/01_Reflection_and_the_Lesson_Ledger.md (the ledger these metrics read)
  - Volume_V/06_Reflection_Growth_Engine.md §6.7, §6.8 (ORIGIN — stated in prose, never built)
  - Volume_V/07_Personality_Evolution_Engine.md §7.6 (personality versioning — source of identity_stability)
  - Volume XVIII (Self-Evolution — consumes a closed cycle as evidence of capability growth)
  - LEARNING_LOOP_v1.md §8 (the minimum viable slice)
  - ADR-Exec-005 (metrics may measure learning; they may never become a learning target for identity)
---

# Chapter 2: Growth Metrics and the Improvement Cycle

## 2.0 Purpose

David's question is one sentence: **"is he actually getting better?"**

Today the only possible answer is a claim. This chapter makes it a number.

Volume V Ch.6 §6.7 and §6.8 named the metrics and the cycle in prose and were **never
implemented — verified 0% on 2026-08-13**: a repo-wide grep for `growth_metrics`,
`intention_realisation`, `repeat_failure_rate`, `identity_stability`, and
`reinforcement_ratio` returns nothing outside canon documents. This chapter specifies
them to a buildable level: what is measured, how improvement is *evidenced* rather than
asserted, and what it means for a cycle to **close**.

> **Does not duplicate Vol V Ch.6.** §6.7's six metric names and §6.8's five-step cycle are
> the origin. This chapter defines each metric's numerator, denominator, window, source
> artefact, and failure mode — and defines the closing condition §6.8 leaves implicit.

## 2.1 The measurement principle

**2.1.1 A metric answers a question David actually asks.** Every metric below maps to a
plain-English question. A metric that answers no question is instrumentation, not
evidence, and does not belong here.

**2.1.2 Metrics are computed from artefacts that already exist.** No metric may require a
new daemon, a new capture path, or a new store beyond a counters file. Everything in §2.2
derives from `lessons_ledger.jsonl`, `growth_journal.jsonl`, `failure_log.jsonl`,
`personality_vector.json`, and the `OutcomeRecord`s that WO-095 introduces.

**2.1.3 Metrics never enter the response path.** (Vol V Ch.6 §6.7, restated as a MUST.)
They never influence a single turn's plan, never appear in a prompt, and are never spoken
as a status report unless David asks. *Measuring growth must not become performing growth.*

**2.1.4 A metric is never a reward.** Metrics observe the learning system; they are not an
input to it. Feeding `intention_realisation` back as a reward creates the classic failure
— the system learns to attempt only easy intents. The reward comes from `OutcomeRecord`s
(`LEARNING_LOOP_v1.md §4.2`); metrics only *report*.

**2.1.5 Some metrics are guardrails, and a guardrail rising is an alarm.**
`identity_stability` is not a growth target. Rising trait variance means integration is
over-adapting and Vol V Ch.7's validation is too loose. **A guardrail must never be
optimised.** (Vol V Ch.6 §6.7; principle: *consistency over novelty*.)

## 2.2 What is measured

Six metrics. **Four are buildable now** (`LEARNING_LOOP_v1.md §8`); two are deferred with
their blocker named, rather than being specified against data that does not exist.

| # | Metric | The question it answers | Formula | Source artefact | Direction | Build |
|---|---|---|---|---|---|---|
| M1 | `intention_realisation` | *Does what he intends actually happen?* | `met / (met + partial + failed + timeout)` | `OutcomeRecord.completion` + `growth_journal.jsonl.completion` | ↑ | **now** |
| M2 | `repeat_failure_rate` | *Does he make the same mistake twice?* | `(episodes whose `cause` recurred in a prior session) / (total failure episodes)`, per cause | `self/failure_log.jsonl` (cause-tagged) | ↓ | **now** |
| M3 | `reinforcement_ratio` | *Is he learning more than he is unlearning?* | `confirming evidence items / (confirming + contradicting)` across the ledger | `lessons_ledger.jsonl` evidence items | ↑, then stable | **now** |
| M4 | `identity_stability` | *Is he still himself?* | trait variance across the `personality_vector.json` changelog over the window | `self/personality_vector.json` + `PersonalityVersion` changelog (Vol V Ch.7 §7.6) | **LOW — rising is an alarm** | **now** |
| M5 | `lesson_yield` | *Is reflection producing anything real?* | `lessons promoted to confirmed / significant episodes` | ledger lifecycle events + Ch.5 significance | ↑ from zero, then plateau | **now (trivial once M3 exists)** |
| M6 | `register_fidelity` | *Does he still sound right to David?* | — | **Blocked.** No verified register signal exists; scoring it from text would be exactly the language-learning ADR-Exec-005 forbids. | stable high | **deferred — see §2.6 Q-XVII-2.1** |

**Two supporting counters (diagnostic, not headline):**

| Counter | Why it exists |
|---|---|
| `scope_coverage` — distinct lesson `scope` values with ≥1 confirmed lesson | The live ledger has produced only `capability` (376) and `behaviour` (1). `preference`, `relationship`, `creative` have **never** been produced. A coverage of 1–2 is a symptom that the *writer* is a template, not that eLo's life is narrow. (Ch.1 §1.3.5.) |
| `verified_evidence_share` — `verified:true` evidence items / all evidence items | The single most important honesty number in the system. If it trends toward 0, eLo is accumulating talk. Today it is **0.0** — no evidence item is a resolvable `episode_ref` at all. |

**Metric rules (MUST):**

- Every metric carries its **window** (`session | 7d | 30d`), its **sample size**, and its
  **as-of timestamp**. A metric over 3 episodes is not a trend and must not be reported as
  one. **A metric with `n < 10` is reported as `insufficient_evidence`, never as a value.**
- Metrics are exposed read-only via `lesson_store.stats()` (`LEARNING_LOOP_v1.md §8`).
  No other module computes them; there is one definition of each number.
- `identity_stability` is written to the metrics store like the others but is **flagged
  `guardrail: true`** so no future optimiser can treat it as an objective.
- Absent data is `null` with a reason, never `0.0`. A zero and a nothing are different
  facts, and conflating them is the same fabrication error the canon forbids everywhere else.

## 2.3 How improvement is evidenced

This is the section Vol V Ch.6 left unwritten, and it is the substance of David's question.

**A claim is not evidence. A single number is not evidence. Evidence is a paired
before/after measurement on a named cause, over a stated window, with a stated sample.**

The evidence unit:

```jsonc
ImprovementEvidence {
  "cycle_id":     "IC-2026-08-13-001",
  "cause":        "surface_offline",      // the specific thing being improved
  "metric":       "repeat_failure_rate",
  "window":       "7d",
  "before":       { "value": 0.42, "n": 24, "as_of": "2026-08-13T…" },
  "after":        { "value": 0.19, "n": 31, "as_of": "2026-08-20T…" },
  "intervention": { "lesson_key": "sha1…", "action": "strengthened", "status_at_close": "confirmed" },
  "verdict":      "improved | no_effect | regressed | insufficient_evidence",
  "closed_at":    "2026-08-20T…"
}
```

**Evidence rules (MUST):**

1. **A before-value must be recorded at the moment of intervention, not reconstructed
   afterwards.** A retrospectively-computed baseline is unfalsifiable. If no before-value
   was captured, the verdict is `insufficient_evidence` — never `improved`.
2. **One cause per cycle.** Strengthening three lessons at once and observing an
   improvement evidences nothing about any of them.
3. **The verdict is computed, not chosen.** `improved` requires the metric to move in the
   declared direction by a margin larger than the window's own noise, with `n ≥ 10` in
   both windows. Everything else is `no_effect`, `regressed`, or `insufficient_evidence`.
4. **`no_effect` and `regressed` are recorded with the same weight as `improved`.** A
   growth record that only contains successes is a marketing document. eLo's own
   `failure_log` discipline (*"these are facts, not failures"*, Ch.6 §6.3) applies to the
   improvement record too.
5. **The evidence is only as good as `verified_evidence_share`.** An `ImprovementEvidence`
   whose intervention rested on unverified episodes is annotated as such and does not count
   toward capability growth in Vol XVIII §1.2.

## 2.4 The Improvement Cycle

Vol V Ch.6 §6.8's five steps, made executable. Runs on the **periodic cadence only**
(Ch.6 §6.2 — daily/weekly/monthly), in the integration window, never in a turn.

```
┌── OPEN ─────────────────────────────────────────────────────────────┐
│ 1. READ    GrowthMetrics + Lessons Ledger + Failure Log             │
│ 2. SELECT  the single highest repeat_failure_rate cause             │
│            (ties → the cause with the larger n; still tied → oldest)│
│ 3. RECORD  the before-measurement NOW — value, n, as_of             │
│ 4. ACT     form or strengthen exactly ONE lesson targeting that     │
│            cause; if trait-scoped and confirmed → PersonalityDelta  │
│            → Vol V Ch.7 §7.5 gate (never self-applied)              │
│ 5. WAIT    one full period. No re-measurement inside the window.    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ next periodic tick
┌── CLOSE ────────────────────────────────────────────────────────────┐
│ 6. MEASURE the same metric, same cause, same window length          │
│ 7. VERDICT computed per §2.3 rule 3                                 │
│      improved              → CONFIRM the lesson (it earned it)      │
│      no_effect             → RETIRE the lesson (reason: no_effect)  │
│      regressed             → RETIRE + record the cause as adverse   │
│      insufficient_evidence → EXTEND one period (max 3 extensions,   │
│                              then close as insufficient_evidence)   │
│ 8. WRITE   the ImprovementEvidence record. Cycle is CLOSED.         │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.4.1 What closes a cycle

A cycle is **closed** — and only closed — when **all four** hold:

1. A before-measurement exists, captured at OPEN (§2.3 rule 1).
2. A full period has elapsed with no intervening intervention on the same cause.
3. An after-measurement exists on the same metric, cause, and window length.
4. A verdict has been computed and an `ImprovementEvidence` record written.

A cycle that cannot satisfy all four closes as `insufficient_evidence`. **It never
silently disappears, and it is never re-opened to get a better answer.** A cycle
"closed" by asserting improvement is not a closed cycle; it is a claim, and the
Reflection Engine exists precisely to stop eLo making those.

### 2.4.2 Cycle rules (MUST)

- **One open cycle per cause at a time.** Concurrent cycles on different causes are
  allowed; concurrent cycles on the *same* cause are not — they make attribution impossible.
- **Recommended concurrency: ≤3 open cycles.** More than that and the periodic pass is
  changing more of eLo than it can attribute.
- **No mid-window peeking, and no mid-window intervention.** Reading the metric early is
  harmless; *acting* on it invalidates the cycle and it must close as
  `insufficient_evidence`.
- **A cycle may never target `identity_stability`.** It is a guardrail (§2.1.5). An attempt
  to open a cycle against a guardrail metric is a bug, and the pass must refuse it.
- **A cycle's intervention is bounded to the write-allow list** (Ch.1 §1.4.1). Improvement
  is achieved by strengthening a lesson, never by editing code, prompts, or the Executive.
- **Cycles are slow by design.** Vol V Ch.6 §6.8: *"improvement is integrated, never
  reactive to a single conversation."*

## 2.5 Faculty Contract

Metrics and cycles are components of the `ReflectionGrowthEngine` (Vol V Ch.6 §6.9,
unchanged). Law 1 (Vol XXII) — one faculty, one purpose. Additions only:

```
Faculty:          ReflectionGrowthEngine       (Vol V Ch.6 §6.9 — unchanged)
Components:       growth_metrics · improvement_cycle
runs_in:          integration-window ONLY  (never the response path, never a prompt)

ADDITIONAL Inputs:
  - type:        lesson_lifecycle_event
    source:      lesson_store (Ch.1 §1.5)
    required:    true
    description: promoted | demoted | retired | revived — the raw material for M3, M5.
  - type:        outcome_record
    source:      the ACK resolution points (server.py:2595-2766)
    required:    true for M1
    description: completion state per intent. Without it, M1 is null, never 0.0.
  - type:        personality_version
    source:      personality_evolution_faculty changelog (Vol V Ch.7 §7.6)
    required:    false
    description: trait variance for M4. Absent → M4 = null (no versions yet is not stability).

ADDITIONAL Outputs:
  - type:        growth_metrics
    destination: metrics store (read-only via lesson_store.stats()); periodic review; Audit
    description: Each value carries window, n, as_of, and guardrail flag. Never a prompt input.
  - type:        improvement_evidence
    destination: metrics store + Growth Journal (Vol V Ch.6 §6.6) + Vol XVIII §1.2
    description: A closed cycle: cause, before, after, intervention, computed verdict.

ADDITIONAL Failure Modes:
  - condition: n < 10 in either window
    fallback:  report insufficient_evidence; do NOT report a value; do NOT close as improved.
  - condition: no before-measurement was captured at OPEN
    fallback:  the cycle closes as insufficient_evidence. Never reconstruct a baseline.
  - condition: an intervention landed inside the window
    fallback:  invalidate the cycle, close as insufficient_evidence, log the collision.
  - condition: metrics store unwritable
    fallback:  skip the pass, preserve prior metrics intact, retry next window.
               Reflection degrades to silence, never to an estimate.
  - condition: a metric is requested during a turn
    fallback:  refuse. Metrics never enter the response path (Vol V Ch.6 §6.7).
  - condition: a cycle is opened against a guardrail metric
    fallback:  refuse and log as an anomaly (§2.4.2).
```

## 2.6 Faculty Lifecycle

Universal lifecycle (`CONTRACTS.md §3`). Metrics live entirely in the integration window.

```
BOOT → REGISTER → INITIALISE   load metrics store + any OPEN cycles (survive restart)
   ↓
READY                          idle
   ↓
ACTIVE (response path)         NOT REACHED. Metrics never run in a turn (§2.1.3).
   ↓
WAITING / SLEEPING             ── periodic tick, integration window ──
   ├─ Learn      recompute M1–M5 + the two counters over their windows
   ├─ Validate   any trait-scoped intervention → Vol V Ch.7 §7.5 gate
   └─ Update     write metrics; OPEN or CLOSE cycles; emit ImprovementEvidence
   ↓
ACTIVE → ERROR → RECOVERY → READY    (prior metrics preserved; no partial cycle writes)
READY → SHUTDOWN
```

**Rules (MUST):**

- An OPEN cycle **survives a restart**. A cycle lost to a process restart has silently
  discarded a before-measurement, which is the one thing §2.3 rule 1 forbids reconstructing.
- Metric recomputation is **idempotent**: running the pass twice in one period produces the
  same values and does not advance any cycle.
- `Learn → Update` without `Validate` remains forbidden for anything personality-adjacent.

## 2.7 Message Envelope Binding

Per `CONTRACTS.md §2`. Vol V Ch.6 §6.11's envelope stands; `growth_metrics` was already a
declared payload type there. One addition:

```jsonc
{
  "id": "uuid",
  "sender": "ReflectionGrowthEngine",
  "receiver": "Memory | *",
  "priority": "low",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "high" }
  },
  "payload": {
    "type": "growth_metrics | improvement_evidence",
    "body": { }
  },
  "confidence": 0.0,               // sample-size-derived reliability; 0.0 when n < 10
  "expires": null,                 // a measurement of the past does not expire
  "trace": ["ReflectionGrowthEngine@ts"]
}
```

**Binding rules (MUST):**

- `receiver` MUST NOT be the Executive or any response-path consumer. Metrics are not
  turn inputs (§2.1.3).
- `confidence` MUST be `0.0` when any reported metric has `n < 10`, so a thin measurement
  cannot travel as a strong one.
- An `improvement_evidence` payload MUST carry both `before` and `after` blocks including
  their `n` and `as_of`. A verdict without both is malformed and is rejected.

## 2.8 Acceptance Tests

### Functional

```
FT-1  Metrics compute from existing artefacts only
  Given:  a populated ledger, growth journal, failure log, and personality changelog
  When:   the periodic pass runs
  Then:   M1–M5 and both counters are produced
          AND no new daemon, capture path, or store beyond the counters file was created

FT-2  Thin data reports insufficient_evidence, not a number
  Given:  a window containing 4 episodes
  When:   metrics compute
  Then:   the affected metrics report insufficient_evidence with n=4
          AND no numeric value is emitted

FT-3  A cycle opens with a recorded before-measurement
  Given:  repeat_failure_rate highest for cause="surface_offline"
  When:   the cycle opens
  Then:   a before block with value, n, and as_of is persisted BEFORE any intervention
          AND exactly ONE lesson is formed or strengthened

FT-4  A cycle closes on a computed verdict
  Given:  an open cycle, one full period elapsed, n ≥ 10 in both windows
  When:   the next periodic pass runs
  Then:   an ImprovementEvidence record is written with a computed verdict
          AND on improved the lesson is confirmed; on no_effect it is retired

FT-5  Absent data is null with a reason, never zero
  Given:  no personality versions exist yet
  When:   metrics compute
  Then:   identity_stability = null with reason="no_versions"
          AND it is NOT reported as 0.0 (perfect stability)

FT-6  Scope coverage exposes the template writer
  Given:  the live ledger (only `capability` and `behaviour` ever produced)
  When:   metrics compute
  Then:   scope_coverage reports 2 of 5 with the produced scopes named
```

### Stability

```
ST-1  Metrics never reach a turn
  Given:  200 turns while metrics exist
  When:   each turn assembles its prompt
  Then:   no metric value appears in CognitiveState, the snapshot, or the prompt
          AND no plan differs because a metric changed

ST-2  identity_stability cannot be optimised
  Given:  an attempt to open an improvement cycle targeting identity_stability
  When:   the pass runs
  Then:   the cycle is REFUSED and logged as an anomaly
          AND a RISE in identity_stability is surfaced as an ALARM, not as growth

ST-3  A retrospective baseline is impossible
  Given:  an intervention was applied with no before-measurement
  When:   the cycle closes
  Then:   the verdict is insufficient_evidence
          AND no baseline is reconstructed from history

ST-4  Failure is recorded with equal weight
  Given:  a cycle whose metric worsened
  When:   it closes
  Then:   an ImprovementEvidence record with verdict=regressed is written and retained
          AND the targeting lesson is retired with that reason

ST-5  Cycles survive restart
  Given:  an open cycle and a process restart
  When:   the next periodic pass runs
  Then:   the cycle is still open with its original before block intact

ST-6  Idempotent recomputation
  Given:  the periodic pass runs twice inside one period
  When:   both runs complete
  Then:   metric values are identical AND no cycle advanced twice
```

### Integration

```
IT-1  The full measured loop
  verified outcomes → ledger lifecycle events
        ↓
  GrowthMetrics (M1–M5)
        ↓
  Improvement Cycle OPEN (before recorded) → lesson strengthened
        ↓  one period
  Improvement Cycle CLOSE (after measured) → verdict → ImprovementEvidence
        ↓
  Growth Journal entry + Vol XVIII §1.2 capability-growth record
  Assert: David can be shown a before/after pair on a named cause with sample sizes,
          not a sentence claiming eLo improved.

IT-2  Metrics and the personality gate agree
  Given:  a cycle whose intervention is a trait-scoped confirmed lesson
  When:   it is applied
  Then:   it passed Vol V Ch.7 §7.5 validation, moved ≤ MAX_STEP (0.02),
          AND identity_stability rose by less than the alarm threshold
          AND the Identity Kernel hash is unchanged
```

## 2.9 Implementation Notes (for the Builder)

- Build the four `LEARNING_LOOP_v1.md §8` metrics first (M1–M4); M5 falls out of M3's
  lifecycle counting. **Do not build M6.** Its blocker is real, not a scheduling choice.
- Expose everything read-only through `lesson_store.stats()`. One definition per number.
- The metrics store is a small counters/history JSON alongside the ledger. It is on the
  write-allow list (Ch.1 §1.4.1); nothing else is.
- Persist OPEN cycles to disk immediately at OPEN. An in-memory cycle is a lost baseline.
- The first honest report will read badly — `verified_evidence_share: 0.0`,
  `lesson_yield: 0.0`, `scope_coverage: 2/5`. **Ship it exactly like that.** A true zero is
  the baseline every later number is evidenced against, and it is the first time the system
  has told the truth about itself.

## 2.10 Open Questions — needs David

- **Q-XVII-2.1 — `register_fidelity` (M6).** Vol V Ch.6 §6.7 names it; there is no verified
  signal for it. Scoring "did eLo match David's register" from text is exactly the
  language-derived learning ADR-Exec-005 D1 forbids. **Options:** (a) drop M6 from canon;
  (b) keep it and source it from an explicit low-friction David signal (a thumbs-down is a
  verified consequence — a real observation, not an inference); (c) keep it as a
  *diagnostic* from the WO-070 shadow log's `delta_cause: "style"` rate — measurable, and
  explicitly **not** a training target (`LEARNING_LOOP_v1.md §6.3`). **Architect
  recommendation: (c) as a diagnostic, never as a reward.** Needs David because it touches
  the ADR-Exec-005 line.
- **Q-XVII-2.2 — the periodic cadence.** Vol V Ch.6 §6.2 says daily/weekly/monthly without
  choosing. The improvement cycle's window length is set by this. **Architect
  recommendation: weekly cycles with 7-day metric windows** — long enough for `n ≥ 10`,
  short enough that David sees a verdict inside a fortnight. Confirm or override.
- **Q-XVII-2.3 — the alarm threshold on `identity_stability`.** A number that says "eLo is
  changing too fast" is an identity-adjacent judgement, which makes it David's, not the
  Architect's. **Architect starting proposal: alarm when 30-day trait variance exceeds
  3 × MAX_STEP (0.06) on any single trait.** Flagged, not set.

## 2.11 Architecture References

- `Volume_V/06_Reflection_Growth_Engine.md` §6.7, §6.8 — **origin text** (prose; 0% built).
- `Volume_V/07_Personality_Evolution_Engine.md` §7.6 — PersonalityVersion changelog (M4's source).
- `Volume_XVII/01_Reflection_and_the_Lesson_Ledger.md` — the ledger and lifecycle events these metrics read.
- `Volume_XVIII/01_Self_Evolution_and_Versioning.md` §1.2 — a closed cycle is the unit of capability growth.
- `LEARNING_LOOP_v1.md` §8 — the minimum viable slice; §4 — where OutcomeRecords come from.
- `adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` — why a metric may never be a reward.
- Code (sources, all live): `self/lessons_ledger.jsonl` · `self/journals/growth_journal.jsonl` ·
  `self/failure_log.jsonl` · `self/personality_vector.json` ·
  `faculties/personality/personality_evolution_faculty.py` (MAX_STEP, identity hash) ·
  `server.py:2595-2766` (ACK resolution → OutcomeRecord).

---

```
Chapter 2 — Growth Metrics and the Improvement Cycle
Status: READY FOR REVIEW
Files: Volume_XVII/02_Growth_Metrics_and_the_Improvement_Cycle.md
Faculty Contract: Included (additions to Vol V Ch.6 §6.9)
Lifecycle State Machine: Included (integration-window only)
Message Envelope: Included (growth_metrics + improvement_evidence)
Acceptance Tests: Included (FT ×6, ST ×6, IT ×2)
Architecture References: Included
Closes: Vol V Ch.6 §6.7/§6.8 — named in prose since 2026-07-26, 0% implemented
Does NOT duplicate: Vol V Ch.6 (origin text, referenced by section)
```

READY FOR REVIEW
