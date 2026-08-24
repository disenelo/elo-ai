# 06_WO-CANON-XII_XV_perception_world.md — perception → world state (the drift the audit found)

**WO:** WO-CANON-XII + XV finish · **Seat:** builder · **Priority:** P2 · **Reserved?** no
**Specs:** `WO-CANON-XII.md` · `WO-CANON-XV.md` · **Canon:** `Volume_XII/` · `Volume_XV/`

## The finding [VERIFIED by audit, file+line]
- `world/live_world_state.py` **EXISTS** (379 lines) and is wired at `spine.py:361-368/450/463` +
  `contracts.py:157` — **but nothing CONSUMES it**, and `Volume_XV/00_Metadata` still says
  `implementation: PENDING`. The WO's old "build it NEW" premise was wrong; it's already rewritten as
  complete+wire+verify.
- **Perception → World-State copy is NOT wired.** `perceive_from_live_state()` exists, but faculties still
  read some sensors directly — the exact drift Vol XV exists to remove.
- WO-096 fixed the swallowed ImportError; **make sure the desktop domain now actually populates** end-to-end.

## Scope
1. Wire the **perception → world-state copy** (Vol XII Ch.3 maps which `PerceptionResult` fields land in which
   `LiveWorldState` domain). Single writer, no double-read.
2. **Make faculties read the world ONCE from the carrier** instead of hitting sensors directly.
3. Promote the WO-076 fidelity guard from a **Chrome-path prompt rail** to **structured `PerceptionResult`
   flags** (`partial`, `relations`) enforced pre-prompt across ALL modalities.
4. Update `Volume_XV/00_Metadata` implementation status to match reality.
5. **Do NOT build a rival spatial model** — geometry belongs to Volume XIII's Spatial Faculty.

## Test
Assert the desktop domain is populated (not `absent`) with a window present · assert a faculty reading the
world gets it from the carrier · assert a partial read is flagged, not asserted as whole.

## Done when
implemented + test green + committed → hash, DONE/, outbox, next card.
