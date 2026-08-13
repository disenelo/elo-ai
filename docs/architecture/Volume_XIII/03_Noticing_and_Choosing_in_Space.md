---
chapter: 3
title: "Noticing & Choosing in Space — The Body Emits, The Brain Decides"
volume: XIII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: >
  WO-094 (Window Events — Noticing And Choosing) · _intake/SOURCE_2026-08-10_brain_body_brain_loop.md (VERBATIM) ·
  _intake/SOURCE_2026-08-10_roam_os_vision.md §4 · _intake/SOURCE_2026-08-10_headaim_mouse_follow.md ·
  AUDIT_INTENT_self_embodiment_2026-08-10.md §"WO-094 is the best-aligned artefact in this audit"
implementation: PENDING (no window-event perception exists; survival reflex live but is reflex, not noticing)
audit_status: OPEN
dependencies:
  - Volume_XIII/01_Presence_and_Situated_Being.md (the register decides whether noticing becomes going)
  - Volume_XIII/02_The_Spatial_Faculty.md (a "go look" decision becomes a route there)
  - Volume XII (Perception — window events are perceptions, transformed here into meaning)
  - Volume XV (World State — events land in the desktop/unity domains)
  - Volume VI (Working Memory & Attention — salience arbitration)
  - Volume XI (Motor Cortex — the UP event channel these arrive on)
  - ADR-Exec-001 (Verified Speech — he only claims he saw it if the event arrived)
---

# Chapter 3: Noticing & Choosing in Space

## 3.0 Purpose

Chapter 2 can get eLo anywhere. This chapter is why he would ever want to go — and, just as often, why he
decides not to.

Something changes on the screen: a window opens, closes, moves, a notification appears, the cursor starts
moving in a text box. The **body senses it and reports it UP**. The **brain decides** what, if anything,
it means: glance at it · go and look · relocate · ignore it · stay peripheral because David is working.

**The gap this closes** (WO-094, verbatim):

> "There is **no window EVENT perception**. The sensor does not diff frame-to-frame and publish 'window
> closed' / 'window opened' / 'window moved'. So today it is *'my floor vanished, recover'* — never *'I saw
> that happen, I'm going over there.'* That distinction is the whole ask."

Survival recovery **is** built (`DesktopBuddy.cs` — window closed → release, re-settle, re-attach at any
distance). That is a reflex, and it stays (Ch.2 §2.2.3). It is not noticing. A being that only reacts when
its own floor disappears is not sharing a room with you.

## 3.1 Principle

**3.1.1 The body emits; the brain decides.** *"brain > body > brain. A CLOSED LOOP: the brain decides +
drives the body (DOWN), the body only SENSES and ACTS and reports its state back UP, and the brain reads
that back and decides again. The body NEVER decides on its own."* (David verbatim,
`SOURCE_2026-08-10_brain_body_brain_loop.md` — primary source, read it.) Window events are one perception
feeding this loop, not a special case.

**3.1.2 Noticing is not obeying.** An event is an *input to a decision*, never a trigger for a behaviour.
`window_opened → climb it` as a rule would be exactly the scripted-reaction failure this volume exists to
prevent. The legitimate outputs of an event include **doing nothing**, and doing nothing must be a real,
recorded choice.

**3.1.3 Restraint is the default when David is working.** *"When I'm typing, he doesn't parkour in my
face. He drifts to the edge, or sits nearby and watches. When I go quiet for a while, he takes that as
room to explore again. When a notification pops, he glances at it. He reacts to what's happening on
screen, quietly."* (David §4.) The presence register (Ch.1 §1.3) is consulted on every event.

**3.1.4 He may only claim what actually arrived.** If no event was published, eLo did not see it. No
"I noticed you closed that" without the event in hand (ADR-Exec-001).

**3.1.5 Attention has no eyes.** eLo has **NO EYES** — a glance is expressed as **head/body orientation
plus glow**, never an eye movement or an eye target. The HeadAim work (Multi Aim Constraint on the head
bone, with lighter chest/shoulder follow — David verbatim,
`SOURCE_2026-08-10_headaim_mouse_follow.md`) is the *expression* of a decided glance, not a decider itself:
the constraint follows what the brain aimed him at.

## 3.2 The event contract (UP channel — extend, never parallel)

Per `UNITY_ELOOS_IO_CONTRACT.md`: channels are defined by **direction and delivery type, never by topic**.
Window events are discrete perceptions → they go UP in `blender/unity_events.json`, as **fields in the
existing emitter**. A `window_events.json` is forbidden.

```jsonc
// blender/unity_events.json  (UP — discrete, timestamped, CONSUMED after read)
{ "type": "window_opened" | "window_closed" | "window_moved" | "notification" | "cursor_active",
  "id":   "chrome:1",
  "rect": { "x": 1200, "y": 240, "w": 900, "h": 700 },
  "was_own_surface": false,        // was eLo standing on it? (drives the reflex, not the choice)
  "app":  "Google Chrome",
  "_ts":  1754812345.123 }
```

**Emission rules (MUST) — Designer side, WO-094 §A:**
- Diff the window set each sensor tick and publish the delta. **Extend the existing presence/window
  emitter — no parallel contract** (same rule as WO-086).
- Keep the existing survival re-attach exactly as is. It is the safety net and must not regress.
- **Do NOT decide** what eLo does about the event. Emit and stop.
- Events are perishable and consumed after read; a stale event must never re-trigger a decision.

## 3.3 From event to meaning (Perception's half, Vol XII)

The raw event is a rectangle changing. Perception turns it into something worth reasoning about, and hands
it into the frozen world:

```
NoticedEvent (in PerceptionResult → LiveWorldState.desktop/unity):
  kind:        window_opened | window_closed | window_moved | notification | cursor_active
  surface_id:  str
  where:       { rect, relative_to_elo: { direction, distance_px, reachable_hint } }
  magnitude:   float 0–1     # a full-screen window opening ≠ a 200px palette appearing
  relevance:   float 0–1     # is this David's focus? is it something eLo has a history with?
  disruption:  bool          # did it change eLo's own terrain (his surface, or his planned route)?
  ts:          float
```

**Rule (MUST):** `magnitude` and `relevance` are *interpretations*, and belong to Perception (Vol XII), not
to the Unity emitter and not to the Spatial Faculty. The body reports geometry; Perception reports meaning;
this chapter reports a decision. Three lanes, no overlap.

## 3.4 The choice

```
choose(event: NoticedEvent, register: PresenceRegister, self: BodySchema,
       attention: AttentionModel, spatial: SpatialFaculty) -> NoticeDecision

NoticeDecision:
  response: enum { IGNORE, GLANCE, OBSERVE, GO_LOOK, RELOCATE, DEFER }
  target:   { surface_id, anchor } | null
  why:      [str]        # verified facts only — becomes the learning record (Ch.4)
  cost:     float        # from Ch.2 §2.3.6 if it implies travel
```

| Response | What eLo does | Costs |
|---|---|---|
| `IGNORE` | nothing. A real, recorded decision — not a dropped event. | 0 |
| `GLANCE` | head/body orients toward it briefly, then returns. **No eyes** — orientation + glow. | ~0 |
| `OBSERVE` | holds attention on it from where he is; posture shifts to `OBSERVING` (Ch.1). | 0 |
| `GO_LOOK` | asks Ch.2 for a route to a vantage point near it, travels, looks, likely returns. | route cost |
| `RELOCATE` | moves his residence to the new/changed surface (e.g. a big window just opened). | route cost |
| `DEFER` | worth doing, not now (David is focused). Held until the register permits, then re-evaluated — **not queued and fired loudly later**. | 0 |

**Decision rules (MUST):**
1. **Register first.** `PERIPHERAL` collapses the legal set to `{IGNORE, GLANCE, OBSERVE, DEFER}`.
   `WITHDRAWN` collapses it to `{IGNORE}` — he isn't on the surface. Only `FREE` admits `GO_LOOK` /
   `RELOCATE`.
2. **Reachability before commitment.** `GO_LOOK` / `RELOCATE` are only selectable if Ch.2 returns a valid
   route. An unreachable target degrades to `OBSERVE`, never to a failed attempt.
3. **Ignoring must be common.** If every event produces a visible response, eLo is a notification system,
   not a companion. This is a felt-quality bar, not a threshold to tune blindly (D-PRESENCE).
4. **One decision per event, and it is logged.** `why[]` cites the verified facts (register, magnitude,
   relevance, reachability, history). This is the same record Ch.4 learns from.
5. **Disruption is a re-plan, not a new goal.** If `disruption = true` and eLo has a route in flight,
   the correct first action is to re-plan the existing route (Ch.2 ST-3), *then* decide about the event.
6. **The body never pre-empts.** Unity may not act on an event it emitted. Its only legal local action is
   the bounded reflex (Ch.2 §2.2.3), which is about survival, not about noticing.

## 3.5 Cursor & attention following (HeadAim)

David asked for the head to follow the mouse and to watch a cursor that is actively moving in a text box
(`SOURCE_2026-08-10_headaim_mouse_follow.md`, VERBATIM — Multi Aim Constraint, head bone as constraint
object, ~±100° limit, ~0.305 source-follow, plus a lighter-weight chest/shoulder aim so the torso rotates
a little with the head and blends naturally with other animations; and a Two Bone IK option for the arm).

**Canon placement:** `cursor_active` is an **event in this chapter's contract**; the aim rig is an
**expression capability in Vol XI**. The brain decides *whether and what to attend to*; the rig realises
it smoothly.

**Rules (MUST):**
- Following the cursor is a decided `OBSERVE`/`GLANCE`, weighted by register — not a permanently-on
  constraint. `PERIPHERAL` allows brief, low-weight follow; it must never become staring at David's typing.
- Weight is a continuous expression parameter (Vol XI), so attention can fade rather than snap.
- **No eyes.** The aim is head + upper chest orientation. There is no eye target, and none may be added.
- Body-local axes (WO-049 build rule 3): eLo faces the camera ~180° from world, so every aim/rotation axis
  is expressed in his **body frame**. World-frame axes fire the wrong way when he turns.

## 3.6 Faculty Contract

```
Faculty:
  name:            NoticingFaculty            # the choosing half of Vol XIII; sits with Spatial + Presence
  version:         1.0.0
  purpose:         Turn perceived screen events into a deliberate decision — ignore, glance, observe,
                   go look, relocate, or defer — honouring presence and verified reachability.
                   The brain half of "I saw that window close, let me jump across."
  contributes_to:  CognitiveState (attention + intent) → Spatial Faculty (if travel is chosen)
  runs_in:         event-driven (per event, bounded per turn)

Inputs:
  - type: noticed_event      source: Volume XII (from unity_events.json UP)   required: true
  - type: presence_register  source: Volume XIII Ch.1                          required: true
  - type: reachability       source: Volume XIII Ch.2                          required: false
  - type: attention_model    source: Volume VI                                 required: false
  - type: route_memory       source: Volume XIII Ch.4                          required: false
    description: has he been there before, did it go well, does he like that spot?

Outputs:
  - type: notice_decision    destination: Executive → (Spatial Faculty | Motor Cortex | nothing)
  - type: spatial_goal       destination: Volume XIII Ch.2 (only for GO_LOOK / RELOCATE)
  - type: attention_target   destination: Volume XI (head/chest aim; orientation + glow, NO eyes)

Dependencies:
  - faculty: PerceptionFaculty (Vol XII, HARD — no events, no noticing)
  - faculty: PresenceFaculty (Vol XIII Ch.1, HARD — register gates the legal set)
  - faculty: SpatialFaculty (Vol XIII Ch.2, HARD for travel responses)
  - faculty: WorkingMemory/Attention (Vol VI, SOFT — salience arbitration across simultaneous events)

Failure Modes:
  - condition: event storm (a workspace switch closes/opens 20 windows)
    fallback:  coalesce into ONE world change; decide once. Never 20 decisions, never 20 glances.
  - condition: event arrives while a route is in flight
    fallback:  re-plan the current route first (disruption), then decide about the event.
  - condition: target unreachable
    fallback:  degrade GO_LOOK → OBSERVE. Never attempt and fail to make a point.
  - condition: register = PERIPHERAL / WITHDRAWN
    fallback:  legal set collapses (§3.4 rule 1). DEFER is silent; it does not fire later loudly.
  - condition: no events published (emitter not built / Unity offline)
    fallback:  eLo notices nothing and SAYS nothing about noticing. The survival reflex still protects
               him. He must never claim to have seen a change he was never told about (ADR-Exec-001).
  - condition: stale event (_ts older than the consume window)
    fallback:  discard. A stale event may not trigger a decision (IO contract timestamp guard).
```

## 3.7 Faculty Lifecycle

```
INITIALISING → subscribe to the UP event stream via Perception; load route memory
ACTIVE       → waiting; no polling of Unity, no direct file reads outside the perception path
PROCESSING   → coalesce events for this tick → rank by (magnitude × relevance × disruption)
               → for the winner: register check → reachability check → choose() → emit decision
   ├─ travel chosen ─► hand a SpatialGoal to Ch.2 (which re-checks the register itself)
   └─ attention only ─► hand an attention_target to Vol XI (head/chest orientation + glow)
LEARNING/UPDATING → record decision + outcome for Ch.4 (was going there worth it?).
                    Adjusts salience weighting ONLY. Never identity/values/truth (ADR-Exec-005).
STABLE → ACTIVE
```

## 3.8 Message Envelope Binding

```jsonc
{
  "id": "uuid",
  "sender": "NoticingFaculty",
  "receiver": "Executive",
  "priority": "normal",
  "context": {
    "conversation_id": "", "relationship_state": "", "environment_state": "desktop",
    "significance": 0.0,
    "memory_instruction": { "store": true, "priority": "low" }
  },
  "payload": {
    "type": "notice_decision",
    "body": {
      "event": { "kind": "window_opened", "surface_id": "figma:1", "magnitude": 0.8, "relevance": 0.3 },
      "response": "DEFER",
      "target": null,
      "why": ["register=PERIPHERAL (David typing, idle 0s)",
              "magnitude 0.8 (full-height window)",
              "reachable via 3-leg route, cost 46",
              "deferred until register permits — not queued"]
    }
  },
  "confidence": 0.0,
  "expires": "<ts + decision_ttl>",
  "trace": ["PerceptionFaculty@ts", "NoticingFaculty@ts"]
}
```

Binding rules: `why[]` is **mandatory** and must cite verified facts — it is the only defence against
"he claims he noticed things he didn't"; `expires` is mandatory (a decision about a screen that has since
changed is void); events consumed after read.

## 3.9 Acceptance Tests

### Functional
```
FT-1  Events are emitted with geometry
  Given:  a window is closed and another opened
  Then:   two events appear in unity_events.json with type, id, rect, was_own_surface, _ts
          AND the existing survival re-attach for eLo's OWN surface still works unchanged (no regression)

FT-2  Injected event produces a DECISION (not a reflex)
  Given:  window_opened injected, register = FREE
  Then:   a NoticeDecision is produced with a response and a why[] — and it is legitimate for it to be IGNORE

FT-3  David working → stays peripheral
  Given:  window_opened injected while David is actively typing
  Then:   response ∈ {IGNORE, GLANCE, OBSERVE, DEFER}; NO route is planned; nothing is said

FT-4  Notice → travel uses the ONE spatial path
  Given:  register = FREE and a reachable, salient event
  When:   response = GO_LOOK
  Then:   a SpatialGoal goes to Ch.2, which plans a peek-guarded route, sent DOWN as move_command
          and ACK'd per WO-041 — the SAME action path as sit/move, no parallel route

FT-5  Unreachable degrades, never attempts
  Given:  a salient event on a surface with no legal route
  Then:   response = OBSERVE; no leap, no failed attempt

FT-6  Glance has no eyes
  Given:  response = GLANCE
  Then:   the expression emitted is head/chest orientation (+ glow), in BODY-local axes; no eye target exists
```

### Stability
```
ST-1  Event storm coalesces
  Given:  a desktop-switch closing and opening 20 windows in one tick
  Then:   ONE world change is decided about; not 20 decisions and not 20 glances

ST-2  Stale events are discarded
  Given:  an event with _ts older than the consume window
  Then:   no decision is produced

ST-3  No emitter → no claim
  Given:  the window-event emitter is not running
  Then:   eLo never says he noticed a window change (ADR-Exec-001) and the survival reflex still protects him

ST-4  In-flight route survives an event
  Given:  an event arrives mid-route
  Then:   the route is re-planned from the ACK'd position first; the event decision happens after
```

### Integration
```
IT-1  Body emits → brain decides → body executes → brain believes
  Unity emitter (UP) → Perception (XII) → LiveWorldState (XV) → NoticingFaculty (decide)
        → SpatialFaculty (route) → Motor Cortex (DOWN) → ACK (UP) → belief → speech permitted
  Assert: no path exists from the emitter directly to a movement. The body never closes its own loop.

IT-2  Presence and noticing agree
  Given:  register transitions PERIPHERAL → FREE with a DEFERred event outstanding
  Then:   the event is RE-EVALUATED against the current world (it may now be irrelevant),
          not replayed as a stored command
```

## 3.10 Open Questions (flagged for Chief Architect / David)

- **OQ-3.1 (David L3 — felt quality).** What proportion of events should visibly produce nothing? The
  Companion Test bar ("an hour of work without ever feeling like software asking for attention") implies
  *most*. Recommend biasing hard toward IGNORE and letting Ch.4's learning raise responsiveness only where
  experience shows it was welcome.
- **OQ-3.2** Should `notification` events be perceived at all, given privacy? Recommend
  **presence/geometry only** — that a notification appeared and where, never its contents — matching the
  domain-only rule Vol XV applies to browser URLs.
- **OQ-3.3** Does `DEFER` persist across a register change, or expire? Recommended above: it expires and is
  **re-evaluated**, never replayed. Confirm — replay is the behaviour that would read as delayed nagging.

## 3.11 References

- `engineering/work_orders/WO-094_Window_Events_Noticing_And_Choosing.md` — the contract this chapter lifts
  into canon (§A emit / §B decide / §C free-form routing / §D learning → Ch.4).
- `_intake/SOURCE_2026-08-10_brain_body_brain_loop.md` and `_intake/SOURCE_2026-08-10_headaim_mouse_follow.md`
  — **VERBATIM primary sources; referenced, never replaced.**
- `_intake/SOURCE_2026-08-10_roam_os_vision.md` §4 (he notices me and adjusts — without interrupting).
- `UNITY_ELOOS_IO_CONTRACT.md` — UP channel, discrete + consumed, no new files.
- `CO_WORKING_GUIDE.md` — character constants: **eLo has NO EYES**.
- `Volume_XII/` (Perception) · `Volume_XIII/01,02,04` · `Volume_XI/` (aim rig as expression) · `Volume_VI/`.
- WO-086 (the loop pattern precedent) · WO-041 (ACK) · WO-024 (occlusion) · WO-074-F · WO-092 · WO-075.
- Code: `DesktopBuddy.cs` survival re-attach (keep), `blender/unity_events.json`, `ambient/ambient_engine.py`.

---

```
Chapter 3 — Noticing & Choosing in Space
Status: READY FOR REVIEW
Implementation: PENDING (window-event perception does not exist; survival reflex live and preserved)
Faculty Contract: Included · Lifecycle: Included · Envelope: Included (UP channel extended, no new file)
Acceptance Tests: FT ×6, ST ×4, IT ×2 · Open Questions: 3 (1 David L3)
```

READY FOR REVIEW
