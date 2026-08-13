---
volume: XX
title: "Cognitive Economy — Thinking Has a Cost"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content 2026-07-27 + ARCHITECTURE_BIBLE.md + runtime/backend_router.py (live)"
implementation: PENDING (real cost surface exists in backend_router.py; the tier→provider mapping,
  expected-value escalation gate, cost telemetry, and mock capability-honesty gate are NOT in code yet)
audit_status: OPEN
canonical_path: docs/architecture/Volume_XX/
tier: GOVERNANCE
dependencies:
  - Volume VII (Executive — allocates budgets, owns escalation authority)
  - Volume VI (Attention budget), Volume V/CONTRACTS.md
  - Volume XV Ch.1 (degraded-world honesty — sibling of degraded-tier honesty)
  - runtime/backend_router.py (the live routing/cost layer)
priority: "Bible GOVERNANCE tier; Audit: no resource budgeting today"
last_review: 2026-08-10
next_review: TBD
---

# Volume XX — Cognitive Economy

**One Brain → One Identity.** Cognitive Economy is a **policy of the Executive** (Vol VII),
not a separate decider. It does not run its own loop or negotiate with the Executive — the
Executive *asks* how deeply to think and where, exactly as it asks every other faculty. The
economy decides how much compute a turn earns; it never decides *what is true* (that stays
with Verified Speech) and it never spends premium cost by default (David is cost-sensitive;
the Ollama `llama3.1:8b` floor is the cheap always-on baseline).

## Scope (authoritative, from the Canon Index)
Budgets · cognitive tiers 0–3 · priority order · value-gated escalation — spending compute
and money only when the expected value justifies it — plus the honesty constraint that a
cheaper/degraded tier must never fake a stronger tier's capability.

## Anchors in the live system
- `runtime/backend_router.py` — the real cost surface: five modes (`auto`/`groq`/`cloud`/
  `local`/`mock`), the auto chain OpenAI→Gemini→Claude→Groq→Cerebras→Ollama→Mock, the pinned
  chain Groq→Cerebras→Ollama→Mock (WO-032), `_token_budget(action)` (600 heavy / 280 casual),
  Groq 429 60 s cooldown + session OpenAI quota flag, the Ollama local floor (WO-073), mock
  last resort, `active_backend()`/`backend_name` (the honesty channel).
- `runtime/faculty_health.py` — `mark_degraded`/`mark_recovered("reasoning")` (WO-042):
  how the rest of the system sees reasoning fall to a degraded tier.
- `backends/mock_backend.py` — the canned presence lines used as the last-resort tier.
- `ARCHITECTURAL_PRINCIPLES.md` — Verified Speech (Invariant 3) + Truth-before-fluency, the
  root of Chapter 3's degradation-honesty rule.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V20-CH01 | Chapter 1 | Budgets, Tiers & Escalation | READY FOR REVIEW |
| ELO-V20-CH02 | Chapter 2 | The Provider Chain — Tiers Made Real | READY FOR REVIEW |
| ELO-V20-CH03 | Chapter 3 | Degradation Honesty — A Cheaper Tier Must Never Fake Capability | READY FOR REVIEW |

## Invariants this volume must never break
1. **Economy is a policy of the Executive, not a parallel decider.** It answers "how deep,
   where, how much" when asked; it never runs its own loop or overrides the Executive.
2. **Cheapest capable path by default.** Default to the lowest tier that satisfies the need
   (Ch.1 §1.3); escalate to a paid tier only on positive expected value; never premium-by-default.
3. **The floor is real, not mute.** The Ollama local brain (WO-073) answers before mock — a
   cheap real answer beats a canned one.
4. **Saving cost never costs the truth (Verified Speech).** A cheaper/degraded tier stays
   within its real capability; it may be simpler or silent, but it never fabricates a stronger
   tier's output (Ch.3 — the sibling of Vol XV's degraded-world honesty).
5. **Safety and user interaction never yield.** Under scarcity, dreams/optimisation yield
   first (Ch.1 §1.4); safety and the person in front of eLo are always served.

## Definition of Done
- [x] Budget dimensions defined · cognitive tiers 0–3 · priority order · escalation rule (Ch.1)
- [x] Executive-owned allocation contract + tests (Ch.1)
- [x] Abstract tiers grounded in the live provider chain — modes, token budgets, quota
      handling, local floor, honesty channel (Ch.2)
- [x] Degradation-honesty rule + mock-degradation gate, tied to Verified Speech (Ch.3)
- [x] Each chapter: contract + lifecycle + envelope + acceptance tests; gaps marked PENDING
- [ ] CA review of the flagged open questions (Ch.2 ×4, Ch.3 ×3) + escalation-gate home (Ch.2 OQ-1)
- [ ] David L3 on RESERVED-adjacent items (API spend / cost telemetry — Ch.2 OQ-2/OQ-3)
- [ ] Architecture Agent can implement without inventing the tier→provider mapping (pending REVIEW)
- [ ] Audit can mark COMPLETE (blocked on the above + building the PENDING levers)

**Status: REVIEW** — three chapters READY FOR REVIEW; abstract policy grounded in the live
`backend_router.py`; PENDING gaps (tier→provider mapping, escalation gate, cost telemetry,
mock honesty gate) named, not hidden.
