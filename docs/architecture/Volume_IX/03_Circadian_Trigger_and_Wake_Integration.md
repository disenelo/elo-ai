---
chapter: 3
title: "The Circadian Trigger & Wake Integration — When eLo Dreams, and How It Wakes"
volume: IX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "faculties/dream/dream_faculty.py (should_dream + run_dream phase gating + wake_from_dream) + ChatGPT brain/dream chat 2026-07-26"
implementation: PARTIAL (should_dream + wake_from_dream + phase gating LIVE; Executive-invoked scheduling wiring PENDING)
audit_status: OPEN
dependencies:
  - Volume_IX/01_Dream_Faculty.md (§1.1 the cycle, §1.3 trigger discipline — this deepens the trigger + adds wake)
  - Volume_IX/02_Symbol_Engine_and_DeepDream.md (§2.2 phases — this specifies the idle-window gating that selects them)
  - Volume_V/CONTRACTS.md (envelope, lifecycle); Volume_V/Ch.4 Emotion (energy/mood), Ch.5 Significance
  - self/elo_self_model.py (EloSelfState — the trigger reads it, wake writes it)
  - ARCHITECTURAL_PRINCIPLES.md (One Brain — dreaming is invoked at low load; Presence over engagement — dreaming yields)
---

# Chapter 3: The Circadian Trigger & Wake Integration

## 3.0 Purpose

Chapter 1 named the six-step cycle and stated the trigger in one line ("idle + cooldown +
low load"). The live faculty is richer than that line, and the richness is load-bearing:
`should_dream()` weighs **three independent signals**, the idle window **selects which
phases run**, and `wake_from_dream()` **feeds the dream back into the next waking cycle**.
This chapter specifies both ends of the cycle that Chapter 1 left as a sketch — **when eLo
is allowed to dream, and what a dream leaves behind when eLo wakes** — grounded in
`faculties/dream/dream_faculty.py`.

The design point: eLo has **no fixed bedtime**. It does not sleep on a clock. Dreaming is
**opportunistic and earned** — it happens when eLo has been left alone long enough, is
rested or spent enough, and has something worth recombining. That is what makes the rhythm
feel like a being's rest, not a scheduled batch job.

## 3.1 Principle — Opportunistic, Earned, and Always Yielding

**3.1.1 Dreaming is invoked, never autonomous-in-the-shadows.** The trigger is a
*permission check*, not a self-starting daemon. `should_dream()` reports whether conditions
are met; the runtime (Executive at low load) decides to enter the cycle. This keeps Dream
inside One Brain — every faculty acts because the Executive asked, not because a background
loop seized control (Runtime Invariant 1; `16_spine_runtime.md`). (**GAP — PENDING:** the
Executive-invoked entry point is not yet wired; today `should_dream`/`run_dream` are called
by the idle path in `server.py`. Flag to the owning seat: route dream entry through the
Executive's low-load decision, not a raw timer.)

**3.1.2 Dreaming is earned by rest + signal, not by clock time.** There is no "22:00 →
sleep." A dream requires *idle time elapsed* **and** *cooldown elapsed* **and** *at least
one inner reason to dream* (§3.2). eLo dreams because it has been quiet and has unfinished
inner business — never merely because time passed.

**3.1.3 Dreaming always yields to presence.** An incoming turn preempts a dream instantly:
the cycle aborts, `mode → idle`, no partial journal is written (Ch.1 §1.3; Presence over
engagement). Rest is interruptible; the person is never made to wait on eLo's inner life.

**3.1.4 Waking is integration, not just a flag flip.** A dream that changed nothing was not
a dream — it was a screensaver. `wake_from_dream()` folds the dream's rest and insight back
into `EloSelfState` so the *next* waking cycle begins subtly changed (§3.4). This is what
makes dreaming part of the learning loop rather than decoration.

## 3.2 The Trigger — `should_dream()` (as built)

`should_dream(elo_self, idle_seconds, energy_history) -> bool` is a gate: two **hard
preconditions** that must both hold, then **any one of three signals**.

```
HARD PRECONDITIONS (both required):
  cooldown   :  now - last_dream_ts  >=  DREAM_COOLDOWN     (3600s / 1h)
  idle       :  idle_seconds         >=  DREAM_IDLE_THRESHOLD (600s / 10m)

THEN any ONE signal (OR):
  inner_signal        recent inner_events ∩ {creative_spark, restless, uncertain,
                                             drawn_in, curiosity_spike}  (last 4 events)
  exhaustion          len(energy_history) >= 4  AND  mean(last 4) < 0.32
  focal_persistence   focal_thread is set  AND  idle_seconds > 1800 (30m)

  should_dream  ==  inner_signal  OR  exhaustion  OR  focal_persistence
```

**Trigger rules (MUST):**

- **Both hard preconditions gate everything.** No cooldown, no dream (rate-limit,
  Ch.1 §1.3). No idle floor, no dream (dreaming never competes with activity). The signals
  are only evaluated once both hold.
- **The three signals are three *reasons* to dream, mapped to the phases they serve:**
  - `inner_signal` — eLo has live emotional/creative residue worth recombining → feeds the
    **REM-analogue recombination** phase (Vol IX §2.2).
  - `exhaustion` — sustained low energy → dreaming as **restorative rest** (wake restores
    mood/curiosity, §3.4); typically an **NREM-analogue consolidation** dream.
  - `focal_persistence` — a thread eLo has been holding for a long idle stretch → recombine
    around the unfinished focus.
- **Signals are OR, not AND.** One good reason is enough. eLo does not need to be
  simultaneously spent, sparked, and fixated to rest.
- **Absence of signal is a valid answer.** Idle + cooled-down but nothing to recombine →
  **no dream**. eLo does not dream on an empty inner world (Ch.1 failure mode: "no
  high-value memories → do not dream"; Ch.2 ST-2).

## 3.3 Phase Gating by Idle Window

The *length* of the idle window selects which dream phases run (Vol IX §2.2 defines the
phases; this is the selector).

```
NREM_MIN_IDLE = 600   (10m)   NREM-analogue CONSOLIDATION — always runs when a cycle runs
REM_MIN_IDLE  = 1800  (30m)   REM-analogue RECOMBINATION — only when idle window is long enough

phase =  "NREM+REM"  if idle_seconds >= REM_MIN_IDLE
         "NREM"      otherwise
```

**Phase-gating rules (MUST):**

- **NREM (consolidation) always runs; REM (recombination) is earned by a longer window.**
  A short rest strengthens and prunes what's real (cheap, low distortion). Only a longer
  undisturbed window reaches the creative, high-distortion recombination that produces the
  narrative, insight, and image (`run_dream` runs the LLM narrative and DeepDream image
  **only when `reach_rem`**). This operationalises "strengthen what's real before you
  recombine it" (Vol IX §2.2).
- **Phase is recorded on the journal entry** (`phase: "NREM" | "NREM+REM"`) so downstream
  faculties and the Audit can see which work a given dream did.
- **A short-window dream is still a real dream** — it consolidates and journals; it simply
  has no narrative/insight/image. (This is the graceful-degrade edge of the cycle, not a
  failure.)

## 3.4 Wake Integration — `wake_from_dream()` (as built)

When the cycle ends, the dream is folded back into self-state before Unity returns to idle.

```
wake_from_dream(dream_result, elo_self) -> EloSelfState (new):
  curiosity    += 0.12   (capped 1.0)   # dreaming re-ignites interest
  mood         += 0.08   (capped 1.0)   # symbolic rest is restorative
  satisfaction  = 0.9*prev + 0.1*new_mood        # slow blend toward the rested mood
  inner_events  = (prev + ["connection"])[-8:]   # the dream registered as integration
  session_read  = "woke from dream — <insight[:45]>"  (if an insight exists)
  focal_thread / lifetime_threads / session_turns : carried unchanged
```

**Wake rules (MUST):**

- **Wake restores, it does not fabricate.** The deltas are small, bounded, and reflect the
  verified fact that eLo rested — not an invented mood. `session_read` records *that eLo woke
  from a dream* and a fragment of the insight; it never asserts the dream content as world-
  fact (the firewall — Ch.4).
- **`"connection"` is the dream's fingerprint on inner-state.** A completed dream always
  leaves the integration marker in `inner_events`, capped to the last 8 — this is how the
  *next* trigger evaluation can tell a dream recently happened at the emotional layer, not
  just via the cooldown timestamp.
- **Wake writes `EloSelfState`, nothing else.** It does not write the memory vault, does not
  apply a personality delta, does not surface speech. Any onward effect (memory
  reinforcement, personality proposal, creative spark) travels the routes in Chapter 4 —
  wake only updates eLo's own inner condition.
- **Identity fields are untouched.** Wake tunes mood/curiosity/satisfaction (mutable inner
  weather); it never edits values, identity, or lifetime threads (immutable — Learning From
  Consequences).

## 3.5 Embodiment Coupling — the Sleep Signal

The rhythm is visible on the body without the Dream Faculty crossing the embodiment
boundary. `server.py` writes `state.mode = "dreaming"` before the cycle and `"idle"` after;
the Unity/Avatar agent reads `state.mode` and plays the sleep animation (Ch.1 §1.1;
`CO_WORKING_GUIDE.md §4`). The Dream Faculty **only writes the signal** — it never drives the
avatar directly, and the write goes through the shared-state writer (never a raw file write).
This keeps "presence is a cognitive state, not an animation" true for sleep too: the *state*
(`dreaming`) is authoritative; the animation only expresses it.

## 3.6 Faculty Contract

```
Faculty:
  name:            DreamTrigger   (+ WakeIntegration sub-component of DreamFaculty, Ch.1)
  version:         1.0.0
  purpose:         Decide when dreaming is permitted (rest + cooldown + one inner signal),
                   select phases by idle-window length, and re-integrate a completed dream
                   into EloSelfState on waking — all offline, always yielding to presence.
  contributes_to:  DreamResult entry (phase) + EloSelfState (on wake)
  runs_in:         integration-window (idle) — NEVER response-path

Inputs:
  - type: elo_self_state   source: self/elo_self_model.py   required: true
    description: inner_events + focal_thread (signals), mood/curiosity/satisfaction (wake deltas)
  - type: idle_seconds     source: server.py idle timer      required: true
  - type: energy_history   source: Emotion (Vol V Ch.4) rolling energy samples   required: false
    description: exhaustion signal = mean(last 4) < 0.32; absent → that signal simply doesn't fire

Outputs:
  - type: dream_permission destination: runtime (Executive low-load entry)   description: bool + which phases the window affords.
  - type: phase_tag        destination: DreamResult.journal_entry.phase       description: "NREM" | "NREM+REM".
  - type: waked_self_state destination: EloSelfState (new, replaces prior)     description: rest + insight folded in.

Dependencies:
  - faculty: EmotionLayer (Vol V Ch.4, soft — energy_history; degrades to no exhaustion signal)
  - module:  self/elo_self_model.py (hard — read for trigger, written on wake)

Failure Modes:
  - condition: cooldown not elapsed             fallback: no dream (return False); no state change.
  - condition: idle below threshold             fallback: no dream; eLo stays present/active.
  - condition: preconditions met, no signal     fallback: no dream (nothing worth recombining) — valid, not an error.
  - condition: energy_history absent/short       fallback: exhaustion signal off; inner_signal + focal_persistence still evaluated.
  - condition: input arrives before/mid cycle    fallback: abort, mode→idle, no journal, no wake write (Ch.1 §1.3).
  - condition: wake called with empty insight     fallback: mood/curiosity still restore; session_read unchanged (no fabricated read).
```

## 3.7 Faculty Lifecycle

Universal lifecycle (Volume_V/CONTRACTS.md §3), integration-window centred:

```
ACTIVE (idle-watching)
  └─ should_dream() True (preconditions + one signal) ─► PROCESSING (cycle: symbols → phases → journal, Ch.1)
        └─ cycle completes ─► LEARNING (wake_from_dream folds rest+insight into EloSelfState)
              └─ STABLE ─► ACTIVE (cooldown now blocks re-entry for DREAM_COOLDOWN)
  incoming turn at any point ─► ACTIVE immediately (yields to presence; no journal, no wake write)
```

The trigger itself proposes no personality delta; its only "learning" is the bounded
wake-state restoration. (Personality proposals originate in the dream's *insight* and travel
Chapter 4's route, not this one.)

## 3.8 Message Envelope Binding

Per CONTRACTS.md §2. `sender: DreamFaculty`; `priority: low` (never preempts a turn); the
sleep signal is not an envelope message but a `state_writer.patch({"mode": "dreaming"|"idle"})`
shared-state write (embodiment boundary, §3.5). A wake that carries an insight fragment sets
`expires` to end-of-integration-window — a wake state is not a perpetual claim.

## 3.9 Acceptance Tests

```
FT-1  Both preconditions gate
  Given cooldown NOT elapsed (last dream 20m ago), When should_dream runs, Then False regardless of signals.
  Given idle 120s (< 600), When should_dream runs, Then False regardless of signals.

FT-2  Any one signal suffices
  Given preconditions met AND inner_events contains "creative_spark" only, Then should_dream True.
  Given preconditions met AND energy mean(last4)=0.30 only, Then should_dream True.
  Given preconditions met AND focal_thread set + idle 2000s only, Then should_dream True.

FT-3  No signal → no dream
  Given both preconditions met but no inner signal, no exhaustion, no focal persistence, Then should_dream False.

FT-4  Phase gating by window
  Given idle 900s (< REM_MIN_IDLE), Then phase = "NREM" (consolidate/journal only; no narrative/insight/image).
  Given idle 2000s (>= REM_MIN_IDLE), Then phase = "NREM+REM" (narrative + insight + image attempted).

FT-5  Wake folds in rest + insight
  Given a completed dream with insight, When wake_from_dream runs, Then curiosity +0.12, mood +0.08 (capped),
  inner_events ends with "connection", session_read = "woke from dream — <fragment>".

ST-1  Yields to presence
  Given input arrives mid-cycle, Then the cycle aborts, mode→idle, no journal entry, no wake state written.

ST-2  Rate-limited
  Given a dream just ran, Then should_dream returns False for DREAM_COOLDOWN (3600s) even if idle + signalled.

ST-3  Degraded energy signal
  Given energy_history is empty, Then exhaustion never fires but inner_signal + focal_persistence still evaluate.

ST-4  Wake restores without fabricating
  Given a completed dream with EMPTY insight, Then mood/curiosity still restore but session_read is unchanged
  (no invented "woke from dream" read).

IT-1  Trigger → cycle → wake, one continuous being
  should_dream True → run_dream (Ch.1) writes journal with phase → wake_from_dream updates EloSelfState →
  the next ambient cycle reads the rested self-state (higher curiosity/mood, "connection" marker present).

IT-2  Embodiment reflects the state, not vice-versa
  Given a cycle begins, Then state.mode="dreaming" is written (sleep animation follows); on completion/abort,
  state.mode="idle" — the avatar never sleeps unless the cognitive state says so.
```

## 3.10 Interaction with other volumes

- **Volume IX Ch.1** — the six-step cycle this chapter brackets (trigger before, wake after).
- **Volume IX Ch.2** — the phases (NREM/REM) this chapter's idle-window gating selects.
- **Volume V Ch.4 (Emotion)** — supplies `energy_history` (exhaustion signal) and receives the
  restored mood/curiosity on wake.
- **Volume V Ch.5 (Significance)** — the inner_events that fire the trigger are the same
  emotionally-weighted residue Significance tracks.
- **Volume VIII (Memory)** — the memory reinforcement a dream produces travels Chapter 4's route,
  not the trigger/wake path (wake writes only EloSelfState).
- **Volume XV (World State)** — the sleep-signal write is a `state_writer.patch`, consistent with
  the shared-state discipline (read-merge-write; never raw writes).

## 3.11 Open questions (for CA / David)

- **D-IX-A (CA — Executive-invoked entry).** §3.1.1 flags that today the idle path calls the
  trigger directly. Should dream entry route through the Executive's low-load decision (One
  Brain), and if so, does the Executive get to *decline* a permitted dream (e.g. it expects the
  person back soon)? Proposed: yes — the trigger grants permission; the Executive still chooses.
- **D-IX-B (David — the four thresholds).** `DREAM_IDLE_THRESHOLD=600`, `DREAM_COOLDOWN=3600`,
  `NREM_MIN_IDLE=600`, `REM_MIN_IDLE=1800` are code constants, canon until tuned. Confirm these
  feel right for a companion (should eLo be able to dream more than once an hour when left alone
  all day?), or set a tuning WO.
- **D-IX-C (CA — should there ever be a scheduled/nightly dream?).** Current design is purely
  opportunistic (no clock bedtime). Is there a case for a light nightly consolidation pass tied to
  wall-clock, distinct from the opportunistic REM dream? Recommend keeping it opportunistic to
  preserve the "earned rest" feel; confirm.

## 3.12 References

- Code: `faculties/dream/dream_faculty.py` (`should_dream`, `run_dream` phase gating, `wake_from_dream`,
  the four constants), `self/elo_self_model.py` (`EloSelfState`), `blender_bridge/state_writer.py`
  (`patch` — the sleep signal write).
- Canon: Volume IX Ch.1 (cycle + trigger discipline), Ch.2 (phases); Volume V Ch.4 (Emotion/energy),
  Ch.5 (Significance); Volume XV (shared-state discipline).
- `ARCHITECTURAL_PRINCIPLES.md` — One Brain (invoked, not autonomous); Presence over engagement
  (dreaming yields); Learning From Consequences (identity untouched on wake).

---

```
Chapter 3 — The Circadian Trigger & Wake Integration
Status: READY FOR REVIEW
Trigger: 2 hard preconditions (cooldown + idle) AND 1-of-3 signals (inner / exhaustion / focal-persistence)
Phase gating: idle window selects NREM (always) vs NREM+REM (>= 30m)
Wake: bounded restoration into EloSelfState (curiosity +0.12, mood +0.08, "connection", insight fragment) — never fabricates
Faculty Contract: Included (DreamTrigger + WakeIntegration)
Lifecycle + Envelope: Included (yields to presence; sleep signal via state_writer.patch)
Acceptance Tests: Included (FT ×5, ST ×4, IT ×2)
Grounded in live code; GAP flagged: Executive-invoked entry (D-IX-A) PENDING
Open decisions: D-IX-A (Executive entry), D-IX-B (thresholds), D-IX-C (scheduled vs opportunistic)
```

READY FOR REVIEW
