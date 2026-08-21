---
volume: III
title: "System Architecture — The Runtime Contracts and the Boundaries They Cross"
status: BUILDABLE — spec written. Ratification follows the build; it does not gate it. ("awaiting CA" removed 2026-08-21: David — "WHO THE FUCK ARE WE GATING AND HOLDING FOR!?" The CA is an agent and David is present. Nobody was waiting.)
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PARTIAL — the four contracts exist and are typed; two are not enforced as specified
Provenance: [ENGINEERING]
audit_status: OPEN
canonical_path: docs/architecture/Volume_III/
written: 2026-08-13
origin_text: docs/architecture/16_runtime_contracts.md (Canonical Reference v2.0, 256 lines, 2026-07-05)
grounding:
  - runtime/contracts.py (400 lines — the four contracts, typed)
  - runtime/spine/spine.py:544, :591, :614 (the contract factories) · runtime/spine/plan.py:22 (the LIVE plan)
  - blender_bridge/state_writer.py · blender_bridge/embodiment_publisher.py (the DOWN publisher)
  - docs/architecture/UNITY_ELOOS_IO_CONTRACT.md (David L3, 2026-08-06 — the boundary interface)
dependencies:
  - Volume IV (The Cognitive Spine — the ORDER these contracts are produced in). WRITTEN IN THE SAME PUSH.
  - 16_runtime_contracts.md (origin text; now points here)
  - CANON_RULINGS_2026-08-10.md Ruling E (shared ownership of movement + mandatory communication)
  - adr/ADR-Exec-002 (Single Cognitive Truth) · adr/ADR-Exec-003 (Embodied Truth) · adr/ADR-0001 (Faculty Bus)
  - Volume XI (Motor Cortex — the motor half of the DOWN/UP boundary) · Volume VII Ch.5 (brain > body > brain)
priority: "FOUNDATION — paired with Volume IV (FOUNDATION_VOLUMES_STATUS_2026-08-10.md §Recommendation #1)"
---

# Volume III — System Architecture

Volume III answers **what the pieces are and where they run.** Volume IV answers **in what
order they run.** Neither is complete without the other, which is why they were written in one
push.

- **Volume III owns:** the four runtime contracts (shape, ownership, mutation discipline), the
  process boundaries (eLo-OS Python · Unity DesktopBuddy · the bridge), and what may and may not
  cross each boundary.
- **Volume IV owns:** the turn order, the ordering invariants, and `CognitiveState` as the
  carrier.

## Why this volume exists — and why it is not a rewrite

Unlike Volume IV, Volume III has a real origin text. `16_runtime_contracts.md` (256 lines,
`Canonical Reference v2.0`, 2026-07-05) is **the most-cited foundation document in the canon** —
Vol XV, Vol V Ch.6 and the spine all take their contract vocabulary from it. It defines the loop
and the four contracts with producer/consumer/mutator discipline, and it opens with the right
instinct: *"If code conflicts with this document, the document is right."*

**This volume does not replace it. It cites it, expands it, and reconciles it with what runs.**

What the origin text lacks, and what this volume adds:

1. **No volume frontmatter, no Definition of Done, no acceptance tests, no lifecycle** — the
   blocks every other volume now carries.
2. **No process boundaries.** It describes four objects inside one process and says nothing
   about the second process (Unity) that consumes the third of them, or about the two files
   that are the entire interface between them.
3. **Drift.** Its named consumer, `runtime/spine/spine.py`, has evolved substantially since
   2026-07-05 (WO-CANON-VI/XII/XV/XVI markers are all visible in the live turn order) and the
   contract document does not reflect it. **Volume IV Ch.1 §1.5 is the drift register; Volume
   III Ch.1 is the reconciliation.**
4. **An undated embedded TODO** at line 221 (`## Passive Awareness (Immediate Fix)`) — an
   in-flight note inside a canonical reference. A canonical document with a live TODO in it is
   either stale or is a work order wearing the wrong hat. See Needs David III-4.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V3-CH01 | Chapter 1 | The Four Runtime Contracts and the Loop | READY FOR REVIEW |
| ELO-V3-CH02 | Chapter 2 | Process and Boundaries — what runs where, and what may cross | READY FOR REVIEW |
| ELO-V3-CH03 | Chapter 3 | Contract Ownership and Mutation, made testable | **NOT WRITTEN** — folded into Ch.1 §1.6 as a register; needs its own chapter to become enforceable |

## Scope

**In scope:**
- The four contracts — `CognitiveState`, `CognitivePlan`, `EmbodimentState`, `ExecutionReport` —
  their purpose, producer, consumer, mutator, and the point at which each freezes.
- The loop those four form, reconciled against the live runtime.
- The **DOWN/UP IO contract boundary**: `blender_state.json` (commands, continuous) and
  `unity_events.json` (ACKs/perceptions, discrete).
- The process map: eLo-OS Python (Builder lane) · Unity DesktopBuddy (Designer lane) · the bridge.
- **Ruling E** as a boundary law: shared ownership of movement, and the body's mandatory
  reporting duty as the binding obligation.

**Out of scope (owned elsewhere):**
- The *order* the contracts are produced in → **Volume IV**.
- `CognitiveState`'s slot-by-slot ownership → **Volume IV Ch.3** (it is the carrier, and the
  carrier is the spine's business).
- The motor half of the boundary — command grammar, movement vocabulary, embodiment parity →
  **Volume XI** (`01_Motor_Cortex_and_the_Body_Contract.md`, `02_Movement_Grammar_*`).
- The UP-relay *coverage* rule and the reflex line → **Volume VII Ch.5**.
- Plugin extension boundaries → Volume XIV (blocked on the Vol XXIII ownership ruling, F-1).

## Definition of Done

- [x] The four contracts promoted to chapter form with producer / consumer / mutator / freeze point
- [x] Reconciled against live code, with every disagreement named and attributed
- [x] The DOWN/UP IO contract boundary stated, with Volume XI named for the motor half
- [x] Process map: what runs where, in which lane, in which language
- [x] **Ruling E encoded**: shared ownership, brain owns intent, body owns execution, body MUST report
- [x] What must never cross a boundary, stated as a MUST NOT list
- [ ] Chapter 3 — contract ownership and mutation as an enforceable register with tests
- [ ] The embedded TODO in `16_runtime_contracts.md` resolved out of canon into a WO (III-4)
- [ ] Acceptance tests built (Ch.1 §1.8, Ch.2 §2.8 specify them; none exists)
- [ ] CA review + David L3 → RATIFIED

## What this volume found

1. 🔴 **`CognitivePlan` exists twice.** `runtime/contracts.py:175` declares a **frozen** one;
   `runtime/spine/plan.py:22` declares a **mutable** one. **The runtime uses the mutable one**
   and mutates it ten times after the decision. Canon says *"frozen at production."* (Ch.1 §1.3)
2. 🔴 **`ExecutionReport` is a contract with no producer.** `build_execution_report()` exists
   (`spine.py:614`) and `contracts.py:342` is fully typed — but nothing in the live turn calls
   it. The loop's fourth quarter (reality → reflection → integration) is **unclosed**, which
   means the delta that drives all learning is never computed. (Ch.1 §1.5)
3. ⚠️ **Two `EmbodimentState` publishers.** The typed contract is built at `spine.py:503`; the
   file that surfaces actually read is written by `blender_bridge/embodiment_publisher.py` via
   `state_writer.py`. The object and the serialisation are produced by different code paths.
   (Ch.1 §1.4, Ch.2 §2.4)
4. ⚠️ **The runtime imports the server.** `spine.py:226` does `import server` to reach response
   pools — a `runtime/ → server.py` dependency that inverts the intended layering. (Ch.2 §2.6)
5. ✅ **The IO boundary is genuinely well governed.** `UNITY_ELOOS_IO_CONTRACT.md` (David L3,
   2026-08-06) is the strongest artefact in this volume's territory: one rule (*channels are
   defined by direction and delivery type, never by topic*), two files, an action protocol with
   a timestamp guard and consumption semantics, and named change control binding both seats.
   Volume III adopts it rather than restating it.

## Needs David

- **III-1 — Do the two `CognitivePlan` classes converge, and when?** (= Vol IV `IV-7b`.) The
  frozen `contracts.py` version is canon; the mutable `spine/plan.py` version is what runs.
  **Architect recommendation: converge on the frozen one at the same time as the Ruling C
  call-site move (IV-1) — both touch the same code path, and doing them separately means
  touching `FREEZE_V1_LOCK`-adjacent code twice.**
- **III-2 — `ExecutionReport` has no producer.** Closing it is what turns "the delta between
  intention and reality" from a written principle into a measurable value. **Architect
  recommendation: this is the highest-leverage unbuilt thing in Volume III's scope — every
  learning claim in Vol XXVIII and ADR-Exec-005 depends on a report that is never produced.
  Builder WO. Not urgent for Presentable v1; blocking for anything called learning.**
- **III-3 — Where does the boundary of "the runtime" sit?** (= Vol IV `IV-3`.) Today
  `server.py` performs memory reads, the Executive decision, and prompt assembly, while
  `runtime/spine/` performs the faculty pass — and `runtime/` imports `server`. **Architect
  recommendation: `server.py` is a TRANSPORT, not a cognitive layer. Everything cognitive it
  currently does moves into `runtime/`, progressively, starting with the `decide()` call site
  (IV-1). Confirm the direction; the sequencing is the Builder's.**
- **III-4 — The embedded TODO** (`16_runtime_contracts.md:221`, *"Passive Awareness (Immediate
  Fix)"*, undated). Either it shipped and should be removed, or it is live and should be a WO.
  (= F-4 in `FOUNDATION_VOLUMES_STATUS_2026-08-10.md`.) **Architect recommendation: the
  Architect drafts it out of canon into a WO once the Builder confirms its state — and Vol IV
  Ch.3 §IV-3e finds the deeper issue anyway: `CognitiveState.graph_context` is never written by
  the assembler at all, so the fix should route passive awareness through `LiveWorldState`
  rather than revive a dead slot.** I cannot confirm from the document alone whether it shipped.

## References

- `16_runtime_contracts.md` — **origin text.** Cited throughout; updated 2026-08-13 to point here.
- `UNITY_ELOOS_IO_CONTRACT.md` — David L3 2026-08-06; the boundary interface, adopted by Ch.2.
- `FOUNDATION_VOLUMES_STATUS_2026-08-10.md` — the assessment that ordered III written with IV.
- `CANON_RULINGS_2026-08-10.md` — **Ruling E** (Ch.2 §2.3).
- `Volume_IV/` — the ordering half of this pair.
- `Volume_XI/01_Motor_Cortex_and_the_Body_Contract.md` · `Volume_VII/05_Brain_Body_Brain_The_Closed_Loop.md`
- Code: `runtime/contracts.py` · `runtime/spine/plan.py:22` · `runtime/spine/spine.py:544,:591,:614` ·
  `blender_bridge/state_writer.py` · `blender_bridge/embodiment_publisher.py`

---

```
Volume III — System Architecture
Status: REVIEW · NOT RATIFIED
Origin text: 16_runtime_contracts.md (256 lines) — cited and expanded, never replaced
Chapters written: 2 of 3 (Ch.3 contract ownership/mutation is named, not written)
Paired with: Volume IV — written in one push so they cannot re-drift
Encodes: Ruling E (shared ownership of movement + the body's mandatory reporting duty)
Findings: two CognitivePlan classes · ExecutionReport has no producer · two EmbodimentState
  publishers · runtime imports server · the IO boundary is well governed and is adopted as-is
Needs David: III-1 … III-4
```

READY FOR REVIEW
