# WO-CANON-XX — Cognitive Economy: make the router a cognitive-tier selector with value-gated escalation + cost telemetry

**Owner:** Builder (eLo OS — `runtime/backend_router.py`, `runtime/faculty_health.py`). **Priority:** P3 — Horizon-2
(post-Presentable v1), Tier B. **Status:** QUEUED behind Presentable v1 + Tier A. Escalation-gate home + cost telemetry
carry **CA + David L3** open questions (David is cost-sensitive) — note the gate below.

**Canon refs:** Volume XX — Ch.1 `01_Budgets_Tiers_Escalation.md`, Ch.2 `02_The_Provider_Chain.md`, Ch.3
`03_Degradation_Honesty.md`. Principle: Verified Speech (Invariant 3). Ties WO-073 (Ollama floor), WO-032 (pinned Groq).

## Problem / Goal
`runtime/backend_router.py` is a LIVE cost surface: five modes, both provider chains, `_token_budget`, Groq/OpenAI
quota handling, the Ollama local floor (WO-073), mock last resort, `backend_name`/`active_backend()` honesty channel,
anti-fabrication (`_has_lore_drift`, `_is_duplicate`). But it selects **provider by availability/mode, not cognitive
depth by expected value** — the tier→provider mapping, the value-gated escalation gate, cost telemetry, and the explicit
mock capability-honesty gate are unbuilt. Goal: bridge "where thinking runs" and "how hard eLo thinks," cheap-first.

## Scope to DoD (grounded in Ch.1–Ch.3)
- **Tier→provider mapping (Ch.2, PENDING):**
  - **M-1** Serve Tier 0 (Reflex: time, calculator, nav, lore, greeting pool) deterministically **before** `route()` is
    ever called; if a turn reaches the router it is already ≥ Tier 1. Lift the length gates that forced short turns to
    mock (`_AUTO_LOCAL_MAX_CHARS=80` is a dormant lever — retire or wire per OQ, David L3).
  - **M-2** Executive supplies a chosen `tier` to the router (new `tier` argument beside `action`); absent a tier, the
    router defaults to the **cheapest capable** path, never the most expensive.
  - **M-3** Make `_token_budget()` **tier-aware** (tier primary key, action secondary). Keep the live budgets
    (`build/challenge/reflect/plan/deep/diagnose → 600`; `celebrate/connect/ground/navigate/witness/silence/answer → 280`).
  - **M-4** Make provider cost class explicit (free-local / cheap-cloud / premium-cloud) so escalation compares cost vs
    expected value. Keep the live mode chains verbatim (auto / groq-pinned / cloud / local / mock) and quota handling
    (Groq 429 → 60s cooldown self-clears; OpenAI 429 → session flag + `mark_degraded("reasoning")`).
- **Value-gated escalation (Ch.1 §1.3 / Ch.2 §2.3):** escalate to a higher tier only when expected value > additional
  cost; default the lowest sufficient tier; prefer the Ollama floor and escalate on demonstrated need; every escalation
  MUST be recorded/auditable (`escalated` flag in the envelope). Enforce the priority order (MUST): Safety > User
  interaction > Executive stability > Working Memory > Planning > Learning > Reflection > Dreams > Optimisation —
  dreams/optimisation yield first, safety + user interaction never yield.
- **Cost telemetry (Ch.2 OQ-2):** per-turn cost/budget accounting + API-spend logging (David L3 to confirm scope +
  retention/privacy posture, ties Vol XXIII). Surface `backend_name`/tier truthfully to the Executive.
- **Degradation-honesty gate (Ch.3, PENDING):** **G-1** no tier asserts a capability it cannot verify it performed;
  **G-2** a downgrade is expressed as reduced capability, never equal; **G-3** `backend_name` truthful + available to
  the Executive; **G-4** cost-driven silence is legitimate. Mock gate: a canned presence line is allowed for
  social/ambient turns, but for factual/technical/action requests mock MUST NOT fabricate — degrade to honest
  limitation ("I can't reason that through right now"). `asserted_only_verified` MUST be true on every outgoing turn;
  Learning never trusts a degraded (mock/floor) turn as belief; consequences tagged by tier (ADR-Exec-005).

## Definition of Done
- Router accepts an Executive-chosen tier and maps tier→provider by cost class; Tier 0 never reaches the router;
  default is cheapest-capable; every escalation is logged with an `escalated` flag.
- Per-turn cost telemetry recorded; priority order honoured under scarcity (safety/user never yield).
- Mock/floor tiers never fabricate a factual answer; downgrades expressed as reduced capability; `backend_name` truthful.
- Audit can mark Vol XX COMPLETE.

## Tests to write (`tests/test_canon_xx_economy.py`) — from Ch.1/Ch.2/Ch.3 §*.7
- Ch.1: lowest sufficient tier ("what time is it" → Tier 0, no LLM), value-gated escalation, scarcity yields
  low-priority, safety never yields, economy→Executive plan (tier + budget in CognitivePlan).
- Ch.2: mode chains match code (groq mode never touches OpenAI/Gemini/Claude), token budget keys off action, local
  floor before mock, Tier 0 never reaches router, Groq 429 → 60s cooldown, OpenAI 429 → session skip + health mark,
  cheap-first default, Executive tier → router budget (escalated logged), degradation visible downstream.
- Ch.3: mock never fabricates a factual answer, downgrade expressed as reduced capability, `backend_name` truthful,
  lore drift replaced not spoken, degraded tier never promoted to belief, silence beats fabrication, router downgrade →
  honesty gate → Executive, parity with degraded-world honesty (Vol XV).

## Dependencies + blocked-by
- **Blocked by:** — none hard; runs behind Presentable v1 + Tier A. Open questions block RATIFICATION, not build start:
  escalation-gate home (Executive vs pre-router policy — CA), cost-telemetry scope/retention (David L3),
  `_AUTO_LOCAL_MAX_CHARS` retire-or-wire (David L3), request-kind classifier home (CA/Vol VII).
- Cross-volume: Vol VII Executive (owns tier choice + escalation authority), Vol VI (attention budget), Vol XV
  (degraded-world-honesty sibling; internet/environment gate reachability), Vol XXIII (telemetry privacy).
- **Gate:** CA on escalation-gate home + David L3 on API-spend/cost-telemetry before Vol XX is promoted.

## Lane
Builder (Python — `runtime/backend_router.py` tier layer + escalation gate + telemetry + mock-honesty gate).
Architect coordinates + carries the escalation-gate / cost decisions to CA + David.
