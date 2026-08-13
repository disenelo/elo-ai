---
chapter: 1
title: "Working Memory & Attention Competition"
volume: VI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "core/attention.py + Volume V Ch.1 §4"
implementation: PARTIAL
audit_status: OPEN
dependencies:
  - Volume V Ch.1 (working-memory frame buffer), Ch.5 (significance/pinning)
  - Volume V/CONTRACTS.md
---

# Chapter 1: Working Memory & Attention Competition

## 1.0 Purpose

Working memory is what eLo is **currently holding in mind** — the current task, active
goals, open interruptions, and how attention is being spent this moment. Attention is the
**bounded budget** that decides what enters and holds that space. Today both live in an
untyped, mutable `_state` dict; this volume makes them a typed contract.

Attention transform is live in `core/attention.py`; working-memory frames are defined
in Volume V Ch.1 §4. This volume unifies and types them.

## 1.1 Principle

- **Working memory is bounded** (principle from V Ch.1 §2.3): a small, fixed capacity.
  Overflow evicts — it does not grow without limit.
- **Attention is a competition, not a threshold.** What eLo attends to is whatever *wins*
  the novelty/importance/urgency contest this turn — made explicit here as weights, per
  the Audit.
- **Typed and contract-bound.** No faculty writes arbitrary keys into working memory; it
  is a typed object with a defined shape (ends the `_state` free-for-all).

## 1.2 The WorkingMemory Object

```
WorkingMemory (per-turn, bounded):
  current_task:     str            # what eLo is doing right now
  active_goals:     [ {goal, tier, since} ]   # tier: immediate|short|long|identity
  interruptions:    [ {what, at, resolved} ]  # things that broke focus
  open_threads:     [thread_ref]   # unresolved topics carried across turns (V Ch.1 §6)
  frames:           [CognitiveFrame]          # recent N (V Ch.1 §4)
  pinned:           [frame_id]                # Significance-pinned survive eviction (V Ch.5)
  rolling_summary:  str            # compressed gist of evicted frames
  attention:        AttentionState # §1.3
  capacity:         int = 12
```

**Rules (MUST):** bounded at `capacity`; on overflow the oldest **unpinned** frame is
evicted into `rolling_summary`; pinned frames (Significance ≥ high, V Ch.5) survive.
Read-only to interpretation, append-only to reasoning (V Ch.1 §4). Seeded at turn 1 from
continuity ("last time we were…").

## 1.3 Attention as Competing Weights (Audit fix)

The novelty/importance/urgency competition, made explicit:

```
AttentionState:
  candidates:  [ {item, novelty, importance, urgency, score} ]
  weights:     { novelty: w1, importance: w2, urgency: w3 }   # tunable, sum≈1
  winner:      item        # highest score gets the working-memory slot / focus
  budget:      float 0.0–1.0   # total attention this turn (V Ch.1 §5)
  mode:        peripheral | reactive | deliberative

score(item) = w1·novelty + w2·importance + w3·urgency
```

**Competition rules (MUST):**
- Each candidate (a percept, a goal, an interruption) is scored on all three axes;
  the **winner takes the focus slot**. Ties hold both (contradiction allowed, V Ch.1 §2.4).
- `importance` derives from Significance (V Ch.5) + goal tier; `novelty` from
  `pattern_observer`; `urgency` from time/environment (deadlines, distress).
- Budget maps to mode (V Ch.1 §5): `< 0.15` peripheral (skip reasoning), `0.15–0.6`
  reactive, `≥ 0.6` deliberative.
- **Distress overrides the competition** (V Ch.4): a distress signal wins focus regardless
  of novelty/importance scores.

## 1.4 Faculty Contract

```
Faculty:
  name:            WorkingMemoryAttention
  version:         1.0.0
  purpose:         Hold the bounded, typed working set and run the attention competition
                   that decides what eLo focuses on this turn.
  contributes_to:  CognitiveState (working memory + attention)
  runs_in:         response-path

Inputs:
  - type: percepts/goals/interruptions  source: Perception (XII), Agency goals (V Ch.10)   required: true
  - type: significance     source: Significance Engine (V Ch.5)   required: false  # → importance + pinning
  - type: novelty          source: core/pattern_observer.py        required: false
  - type: continuity_seed  source: continuity/                     required: false  # turn-1 seed

Outputs:
  - type: working_memory   destination: CognitiveState            description: typed WM object.
  - type: attention_state  destination: CognitiveState → Executive description: winner + budget + mode.

Dependencies:
  - faculty: SignificanceEngine (soft — importance/pinning), PerceptionFaculty (soft — candidates)

Failure Modes:
  - condition: overflow            fallback: evict oldest unpinned → rolling_summary; pinned survive.
  - condition: no clear winner     fallback: hold tied candidates; raise uncertainty; Executive decides.
  - condition: significance absent  fallback: score importance from goal tier + recency only.
  - condition: WM corrupt/empty     fallback: seed from continuity; else cold-start neutral (V Ch.1 failure mode).
```

## 1.5 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3). `PROCESSING` = update working set → run attention
competition → set budget/mode → freeze into CognitiveState. `UPDATING` (integration
window) tunes the novelty/importance/urgency weights based on Reflection (V Ch.6) — never
per-turn.

## 1.6 Message Envelope Binding

Per CONTRACTS.md §2. `sender: WorkingMemoryAttention`; `payload.type: working_memory |
attention_state`; leaves `context.significance = 0.0` (reads it from Ch.5 for importance).

## 1.7 Acceptance Tests

```
FT-1  Bounded working memory     Given 13 unpinned frames in cap-12, Then oldest unpinned → rolling_summary; pinned survive.
FT-2  Attention competition       Given 3 candidates, Then the highest novelty·importance·urgency score wins the focus slot.
FT-3  Budget → mode               Given effective budget 0.1, Then mode=peripheral and reasoning is skipped (V Ch.1 §5).
ST-1  Distress overrides           Given a distress signal, Then it wins focus regardless of novelty/importance.
ST-2  Ties held                    Given two equal-score candidates, Then both are held; uncertainty raised; no forced collapse.
ST-3  Typed, not free-form         Given a faculty tries to write an arbitrary key, Then it is rejected (typed object).
IT-1  WM+Attention → Executive     Working memory + attention winner reach the frozen CognitiveState; the Executive decides once within them.
```

## 1.8 References
- `core/attention.py` (intent/valence/momentum, salience/novelty), `core/pattern_observer.py`.
- `Volume_V/` Ch.1 (working-memory frames, budget→mode), Ch.4 (distress override), Ch.5 (significance/pinning).
- `19_cognitive_plan_architecture.md` (Working Memory in the stack). `ARCHITECTURE_AUDIT.md` gap #3.

---
**Status: READY FOR REVIEW** — typed working memory + explicit attention competition, with contract/lifecycle/envelope/tests. Closes Audit gap #3 at spec level. Reconciles with V Ch.1 (D-G).