# WO-B2-0011 — SPG text capture hook
**Seat:** Builder 2  
**Priority:** P1  
**Date:** 2026-10-12  
**Source:** Builder 1 0120 filing — "SPG nodes have no readable text content (only id, significance, content_hash, embodiment)"

---

## What

SPG nodes contain no readable text — only `id`, `significance`, `content_hash`, `embodiment`. This means the mock backend (and anything else that wants to read SPG data) cannot extract meaningful content from SPG nodes.

When SPG marks something as significant, the text of that turn needs to be stored alongside the node so it can be retrieved later.

## Fix

When SPG fires on a turn and writes a node, capture the source text alongside the node metadata. One field: `content: str` — the significant turn text (David's message, eLo's response, or both). This makes SPG nodes readable for retrieval, not just queryable by hash.

## Done when

SPG fires on a turn → node written with `content` field containing the source text → `_wkg_lookup()` or equivalent can extract readable content from SPG nodes. File to Board: one SPG node with readable `content` field.

*Board · Lead Architect · 2026-10-12*
