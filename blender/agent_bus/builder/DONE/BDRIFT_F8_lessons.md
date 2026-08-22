# BDRIFT-F8 — Lessons: Verified Consequence → Lesson Candidate Write Side

SOURCE: `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_F7_F8_separate_work_packages.md`
AUTHORITY: ADR-Exec-005 D1 · D2 · D4 · D5 · David directive 2026-08-22 · WO-095 (card 0082)

---

## FINDING

F-8 is the runtime maturity gap on the WRITE side of eLo's lesson engine. The READ side (LOOP-7, `faculties/learning/faculty.py`) is built, wired, and passing. The problem is that lesson candidates currently written to `self/lessons_ledger.jsonl` do not carry the `action` and `outcome` fields that ADR-Exec-005 D1 requires — so the D1 gate on the READ side correctly rejects them all.

David constraint (verbatim): "We don't want a lesson engine that simply turns model-generated interpretations into permanent learning."

ADR-Exec-005 D1 (verbatim governing rule): "Language alone is never evidence. A lesson must have verified consequences."

David's required chain:

```
experience
    ↓
verified consequence              (executed action + outcome, not generated text)
    ↓
lesson candidate                  (written by reflection_faculty.py — WRITE SIDE GAP HERE)
    ↓
validation / consolidation        (promote_pass() — exists, correctly gated)
    ↓
retrievable lesson                (recall() — exists, confirmed status only)
    ↓
future behaviour                  (consult() in learning/faculty.py — LOOP-7, built and wired)
```

---

## CURRENT BEHAVIOUR

| Location | What exists today |
|---|---|
| `runtime/reflection_faculty.py:1–55` | Lesson WRITER — sole creator of new rows in `self/lessons_ledger.jsonl`. Runs at session close / idle, never in the response path. |
| `self/lesson_store.py:127–201` | `record_outcome()` — accepts `action` and `outcome` keyword args (lines 133–134) and writes them into `ev_entry` if non-empty (lines 163–170). The fields EXIST in the schema. |
| `self/lessons_ledger.jsonl:1` | Entry `L-20260813030555`: 19 evidence entries, all `episode_ref: "GN·CV·2608·7"` (1 distinct ref), all `session_id: "eLo OS"`, NONE carry `action` or `outcome`. Strength=1.0, status="candidate". Cannot promote: needs 3 distinct episode_refs, has 1. Cannot pass D1: no action/outcome. |
| `self/lessons_ledger.jsonl:2` | Entry `L-1787263195`: 1 evidence entry, `session_id: "1787261879"` (purely numeric — fails D1 non-numeric check at `faculty.py:76`), no `action` or `outcome`. Status="candidate", strength=0.45. |
| `faculties/learning/faculty.py:63–81` | `_evidence_is_verified()` — D1 gate on READ side. Requires: `verified=True`, non-numeric `session_id`, at least one of `action` or `outcome` present. Currently 0 of 2 live lessons pass this gate. |
| `self/lesson_store.py:245–332` | `promote_pass()` — consolidation gate. Requires: strength≥0.70, ≥3 distinct `episode_ref`, ≥2 distinct `session_id`, ≥2 verified episodes. Sole writer of `status`. Must NOT run in response path. |
| `self/lesson_store.py:432–476` | `recall()` — returns `status == "confirmed"` only. Currently returns [] (no confirmed lessons). |
| `self/lessons_ledger_pre_v1.jsonl` | 754 rows, no `lesson_key` field, string evidence entries. Migrated out of active ledger by `migrate_pre_v1()`. Must NOT be promoted. Must NOT be merged back. |
| `self/lesson_store.py:101–122` | `migrate_pre_v1()` — moves pre-v1 rows to archive. Idempotent. |

---

## REQUIRED BEHAVIOUR

```
Verified consequence occurs (executed CAL action with observable outcome)
    ↓
reflection_faculty.py creates lesson candidate row — evidence entry carries:
    verified=True
    episode_ref=<non-empty string>
    session_id=<non-numeric, stable session identifier>
    action=<CAL action executed>
    outcome=<what actually happened>
    ↓
self/lessons_ledger.jsonl  (append-only, no deletion)
    ↓
promote_pass() runs offline (session close / idle):
    candidate → confirmed when: strength≥0.70, ≥3 distinct episode_refs,
                               ≥2 distinct session_ids, ≥2 verified episodes
    ↓
recall() returns confirmed lessons
    ↓
consult() in faculties/learning/faculty.py (LOOP-7 — already built and wired)
    ↓
LearningAdvice reaches Executive as advisory (D4 scope only)
```

The gate definition that must be encoded in `reflection_faculty.py` before writing a lesson candidate:

1. An experience qualifies as a lesson candidate ONLY IF it is a completed CAL action with a verified, observable outcome — not a model-generated interpretation of what happened.
2. The evidence entry MUST carry `action` (the CAL action executed) and `outcome` (what actually happened) — not prose summary, not generated commentary.
3. `session_id` MUST be the stable, non-numeric session identifier from `runtime.session_id.SESSION_ID` — not a process id or timestamp.

---

## EXACT CHANGE BOUNDARY

Builder touches ONLY:

1. **`runtime/reflection_faculty.py`** — the WRITE side. When `reflection_faculty.py` creates a lesson candidate row (directly or via `lesson_store.ensure_lesson()` + `lesson_store.record_outcome()`), it MUST pass `action=<cal_action>` and `outcome=<what_happened>` to `record_outcome()`. It MUST use `SESSION_ID` from `runtime.session_id` as `session_id` — not a generated or numeric value. Do not change the lesson schema structure; the `action`/`outcome` fields already exist in `record_outcome()` (lesson_store.py:133–134).

2. **Tests** — add/extend a test that:
   - calls `reflection_faculty.py` with a fabricated verified episode carrying `action` and `outcome`
   - asserts the written ledger row's evidence entry contains `action`, `outcome`, non-numeric `session_id`
   - calls `_evidence_is_verified()` from `faculties/learning/faculty.py` on the written row
   - asserts it returns `True`
   - cuts `action` from the evidence entry and asserts `_evidence_is_verified()` returns `False` (regression)

---

## DO NOT CHANGE

- `faculties/learning/faculty.py` — READ side, LOOP-7. Already built and wired. Do not touch.
- `self/lesson_store.py:245–332` — `promote_pass()` gate thresholds. Do not relax.
- `self/lesson_store.py:432–476` — `recall()` — do not lower status filter to include "candidate"
- `self/lessons_ledger_pre_v1.jsonl` — 754 archived rows. Do not promote, do not merge back into active ledger.
- `self/lessons_ledger.jsonl` — the two live rows. Do not delete or rewrite; they stay as candidate rows with their current state. Future verified evidence can strengthen them via `record_outcome()`.
- `runtime/executive.py` — FREEZE_V1_LOCK
- Any canon or Volume documents

---

## INPUTS

- A completed, verified CAL action with an observable outcome (the experience)
- `SESSION_ID` from `runtime.session_id` (stable, non-numeric)
- The CAL action name (one of the 9 frozen actions)
- The outcome: what actually happened (not generated commentary)

---

## OUTPUT

- A row in `self/lessons_ledger.jsonl` with `status="candidate"`, evidence entry carrying `verified=True`, non-numeric `session_id`, `action`, and `outcome`
- After `promote_pass()` (offline, not in response path): `status="confirmed"` when all thresholds met
- `recall()` returns confirmed lessons to `consult()` in `faculties/learning/faculty.py`

---

## ACCEPTANCE TEST

All four conditions required (Rule 4j):

1. **Built** — `reflection_faculty.py` writes a lesson candidate row whose evidence entries carry `action`, `outcome`, and a non-numeric `session_id`.
2. **Wired** — `_evidence_is_verified()` in `faculties/learning/faculty.py` returns `True` for a row produced by the fixed `reflection_faculty.py`.
3. **Exercised** — a real session-close or offline integration cycle produces at least one candidate row that passes `_evidence_is_verified()`.
4. **Falsifiable** — test goes RED when `action` is removed from the evidence entry before calling `_evidence_is_verified()`.

Specific assertion: `_evidence_is_verified(row)` returns `True` IFF the row has at least one evidence entry where: `verified=True` AND `session_id` is a non-empty, non-purely-numeric string AND at least one of `action` or `outcome` is present. Builder must confirm this against the actual gate at `faculties/learning/faculty.py:63–81` — do not re-derive the rule, read the gate.

---

## REGRESSION TEST

What must stay RED if the wire is cut:

- Test: produce a lesson candidate via `reflection_faculty.py` WITHOUT `action`/`outcome` → call `_evidence_is_verified()` → assert it returns `False`.
- Test: produce a lesson candidate with numeric `session_id` (e.g. `"1234567890"`) → call `_evidence_is_verified()` → assert `False`.
- `lessons_ledger_pre_v1.jsonl` rows (string evidence entries) must be rejected by `_evidence_is_verified()` — this is already enforced at `faculty.py:71` (`if not isinstance(ev, dict): continue`). Confirm this still holds.

---

## EVIDENCE REQUIRED

Builder must produce:

1. `git diff` showing only `runtime/reflection_faculty.py` and test files
2. Test run output showing: new test passing, `_evidence_is_verified()` returns `True` for a row produced by the fix, and `False` when `action` is cut
3. A sample written ledger row (JSON) showing the `action` and `outcome` fields present in evidence
4. Confirmation that LOOP-7 (`faculties/learning/faculty.py`) tests still pass after the change
5. Confirmation that `lessons_ledger_pre_v1.jsonl` rows are not affected

---

## ESCALATION CONDITION

Stop and raise to Architect if:

- `reflection_faculty.py` does not have access to the CAL action name or outcome at the point where it writes the lesson row — that is an architectural routing question (what carries verified consequence to the Reflection Faculty)
- The stable non-numeric `SESSION_ID` is not available in `reflection_faculty.py`'s import context (check `runtime/session_id.py`)
- `promote_pass()` is currently being called in the response path (that is a FREEZE_V1_LOCK concern)
- Any proposed fix requires editing `faculties/learning/faculty.py` — that is the READ side and is already correct; the problem is on the WRITE side only
- A path exists for `lessons_ledger_pre_v1.jsonl` rows to re-enter the active ledger — stop immediately
