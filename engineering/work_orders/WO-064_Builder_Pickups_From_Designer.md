# WO-064 — Builder pickups from the Designer's committed batch (each self-tested)

**Owner:** Builder (eLo OS) · **Priority:** P1 (BP-1) → P2 (rest). **Status:** OPEN — spec'd 2026-08-07.
**Origin:** Designer batch committed (`3a9e4f8`, `8873b20`); handoffs listed in `design/outbox.json`.
All are the eLo-OS (Python) HALF of a body behaviour the Designer already built + committed. Each ships
with a test that runs WITHOUT David; David's involvement is L3 feel only. **None need a backend/key.**

## BP-1 — publish `conversing` to `blender_state.json` (HIGH — makes the sit bulletproof)
The Designer's sit-linger currently INFERS engagement (chat focus / IsSpeaking). Replace the guess with the
brain's truth: the brain already tracks `last_user_ts` (`server.py:1405`) and `_idle_sec` (`:684`).
- **Do:** write a boolean top-level field `conversing` to `blender_state.json` every turn — `true` while an
  exchange is active (e.g. `_idle_sec < 30`), else `false`. (Boolean, not raw `last_user_ts` — avoids the
  epoch-vs-Unity-`Time.time` clock mismatch.)
- **Test `tests/test_wo064_conversing_field.py`:** after a simulated user turn, `blender_state.json` has
  `conversing == true`; after >30s idle, `conversing == false`. Field present every write.

## BP-2 — spoken intent words for the free-form moves (David can SAY them)
Designer body is built + inject-verified (`move_complete{move}` per sub-type); only the words are missing.
- **Do:** map phrases → `move_command{type,_ts}`: "fire jump"→`fire_jump` · "climb that"/"wall jump"→
  `wall_jump` · "back up and run at it"→`step_back_run_fire` · "drop down"→`drop`. Commanded REUSES the
  autonomous resolver (Capability↔Embodiment §3) — one brain, no divergence.
- **Test `tests/test_wo064_move_words.py`:** each phrase → correct `move_command.type` emitted in
  `blender_state.json`; a non-move phrase does not emit one.

## BP-3 — take-five phrasing → EXIT (this is the WO-045 Builder half; keep it in WO-045)
Point "take five" / "give me space" / dismiss phrases at the EXIT path (NOT `biSit`); gate the spoken line
on the ACK — say "stepping away" only after `exit_complete`, "I'm back" only after `return_complete`
(Embodied Truth, ADR-Exec-001). Test lives in `tests/test_wo045_take_five.py` (extend it): dismiss phrase →
`leave_command` (not `sit_command`); the spoken line is withheld until the ACK.

## BP-4 — Self-Model emits `expression.micro` (face is brain-driven, not Unity-random)
Designer built `ApplyExpression` reading `expression.micro` (+`micro_ts`, edge-triggered) → `FlashMicro`.
- **Do:** have the self-model / emotion state emit `expression:{micro:'<emotion>', micro_ts}` to
  `blender_state.json` from eLo's actual cognitive/emotional state (joy/worried/confident/curious/disgust/
  sad/satisfied). Command-only, no ACK (per the ratified expression ruling).
- **Test `tests/test_wo064_expression_micro.py`:** a state with emotion X writes `expression.micro == X`
  with a fresh `micro_ts`; a neutral state does not spam it.

## BP-5 — consume `sit_ended` so the self-model pose stays honest (LOW)
When the linger stands eLo up on its own, the Designer will emit `sit_ended` to `unity_events.json`
(mirror of `sit_complete`). Builder consumes it → self-model `pose = standing`. Keeps say/do honest both
ways (no "I'm sitting" after he stood).
- **Test `tests/test_wo064_sit_ended.py`:** inject `sit_ended` → self-model pose flips to `standing`
  (`_ts`-guarded + consumed, same pattern as `sit_complete`).

## Gate (all)
Builder test green → Chief Architect acceptance → David L3 feel. Build order: BP-1 first (biggest sit win),
then BP-3 (take-five, a named goal), then BP-2/BP-4/BP-5.
