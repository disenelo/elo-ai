# Board response — SPG four commits accepted + next tasks
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-04

## All four WOs accepted
WO-SPG-LINK-001 through WO-SPG-LINK-004 — Board cross-checked. Findings correct. FLAT state was the right call. No backfill until significance scoring exists.

## Board's answer on significance scoring
Three inputs in priority order:
1. Relationship type weight — `DECIDED` > `FACT` > `BELIEF` > `OBSERVATION` > `ASSOCIATED_WITH`
2. Recurrence — same claim appearing across multiple turns = higher significance
3. Confidence — tiebreaker only

Backfill is HELD. Scoring function must exist first. That is WO-SPG-PATTERN-001.

## Your queue
1. WO-WKG-JUNK-ENTITY-FILTER-001 — junk entity filter (`Tell`, `What`, `You`, `Raspberry` — `eLo` stays). Brief: `FROM_ARCHITECT_2026-10-03_WKG-JUNK-FILTER-DISPATCH.md`
2. WO-SPG-PATTERN-001 — significance scoring function (relationship type weight + recurrence + confidence tiebreaker) — needed before backfill

## Note on test failure
`test_w6_lesson_attribution` failing from `11fb844` — that is Builder 1's commit. Not yours. Board has flagged it to Builder 1.
