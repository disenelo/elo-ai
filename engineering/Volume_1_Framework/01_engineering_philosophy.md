# Volume 1 — Engineering Philosophy

---

## Why This Programme Exists

eLo is being built over 12–18 months across desktop, Unity, robot, and mobile embodiments. Without a disciplined build programme, each session risks:

- Adding capabilities before prior ones are validated
- Breaking Phase N behaviour when implementing Phase N+1
- Losing architectural coherence as the system grows
- Accumulating cognitive debt that eventually requires a full rewrite

The Engineering Programme prevents all of that by making the lifecycle identical for every phase. Claude knows exactly how to approach each one. Evidence gates expansion. Freezes are permanent.

---

## The Governing Principle

**Presence comes less from adding more capabilities and more from ensuring the cognitive pipeline accurately tracks what matters in the moment before deciding whether to speak.**

Every phase review asks: does this make eLo more present, or just more capable? Those are different questions. An eLo that speaks less but always accurately is better than one that speaks more and misses the room.

---

## What This Programme Is Not

- Not a feature roadmap (that's the Master Roadmap)
- Not an architecture specification (that's `architecture/`)
- Not a TODO list
- Not a sprint board

This is the engineering discipline that governs *how* the roadmap gets built — the same discipline whether David is building alone, with Claude, or with future contributors.

---

## The One Brain Principle in Practice

Every phase must pass the One Brain test before freeze:

> Does this phase add a second decision-maker?

If yes — reject. Revise until it doesn't.

The test is simple: trace the data flow. Every path must end at the Executive. Any path that ends somewhere else without going through the Executive is a violation.

The Connection Surface is a clean example: it observes, produces an `AttentionSnapshot`, injects into `g_ctx`, and stops. The Executive reads `g_ctx` and decides. The Connection Surface never decides anything.

---

## Silence as a Feature

The most important output of a well-built cognitive system is silence.

If eLo is constantly doing things, producing observations, firing notifications, the pipeline is too eager. A calm, well-tuned system watches most of the time. It speaks when it has something real to say.

Every Phase 2.5 validation tests for this. Constant output is a red flag, not a sign of health.

---

## Evidence Gates Expansion

No phase begins implementation until the prior phase passes Phase 2.5-equivalent validation.

This rule was introduced at Phase 2.5 specifically because Phase 2 grew considerably before being validated. The Connection Surface, AttentionSnapshot, StreamDefinition, ring buffer, multi-signal confidence, session references, vision stream — all of this was designed and built before a single long-session test was run.

Phase 2.5 fixes that. From Phase 3 onward: design → playbook → architecture → **validation of prior phase** → implementation.

---

## Freeze Is Permanent

When a phase is frozen:

- Its architecture does not change
- Its interfaces do not change
- Its documented behaviour is the regression baseline for all future phases
- Bugs can be fixed; behaviour cannot be redesigned

The only exception: a critical regression discovered in a later phase that cannot be fixed without modifying a frozen component. In that case, the Engineering Programme requires:

1. Document the regression (what failed, what was expected)
2. Propose the minimum change to the frozen component
3. Re-run all tests for the frozen phase
4. Update the freeze document with the amendment and date

---

## The 12-Step Lifecycle

This is not a suggestion. Every phase executes all 12 steps in order.

```
01. Architecture Review    — read everything, produce a report, no code
02. Current State Audit    — what exists, what works, what is broken
03. Gap Analysis           — what is missing for this phase
04. Runtime Design         — exact data flow, interfaces, contracts
05. Implementation         — write the code
06. Unit Tests             — isolate and test components
07. Conversation Tests     — talk to eLo, break eLo
08. Stress Tests           — long sessions, edge cases
09. Regression             — run prior phase tests
10. Freeze Decision        — approve / reject / rollback
11. Architecture Update    — update docs to match reality
12. Handover               — what the next phase needs
```

Steps 01–04 must be complete before 05. Steps 06–09 must be complete before 10.

There is no shortcut. The shortcut is what creates cognitive debt.
