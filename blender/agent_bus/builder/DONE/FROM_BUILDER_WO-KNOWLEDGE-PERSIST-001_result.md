# FROM_BUILDER — WO-KNOWLEDGE-PERSIST-001
**Status:** NOT SERVING — entity extraction gap prevents fact recall
**Date:** 2026-09-09
**Builder:** Claude (session b15c1e7a resumed)

## Test

**Input:** "where am i from"
**Expected:** eLo recalls David is from London (WKG foundational fact)
**Actual:** "You keep coming back to narrative." (mode: reflect)

## Root Cause

WKG claims.json has 65 entries (grown from 21 — write path works). But ALL 65 claims
have subject=None, object=None, relationship_type=None or ASSOCIATED_WITH.

The entity extraction step that should identify `subject="David"`, `object="London"`,
`relationship_type="IS_FROM"` is not functioning. Claims are written as null-entity
associations with no useful lookup key.

## What's working vs what's not

WORKING:
- Claim write path — WKG grows per session (21→65 claims)
- SPG significance scores — populated on all new signals (confirmed 2026-09-09)

NOT WORKING:
- Entity extraction — subject, object, relationship_type all null
- Fact retrieval — can't query by entity (David, London) when entities aren't labelled

## Active WO

Board has this as PENDING: "WO-WKG-LIVE-WRITE-001 (content-specific part) — Needs semantic
entity extraction WO from Board". This is that gap, confirmed.

## Next step

Board must dispatch a WO for semantic entity extraction in WKG. Until entities are labelled,
knowledge persist cannot be verified — the infrastructure writes but the graph is not queryable.
