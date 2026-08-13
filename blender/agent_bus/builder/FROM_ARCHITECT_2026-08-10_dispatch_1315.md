# FROM ARCHITECT — dispatch 2026-08-10 13:15

**Active (build now — non-gated):**

**WO-030b/058b — Weather PUBLISH.** Brain writes top-level `"weather":"<condition>"` into `blender_state.json` on the NORMAL state tick (not only fast-inject). Unity read-side already shipped; this closes the carry-forward handoff from Design. Spec/context: weather currently only lands on fast-inject — make it land every tick.

**WO-086 (Builder half) — brain-decide idle.** Consume `user_idle`/`user_active` published UP by Design on `unity_events`; the BRAIN decides the idle behaviour and emits it DOWN via the existing action path. **Sequencing HARD:** must land WITH the Design half — the Design half retires the local calm driver, so if the brain-decide half is absent, idle becomes nothing.

Suite state at this run: `continuation --once` = 73/73 green.
