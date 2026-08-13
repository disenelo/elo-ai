# FROM ARCHITECT — dispatch 2026-08-10 12:15

**Active (build now — David greenlit, non-gated for the idle-perception half):**

**WO-086 (Design half) — Mouse-idle → brain; retire the local calm driver.** Publish `user_idle`/`user_active` UP on the unity_events channel (same as EloFileDrop / sit-heartbeat); RETIRE `EloIdleBehaviour`'s local DECISION (keep detection→publish + keep the yield-to-commanded guard); execute whatever idle behaviour comes DOWN via the existing action path. **Sequencing HARD:** land WITH the Builder brain-decide half — never before (idle would become nothing). Keep the idle-breathing wobble as a reflex. Spec: `engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md`.

**Still gated (do NOT build in ticks — correct per your rule-6 pushback):** WO-074 (C edge-roam / F jump-too-far) + WO-075 (gravity/landing) all live in DesktopBuddy.cs core + movement-FEEL is unverifiable autonomously → held for a David-supervised L3 session. Surfaced to David.
