# WO-048 — "How's the company?" made real

> **⚡ VERIFY FIRST** — `DAVID_APPROVED.md` records "David live-confirmed 'works'" 2026-08-10. Test file exists: `tests/test_wo048_company_real.py` (12 ATs). **Run it before any implementation.** If all 12 pass → return result card and close. If any fail → implement the specific failing items only (not a full rewrite).



**From:** Board / Lead Architect — 2026-08-28
**Priority:** P1 — TIER 1 ACCEPTANCE TEST (one of David's two named goal behaviours for Presentable v1)
**Full WO:** `engineering/work_orders/WO-048_How_Is_The_Company_Real.md`
**API-FREE — build NOW regardless of Tier 0 brain status. Zero API cost. Pure deterministic Python.**

---

## The goal

Ask "how's the company / what's on the board / what should I work on" → eLo answers with something **REAL, that VARIES, with LINKS, and a view on what's better to work on.** Not hallucinated. Not a raw backlog dump.

## What to build (6 deliverables — all deterministic)

1. **Broaden company intent classifier** — every company/board phrasing routes to company path, NEVER falls to LLM/mock. At minimum: "how's the company / how are things / what's the company doing / what's on the board / what should I work on / what's the focus / status" + 6 more variations.
   - Ref: `server.py:2170` (`is_company_intent`). Same fix pattern as WO-035b semantic sit.
2. **Answer from REAL state, ranked to FOCUS** — read live `COMPANY_FOCUS` marker + `company_state.json`, surface FOCUS items first. Not the first ready-P1 rows (that's the WO-061 fault).
   - Include DISENELO identity/mission from the Operating Model doc.
3. **LINKS** — include path/link to actual work referenced (board row, WO, doc named).
4. **Recommendation** — one honest "what's better to work on" line: highest-tier unblocked close-out item, deterministic ranking.
5. **VARIED** — answer reflects current state each time; changes when state changes.
6. **Honest fallback** — if a datum is missing: say so, never invent.

## 5 ATs (`tests/test_wo048_company_real.py`)

- **AT-1:** 12+ company phrasings ALL route to company path; `backend` == `company_state` (never `mock`/LLM); 3 non-company controls do NOT misroute.
- **AT-2:** answer contains real DISENELO tokens from `company_state.json`/Operating Model (assert against actual state); mutated state changes the answer (VARIED).
- **AT-3:** with `COMPANY_FOCUS` set, answer surfaces FOCUS items, not first ready rows.
- **AT-4:** answer includes at least one link/path AND one "what to work on" line.
- **AT-5:** with a field blanked, answer says it doesn't have it (no fabricated value).

**Return:** `DONE/FROM_BUILDER_WO-048_company_real_result.md` · 5/5 AT PASS · commit hash
**Gate:** test green → David L3 live feel ("how's the company")

*Board / Lead Architect · 2026-08-28*
