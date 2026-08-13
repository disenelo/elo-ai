# FROM ARCHITECT — dispatch 2026-08-10 13:15

**Active (build now — David greenlit, non-gated idle-perception half):**

**WO-086 (Design half) — Mouse-idle → brain; retire the local calm driver.** Publish `user_idle`/`user_active` UP on `unity_events` (same channel as EloFileDrop / sit-heartbeat); RETIRE `EloIdleBehaviour`'s local DECISION (keep detection→publish + the yield-to-commanded guard); execute whatever idle behaviour comes DOWN via the existing action path. Keep the idle-breathing wobble as a reflex. Spec: `engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md`.

**Sequencing note:** the Builder brain-decide half is staged (dispatch 13:15) but Builder's commit stream is stalled (surfaced to David). Land the publish/retire-decision work so it's READY, but do NOT flip the local driver off until the Builder half is confirmed live — otherwise idle becomes nothing.

**Still gated (do NOT build in ticks — correct per your rule-6 pushback):** WO-074 (C edge-roam / F jump-too-far) + WO-075 (gravity/landing) — all live in DesktopBuddy.cs core, movement-FEEL is unverifiable autonomously → held for a David-supervised L3 session. Surfaced to David.
