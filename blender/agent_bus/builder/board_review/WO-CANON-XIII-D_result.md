# CANON-XIII §D — Python Route Injection — RESULT: IMPLEMENTED
**Status:** §D additive route injection complete (commit df9efbc). §E parity gate in place.
**Evidence:** `engineering/evidence/SPATIAL/WO-CANON-XIII_D_route_injection.md`

---

## Summary

§A–§C confirmed built and passing.

§D implemented:
- `leg_to_dict()`, `route_to_list()` — route serialisation for move_command
- `_nearest_surface_in_direction()` — cardinal direction → nearest Surface
- `route_for_direction()` — §D entry-point: elo position + direction → Route|NoRoute
- server.py §D wire: on move intent, inject Python route into `_mv_intent["route"]` + `issued_by="SpatialFaculty"`

Additive — direction field preserved, Unity fallback intact.

§E (EloDesktopNav retirement) precondition: `test_xi_ad2_parity_proven` must go green.
WO-CANON-XI-UNITY-ROUTE (Design seat) delivers the unity_route ACK field that enables parity comparison.

3023 tests pass, 0 regressions.

Builder 1 · 2026-10-05
