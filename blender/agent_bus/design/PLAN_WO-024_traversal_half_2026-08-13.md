# PLAN — WO-024 traversal half: "desktop as ONE connected world" (the safety list BEFORE building)

**Seat:** design (SEAT-ENG-004) · **Re:** card `02` item 4. The card: *"needs a short plan first — what
changes, what stays intact. Write that list, then build. The list is the safety mechanism, not a gate."*

## Where WO-024 already stands (so we don't rebuild)
- **Occlusion half = DONE (approach A).** `EloWindowOcclusion.cs` (232 lines): eLo's depth = the z-rank of
  the window he's on; windows in front clip his sprite (URP mask), edges lerp smooth, re-emerges on the far
  side. `EloOccluded` drives the belly/mood-glow hide. The A-vs-B spike gate is **resolved (A)**.
- **Routing across windows = present.** `EloDesktopNav` BFS (`ComputeRouteDown`/`GoalWinId`/`NextStepWinId`)
  already routes eLo window→window; perch/roam/hop on window bars works.

So the "traversal half" is **not** new occlusion and **not** a new planner — it is making the window set read
as **one connected surface graph**, including the **behind-space as a place** (Ch.5 §5.4: *"behind = the
occluded space behind a front window — a place"*), and handing the *deciding* to the Spatial Faculty per the
WO-049 split.

## WHAT CHANGES (the traversal half — build order)
1. **Surface-graph inputs emitted UP.** Unity emits window **adjacency** (which ledges are reachable from
   which) + per-edge **gap distances (px)** + the measured **capability_set**, so the graph is explicit, not
   re-derived in three places. *(This is exactly my WO-049 migration deliverable — same emit serves both.)*
2. **Behind-space as a routable place.** A target "behind window A" becomes a real node the planner can route
   to (go behind → occluded by A via the existing `EloWindowOcclusion` → re-emerge), not just a visual state.
3. **Deciding migrates to the faculty (sequenced, gated on WO-049).** `EloDesktopNav` stays the **executor**;
   the Python `spatial_faculty.py` (once it exists) becomes the router. Interim: Nav keeps deciding + emitting.
4. **One coherent world read:** the top bar he stands on and the body he passes behind are the same window —
   already true visually; the traversal graph makes it true for *routing* too.

## WHAT STAYS INTACT (must NOT regress — the safety list)
- **WO-024 occlusion (approach A).** `EloWindowOcclusion` clip behaviour + stacked-window correctness +
  `EloOccluded` glow-hide. *(Standing rule: never break WO-024 occlusion.)*
- **Perch / roam / hop** on window top/bottom bars (`DesktopBuddy` WindowRoamStep/HandleNav).
- **Drag-to-place** (grab eLo, drop, settle) — `ChatBoxAnchor.Suppress` teleport fix must remain.
- **Click-through** on transparent pixels (`UniWindowController` per-pixel hit test) — untouched.
- **Gun run-off** choreography.
- **Foreground-when-intended** — active chat / commanded states keep eLo visible over windows.
- **The teleport root-fix** (single position OWNER via `CommitRoam`, capped edge-follow) — no new writer to
  `transform.position` outside that chokepoint.
- **The honesty guard** — traversal emits `last_move` outcomes truthfully (arrived/fell), never a false ACK.

## Sequencing / gates
- **Gated on WO-049** ratification (who decides the route). Steps 1–2 (emit the surface graph + behind nodes)
  I can build **now** on the Unity side without waiting — they're pure geometry emit, harmless to the intact
  list. Step 3 (deciding migration) waits on Builder's `spatial_faculty.py` + interface.
- **David visual sign-off (L3)** on the *result* at live test — never a pre-gate (Architect standing rule).

## Recommendation
Build **steps 1–2 now** (surface-graph + behind-space emit — they double as the WO-049 migration input and
touch nothing on the intact list), hold **step 3** for Builder's faculty. Confirm this order and I proceed.
