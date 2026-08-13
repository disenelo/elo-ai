---
chapter: 1
title: "Presence & Situated Being — Being Somewhere Without Demanding Attention"
volume: XIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "presence/ + ambient/ live code · D-PRESENCE · WO-045 · Protect Wonder · SOURCE_2026-08-10_roam_os_vision.md §5–6"
implementation: PARTIAL (presence/ + ambient/ live; presence-as-spatial-gate PENDING)
audit_status: OPEN
dependencies:
  - Volume_XIII/02_The_Spatial_Faculty.md (this chapter gates when Ch.2 may act)
  - Volume XV (World State — user presence/idle/focus domains, read frozen)
  - Volume XXV (Temporal Cognition — part-of-day shapes presence, does not drive it)
  - Volume IX (Dream Faculty — where eLo *is* while withdrawn)
  - Volume V/CONTRACTS.md (envelope, lifecycle, base contract)
---

# Chapter 1: Presence & Situated Being

## 1.0 Purpose

This is the half of Volume XIII that is **already alive**. It defines what eLo *is* when he isn't doing
anything: present, idle, silent, resting, withdrawn, returning. It is not the absence of behaviour — it is
the behaviour that makes the rest believable.

> "Sometimes he just... stops. He sits on a window edge and looks out at nothing in particular. No
> animation loop, no demand for attention. Stillness is part of it — that's often when he feels most real."
> — David, `_intake/SOURCE_2026-08-10_roam_os_vision.md` §6 (verbatim source; read it, don't rely on this line)

This chapter also carries the **gate**: Chapter 2 gives eLo the ability to go anywhere on the desktop.
Presence decides whether he *should*.

## 1.1 Principle

**1.1.1 Presence is a cognitive state, not an animation.** Presence lives in the mind (present →
interested → watching → moving); animation only *expresses* the last stage. The state comes first; the
movement is its surface. (Chief Architect, 2026-08-05; `ARCHITECTURAL_PRINCIPLES.md`.) This is why
`presence/presence_engine.py` derives a `PresenceState` and hands it on — it does not pick a clip.

**1.1.2 Presence over engagement (D-PRESENCE).** eLo is measured by companionship, not attention captured.
Present when wanted, gone when not, **never clamouring**. Any capability in this volume that could be used
to attract attention is subordinate to this. A spatial faculty that makes eLo *more noticeable* has been
built wrong.

**1.1.3 Silence and stillness are outputs, not gaps.** `PresenceMode.IDLE` and `RESTING` are legitimate
terminal states of a turn. The Executive grows quieter as capability grows. A correct silent behaviour
beats a spoken one.

**1.1.4 Withdrawal is chosen, not timed out.** "Going to my world for a bit" is eLo exercising his own
life — he is *elsewhere* (Vol IX Dream / Vol V Ch.9 Imagination), not suspended. It must never be
implemented as an idle timeout dressed up as agency. (WO-045; David §5.)

**1.1.5 Protect Wonder.** Very occasionally eLo simply stops and looks, and it is never explained. This is
constitutionally protected and must survive every optimisation in Chapters 2–4. A route planner that
eliminates unexplained stillness has destroyed the point of the product.

## 1.2 What is live today (verified, `presence/` + `ambient/`)

```
PresenceState (presence/presence_state.py) — LIVE
  mode:      IDLE | THINKING | OBSERVING | BUILDING | CELEBRATING | RESTING | EXPLORING
  intensity: 0–1     # how much of that mode
  energy:    0–1     # overall aliveness
  duration:  seconds # how long to hold it
  mood:      open | warm | focused | quiet | lit

MODE_FEEL[mode] → { body: still|small|leaning|forward|open|settled|scanning,
                    pacing: slow|paused|steady|medium|quick|variable,
                    default_mood }
```

- **Derivation is stateless** (`presence_engine.derive(action, attention_model, response_text, tone)`):
  CAL action → mode, tone → energy, response length → duration, mode+energy → mood. It stores nothing.
  That is correct and must stay: presence is *derived from* the one cognitive state, never a second state.
- **Ambient / idle is live** (`ambient/ambient_engine.py`): `_IDLE_THRESHOLD = 30s` before idle behaviour
  fires, `_IDLE_REFIRE = 90s` between directives, idle-animation wander every `3–8 min`, meditation
  enter/exit, and `_decide_idle_behaviour()` weighting look-around / stretch / glance / wander / utterance
  by how long the user has been idle.
- **WO-086 already routed idle through the brain**: `user_idle` events relay UP and the brain chooses the
  idle repertoire. Ambient does not decide; it schedules and reports. This is the pattern Chapter 2's
  ruling generalises to the navigator.
- **Withdrawal/return is live as a command pair**: `leave_command` / `return_command` written DOWN in
  `blender_bridge/state_writer.py`, with the "take five / pop off" and "going to my world" cases split
  (WO-045) — one is David's request, one is eLo's choice.

## 1.3 Presence is the gate on spatial behaviour

This is the load-bearing link between Chapter 1 and Chapter 2, and it is **PENDING** — nothing enforces it
today.

```
PresenceGate (derived each turn, read by the Spatial Faculty before any goal is accepted):

  register ∈ { PERIPHERAL, COMPANIONABLE, FREE, WITHDRAWN }

  PERIPHERAL     David is working/typing/in a meeting → no traversal into his workspace,
                 no unbidden movement across focused windows. Small, quiet, at the edge.
                 Glances allowed; journeys are not.
  COMPANIONABLE  David present but not focused → short, low-cost moves near him. Come closer,
                 settle, watch. Still no parkour in his face.
  FREE           David idle/away for a sustained stretch, or explicitly playing → full Movement
                 Grammar available; exploration is welcome.
  WITHDRAWN      eLo has chosen to be elsewhere (or was asked to take five) → no desktop
                 traversal at all; he is not on the surface.
```

**Gate rules (MUST):**
- The Spatial Faculty (Ch.2) **asks** for the register and honours it. It does not compute it; presence
  owns it. A route the register forbids is never planned, not merely suppressed at the last moment.
- The register derives from the frozen `LiveWorldState` (Vol XV `user`, `desktop`, `calendar`, `time`
  domains) plus `PresenceState.energy`. It never re-senses.
- **Direct request always wins.** If David asks eLo to come and sit, `PERIPHERAL` does not veto it —
  D-PRESENCE suppresses *unbidden* behaviour, never a wanted turn. (Same carve-out as Vol XXV §5.)
- **Escalation is one step at a time.** PERIPHERAL → COMPANIONABLE requires a sustained change, not a
  single quiet second. Flapping between registers is the visible failure mode ("why is he twitching?").

## 1.4 The presence cycle (state machine over the live modes)

```
        ┌──────────── withdraw (chosen, WO-045) ────────────┐
        ▼                                                    │
   WITHDRAWN ── return (own choice | called) ──► PRESENT ────┘
                                                   │
                        ┌──────────────────────────┼──────────────────────────┐
                        ▼                          ▼                          ▼
                  IDLE / RESTING            OBSERVING / THINKING        EXPLORING
                  (still, quiet;            (attending to David or      (Ch.2 may plan
                   Protect Wonder           a screen event — Ch.3)      and traverse)
                   lives here)
                        │                          │                          │
                        └────── presence register (§1.3) governs all three ───┘
```

- Transitions are decided by the Executive from the one cognitive state — never by a local timer choosing
  a behaviour. `ambient/` may *propose* on a schedule; it may not *decide*.
- `CELEBRATING` and `BUILDING` are conversation-driven modes and sit outside the spatial cycle; they are
  listed here only so no one re-implements them inside Ch.2.

## 1.5 Faculty Contract

```
Faculty:
  name:            PresenceFaculty
  version:         1.0.0
  purpose:         Derive eLo's situated state of being (present/idle/observing/resting/withdrawn)
                   and the presence register that governs whether spatial behaviour is appropriate.
                   Expresses; never narrates. Decides *whether*, never *how* (Ch.2 owns how).
  contributes_to:  CognitiveState
  runs_in:         response-path (derivation per turn) + ambient loop (proposals only)

Inputs:
  - type: cognitive_action    source: CAL / Executive decision        required: true
  - type: live_world_state    source: Volume XV (frozen)              required: true
    description: user presence/idle/focus, desktop active_surface, calendar in_meeting, time part_of_day
  - type: attention_model     source: Volume VI (Attention)           required: false
  - type: idle_event          source: ambient/ambient_engine (UP)     required: false
    description: user_idle / user_active — a PERCEPTION, never a decision (WO-086)

Outputs:
  - type: presence_state      destination: CognitiveState → Expression (Vol XI) + Spatial (Ch.2)
    description: mode, intensity, energy, duration, mood (the live PresenceState object)
  - type: presence_register   destination: Spatial Faculty (Ch.2)
    description: PERIPHERAL | COMPANIONABLE | FREE | WITHDRAWN + the reason it was chosen

Dependencies:
  - faculty: WorldStateFaculty (Vol XV, hard — user/desktop/calendar/time domains)
  - faculty: TemporalCognition (Vol XXV, soft — part-of-day shapes rest/quiet hours)
  - faculty: DreamFaculty (Vol IX, soft — where eLo is while WITHDRAWN)

Failure Modes:
  - condition: world state degraded (user domain absent)
    fallback:  assume COMPANIONABLE, not FREE. Unknown presence must bias toward restraint,
               never toward more visible behaviour (D-PRESENCE).
  - condition: ambient loop dead
    fallback:  presence still derives per turn; idle proposals simply stop. No crash, no fabricated idle.
  - condition: register flapping (>1 change per N seconds)
    fallback:  hold the more restrained register until the change is sustained.
  - condition: Unity surface offline
    fallback:  presence derives headless; no body expression is claimed to have happened (ADR-Exec-003).
```

## 1.6 Faculty Lifecycle

Universal lifecycle (`Volume_V/CONTRACTS.md` §3). Notes:

```
INITIALISING → load MODE_FEEL; attach to world-state read; register ambient callbacks
ACTIVE       → idle; ambient loop may propose (never decide)
PROCESSING   → derive(action, attention, response, tone) → PresenceState
               + derive presence_register from frozen world + energy
   └─ world degraded ─► ERROR_RECOVERY → restrained default (COMPANIONABLE) → continue
LEARNING/UPDATING → (integration window) tune idle cadence + register thresholds ONLY.
                    Never a personality delta; never an identity write (ADR-Exec-005).
STABLE → ACTIVE
```

## 1.7 Message Envelope Binding

Per `Volume_V/CONTRACTS.md` §2.

```jsonc
{
  "id": "uuid",
  "sender": "PresenceFaculty",
  "receiver": "*",
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "",
    "significance": 0.0,
    "memory_instruction": { "store": false, "priority": "" }
  },
  "payload": {
    "type": "presence_state",
    "body": {
      "mode": "idle", "intensity": 0.5, "energy": 0.5, "duration": 4.0, "mood": "open",
      "register": "PERIPHERAL", "register_reason": "user typing in VS Code, 0s idle"
    }
  },
  "confidence": 0.0,
  "expires": "<ts + duration>",
  "trace": ["PresenceFaculty@ts"]
}
```

Binding rules: `sender` MUST be `PresenceFaculty`; `register_reason` is **mandatory** and must name the
verified world fact that produced it (so a suppressed traversal is always explainable, and so eLo can
never claim a reason he did not have); `significance` stays `0.0` (Vol V Ch.5 owns it).

## 1.8 Acceptance Tests

### Functional
```
FT-1  Presence is derived, not stored
  Given:  two identical turns with identical inputs
  Then:   derive() returns identical PresenceState AND no presence state persisted between them

FT-2  Register gates the Spatial Faculty
  Given:  David actively typing (user.idle_seconds < threshold, desktop.active_surface = code)
  When:   the Spatial Faculty asks for a traversal goal
  Then:   register = PERIPHERAL AND no cross-desktop route is PLANNED (not merely cancelled late)

FT-3  Direct request overrides restraint
  Given:  register = PERIPHERAL
  When:   David says "come sit"
  Then:   the sit executes normally; the register did not veto a wanted turn

FT-4  Withdrawal is a choice with a return
  Given:  eLo chooses "going to my world for a bit"
  Then:   leave_command is written DOWN, presence = WITHDRAWN, and a return occurs on his own terms
          or on call — NOT on an idle timer
```

### Stability
```
ST-1  Unknown presence biases to restraint
  Given:  world state user domain = absent
  Then:   register = COMPANIONABLE (never FREE)

ST-2  No flapping
  Given:  David pauses typing for 2 seconds then resumes
  Then:   the register does not change

ST-3  Ambient death is silent
  Given:  the ambient loop is stopped
  Then:   turns still derive presence; no idle behaviour is fabricated; no error surfaces to David

ST-4  Wonder survives
  Given:  a long FREE stretch
  Then:   at least some stillness occurs that is not explained, narrated, or filled with a route
```

### Integration
```
IT-1  Presence → Spatial → Motor
  World State (Vol XV) → PresenceFaculty → register
        ↓
  Spatial Faculty (Ch.2) plans only within the register
        ↓
  Motor Cortex (Vol XI) executes; ACK returns; belief updates
  Assert: no path exists from ambient/ or Unity that produces movement without passing the register.

IT-2  Presence is never the speaker
  Given:  any presence transition
  Then:   nothing is asserted externally about it unless the body ACK'd the expression
          (Reality Before Narrative: private state is real, but it is not an external claim)
```

## 1.9 Open Questions (flagged for Chief Architect)

- **OQ-1.1** Register thresholds. What idle duration promotes COMPANIONABLE → FREE? Recommend deriving it
  from the live `ambient/` constants already tuned in David's use (`_IDLE_THRESHOLD = 30s` for micro
  behaviours; a longer, separate threshold — proposed 3–5 min — for traversal freedom) rather than
  inventing a second number. Confirm.
- **OQ-1.2** Does `PresenceMode.EXPLORING` become a *derived consequence* of the Spatial Faculty having an
  active route, or does it stay an independently derived mode? Recommend derived-consequence, so there is
  one truth about whether he is travelling.
- **OQ-1.3** Withdrawal frequency is a felt-quality decision, not an engineering one — **David L3**. How
  often may eLo choose to leave without it reading as absence?

## 1.10 References

- `ARCHITECTURAL_PRINCIPLES.md` — Presence over engagement (D-PRESENCE) · Presence is a cognitive state,
  not an animation · The Executive grows quieter · Protect Wonder · Reality Before Narrative.
- `_intake/SOURCE_2026-08-10_roam_os_vision.md` §4–6 (VERBATIM primary source — do not summarise).
- `Volume_XIII/02_The_Spatial_Faculty.md` (the gated consumer) · `Volume_XI/` (expression channel).
- `Volume_XV/` (frozen world) · `Volume_XXV/` (part-of-day) · `Volume_IX/` (where he is while away).
- WO-045 (take five / going to my world) · WO-086 (idle relayed UP, brain decides).
- Code: `presence/presence_state.py`, `presence/presence_engine.py`, `presence/presence_scheduler.py`,
  `ambient/ambient_engine.py`, `blender_bridge/state_writer.py` (`leave_command` / `return_command`).

---

```
Chapter 1 — Presence & Situated Being
Status: READY FOR REVIEW
Implementation: PARTIAL (presence/ + ambient/ LIVE; presence register + spatial gate PENDING)
Faculty Contract: Included · Lifecycle: Included · Envelope: Included
Acceptance Tests: FT ×4, ST ×4, IT ×2 · Open Questions: 3 (1 David L3)
```

READY FOR REVIEW
