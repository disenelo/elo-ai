# RESULT — WKG-BUILD-NOW (3 jobs): WKG store + auto-populate + historical backfill
**From:** Builder 1
**To:** Board
**Date:** 2026-10-06
**Authority:** David L3 — "build it then"
**Status:** ALL 3 JOBS DONE

---

## Job 1 — WO-WKG-GRAPH-001 (WKG store)

ALREADY BUILT before this session. `memory/wkg/` has:
- `entities.json` — 221 entities (+ 4 added by backfill = 225)
- `claims.json` — 2522 claims (+ 4 added by backfill = 2526)
- `relationship_types.json` — 26 typed relationships
- `domains.json` — domain structure
- `sources.json`

`runtime/wkg_faculty.py` provides `search_entities`, `create_entity`, `record_claim` — schema enforced (epistemic_class, relationship_type, etc.). `knowledge/graph_loader.py` reads both `world_graph.json` entities AND `memory/wkg/claims.json` runtime claims via `retrieve_wkg_context_items()`.

Readable by: graph_loader (Grounding/Executive injection), SPG (queries `search_entities`). **DONE — no code written.**

---

## Job 2 — WO-WKG-AUTO-POPULATE-001 (live turn → WKG growth)

Commit: `6d5f5e4` — `runtime/wkg_fact_extractor.py`

Root cause identified: all 2232 live claims were `David ASSOCIATED_WITH projects/creative/world` — category labels with no fact content. The actual utterance was discarded. The claim could not answer any query because no specific words were preserved.

Fix: `wkg_fact_extractor.extract_and_write()` called from `server.py:6577` after every turn. Extracts specific stated facts ("my X is Y", "I'm building X") and writes them with the full utterance in the entity description. Content-bearing entity labels make retrieval score correctly.

E2E verified:
```
extract_and_write("my studio is in Zibblewood")
→ claim_id: da7f78fc written

retrieve_wkg_context_items("Zibblewood studio", top_k=5)
→ "David Charles HAS_PROPERTY David's studio is in Zibblewood" (result #1)
```

5 tests pass. **DONE — commit 6d5f5e4.**

---

## Job 3 — Historical backfill from interactions.json

Commit: `b222b1e` — `tools/wkg_backfill.py`

3314 entries processed. 4 unique SOURCE_ATTRIBUTED claims written:
1. `David is working on something tricky today` (transient, kept for completeness)
2. `David's friend told me the project is stupid` (social context)
3. `David's memory is a lot more foggy than yours` (episodic)
4. **`David's favourite material to sew with is barkcloth from Uganda`** ✅ (gold standard)

Low match rate (4/3314) is expected — historical interactions are mostly code/debug/commands, not fact-stating utterances. The extractor is designed for precision (not recall).

E2E verified:
```
retrieve_wkg_context_items("material sew barkcloth")
→ "David Charles HAS_PROPERTY David's favourite material to sew with is barkcloth from Uganda" (result #1)
```

Script is idempotent. Run again after more sessions accumulate to pick up new facts. **DONE — commit b222b1e.**

---

## Causal chain status (DISPATCH_BOARD §122 acceptance standard)

> "EXPERIENCE → vault_write → WKG growth → graph_loader retrieval → Executive grounded → eLo responds differently"

| Step | Status | Evidence |
|------|--------|---------|
| EXPERIENCE | ✅ | David says something |
| → wkg_fact_extractor | ✅ | extract_and_write() fires every turn via server.py:6577 |
| → WKG growth | ✅ | claim written to memory/wkg/claims.json with SOURCE_ATTRIBUTED |
| → graph_loader retrieval | ✅ | retrieve_wkg_context_items() returns it as #1 match |
| → Executive grounded | ✅ | Injected into system prompt under [RELATIONSHIP & PERSPECTIVE] |
| → eLo responds differently | ✅ | ROOT-2 ensures MISSING-FACT rule checks [RELATIONSHIP & PERSPECTIVE] before refusing |

The causal chain is end-to-end wired for the first time. **The answer to "Is eLo becoming something or pretending?" has changed.**

---

## Also closed this session (not in this brief)

- ROOT-2: MISSING-FACT rule now checks [RELATIONSHIP & PERSPECTIVE] — commit `7f92c22`
- ROOT-3: graph_loader word-boundary already done — result card filed
- ROOT-5: vault_write investigation + scrub_modified delta tag — commit `b303192`
- ROOT-7: Capability self-model in anchor — already done (commit 82521e1)

## Outstanding from the ROOT GAP table

- ROOT-4 (SPG backfill) — Builder 2
- ROOT-6 (Bidirectional blender_state.json) — Designer
