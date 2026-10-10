# 05c_WO-110 — **KNOW · INFER · UNKNOWN (rows 9, 10, 11, 25, 26).** Tiers exist. They cover only his body.

**Seat:** builder · **Priority:** P1 · **Gate?** none · **Rows:** 9·10·11·25·26 → VERIFIED
**Canon:** ADR-Exec-001 Verified Speech, applied beyond the body.

## The finding [VERIFIED]
Tier vocabulary `runtime/the_moment.py:29-35`, applied in `compile()` `:64-90`, live at
`server.py:3056-3062`, written to `self/state/the_moment.json`. **It works — for pose, surface, caps,
nearby, locomotion.**

Three defects:
1. **Body only.** Nothing tiers memory, vault facts, facts about David, or tool results. So eLo can say
   *"I can see YouTube"* or *"you told me X"* with **no epistemic status at all** — §4's exact prohibition.
2. **Two tiers are constants, not checks.** `:67` always emits `"verified"`; `:85` always `"inferred"`.
   A constant is not a confidence.
3. **Skipped on direct/greeting turns** — the block only runs inside the LLM `else` branch; the fallback at
   `server.py:3064` is untiered. So the fastest, most common turns are the least honest.

## Build
- Make the tier a **general property of any fact eLo holds**, not a body-state decoration:
  `OBSERVED · INFERRED · REMEMBERED · UNKNOWN` (§4).
- **Compute** the tiers. Replace both constants with real checks against source + recency.
- **Never skip.** Direct and greeting turns get tiered state too.
- **UNKNOWN must be representable** — absence of state is itself a fact he can state.

## Test (without David)
- eLo distinguishes OBSERVED / INFERRED / REMEMBERED / UNKNOWN for a **non-body** fact.
- With state absent he says **"I don't know"** rather than producing a plausible answer.
- A tier changes when the underlying source changes (proves it's computed, not constant).
- Direct-turn path is tiered — assert on the fast path specifically.

## Done when
Committed. **Outbox: one example of each of the four tiers, from a real turn.**
