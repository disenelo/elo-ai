---
chapter: 2
title: "The Provider Chain — Tiers Made Real"
volume: XX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
source: "runtime/backend_router.py (live) + Chapter 1 (abstract tiers) + CLAUDE.md standing facts"
dependencies:
  - Volume_XX/01_Budgets_Tiers_Escalation.md (the abstract tier + escalation policy this grounds)
  - Volume VII (Executive — chooses tier, owns escalation)
  - Volume XV Ch.2 (World State — internet/environment domains gate provider reachability)
  - runtime/backend_router.py (the live routing layer)
---

# Chapter 2: The Provider Chain — Tiers Made Real

## 2.0 Purpose

Chapter 1 defines the *abstract* economy: cognitive tiers 0–3, budget dimensions, a
value-gated escalation rule, a priority order. This chapter grounds that policy in the
**one place cost is actually spent today** — `runtime/backend_router.py`, the layer that
chooses which reasoning engine answers a turn and how many tokens it may burn.

Two facts must be held together honestly:

1. The router is the **real, running** cost surface. Provider preference, token budgets,
   quota cooldowns, and the local floor all exist in code today.
2. The router does **not yet** implement Chapter 1's cognitive-tier model or its
   expected-value escalation gate. It selects a *provider* by availability and mode; it
   does not select a *cognitive depth* by expected value. That mapping is the work this
   chapter specifies as PENDING.

Naming this gap is the point. We do not claim the economy is implemented because a router
exists (Governance: *canon before implementation*).

## 2.1 What exists today (grounded, verified in code)

`route(system_prompt, user_input, mode, max_sentences, action)` returns
`(response_text, backend_name)`. The live cost levers are:

**2.1.1 Provider preference by mode.** `ELO_BACKEND` selects one of five modes
(`backend_router.py` module docstring + `route()`):

```
auto   (default) : OpenAI → Gemini → Claude → Groq → Cerebras → Ollama → Mock
groq   (pinned)  : Groq → Cerebras → Ollama → Mock          (WO-032 voice-consistent; skips
                   OpenAI/Gemini/Claude entirely to avoid voice drift)
cloud            : OpenAI → Gemini → Claude → Groq → Cerebras → Mock   (no local)
local            : Ollama → Mock
mock             : Mock only (testing)
```

If no `ELO_BACKEND` is set **and** no cloud key is present, `route()` forces `local`
(offline immediately). This is the offline default, not a silent cloud attempt.

**2.1.2 Token budget by action** — the one cost lever that already keys off cognitive
weight. `_token_budget(action)`:

```
build · challenge · reflect · plan · deep · diagnose  → 600 tokens   (heavier cognition)
celebrate · connect · ground · navigate · witness · silence · answer · ""  → 280 tokens
```

This is a real, primitive form of Chapter 1's tiering: heavier CAL actions are already
granted more compute. It keys off the **action**, not off an expected-value estimate.

**2.1.3 Quota handling** (cost-protection that already runs):
- `_groq_quota_cooldown_until` — a Groq HTTP 429 opens a **60-second** cooldown
  (`time.monotonic() + 60.0`) that routes past Groq to Cerebras/Ollama, then self-clears.
  One transient rate-limit never pins the session to mock (WO-032b).
- `_openai_quota_exceeded` — a **session-level** flag; first OpenAI 429 skips OpenAI for
  the rest of the session and marks the reasoning faculty degraded (WO-042).

**2.1.4 The local floor** (WO-073). In `groq` and `auto` modes, before mock, the router
tries `_ollama_available()` — true only when Ollama is up *and* a model is installed.
Ollama (David's `llama3.1:8b`, set via `ELO_OLLAMA_MODEL`) is the **cheap always-on
floor**: a local brain answers rather than dropping to the canned mock whenever the paid
tiers are unreachable. This is the economic heart — the floor costs nothing per call.

**2.1.5 Model overrides.** `_detect_model_override()` lets the user pin one engine for a
turn ("ask claude", "use gemini", "fast answer" → groq). The Executive still owns the
turn; only the reasoning engine changes.

**2.1.6 Faculty health integration** (WO-042). Exhaustion/recovery is reported to
`runtime.faculty_health` (`mark_degraded("reasoning", …)` / `mark_recovered("reasoning")`),
so the rest of the system can *see* when reasoning has fallen to a degraded tier — the hook
Chapter 3 depends on for honest degradation.

## 2.2 Tier → provider mapping (the model, PENDING)

Chapter 1's tiers describe **cognitive depth** (how hard eLo thinks). The router chooses a
**provider** (where thinking runs). They are different axes; today only the second is
implemented. This section specifies the intended bridge so the Architecture Agent can build
it without inventing the mapping.

```
Tier 0 — Reflex        no LLM at all. Deterministic paths: time, calculator, nav, lore,
                       greeting pool. Cost = 0 API, 0 cloud. MUST never reach route().
Tier 1 — Routine       cheapest capable reasoning engine. Preferred target: local Ollama
                       floor, or the fastest cloud engine (Groq/Cerebras/gpt-4o-mini) at
                       the 280-token budget.
Tier 2 — Deliberate    a capable cloud engine at the 600-token budget (build/plan/design).
Tier 3 — Deep Cognition the strongest available engine, 600-token budget, may run off the
                       response path (reflection, dream synthesis, long planning).
```

**Mapping rules (MUST, when built):**

- **M-1** Tier 0 is served *before* `route()` is ever called. If a turn reaches the router,
  it is already ≥ Tier 1. (Greetings are already pooled upstream — see the WO-032 note in
  `route()`; the length gates that used to force short turns to mock are *lifted*, because a
  real answer beats a canned one.)
- **M-2** The Executive supplies the chosen tier to the router (a new `tier` argument beside
  `action`). Absent a tier, the router MUST default to the cheapest capable path — never the
  most expensive by default (Ch.1 §1.3: default to the lowest tier that satisfies).
- **M-3** `_token_budget()` becomes tier-aware, not only action-aware: tier is the primary
  key, action a secondary refinement.
- **M-4** Provider *cost class* is made explicit (free-local / cheap-cloud / premium-cloud)
  so escalation can compare cost against expected value (Ch.1 §1.3) rather than blindly
  walking the availability chain.

**Gap (PENDING, flag for CA/David):** there is no cost telemetry, no per-turn budget
accounting, and no expected-value estimate in the router today. `_AUTO_LOCAL_MAX_CHARS = 80`
exists as a declared local/cloud split threshold but is **not referenced** in `route()` — a
dormant lever, not a live one. The escalation *decision* (Ch.1 §1.3) has no home in code yet.
Whether it lives in the Executive (Vol VII) or as a pre-router policy is an open design
question below (OQ-1).

## 2.3 Value-gated escalation, concretely

Chapter 1 §1.3: escalate only when expected value exceeds additional cost. Grounded against
the chain:

- The **floor** (Ollama) and **mock** cost ~nothing. Cloud tiers cost money and latency.
- Escalation to a paid tier MUST be justified by the turn's expected value — a factual
  one-liner ("what time is it") is Tier 0 and never escalates; a design/plan/reflect turn
  may justify Tier 2/3.
- David is **cost-sensitive** (CLAUDE.md standing fact). The default posture is therefore:
  **prefer the floor; escalate on demonstrated need, not by default.** The pinned-`groq`
  chain and the Ollama floor already encode a cheap-first bias; the missing piece is the
  *gate* that decides when a turn earns a premium engine.
- Every escalation MUST be recorded so cost can be audited (Ch.1 §1.3). Today the only
  audit trail is `backend_name` in the return tuple and the WO-042 health marks; a
  cost/escalation log is PENDING.

## 2.4 Faculty Contract

```
Faculty:
  name:            CognitiveEconomy.ProviderRouting   # a policy surface of the Executive
                                                       # (Vol VII), realised in backend_router.py
  version:         1.0.0
  purpose:         Given a turn's chosen cognitive tier and action, select the cheapest
                   capable reasoning engine from the mode-appropriate provider chain,
                   allocate a token budget, honour quota state, and fall to the local floor
                   before mock — spending premium compute only on positive expected value.
  contributes_to: CognitivePlan (provider + token budget), and the response text itself
  runs_in:        response-path (route / route_streaming)

Inputs:
  - type: routing_request
    fields: system_prompt, user_input, mode(ELO_BACKEND), action, tier(PENDING),
            max_sentences
    required: true
  - type: environment
    source: os.environ (provider keys), Ollama /api/tags, World State internet domain (Vol XV)
    required: false   # absence degrades the chain, never blocks the turn
  - type: quota_state
    source: _groq_quota_cooldown_until, _openai_quota_exceeded, faculty_health
    required: false

Outputs:
  - type: routed_response
    body: (response_text, backend_name[, first_token_ms])
    destination: Executive → output surfaces
    note: backend_name is the honesty channel — it names the actual engine used
          (e.g. "ollama", "mock"), never masks a downgrade (Ch.3).

Dependencies:
  - faculty: Executive (hard — owns tier choice + escalation authority, Vol VII)
  - faculty: FacultyHealth (soft — WO-042; receives degraded/recovered marks)
  - World State internet/environment domains (soft — reachability context, Vol XV)

Failure Modes:
  - condition: a provider errors / times out
    fallback: log, try next in the mode chain (never surface a stack trace as speech)
  - condition: Groq 429
    fallback: 60 s cooldown → Cerebras → Ollama; self-clears (WO-032b)
  - condition: OpenAI 429
    fallback: session skip + mark reasoning degraded (WO-042); continue down chain
  - condition: all paid tiers unreachable
    fallback: Ollama local floor (WO-073) — a real, cheap answer
  - condition: floor unreachable too
    fallback: mock — and the downgrade MUST be visible (backend_name="mock"), never faked (Ch.3)
  - condition: cost estimate unavailable (PENDING lever)
    fallback: assume higher cost, do NOT escalate (Ch.1 §1.5)
```

## 2.5 Lifecycle

Universal lifecycle (Volume_V/CONTRACTS.md §3). Notes:

```
INITIALISING → read ELO_BACKEND + provider keys; probe Ollama; set mode
ACTIVE       → idle between turns; quota cooldowns tick down out-of-band
PROCESSING   → per turn: pick tier (PENDING) → walk mode chain → allocate token budget →
               return (text, backend_name)
   └─ provider fault ─► ERROR_RECOVERY (that provider only) → next in chain → continue
LEARNING/UPDATING → (integration window) tune token budgets, cooldown durations, cost classes
STABLE → ACTIVE
```

The routing policy has **no personality-affecting learning** — its only `UPDATING` is
tuning budgets/cooldowns/cost classes. It never proposes a personality delta.

## 2.6 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "CognitiveEconomy.ProviderRouting",
  "receiver": "Executive",
  "priority": "normal",              // per Ch.1 §1.4 priority order; user-interaction turns high
  "context": { "significance": 0.0, "memory_instruction": { "store": false, "priority": "" } },
  "payload": {
    "type": "budget_allocation",
    "body": {
      "tier": 0,                     // PENDING — Executive-supplied cognitive tier
      "backend_name": "ollama",      // the engine actually used (honesty channel)
      "token_budget": 280,           // from _token_budget(action)/tier
      "escalated": false,            // true only when a premium tier was chosen over the floor
      "quota_state": { "groq_cooldown": false, "openai_exceeded": false }
    }
  },
  "confidence": 0.0,
  "expires": "<turn_ttl>",
  "trace": ["CognitiveEconomy.ProviderRouting@ts"]
}
```

Binding rules: `payload.type` MUST be `budget_allocation` (Ch.1 §1.6); `backend_name` MUST
name the real engine (Ch.3 honesty); `escalated` MUST be set whenever a paid tier was chosen
over the free floor, so cost is auditable (Ch.1 §1.3).

## 2.7 Acceptance Tests

### Functional

```
FT-1  Mode chains match code
  Given:  ELO_BACKEND=groq, all keys present
  When:   route() runs and Groq is down
  Then:   it tries Cerebras → Ollama → Mock in that order, and NEVER OpenAI/Gemini/Claude.

FT-2  Token budget keys off action
  Given:  action="plan"  vs  action="answer"
  When:   route() allocates a budget
  Then:   plan → 600, answer → 280  (per _token_budget).

FT-3  Local floor before mock
  Given:  no cloud keys reachable, Ollama up with llama3.1:8b installed
  When:   route() runs (auto or groq)
  Then:   backend_name == "ollama", NOT "mock" — a real cheap answer served.

FT-4  Tier 0 never reaches the router  (PENDING)
  Given:  "what time is it"
  When:   the turn is handled
  Then:   a deterministic path answers; route() is not called; 0 API cost.
```

### Stability

```
ST-1  Groq 429 → 60 s cooldown, not session death
  Given:  Groq returns 429
  When:   the next turns run
  Then:   Groq is skipped for ~60 s (Cerebras/Ollama serve), then Groq is retried — the
          session is NOT pinned to mock.

ST-2  OpenAI 429 → session skip + health mark
  Given:  OpenAI returns 429 in auto mode
  When:   subsequent turns run
  Then:   OpenAI is skipped for the session AND faculty_health shows reasoning degraded.

ST-3  Cheap-first default  (PENDING gate)
  Given:  a turn with no supplied tier
  When:   the economy chooses a path
  Then:   it picks the cheapest capable engine, never a premium engine by default.
```

### Integration

```
IT-1  Executive tier → router budget  (PENDING)
  Executive (Vol VII) chooses Tier 2 for a design turn
        ↓ tier
  ProviderRouting allocates 600-token budget on a capable cloud engine, escalated=true
        ↓
  Assert: escalated turns are logged; a Tier-0/1 turn shows escalated=false.

IT-2  Degradation is visible downstream
  Given:  all paid tiers + floor fail → mock
  When:   the response is produced
  Then:   backend_name="mock" propagates; Ch.3's honesty gate can act on it.
```

## 2.8 Open Questions (flag for CA/David)

- **OQ-1** Where does the escalation *gate* live — inside the Executive (Vol VII) as part of
  tier choice, or as a pre-router policy? Chapter 1 §1.5 calls it "a policy of the Executive,
  not a separate decider," which argues for Vol VII. Needs CA ratification.
- **OQ-2** Cost telemetry: do we log per-turn (provider, tokens, escalated, est. $) to a
  cost ledger for audit (Ch.1 §1.3)? What is the retention/privacy posture (ties Vol XXIII)?
- **OQ-3** `_AUTO_LOCAL_MAX_CHARS = 80` is declared but unwired. Retire it, or wire it as the
  Tier-1 "short → local floor" heuristic? (RESERVED-adjacent: touches money via API spend.)
- **OQ-4** Streaming (`route_streaming`, OpenAI-only today) vs the cheap-first bias: streaming
  currently privileges the *premium* engine for first-token latency. Reconcile latency budget
  (Ch.1 §1.1 Time) against cost bias.

## 2.9 References

- `runtime/backend_router.py` — `route()`, `route_streaming()`, `_token_budget()`,
  `_groq_quota_cooldown_until`, `_openai_quota_exceeded`, `_ollama_available()` (WO-073),
  `active_backend()`, `_mock_fallback()`, `_detect_model_override()`.
- `runtime/faculty_health.py` — `mark_degraded` / `mark_recovered` (WO-042).
- `Volume_XX/01_Budgets_Tiers_Escalation.md` — the abstract tier + escalation policy.
- Volume VII (Executive), Volume XV Ch.2 (World State internet/environment), CONTRACTS.md.
- CLAUDE.md standing facts — Ollama `llama3.1:8b` floor; pinned chain; cost-sensitivity.

---

```
Chapter 2 — The Provider Chain: Tiers Made Real
Status: READY FOR REVIEW
Files: Volume_XX/02_The_Provider_Chain.md
Grounded in: runtime/backend_router.py (verified, live)
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (budget_allocation, honesty-channel backend_name)
Acceptance Tests: Included (FT ×4, ST ×3, IT ×2)
Open Questions: 4 (flagged for CA/David)
Implementation: PENDING — tier→provider mapping + escalation gate + cost telemetry not in code today
```

READY FOR REVIEW
