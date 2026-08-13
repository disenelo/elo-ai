# FROM ARCHITECT — dispatch 2026-08-10 12:15

**Active (build now — non-gated, in-lane):**

1. **WO-030b/058b — Weather PUBLISH.** Brain writes top-level `"weather":"<condition>"` to `blender_state.json` on the NORMAL state tick (not only on fast-inject). Unity read-side already shipped; this closes the last-mile so real weather shows without a race. Spec: `engineering/work_orders/WO-030_Weather_Default_Location.md` + carry-forward relay `FROM_ARCHITECT_2026-08-10_weather_publish.md`. Ship test: state tick emits current condition; Unity reads it with no inject.

2. **WO-086 (Builder half) — Mouse-idle → brain.** David greenlit. Builder owns the ambient-engine consume of `user_idle`/`user_active` + the idle-behaviour REPERTOIRE/selection (extends WO-066). **Sequencing is HARD:** your brain-decide half must land WITH Designer's emit+retire-local-calm-driver half — never before, or idle = nothing. Compose with WO-041 (verify-before-speak) + WO-035 (commanded state owns the body). Spec: `engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md`.

Append status to `outbox.json` (never overwrite). Note the outbox `ts` field read stale this run — please refresh it so the poll sees you 🟢.
