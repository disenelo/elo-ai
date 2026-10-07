# KICKSTARTER PRIORITY — Next tasks
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-04

Kickstarter in one month. Your focus:

## 1. WKG JUNK ENTITY FILTER — NOW
WO-WKG-JUNK-ENTITY-FILTER-001
Brief: FROM_ARCHITECT_2026-10-03_WKG-JUNK-FILTER-DISPATCH.md
Remove Tell, What, You, Raspberry as entities. eLo stays. Add stopword filter + substring check to wkg_faculty.record_claim(). Report when done.

## 2. SPG SIGNIFICANCE SCORING
WO-SPG-PATTERN-001
Build the scoring function before any backfill. Three inputs in priority order:
1. Relationship type weight — DECIDED > FACT > BELIEF > OBSERVATION > ASSOCIATED_WITH
2. Recurrence — same claim across multiple turns = higher significance
3. Confidence — tiebreaker only

## 3. INNER THOUGHTS — S2 PHASE 1
After junk filter and significance scoring: continue S2 Phase 1.

## Report after each item.
