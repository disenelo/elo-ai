---
volume: XXIV
title: "Knowledge Architecture"
status: REVIEW — deep chapters drafted (READY FOR REVIEW)
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "ARCHITECTURE_BIBLE.md v1.0 (David Charles)"
audit_status: OPEN
canonical_path: docs/architecture/Volume_XXIV/
tier: GOVERNANCE
last_review: 2026-08-10
---

# Volume XXIV — Knowledge Architecture

## Scope (authoritative, from the Bible)
Ontology · knowledge graph · semantic networks · retrieval · compression · confidence ·
evidence · citation · reasoning support.

## Anchors in the live system
- `knowledge/graph_loader.py` — the **Connection Engine** (the anchor the chapters specify).
- `relationships/world_graph.json` (entities + relationships), `relationships/concepts.json`,
  `knowledge/viewpoints.json` — the three files the loader actually reads.
- `identity/world_graph.json` — **NOTE (flagged):** a *different, unused* schema (dict-keyed
  `{why,role,connects_to}` / `connections[]`, ids like "eLo-OS"); NOT read by graph_loader.
  Two-world-graph resolution is a blocking open decision (Ch.1 §1.6).
- Wiring: `server.py` (`graph_context`), `runtime/spine/control_plane.py` (`_build_context_block`).
- Memory retrieval/compression: Volume VIII + `17_memory_update.md`.
- Distinct from Vol XV World State (live world) — this is durable *knowledge*. Pairs with Vol VIII.

## Chapter Build Queue

| Ch | Title                                                        | Status            | Live anchor grounded |
|----|--------------------------------------------------------------|-------------------|----------------------|
| 01 | Ontology & the Knowledge Graph                               | READY FOR REVIEW  | graph_loader + world_graph/concepts/viewpoints json (node/edge schema) |
| 02 | Semantic Retrieval, Confidence & Evidence                    | READY FOR REVIEW  | build_context / _find_* retrieval path → ranked + confidence + evidence (Verified Speech) |
| 03 | Compression & Reasoning Support                              | READY FOR REVIEW  | build_context ≤800-char compression; boundary Vol VIII / Vol XV |

**Status: REVIEW** — all three deep chapters drafted READY FOR REVIEW; scope locked; pairs
closely with Vol VIII Memory. Blocking decision for CA/David: canonical world graph
(`relationships/` vs `identity/`), Ch.1 §1.6. Not RATIFIED — awaiting review.
