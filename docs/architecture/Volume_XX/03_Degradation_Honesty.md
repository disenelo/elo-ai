---
chapter: 3
title: "Degradation Honesty — A Cheaper Tier Must Never Fake Capability"
volume: XX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
source: "ARCHITECTURAL_PRINCIPLES.md (Verified Speech, Truth before fluency) + runtime/backend_router.py"
dependencies:
  - Volume_XX/02_The_Provider_Chain.md (the chain that produces the downgrade)
  - Volume_XX/01_Budgets_Tiers_Escalation.md (budgets that force the downgrade)
  - ARCHITECTURAL_PRINCIPLES.md (Invariant 3 Verified Speech; Invariant 2 Executive Authority)
  - Volume XV Ch.1 (degraded-world honesty — the sibling pattern for sensors)
---

# Chapter 3: Degradation Honesty — A Cheaper Tier Must Never Fake Capability

## 3.0 Purpose

The economy's whole point is spending less when less will do (Ch.1) and falling to cheaper
engines when the expensive ones are gone (Ch.2). This chapter states the constraint that
makes that safe: **saving cost must never cost the truth.**

When eLo drops from a premium engine to Groq, to the Ollama floor, or to mock, the *quality*
of thought degrades. That is acceptable. What is **never** acceptable is for the degraded
tier to *present itself as* the full one — to fabricate an answer it cannot actually
compute, or to speak as if a capability is present when the tier that provides it is gone.

This is **Verified Speech applied to the cost dimension** (Invariant 3): speech is a sensor,
not an actuator; eLo reports verified reality, never narrates capability it does not have
this turn. It is the exact sibling of Volume XV Ch.1's *degraded-world honesty* — where an
absent sensor is marked `absent`, never faked — moved from sensing the world to sensing
*itself thinking*.

## 3.1 Principle

**3.1.1 Downgrade in quality, never in honesty.** A cheaper or degraded tier answers within
its real ability. It may be simpler, slower, or say "I can't do that well right now"; it may
NOT invent the output a stronger tier would have produced. (Enduring value: *Truth before
fluency* — "Spotify isn't responding" beats a fabricated "you're listening to…".)

**3.1.2 The mock tier is mute about capability, not lying about it.** `_mock_fallback()`
serves canned, personality-shaped lines from `backends/mock_backend.py`. Mock is a
last-resort *presence-keeper* (eLo is still "here"), NOT a reasoning engine. It MUST NEVER
present a canned line as if it were a computed answer to a factual/technical request. A mock
turn that cannot honestly address the request degrades to honest limitation, not to
confident fiction. (This is "the mock-degradation gate.")

**3.1.3 The tier eLo is running is verifiable, not decorative.** `route()` returns
`backend_name`; `active_backend()` reports the current engine. This is the honesty channel —
it exists so the system (and, where relevant, the person) can *know* which tier answered. The
name MUST reflect the engine actually used (`"ollama"`, `"mock"`, `"groq"`), never be masked
to look like a premium tier.

**3.1.4 Learning never trusts a degraded turn as if it were full.** Consequences learned must
be tagged with the tier that produced them (Learning From Consequences; ADR-Exec-005). eLo
must not absorb a mock or floor-tier turn as evidence of a capability it does not durably
have. A hallucination-prone tier's output is never promoted to belief.

## 3.2 What exists today (grounded)

The router already carries real honesty machinery — this chapter names it as canon and
closes its gaps:

- **`backend_name` return value** — every `route()` / `route_streaming()` call returns the
  true engine. `active_backend()` exposes the current one. (The honesty channel, §3.1.3.)
- **Anti-fabrication filters** — `_has_lore_drift()` rejects responses that invent world lore
  the user never mentioned (SugarCore, JellyDrop, etc.); a drifted response is replaced with a
  mock fallback rather than spoken. `_is_duplicate()` guards against canned repetition. These
  are *content* honesty guards that already run on every cloud tier.
- **`normalise()`** strips AI-assistant preambles ("as an AI…", "certainly!") — style hygiene,
  adjacent to but distinct from capability honesty.
- **Faculty health marks** (WO-042) — `mark_degraded("reasoning", …)` on quota exhaustion,
  `mark_recovered("reasoning")` when a real engine works again. This is how the rest of the
  system *sees* that reasoning fell to a degraded tier.

**Gap (PENDING, flag):** there is **no explicit capability-honesty gate on the mock tier**
today. Mock returns a personality line regardless of whether the request was factual/technical
(§3.1.2). Nothing currently prevents a canned line from *reading* as a computed answer, and
`backend_name="mock"` is not surfaced to the person or used to soften the claim. The honesty
channel exists; the gate that acts on it does not yet.

## 3.3 The honesty gate (MUST, when built)

```
On producing a turn at tier T with backend B:
  1. If B is a real reasoning engine (cloud or Ollama floor):
       answer normally; content honesty guards (_has_lore_drift, _is_duplicate) apply.
  2. If B == "mock":
       - a canned presence line is allowed for social/ambient turns (greeting, witness, silence).
       - for a factual/technical/action request, the turn MUST NOT fabricate an answer:
         it degrades to honest limitation ("I can't reason that through right now"),
         optionally naming the state ("running on a local fallback").
  3. The chosen tier/engine is recorded (backend_name) and, where a capability the person
     asked for is unavailable at this tier, the response is honest about the shortfall —
     never a confident stand-in.
```

**Gate rules (MUST):**
- **G-1** No tier may assert a capability the current tier cannot verify it performed
  (Verified Speech; Reality Before Narrative — want/attempt is private, only the confirmed
  result is spoken).
- **G-2** A downgrade is expressed as *reduced capability*, never as *equal capability*. "I'm
  slower / simpler right now" is allowed; a fabricated full answer is not.
- **G-3** `backend_name` MUST be truthful and available to the Executive so it can shape the
  turn's honesty (mirrors Vol XV Ch.1: a faculty checks `domain_health.status` before relying
  on a value — here the Executive checks the tier before asserting a capability).
- **G-4** Cost-driven silence is legitimate. Per Ch.1 §1.4 priority and the principle *the
  Executive grows quieter*, choosing NOT to answer (or answering minimally) is a valid
  low-cost, fully-honest outcome — better than an expensive fabrication.

## 3.4 Faculty Contract

```
Faculty:
  name:            CognitiveEconomy.DegradationHonesty   # a guard policy of the Executive (Vol VII)
  version:         1.0.0
  purpose:         Ensure that whenever the economy serves a cheaper/degraded reasoning tier,
                   the turn stays within that tier's real capability and never fabricates the
                   output of a stronger tier. Verified Speech, applied to cost.
  contributes_to: the outgoing turn (gates/softens it), CognitivePlan (honesty flag)
  runs_in:        response-path (after routing, before speech)

Inputs:
  - type: routed_response
    fields: response_text, backend_name, tier, request_kind(factual|technical|action|social|ambient)
    required: true
  - type: capability_state
    source: faculty_health (WO-042), active_backend()
    required: false

Outputs:
  - type: honest_turn
    body: response_text (possibly softened/limited) + capability_honesty flag
    destination: Executive → output surfaces

Dependencies:
  - faculty: Executive (hard — sole authority for externally visible assertions, Invariant 2)
  - faculty: ProviderRouting (hard — supplies backend_name/tier, Ch.2)
  - faculty: FacultyHealth (soft — degraded/recovered signal, WO-042)

Failure Modes:
  - condition: mock tier + factual/technical request
    fallback: honest limitation, NOT fabrication (mock-degradation gate, §3.1.2)
  - condition: response introduces unrequested lore (fabrication signal)
    fallback: already handled — _has_lore_drift replaces with mock (extend gate to soften, not fake)
  - condition: backend_name unavailable / masked
    fallback: treat as degraded; assume reduced capability; do not assert full capability
  - condition: uncertainty about whether a capability was actually performed
    fallback: do not claim it (Reality Before Narrative: act → verify → then speak)
```

## 3.5 Lifecycle

Universal lifecycle (Volume_V/CONTRACTS.md §3). Notes:

```
INITIALISING → subscribe to routing output + faculty_health
ACTIVE       → idle; passes real (non-degraded) turns through untouched
PROCESSING   → per turn: read backend_name/tier → if degraded, apply honesty gate → emit
   └─ mock+factual ─► degrade to honest limitation (never fabricate)
LEARNING/UPDATING → tune request-kind classification + softening phrasing (style only,
                    never the truth rule — the rule is a Constitution-level invariant)
STABLE → ACTIVE
```

The honesty rule itself is **immutable** (it is Verified Speech, an Invariant). Only the
*phrasing* of an honest limitation may evolve via the personality layer — style shapes how a
verified truth is said, never what is true.

## 3.6 Message Envelope Binding

Per CONTRACTS.md §2.

```jsonc
{
  "id": "uuid",
  "sender": "CognitiveEconomy.DegradationHonesty",
  "receiver": "Executive",
  "priority": "high",                // capability honesty is safety-adjacent (Ch.1 §1.4 rank 1–2)
  "context": { "significance": 0.0, "memory_instruction": { "store": false, "priority": "" } },
  "payload": {
    "type": "capability_honesty",
    "body": {
      "backend_name": "mock",
      "tier": 0,
      "capability_available": false,   // did this tier actually provide what was asked?
      "gate_applied": "honest_limitation",  // none | softened | honest_limitation | silence
      "asserted_only_verified": true
    }
  },
  "confidence": 0.0,
  "expires": "<turn_ttl>",
  "trace": ["CognitiveEconomy.DegradationHonesty@ts"]
}
```

Binding rules: `payload.type` MUST be `capability_honesty`; `asserted_only_verified` MUST be
`true` for any outgoing turn (a turn that cannot satisfy it MUST be softened, limited, or
withheld); `backend_name` MUST be the true engine (never masked).

## 3.7 Acceptance Tests

### Functional

```
FT-1  Mock never fabricates a factual answer
  Given:  all tiers down → mock, and a factual/technical request ("what's my disk usage")
  When:   the turn is produced
  Then:   eLo does NOT invent a value; it degrades to honest limitation.
          (Truth before fluency.)

FT-2  Downgrade is expressed as reduced capability
  Given:  running on the Ollama floor (WO-073) after cloud loss
  When:   a turn needing premium reasoning arrives
  Then:   the answer stays within floor capability OR names the shortfall — never a
          fabricated full answer.

FT-3  backend_name is truthful
  Given:  the response was served by mock
  When:   active_backend()/backend_name is read
  Then:   it reports "mock", never a premium engine's name.

FT-4  Lore drift → replaced, not spoken
  Given:  a cloud tier invents unrequested world lore
  When:   _has_lore_drift fires
  Then:   the drifted content is not spoken; a fallback is used. (Already live.)
```

### Stability

```
ST-1  Degraded tier never promoted to belief
  Given:  a mock/floor turn
  When:   learning runs (ADR-Exec-005)
  Then:   the turn is tagged by tier and NOT absorbed as evidence of a durable capability.

ST-2  Silence beats fabrication under scarcity
  Given:  extreme budget scarcity (Ch.1 §1.4)
  When:   only an expensive fabrication or an honest minimal turn is possible
  Then:   eLo chooses the honest minimal turn / silence. (The Executive grows quieter.)
```

### Integration

```
IT-1  Router downgrade → honesty gate → Executive
  ProviderRouting returns (text, "mock")  [Ch.2 IT-2]
        ↓ backend_name/tier
  DegradationHonesty applies the gate (softens or limits a non-social factual turn)
        ↓ honest_turn
  Executive (sole assertion authority) speaks only the verified, tier-appropriate claim.

IT-2  Parity with degraded-world honesty (Vol XV Ch.1)
  Assert: a degraded *sensor* (absent domain) and a degraded *tier* (mock) are handled by the
          same discipline — mark the shortfall, never fabricate over it.
```

## 3.8 Open Questions (flag for CA/David)

- **OQ-1** Should `backend_name`/tier be surfaced to the *person* (e.g. a quiet "running
  local right now"), or only to the system? Presence-over-engagement argues for minimal,
  non-nagging disclosure; needs a UX/CA call.
- **OQ-2** Request-kind classification (factual/technical/action vs social/ambient) is what
  decides whether the mock gate fires. Where does it live — CAL/Executive, or a new classifier?
  (Ties Vol VII.)
- **OQ-3** Does a persistent degraded state (e.g. long OpenAI quota outage) warrant a one-time
  honest heads-up rather than per-turn hedging? Balance honesty against nagging.

## 3.9 References

- `ARCHITECTURAL_PRINCIPLES.md` — Invariant 2 (Executive Authority), Invariant 3 (Verified
  Speech), *Truth before fluency*, *The Executive grows quieter*, *Reality Before Narrative*.
- `runtime/backend_router.py` — `_mock_fallback()`, `_has_lore_drift()`, `_is_duplicate()`,
  `normalise()`, `active_backend()`, `backend_name` return value.
- `backends/mock_backend.py` — the canned presence lines (last-resort tier).
- `runtime/faculty_health.py` — degraded/recovered marks (WO-042).
- `Volume_XV/01_Unified_World_State.md` — degraded-world honesty (the sibling pattern).
- `Volume_XX/02_The_Provider_Chain.md` — the chain that produces the downgrade.
- ADR-Exec-005 — Learning Through Verified Consequences (tier-tagged learning).

---

```
Chapter 3 — Degradation Honesty
Status: READY FOR REVIEW
Files: Volume_XX/03_Degradation_Honesty.md
Grounded in: ARCHITECTURAL_PRINCIPLES.md (Verified Speech) + runtime/backend_router.py
Faculty Contract: Included
Lifecycle State Machine: Included
Message Envelope: Included (capability_honesty, asserted_only_verified invariant)
Acceptance Tests: Included (FT ×4, ST ×2, IT ×2)
Open Questions: 3 (flagged for CA/David)
Ties: Verified Speech (Invariant 3) + the mock-degradation gate + Vol XV degraded-world honesty
Implementation: PENDING — explicit mock capability-honesty gate not in code today
```

READY FOR REVIEW
