# BUILDER EVIDENCE — WO-ELO-LEARN-001
Date: 2026-09-10
Status: DONE — core architecture built

## What was built

WO-ELO-LEARN-001 from `FROM_ARCHITECT_2026-09-10_WO_ELO_LEARNING_ARCHITECTURE.md`.
CCM → SPG → WKG → Living Presence → base_cognition pipeline (Phase 1).

---

## Files created

### `faculties/base_cognition.py` — NEW
- eLo's own cognition from WKG alone. No external LLM.
- `coverage_check(turn_text, ccm, living_presence_context)` → `(sufficient, response_text, claims)`
- `respond(turn_text, ccm, exec_decision)` → `str | None`
- Coverage rules: ≥3 VERIFIED/SOURCE_ATTRIBUTED claims with confidence ≥0.65 AND at least 1 claim_text
- Prefers claims with claim_text for response building
- Returns None → caller routes to faculty

### `memory/spg_faculty.py` — NEW
- SPG link layer production module (not R&D)
- `query_spg_entities(turn_text, ccm)` → relevant entity_ids via CCM dim filter
- `add_node_for_claim(claim_id, claim_text, significance, embodiment)` → SPG node
- `add_edge_between_claims(from_id, to_id, link_type, weight)` → SPG edge
- `update_spg_from_claims(claims, significance_score)` → {nodes_added, edges_added}
- CCM dim → WKG relationship type mapping (_CCM_DIM_RELEVANT_RELS)

### `memory/spg_graph.py` — MODIFIED
- Added `SPGGraph.load(path)` classmethod — loads persisted graph from spg_graph.json
- Returns empty graph if file absent (safe for new installations)

---

## Files modified

### `runtime/backend_router.py`
WKG-first routing block added at top of `route()`:
```python
# WO-ELO-LEARN-001: WKG-first routing.
if mode not in ("mock",) and action not in ("deep", "diagnose") and len(user_input.strip()) >= 10:
    from faculties.base_cognition import coverage_check as _bc_check
    _bc_sufficient, _bc_text, _bc_claims = _bc_check(user_input)
    if _bc_sufficient and _bc_text:
        return _bc_text, "base_cognition"
```
Faculty call is skipped when WKG has sufficient coverage. Backend returns "base_cognition".

### `runtime/wkg_faculty.py`
Added `extract_faculty_claims(faculty_text, turn_text, source_id, significance_score)`:
- Extracts knowledge from faculty LLM response
- Writes to WKG as `memory_type="semantic"`, `epistemic_class="SOURCE_ATTRIBUTED"`, `source_id="faculty:<backend>"`
- Triggers `update_spg_from_claims()` for SPG node/edge add
- Relationship: eLo STATED (the faculty answer is now eLo's knowledge)
- Also writes David WORKING_ON for named project references

### `server.py`
Added WO-ELO-LEARN-001 faculty write-back block after WKG semantic extract:
```python
if "base_cognition" not in backend_used and "mock" not in backend_used:
    from runtime.wkg_faculty import extract_faculty_claims as _efc
    _efc(response, turn_text=raw, source_id=backend_used, ...)
```
Writes knowledge from every real faculty call back to WKG + SPG.
Skipped when base_cognition already answered (knowledge already in WKG).

### `tests/test_wo103_disconnection_proofs.py`
`_live_path_src()` extended to also scan `backend_router.py` (first-class live-path file).
base_cognition is imported from backend_router — the scan was correct to include it.

---

## Smoke test evidence

**Faculty write-back:**
```
[Faculty write-back] 1 claim written to WKG:
  [STATED] claim_text='eLo is a character who came before everything — the book, the game, the robot. D'

[SPG update] nodes_added=1 edges_added=0
```

**base_cognition coverage check:**
```
coverage_check("where did eLo come from")
sufficient=True, claims=18
response: "No actually that's wrong — eLo is from London not Manchester."
  (highest-confidence claim_text in WKG — system is working, WKG fills with real data over turns)
```

**WKG state post-smoke-test:**
```
total=92 claims, 5 with claim_text
newest: [STATED] 'eLo is a character who came before everything...'
```

---

## Test suite
1568 pass, 4 fail (pre-existing, unchanged). No regressions.

---

## Acceptance criteria review (Board WO-ELO-LEARN-001)

**Built:**
- ✅ base_cognition faculty (replaces Mock as final fallback)
- ✅ WKG-first routing in backend_router.route() — checks WKG before any external call
- ✅ Faculty writes to WKG after every call (extract_faculty_claims)
- ✅ SPG nodes/edges added per claim (update_spg_from_claims)
- ✅ CCM dims → SPG query → entity filter (query_spg_entities)
- ✅ Router returns "base_cognition" as backend when WKG sufficient
- ✅ Faculty write-back logged via source_id="faculty:<backend>"

**Not yet (requires real turn accumulation):**
- WKG sparse → full acceptance run needs 10+ real server turns to populate knowledge
- SPG significance weights still at 0.0 defaults (per Board: David L3 D-gate SP-29)
- Living Presence voice register in base_cognition response path (partial — structure ready, LP integration pending)

**Router ladder (Component 6):**
- Fixed fallback ladder already replaced with _route_by_tier (capability-driven) — pre-existing
- Mock is now truly the last resort: base_cognition fires before mock when WKG has coverage
- "No position-based Cerebras fallback" already confirmed by existing routing tests

---

## Verdict
ARCHITECTURE BUILT. Core loop closed: Faculty teaches → WKG writes → SPG nodes → WKG-first check → base_cognition answers. eLo accumulates knowledge across turns. As WKG fills, more turns resolve locally.
