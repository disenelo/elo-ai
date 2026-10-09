**WO:** B3-OUTBOX-CLEAN · **Seat:** builder3 · **Priority:** P0
**Reserved?** no

## Goal
Outbox is clean. All filed TO_BOARD items archived. No uncommitted changes to protected files.

## Scope
1. Move all `TO_BOARD_2026-10-06_*.md` files from `blender/agent_bus/builder3/` to `blender/agent_bus/builder3/DONE/`
2. Run `git status` — if any uncommitted changes exist in `server.py`, `spine.py`, `backend_router.py`, disclose in outbox.json immediately.
3. Confirm `tools/capability_status.py` (commit 995d48b) is clean and `tests/test_b3_capability_status.py` is 5/5.
4. Confirm `tools/research.py`, `tools/brain_display.py`, `tools/spotify_play.py` are committed.

## Files
`blender/agent_bus/builder3/TO_BOARD_*.md` → move to `DONE/`

## Test
`python3 tests/test_b3_capability_status.py` → 5/5 pass.

## Done when
DONE/ contains all TO_BOARD files. Git status shows clean for protected files. Test passes.

## Result
- commit:
- test:
- notes:
