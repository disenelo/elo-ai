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

---

## Close-out — 2026-08-20

**Commit:** `5f92954` — "card 0006 (WO-CANON-XII+XV): perception→world carrier-side; structured fidelity"

**Files changed:**
- `faculties/perception/perception_faculty.py` — `PerceptionResult.relations: tuple = ()`; module-level `tag_partial()` helper (generalises the WO-076 Chrome-only tagger); `perceive()` sets `partial=True` when any modality read is truncated.
- `world/live_world_state.py` — perception→domain copy now stamps `domain_health.desktop.partial` from `PerceptionResult.partial` (carrier-side fidelity flag).
- `runtime/claim_gate.py` — `_vision_gate(world=None)` reads from `world.environment.vision_active` when a carrier is passed; falls back to `blender_state.json` otherwise. `classify_and_gate(text, world=None)` threads it through.
- `runtime/spine/spine.py` — `_conversation_faculty` passes `plan.world` into `classify_and_gate` (single-read discipline).
- `docs/architecture/Volume_XV/00_Metadata.md` — `implementation: PENDING` → `WIRED` with specific artefacts + 3 new DoD checkboxes.
- `tests/test_card_0006_perception_world.py` — new AT-1…AT-7.

**Acceptance:** `python3 tests/test_card_0006_perception_world.py` → **7 passed, 0 failed**.

Regression: WO-076 8/8, WO-096 5/5, WO-009 7/7 all still green. Two pre-existing failures in `test_canon_xv_world_state.py` (FT-4, ST-1) patch a removed `get_active_window` symbol; unrelated to this card.

**Scope check:**
- (1) perception→world copy live ✅ (Vol XII Ch.3 §3.2 mapping already implemented in `assemble_world_state`; verified end-to-end via AT-1).
- (2) faculties read from carrier ✅ (Temporal reads `world.time` verbatim — AT-2; capability.vision now reads carrier — AT-6).
- (3) fidelity guard structural ✅ (`partial` now structural for any modality; `relations: tuple` field added — AT-3, AT-4, AT-5).
- (4) Vol XV/00_Metadata updated ✅.
- (5) no rival spatial model built ✅ (only edited existing files; Vol XIII spatial faculty untouched).
