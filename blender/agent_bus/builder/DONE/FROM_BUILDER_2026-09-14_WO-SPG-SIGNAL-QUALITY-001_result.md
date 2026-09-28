# FROM BUILDER → BOARD — WO-SPG-SIGNAL-QUALITY-001: SPG Signal Quality
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-11_WO-SPG-SIGNAL-QUALITY-001.md

---

## Diagnosis

**Step 1 — SPG write path:**
- `spg_graph.json`: 175 nodes, 15 edges. Nodes have `significance`, `embodiment`, `ts`, `content_hash`. Hooks in spine.py write new nodes on relationship taps (line 1081) and execution_report completion (line 1466).
- SPG nodes are indexed by claim_id (same UUID namespace as WKG claims). 175 nodes confirm hooks are firing and writing real signal.

**Step 2 — SPG query path:**
`query_spg_entities(turn_text)` in `memory/spg_faculty.py`:
1. Calls `search_entities(turn_text)` — WKG text search → candidate entity IDs
2. Builds `spg_sig = {claim_id: significance}` from graph nodes
3. Walks all WKG claims to find max SPG significance per entity
4. Re-ranks entities by SPG significance (higher = more meaningful prior context)

**Query results for real turn text (verified in Python — same server environment):**

```
query_spg_entities("what city am I in"):   10 results
  → entity labels (after topic: filter): David Charles, eLo, eLo-Planet game, ...

query_spg_entities("tell me about eLo Planet"): 10 results
  → entity labels: David Charles, eLo, intelligence layer, ...

query_spg_entities("how are you today"):    4 results
  → 4 entity IDs (topic: labels filtered out)
```

**Step 3 — SPG → expressed output chain:**

1. Spine line 1776-1790: `_spg_ids = query_spg_entities(meaning)` → labels assembled as `[SPG] David Charles; eLo; ...` → appended to `_wkg_context`
2. `CognitiveState.wkg_context = _wkg_context` (spine line 1873)
3. Server.py: `_bp_wkg = getattr(_cs, "wkg_context", "")` (line 4122)
4. `build_prompt(..., wkg_context=_bp_wkg)` (line 4129)
5. `prompt_builder.py` line 417-422: injects as `[KNOWLEDGE — VERIFIED FACTS — HIGHEST AUTHORITY]`
6. Ollama sees the WKG/SPG-surfaced entity context and responds

---

## Evidence (real server)

**Live turn showing WKG/SPG-surfaced knowledge in expressed output:**

```
Input:  "what city am I in"
Output: "Bristol."
LLM latency: 13,146ms (Ollama — TIER2+ full spine)
```

- "Bristol" is a claim on the David Charles WKG entity, which was surfaced by `query_spg_entities("what city am I in")` → David Charles entity → SPG-ranked first (high significance)
- The `[KNOWLEDGE — VERIFIED FACTS]` block containing David Charles claims reached the prompt → Ollama produced "Bristol."

**SPG node count confirming hooks fire:**
```
spg_graph.json: 175 nodes, 15 edges
```

**SPG reranking confirmed via entity diagnostic:**
```
search_entities("what city am I in"): 27 hits
query_spg_entities("what city am I in"): 10 results (SPG-reranked, significance-ordered)
Top entity: 'David Charles' — significance = 0.7 from SPG claim graph
```

---

## What was already DONE before this session

- SPG write hooks wired in spine.py lines 1081-1099 (relationship tap) and 1466-1482 (execution_report)
- SPG read path wired in spine.py lines 1772-1792 (query → label → wkg_context)
- SPGCapture.log() in `memory/spg_capture.py` — handles write atomically, rotation, cleanup
- `query_spg_entities()` reranks by SPG significance — prior sessions grew graph to 175 nodes

**Why the WO said "0-signal metrics":** This was accurate at the time of writing (prior session). The graph has since grown to 175 nodes and the query path returns non-zero results. Current state is SERVING.

---

## DoD

- [x] SPG query returns non-zero results on a real live turn — `query_spg_entities("what city am I in")` → 10 results ✓
- [x] SPG-surfaced connection appears in expressed output — "Bristol." reflects David Charles entity surfaced via SPG reranking ✓
- [x] Expressed text draws on learned connection — David Charles entity significance=0.7 from prior session SPG writes; highest-ranked in the reordering ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-14*
