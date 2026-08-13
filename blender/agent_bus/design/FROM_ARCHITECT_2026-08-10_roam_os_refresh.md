# ▶ DESIGNER — Roam × OS vision refreshed into WO-049 (David live 2026-08-10)

David re-stated the full roam×OS vision (desktop = a world eLo reasons about, not a clip player). Captured
VERBATIM at `docs/architecture/_intake/SOURCE_2026-08-10_roam_os_vision.md` (do-not-summarise). The vision was
already in WO-049; I folded in the concrete build rules that weren't explicit — see WO-049 §"2026-08-10 —
Build rules made explicit". These are now authoritative for the Track-A (049-A) build:

1. **Peek before EVERY jump** — `PeekPitch` fires before any ledge-to-ledge leap. No blind jumps.
2. **Whole window = walkable surface** (via WO-024 occlusion): "behind" is a go-there affordance, re-emerge
   correctly stacked. Depth, not a floating sprite.
3. **Body-local axes** — eLo faces the camera (~180°); rotation axes (peek, wall-jump, gesture) in his BODY
   frame or they fire wrong when he turns.
4. **No regressions** — perch · roam · drag · click-through · gun-runoff all keep working (acceptance check).
5. **Sit-held is the keystone we're on NOW** (WO-040 `_sitHeld` · WO-035 intent · WO-041 ACK) — the rest of
   the moveset rides on it landing.

This is the fuller vision behind the movement-feel bugs already in your START_HERE (WO-074 C/F edge-roam +
jump-too-far, WO-075 gravity/landing) — fixing those IS building toward this. Track B (the deciding Spatial
Faculty) stays post-Presentable; the moveset consumes it later, never fakes it. Per-move→WO map is in WO-049.
