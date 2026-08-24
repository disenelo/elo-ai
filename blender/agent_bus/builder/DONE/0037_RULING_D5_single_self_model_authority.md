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
