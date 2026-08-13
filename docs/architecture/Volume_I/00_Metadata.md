---
volume: I
title: "Philosophy"
status: REVIEW — two chapters authored (READY FOR REVIEW); NOT RATIFIED
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: N/A — Volume I is expressed, not executed (see §"What implements Volume I")
audit_status: OPEN
canonical_path: docs/architecture/Volume_I/
tier: FOUNDATION
origin_texts:
  - docs/architecture/ARCHITECTURAL_PRINCIPLES.md (the real constitution — 7 Runtime Invariants + enduring values)
  - docs/architecture/00_MANIFESTO.md (David's canonical statement — the philosophical root)
  - docs/architecture/01_PRINCIPLES.md (the methodology layer beneath the Manifesto)
  - docs/architecture/00_DAVIDS_VISION_SPINE.md (founder intent — append-only, wins on drift)
  - docs/architecture/18_identity_kernel.md (what eLo IS — immutable kernel)
dependencies:
  - docs/architecture/Volume_I_PERSONAL_SCOPE_2026-08-10.md (eLo's person is David Charles — canon note, needs L3)
  - docs/architecture/CANON_RULINGS_2026-08-10.md (Ruling F — identity asserted by spine/brain, never learned)
  - docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md (why this volume did not exist until now)
  - Volume_II (Cognitive Principles — how eLo reasons, one layer down)
  - Volume_VII (The Executive — where Verified Speech is enforced)
  - Volume_XVIII (what may and may not be learned — ADR-Exec-005)
last_review: 2026-08-13
next_review: TBD
---

# Volume I — Philosophy

**This is the philosophical root the rest of the canon hangs from.** Every other volume
specifies a mechanism; this one states what the mechanisms are *for*, and what they may
never cost. When a design choice conflicts with this volume, the volume wins
(`ARCHITECTURAL_PRINCIPLES.md`: *"When a design choice conflicts with a principle here,
the principle wins."*)

## Why this directory exists

`00_CANON_INDEX.md` marked Volume I **"✅ Live"** and pointed the row at
`prompts/living_presence_spec.txt` and `VISION.md`. Neither is a volume:
`living_presence_spec.txt` is a **runtime prompt** under `FREEZE_V1_LOCK` (an
implementation), and `VISION.md` is a prospective pitch addressed to a buyer who does not
exist — the product track is parked. The `✅` then exempted Volume I from the Whole-Canon
Build Queue, so it was never written.
(`FOUNDATION_VOLUMES_STATUS_2026-08-10.md` §"Volume I".)

**This directory is the honest replacement for that row.** It does not rewrite the origin
texts — they are good, they are cited everywhere, and compressing them would lose the
signal. It gives them a volume-shaped home and resolves the three things they leave open:
who eLo's person is, what artefact class the runtime prompt belongs to, and what may never
change.

## Scope

- **In scope:** who eLo is and who eLo is *for*; the layering (Constitution → Canon →
  Engineering → Runtime → Behaviour); the constants that survive every evolution; the
  artefact-class rule that keeps a prompt from being mistaken for canon.
- **Out of scope (owned elsewhere):** *how* eLo reasons (Volume II) · the Executive's
  enforcement of Verified Speech and epistemic tiers (Volume VII Ch.1, Ch.3) · the
  personality vector and its drift gate (Volume V Ch.7, Volume X) · what may be learned
  (Volume XVIII / ADR-Exec-005) · security policy and approval gates (Volume XXIII).

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V1-CH01 | Chapter 1 | Who eLo Is | READY FOR REVIEW |
| ELO-V1-CH02 | Chapter 2 | The Constants | READY FOR REVIEW |

## What implements Volume I

Volume I has no runtime object. It is **expressed** through artefacts owned by other
lanes, and the distinction is load-bearing:

| Artefact | Class | Relationship to Volume I |
|---|---|---|
| `ARCHITECTURAL_PRINCIPLES.md` | Canon (constitution) | **Origin text.** Volume I cites it; it is not superseded. |
| `00_MANIFESTO.md` · `01_PRINCIPLES.md` | Canon (root + methodology) | Origin texts. The *why* and the discipline that keeps it honest. |
| `00_DAVIDS_VISION_SPINE.md` | Founder intent | Sits **above** Volume I. On drift, the Spine wins. |
| `18_identity_kernel.md` | Canon (immutable kernel) | The `what eLo is` layer Ch.2's constants are drawn from. |
| `prompts/living_presence_spec.txt` | **Implementation** (runtime prompt, FREEZE_V1_LOCK) | An **expression of** Volume I, never Volume I itself. See Ch.1 §1.6. |
| `runtime/prompt_builder.py` (`_PERSONA`) | **Implementation** (embedded fallback copy) | Same class as above; drifts from it silently if edited alone. |
| `VISION.md` | **Marketing artefact** | Recommended: retire as a cited spec. See Ch.1 §1.6 and Needs-David D-2. |

**Rule (proposed, Ch.1 §1.6):** *an implementation may be cited as a volume's grounding;
it may never be cited as its spec.* This is the general form of the mechanism that
produced the `✅ Live (code)` holes (`FOUNDATION_VOLUMES_STATUS_2026-08-10.md`
§"What must not happen again").

## Definition of Done

- [x] Chapter 1 — who eLo is, who eLo is for, and the artefact-class rule
- [x] Chapter 2 — the constants that may never change
- [x] Origin texts named rather than duplicated
- [ ] David L3 on the personal-scope statement (identity + voice = RESERVED) — **BLOCKING**
- [ ] David's call on `VISION.md`'s status and on `living_presence_spec.txt`'s artefact class
- [ ] Conformance tests written and run (Ch.2 §2.7) — no shipped artefact contradicts an Invariant
- [ ] Canon Index row I corrected to point here rather than at a prompt and a pitch
- [ ] Audit can mark COMPLETE

## Needs David

- **D-1 — The personal scope (identity/voice = RESERVED, L3).** Ch.1 §1.3 states eLo's
  person is **David Charles**, named. This is the canon half of
  `Volume_I_PERSONAL_SCOPE_2026-08-10.md` §5, which is still awaiting L3. **The prompt
  change is a separate act** requiring a scoped `FREEZE_V1_LOCK` unlock and belongs to the
  Builder — nothing here touches `prompts/`. Confirm: does eLo say "David", and is the
  canon statement approved?
- **D-2 — `VISION.md`'s status.** Architect recommendation: reclassify as a marketing
  artefact and remove it from the Canon Index row for Volume I. It addresses a prospective
  buyer; the product track is parked (`DISPATCH_BOARD.md`).
- **D-3 — `living_presence_spec.txt`'s artefact class.** Architect recommendation: it stays
  an **implementation** of Volume I, not Volume I. Consequence: editing the prompt is an
  engineering act under the freeze, not a canon amendment. David's call, because it
  determines the governance path for every future voice change.
  (= `FOUNDATION_VOLUMES_STATUS_2026-08-10.md` F-2.)

---

```
Volume I — Philosophy
Status: REVIEW — READY FOR REVIEW · NOT RATIFIED
Files: Volume_I/00_Metadata.md · 01_Who_eLo_Is.md · 02_The_Constants.md
Origin texts: ARCHITECTURAL_PRINCIPLES.md · 00_MANIFESTO.md · 01_PRINCIPLES.md ·
  00_DAVIDS_VISION_SPINE.md · 18_identity_kernel.md  (cited, not duplicated)
Replaces: Canon Index row I ("✅ Live" → prompts/living_presence_spec.txt, VISION.md)
Needs David: D-1 (personal scope, L3) · D-2 (VISION.md) · D-3 (prompt artefact class)
```

READY FOR REVIEW — NOT RATIFIED
