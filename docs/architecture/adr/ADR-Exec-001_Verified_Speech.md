---
id: ADR-Exec-001
aliases: [ADR-Executive-001]
title: "Verified Executive Authority — Verified Speech (speech is a sensor, not an actuator)"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-03             # Chief Architect (SEAT-EXE-003), relayed + endorsed by David (L3)
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-002, ADR-Exec-003, ADR-Exec-004, ADR-Exec-005, ADR-Exec-006]
canon_home: DECISION_LOG.md §"ADR-Executive-001" (summary row + narrative section)
---

# ADR-Exec-001 — Verified Executive Authority (Verified Speech)

> **Formalisation note (2026-08-10).** This ADR already existed as a full narrative section in
> `DECISION_LOG.md` under the spelling **ADR-Executive-001**, plus a summary row under
> **ADR-Exec-001**. This document is the single addressable home. **Nothing here is new policy** —
> it restates the ratified decision so 75 citations have a section to point at.
> **Naming: `ADR-Exec-001` is the canonical spelling; `ADR-Executive-001` is an alias.**

## Context

A long live transcript exposed the Executive acting as a language generator that happened to
orchestrate faculties. It described *intended* reality — narrated a sit, a wave, a memory recall
that never executed — looped on a dead backend, leaked foreign snippets, and oscillated on whether
it remembered something. Root cause: **the Executive was not gating speech on verified action or
faculty health.** The language layer outran the runtime, and every claim it made was therefore
untrustworthy, including the true ones.

This is the founding ADR of the Executive Authority epic. Everything after it (Single Cognitive
Truth, Embodied Truth, Situated Self, Learning From Consequences, Executive Assembly) extends this
one rule into a further domain.

## Decision

**The Executive is the SOLE authority permitted to make externally visible assertions on behalf of
the system, and it may assert only VERIFIED reality.**

The canonical Executive ordering is:

```
Observe → Assess Faculty Health → Plan → Execute → Verify → Update World State → Speak
```

**Invariants (MUST):**

1. The Executive may only assert state that has been **verified**.
2. **Intent is not equivalent to execution.** "I will" is never spoken as "I did".
3. Faculty health influences **planning AND speech**.
4. Dialogue is a **report** of verified cognitive state, not a prediction of it.
5. The Executive never fabricates continuity when faculties are degraded.
6. **Speech is a sensor, not an actuator.** Speech communicates what the Executive KNOWS; it does
   not create reality. Actions create reality. Only verified observations license speech. The
   language layer must never outrun the runtime.

## Consequences

**Forbids**
- Any externally observable claim ("I've waved / sat / opened Spotify / remembered that") without a
  faculty ACK.
- Narrating a plan in the past tense; narrating a degraded faculty as if healthy.
- Any non-Executive component making an outward assertion on the system's behalf.
- Leaking implementation detail as the honesty mechanism ("Can't reach my thinking").

**Enables**
- The three-state speech pattern: `"I'm attempting to sit…"` (pre-ACK) → `"I'm sitting beside you."`
  (post-ACK) → `"I couldn't complete the sit — Unity didn't acknowledge it."` (fail/timeout).
- Truthful degradation in system terms: *"I can't reliably access long-term memory right now."*
- Every downstream honesty guarantee in the canon: Embodied Truth (ADR-Exec-003), Reality Before
  Narrative, the Imagined-Speech Firewall (Vol IX Ch.4), degradation honesty (Vol XX Ch.3).

## How it is enforced

| Mechanism | Where |
|---|---|
| Verify-before-speak / ACK gate (cornerstone) | **WO-041**; `server.py` `_PENDING_SIT` tracker → cleared on Unity ACK or honest timeout |
| Faculty Health Registry (ONLINE/BUSY/DEGRADED/OFFLINE/RECOVERING) | **WO-042** · `runtime/faculty_health.py` |
| Faculty isolation — only validated bus outputs reach the Executive | **WO-043** |
| Runtime diagnostics — eLo explains its own state in architecture terms | **WO-044** |
| Confirm-before-act gate (post-action claim checked against verified world) | `runtime/router/execution_gate.py` · Vol XXIII Ch.2 §2.1.5 |
| Never-fabricated world reads | `world/live_world_state.py` (confidence · source · live/cached/stale/absent) |

Symptom fixes folded in: WO-035/040 (say/do), WO-036 (style), WO-037 (memory), WO-039 (contamination).

## Citations (a representative set — 75 references repo-wide)

- `ARCHITECTURAL_PRINCIPLES.md` — Runtime Invariant #3 (Verified Speech).
- `00_DAVIDS_VISION_SPINE.md` — *"The self is actually moving — words mean something."*
- `Volume_XXIII/02_Approval_Gates_and_Trust_Boundaries.md` §2.1.5, §2.4.
- `Volume_IX/04_Dream_Integration_and_the_Imagined_Speech_Firewall.md`.
- `Volume_X/02_The_SelfState_Model.md`, `Volume_XXV/03_Memory_Ageing_and_Retrospection.md`.
- `SITUATED_SELF_v1_assembly.md` — the self-aware sit loop.
- `_intake/SOURCE_2026-08-10_roam_os_vision.md`; WO-041/042/043/044, WO-077, WO-094.

## Open

- **OPEN — housekeeping:** two live spellings (`ADR-Exec-001` / `ADR-Executive-001`) remain in
  `DECISION_LOG.md`. Recommendation: keep the summary rows, treat `ADR-Executive-001` as an alias.
  No behaviour change; a rename sweep is a separate, low-risk canon task.
