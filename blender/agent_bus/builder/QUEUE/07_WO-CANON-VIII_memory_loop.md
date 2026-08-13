# 07_WO-CANON-VIII_memory_loop.md — close the memory loop (reinforce is never called)

**WO:** WO-CANON-VIII · **Seat:** builder · **Priority:** P2 · **Reserved?** no
**Spec:** `WO-CANON-VIII.md` · **Canon:** `Volume_VIII/` (4 ch) · ties `LEARNING_LOOP_v1.md`

## The finding [VERIFIED by audit]
- **`reinforce()` exists and is tested but is NEVER CALLED on retrieval** — so the forgetting curve runs with
  no counterforce. Memories decay even when eLo uses them.
- **Sole *physical* writer holds** (`vault_layer.write_memory` is the one chokepoint) but the single *logical*
  MemoryFaculty (candidate-in / decision-out) is **not wired** — callers invoke the writer directly.
- `17_memory_update.md` is an **empty stub** still cited by Vol VIII → retire the reference; Vol VIII is the
  memory root (D-F direction).

## Scope
1. **Call `reinforce()` on retrieval.** A memory that gets used should strengthen. This is one edge and it
   makes recall visibly better over time.
2. Wire the **single logical MemoryFaculty** — candidates in, decisions out; no direct writer calls.
3. Retire the `17_memory_update.md` citation.

## Test
Assert a retrieved memory's strength increases · assert direct writer calls are gone (or fail) · assert
decay still applies to unused memories.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
