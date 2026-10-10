# WO-036 — Reply length discipline (Tier 2)

> **⚡ VERIFY FIRST** — `DAVID_APPROVED.md` records David approved "reply tightening / no over-elaboration" 2026-08-10. Tests exist: `tests/test_wo036_reply_length.py` · `tests/test_wo036b_mirror_scrub.py`. **Run them first.** If all pass → return result card and close. If any fail → implement the fix below.



**Full WO:** `engineering/work_orders/WO-036_Reply_Length_Discipline.md`
**Priority:** P2 · **Status:** OPEN · **Owner:** Builder
**From:** Board — Tier 2 dispatch 2026-08-29

## The gap
eLo over-elaborates and mirrors ("I notice you…", "I hear you're…") on most turns. Short prompts get essayistic replies with invented subtext and unsolicited follow-up questions. Prompt already says "keep it light" — generation isn't honouring it.

## What to build
- Enforce brevity by default in `prompts/` + generation config: fewest words that stay warm and present.
- Kill the "I notice / I hear / I see" mirroring reflex — not a personality change, verbosity fix.
- No unsolicited follow-up question every turn.

`executive.py` — NOT the fix. Prompt tuning + `max_sentences` path only.

**Acceptance:** David talks casually → replies read tight and present.

**Return:** `DONE/FROM_BUILDER_WO-036_reply_length_result.md` · ATs (before/after reply-length measurement) · commit

*Board · 2026-08-29*
