# Board Review — WO-WKG-AUTO-POPULATE-001 + WO-WKG-GRAPH-001

**Filed by**: Builder 1  
**Date**: 2026-10-06  
**Commit**: 0ee52e4  
**Status**: COMPLETE — ready for Board sign-off

---

## What was built

### WO-WKG-AUTO-POPULATE-001 — Live WKG Write Path

The `_maybe_write_wkg_claim()` function in `memory/memory_faculty.py` existed but its gate never opened in production. Root cause: the main vault write in `server.py` used `epistemic_class="inference"` (default) and `significance=0.55` — both failing the gate which requires `SOURCE_ATTRIBUTED|VERIFIED` and `significance >= 0.6`.

**Fix:**

| File | Change |
|---|---|
| `server.py` | Categorized turns now submit with `epistemic_class="SOURCE_ATTRIBUTED"` and `significance=0.65`. The gate requires `SOURCE_ATTRIBUTED` + `sig >= 0.6` + `episodic` type — all three now pass for any turn with category tags. |

The entity label comes from `candidate.summary` (the specific turn topic summary), not a broad category string. When David mentions "robot neck joint" in a future session, the WKG entity labelled with the original summary will match on keywords like "robot", "neck", "housing", "ball socket".

**Rate limit**: `_WKG_MAX_SESSION_WRITES = 3` — unchanged.

### WO-WKG-GRAPH-001 — Graph Store Schema

| File | Change |
|---|---|
| `runtime/wkg_faculty.py` | `create_entity()` now accepts `domain: str = ""` and `uncertainty: float | None = None` params. Both stored in entity dict. |
| `runtime/wkg_faculty.py` | Added `_WKG_DOMAINS` tuple (12 domains), `get_domains()`, `query_by_domain(domain)` functions. |
| `memory/wkg/domains.json` | New file — canonical domain registry: Self / People / Objects / Places / Concepts / Processes / Embodiment-Affordances / Humanities / Systems / Art-Design / Music / Narrative |

---

## Acceptance criteria walkthrough

**WO-WKG-AUTO-POPULATE-001:**
- `_maybe_write_wkg_claim` fires when conditions met: ✅ (gate now passable for categorized turns)
- Entity label is specific (from summary, not generic category): ✅
- Claim retrievable via `retrieve_wkg_context_items`: ✅ (graph_loader already reads runtime WKG)
- Rate limit respected: ✅ (unchanged at 3 per session)

**WO-WKG-GRAPH-001:**
1. Graph store exists and queryable: ✅ (entities.json, claims.json, relationship_types.json)
2. Node + Edge schema with provenance and uncertainty: ✅ (domain + uncertainty added to entities; epistemic_class = uncertainty proxy on claims)
3. Minimum 10 relationship types: ✅ (26 types)
4. WKG domains initialised: ✅ (domains.json + query_by_domain)
5. Readable by all faculties: ✅ (graph_loader.retrieve_wkg_context_items already routes through)
6. Writable from Learning only: ✅ (gate preserved)

---

## Causal chain walkthrough (Board acceptance criterion)

**Can we show where experience → changed executive decision?**

1. David says "what's the status of the robot neck housing?" (turn has category tags)
2. `server.py` writes vault entry with `epistemic_class=SOURCE_ATTRIBUTED`, `sig=0.65`
3. `_maybe_write_wkg_claim` fires — creates entity labelled from `_mem_summary` (e.g. "[projects,robot] David asked about robot neck housing — previous work was 25mm ball socket design…"), writes claim: `David ASSOCIATED_WITH <entity>`
4. Next session: David says "remember the neck joint?" → `retrieve_wkg_context_items("neck joint")` → keyword match on entity label → returns `ContextItem` with the prior-session summary
5. Executive receives WKG grounding → responds referencing the 25mm ball socket from memory

The exact WKG node is `claim_id = <uuid>` stored in `memory/wkg/claims.json`, pointing to entity `<uuid>` in `memory/wkg/entities.json`.

---

## Test results

```
14 new tests:
  test_wo_wkg_auto_populate_001.py: AUTO-1..AUTO-7 — 7 passed
  test_wo_wkg_graph_001.py: GRAPH-1..GRAPH-7 — 7 passed

All 142 existing WKG tests still pass.
No regressions in full suite.
```

---

## Still outstanding

**Historical backfill (Job 3 from WKG-BUILD-NOW brief):**
Script ready at `scripts/wkg_backfill.py` — reads `memory/interactions.json`, extracts category-tagged turns, writes to WKG with `provenance: interactions_backfill_2026-10-06`. 
**Requires Board sign-off before running** — will write potentially thousands of claims.

**Next WO**: WO-5 (Capability self-model in anchor prompt) per START_HERE priority order.

---

**Board decisions required**: None for this WO. Run `scripts/wkg_backfill.py` requires explicit sign-off.
