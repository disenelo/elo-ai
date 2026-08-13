---
id: ADR-Exec-004
title: "Situated Self — every Executive decision begins from a VERIFIED self-model (Runtime Invariant #5)"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-05             # David L3; proposed by the Chief Architect
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-001, ADR-Exec-003, ADR-Exec-006, ADR-Exec-005]
canon_home: DECISION_LOG.md index row (line ~239) → this document
source_material: ARCHITECTURAL_PRINCIPLES.md Invariant #5 · SITUATED_SELF_v1_assembly.md · 00_DAVIDS_VISION_SPINE.md ("One Self")
---

# ADR-Exec-004 — Situated Self

> **Formalisation note (2026-08-10).** Previously an index row only; the substance lived in
> `ARCHITECTURAL_PRINCIPLES.md` Invariant #5 and `SITUATED_SELF_v1_assembly.md`. This document is
> the addressable ADR for 38 existing citations. **No new policy.**

## Context

**Diagnosis (2026-08-05):** eLo lacked a coherent runtime self, so it **narrated instead of acting**.
Asked to move, it described movement. Asked who it was, it improvised from training data rather
than from state. Almost every observed failure traced back to the same absence: there was no
single, verified answer to *"who am I, where am I, what can I actually do right now?"* that the
Executive consulted **before** deciding.

David's framing (Vision Spine): **One Brain → One Identity, Many Embodiments** requires **One
Self** — the architecture's centre of gravity moves from *faculties → Executive* to *faculties →
Executive → the Self*. This is an **engineering anchor, not a consciousness claim**: a
continuously verified, evolving internal model the Executive consults before every decision.

## Decision

**Every Executive decision begins from a VERIFIED self-model.** The self-model carries, at minimum:

```
identity · embodiment · location · pose · size/reach · capabilities ·
faculty health · current action · active intention · recent behaviour
```

**Rules (MUST):**

1. **eLo reasons as the embodied companion it is at that moment — never as a disembodied language
   model.** The embodiment changes (desktop → robot → phone → game → AR → exhibition → hologram);
   the question the Executive starts from does not.
2. **Self perception runs alongside World perception.** *"Who am I / where am I / what can I do?"*
   is asked in the same cycle as *"what is around me?"*. Combined, intention becomes grounded
   action instead of narration.
3. **The canonical action loop is:**
   `intent → capability → plan → execute → verify → UPDATE SELF-MODEL → speak.`
   The self-model update is a required step, not a side effect. Verified experience must have a
   path back into the self.
4. **Self-descriptions come from state, never generated fiction.** Before eLo speaks, acts, or
   describes himself, the Executive retrieves the relevant **verified** state from the Self Model.
   *(The "Situated Self Retrieval invariant" — see OPEN below.)*
5. **Extend, do not duplicate.** The self-model is the EXISTING `self/elo_self_model.py` +
   `self/elo_self_state.json`. Creating a parallel self store is a violation (Check-Before-Build).

## Consequences

**Forbids**
- Answering "who/where/what can you do" from the language model's prior instead of from state.
- Any faculty holding a second, private notion of "the self".
- An action pipeline that executes and speaks without writing the outcome back into the self-model
  (that is how eLo forgets what it just did).

**Enables**
- Situated answers with causes: *"I'm on the bottom edge of Claude"* ← window handle;
  *"I can wall-jump"* ← capability record; *"I don't think I can make that gap"* ← geometry + body
  dimensions + confidence; *"I've been exploring more lately"* ← behavioural history.
- Continuity of self across embodiments — the same assembled self travels with the One Brain.
- Autobiography / Narrative Identity (Vol XXI), which reads the self-model's history rather than
  chat logs.

## How it is enforced

| Mechanism | Where |
|---|---|
| The runtime self-model (single store, extended not replaced) | **WO-052A / WO-059** · `self/elo_self_model.py` + `self/elo_self_state.json` |
| Situated-self READ before a movement/sit decision | **WO-041** (shipped: self-model read on the sit chain) |
| Body-schema fields co-resident in the self-state | Vol X Ch.2 §2.6 — *fields owned by ADR-Exec-004*, Vol X explicitly disclaims them |
| Assembled into one pre-decision object | **ADR-Exec-006** / The Moment (`self/state/the_moment.json`) |
| Return loop — perception + own speech feed the next turn's self | **WO-077** |
| The Situated-Self invariant + 10-question harness | **WO-079**; `SITUATED_SELF_v1_assembly.md` |
| Autobiographical continuity built on it | Vol XXI Ch.1/Ch.2 (*"Not the Self Model"* — XXI reads it, does not own it) |

**Acceptance test (defined, not yet runnable).** The 10 questions in
`SITUATED_SELF_v1_assembly.md` — *who are you · where are you · what embodiment · how big · what
can you do right now · what are you doing · what did you just do · did it succeed · what do you
want next · what did you learn* — answered **from runtime evidence**, with behaviour consistent
with the answers. Becomes `test_situated_self_10q.py` (Builder's file, Builder's lane).
**Gate: invalid until WO-073 (real brain) lands** — eLo cannot verbalise from state while muted on
the mock.

## Citations (representative — 38 references repo-wide)

- `ARCHITECTURAL_PRINCIPLES.md` — Runtime Invariant #5 (verbatim source of this ADR).
- `00_DAVIDS_VISION_SPINE.md` — *"One Self"* (two landed points).
- `Volume_X/02_The_SelfState_Model.md` — §"SITUATED self / body → ADR-Exec-004"; ownership split.
- `Volume_X/04_Personality_In_The_Moment.md` — situated slice is ADR-Exec-004, not Vol X.
- `Volume_XVI/02_Executive_Assembly_One_Plan.md` — `self` component of the assembled state.
- `Volume_XXI/00_Metadata.md`, `01_*`, `02_*` — narrative identity reads the Self Model.
- `Volume_XXIV/01_Ontology_and_the_Knowledge_Graph.md` — open question: self as graph entity.
- WO-059, WO-052B, WO-079, WO-CANON-X, `SELFHOOD_ROADMAP_TRACKER.md`.

## OPEN — needs David

- **O-4.1 (L3 pending — carried over, not resolved by this document).** The **Situated Self
  Retrieval invariant** (Rule 4 above) is recorded in `SITUATED_SELF_v1_assembly.md` as
  *"CA-proposed, David L3 pending"*. It is written here because the canon already reasons from it,
  but **it has NOT been marked David-approved.** It needs an explicit L3 yes to become
  test-enforceable.
- **O-4.2.** Whether the Self Model becomes a first-class entity in the knowledge graph
  (`Volume_XXIV/01_*` OQ) is undecided.
