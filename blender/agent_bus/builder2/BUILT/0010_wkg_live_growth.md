# WO-B2-0010 — WKG growth from live turns (causal chain P0)
**Seat:** Builder 2 (coordinate with Builder 1)  
**Priority:** P0 — causal chain, demo milestone  
**Date:** 2026-10-11

## What
The causal chain: EXPERIENCE → vault_write → WKG growth → graph_loader retrieval → Executive grounded → eLo responds differently.

WKG has 3,167 nodes from backfill. Zero deprecated nodes. No nodes written from live turns this session.

Builder 2's half: confirm vault_write fires reliably on every significant turn. Confirm the signal reaches WKG. If vault_write is dropping writes, find why and fix it.

Builder 1's half: graph_loader retrieval wired into the spine's CognitivePlan (WO-0119 context).

## Done when
Live turn: David says something. Board checks claims.json. New node exists from that turn. File to Board: (1) the node, (2) the turn it came from, (3) next retrieval uses it.
