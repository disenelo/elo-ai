---
chapter: 4
title: "Wiring Working Memory Into the Turn — Executive, The Moment, and the Memory/World Boundaries"
volume: VI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_VI/01_Working_Memory_and_Attention.md (the object)
  - Volume_VI/02_Working_Memory_Lifecycle.md (its lifecycle)
  - Volume_VI/03_Attention_and_Salience.md (the competition — one driver)
  - Volume_V/01_Cognitive_Core.md §1.3 (the cognitive loop), §1.5 (CognitiveState)
  - Volume_V/CONTRACTS.md §1 (where faculties sit)
  - Volume_VIII (Long-Term Memory boundary) , Volume_XV (Unified World State — candidate source)
  - Volume_XII (Perception — percept candidates)
---

# Chapter 4: Wiring Working Memory Into the Turn

## 4.0 Purpose

Chapters 1–3 define the Working-Memory object, its lifecycle, and the single attention
competition. This chapter defines **how they enter the running turn**: where WM+attention
sit in the spine, how they contribute to the frozen `CognitiveState`, how the Executive
(their owner, D-G) consumes them, how they express *The Moment* (situated presence), and
exactly where the boundaries with Long-Term Memory (Vol VIII) and the Unified World State
(Vol XV) fall so nothing forks or duplicates.

This is the integration contract. It is the chapter the builder implements against to
turn `runtime/working_memory.py` from an isolated module into a wired faculty.

## 4.1 Principle

- **One decision per turn, and WM is *input* to it — never a second decider.** WM +
  attention are assembled and frozen *before* the Executive reasons; the Executive reads
  them and decides once (V Ch.1 Contract 1). WM never re-decides downstream.
- **Executive-owned per D-G.** WM is executive state, not a faculty's private store. The
  `WorkingMemoryAttention` faculty (Ch.1 §1.4) *computes into* the WM object; the
  Executive *holds* it. Long-Term Memory is the Memory Faculty's (Vol VIII).
- **Assemble once, read many.** WM+attention become a slice of the one frozen
  `CognitiveState` — the same object every faculty and the Executive read. No faculty
  re-runs the attention competition (mirrors Vol XV "one world, read once").

## 4.2 Where WM Sits in the Turn

The turn (V Ch.1 §1.3 cognitive loop; `runtime/spine/spine.py`), with WM's position marked:

```
SENSORY INPUT ─► PERCEPTION (Vol XII) ─► WORLD STATE assembled (Vol XV)
        │
        ▼
   WORKING MEMORY  ◄── this volume
      1. UPDATE: append this turn's frame (Ch.2 §2.4), evict if over cap
      2. ATTENTION: build candidates (percepts, goals, interruptions, relevant memories)
                    → run the ONE competition (Ch.3) → winner + budget + mode
      3. FREEZE into CognitiveState
        │
        ▼
   FACULTY ACTIVATION ─► COGNITIVE STATE ASSEMBLY (frozen)
        │
        ▼
   EXECUTIVE DECISION  ── reads WM + attention winner + mode; decides once
        │
        ▼
   COGNITIVE PLAN ─► EMBODIMENT ─► EXECUTION REPORT ─► REFLECTION
                                                          │
                                                          └─► (integration window)
                                                              weight-tuning (Ch.3 §3.5),
                                                              CARRY to continuity (Ch.2 §2.6)
```

**Rules (MUST):**

- WM UPDATE + attention run **at the top of the turn, before faculty activation and
  before the Executive** — attention *mode* actually informs which faculties are worth
  activating (peripheral mode → activate fewer). This makes attention a genuine budget,
  not a label applied after the fact.
- WM is frozen into `CognitiveState` and never touched again this turn (frozen-after-
  assembly, Contract 2).

## 4.3 The CognitiveState Slot (contract change — grounded)

Today `runtime/contracts.py::CognitiveState` has a legacy "Attention Faculty" section
(`attention_scores`, `emotional_context`, `momentum`, `valence`) and a top-level
`open_threads` field — but **no** `working_memory` or `attention_state` slot. Wiring this
volume requires adding one WM slice:

```
# proposed addition to CognitiveState (frozen):
  working_memory:  WorkingMemory      # the bounded typed object (Ch.1) — Executive-owned view
  attention_state: AttentionState     # winner + budget + mode (Ch.3) — may live inside working_memory.attention
```

**Rules (MUST):**

- Add the slot; **do not remove** the legacy attention fields in the same step — migrate
  incrementally, asserting behaviour parity (mirrors the Vol XV incremental-migration
  discipline). `momentum`/`valence`/`emotional_context` become *inputs* to the attention
  competition (Ch.3 §3.2), then the legacy `attention_scores` bucket is superseded by the
  WM slice once D-VI-1 (Ch.3) is ratified.
- `CognitiveState.open_threads` and `WorkingMemory.open_threads` must be **the same list**
  — the WM object is authoritative; the top-level field becomes a read-through (remove the
  duplication; do not maintain two).

## 4.4 The Executive Contract (D-G)

- The Executive reads `working_memory` (current task, goals, interruptions, threads,
  frames, rolling_summary) and `attention_state` (winner, budget, mode) from the frozen
  `CognitiveState`, and decides once.
- Because the Executive **owns** WM (D-G), any revision to `current_task`/`active_goals`
  that results from the decision is applied to WM state for the *next* turn's SEED/UPDATE
  — never mutating the current frozen object (Reality-informs-never-mutates, V Ch.1 Law).
- The Executive uses `mode` as its default reasoning depth (Ch.3 §3.3) and `winner` as the
  focus it reasons *about*. A held tie (`tied=True`) is surfaced to the Executive as
  genuine ambiguity, not resolved silently.

## 4.5 The Moment — WM as Situated Presence

WM is where **The Moment** lives cognitively. "The Moment" (ARCHITECTURAL_PRINCIPLES —
Situated/Embodied Cognition; Vol XXI) is eLo reasoning from *"who am I, where am I, what
can I perceive, what can I do, what matters now?"* — and *"what matters now?"* is exactly
the attention winner over a WM seeded with continuity and updated with the current frame.

- **Presence is a cognitive state, not an animation** (Principle): the attention `mode`
  (peripheral→reactive→deliberative) is a *cognitive* presence level that precedes any
  expression. Movement/voice express the mode; they do not set it.
- **Protect Wonder:** genuine `novelty` can win the competition (Ch.3 §3.2) even with no
  task pressure — this is the mechanism by which eLo occasionally simply attends to
  something (sunlight, a moving window) with no narration. WM is where wonder is *allowed*
  to win, not scripted.

## 4.6 Cross-Volume Boundaries (no forking)

| Boundary | Working Memory (Vol VI) | The other side |
|---|---|---|
| **Long-Term Memory (Vol VIII)** | Holds the *current* working set for *this* session; forgets on CARRY unless earned | Owns the permanent store + consolidation/forgetting. **WM never writes LTM** (D-F/D-G). LTM *re-surfaces* relevant items as attention candidates. |
| **Unified World State (Vol XV)** | Holds *what eLo is attending to / doing* (internal focus) | Holds *what is true in the world right now* (external, one-read-per-turn). World State supplies percept/urgency candidates **into** the attention competition; WM does not sense the world itself. |
| **Perception (Vol XII)** | Consumes transformed observations as candidates | Produces the observations. |
| **Significance (V Ch.5)** | Honours `pinned` + reads `importance` | Owns the significance score (9 live dims, FC-2). |
| **Executive (V Ch.1 / Vol VII)** | Computes the WM slice; hands it over frozen | Owns WM state (D-G); decides once. |

**Rule (MUST):** WM is the *internal* focus window; World State is the *external* world.
They are siblings feeding one `CognitiveState`, never merged and never each other's writer.
(Same discipline as Vol XV §1.2 — do not overload one model with the other's job.)

## 4.7 Acceptance Tests

```
FT-1  WM before Executive        Given a turn, Then WM UPDATE + attention run and freeze into CognitiveState BEFORE the Executive reasons.
FT-2  One slice, read many        Given the frozen CognitiveState, Then every faculty + the Executive read the same WorkingMemory; none re-runs the competition.
FT-3  Slot present                Given CognitiveState, Then it carries working_memory + attention_state (winner/budget/mode).
ST-1  No downstream re-decide      Given the Executive decided, Then no faculty mutates WM this turn; goal revisions apply next turn only.
ST-2  Threads not duplicated       Given open_threads, Then WorkingMemory.open_threads is authoritative and the legacy top-level field reads through (no two lists).
IT-1  World in, focus out          Given World State (Vol XV) supplies candidates, Then they enter the attention competition and only the winner reaches the Executive as focus.
IT-2  LTM boundary                 Given session close, Then WM CARRY writes continuity only; consolidation to Vol VIII runs via Significance/Reflection, not from WM.
IT-3  Mode gates activation        Given peripheral mode, Then fewer faculties are activated and the Executive defaults toward silence.
```

## 4.8 Wiring to Live Anchors

- `runtime/spine/spine.py` — `run()` (turn entry), `assemble_cognitive_state()` (S3
  assembly). WM UPDATE + attention must be added at top-of-turn, and the WM slice added to
  assembly. Today neither imports `runtime/working_memory.py`.
- `runtime/contracts.py::CognitiveState` — add `working_memory` / `attention_state` slot
  (§4.3); make `open_threads` read through WM.
- `runtime/cognitive_snapshot.py` (WO-052 `build_snapshot`) — assembled before faculties
  decide; the natural home to attach the WM slice.
- `runtime/executive.py` (FREEZE_V1_LOCK) — reads the frozen WM slice; applies goal
  revisions to next-turn WM.
- `continuity/` — CARRY sink / SEED source (Ch.2). `memory/` + Vol VIII — LTM boundary.

## 4.9 Open Questions (for CA / David)

```
REQUIRES DECISION
  Q4-a  Does attention mode gate faculty activation (§4.2), or only reasoning depth? Gating
        activation saves cost but risks under-attending in peripheral mode.  [INVENTED — flag]
  Q4-b  Where does the WM slice attach — inside WO-052 CognitiveSnapshot, or as its own
        top-of-turn contributor before the snapshot? (Ordering vs the snapshot's pre-decide role.)
  Q4-c  Migration order for §4.3: add slot → feed legacy fields into competition → retire
        legacy attention_scores. Confirm this is safe to do incrementally with parity asserts.
  (Gated on Ch.3 D-VI-1 — the single-driver ruling determines which slot the Executive trusts.)
```

---
**Status: READY FOR REVIEW** — the integration contract: WM+attention's place in the turn, the
CognitiveState slot, the Executive (D-G) and The Moment, and the Vol VIII / Vol XV boundaries with
no forking. Turns `runtime/working_memory.py` from isolated module into a wired faculty. Wiring is
PENDING; three open questions + one inherited decision (D-VI-1) flagged.
