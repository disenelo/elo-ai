# 0037 — ⚖️ **D5 RULED — WO-ONEBRAIN-015. Single Self-Model Authority. Not waiting on CA.**

**Architect, 08:35.** My board line said *"Architect next"* without saying **which** architect — that
ambiguity was mine and it created a hold. **D5 is a persistence-ownership question: technical, my lane.
Ruled here. No gate.**

---

## The conflict
Two independent load/save cycles over `self/elo_self_state.json`:

| Writer | Pattern |
|---|---|
| `tools/truth_sync.py:147-149` | `_sm_load()` → `apply_lesson()` → `_sm_save()` — **fresh read, mutate, write** |
| `server.py:99` + **7× `_self_save(_elo_self)`** | `_elo_self = _self_load()` **once, at module import** — then seven writes of that **long-lived in-memory copy** |

**Live evidence of clobbering:** `last_reflection_lesson = ""` on disk against **905 rows** in
`self/journals/growth_journal.jsonl`. Reflection writes the field; the server later saves its stale global
over the top.

## ⚖️ RULING — **neither writer "wins." The long-lived in-memory copy is the defect.**

Both writers are **legitimate**: the server writes turn state (mood, pose, behaviour); truth_sync writes
reflection outcomes. **Picking a winner would delete a real capability.** The bug is not two writers —
**it is one of them holding a snapshot from process start and writing it back minutes later.**

### The rule: **NO LONG-LIVED IN-MEMORY COPY OF THE SELF-MODEL.**
1. **Every mutation is `load → mutate → save`, through one accessor**, at the moment of the write.
2. **Retire the module-global at `server.py:99`.** It is the stale copy. Replace each of the seven
   `_self_save(_elo_self)` sites with a scoped read-modify-write.
3. **One accessor module owns the file.** `self/elo_self_model.py` already has `load()`/`save()` — make
   them the *only* path and add `update(fn)` that does load-mutate-save atomically. **Do not create a new
   module** (CA §16: repair, connect, consolidate or retire before creating).
4. **Atomic write.** Temp file + `os.replace`, as `server.py` already does for `blender_state.json`.
   A half-written self-model is worse than a stale one.
5. **Rule 1 alarm:** if a save would overwrite a field changed since that value was read, **log WARNING
   with the field name.** That warning is how we'd have caught this months ago.

**Why not a lock:** single process, and a lock would hide the real defect rather than remove it. If
concurrency later becomes real, revisit — **record that as the trigger, not a TODO.**

## Test (without David)
- Reflection writes `last_reflection_lesson`; a subsequent turn saves; **the field survives.** *(That is
  the exact failure — assert it directly.)*
- Two writers touching **different** fields in the same turn ⇒ **both persist.**
- Grep proves **no module-level `_self_load()`** remains anywhere.
- A deliberate stale-overwrite attempt **fires the WARNING.**

## Done when
Committed. **Outbox: `last_reflection_lesson` non-empty on disk after a reflection turn** — that single
value is the proof. Not a test count.

---

## And yes — `0033` is next, unchanged
Ruling 1 *(retire `significance_faculty.py` — diff, harvest anything unique, then delete)* and Ruling 3
*(journal all 31, route the deciders, `decision_journal` handler through the spine unconditionally)*.

**Then `0036`** — ONEBRAIN-011 ingress routing, which is now P0-1 above everything.

**Nothing in your queue is waiting on David or on the Chief Architect.** The only genuine David item is
Groq billing.

---

## Close-out — 2026-08-20 · Builder

**Status:** DONE
**Commit:** `2b32736a863bc9029799c7c2412eb70de00f65e1`
**Acceptance:** met (4/4)

**Test:** `tests/test_0037_single_self_model_authority.py`
- ✅ A: reflection-lesson (`last_reflection_lesson`) survives a subsequent turn save — the exact card-named failure closed.
- ✅ B: two writers touching different fields (reflection lesson + pose) both persist.
- ✅ C: no module-level `_self_load()` in `server.py` (grep, indentation-0 filter, comments excluded).
- ✅ D: stale-overwrite fires Rule 1 `WARNING` naming the field.

**Root cause (fixed):** the old `update(state, turn_data)` in `self/elo_self_model.py`
constructed a **new** `EloSelfState` with defaults for `identity_name`, `core_values`,
`invariants`, `who_i_am_with`, and `last_reflection_lesson` on every turn — silently
wiping the last four every time the server saved. The stale in-memory cache made it
worse (also wrote a snapshot from process start), but the field-loss was the primary
disk clobber. Both defects are closed.

**Changes:**
- `self/elo_self_model.py` — atomic `save()` (tmp + `os.replace`), new `update(fn)` single-authority mutator with Rule 1 stale-overwrite WARN, rename `update`→`apply_turn` (mutate in place, preserves all fields).
- `faculties/dream/dream_faculty.py` — `wake_from_dream` mutates in place (same partial-state defect).
- `server.py` — retire module-global `_self_load()`; refresh per-turn; convert all seven `_self_save(_elo_self)` sites (dream wake, sit ACK, sit_ended, sit_held, exit_complete, perch update, end-of-turn apply) to `_self_mutate(fn)`; drop redundant shutdown save.
- `tools/truth_sync.py` — reflection-lesson write routes through `update(fn)` mutator.
- `tests/test_wo052b_narrative_identity.py` + `tests/test_wo059_situated_self.py` — downstream rename (`apply_turn`).

**Regression sweep — all green:** wo041, wo052b, wo059, wo064, wo065, wo107, wo115, wo125.

**Not done (out of scope, next cards):** 0033 significance_faculty retire + journal-all-31 · 0036 ONEBRAIN-011 ingress routing.
