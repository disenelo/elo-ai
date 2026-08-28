# DRIFT NOTICE — Routing Architecture
# Filed by: Board / Lead Architect
# Date: 2026-08-28
# Authority: Initiative 02 §11 (Universal eLo Execution Constitution, David L3, 2026-08-27)
# Canonical source: docs/architecture/_intake/SOURCE_2026-08-28_DAVID_L3_canonical_execution_flow.md

---

## §11 DRIFT RECORD

### Original Intent (David L3)

David's canonical execution flow (relayed 2026-08-28, direct L3 input):

```
eLo/INPUT → FACULTIES → ASSEMBLED STATE → EXECUTIVE (DECIDES) → ONE COGNITIVE PLAN → EXECUTION GATE → CAPABILITY → ACTION → CONSEQUENCE → RESULT/NEW STATE → eLo → MEMORY/LEARNING (loop)
```

CAPABILITY is downstream of EXECUTIVE DECIDES + EXECUTION GATE.

Initiative 02 §7 (verbatim): "There must be no permanent: primary model → secondary model → fallback model authority ladder defining eLo."

Initiative 02 §6: Never `DAVID → FACULTY → RESPONSE`. Route must always pass through eLo reconciliation.

### Current Implementation

`runtime/backend_router.py`:
- `_TIER_PROVIDER_ORDER` (line ~89): static dict mapping tier name → [ordered provider list]
  - `_TIER_CONVERSATIONAL`: [ollama, openai, groq, anthropic, mock]
  - `_TIER_REASONING`: [groq, ollama, openai, anthropic, mock]
  - (etc.)
- `_route_by_tier(tier, prompt, ...)` (line ~615): iterates `_TIER_PROVIDER_ORDER[tier]` in order, tries each, returns first that works
- Line ~1131: when `ELO_BACKEND` not set, derives `_derived_tier` from action and calls `_route_by_tier()`
- Wired via WO-BRAIN-AUTHORS

**Result:** The provider priority ladder (`_TIER_PROVIDER_ORDER`) determines which LLM executes — not the Executive's cognitive plan. The provider selection happens as a static structural decision, not as a capability requirement derived from the plan.

### Divergence

| Axis | Intended | Current |
|------|----------|---------|
| Where capability is selected | AFTER Executive decides → Execution Gate → Capability | BEFORE — static tier ladder selects provider during routing, independent of cognitive plan content |
| Who determines provider | Cognitive plan's expressed capability requirement | `_TIER_PROVIDER_ORDER` static priority order |
| Provider authority | Provider serves the plan | Provider order IS the routing authority |
| Model ladder | None — §7 explicitly forbids | Present — Ollama-first/Groq-first depending on tier |

### Likely Cause

WO-BRAIN-AUTHORS implemented provider-tier routing to address latency / reliability concerns (0057). This was a valid engineering objective at the time. The canonical execution flow had not yet been formally specified by David L3. Initiative 02 was issued 2026-08-27 — after WO-BRAIN-AUTHORS. The implementation is not wrong in intent; it is wrong in architecture relative to the canonical flow.

### Affected Systems

- `runtime/backend_router.py` — `_TIER_PROVIDER_ORDER`, `_route_by_tier()`, `_derive_tier()`
- 0057 §3 "wired quicker route" — superseded; the "quicker route" is not a tier ladder
- All LLM provider selection for eLo responses

### Authority Required

David L3. Initiative 02 is a David L3 document. The correction must be ratified by David L3 before any implementation.

### Existing SPEC-WO

None yet. This drift notice is the first formal record.

WO-BRAIN-AUTHORS: the WO that created the tier routing — now flagged as architecturally non-compliant with Initiative 02 §6+§7.

### Proposed Governed Correction

Board/LA recommendation (not yet approved):

**Option A — Capability-requirement field in CognitivePlan**
The Executive's cognitive plan emits a `capability_requirement` field specifying what execution quality is needed (e.g., `{speed: "fast", mode: "generative", context_size: "small"}`). The backend_router selects a provider that satisfies this requirement for this turn, with no static priority ladder.

**Option B — Execution Gate emits provider spec**
The Execution Gate (between ONE COGNITIVE PLAN and CAPABILITY) is a new or extended module that translates the plan into a provider specification. Provider selection is the Gate's responsibility, not the router's. The router is a pure capability executor.

**Option C — Remove tier routing entirely; use single configured provider per environment**
`ELO_BACKEND` is always set per environment (Ollama for local, OpenAI for cloud). No fallback ladder. The Executive's plan runs on whatever is configured. Simplest; removes the ladder entirely.

**Board/LA assessment:** Option C is the most Initiative-02-aligned — it removes the ladder, makes capability selection an environment configuration, and lets the Executive focus on the plan. Option A is the most flexible long-term. Both require David L3 ratification.

### What Must NOT Happen Before Ratification

- DO NOT remove `_TIER_PROVIDER_ORDER` without David L3 ruling
- DO NOT modify `executive.py` (FREEZE_V1_LOCK)
- DO NOT add compensation code to mask the divergence
- DO NOT issue a Builder WO to implement the correction without ratification

### What Happens Next

1. This notice filed — DONE
2. Added to board_state.json `needs_david` — DONE
3. Added to programme_integrity_flags — DONE
4. DISPATCH_BOARD.md updated — DONE
5. David L3 reviews and ratifies Option A, B, or C (or provides new direction)
6. Board/LA issues correction WO
7. Builder implements
8. Board/LA verifies: executive.py untouched, no tier ladder, FREEZE_V1_LOCK clean

---

*Board / Lead Architect · 2026-08-28*
