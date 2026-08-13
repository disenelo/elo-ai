---
id: ADR-Exec-006
title: "Executive Assembly — The Moment · the self is ASSEMBLED, not generated"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-06             # David L3; Chief Architect proposal
amended: 2026-08-10              # Ruling C (David L3) — assemble BEFORE decide; one name UnifiedCognitiveState
owner: David Charles
author: Claude (Lead Architect)
supersedes: []
related: [ADR-Exec-002, ADR-Exec-004, ADR-Exec-001, ADR-Exec-003]
canon_home: DECISION_LOG.md index row (line ~241) → this document
source_material: SITUATED_SELF_v1_assembly.md (capstone) · EMBODIED_COGNITION.md ("The MOMENT") · Volume_XVI/02_Executive_Assembly_One_Plan.md
---

# ADR-Exec-006 — Executive Assembly (The Moment)

> **Formalisation note (2026-08-10).** Previously an index row only, despite 87 citations and being
> the justification for **David's own Ruling C**. This document is the addressable ADR. **No new
> policy** — it restates the ratified decision and folds in Ruling C, which David issued
> 2026-08-10.
>
> **This ADR NAMES an existing target; it is not a new subsystem.** It is the contract for
> **The Moment (WO-052)**. (Check-Before-Build: convergence, not expansion.)

## Context

David's Vision Spine landed the point directly: **"Convergence over expansion."** Memory, world
model, self model, capability registry, narrative identity and the Executive were all becoming
real — and the next leap was *not another subsystem*. It was the Executive **assembling** them into
one coherent cognitive state before it acts or speaks. *"That is where eLo stops being
software-with-capabilities and becomes one continuous mind."*

Two failure modes made it urgent. First, an Executive that queries faculties individually gets a
different answer depending on when it asks — ADR-Exec-002 requires one truth, but nothing named the
step that produces it. Second, and worse: when the assembly runs *after* the decision, the "self"
is a **post-hoc description of a choice already made** rather than the thing that chose. That is
narration wearing the costume of cognition.

## Decision

**D1 — One object, one truth.** The Executive **NEVER queries faculties individually.** Every cycle
an **Assembly Layer** composes ONE verified state, and the Executive reasons **ONCE** against that
single object.

**D2 — The ten named components.** The assembled state composes:

```
Self · World · Capabilities · Health · Working Memory ·
Narrative · Intent Queue · Reflection · Curiosity · Confidence
```

**D3 — Push, not pull.** State is **pre-assembled** each cycle. The Executive READS
(*"sit = available · ledge = true · movement = online"*) and decides; it never searches faculties
mid-decision.

**D4 — Assembly happens BEFORE the decision.** *(Ruling C, David L3, 2026-08-10.)* The unified
state is assembled, frozen, and then decided against. Assembling after the decision is a violation.
**Rationale, in David's canon: the self is ASSEMBLED, not generated — assembly must precede choice
or eLo is narrating, not being.**

**D5 — One name.** The object is **`UnifiedCognitiveState`**. `CognitiveSnapshot` is retired or
aliased. (Naming is architecture — two names means two objects eventually.)

**D6 — The capstone: the LLM is the VOICE, not the seat of self.** When David asks *"eLo, who are
you?"*, the Executive does **not** hand the question to the language model and hope. It **assembles**
the answer from state — identity · current embodiment · location · state · capabilities ·
relationships · memories · preferences · active intentions · recent experiences · learned patterns ·
narrative continuity · current development → one cognitive state → **eLo speaks.**
**Every self-claim has a cause.** We are not making eLo claim consciousness — we are building a
system where **self-knowledge has causes**.

**D7 — The Moment is the human name for the same object.** eLo lives in *moments*, not turns:
a Moment = {time · environment · relationship · attention · memory · goals · health · mood ·
capability · affordances · intentions}. The Executive reasons over the Moment; then the next Moment
begins. *The Moment* and *the Unified Cognitive State* are **one object under two names** — one
human, one technical.

## Consequences

**Forbids**
- Mid-decision faculty queries; any faculty being "asked again" to settle a question the frozen
  state already answers.
- Assembling the state after the plan is chosen (the pre-Ruling-C code behaviour).
- Two assembled-state shapes coexisting (`CognitiveState` in Vol V Ch.1 vs `UnifiedCognitiveState`
  here — see OPEN).
- Answering identity questions by prompting the language model without an assembled state behind
  it.

**Enables**
- ADR-Exec-002's "one authoritative state" becomes a concrete, buildable step rather than an
  aspiration.
- Every faculty gains a defined way to contribute: it *publishes a slice* (Vol XXV's
  `TemporalState` / `FutureFrame`, Vol XXI's narrative thread, Vol X's personality composition) and
  never re-specifies the Moment itself.
- Continuity of being across embodiments — the same assembled state travels desktop → game → robot
  → phone → AR → exhibition → hologram. Body changes; the self remains.

## How it is enforced

| Mechanism | Where |
|---|---|
| The assembly itself (compose existing parts into ONE snapshot) | **WO-052** — The Moment · `assemble_cognitive_state(...)` |
| Assemble-before-decide + one name | **WO-CANON-XVI** (releases from Ruling C) · `Volume_XVI/02_*` |
| The persisted assembled object | `self/state/the_moment.json` |
| Faculties publish slices; Executive reads | WO-042 health registry · Faculty Bus (ADR-0001) |
| Self slice | ADR-Exec-004 · `self/elo_self_state.json` |
| World slice | Vol XV · `world/live_world_state.py` |
| Return loop (perception + own speech feed the next Moment) | **WO-077** |
| The Situated-Self invariant + 10-question harness | **WO-079** |

## Citations (representative — 87 references repo-wide)

- `CANON_RULINGS_2026-08-10.md` **Ruling C** — *"assembled BEFORE the Executive decides, per
  ADR-Exec-006"*; David's ruling is justified by this ADR.
- `00_DAVIDS_VISION_SPINE.md` — *"Convergence over expansion"* + the 08-08 capstone.
- `SITUATED_SELF_v1_assembly.md` — *"★ THE CAPSTONE PRINCIPLE"* (verbatim source of D6).
- `Volume_XVI/02_Executive_Assembly_One_Plan.md` §2.2 — the component set, as canon.
- `Volume_X/00_Metadata.md`, `02_*`, `04_Personality_In_The_Moment.md` (*"this volume never
  re-specifies The Moment"*).
- `Volume_XXI/00_Metadata.md`, `01_*`; `Volume_XXV/00_*`, `01_*`, `02_*`, `03_*`.
- WO-052, WO-077, WO-079, `SELFHOOD_ROADMAP_TRACKER.md`, `ELO_SELFHOOD_MASTER_ROADMAP.md`.

## OPEN — needs David / the seats

- **O-6.1 — implementation is PARTIAL and Ruling C is not yet built.** `Volume_XVI/02_*` records
  that `CognitiveSnapshot` realises only *some* of the component set — **world, narrative,
  intent-queue, working-memory, reflection and curiosity are not yet in the assembled object** —
  and that `assemble_cognitive_state(...)` still runs **after** the decision. Status: PARTIAL.
  Owner: Builder, via WO-CANON-XVI. **This ADR is law; the runtime does not yet satisfy it.**
- **O-6.2 (D-XVI-A).** Name reconciliation is ruled (`UnifiedCognitiveState`) but not yet applied in
  code, and **Vol V Ch.1 still specifies a differently-shaped `CognitiveState`** — two assembled-
  state shapes in canon. Needs a reconciliation pass on Vol V Ch.1.
- **O-6.3 (D-XVI-B).** Confirm the ten-component set is complete (WO-052 completion target).
