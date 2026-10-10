# 00_WO-095_learning_loop.md

**WO:** WO-095 · **Seat:** builder · **Priority:** P0 · **Reserved?** no · **Take this FIRST**

## Goal
Make eLo actually learn. Build the missing **read side** of the learning loop: something that
reads the lessons ledger, promotes lessons on **verified** evidence, changes the next turn, and
computes reward from a **body ACK** instead of from conversation text.

## The verified problem (checked against the live repo 2026-08-11 — not from a summary)
- `self/lessons_ledger.jsonl`: **376 lessons, 376 `candidate`. Zero confirmed, ever.** 374 are the
  same sentence. `growth_journal.jsonl`: 815 entries.
- **Nothing reads either file.** Only reference is the writer — `runtime/reflection_faculty.py:29`/`:149`/`:154`.
- `reflection_faculty.py:97-99` hardcodes `strength 0.3 / status candidate`, never touched again.
- `personality_evolution_faculty.py:222-228` rejects anything not `confirmed` → **channel 2 is dead
  by construction**, and that file is imported by nothing outside its own test.
- `memory/significance_engine.py:167-208` `evaluate()` takes **only text**, keyword-scored (`:44-71`).
  Canon says use it as the reward → building it as written = **ADR-Exec-005 violation on day one**.

## Scope — exactly this
- **`self/lesson_store.py` (NEW)** — the reader. `record_outcome()` · `promote_pass()` (periodic
  only; sole writer of `status`) · `recall()` (confirmed only) · `stats()`. Reads/rewrites the
  **existing** ledger — no second store. Lesson identity = `sha1(scope|statement|cause)` so repeats
  **strengthen** instead of appending (that's the 374 bug). Evidence = a resolvable SPOT code, each
  tagged `verified: bool`. Thresholds: spec §3.4.
- **`OutcomeRecord`** — emit where the ACK already resolves: `server.py:2605` (`sit_complete`),
  `:2691` (`move_complete`), `:2762` (`exit_complete`) **and the 15s timeout branches** (`:2595`).
  No second ACK channel. **A timeout is evidence** and is currently thrown away.
- **Reward from outcomes** — `significance_engine.evaluate()` gains optional `outcome=None`
  (back-compatible; existing callers untouched) + three dims scored **from the OutcomeRecord only**:
  **embodiment · efficiency · safety**. `reward = 0.70*outcome + 0.30*significance`. Hard rules:
  `verified==False` → outcome terms 0 and **no** strengthen/promote/delta; significance capped at
  0.30 and never the sole promotion input; no OutcomeRecord → no learning update.
- **Recall into the turn** — `cognitive_snapshot.build_snapshot()` gains `lessons` (**≤3, ≤240
  chars**) → `prompt_builder.py` bounded hint block, labelled as heuristic, never as fact.
- **First live PersonalityDelta** — `promote_pass()` → `validate_delta()` → `apply_delta()`.
  **Call the validator; do NOT weaken it.** A rejection is the system working.
- **GrowthMetrics slice** — `intention_realisation · repeat_failure_rate · reinforcement_ratio ·
  identity_stability` via `stats()`. Read-only, never in the response path. Rising
  `identity_stability` is an **alarm**, not progress.
- **Vol IX edge** — dream `memory_refs` → `consolidation_faculty.reinforce(spot, steps=1)`. Weight
  only: **a dream may never create, edit or contradict a record.** ≤5 refs/cycle.

## Files likely touched
`self/lesson_store.py` (NEW) · `memory/significance_engine.py` · `server.py` ·
`runtime/cognitive_snapshot.py` · `runtime/prompt_builder.py` · `runtime/reflection_faculty.py`
(real `episode_ref` + dedupe key) · `faculties/dream/…` · `tests/test_wo095_learning_loop.py` (NEW)

## MUST NOT touch
`runtime/executive.py` · `prompts/` (FREEZE_V1_LOCK) · the personality validator's `confirmed`
requirement / `MAX_STEP` / Identity Kernel floors · vault record **content** · `~/Desktop/Output/`.
**Do not delete any existing lesson row** — archive pre-v1 rows to `lessons_ledger_pre_v1.jsonl`.

## Test (without David) — `tests/test_wo095_learning_loop.py`
- **AT-1** a lesson **promotes on evidence**: 3 verified episodes / 2 sessions → `confirmed`;
  2 episodes, or 1 session, or 1 verified → stays `candidate`.
- **AT-2** something **READS the ledger and behaviour changes**: the confirmed lesson appears in
  `CognitiveSnapshot.lessons` and in the built prompt; ≤3 / ≤240-char bound holds.
- **AT-3** **reward from a verified ACK, not text**: identical text, one `ack_received:true`, one
  `timeout` → different rewards; the unverified one produces **zero** learning update. Plus
  back-compat: `evaluate()` with no `outcome` returns today's exact values.
- **AT-4** **nothing in the learning path writes identity**: kernel hash unchanged · self-state
  identity fields unchanged · vault content byte-identical · executive/prompts untouched ·
  over-MAX_STEP or floor-breaching deltas rejected, lesson stays `candidate`.
- AT-5 repeat strengthens, no duplicate row · AT-6 contradiction demotes/retires, nothing deleted ·
  AT-7 `stats()` moves correctly, `identity_stability` rise = alarm · AT-8 dream reinforce +1 once,
  no-op on unknown SPOT, never creates · AT-9 `promote_pass()` never in the response path ·
  AT-10 `journal_router` + `significance_faculty` regression clean.

## Done when
All ATs green + committed → hash, DONE/, outbox, next card — **plus David's bar:**
> **eLo visibly gets better at something over repeated use.** Demonstrate it: the same situation
> twice, N uses apart, the second going better *because a confirmed lesson was recalled*, with
> `stats()` backing it. Tests passing alone is NOT done.

## Flagged for David (do not build toward these; they don't block you)
D1 the LoRA-on-speech contradiction (Vol XXVIII forbids learning speech correctness then specifies
a LoRA that does it — recommended fix: tag shadow rows `delta_cause: style|verification|l3_override`
and **train only on `style`**; **this WO does not touch the LoRA path**) · D2 closing FC-2 ·
D3 pre-v1 ledger rows (default: reversible archive) · D4 Vol V's ratified status.

**Spec:** `docs/architecture/LEARNING_LOOP_v1.md` (read §2–§7 first)
**WO:** `engineering/work_orders/WO-095_Learning_Loop_Close_The_Read_Side.md`

## Result
- commit: 0a202f0
- test: 10/10 AT (promote on evidence, snapshot read-through, reward ACK-vs-unverified, identity isolation, dedup, back-compat, stats, response-path gate, regression, pre-v1 migration)
