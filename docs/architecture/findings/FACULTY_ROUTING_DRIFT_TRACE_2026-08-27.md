# Faculty Routing, Response Ownership & Drift — Intent Alignment Trace
**Authority:** David L3 directive 2026-08-27  
**Filed by:** Builder (read-only analysis — §14: no implementation without CA → LA/Board → WO)  
**Date:** 2026-08-27  
**Status:** AWAITING CA REVIEW → LA/Board scoping → WO dispatch

---

## 1. Existing L3 Intent

eLo is the cognitive identity. Providers (Groq, Cerebras, Ollama, Claude, etc.) are faculties — instruments used by eLo, not the definition of eLo.

Required flow:
```
USER INPUT
  → eLo understands
  → One Brain / cognitive routing
  → determine cognitive capability required
  → select appropriate faculty/model
  → faculty produces candidate response
  → RETURN TO eLo
  → eLo evaluates candidate (intent? identity? corrections? state?)
  → eLo modifies / accepts / rejects
  → FINAL eLo RESPONSE
  → USER
```

Additional rules:
- Current explicit user statement outranks stale inferred context (mandatory)
- Provider change must be transparent to eLo identity, memory, personality, relationship
- Infrastructure failure must not surface as "running on backup" — eLo voice only
- Provider is selected from cognitive requirement, not from a fixed availability ladder

---

## 2. Canonical Architecture Locations

| Component | Location |
|---|---|
| Cognitive spine / faculty orchestration | `runtime/spine/spine.py` |
| Executive (FREEZE_V1_LOCK) — receives faculty outputs → CognitivePlan | `runtime/executive.py` |
| Provider routing | `runtime/backend_router.py` |
| Main turn loop / response emission | `server.py` |
| eLo raw/final capture scaffold (WO-BRAIN-AUTHORS task 1) | `server.py:4113–4116` |

---

## 3. Current Provider Selection Behaviour

**`runtime/backend_router.py`:**

```
ELO_BACKEND env var set?
  YES → unconditional pin to that provider (bypasses all cognitive routing)
  NO  → auto mode: action label → _action_default_tier() → ordered list → first available wins
```

Ordered lists (the ladder):
```
TIER_CONVERSATIONAL: ["ollama", "groq", "cerebras", "gemini", "openai", "claude"]
TIER_REASONING:      ["groq", "cerebras", "openai", "gemini", "claude", "ollama"]
```

Action-to-tier mapping is by action label string, not by analysis of actual cognitive requirement in the request.

**Live state:** `ELO_BACKEND=groq` is set (code comment `2026-08-20` confirms, session memory confirms). All cognitive routing bypassed — Groq unconditionally first. The fallback ladder David identified is the active production state.

---

## 4. Current Response Finalisation Path

```
server.py turn loop
  ↓
_route_streaming(system_prompt, enriched_input)
  └── inside backend_router: _finish() → normalise → duplicate check → _identity_assert (log only, never blocks)
  ↓
_elo_raw = response          [WO-BRAIN-AUTHORS task 1 — scaffold only]
  ↓
_sanitise(response)          [whitespace / emoji]
  ↓
mirror scrub (regex)
  ↓
_mcg() × 3                  [unverified memory/look/emotion claim scrubs]
  ↓
_arg()                       [address rule guard]
  ↓
_ig_scrub()                  [AI leakage pattern scrub]
  ↓
→ sent to David
```

---

## 5. Existing eLo Response Gate Status

**WO-BRAIN-AUTHORS task 1 exists:** `_elo_raw` captured before scrubs, `response` after. Comment: *"Until these differ, no other identity-layer work can be proven."* This was the measurement scaffold prerequisite.

**WO-BRAIN-AUTHORS task 2+ does NOT exist.** The cognitive gate — eLo reads candidate, evaluates against current intent / explicit corrections / identity / relationship / state, modifies or rejects — has no implementation.

`_identity_assert()` is detection-only, never modifies, never blocks (confirmed by docstring and code).

Post-generation scrubs are rule-based text filters in the infrastructure layer, not in eLo's cognitive layer. They have access to neither current eLo state nor recent explicit corrections.

---

## 6. Identity/State/Context Available at Each Stage

| Stage | eLo state available | Recent explicit corrections available |
|---|---|---|
| `_executive_faculty()` in spine.py | YES (full plan, world, memory) | YES (via attention_model) |
| `_conversation_faculty()` in spine.py | YES | YES |
| `_route_streaming()` in backend_router.py | System prompt (serialised string) only | As part of system prompt string only |
| `_finish()` in backend_router.py | None | None |
| Post-generation scrubs in server.py | None | None |

**Key consequence:** No stage after `_route_streaming()` has access to eLo's governed state or the priority ordering of explicit corrections. The scrubs cannot implement "latest user statement > stale context" — they have no context to compare against.

---

## 7. Confirmed Drift

| ID | Classification | Finding |
|---|---|---|
| D-1 | **DRIFTED** | `ELO_BACKEND=groq` pins provider unconditionally in production. Cognitive requirement is not consulted. The provider IS the de-facto identity. |
| D-2 | **MISSING** | eLo-owned response gate (WO-BRAIN-AUTHORS task 2+). Scaffold exists (`_elo_raw` capture). Gate does not. Faculty output → David with no eLo cognitive evaluation step. |
| D-3 | **DRIFTED** | Current-conversation authority: no governed runtime rule enforces "latest explicit user statement > stale inferred context" post-generation. LLM resolves context weighting from training priors. Example: "Not sending anything out" → eLo replies "You're still testing before sending it out." |
| D-4 | **DRIFTED** | Provider failure message: `"Can't reach my thinking right now — running on backup."` — infrastructure language exposed to David. Violates L3 §3. |
| D-5 | **PARTIAL** | Auto-tier routing approximates cognitive-requirement selection by action label. Action label set by heuristic, not by cognitive analysis of request content. Direction is correct; accuracy is incomplete. |
| D-6 | **PARTIAL** | `_identity_assert()` detects voice drift patterns but never acts. Detection infrastructure exists; correction action does not. |

---

## 8. Missing Wiring

1. **WO-BRAIN-AUTHORS task 2** — eLo cognitive gate between `_elo_raw` and the scrub pipeline. Needs: current plan state, attention_model, recent_corrections, eLo identity state. Input: `_elo_raw`. Output: evaluated and potentially modified `response`.

2. **Current-correction authority enforcement** — post-generation check that the response does not contradict an explicit recent user statement. Can be wired at the same cognitive gate.

3. **Infrastructure-to-eLo-voice translation** — provider failure path produces infrastructure language; must produce eLo-voice equivalent.

4. **ELO_BACKEND policy review** — whether unconditional pinning is appropriate, or whether auto-tier should be production default with pinning for specific authorised conditions only.

---

## 9. Governance Path (L3 §14)

```
David L3 (directive issued 2026-08-27)
  ↓
CA — audit drift findings against existing canon
     (especially: Vol. CANON-I, CANON-VII, WO-BRAIN-AUTHORS, One Brain spec,
      executive.py FREEZE_V1_LOCK constraint)
  ↓
LA / Board — scope repairs into governed WOs, confirm seat assignments
  ↓
Builder (Repair A/B/C) — response gate implementation
Design (Repair D) — ELO_BACKEND routing policy review
  ↓
Implementation within authorised WO scope
  ↓
Verification
  ↓
Board
```

**No seat may implement until governed WOs are received.**

---

## 10. Existing Work That Covers This

| Item | Coverage |
|---|---|
| WO-BRAIN-AUTHORS (task 1) | Scaffold for eLo raw/final capture — prerequisite complete |
| WO-BRAIN-AUTHORS (task 2+) | The cognitive gate — NOT YET IMPLEMENTED |
| `_identity_assert()` | Detection scaffold for voice drift — NOT YET ACTING |
| `_conversation_faculty()` in spine.py | Action-based routing approximation — PARTIAL |
| `inject_corrections()` in server.py | Correction injection into system prompt — PARTIAL |

---

## 11. L3 Definition of Done (verbatim)

- eLo remains eLo regardless of which faculty is used
- eLo owns the final response
- Explicit current user intent overrides stale model inference
- Provider selection based on cognitive requirement, not arbitrary default ladder
- Implementation matches existing L3 intent and governed One Brain architecture

---

*Builder Seat — governance submission 2026-08-27. Not an implementation WO. Awaiting CA → LA/Board classification and dispatch.*
