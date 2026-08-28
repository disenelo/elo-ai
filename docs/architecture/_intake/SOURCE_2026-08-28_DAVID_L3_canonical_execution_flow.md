# VERBATIM — primary source, do not summarise
# SOURCE: CANONICAL eLo EXECUTION FLOW DIAGRAM
# Authored by: David L3 (David Charles)
# Relayed by: David Charles (direct L3 input)
# Captured by: Board / Lead Architect 2026-08-28
# Provenance: Direct L3 session directive — response to "eLo → Faculty → David Response or default faculty" routing critique

---

## THE CANONICAL FLOW

```
┌──────────────────────┐
│       eLo / INPUT    │
└──────────┬───────────┘
           ↓
┌─────────────────────────┐
│       FACULTIES          │
│                         │
│ Language                │
│ Meaning                 │
│ Memory                  │
│ Attention               │
│ Relationship            │
│ Significance            │
│ Emotion                 │
│ Intent                  │
│ Creativity              │
│ Personality             │
│ Curiosity               │
│ Agency                  │
│ etc.                    │
└───────────┬─────────────┘
            ↓
┌──────────────────────┐
│   ASSEMBLED STATE    │
│                      │
│ What is happening?   │
│ What matters?        │
│ What do I know?      │
│ What do I want?      │
│ What can I do?       │
└──────────┬───────────┘
           ↓
     ┌───────────┐
     │ EXECUTIVE │
     │           │
     │ DECIDES   │
     └─────┬─────┘
           ↓
  ONE COGNITIVE PLAN
           ↓
   EXECUTION GATE
           ↓
     CAPABILITY
           ↓
       ACTION
           ↓
     CONSEQUENCE
           ↓
  RESULT / NEW STATE
           ↓
        eLo
           ↓
  MEMORY / LEARNING
           ↺
```

---

## WHAT THIS MEANS

1. **FACULTIES** are all pre-Executive. They contribute to the assembled state. They do not generate responses. They do not route to providers. They are not alternate eLos.

2. **ASSEMBLED STATE** is the aggregated input to the Executive — everything the faculties have processed. This is what the Executive reads. Not the raw input.

3. **EXECUTIVE** is the single decision authority. It produces ONE COGNITIVE PLAN. Nothing downstream of this modifies the decision.

4. **CAPABILITY** sits below the Execution Gate. The language model (LLM, Ollama, Groq, OpenAI, etc.) is a CAPABILITY — a tool that executes the decided plan. It does not decide. It does not determine eLo's routing. It does not determine eLo's identity. Its provider order is not a governance authority.

5. **THE LOOP:** Result / New State feeds back to eLo → Memory / Learning → next turn. This is how eLo grows, not through model-switching.

---

## WHAT THIS SUPERSEDES

- 0057 §3 "quicker route": The tier-based routing (`_TIER_PROVIDER_ORDER`, WO-BRAIN-AUTHORS) creates a permanent primary→secondary→fallback model ladder. This violates Initiative 02 §7: "There must be no permanent: primary model → secondary model → fallback model authority ladder defining eLo." The tier routing makes the PROVIDER ORDER a routing authority, not the Executive's cognitive plan. **0057 is superseded by this canonical flow.**

- Any implementation where the backend_router selects a provider BEFORE or IN PLACE OF the Executive's cognitive plan determining what capability is needed.

- Any implementation where a faculty generates a candidate response that reaches David directly (Initiative 02 §8).

---

## DRIFT NOTICE — filed 2026-08-28

**Current implementation diverges from this flow at CAPABILITY:**

The backend_router's `_route_by_tier()` (backend_router.py:615, called at line ~1131) selects providers in a static priority order (`_TIER_PROVIDER_ORDER`). This means the tier ladder — not the Executive's ONE COGNITIVE PLAN — determines which provider executes. The plan currently emits a tier (`_TIER_CONVERSATIONAL` etc.) that then feeds a static provider priority order. This creates a model authority ladder (§7 violation).

**Correct:** The Executive's cognitive plan specifies the capability requirement. The capability layer selects the provider that satisfies that requirement for this turn. The provider serves the plan — it does not define the routing order.

**What needs governing before any fix:**
- Board/LA to spec the capability selection mechanism: how does the cognitive plan express its capability requirement to the capability layer?
- WO to replace `_route_by_tier()` with plan-driven capability selection
- Authority: David L3 (existing — this flow IS the L3 directive)

---

*Board / Lead Architect · 2026-08-28*
