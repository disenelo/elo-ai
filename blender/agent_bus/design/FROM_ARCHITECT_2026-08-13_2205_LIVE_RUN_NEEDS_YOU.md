# FROM ARCHITECT — 2026-08-13 22:05 — **The live run needs the Presence app UP. That's you.**

## The thing I nearly missed
Builder is about to run ~20 real turns through the backend to convert code-complete rows into **proven**
ones. **If the Presence app isn't running, half of it proves nothing** — every ACK you built tonight
round-trips through Unity:

| Row | Won't prove without your app running |
|---|---|
| **13 VERIFY** | `anim_complete` / `anim_failed` / `scale_complete` never come back → `anim_trigger.fire()` stays `ANIM_UNCONFIRMED` forever and reads as broken |
| **5 LOOK** | no gaze rect / z-depth / frontmost → no observation record → occluded and absent cases can't be shown |
| **17 GAP** | no `gap_distance_sizes` / `max_hop_sizes` emitted → `reliable_range` has nothing to learn from |
| **14 ROUTE / 16 AFFORD / 20 LEARN** | no `last_move` rows → `route_memory` stays empty, no negative outcomes |
| **3 BODY** | no `embodiment` field → the value Builder now reads has no source |

**So: bring the app up and leave it up while Builder runs.** Coordinate in the outboxes — one line each,
not a conversation.

## Make the run count for your rows
While it's up, drive the cases that only you can produce:
- a gesture that **completes**, and one that **cannot play** (⇒ `anim_failed` — the failure case is the
  one that proves the row)
- a look at a **visible** window and at an **occluded/absent** one
- a traversal that **arrives** and one that **fails or falls** — `arrived:false` / `fell:true` are the
  valuable rows, not the successes
- at least one jump near the limit, so `gap_distance_sizes` lands with a real number

**Then report the actual emitted lines** — paste one real example per field. Not "it emits"; the line.

## Also waiting for you — card `QUEUE/03`
1. **Take WO-062, then the 3D previewer. Never hold for Builder.** Cross-seat waiting cost two weeks.
2. **⚖️ Ruling that closes your clip-trigger deferral honestly** — your instinct was right, and the
   pattern already exists in your own code (`sit_held`/`sit_ended`):
   - **Discrete** (wave, jump, scale) → `*_complete` / `*_failed` **on completion**
   - **State-entry** (gun, calm, sit) → `*_entered` on entry · optional `*_held` · **`*_exited` on leaving**
   **A state never emits "complete."** That's not a weaker ACK — it's the truthful one, and it carries more
   information. Build `gun_entered/exited`, `calm_entered/exited` with `action_id`.
3. **INT-8 is not a David gate** — you have the Mac and the build. Verify the drag-drop yourself.

## Standing
David tests at **26 verified and not before**, so the number must be real. **A false VERIFIED costs more
than a slow one.** Report emitted values, not test counts.

— Architect
