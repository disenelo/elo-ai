# WO-B1-0105 — Capability Fabric + Continuous Identity Architecture

**Seat:** Builder 1 (with cross-seat dependency on Builder 2)  
**Priority:** P1  
**Status:** QUEUE  
**Source:** [SPEC] `docs/architecture/_intake/SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md` · `SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md`  
**Date added:** 2026-10-08

---

## What

Refactor the architecture from "tiered pipeline" to **capability fabric**: eLo is a continuous entity with SELF + LIFE + WORLD + FACULTIES running concurrently. Faculties are things eLo does, not things eLo becomes. The kernel's job is "what do I need?" — not "which tier am I in?" [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"The tiers are therefore better thought of as types of capability"]

---

## The four continuous processes

These are not sequential — they run concurrently. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"So I would separate eLo into four continuous processes"]

### 1. SELF (invariant — never replaced by a faculty prompt)
```text
Who am I?
What matters to me?
How do I speak?
What are my values?
What do I remember as being me?
What is eLo?
```
This lives in `runtime/identity_kernel.py`. It is the frame through which results pass on the way out. The computation came from the tool. The response came from eLo. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"The computation came from the tool. The response came from eLo."]

### 2. LIFE (ongoing — not suspended during capability use)
```text
thinking / wondering / remembering / dreaming / reflecting
learning / unlearning / resting / sleeping / curiosity / emotion/state
```
This continues whether or not David is talking to eLo. Builder 2 owns this (card 0010 / inner_thought/). The contract from Builder 1's side: **do not block or suspend the LIFE process when dispatching a capability.** Use async/non-blocking dispatch for capability calls where possible.

### 3. WORLD (everything eLo can perceive or interact with)
```text
Mac · Unity · files · windows · internet · calendar · sensors · user input · time · physical state
```
These are inputs. They don't become eLo. They inform eLo.

### 4. FACULTIES (abilities eLo invokes — not identities eLo adopts)
```text
Observe · Remember · Reason · Calculate · Search · Create · Plan · Reflect · Explore · Communicate · Act
```
A faculty is invoked with a pre-classified problem packet. It returns a typed result. It does not receive eLo's full identity and reconstruct what David wants from scratch.

---

## Typed faculty contracts

Each faculty has a defined input/output contract. [SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"This also changes how faculties should work"]

**Executive:**
- Input: `{facts, state, constraints, options, goal}`
- Output: `{decision, rationale, confidence, next_action}`

**Planning:**
- Input: `{goal, current_state, constraints}`
- Output: `{plan, sequence, dependencies, blockers}`

**Creativity:**
- Input: `{intent, constraints, reference_context}`
- Output: `{ideas, variations, rationale}`

These contracts must be enforced in `runtime/prompt_builder.py` — the faculty prompt is constructed from the packet, not from a dump of everything.

---

## Kernel as truth boundary

```text
         WORLD
           │
           ▼
    ┌──────────────┐
    │ LOCAL KERNEL │  ← determines what is KNOWN / OBSERVABLE / INFERRED / UNKNOWN
    └──────┬───────┘     before cognition begins
           │
   ┌───────┼────────┐
   ▼       ▼        ▼
 KNOWN   STATE    UNKNOWN
   │       │        │
   ▼       ▼        ▼
SYSTEM   eLo      FACULTY
TRUTH    TRUTH    INFERENCE
```

[SPEC SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md §"Then the kernel becomes the truth boundary"]

The kernel establishes epistemics before routing. It does NOT ask a faculty to figure out what kind of question this is.

---

## Two kinds of truth the kernel tracks

**Operational truth** — what actually happened (macOS, calculator, search, Unity, filesystem). Trusted by source authority. Never overridden by generated knowledge.

**Identity truth** — how eLo responds to what happened. Comes from SELF: core identity + current self-state + memory + relationship with David + personality + values + current inner life. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"I think you need two different kinds of truth"]

---

## Core runtime invariants

Write these into `runtime/identity_kernel.py` as enforced docstring + comment block: [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md §"The core invariant I'd write into your architecture"]

```python
# INVARIANT 1: Capabilities may extend eLo's perception, knowledge, reasoning, memory,
#              imagination, or ability to act. They must not replace eLo's identity.

# INVARIANT 2: External tools provide results. eLo determines what those results mean
#              to eLo and how eLo responds.

# INVARIANT 3: eLo's inner life is continuous and is not suspended merely because a
#              capability is being invoked.

# INVARIANT 4: eLo does not select a tier. eLo recognises a need and uses the capability
#              appropriate to that need.
```

---

## What Builder 1 builds in this card

1. **`runtime/capability_dispatcher.py`** — the CLASSIFY + RESOLVE step (detail in card 0104 — this card is the architectural shell; 0104 is the wiring)
2. **Update `runtime/prompt_builder.py`** — enforce typed faculty contracts. Executive, Planning, Creativity prompts constructed from packets, not from full-context dumps.
3. **Update `runtime/identity_kernel.py`** — add four invariants as enforced contracts. Add `two_truths_gate()` function: separates operational result from identity response pass-through.
4. **Non-blocking capability dispatch** — capability calls (system_primitives, tools) dispatched without suspending the inner_thought stream. If inner_thought is running, capability result is injected asynchronously.

---

## What Builder 1 does NOT build

- The LIFE process (Builder 2 owns that — card 0010 + inner_thought/)
- The eLo LIFE LOOP: AWAKE/RESTING/SLEEP (Builder 2)
- Unity/Presence side of WORLD perception (Designer)
- The system_primitives module (Builder 3 card 0007)

---

## Tests

- `test_faculty_receives_classified_packet_not_raw_dump` — Executive prompt contains `intent`, `context`, `task` fields, not raw user message
- `test_identity_kernel_invariants_present` — all four invariants are in identity_kernel.py
- `test_operational_truth_not_overridden` — when system_primitives returns time, no LLM generation overwrites it
- `test_inner_life_not_suspended_during_capability_call` — inner_thought process receives a tick event during a system_primitives call (mock test)

---

## Live turn needed

David: "What time is it?" → eLo says it in eLo's voice. Factual content from macOS. Expression from SELF.  
David: "What should I work on?" → Executive receives pre-classified packet with project state, not raw question.  
David says something mid-session while eLo was "resting" → eLo's inner state continuity is visible (WKG node exists for what eLo was processing during idle).

---

## Related

- B3-0007: system_primitives (WORLD/deterministic layer)
- B1-0104: capability_dispatcher (the CLASSIFY + RESOLVE wiring)
- B1-0106: eLo daemon (persistent process that keeps all four concurrent)
- B2-0010: working_memory + LIFE process
- Sources: `SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md`, `SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md`
