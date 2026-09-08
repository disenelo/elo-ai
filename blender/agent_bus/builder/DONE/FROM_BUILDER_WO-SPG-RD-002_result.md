# FROM_BUILDER — WO-SPG-RD-002 Result Card
**Date:** 2026-09-05  
**WO:** WO-SPG-RD-002 — SPG R&D Track: Memory Link Graph  
**Priority:** R&D · Authority: David L3 2026-09-05  
**Executed by:** Builder seat  

---

## Deliverables

| Item | Status |
|---|---|
| `memory/spg_graph.py` — `Node` + `Edge` dataclasses (D-1 schema) | CHANGED (NEW) |
| `SPGGraph` class — add_node, add_edge, top_linked, save/to_dict (D-2 builder) | CHANGED (NEW) |
| `build_graph()` — reads `data/spg_signals.jsonl`, constructs graph | CHANGED (NEW) |
| `build_and_save()` — build + persist to `data/spg_graph.json` | CHANGED (NEW) |
| `top_linked(context_node_id, top_n)` — query prototype (D-3) | CHANGED (NEW) |

## Graph schema (D-1)

```
Node:
  id:           str          # turn_id:signal_type composite
  content_hash: str          # sha256[:16] of signal record
  significance: float        # SP-29 overall score
  embodiment:   str          # surface (desktop / mobile)
  ts:           float        # creation timestamp

Edge:
  from_node:    str
  to_node:      str
  link_type:    str          # temporal | semantic | significance_chain | embodiment_continuity
  weight:       float        # 0.0–1.0
  evidence:     str
```

## Link types implemented (D-2)

| Link type | Construction rule |
|---|---|
| `temporal` | Adjacent signals in the same turn (ordered by signal list position) |
| `significance_chain` | Both nodes have `significance ≥ 0.6` — weight = average significance |
| `embodiment_continuity` | Same signal_type emitted from different embodiments |

`semantic` and `relational` links not yet implemented — require semantic embedding or entity extraction that is not available in the signal log format.

## Gate measurements (D-4)

**G-2 (real-memory applicability):** NOT YET MEASURABLE. `data/spg_signals.jsonl` is empty — no hook points have fired yet (all D-3 hook points in WO-SPG-CAPTURE-001 were DEFERRED pending clean hook points in spine). G-2 requires ≥10 real turns of signal data. Status: OPEN.

**G-5 (production utility):** NOT YET MEASURABLE for the same reason. The graph builder runs cleanly with synthetic data and sub-millisecond query latency at small scale (3 nodes, 3 edges = 0ms). At production scale, cost depends on graph density — to be measured once real signals accumulate. Status: OPEN.

**G-3 (unique-addressability):** CLOSED 2026-08-23. Documented in `findings/G3_CLOSURE_2026-08-23.md`.

## Prototype validation

```
Schema PASS: 3 nodes, 2 edges
Query PASS: top_linked returned correct ranking
Save PASS: graph JSON serialises cleanly
Empty PASS: no signals → empty graph (graceful)
Build PASS: 3 synthetic signals → 3 nodes, 3 edges
```

**Test run:** 1559 passed. 3 pre-existing failures unchanged.

## Next step for gates

Once SPG hook points are wired (future WO), real signals will accumulate in `data/spg_signals.jsonl`. Run `build_and_save()` against real data, evaluate G-2 manually across 10 turns, measure G-5 latency. Board reviews gate results and rules production integration separately.

*Builder seat · 2026-09-05 · WO-SPG-RD-002 · R&D only · G-2/G-5 OPEN*
