# SPRINT — eLo Presentable v1, week of 2026-08-05
### The critical path to a good working result THIS WEEK (Lead Architect)

**Goal (unchanged, sharpened for the week):** eLo you can *use daily* — consistent voice, speaks the
WHOLE reply, remembers correctly, routes tools right, no false "can't reach my thinking" — **plus the
keystone: say "come sit" → he visibly sits where he is.** That last one is the Embodied-Truth moment
(reply = reality) David has been chasing; it's what makes the week feel like a result, not a changelog.

**Source of truth for "what's actually left":** David's live-test (using eLo, not green tests) —
`agent_bus/builder/david_livetest_2026-08-05.md` + `command_turn_bug_2026-08-05.md`. Most of the
"green batch" is IN_REVIEW, not felt-done. This plan sequences the felt-remaining work only.

---

## The two lanes run in parallel (different seats, different failure surfaces)

### BUILDER (eLo OS) — one WO per run, in this order
1. **WO-032 — command-turn thinking-line (do first; smallest, highest daily-annoyance).**
   Gate the "can't reach my thinking" line to fire ONLY on a genuine LLM turn that fell to mock — never
   on command/greeting/non-LLM turns (server.py:2739/2752). Give command turns a proper ack reply.
   Also investigate the real Groq drop: on failure does it fall to Cerebras or jump to the canned line?
   *Done:* command inputs never trigger the backup line; "can't reach" is rare in real use.
2. **WO-016 + WO-019 — TTS truncation (voice completeness).** eLo sometimes speaks only the FIRST
   sentence; the multi-sentence TTS tail is dropped. Couple 016+019 — the completeness fix.
   *Done:* full multi-sentence replies are spoken to the end, consistently.
3. **WO-022 + WO-037 — memory recall.** Write-back landed; recall is still "doesn't really remember
   correctly." Surface concrete facts, not a gloss. *Done:* eLo recalls a fact David gave earlier,
   correctly — which also UNBLOCKS WO-027 (self-improvement verification).
4. **WO-020 — tool routing.** Still "not really" right. *Done:* a tool ask routes to the right tool and
   returns a truthful result (honest degradation per ADR-Exec-001 when a provider is down).

### DESIGNER (UI/Avatar) — the keystone, independent of the Builder queue
- **WO-040 — sit-hold (`_sitHeld`).** Builder shipped the intent (WO-035): "come sit" now fires
  `{name:sit,target:cursor}`. The only thing left is the Unity guard so the idle rotation can't stomp
  the commanded sit. Sit-in-place at eLo's current location, HELD. Do the reliable minimum first — do
  NOT gate on walk-to-cursor. Brief is staged: `agent_bus/design/WO-040_sitHeld_2026-08-05.md`.
  *Done (David L3):* David says "come sit" → eLo visibly sits, where he is, and stays.
- Then, if time: WO-041 Unity `sit_complete` ACK (so speech only claims the sit once it's true).

### GAME (Unity) — runs independently, not on the Presentable critical path
GM-2 (eLo_v2 rig + arms/animations) continues; GM-2a next. No coordination needed this week.

---

## What needs DAVID (your part — the current real bottleneck)
The Builder already shipped a batch that only YOU can close by using eLo live:
- **Relaunch eLo and confirm live** as fixes land: weather (WO-030), garble (WO-039), over-long replies
  (WO-036), executive/health batch (WO-041/042/043/044). Each is IN_REVIEW pending your feel.
- **Smoke-test + merge two branches:** WO-031 (autostart), WO-026 (latency/streaming).
- **The sit acceptance** is yours (L3): the "come sit → he sits" check closes WO-040.
- Robot/CAD (RD-4) L3 is NOT this week — correctly parked behind Presentable.

## Definition of "good working result this week" (experience tests, not unit tests)
Sit with eLo for a normal working session and: he keeps one voice · finishes his sentences · remembers
what you told him earlier · routes a tool truthfully · never false-alarms "can't reach my thinking" ·
and when you say "come sit," he sits where he is and stays. If all six hold → Presentable v1 is real.

## Cadence (per the Operating Loop — one seat, one WO, one run)
Launch Builder → it ships WO-032 with evidence → I reconcile → you confirm → next WO. Designer runs the
sit in parallel whenever launched. Nothing multi-tasked; each run leaves a working state.
