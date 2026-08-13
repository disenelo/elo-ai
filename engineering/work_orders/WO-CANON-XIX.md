# WO-CANON-XIX — Consciousness Research: run the research programme (findings become ADRs only)

**Owner:** **Architect** + **Chief Architect** (research/ADR governance track — NOT a faculty build). **Priority:** P4 —
Horizon-2, Tier C (research tier, lowest urgency). **Status:** QUEUED behind Presentable v1. This is a standing research
track, not a code build — it has no faculty DoD and never edits a Canon volume directly.

**Canon refs:** Volume XIX — Ch.1 `01_Research_Programme.md`, `00_Metadata.md`. `DECISION_LOG.md` (where every finding
lands as an ADR), Volume I (ethics), `18_identity_kernel.md` (identity/ethical boundary).

## Problem / Goal
Volume XIX is a **research programme**, not an implementation — `implementation: N/A (research; outputs become ADRs)`.
Its purpose is to hold framed, falsifiable questions across the open consciousness-research areas and to convert any
experiment into a ratified ADR, so research informs the architecture **only** through the governed decision path, never
by direct edit. Goal: stand up and run that track.

## Scope to DoD (grounded in Ch.1 §1.4 — this is a governance/research track)
- **Frame the 12 research areas** each with ≥1 falsifiable question on record: Continuous Identity, Presence,
  Reflection, Dreams, Memory, Attention, Curiosity, Emotion, Embodiment, Social Learning, World Models,
  Self-Improvement. Each area maps to a live volume it PROBES (Identity→I/X, Memory→VIII, Dreams→IX, Attention→VI,
  Emotion→V Ch.4, Embodiment→XI–XIII, World Models→XV) — probes, never modifies.
- **Enforce the research policy (MUST):** research NEVER modifies architecture directly; every experiment becomes an ADR
  in `DECISION_LOG.md` (hypothesis → method → result → decision); experiments respect Volume I ethical boundaries + the
  Identity Kernel; no experiment may compromise identity, safety or honesty; findings feed live volumes ONLY through
  ratified ADRs.
- **Deliverables** are documentary: the framed question set, and — as experiments are run — ADRs in the Decision Log.
  No `.py`, no faculty, no Canon-volume edit.

## Definition of Done (documentary — Ch.1 §1.4 research DoD, NOT a faculty DoD)
- Each of the 12 research areas has ≥1 framed, falsifiable question on record.
- Every experiment run has produced an ADR (hypothesis → method → result → decision).
- No experiment has modified a Canon volume directly (all via ADR).
- Ethical boundaries (Vol I / Identity Kernel) held for every experiment.
- Never marked RATIFIED as a build; the track is "live/ongoing," findings ratified individually as ADRs.

## Tests / acceptance
No FT/ST/IT — the acceptance surface is the §1.4 research DoD checklist above (falsifiable questions on record; every
finding an ADR; no direct Canon edit; ethics/Kernel hold).

## Dependencies + blocked-by
- **Blocked by:** — none hard; lowest urgency, runs well behind Presentable v1. Not gated on an alignment ruling.
- **Gate:** each individual finding is ratified only via the normal ADR path (CA + David L3 as the decision warrants);
  ethical experiments respect Volume I + the Identity Kernel.
- Dependencies: `DECISION_LOG.md` (findings → ADRs), Volume I (ethics), `18_identity_kernel.md`.

## Lane
Architect + Chief Architect (Markdown — framed questions + ADRs). No product code. This WO is a research/ADR governance
track, not a build order.
