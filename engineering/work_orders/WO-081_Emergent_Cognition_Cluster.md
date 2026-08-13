# WO-081 — Emergent cognition: internal intent · attention · habits · autobiography · absence ("free eLo")

**Owner:** Builder (eLo OS) · Architect coordinates. **Priority:** P2 — POST-Presentable richness (the "free
eLo" layer). **Status:** OPEN — spec'd 2026-08-08 (Chief Architect "10 additions", David relay).
**Canon home:** reconciles onto EXISTING volumes — Vol V (Attention · Reflection & Growth) · Vol XXVIII
(Adaptive Learning) · Agency · The Moment (WO-079). **NOT a new Volume XXIX** (Check-Before-Build). Gated on
WO-079 (The Moment) + WO-073 (real brain).

## Why one WO, not six
These are the emergent layer that turns eLo from prompt-responder into a resident who inhabits the desktop.
Bundled so they land as a coherent program, each a sub-part with its own test — not six scattered WOs.

## Sub-parts
1. **Dual-intent queue + governance.** Two intent sources: EXTERNAL (David: "sit") + INTERNAL urges ("I want
   to explore / rest / watch / practise that jump / go back to David"). The Executive arbitrates by priority
   through PRESENCE/BOUNDARY → CAPABILITY → AFFORDANCE → EXECUTIVE → ACTION. Freedom without chaos (bounded
   autonomy, never unrestricted).
2. **Attention matrix.** eLo weights what he notices (David 0.92 · a new app 0.83 · window edge 0.48 · nothing
   new 0.04). Attention → significance → what he brings up. Feeds the "if something sticks out, touch on it"
   conversation behaviour David asked for.
3. **Habits (verified experience → tendencies, NOT RL rewriting personality — ADR-Exec-005).** Rolling counts
   nudge preferences/confidence (wall_jump 9/10 · likes high surfaces 0.81 · frequently waves 0.91). Enables
   genuine self-observation: "I've noticed I wave a lot when I greet you."
4. **Autobiography / self-history** (`self/journals/autobiography.jsonl`). Append-only lived runtime timeline
   ("01:12 wall-jump attempted — success · 01:18 sat beside David"). "What have you been doing?" reads his OWN
   history, not chat logs. `habit_analyzer` aggregates every ~100 turns.
5. **Absence-awareness.** Sliding idle timer: David idle > N min → drop `Attention.David`, raise
   `Curiosity.Exploration`, push autonomous exploration to the internal queue; on return, eLo has something
   real to report ("I found a route between the two windows while you were away"). Presence is world-state,
   not pretend-emotion.
6. **Reflection moment → visualiser.** Experience → significance → reflection → self-model/confidence update →
   memory. The One-Brain visualiser reads this real pipeline (attention→emotion→memory→reflection→learning),
   not fake activity.

## Sub-parts (continued — CA continuity additions 2026-08-08)
7. **Self-change awareness (ME-NOW ↔ ME-BEFORE).** eLo compares his self-model over time → "I used to stay
   low; I've been exploring higher lately." Reads the autobiography + habit trends. Feeds RL (Vol XXVIII).
8. **Active threads (unfinished thoughts).** A live `active_threads` list (e.g. "David mentioned the robot",
   "curious about K-7", "wants to explore upper screen") eLo can spontaneously return to — conversation
   CONTINUITY, not memory retrieval ("what I was thinking about earlier…"). Ties WO-077 (return loop).
9. **Interest formation.** experience→significance→repetition→preference produces mutable interests
   (parkour 0.84 · music 0.71 · exploration 0.89) that actually influence answers ("do you want to play
   fetch?"). Ties habits + Vol X Personality + Vol XXVIII.
10. **Micro-goals.** Tiny goals (reach the top window · find a spot to sit · try a route · return to David ·
    explore 2 min) → plan→action→verify→experience→reflect. The smallest unit of autonomous eLo.
11. **Home/World transition** → primarily **WO-049** (Presence-world ↔ eLo-world as a real state move, not
    just hiding the avatar); referenced here for the intent that drives it.
> Cross-refs: structured FAILURE-learning + "why did I do that" → **WO-082**. Body confidence → **WO-079**
> body_map. Imagination/dreams → Vol IX. See `ELO_CAPABILITY_HORIZON.md` for the full end-goal register.

## Definition of Done
- Intent-switch: with no user input, internal curiosity generates low-priority exploration commands (bounded,
  no crash/error).
- Attention/absence: David-idle raises curiosity + triggers autonomous exploration; return yields a real report.
- Habits/autobiography: eLo can truthfully state an observed tendency + read his own action history.
- All bounded by governance + presence-gating; nothing overrides the Executive/honesty/self-model invariant.

## Sequencing
POST-Presentable. Depends on WO-079 (The Moment/self-state), WO-070/071 (capture + reflection), WO-073 (brain).
Curiosity-matrix CALIBRATION (how often he seeks new windows while David works) is a David tuning pass AFTER
this is wired — not calibrated in advance.
