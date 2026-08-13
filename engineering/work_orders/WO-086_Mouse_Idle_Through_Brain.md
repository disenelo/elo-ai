# WO-086 — Route mouse-idle (and other local reflex drivers) through the brain

**Owner:** Designer (emit/retire local driver) + Builder (brain consumes + decides). **Priority:** P2.
**Status:** OPEN — spec'd 2026-08-10 (Designer flag, outbox after commit `62a7940`). **Awaiting David greenlight**
(changes autonomous behaviour). **Canon:** One Brain — the brain drives, the body obeys; autonomous behaviour
should be brain-gated, not a local driver.

## Problem (Designer flag)
eLo's **mouse-idle "calm" behaviour is a LOCAL Unity driver** — the body decides to go calm/idle on its own,
bypassing the brain. That breaks One-Brain: the body is making a cognitive call (am I idle? go calm) instead
of the brain making it from real presence state. Same family as the earlier autonomous warp/wave/expression
firing mid-conversation.

## Fix — brain > body > brain loop
1. **Signal UP:** Designer emits the mouse-idle / presence signal to `unity_events.json` (reuse the existing
   presence path — the brain already gets `conversing`/`last_user_ts`, WO-064 BP-1).
2. **Brain decides:** eLo OS reads it and DECIDES the calm/idle response from real state (presence + engagement
   + energy), not a local timer.
3. **Command DOWN:** brain issues the calm/idle directive; Unity executes.
4. **Retire the LOCAL calm driver** so the body no longer self-triggers it.
5. **AUDIT for other local drivers** that bypass the brain (any autonomous Unity behaviour making a cognitive
   call) → list them; each either routes through the brain or is justified as a pure sub-perceptual reflex
   (per the earlier ruling: neutral aliveness jitter stays a Unity reflex; anything with intent/valence goes
   via the brain).

## Definition of Done
Mouse-idle calm is brain-decided (brain>body>brain), the local calm driver is retired, and the audit lists
every remaining local driver with a keep-as-reflex / route-through-brain verdict. David L3 on the feel.

## Test / verify
Designer inject/log: idle signal UP → brain emits calm directive → body plays it (no local self-trigger).
Audit deliverable = the local-driver list + verdicts. David L3 = it still feels natural, not laggy.

## Designer audit + Architect confirmations (2026-08-10)
Designer (SEAT-ENG-004) delivered step-3 audit + a full event contract + David's loop principle, and asked the
Architect to confirm 4 asks. **Architect confirms:**
- **(a) Audit verdicts — CONFIRMED.** *Route-through-brain:* EloIdleBehaviour mouse-idle "go calm" DECISION
  (the core) · EloEmojiReact = **REVIEW** (if it interprets to pick an emotional valence → brain owns it; if
  it mirrors an already-decided emotion → keep — do the closer read). *Keep as reflex/compliant:* ArmWave/
  ArmReach (event-commanded — **confirm autoTest self-fire toggles OFF in build**) · HeadLook (gaze-follow,
  yields to brain) · EloGunVisibility (visual reflex) · BodyGlow/BrainCluster/OneBrainPanel/AmbientVfx
  (reflect brain, don't decide) · PresenceEngine/EloPresenceSignal (correct UP emitters) · Receiver (executor).
  Enemies out of scope.
- **(b) Emit — REUSE + EXTEND, do NOT add a parallel contract (Check-Before-Build).** The presence emitter
  largely exists. Extend it to emit explicit EDGE events on the UP channel (`unity_events.json`):
  `{type:'user_idle', idle_secs, _ts}` when still past threshold; `{type:'user_active', _ts}` on movement.
- **(c) DOWN vocabulary + ownership — CONFIRMED.** The chosen idle behaviour goes DOWN via the SAME action
  path (`blender_state.json`) that meditation/sit/move use; Receiver executes. MUST yield to any commanded
  state (WO-035 — commanded owns the body), exactly as EloIdleBehaviour already yields to SitHeld. Verify/ACK
  per WO-041 before any spoken part. The idle REPERTOIRE (calm · look-around · stretch · glance at an app ·
  wander · soft utterance — NOT always "calm") is owned by the Builder's ambient engine (extends WO-066).
- **(d) Sequencing — CONFIRMED, hard.** Designer emit+retire lands WITH the Builder brain-decide half, NEVER
  before (retire-first = idle-does-nothing regression). Keep EloIdleBehaviour's detection→publish + the
  yield-to-commanded guard + the idle-breathing wobble as a pure reflex.

### Generalisable principle (David 2026-08-10) — brain > body > brain (closed loop)
The brain decides + drives (DOWN); the body only SENSES, ACTS, and reports state UP; the brain reads it back
and decides again. **The body never decides.** Mouse-idle is just the FIRST perception feeding this loop.
**Rule to enforce:** EVERY body perception (mouse-idle · occlusion/behind-window · perch/surface · user-active
· file-drop) relays UP; no local script may choose a behaviour. The audit's "route-through-brain" list is the
backlog. Worth ratifying as a One-Brain invariant alongside the Situated-Self invariant (WO-079).

### Gate + lane
Steps 1–2 (emit + retire local calm driver) touch the sensitive DesktopBuddy avatar file + change autonomous
behaviour → **AWAITING DAVID GREENLIGHT.** Step 3 (audit) DONE. Designer: emit UP + retire local DECISION
(keep detection/yield/wobble) + execute DOWN behaviours. Builder: ambient engine consumes `user_idle`, owns
the repertoire + selection (extends WO-066).

## Lane / ties
Designer (Unity emit + retire) + Builder (brain decide). Ties WO-064 BP-1 (`conversing`/presence signal) ·
WO-063 (command wakes body) · the One-Brain autonomous-behaviour principle. Awaiting David greenlight.
