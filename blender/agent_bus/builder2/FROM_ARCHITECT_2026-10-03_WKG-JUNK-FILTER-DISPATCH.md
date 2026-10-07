# DISPATCH — WO-WKG-JUNK-ENTITY-FILTER-001
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-03
**Priority:** P1 — your next task

## WO
`engineering/work_orders/WO-WKG-JUNK-ENTITY-FILTER-001.md`

## Gap
WKG writer is creating junk entities: "Tell" (a verb, not a concept) and "Raspberry" (fragment, duplicates "Raspberry Pi"). These pollute the knowledge graph.

## Fix
In `wkg_faculty.record_claim()`:
1. Add a stopword filter — common verbs, articles, fragments under N chars should not become entities
2. Add a substring check — if a new entity name is a substring of an existing entity (e.g. "Raspberry" ⊂ "Raspberry Pi"), reject it

## After this WO
S2 Phase 1 — unless Board redirects.
