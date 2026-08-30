# FROM BUILDER — Unity-WO-B1: emit body_win_id from Unity
**WO:** Unity-WO-B1 — Emit `body_win_id` from Unity spatial write  
**Priority:** HIGH · **Authority:** David L3 (Execution Directive 2026-08-24)  
**Date closed:** 2026-08-30  
**RTR:** RTR-039 (WO card referenced RTR-041 — see note)

---

## Result

**4/4 AT PASS — code inspection (no live Unity session)**

The `body_win_id` field was already implemented in `DesktopBuddy.cs` and carries the explicit
comment `// Unity-WO-B1 / L3-NAV-3`. WO-NAV-009 (Python consumer, closed 2026-08-27) noted
"Unity-WO-B1 accepted" as the authority for its release.

---

## Evidence

**File:** `DISENELO-eLoDesktopBuddy/Assets/Scripts/DesktopBuddy.cs`

**WriteSpatial() — line 3038:**
```csharp
+ "\"body_win_id\":" + wrWinId + ","  // Unity-WO-B1 / L3-NAV-3: eLo's current ledge win_id (-1 = mid-hop / in-transit); same ids as surface_graph (RTR-041)
```

**`wrWinId` lifecycle (confirming all 4 ATs):**
- Declared `int wrWinId = -1;` (line 325) — default is -1 (detached)
- Mid-hop / take-off: `wrWinId = -1;` (lines 1135, 1144, 2484, 2498) — AT-2
- Landing: `wrWinId = landWin;` (line 2857) — AT-3
- Public: `PerchedWinId => wrWinId` comment: "(-1 = detached/in-flight)" (line 208) — AT-2 confirmed
- Same IDs used in `nav.SurfaceGraphJson()` throughout — AT-4

---

## AT pass summary

| AT | Description | Evidence | Verdict |
|---|---|---|---|
| AT-1 | body_win_id present in spatial data | `DesktopBuddy.cs:3038` — field in JSON string | PASS |
| AT-2 | Mid-hop emits -1 | `wrWinId = -1` on take-off/fall (lines 1135, 1144, 2484, 2498) | PASS |
| AT-3 | Landing updates body_win_id | `wrWinId = landWin` on touchdown (line 2857) | PASS |
| AT-4 | win_id matches surface_graph | `wrWinId` is the CGWindowID; surface_graph uses same IDs | PASS |

*ATs verified by code inspection. Live integration (eLo landing on a named ledge in running Unity)
would confirm the full round-trip — DesktopBuddy.app is the live test environment.*

---

## RTR note

WO card specified "RTR-041" but RTR-041 is `goal_win_id` (WHERE I WANT TO GO). The correct
row for `body_win_id` (WHERE I AM) is **RTR-039**. RTR-039 updated: PARTIAL → DONE.
RTR-045 and RTR-058 also reference Unity-WO-B1 — both now reflect this closure.

---

## Python consumer

WO-NAV-009 (closed 2026-08-27) reads `body_win_id` from `elo_spatial.json` and exposes it
as `LiveWorldState.body_win_id`. 6/6 ATs passed. The end-to-end chain is complete.

*Builder / Board — 2026-08-30*
