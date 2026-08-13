---
id: WO-095
title: "Learning Loop v1 — close the read side (promotion · recall · verified-outcome reward)"
status: OPEN            # OPEN | IN_PROGRESS | IN_REVIEW | DONE
target_agent: Builder
priority: P0            # David's headline ask — "get the brain to think more, learn"
owner: Builder (eLo OS)
gated: false            # NOT gated. Nothing blocks the start.
depends_on: []          # three items need David L3 (§10) but NONE of them block §Scope A–D
blocks: [WO-094 §D, WO-CANON-XXVIII]
spec_refs:
  - docs/architecture/LEARNING_LOOP_v1.md          # the authoritative spec — read it first
  - docs/architecture/Volume_V/06_Reflection_Growth_Engine.md   # §6.4 §6.5 §6.7 §6.8
  - docs/architecture/Volume_V/05_Significance_Engine.md
  - docs/architecture/Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md
  - docs/architecture/Volume_IX/00_Metadata.md     # :9 :53 — the PENDING reinforce() edge
  - docs/architecture/DECISION_LOG.md              # ADR-Exec-001 / 003 / 005 · FC-2
audit_gap: "AUDIT_MASTER_2026-08-10 §1 (write-only loop) + §2 (reward from language)"
created: 2026-08-11
---

# WO-095 — Learning Loop v1: close the read side

## 1. Objective (one sentence)
Make eLo actually learn: build the missing **read side** of the learning loop — something that
reads the lessons ledger, promotes lessons on **verified** evidence, changes the next turn's
behaviour, and computes its reward from a **body ACK** rather than from conversation text.

## 2. Why now — the verified problem

Independently verified against the live repo 2026-08-11 (not taken from the audit on faith):

- `self/lessons_ledger.jsonl` = **376 lessons, 376 of them `status: candidate`. Zero confirmed,
  ever.** **374** are the identical sentence. All 376 are `scope: capability`.
- `self/journals/growth_journal.jsonl` = **815 entries.**
- **Nothing in the codebase reads either file.** The only reference is the writer,
  `runtime/reflection_faculty.py:29` / `:149` / `:154`.
- `runtime/reflection_faculty.py:97-99` hardcodes `strength 0.3, status candidate` and no code
  path ever touches that record again. `:104-113` shows the "lessons" are a three-branch
  string template.
- `faculties/personality/personality_evolution_faculty.py:222-228` rejects any delta whose
  `strength != "confirmed"` — so **channel 2 is dead by construction**, and that whole file is
  imported by nothing outside its own test.
- `memory/significance_engine.py:167-208` `evaluate()` takes **only text** and scores it with
  keyword tables (`:44-71`). No outcome input, no ACK input. Canon tells you to use this as the
  reward → building it as written ships an **ADR-Exec-005 violation on day one**.

Result: eLo captures and never reads. There is no measurable sense in which he is better today
than in July. This is the cheapest thing on the whole audit list to fix, and it is David's #1 ask.

## 3. Read these first
1. **`docs/architecture/LEARNING_LOOP_v1.md`** — the spec. §2 (the loop + the named missing
   pieces), §3 (promotion thresholds), §4 (OutcomeRecord + the reward rule), §5 (one Significance
   vector), §6 (the ADR-Exec-005 write-allow / write-deny lists), §7 (the three loops).
2. Vol V Ch.6 §6.4 / §6.5 / §6.7 / §6.8 — this WO implements prose that already exists.
3. ADR-Exec-005 row in `DECISION_LOG.md` — the governing law.

## 4. Deliverable

### A. `self/lesson_store.py` — **NEW. This is the missing reader.**
Reads and rewrites the **existing** `self/lessons_ledger.jsonl`. **Do not create a second
store** (Check-Before-Build). `reflection_faculty.py` keeps writing; this reads and promotes.
```python
record_outcome(lesson_key, outcome, episode_ref) -> dict
promote_pass() -> dict        # periodic ONLY; the sole writer of `status`
recall(scope, context, k=3) -> list[dict]     # CONFIRMED lessons only
stats() -> dict               # GrowthMetrics (spec §8)
```
- Lesson identity = `sha1(scope|normalised_statement|cause)`. A repeat **strengthens an existing
  record**; it does not append a duplicate row. (This is the root cause of the 374.)
- Evidence = a resolvable **SPOT code** (`integrate_session()` already returns it as `spot`), not
  a text truncation, and each item carries `verified: bool`.
- Thresholds exactly as spec §3.4: `+0.15` confirm / `-0.20` contradict / `-0.02` per idle week;
  **confirm at `strength ≥ 0.70` AND ≥3 distinct episode_refs AND ≥2 sessions AND ≥2 verified**;
  demote `<0.50`; retire `<0.20` or 3 consecutive contradictions or 60 idle days.
- **Nothing is deleted.** Retired rows keep `retired_at` + `reason`.
- New record schema: spec §3.6.

### B. `OutcomeRecord` — the verified-outcome signal
Emit it **where the ACK is already resolved** — `server.py:2605-2611` (`sit_complete`),
`:2689-2695` (`move_complete`), `:2760-2766` (`exit_complete`), and their **15s timeout
branches** (`:2595`). **Do not build a second ACK channel.**
Fields per spec §4.1. A **timeout is evidence**: `ack_received:false`, `completion:"timeout"`,
`verified:true` — negative confirming evidence, and today it is computed and thrown away.

### C. Reward from outcomes, not language
- `memory/significance_engine.py:167` gains **optional** `outcome=None`. With `outcome=None` the
  behaviour is byte-identical to today, so `memory/journal_router.py:120` and
  `faculties/significance/significance_faculty.py:143` are unaffected.
- Add the three outcome dimensions — **embodiment · efficiency · safety** — scored **from the
  OutcomeRecord only, never from text** (definitions: spec §5.1). Each returns `0.0` when
  `outcome is None`.
- `reward = 0.70 * outcome_terms + 0.30 * significance_terms`, with three asserted rules:
  1. `verified == False` → `outcome_terms = 0` **and** no strengthen / promote / PersonalityDelta.
  2. Significance contributes, never decides — capped at 0.30, never the sole promotion input.
  3. No OutcomeRecord → no learning update at all.

### D. Recall into the turn + the first live PersonalityDelta
- `runtime/cognitive_snapshot.py:99` `build_snapshot()` gains `lessons: tuple[str, ...]` from
  `recall(...)`. **Bounded: ≤3 lessons, ≤240 chars total** — same discipline as WO-071's
  ≤600-char correction frame. Never crowd the prompt.
- `runtime/prompt_builder.py` renders it as a labelled *learned heuristic* hint block — never
  as fact.
- `promote_pass()` emits `PersonalityDelta(sender="ReflectionGrowthEngine", strength="confirmed",
  evidence=(episode_refs…))` → `validate_delta()` → `apply_delta()` → `save_personality()`.
  **This is the first live caller of `personality_evolution_faculty.py` in the repo's history.**

### E. GrowthMetrics minimum slice (Vol V §6.7 — today 0%)
`intention_realisation` · `repeat_failure_rate` · `reinforcement_ratio` · `identity_stability`,
via `lesson_store.stats()`. Read-only. **Never enters the response path.**
`identity_stability` is a **guardrail — rising is an alarm, not progress.**

### F. Vol IX `reinforce()` edge (small, near-term loop (b))
In the dream wake/integration path, call `memory.consolidation_faculty.reinforce(spot, steps=1)`
for each NREM `memory_ref`. Guards: only refs resolving to an existing SPOT (the function already
no-ops otherwise, `consolidation_faculty.py:170-172`); **a dream may never create, edit or
contradict a record — weight only**; `steps=1` max per record per cycle; ≤5 refs per cycle.

## 5. Files likely touched
- `self/lesson_store.py` — **NEW** (the reader/promoter)
- `self/lessons_ledger.jsonl` — new schema on new rows; pre-v1 rows handled per §7 below
- `memory/significance_engine.py` — additive `outcome=` kwarg + 3 outcome dims
- `server.py` — emit `OutcomeRecord` at the existing ACK/timeout resolution points
- `runtime/cognitive_snapshot.py` — `lessons` on the snapshot
- `runtime/prompt_builder.py` — bounded hint block
- `runtime/reflection_faculty.py` — write the real `episode_ref` (the `spot` it already has) into
  `evidence` instead of `session_summary[:120]`, and the dedupe `lesson_key`
- `faculties/dream/…` — the `reinforce()` call
- `tests/test_wo095_learning_loop.py` — **NEW**

## 6. Files/things you MUST NOT touch
- `runtime/executive.py`, `prompts/` — FREEZE_V1_LOCK
- `faculties/personality/personality_evolution_faculty.py` — **call it, do not weaken it.** The
  `confirmed` requirement at `:222-228`, `MAX_STEP` at `:31`, and the Identity Kernel floors at
  `:36-38` are the guard. If a delta is rejected, that is the system working.
- Vault record **content** — learning may raise a weight; it may never create, edit or contradict
  a memory record.
- The DISENELO apps in `~/Desktop/Output/` (D-I) — Builder write-scope is `~/elo-ai/` only.
- Do **not** delete any existing lesson row (see §7).

## 7. Pre-v1 ledger rows
The 374 identical rows are a template artefact of `reflection_faculty.py:104-113`, not evidence.
**Recommended (non-destructive):** move all pre-v1 rows to `self/lessons_ledger_pre_v1.jsonl`
untouched and start the v1 ledger clean. If David prefers, mark them in place as
`status: retired`, `reason: "pre-v1 template artefact"`. **Either way: nothing is deleted.**
This is spec §10 D3 — if David has not answered when you reach it, take the archive option
(it is reversible) and note it in the handback.

## 8. Acceptance tests (Definition of Done) — `tests/test_wo095_learning_loop.py`

**The four that prove the loop is real:**
- [ ] **AT-1 — a lesson gets promoted on evidence.** Feed 3 distinct verified episodes across
      2 sessions for one `lesson_key` → `status` flips `candidate → confirmed`, `strength ≥ 0.70`,
      3 resolvable `episode_ref`s recorded. With only 2 episodes, or only 1 session, or only 1
      verified: it stays `candidate`.
- [ ] **AT-2 — something READS the ledger and behaviour changes.** After AT-1, a fresh
      `build_snapshot()` contains that lesson in `CognitiveSnapshot.lessons`, and the built prompt
      contains the hint block. Assert the read occurred (not just that the file exists), and assert
      the ≤3 / ≤240-char bound holds.
- [ ] **AT-3 — reward is computed from a verified ACK, not from text.** Two runs with *identical*
      `raw` and `response`; one with `OutcomeRecord{ack_received:true, completion:"met"}`, one with
      `{ack_received:false, completion:"timeout"}` → **different rewards**, and the unverified run
      produces **zero** strengthen / promote / PersonalityDelta. Also: `evaluate()` called with no
      `outcome` returns exactly today's values (back-compat regression).
- [ ] **AT-4 — nothing in the learning path can write identity.** Run a full learning pass, then
      assert: `personality_evolution_faculty.compute_identity_hash()` unchanged · identity fields in
      `self/elo_self_state.json` unchanged · vault record **content** byte-identical · `runtime/
      executive.py` and `prompts/` untouched · any delta exceeding `MAX_STEP` or breaching a kernel
      floor is **rejected** and the lesson stays `candidate`.

**Supporting:**
- [ ] AT-5 — a repeat lesson **strengthens an existing record**; the ledger does not grow a
      duplicate row (the 374 bug cannot recur).
- [ ] AT-6 — contradiction demotes: `confirmed` → `candidate` below 0.50; 3 consecutive
      contradictions → `retired` with `reason` recorded; nothing deleted.
- [ ] AT-7 — `stats()` returns the four metrics and they move in the right direction across a
      simulated good period and a simulated bad period. `identity_stability` rising is reported
      as an **alarm**, not as growth.
- [ ] AT-8 — Vol IX edge: a dream naming a real SPOT raises its weight by exactly 1, once; a dream
      naming a non-existent SPOT is a silent no-op; **no new record is ever created by a dream**.
- [ ] AT-9 — `promote_pass()` never runs in the response path; response-path latency is unchanged.
- [ ] AT-10 — Regression: `journal_router` and `significance_faculty` behave exactly as before
      (they call `evaluate()` without `outcome`).

## 9. Definition of Done
Every AT-1…AT-10 green · committed with hash · no FREEZE_V1_LOCK file touched · handback per
`COMPLETION_LOG.md` with the test output attached · **and**:

> **David's bar: eLo visibly gets better at something over repeated use.**
> Not "the tests pass" — demonstrate it. Show the same situation twice, N uses apart, and show the
> second one going better *because a confirmed lesson was recalled*, with `stats()` backing it.
> If you cannot demonstrate that, this WO is not done.

## 10. Open items that do NOT block this WO (David L3 — spec §10)
- **D1** — the LoRA-on-speech contradiction (Vol XXVIII forbids learning speech correctness, then
  specifies a LoRA that does it). Resolution recommended in spec §6.3: tag every WO-070 shadow row
  with `delta_cause: style|verification|l3_override` and **train only on `style`**. **This WO does
  not touch the LoRA path** — it is flagged so the Builder does not build toward the contradiction.
- **D2** — closing FC-2 in the DECISION_LOG (one Significance vector). Adding the three outcome
  dims is safe and additive either way; the canon edit is David's.
- **D3** — pre-v1 ledger rows (see §7). Default to the reversible archive.
- **D4** — Volume V's "ratified / verify-only" status vs Ch.6 being unbuilt. Governance, not code.

## 11. Risks / footguns
- **Do not weaken the personality validator to make a test pass.** A rejected delta is correct
  behaviour. If nothing ever promotes, the *evidence* is the problem, not the gate.
- **Do not let significance sneak back in as the sole reward.** The 0.30 cap and the
  `verified == False → 0` rule are the whole point of this WO.
- **Do not put `promote_pass()` in the response path.** Integration window only (Vol V Ch.6 §6.0).
- **Bound the prompt injection.** ≤3 lessons / ≤240 chars. An unbounded hint block will quietly
  degrade every reply.
- **Recall must be honest.** A recalled lesson is a heuristic, not a fact. It must never let eLo
  claim something happened that no ACK confirmed (ADR-Exec-001).

## 12. Handback
Set WO-095 → `IN_REVIEW` on the board · append a Completion Record to `COMPLETION_LOG.md` ·
attach test output + the "visibly better" demonstration from §9 · move the queue card to `DONE/`
and take the next card.
