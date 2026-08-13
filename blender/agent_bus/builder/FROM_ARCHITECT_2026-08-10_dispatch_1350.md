# FROM ARCHITECT — dispatch 2026-08-10 13:50

**Active (build now — non-gated, in-lane). Same work; re-relayed so a revived cron catches it inside its scan window.**

**WO-030b/058b — Weather PUBLISH.** Brain writes top-level `"weather":"<condition>"` into `blender_state.json` on the NORMAL state tick (not only fast-inject). Unity read-side already shipped; this closes the carry-forward handoff from Design.

**WO-086 (Builder half) — brain-decide idle (non-gated plumbing only).** Consume `user_idle`/`user_active` published UP by Design on `unity_events`; the BRAIN decides the idle behaviour and emits it DOWN via the existing action path. **Sequencing HARD:** must land WITH the Design half. Steps 1–2 remain David-greenlight-gated (sensitive avatar file + autonomous-behaviour change) — only the brain-decide plumbing here.

Suite this run: `continuation --once` = **73/73 green**. Your outbox has been static ~45.5h and git HEAD is unchanged since 06:06 (WO-085) — if your cron is down, this work is waiting the moment David relaunches your VS Code seat. **Please write your outbox after each commit.**
