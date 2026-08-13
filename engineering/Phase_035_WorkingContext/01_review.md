# Phase 3.5 — Architecture Review

**Phase:** Working Context
**Status:** 📐 ARCHITECTURE PHASE — implementation blocked until Phase 3 FROZEN
**Date:** 2026-07-10
**Decision:** DESIGN APPROVED — implementation pending Phase 3

---

## Phase Objective

Working Context is the mental desk.

Not memory (what happened before). Not attention (what's happening now). What is continuously held as cognitive foreground during active work.

A human mid-project carries these simultaneously, without retrieval:
- Current project
- Current asset
- Current goal
- Current problem
- Current constraint
- Current momentum

eLo should carry the same. When David says "Let's continue." without naming anything, Working Context should already know: Blender, robot rig, walking animation, IK chain, current file, last obstacle, desired outcome.

That's not memory retrieval. That's a working cognitive surface.

---

## The Core Distinction

| System | What It Holds | How It's Populated | Lifespan |
|---|---|---|---|
| Memory | What happened in the past | Journaling, session notes, semantic similarity | Cross-session, decays |
| Attention | What's happening right now | Live stream observations | Seconds to minutes |
| Working Context | What's active on the desk right now | Session start + stream + conversation inference | Session |

Working Context is not persistent between sessions. At session start, it is reconstructed from:
1. Most recent journal entry (what was the last session about?)
2. Attention history (what has eLo been observing since startup?)
3. First few conversation turns (what is David working on today?)

It is then maintained in real time as conversation and observation update it.

---

## Architecture Constants Check

| Constant | Status | Notes |
|---|---|---|
| One Brain | ✅ COMPLIANT | Working Context is a subsystem of the Cognitive Faculty |
| One Executive | ✅ COMPLIANT | Executive reads WorkingContextSnapshot from g_ctx — not modified |
| Faculties Observe | ✅ COMPLIANT | Working Context maintains state; it does not decide |
| FREEZE_V1_LOCK | ✅ COMPLIANT | No frozen files touched |
| Silence is Valid | ✅ COMPLIANT | If Working Context is empty (session just started, no signal yet), it contributes nothing |
| Evidence Gates | ⚠️ GATE | Implementation blocked until Phase 3 FROZEN |

---

## The "Let's Continue." Test

This is the acceptance criterion for Phase 3.5.

Setup: Start a new session. Do not tell eLo what you're working on. Do not open any files yet. Say: "Let's continue."

**Phase 3.5 passes when eLo's response is specific:**
- Names the project
- Names the asset or file
- Names the goal or problem
- References the last obstacle

**Phase 3.5 fails when eLo's response is generic:**
- "Of course, what would you like to work on?"
- "Sure, where were we?"
- Any response that requires David to provide context

---

## What Phase 3.5 Produces

```python
@dataclass
class WorkingContextSnapshot:
    current_project:    str | None    # e.g. "eLo-Planet"
    current_asset:      str | None    # e.g. "robot rig"
    current_goal:       str | None    # e.g. "walking animation IK chain"
    current_problem:    str | None    # e.g. "FK/IK switching not smooth"
    current_constraint: str | None    # e.g. "must export to Unity without leaf bones"
    current_momentum:   str | None    # e.g. "2 hours deep, close to working"
    last_session_date:  str | None    # e.g. "2026-07-10"
    confidence:         float         # how certain Working Context is about its own state
    source:             str           # "journal" | "attention" | "conversation" | "inferred"
```

Injected into g_ctx via str() like AttentionSnapshot. The Executive reads it as ambient context.

---

## How Working Context Is Reconstructed at Session Start

```
Step 1: Read most recent journal entry filename → date + title tokens → project/goal inference
Step 2: Load attention history from last session (if persisted) → recent concept clusters
Step 3: Low-confidence WorkingContextSnapshot assembled from Steps 1+2
Step 4: First 3 conversation turns → update Working Context from explicit user statements
Step 5: By turn 3–5, Working Context should have high enough confidence to inform "Let's continue."
```

The confidence field tracks this. Low confidence = eLo may ask one clarifying question. High confidence = eLo proceeds without asking.

---

## Dependency on Phase 3

Working Context uses the Semantic World Model (Phase 3) to describe its state accurately. Without Phase 3:
- "Current project: eLo-Planet" — generic
- "Current asset: robot rig" — generic

With Phase 3:
- Working Context understands that "robot rig" belongs to the embodiment family, which connects to the walking animation goal
- The description is richer because the semantic relationships are understood

---

## Risks

1. **Inference accuracy** — Reconstructing Working Context from journal + attention may produce wrong inferences. Mitigation: confidence field; low-confidence state produces no claim, just a question.

2. **Session boundary handling** — What happens when David switches from eLo-Planet to Plushies mid-session? Working Context must update gracefully. New project → old context deprecated.

3. **Over-confidence** — If Working Context always claims high confidence, it will make specific but wrong claims. Worse than generic responses. Mitigation: confidence decay if no corroborating signals.

---

## Recommendation

DESIGN APPROVED. Architecture is coherent and fills a genuine gap — Working Context is distinct from Memory and Attention and not served by either alone. Implementation begins after Phase 3 FROZEN.
