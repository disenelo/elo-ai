# FROM BUILDER — WO-NAV-012 Candidate Surfaces in world_dict
**Seat:** Builder  
**WO:** WO-NAV-012 — SP-13 (candidate_surfaces in world_dict)  
**Date:** 2026-08-27  
**Authority:** Released by Architect 2026-08-27 (WO-NAV-010 ✅ + WO-NAV-011 ✅)

**Scope note:** SP-25 and SP-26 are NOT in this WO — gated on Design/MT DM-2/DM-3 measurements (still outstanding). SP-13 only.

---

## D-1 — SP-13: candidate_surfaces in world_dict ✅

`runtime/executive_context.py` — added after significance_score block:

```python
# SP-13 (WO-NAV-012): candidate_surfaces
_all_cands = generate_candidates(body_win_id, surface_edges, win_id_to_surface, jump_px, route_history)
_reachable = [c for c in _all_cands if c.reachable]
_reachable.sort(key=lambda c: (-c.route_confidence, c.horizontal_gap))
world_dict["candidate_surfaces"] = [dict(c[:10]) for c in _reachable]  # max 10
```

Each entry: `{target_win_id, horizontal_gap, euclidean_gap_px, requires_verb, route_confidence}`.

- Empty list when `body_win_id == -1` (mid-hop / L3-NAV-3)
- Filtered: `reachable=True` only
- Sorted: `route_confidence DESC`, `horizontal_gap ASC`
- Capped: top 10

---

## ATs — 7/7 PASS ✅

```
python3 -m pytest tests/test_wo_nav012_candidate_surfaces_world_dict.py -v
7 passed in 0.04s
```

AT-1 candidate_surfaces key present ✅  
AT-2 body_win_id=-1 → empty list ✅  
AT-3 only reachable candidates included ✅  
AT-4 sorted by route_confidence DESC ✅  
AT-5 capped at 10 ✅  
AT-6 candidate dict has all required keys ✅  
AT-7 candidate_surfaces in executive_context world_dict (integration) ✅  

**Full regression:** 53/53 PASS across SP-31/32, SP-38, NAV-009, NAV-010, NAV-011, NAV-012 test suites.

---

## Alignment check

- **Architecture:** candidate_surfaces in world_dict = Executive can now read and reason about reachable surfaces on each turn
- **Scope:** no SP-25/26 — separate WO pending DM-2/DM-3
- **Next:** WO-NAV-012b (SP-25 + SP-26) when DM-2/DM-3 arrive from Design/MT

*Builder · 2026-08-27*
