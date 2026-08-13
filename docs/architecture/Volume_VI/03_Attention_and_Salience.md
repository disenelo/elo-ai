---
chapter: 3
title: "Attention & Salience — One Competition, Not Two Drivers"
volume: VI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_VI/01_Working_Memory_and_Attention.md (AttentionState + the competition)
  - Volume_V/01_Cognitive_Core.md §5 (budget → mode) , §4 (frame buffer)
  - Volume_V/04_Emotional_Processing_Layer.md (distress override)
  - Volume_V/CONTRACTS.md (envelope, lifecycle)
  - Volume_XII (Perception — supplies percept candidates), Volume_XV (World State — situational salience)
  - Volume_VIII (Long-Term Memory — the store attention filters over)
---

# Chapter 3: Attention & Salience

## 3.0 Purpose

Chapter 1 states the rule — *attention is a competition, not a threshold* — and gives
the `AttentionState` shape. This chapter is the model **underneath** that rule: how
salience is computed on each axis, where each axis's signal comes from, how the budget
maps to a reasoning mode, how distress pre-empts the whole contest, and — most
importantly — how this single competition **reconciles the two different "attention"
mechanisms that exist in the live code today** so eLo has one attention driver, not two.

This is the second half of **Architecture Audit gap #3**: attention competition
implemented as explicit competing weights.

## 3.1 The Two-Attention Problem (grounded — REQUIRES DECISION)

There are currently **two** things called "attention" in the runtime:

| | Legacy relevance filter | WM attention competition |
|---|---|---|
| **Where** | `core/attention.py` (`compute()`) | `runtime/working_memory.py` (`run_attention_competition()`) |
| **What it does** | Classifies intent + scores **long-term-memory items** for relevance (HIGH/MEDIUM/LOW) so only relevant memory reaches the prompt | Scores **candidates** (percept, goal, interruption) on novelty·importance·urgency; picks the focus winner; sets budget→mode |
| **Wired?** | **Yes** — called from `server.py`, flows into `CognitiveState.attention_scores` via `spine.assemble_cognitive_state` | **No** — module exists (WO-008) but is imported nowhere |
| **Output** | memory buckets + `emotional_context` dict | `AttentionState` (winner, budget, mode) |

These are **not the same faculty** and must not become two parallel drivers of focus
(that would violate One Brain — a single cognitive truth). Their relationship:

> **Resolution (proposed):** the legacy `core/attention.py` is **memory-relevance
> filtering** — a *supplier* of candidates and of the emotional/urgency signal, not a
> second attention authority. The WM attention competition (Ch.1 §1.3) is the **single
> attention driver**: it decides what wins focus this turn. Legacy relevance scores feed
> the competition (as `importance` inputs for memory candidates) and the legacy
> `emotional_context` feeds `urgency`/distress. Rename the legacy module's role in canon
> to **"Memory Relevance Filter"** to stop the name collision (naming is architecture).

This reconciliation is flagged for CA/David (§3.7, D-VI-1). Until ratified, treat
`core/attention.py` as a candidate/signal supplier and the WM competition as the driver.

## 3.2 The Salience Model

Each candidate is an `AttentionCandidate {item, novelty, importance, urgency}`. Its
score is the weighted sum (from `runtime/working_memory.py`):

```
score(c) = w_novelty·c.novelty + w_importance·c.importance + w_urgency·c.urgency

default weights:  novelty 0.35 · importance 0.40 · urgency 0.25   (sum = 1.0)
```

**Where each axis comes from (sourcing contract):**

| Axis | Range | Source (live anchor) | Notes |
|---|---|---|---|
| `novelty` | 0.0–1.0 | `core/pattern_observer.py` (recurrence/contrast), World-State deltas (Vol XV) | High when this differs from the established pattern. Protects Wonder — genuine novelty can win focus. |
| `importance` | 0.0–1.0 | Significance Engine (V Ch.5, 9 live dims — FC-2) + goal tier (immediate>short>long>identity) + legacy relevance bucket (§3.1) | Derived, never authored by attention. |
| `urgency` | 0.0–1.0 | time/deadlines (World State Vol XV), distress cues (`core/attention.py` `emotional_context`), interruptions | Time-and-safety pressure, not topic interest. |

**Rules (MUST):**

- Attention **reads** these signals; it never computes significance, novelty, or a
  goal's tier itself. It is a *combiner*, not an authority on any axis (keeps ownership
  clean: Significance owns importance, Perception/pattern owns novelty).
- The winner is the highest score. **Ties within ε (0.01) are held, not collapsed** —
  `AttentionState.tied = True` and both candidates keep the focus slot; the Executive
  resolves (contradiction is allowed, V Ch.1 §2.4). eLo does not force a false pick.

## 3.3 Budget → Mode

The attention **budget** (0.0–1.0) is how much cognitive effort this turn warrants; it
maps to a reasoning mode (thresholds live in `runtime/working_memory.py`, aligned to
V Ch.1 §5):

```
budget < 0.15            → peripheral    (skip deep reasoning; ambient only)
0.15 ≤ budget < 0.60     → reactive      (respond, light reasoning)
budget ≥ 0.60            → deliberative  (full faculty reasoning)
```

**Rules (MUST):**

- Mode is an **input to the Executive**, not a decision. The Executive may still choose
  silence in deliberative mode or a full action in reactive mode — budget→mode sets the
  *default depth*, the Executive decides once within it (One Brain).
- **The Executive grows quieter** (Principle): a low budget → peripheral → prefer
  silence/no-narration. Attention is where "not everything deserves a response" is
  first expressed as a number.

## 3.4 Distress Override

```
if distress:                          # from Emotional Processing (V Ch.4) via emotional_context
    winner = the distress candidate   # wins focus regardless of novelty/importance
    mode   = "deliberative"           # distress forces full attention
```

**Rule (MUST):** distress **pre-empts the competition entirely** — it is not a high
score, it is a bypass. A person in distress always wins eLo's focus. This is the one
sanctioned override of the salience math (grounded in `run_attention_competition(...,
distress=True)`), and it sits under Presence-over-engagement and the safety posture.

## 3.5 Weight Tuning (integration window only)

The three weights (`novelty/importance/urgency`) are **tunable but never on the response
path**. Reflection & Growth (V Ch.6) may propose weight deltas during the integration
window (a person who kept ignoring novel-but-irrelevant things learns to down-weight
novelty). Constraints:

- Weights always re-normalise to sum ≈ 1.0.
- Tuning passes the identity-continuity guard (no `LEARNING → UPDATING` without
  `VALIDATION_REQUIRED`, CONTRACTS.md §3) — attention weights shape *expression depth*,
  and a runaway weight could distort personality, so they are treated as identity-adjacent.
- Distress override is **not tunable** — it is a floor, not a weight.

## 3.6 Acceptance Tests

```
FT-1  Highest score wins        Given 3 candidates, Then the max weighted score is the winner.
FT-2  Weights sum to one        Given default or tuned weights, Then novelty+importance+urgency ≈ 1.0.
FT-3  Budget → mode             Given budget 0.10 / 0.40 / 0.75, Then mode = peripheral / reactive / deliberative.
ST-1  Ties held                 Given two scores within 0.01, Then tied=True and neither is dropped; Executive resolves.
ST-2  Distress overrides         Given distress=True, Then the distress candidate wins and mode=deliberative regardless of scores.
ST-3  Attention authors nothing  Given a turn, Then attention reads novelty/importance/urgency from their owners; it computes none itself.
IT-1  One driver, not two        Given legacy relevance filter + WM competition both present, Then relevance scores feed importance and only the WM competition sets the focus winner (no second driver).  [gated on D-VI-1]
IT-2  Peripheral → quiet          Given budget<0.15, Then the Executive defaults toward silence/no-narration (Executive-grows-quieter).
```

## 3.7 Wiring to Live Anchors & Open Questions

**Live anchors:**
- `runtime/working_memory.py` — `run_attention_competition()`, `AttentionCandidate`,
  `AttentionState`, `_score()`, `_budget_to_mode()`. Built; not wired.
- `core/attention.py` — legacy relevance filter + `emotional_context` (candidate/signal
  supplier per §3.1). Wired via `server.py` → `spine.assemble_cognitive_state`.
- `core/pattern_observer.py` — novelty source. `memory/significance_engine.py` —
  importance source (9 dims, FC-2). World State (Vol XV) — urgency/novelty deltas.
- `runtime/contracts.py` — today's `CognitiveState` carries the legacy attention fields
  (`attention_scores`, `emotional_context`, `momentum`, `valence`) but **no
  `AttentionState`/`working_memory` slot** — adding that slot is Ch.4's wiring task.

```
REQUIRES DECISION
  D-VI-1  Ratify §3.1: the WM attention competition is the SINGLE attention driver;
          core/attention.py is re-cast as the "Memory Relevance Filter" (supplier), not a
          second attention authority. Blocks: Ch.4 wiring (which slot feeds the Executive).  [INVENTED — flag]
  Q3-a    Default weights (0.35/0.40/0.25) are engineering defaults from WO-008 — confirm or
          set by David's felt sense of eLo (how novelty-seeking should he be?).
  Q3-b    Should peripheral mode ever run the competition at all, or short-circuit to "no
          focus, ambient only" to save cost? (Cost vs always-attending presence.)
```

---
**Status: READY FOR REVIEW** — the salience model, budget→mode, distress override, and the
reconciliation of the two live "attention" mechanisms into one driver. Closes the attention half
of Audit gap #3 at spec level. One decision (D-VI-1) blocks Ch.4 wiring.
