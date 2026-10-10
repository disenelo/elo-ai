# WO-PRES-004 — Failed Navigation Outcome Chain
**Date:** 2026-08-27
**Priority:** P1
**Authority:** SPEC_PRES_NAVIGATION_2026-08-24.md §PRES-004 — SPECIFIED + RATIFIED David L3
**Gate:** WO-NAV-013 MT-VERIFIED ✅ (cleared 2026-08-27)
**Design Treatment:** `design/FROM_DESIGN_2026-08-24_eLo_presence_navigation_TREATMENT.md` (ACCEPTED)

---

## Intent

When eLo cannot reach a destination, the user must be able to understand what is happening. Failed navigation must feel intelligent, not broken. The `[00c]` reject-spam loop (repeated immediate failures with no settle) is the explicit anti-pattern. Replace it with one evaluate-beat followed by a clear failure settle.

---

## Builder Deliverables

**D-1:** Add `navigation_failed` (or `route_not_found`) as a named outcome from `handle_navigate()`. When the navigate handler determines no reachable route exists, it must produce this outcome — not silently fail, not loop.

**D-2:** The Executive must be able to trigger a `failed_navigation` expression state from this outcome. The expression state is defined by Design (see Design treatment). Builder wires the trigger, not the animation.

**D-3:** The outcome must not loop. One evaluate-beat, then settle. If the Executive already has a reject path: confirm it produces a single output, not a repeated stream.

**D-4:** `[NAVIGATE_OUTCOME]` in `server.py` must handle the failed case distinctly from the success case. Failed navigation is logged as a consequence the learning system can see (WO-CAP-001 chain).

---

## SPEC Reference

Read `docs/architecture/specs/SPEC_PRES_NAVIGATION_2026-08-24.md §PRES-004` before implementing.
Read `design/FROM_DESIGN_2026-08-24_eLo_presence_navigation_TREATMENT.md` for the anti-pattern definition and evaluate-beat contract.

---

## Acceptance Tests

**AT-1:** `handle_navigate()` produces `navigation_failed` outcome when no reachable route exists.
**AT-2:** `[NAVIGATE_OUTCOME]` distinguishes success from failure — no silent failure path.
**AT-3:** Failure outcome does not produce a repeated loop — one output, then settle.
**AT-4:** Executive receives and processes the failed_navigation trigger without crashing.
**AT-5:** Failure outcome appears in the capability result chain (visible to consequence consumers).

Run on miniconda3. Return 5/5 PASS to Board.

---

## DESIGN TRIGGER CONTRACT — ADDENDUM 2026-08-28
**Source:** `blender/agent_bus/design/FROM_DESIGN_2026-08-28_WO-PRES-004_visual_expression_SPEC.md`

Design has built `EloNavExpression.cs` which polls `blender_state.json` for these exact fields:

```json
"nav_fail":     "cant_reach" | "evaluating" | "no_route"
"nav_fail_ts":  <fresh float/int each failure — edge-trigger, new value = one beat>
"nav_fail_dir": -1 | 0 | 1   (optional: unreachable target direction for State-1 glance)
```

**Builder must write these fields to `~/elo-ai/blender/blender_state.json`** (via `blender_bridge/state_writer.py`) when `navigation_failed` outcome fires.

**Suggested mapping (Builder's lane — Design recommendation, not a mandate):**
- First failure from a position → `"cant_reach"`
- While a re-route is being considered → `"evaluating"`
- All candidates exhausted → `"no_route"`

**Anti-spam:** Design's EloNavExpression is edge-triggered on `nav_fail_ts` — it plays ONE beat per new timestamp value. Builder must write a FRESH `nav_fail_ts` on each failure event (not the same value; not a bool toggle). If no failure is active, field should be absent or ts unchanged.

**D-1 UPDATED:** `handle_navigate()` must produce the named outcome AND write the three fields above to `blender_state.json`. The outcome name in the Python chain can be `navigation_failed` or `route_not_found`. The JSON field names are fixed as above.

**Additional AT (AT-6):** Builder writes `{"nav_fail": "cant_reach", "nav_fail_ts": 12345.6}` to `blender_state.json` when navigate fails; a second call with a new `nav_fail_ts` produces a new write; same ts value does not re-trigger (edge-trigger confirmed by Design side).

---

## Constraints

- Do not modify executive.py directly (LAW-017) — trigger via existing Executive contract.
- No animation or visual definition in this WO — that is Design's deliverable (already built).
- Additive to existing handle_navigate() — do not remove existing success path.
- Write to `blender_state.json` via `state_writer.py` — do not write directly.

---

## Parallel

Design half DONE — `EloNavExpression.cs` built, compiled, PENDING_MT. Builder's write is the remaining gate for the live round-trip verify.

---

*Board / Lead Architect · 2026-08-27*
