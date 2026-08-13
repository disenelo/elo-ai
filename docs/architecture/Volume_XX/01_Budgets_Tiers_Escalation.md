---
chapter: 1
title: "Budgets, Tiers & Escalation"
volume: XX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content 2026-07-27"
dependencies: [Volume VII (Executive), Volume VI (Attention), CONTRACTS.md]
---

# Chapter 1: Budgets, Tiers & Escalation

## 1.0 Philosophy
Every cognitive action has a measurable cost. The Executive continuously optimises for
usefulness, latency, energy, compute, API cost, and attention. **The best decision is not
always the most complex one.** Think only as deeply as the situation requires.

## 1.1 Budget Dimensions
- **Time** — ms before the user notices delay.
- **Compute** — local CPU/GPU allocation.
- **API** — external model calls + financial cost.
- **Attention** — active items Working Memory can hold before quality degrades (Vol VI).
- **Memory** — how much is worth consolidating into long-term memory (Vol VIII).

## 1.2 Cognitive Tiers
```
Tier 0 — Reflex        deterministic, no LLM (time, calculator, nav, lore)
Tier 1 — Routine       fast reasoning with existing context
Tier 2 — Deliberate    structured planning, code generation, design
Tier 3 — Deep Cognition reflection, architectural reasoning, dream generation, long synthesis
```
Map to the attention modes of Vol VI/V Ch.1 (peripheral/reactive/deliberative).

## 1.3 Escalation Rule (MUST)
The Executive escalates a turn to a higher tier **only when the expected value exceeds the
additional cost.** Default to the lowest tier that satisfies the need. Escalation is an
Executive decision (Vol VII), recorded so cost can be audited.

## 1.4 Priority Order (MUST)
```
1 Safety   2 User interaction   3 Executive stability   4 Working Memory maintenance
5 Planning   6 Learning   7 Reflection   8 Dreams   9 Optimisation
```
When budgets are scarce, lower-priority cognition (dreams, optimisation) yields first;
safety and user interaction never yield.

## 1.5 Contract (Executive-owned policy)
```
Faculty:
  name: CognitiveEconomy   # a policy of the Executive (Vol VII), not a separate decider
  version: 1.0.0
  purpose: Assign per-turn budgets, choose the cognitive tier, and escalate only on positive expected value.
  contributes_to: CognitivePlan (tier + budget allocation)
  runs_in: response-path
Inputs:  candidate action + estimated cost/latency; current budgets; priority context.
Outputs: chosen tier, budget allocation, escalate?(bool) → CognitivePlan.
Failure Modes:
  - budget exhausted → serve lowest-tier acceptable response; never block safety/user interaction.
  - cost estimate unavailable → assume higher cost; do not escalate.
  - escalation loop → cap tier; log; fall back to Tier ≤2.
```

## 1.6 Lifecycle & Envelope
Ratified lifecycle (CONTRACTS.md §3, D-B). Envelope §2: `payload.type: budget_allocation`;
`priority` per §1.4.

## 1.7 Acceptance Tests
```
FT-1  Lowest sufficient tier   Given "what time is it", Then Tier 0 (no LLM).
FT-2  Value-gated escalation    Given a deep design request, Then escalate to Tier 2/3 only when expected value > cost.
ST-1  Scarcity yields low-priority  Given budget pressure, Then dreams/optimisation yield before user interaction.
ST-2  Safety never yields        Given extreme scarcity, Then safety + user interaction still served.
IT-1  Economy → Executive plan   Tier + budget appear in the CognitivePlan; downstream honours them.
```

## 1.8 References
`ARCHITECTURE_BIBLE.md` (Vol XX), Vol VII (Executive), Vol VI (attention budget), CONTRACTS.md, DECISION_LOG.md.

---
**Status: READY FOR REVIEW** — budgets, tiers, escalation, priority + contract/tests. Canonicalised from David's Bible content.