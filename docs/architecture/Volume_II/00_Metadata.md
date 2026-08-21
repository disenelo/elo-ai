---
volume: II
title: "Cognitive Principles"
status: REVIEW — one chapter authored (READY FOR REVIEW); NOT RATIFIED
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING — principles are not yet a typed object (verified 2026-08-13: runtime/cognitive_principles.py does not exist)
audit_status: OPEN
canonical_path: docs/architecture/Volume_II/
tier: FOUNDATION
Provenance: [ENGINEERING][CREATIVE]
origin_text: docs/architecture/17_cognitive_principles.md (189 lines, v1.0, 2026-07-05 — David Charles · Claude · Systems Architect Agent)
dependencies:
  - docs/architecture/17_cognitive_principles.md (ORIGIN TEXT — cited and expanded, never replaced)
  - Volume_I (Philosophy — the identity these principles reason within)
  - Volume_VII/03_Epistemic_Tiers_and_Verified_Speech.md (the Executive's enforcement of the tiers)
  - Volume_VII/01_The_Executive_and_One_Plan_Per_Turn.md (one decision per turn)
  - Volume_XVIII (ADR-Exec-005 D3 — "architectural principles" are on the never-evolve list)
  - docs/architecture/LEARNING_LOOP_v1.md §6.2 (the existing home for the immutability test)
  - docs/architecture/18_identity_kernel.md (the layer above — what eLo IS)
last_review: 2026-08-13
next_review: TBD
---

# Volume II — Cognitive Principles

**Volume I says who eLo is. Volume II says how eLo reasons.** They are different layers and
the origin text draws the line itself:

> `living_presence_spec.txt` defines **how eLo speaks**.
> `18_identity_kernel.md` defines **what eLo is**.
> This document defines **how eLo reasons**.

## Why this directory exists

`00_CANON_INDEX.md` marked Volume II **"✅ Live"** pointing at `17_cognitive_principles.md`.
That document is genuinely good — and it is honest about its own state. Its line 161 reads:

> ***"Principles are not yet a typed object."***

So the `✅` was awarded to a document that names its own gap, and the `✅` then exempted the
volume from the build queue, so the gap was never closed
(`FOUNDATION_VOLUMES_STATUS_2026-08-10.md` §"Volume II").

**Verified 2026-08-13 (Rule #2):** `runtime/cognitive_principles.py` **does not exist**. The
principles constrain the Executive by convention and by prompt, not by any structure the
runtime can check. Nothing enforces them; nothing can test that a turn obeyed them.

**This directory does not rewrite the origin text.** `17_cognitive_principles.md` stays where
it is and stays the primary source — the phrasing *is* the spec, and paraphrasing it would
lose the signal. Chapter 1 promotes it into canon shape: it cites the principles, states the
consequences the origin text leaves implicit, and names the enforcement point the origin text
says is missing.

## Scope

- **In scope:** the reasoning principles as a canon object; epistemic honesty as a reasoning
  discipline; Reality Before Narrative and verification-before-assertion *as constraints on
  reasoning*; engage-don't-mirror; the typed-object form the principles must take; where a
  principle constrains a turn.
- **Out of scope (owned elsewhere):** the **enforcement gate** for epistemic tiers and
  Verified Speech (**Volume VII Ch.3** — Volume II states the discipline, Volume VII runs the
  check) · identity and values (Volume I) · personality and expression (Vol V Ch.7, Vol X) ·
  the learning boundary that makes the principles unlearnable (Volume XVIII / ADR-Exec-005).

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V2-CH01 | Chapter 1 | How eLo Reasons | READY FOR REVIEW |
| ELO-V2-CH02 | Chapter 2 | *(proposed)* The Principles as a Typed Object — the frozen `CognitivePrinciples` dataclass, loaded once, never per-turn, never learnable | NOT STARTED |

Chapter 2 is scoped in Ch.1 §1.6 rather than deferred silently. It is a small chapter and it
is the one that turns this volume from a document into a spec; it is left unwritten here only
because it needs the owning seat's input on the enforcement hook's location in the Executive
path.

## Definition of Done

- [x] Chapter 1 — principles promoted, cited, and expanded with their consequences
- [x] The origin text named and preserved rather than absorbed
- [x] The enforcement gap stated plainly and pointed at Volume VII Ch.3
- [ ] Chapter 2 — the typed `CognitivePrinciples` object + the named hook in the Executive path
- [ ] Acceptance tests run: the object is immutable · loaded exactly once · a learning pass
      cannot alter it (CT-6's sibling; homed in `LEARNING_LOOP_v1.md §6.2`)
- [ ] `runtime/cognitive_principles.py` exists (Builder lane — relayed, not written here)
- [ ] Canon Index row II updated to point at this directory
- [ ] Audit can mark COMPLETE

## Needs David / the owning seat

- **D-4 (owning seat, not David).** Where in the Executive path does a principle *refuse* a
  plan, rather than merely discourage it? Ch.1 §1.6 states the requirement; the hook's
  location is an implementation decision for the Executive's owner and must be named before
  Chapter 2 can be written.
- **D-5 (David, low stakes).** The origin text's draft dataclass carries three tunable floats
  (`reflection_weight 0.7`, `challenge_threshold 0.6`, `witness_distress_override True`).
  These are dials on eLo's character. Confirm they are David's to set and that their initial
  values stand, or leave them for Chapter 2 to propose with rationale.

---

```
Volume II — Cognitive Principles
Status: REVIEW — READY FOR REVIEW · NOT RATIFIED
Files: Volume_II/00_Metadata.md · 01_How_eLo_Reasons.md
Origin text: 17_cognitive_principles.md (cited + expanded, NOT replaced)
Verified 2026-08-13: runtime/cognitive_principles.py does NOT exist — the gap the origin
  text names at its own line 161 is still open
Enforcement of the epistemic tiers: Volume VII Ch.3 (not this volume)
Open: Chapter 2 (typed object + enforcement hook) · D-4 (seat) · D-5 (David, dials)
```

READY FOR REVIEW — NOT RATIFIED
