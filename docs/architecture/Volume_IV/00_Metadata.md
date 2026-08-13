---
volume: IV
title: "The Cognitive Spine — The Turn Loop"
status: REVIEW — spec written from live code; awaiting CA + David L3. NOT RATIFIED.
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: LIVE-BUT-UNCANONISED
audit_status: OPEN
canonical_path: docs/architecture/Volume_IV/
written: 2026-08-13
origin_text: NONE — this volume is transcribed from the running system, not promoted from prose.
grounding:
  - runtime/spine/spine.py (621 lines — the live turn loop; the authority this volume transcribes)
  - runtime/spine/{plan,presence_faculty,control_plane,relationship_faculty,executive_faculty,executive_extension}.py (1,900 lines total, verified `wc -l` 2026-08-13)
  - runtime/contracts.py (400 lines — CognitiveState · CognitivePlan · EmbodimentState · ExecutionReport)
  - server.py:2321, :2322, :2925, :2926, :3346 (the live callers — IRV 2026-08-13)
dependencies:
  - Volume III (System Architecture — the four contracts this volume orders the production of). WRITTEN IN THE SAME PUSH; see FOUNDATION_VOLUMES_STATUS_2026-08-10.md §Recommendation.
  - 16_runtime_contracts.md (the contract vocabulary; now points here)
  - ADR-Exec-006 (Executive Assembly — assemble before decide) · ADR-Exec-002 (Single Cognitive Truth)
  - CANON_RULINGS_2026-08-10.md Ruling C (assemble before decide) · Ruling E (shared ownership + mandatory reporting) · Ruling F (identity asserted by the spine, never learned)
  - Volume XII (Perception) · Volume XV (World State) · Volume VI (Working Memory / Attention) · Volume VII (Executive Cortex) · Volume XVI (Coordination) · Volume XI (Motor Cortex) · Volume XIII (Presence / Spatial)
supersedes: docs/architecture/16_spine_runtime.md (5 lines, "STATUS: PENDING")
priority: "FOUNDATION — highest-value unwritten volume (FOUNDATION_VOLUMES_STATUS_2026-08-10.md §Recommendation #1)"
---

# Volume IV — The Cognitive Spine

The spine is the **order of a turn**. Not what eLo knows (Volume XV), not what he decides
(Volume VII), not how he moves (Volume XI) — the *sequence* in which those things happen, and
the guarantees that sequence gives every other volume.

## The honest note — why this volume did not exist until today

`00_CANON_INDEX.md` marked Volume IV **"✅ Live"** for months. It was not live. It was a
**five-line file**:

```
docs/architecture/16_spine_runtime.md
# eLo OS v1.7
# spine.py Runtime Alignment
# Architecture Specification

STATUS: PENDING — to be written in a dedicated session.
```

`AUDIT_INTENT_support_governance_2026-08-10.md:40` records that a task *"Build
16_spine_runtime.md"* was **marked completed**. It was not built. The tracking said done; the
artefact was five lines.

**The trap is self-sealing and worth naming precisely**, because it is the mechanism, not the
accident:

1. The Index named **code** (`runtime/spine/spine.py`) as the volume's canon.
2. A volume whose canon is code is marked ✅ Live.
3. The Whole-Canon Build Queue exempted every ✅ Live volume — *"ALREADY LIVE (canon = code;
   write spec only if formalisation needed): I, II, III, IV, …"*.
4. So Volume IV was never queued, so it was never written, so nothing ever caused it to exist.

The consequence is not bureaucratic. **Code named as canon cannot be wrong.** There was no
document to check `spine.py` against, so the turn order — the single thing four other volumes'
core guarantees assume — was whatever `spine.py` happened to do that week, changing without a
canon amendment and with nothing able to detect it.

**The rule this volume exists to establish:** *code existing is never evidence that canon
exists.* An implementation may be cited as a volume's **grounding**; it may never be cited as
its **spec**.

## Status vocabulary — read this before the chapters

`implementation: LIVE-BUT-UNCANONISED` is a deliberate and unusual value. Every other volume in
the canon is `PENDING` or `PARTIAL` — a spec written ahead of the code. Volume IV is the
inverse: **the code has been carrying load in production for months and the specification is
one day old.**

That reverses the normal precedence rule. `16_runtime_contracts.md` opens with *"If code
conflicts with this document, the document is right."* **That sentence does not apply to
Volume IV Chapter 1.** Chapter 1 is a *transcription* of `spine.py`, not an instruction to it.
Where this volume describes the turn order, **the code is current truth and the document is the
record**; where this volume states an *invariant* (Chapter 2), the invariant is law and any
divergence is a named, dated gap with an owner — never a silent one.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V4-CH01 | Chapter 1 | The Turn Loop — the canonical order, transcribed from live code | READY FOR REVIEW |
| ELO-V4-CH02 | Chapter 2 | Ordering Guarantees and Invariants | READY FOR REVIEW |
| ELO-V4-CH03 | Chapter 3 | `CognitiveState` — The Carrier | READY FOR REVIEW |
| ELO-V4-CH04 | Chapter 4 | Spine Failure and Degradation (tier drops, contributor failure, cold start) | **NOT WRITTEN** — see Scope |
| ELO-V4-CH05 | Chapter 5 | The Silent Turn (the loop with no input; presence, not request-response) | **NOT WRITTEN** — see Scope |

## Scope

**In scope (this volume owns it):**
- The **order** of the turn: which faculty runs in which position, what each contributes, where
  assembly happens, where the decision happens, where output is produced.
- The **ordering invariants** other volumes depend on, each with a named dependant and a test
  that fails if the sequence changes.
- `CognitiveState` as the **single carrier** between faculties and the Executive — its slots,
  who writes each, who reads each.
- The spine's **freezing discipline**: what is frozen at which point, and what may still mutate.

**Out of scope (owned elsewhere — this volume orders them, it does not specify them):**
- *What* perception senses → Volume XII. *What* the world contains → Volume XV.
- *How* attention competes → Volume VI. *How* the Executive reasons → Volume VII.
- *How* assembly composes its components → Volume XVI Ch.2.
- *How* movement reaches the body and confirmations return → Volume XI, Volume VII Ch.5.
- The four contracts' *shapes* and *ownership* → **Volume III** (written alongside this one).

**Deferred to Ch.4 / Ch.5 (named so the gap is visible, not silently absent):**
- Per-stage degradation tiers and where in the turn Volume XX's tier drop is applied.
- The turn that runs with no user input (Vol VII §2.4: *"a Moment that only exists when David
  types is a chatbot's context window, not a companion's present tense"*). `spine.run()` today
  is entered only from a request path (`server.py:2926`); there is no idle-loop caller. That is
  a real gap and Ch.5 is its home.

## Definition of Done

- [x] The live turn order transcribed with file+line citations (Ch.1)
- [x] Each ordering guarantee stated with its dependant volume and a test shape (Ch.2)
- [x] `CognitiveState` slot ownership: who writes, who reads (Ch.3)
- [x] Every canon-vs-code disagreement named, dated, and attributed to code as current truth
- [x] Ruling E (shared ownership + mandatory reporting) encoded as an ordering invariant (Ch.2 §2.5)
- [x] Ruling F (identity asserted by the spine, never sourced from learned weights) encoded (Ch.3 §3.6)
- [ ] Chapter 4 (failure and degradation) written
- [ ] Chapter 5 (the silent turn) written
- [ ] `IT: the document and spine.py agree` — the executable canon-vs-code check — built (Ch.2 §2.8)
- [ ] CA review + David L3 → RATIFIED

## What this volume found (summary — the detail is in the chapters)

Reading the live spine end-to-end surfaced five things canon did not previously record. They
are stated here so they are not buried:

1. 🔴 **Assembly does not precede the decision at process level.** `exec_decide()` runs at
   `server.py:2322`, ~600 lines before `spine.run()` is entered at `server.py:2926`.
   `_executive_faculty()` (`spine.py:456`) *transcribes* that decision (`spine.py:162`); it does
   not make one. **Ruling C / ADR-Exec-006 D4 is VIOLATED at runtime.** (Ch.2 §2.3)
2. 🔴 **`EmbodimentState` is built before the utterance exists.** `build_embodiment_state()`
   runs at `spine.py:503`; `_conversation_faculty()` — which sets `plan.direct_response` — runs
   at `spine.py:509`. `build_embodiment_state` reads `plan.direct_response` at `spine.py:599`.
   On every direct-response turn, `response_text` / `display_text` / `tts_text` are published
   **empty**. (Ch.2 §2.6)
3. ⚠️ **`CognitiveState` is assembled with 11 of ~50 declared slots populated.** Memory,
   relationship, environment, conversation-matrix and human-interaction slots are all left at
   their dataclass defaults (`spine.py:576–588`). The contract advertises a completeness the
   assembly does not deliver. (Ch.3 §3.3)
4. ⚠️ **Relationship contributes to the PLAN, not to `CognitiveState`.** `rel_analyse()` runs at
   `spine.py:435` but its output goes to `enrich()` at `spine.py:470`, *after* the Executive.
   `16_runtime_contracts.md` lists Relationship Faculty as a `CognitiveState` contributor. It is
   not one. (Ch.3 §3.4)
5. ⚠️ **`PerceptionResult` is never pinned to the plan.** The comment at `spine.py:462` reads
   *"Store frozen world + perception on plan"*; line 463 stores only `plan.world`. Perception
   survives the turn only through whatever `assemble_world_state()` copied out of it. (Ch.2 §2.1)

## Needs David

- **IV-1 — Ruling C closure sequencing.** Moving the `decide()` call site from `server.py:2322`
  into the post-assembly position inside `spine.run()` is a Builder-lane change around a module
  under `FREEZE_V1_LOCK`. Before or after Presentable v1? *(Duplicates `OQ-VII-3`; recorded here
  because Volume IV is where the ordering invariant now lives.)* **Architect recommendation:
  after Presentable v1, as the first deliverable of WO-CANON-IV, sequenced WITH WO-CANON-XVI and
  never against it.**
- **IV-2 — The empty-`EmbodimentState` bug (finding 2 above).** This is a live behaviour defect,
  not a canon question, but it is identity-adjacent: every surface (Unity, robot LED, TTS) is
  currently handed an empty utterance on direct turns. **Architect recommendation: Builder WO,
  urgent, ahead of the Ruling C move — it is a two-line reorder (`spine.py:503` after `:509`)
  and it is silently degrading every direct-response turn.** Flagged, not fixed: the Architect
  does not touch product code (Rule #3).
- **IV-3 — Is Volume IV allowed to bind `server.py`?** The turn order this volume canonises
  begins *outside* the spine — memory read, attention compute and the Executive decision all
  happen in `server.py` before `spine.run()`. Either the spine's boundary is redrawn to include
  them, or `server.py`'s pre-spine section becomes a named, canonised part of the turn.
  **Architect recommendation: the second — name it "the pre-spine prologue" in Ch.1 §1.1 (done)
  and treat closing IV-1 as the act that dissolves it.** Confirm.
- **IV-4 — Turn identity.** `assemble_world_state(turn_id=raw[:32] ...)` (`spine.py:366`) uses
  the first 32 characters of the user's text as the turn id. Volume XV depends on `turn_id` for
  perishability (Vol XV §1.8: *"a stale one must be dropped, never reused across turns"*); two
  identical inputs produce the same id, and a silent turn produces `""`. **Architect
  recommendation: a monotonic per-session turn counter, owned by the spine, threaded to every
  assembly. Small, and it is a precondition for every perishability test in Vols XV/XVI/VII.**

## References

- `FOUNDATION_VOLUMES_STATUS_2026-08-10.md` — the assessment that ordered this volume written,
  and written **with Volume III** (*"Written apart, they will drift from each other exactly as
  III has already drifted from `spine.py`"*).
- `16_spine_runtime.md` — the 5-line stub this volume supersedes.
- `16_runtime_contracts.md` — the contract vocabulary; updated 2026-08-13 to point here.
- `CANON_RULINGS_2026-08-10.md` — Ruling C, Ruling E, Ruling F.
- `adr/ADR-Exec-006_Executive_Assembly_The_Moment.md` · `adr/ADR-Exec-002_Single_Cognitive_Truth.md`
- `Volume_VII/02_Executive_Assembly_and_The_Moment.md` (the ordering *law*; this volume is the
  ordering *record*) · `Volume_VII/05_Brain_Body_Brain_The_Closed_Loop.md`
- `Volume_XVI/02_Executive_Assembly_One_Plan.md` (the assembly *mechanism*)
- `Volume_XV/01_Unified_World_State.md` · `Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md`

---

```
Volume IV — The Cognitive Spine
Status: REVIEW · NOT RATIFIED
Implementation: LIVE-BUT-UNCANONISED (the code predates the spec by months)
Chapters written: 3 of 5 (Ch.4 failure/degradation and Ch.5 the silent turn are named, not written)
Origin text: none — transcribed from runtime/spine/spine.py, IRV 2026-08-13
Encodes: Ruling C (ordering) · Ruling E (ACK before belief) · Ruling F (identity from the spine)
🔴 Records TWO live ordering violations: assemble-before-decide (server.py:2322) and
   EmbodimentState-before-utterance (spine.py:503 vs :509)
Needs David: IV-1 … IV-4
```

READY FOR REVIEW
