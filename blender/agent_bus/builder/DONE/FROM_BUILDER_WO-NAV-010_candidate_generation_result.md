# FROM BUILDER — WO-NAV-010 Candidate Generation
**Seat:** Builder  
**WO:** WO-NAV-010 — SP-12 (Surface Identity Bridge) + SP-11 (Candidate Generation)  
**Date:** 2026-08-27  
**Authority:** Released by Architect 2026-08-27 (WO-NAV-009 ✅ + Unity-WO-B1 accepted)

---

## D-1 — SP-12: Surface identity bridge ✅

`world/navigation.py` (NEW) — `build_surface_index(surfaces: tuple) → dict[int, surface_dict]`.

Extracts integer win_id from `"win-N"` string id on each surface node.
Called at LiveWorldState assembly time; result stored in `LiveWorldState.win_id_to_surface`.

---

## D-2 — SP-11: Candidate dataclass ✅

`world/navigation.py` — `Candidate` dataclass:
```python
@dataclass
class Candidate:
    target_win_id: int
    horizontal_gap: float
    euclidean_gap_px: float
    requires_verb: str
    reachable: bool
    route_confidence: float
```

---

## D-3 — SP-11: generate_candidates() ✅

`world/navigation.py` — `generate_candidates(body_win_id, surface_edges, surface_index, jump_px, route_history) → list[Candidate]`.

- Returns `[]` immediately when `body_win_id == -1` (mid-hop / L3-NAV-3)
- Traverses `surface_edges` for edges where `from == f"win-{body_win_id}"`
- Phase 2: excludes `kind="overhang"` and `kind="wall"` nodes
- Horizontal gap = `target_rect_px[0] - (source_rect_px[0] + source_rect_px[2])` (L3-NAV-1)
- Reachability: `horizontal_gap <= jump_px AND requires_verb truthy`
- `route_confidence` from SP-14 via `self.route_memory.route_confidence_by_win_id`; default 0.5

---

## D-4 — LiveWorldState fields ✅

`world/live_world_state.py`:
- `surface_edges: tuple` — raw edge list from `surface_graph.edges`, assembled each turn
- `win_id_to_surface: dict` — SP-12 bridge, built via `build_surface_index()` at assembly

Both are fail-quiet (empty on read error).

---

## ATs — 10/10 PASS ✅

```
python3 -m pytest tests/test_wo_nav010_candidate_generation.py -v
10 passed in 0.06s
```

AT-1 surface index maps integer key ✅  
AT-2 lookup returns correct surface ✅  
AT-3 empty surfaces → empty index ✅  
AT-4 unparseable id → silently skipped ✅  
AT-5 body_win_id=-1 → empty list (L3-NAV-3) ✅  
AT-6 reachable within jump_px / unreachable present as Candidate ✅  
AT-7 overhang excluded from candidates ✅  
AT-8 unreachable candidate has reachable=False ✅  
AT-9 no edges from body → empty list ✅  
AT-10 LiveWorldState has surface_edges + win_id_to_surface fields ✅  

---

## Alignment check

- **Intent preserved:** SP-12 (Surface bridge) + SP-11 (candidate generation) — both built per spec contract
- **Architecture:** `world/navigation.py` is the right module; no circular imports; LiveWorldState owns the data
- **Scope:** no SP-13 (candidate_surfaces in world_dict) — that is WO-NAV-012 after WO-NAV-010+011 complete
- **Next:** WO-NAV-012 (SP-13 + SP-25 + SP-26) when WO-NAV-011 also complete

*Builder · 2026-08-27*
