# ▶ DESIGNER — WO-086: Architect confirms your 4 asks (2026-08-10)

Audit received (step 3) — solid. All confirmations are written into `engineering/work_orders/WO-086_Mouse_Idle_Through_Brain.md`. Summary:

- **(a) Audit verdicts — CONFIRMED.** EloEmojiReact stays REVIEW (route to brain only if it picks emotional
  valence; keep if it mirrors a brain-decided emotion — do the closer read). Confirm ArmWave/ArmReach autoTest
  self-fire toggles are OFF in the build.
- **(b) Emit — REUSE + EXTEND, no parallel contract.** Extend the existing presence emitter to send edge events
  on `unity_events.json`: `{type:'user_idle', idle_secs, _ts}` + `{type:'user_active', _ts}`. Don't build a new emitter.
- **(c) DOWN + ownership — CONFIRMED.** Idle behaviour comes DOWN via the SAME action path as meditation/sit/move;
  yields to a commanded state (WO-035, like your SitHeld yield); ACK'd per WO-041. Repertoire owned by Builder's
  ambient engine (extends WO-066) — not always "calm."
- **(d) Sequencing — CONFIRMED, hard.** Emit+retire lands WITH the Builder brain-decide half, never before. Keep
  detection→publish + yield guard + idle-breathing wobble.

**Still gated:** steps 1–2 touch the sensitive avatar file + change autonomous behaviour → awaiting **David's
greenlight** (I'm surfacing that to him now). Build step 3 only (audit, done); hold 1–2 until greenlit + the
Builder half is ready. Your proposed event contract + loop principle are folded into WO-086 verbatim in intent.
