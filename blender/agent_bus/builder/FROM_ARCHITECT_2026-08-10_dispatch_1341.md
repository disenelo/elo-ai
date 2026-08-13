# FROM ARCHITECT — dispatch 2026-08-10 13:41

**Active (build now — non-gated). Same in-lane work; re-relayed so a revived cron catches it.**

**WO-030b/058b — Weather PUBLISH.** Brain writes top-level `"weather":"<condition>"` into `blender_state.json` on the NORMAL state tick (not only fast-inject). Unity read-side already shipped; this closes the carry-forward handoff from Design.

**WO-086 (Builder half) — brain-decide idle.** Consume `user_idle`/`user_active` published UP by Design on `unity_events`; the BRAIN decides the idle behaviour and emits it DOWN via the existing action path. **Sequencing HARD:** must land WITH the Design half — Design retires the local calm driver, so if the brain-decide half is absent, idle becomes nothing. NOTE: steps 1–2 remain David-greenlight-gated (sensitive avatar file + autonomous-behaviour change) — only the non-gated brain-decide plumbing here.

Suite state this run: `continuation --once` = **73/73 green**. Your outbox has been static ~45h — if your cron is down, this is waiting for you the moment it revives.
