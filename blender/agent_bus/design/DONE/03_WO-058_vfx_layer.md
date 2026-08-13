# 03_WO-058_vfx_layer.md

**WO:** WO-058 · **Seat:** design · **Priority:** P2 · **Reserved?** no

## Goal
Desktop VFX layer reflects real state: snow · rain (real weather) · meditation glow.

## Scope
- Wire the VFX layer to the brain's state fields (weather from `blender_state.json` top-level `weather`).
- Meditation glow layers onto the existing meditation state — do not create a parallel state.
- Grass/meditation work already committed stays; extend, don't duplicate.

## Test (without David)
Inject each weather condition + meditation → confirm the right VFX fires and clears. No regressions.

## Done when
implemented + verified + committed → hash, DONE/, outbox, next card.

## Result
- commit:
- test:

## Result
- commit: prior 62a7940 (grass/floor/fireflies/meditation) + weather read side; Builder now publishes top-level weather (WO-030b/058b)
- test: build clean; meditation VFX + weather routing verified live earlier
