# Architecture Standards — eLo OS

**Status:** ACTIVE
**Authority:** Lead Systems Architect

---

## The One Brain Principle

The most important architectural rule in eLo OS:

> **The Executive Faculty is the sole decision-maker. Every other component observes, computes, or contributes information. Nothing else decides.**

A component violates the One Brain Principle if it:
- Selects a response without going through the Executive
- Chooses which action to take based on its own internal state
- Produces output directly to the user without Executive approval
- Short-circuits the spine to deliver a reply

The only permitted exceptions are pre-spine interceptors (farewell pool, anim commands, scale commands) that exist precisely because they need to bypass the LLM for speed — and each one is explicitly documented, has a fixed pool it draws from, and does not decide based on internal state.

---

## Faculty Roles

| Faculty | Role | May Decide? |
|---|---|---|
| Language Faculty | Classify intent, detect register, detect meaning | No |
| Memory Faculty | Retrieve and rank relevant memories | No |
| Attention Faculty | Score intent, valence, momentum | No |
| Relationship Faculty | Provide relational context | No |
| Capability Faculty | List available tools, health status | No |
| Connection Surface | Observe session patterns, produce snapshot | No |
| Executive Faculty | Read all faculty outputs. Produce one decision. | YES — only this |
| Spine | Assemble the plan from faculty outputs | No — assembles, does not decide |
| Embodiment (Desktop, Unity, Robot) | Execute the decision | No — executes, does not interpret |

---

## System Invariants

These never change. Any architecture proposal that violates one is rejected.

1. **One Brain.** Single cognitive process. Same executive across all embodiments.
2. **One Executive.** `runtime/executive.py` is the sole decision-maker. FREEZE_V1_LOCK.
3. **Silence is valid.** No faculty is required to produce output. Empty = nothing happens.
4. **Faculties observe. Executive decides. Embodiment executes.**
5. **Evidence before expansion.** No work package begins implementation without prior validation passing.
6. **Freeze is permanent.** Frozen behaviour is the regression baseline. It does not change.
7. **FREEZE_V1_LOCK.** `runtime/executive.py` and `prompts/` are never modified.

---

## Interface Contracts

Every new component must document:

**Input:** exact schema, types, optionality
**Output:** exact schema, types, optionality
**Invariants:**
- The component never decides
- Empty input → empty output (no fallback unless specified)
- Never raises — all failures are silent and logged
- Never writes to the user directly

---

## Routing Principle

> **Routing exists to understand, not to restrict.**

The routing pipeline classifies input so the right faculty can respond correctly. It does not restrict what the user can say. It does not apply editorial judgement. A routing failure (wrong classification) degrades gracefully — the Executive receives less context but still decides.

---

## Embodiment Principle

> **Embodiment follows cognition.**

The Desktop Avatar, Unity Avatar, and Robot are all output surfaces for the same brain. None of them contain their own decision logic. They read state from `blender_state.json` and execute. If a new surface is added, it reads state — it does not add a new cognitive layer.

---

## Extension Principle

> **Prefer extending existing faculties over creating new ones.**

Before proposing a new faculty, ask: can this be a new signal added to an existing faculty's output? If yes, do that. New faculties add coordination complexity. New signals add data only.

---

## Architecture Document Standards

Every architecture document (`docs/architecture/NN_name.md`) must contain:

1. **Purpose** — one sentence
2. **Role in the One Brain** — what does this component observe, report, or execute?
3. **Interface** — exact input/output schema
4. **Runtime Flow** — how data flows through this component to the Executive
5. **Invariants** — what must always be true
6. **What This Component Does Not Do** — explicit scope limit
7. **Interaction Map** — how it interacts with every other faculty
8. **Known Limitations** — honest about what is missing
9. **Freeze Status** — FROZEN / ACTIVE / PLANNED
