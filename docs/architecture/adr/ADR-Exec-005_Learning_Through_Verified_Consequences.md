---
id: ADR-Exec-005
title: "Learning Through Verified Consequences — RL may optimise behaviour, never identity or truth"
status: ACCEPTED · CANON · LAW
date: 2026-08-10                 # date this ADR document was written
ratified: 2026-08-06             # David L3; Chief Architect proposal + CA amendment
owner: David Charles
author: Claude (Lead Architect)
supersedes: [ADR-Learn-001]      # absorbed — one learning ADR, not two
related: [ADR-Exec-001, ADR-Exec-003, ADR-Exec-006, Ruling D (2026-08-10)]
canon_home: DECISION_LOG.md index row (line ~240) → this document
source_material: Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md · ARCHITECTURAL_PRINCIPLES.md ("Learning From Consequences")
---

# ADR-Exec-005 — Learning Through Verified Consequences

> **Formalisation note (2026-08-10).** This is the **most-cited law in the canon (116 references)**
> and it existed only as a cell in a summary table. This document promotes it to a real ADR. It
> restates the ratified decision — including the Chief Architect's governing amendment — and adds
> **no new policy**. Volume XXVIII states the same boundary in full; this ADR is the law, XXVIII is
> the volume that builds against it.

## Context

eLo is designed for **Continuous Becoming** — it should get better at what it does. But a system
that learns from its own language learns from things that never happened: hallucinations, imagined
conversations, and things it merely *said*. A system that learns without a boundary eventually
optimises away the personality, values, and honesty guarantees built over months — Verified Speech
would become *"lying sometimes gives higher reward."*

So learning had to be given (a) a **source of evidence** it is allowed to learn from, and (b) a
**ceiling** it may never cross.

## Decision

**The Executive may adapt behaviour ONLY from verified outcomes.**

**D1 — Evidence rule.** **Language alone is never evidence.** Only *executed actions with verified
consequences* influence future policy. eLo does not learn because it talked; it learns because
something actually happened.

**D2 — Position in the loop.** Adaptation sits **AFTER** verification:

```
Execute → Verify → Outcome → Reflect → Learn → Memory
```

Learning passes through **Reflection** before **Memory**. It never runs on the intent, only on the
result.

**D3 — The constitutional boundary (the ceiling).**

> **Reinforcement Learning may optimise behaviours and skills, but it may NEVER alter identity,
> constitutional principles, Executive Authority, or verified truth.**

RL / adaptation is **not allowed to learn**: personality · values · ethics · memory truth ·
identity · Executive Authority · **speech correctness** · architectural principles. Those are
governed by the Constitution, the ADRs, and the Executive, and stay **deterministic**.

**D4 — The governing line (Chief Architect amendment, ratified with the ADR).**

> **Learning never modifies TRUTH — only future DECISION-MAKING.**
> RL **may** change: action preferences · exploration weighting · confidence · planning heuristics ·
> curiosity thresholds.
> RL **may never** change: memory truth · verified observations · Executive Authority · speech
> verification.
> **RL sits safely beneath Executive Authority.**

**D5 — Immutability split.** *Identity is immutable; policies adapt, skills improve, preferences
evolve, truth never changes.* Constitution defines **who**; the Executive decides **what**; RL
improves **how well**.

**D6 — Where it lives.** In a **Reinforcement & Adaptation (Learning) Faculty** — a faculty the
Executive *asks*, like any other — which sits **after Verify** in the loop. Never inside the
Executive, never inside identity. It runs simulations, learns policies, evaluates rewards, stores
policies, and reports confidence. It **never** rewrites code, the Constitution, or the Executive.

```
Executive (deterministic) → Movement Faculty → RL Policy → Action
```

**D7 — Reward is a VECTOR, not a scalar.** The learning signal is aligned to eLo's values:
**Meaning · Novelty · Relationship · Embodiment · Curiosity · Efficiency · Safety.** Learning
optimises *toward what matters*, not toward a number. (Reuse the existing Significance Engine —
see the contradiction flagged below.)

**D8 — Simulation-first.** eLo learns by running **simulated** attempts, storing policy +
confidence, and only acting for real above a confidence/safety threshold. Robot RL (RD-3) is
sim-only until David L3 + LG-2.

## Consequences

**Forbids**
- Any learning input derived from generated text, an unexecuted plan, an imagined conversation, or
  a gated action that never ran (a gated action produces a diagnostic record, not a learning
  signal — Vol XXIII §2.6).
- Personality drift self-applying to disk. Drift is a **validated proposal** through a gate
  (**Ruling D, David L3, 2026-08-10**, justified by this ADR).
- Any learned-policy update that changes identity, values, memory truth, or the verification path —
  such an update is **rejected as a VIOLATION, not accepted as a version** (Vol XXII §3.5 / §4.3).
- A faculty evolving past its genome's `constraints`, which MUST encode this boundary.

**Enables**
- Honest, measurable self-improvement: *"landing on narrow window edges: 68% → 94%"*, *"I've
  learned a smoother route between the browser and Spotify."*
- Habits: verified experience nudging preferences — **not** RL rewriting personality.
- Skills learned in one body informing behaviour in another (One Brain), because what transferred
  was a policy, not an identity.
- eLo becoming **more capable without becoming unstable.**

## How it is enforced

| Mechanism | Where |
|---|---|
| Learning runs only in the integration window, after Verify | `Volume_XVI/02_Executive_Assembly_One_Plan.md` §"reflection"; Vol XVI §184 |
| Reward vector via the Significance Engine | `memory/significance_engine.py` + Vol V Ch.5 (⚠ see O-5.1) |
| Reflection gate before Memory | Vol V Ch.6 (Reflection & Growth) · WO-027 |
| Personality change is proposal-only, gated | Ruling D · Vol X Ch.3 · `personality_evolution_faculty.py` (requires `confirmed`) |
| Genome registry rejects boundary-crossing versions | Vol XXII §3.5, §4.3 `[C]`/`[R]` gates, §4.5 |
| Memory truth immutable to learning | Vol XXIII Ch.3 §111; Vol XVI Ch.4 |
| Tier-tagged learning under degradation | Vol XX Ch.3 |
| RL scope-locked to four domains (movement · curiosity · presence timing · robot locomotion) | Vol XXVIII |

## Citations (representative — 116 references repo-wide, the most-cited law in the canon)

- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — the constitutional boundary, verbatim.
- `ARCHITECTURAL_PRINCIPLES.md` — "Learning From Consequences" (enduring value).
- `CANON_RULINGS_2026-08-10.md` **Ruling D** — *"Identity is not allowed to drift unsupervised
  (ADR-Exec-005)"* — David's own ruling is justified by this ADR.
- `Volume_XXII/03_*` and `04_*` — the genome's constitutional ceiling, stated in genome terms.
- `Volume_X/03_Drift_Management_vs_Healthy_Growth.md`; `Volume_XXI/01_*`, `03_*`;
  `Volume_XXIII/02_*` §2.6, `03_*`; `Volume_XX/03_Degradation_Honesty.md`;
  `Volume_IX/04_*` (imagined-speech firewall).
- `SITUATED_SELF_v1_assembly.md` §"habits"; WO-094 §D; WO-055; WO-070/071.

## OPEN — needs David (three live contradictions found by the 2026-08-10 audit)

These are **recorded, not resolved.** This ADR is written conservatively: where the canon and the
code disagree, the ADR states the law and flags the gap.

- **O-5.1 — the reward signal currently learns from LANGUAGE.**
  `significance_engine.evaluate()` takes **only user text + reply text**, scored by keyword tables —
  **no outcome input, no ACK input.** Canon says "reuse it as the reward." Building WO-094 §D or
  WO-CANON-XXVIII *as written* would therefore ship *"learn from what was said"* while believing it
  obeys D1. **Decision needed:** extend `significance_engine.py` with verified-outcome inputs, or
  define a separate outcome-reward vector. (Builder's lane to implement; the choice is David's.)
- **O-5.2 — three incompatible Significance vectors are live.** ADR/Vol XXVIII **7-dim** (D7 above)
  · Vol V Ch.5 **5-term** · live code **9-dim**. Logged as drift in `FC-2` on 2026-07-27 and never
  reconciled; 29 citations of an unreconciled drift.
- **O-5.3 — the speech carve-out.** D3 forbids learning "speech correctness". Vol XXVIII then
  specifies a **LoRA fine-tune of a local understudy on eLo's own turns**, and **WO-071 (in-context
  correction injection) has already shipped** — both of which improve exactly that. The Volume's own
  guardrail says the understudy "sharpens skill/style ONLY… and remains a FALLBACK brain that still
  passes Executive verification." **David must rule whether style-sharpening under Executive
  verification is a permitted carve-out or a violation.** Until then, treat WO-071 as *shipped under
  review*, not as precedent.
