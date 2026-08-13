---
id: ADR-Exec-003
title: "Embodied & Situated Cognition — Embodied Truth · Embodied Cognition · Situated Cognition · Affordance Before Action · Presence is a state"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-05             # David L3 (greenlit "The Moment"); principles proposed by the Chief Architect
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-001, ADR-Exec-004, ADR-Exec-006, ADR-Exec-005]
canon_home: DECISION_LOG.md index row (line ~238) → this document
source_material: EMBODIED_COGNITION.md · ARCHITECTURAL_PRINCIPLES.md ("Enduring values")
---

# ADR-Exec-003 — Embodied & Situated Cognition

> **Formalisation note (2026-08-10).** Until now ADR-Exec-003 existed only as a **row in the
> `DECISION_LOG.md` index table**, while its substance lived un-ADR'd in `EMBODIED_COGNITION.md`
> and `ARCHITECTURAL_PRINCIPLES.md`. This document promotes it to a real ADR. **It states what 23
> existing citations already rely on; it adds no new policy.**
>
> **How the canon actually cites it:** in ~80% of citations, `ADR-Exec-003` is used as shorthand
> for **"Embodied Truth"** specifically — *eLo only believes/says he did something once the body
> ACKs it.* That is §D1 below and is the operative rule for builders. The other four principles are
> bundled under the same ID because they were ratified in the same pass.

## Context

ADR-Exec-001 made speech honest about *cognition*. It did not make it honest about *the body*.
eLo would decide to sit and say "I'm sitting beside you" while the avatar had not moved — because
the Executive treated its own decision as the event. Separately, behaviour was being chosen as
**animations** ("play sit") rather than as responses to what the environment actually affords, and
"presence" was being implemented as an animation rather than as a cognitive state.

The diagnosis in `EMBODIED_COGNITION.md`: the Executive asks *"what should I say?"* when it should
ask *"what exists, what can I perceive, what am I capable of, what have I actually done — and only
then, what do I say or do?"* Most of the parts already existed (capability registry, self-model,
`LiveWorldState`, faculty health, the `_PENDING_SIT` tracker). What was missing was the **rule**
binding them and the **ACK loop** closing them.

## Decision

Five principles, ratified together, all governing the seam between cognition and body:

**D1 — Embodied Truth (the operative rule).**
**eLo believes it has acted only when its body confirms the action.** The order is:

```
Thought → Decision → Body → Confirmation (ACK) → Belief → Speech
```

never `Thought → Speech → hope the body catches up`. Extends ADR-Exec-001 from "verified cognition"
to "verified embodiment": an unACKed action is **not** an event, and eLo's *internal belief state*
— not merely his sentence — must not record it as one.

**D2 — Embodied Cognition.** eLo always reasons from an accurate model of **self, world, and
capability** before choosing speech or action. Every behaviour begins with awareness, not
animation.

**D3 — Situated Cognition.** Every decision is made relative to the **current environment,
capabilities, and relationship with the person**. eLo never reasons in isolation. Each cognitive
cycle begins with: *where am I? who am I with? what can I perceive? what can I do? what matters
now?*

**D4 — Affordance Before Action.** eLo never chooses an animation directly. It perceives what the
environment **affords** (this ledge affords sitting; this gap affords jumping), then selects an
action that satisfies its current intention **within its verified capabilities**. The Executive
searches *possibilities*, never an animation list.

**D5 — Presence is a cognitive state, not an animation.** Presence lives in the mind
(present → interested → watching → moving); animation only *expresses* the last stage. The state
comes first; the movement is its surface.

## Consequences

**Forbids**
- Speaking, or internally recording, a physical action before the body ACKs it — including on
  timeout (a timeout is reported as a failure, never silently upgraded to success).
- Selecting behaviour by animation name; hard-coding "play sit" as the decision.
- A local script in the body choosing a behaviour on its own (**brain > body > brain**: the body
  executes and reports; it never decides).
- Implementing presence/idle as an animation loop with no cognitive state behind it.

**Enables**
- The sit chain and every action after it share **one template**: intention → capability check →
  command → body → ACK → pose update → self-model update → **then** speech.
- Emergent behaviour instead of scripted behaviour (Vision Spine: *Emergence over scripting*).
- Honest failure language: *"I tried to sit but my movement system didn't confirm."*

## How it is enforced

| Mechanism | Where |
|---|---|
| ACK gate + honest timeout on movement | **WO-040 / WO-041**; `server.py` `_PENDING_SIT`; Unity movement-completion event |
| Affordances as a first-class field on the World Model | **WO-056** · `runtime/affordances.py` (surface → affordance set) |
| Body schema (height, bounding box, surface, reach) + spatial faculty | **WO-049** |
| Never-fabricated world reads (confidence · source · live/cached/stale/absent) | `world/live_world_state.py` (Vol XV) |
| Arrival/"did it happen" claims sourced from the body event, not the plan | **WO-094** §"arrived" · WO-077 return loop |
| Presence as state, not animation | Presence layer (Vol XIII — **NOTE: volume not yet written**) |

**Acceptance shape for any new action capability:** it is not done when it *executes*; it is done
when a failure to execute produces an honest report and no belief update.

## Citations (representative — 23 references repo-wide)

- `ARCHITECTURAL_PRINCIPLES.md` — Embodied Truth · Embodied Cognition · Affordance Before Action ·
  Situated Cognition · Presence-is-a-state (all five, "Enduring values").
- `EMBODIED_COGNITION.md` — the full reconciliation + design closure.
- `WO-059_Situated_Self_Runtime_Self_Model.md` (`invariant:` line) · `WO-094_*` · WO-077.
- `blender/agent_bus/PAIRED_sit_chain_situated_self_2026-08-05.md` — the sit chain as template.
- `_intake/SOURCE_2026-08-10_roam_os_vision.md` — *"only then does eLo believe/say it happened."*
- `AUDIT_INTENT_learning_growth_2026-08-10.md` — named as governing law alongside ADR-Exec-005.

## OPEN — needs David

- **O-3.1 (form).** Five principles under one ID makes precise citation impossible ("per
  ADR-Exec-003" could mean any of five). Recommendation: keep ONE ID (renumbering would break 23
  citations) and cite as `ADR-Exec-003 §D1…§D5`. **Not applied without David's word.**
- **O-3.2 (scope).** D5 (Presence is a state) has **no volume to live in** — Volume XIII
  (Presence & Embodied Spatial Intelligence) is unwritten. Until it exists, D5 is enforced by this
  ADR alone and by no test.
- **O-3.3 (known violation, unresolved).** `EloDesktopNav._route` chooses the traversal route
  **inside Unity** — a local body decision, contrary to D2/D3 and to David's *"the body NEVER
  decides on its own"*. Three route planners exist unreconciled (`world/world_state.py`,
  `desktop/spatial_state.py`, `EloDesktopNav`). Flagged by `AUDIT_MASTER_2026-08-10.md` §3; the
  fix is a Builder/Designer lane item, not an ADR change.
