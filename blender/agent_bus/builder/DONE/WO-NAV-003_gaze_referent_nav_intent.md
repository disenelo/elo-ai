# WO-NAV-003 — Gaze Wiring + Referent Resolver + Navigation Intent Category
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 independent; can run parallel to WO-NAV-001  
**RTR:** RTR-044 (gaze wiring), RTR-045 (nav intent), RTR-046 (referent resolver)  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` — SP-6, SP-16, SP-17

---

## Context

These three items are independent of each other and of WO-NAV-001. They establish:
- The live gaze signal in world_dict (SP-6) — prerequisite for referent resolver
- The navigation intent category in intent_engine (SP-16) — prerequisite for navigate handler (SP-18, later)
- The referent resolver that maps speech deixis ("that platform", "over there") to a win_id (SP-17) — depends on SP-6

All three should be built in order: SP-6 → SP-17 (SP-6 first, then SP-17), SP-16 (independent).

---

## Deliverables

### D-1 — SP-6: Wire `GazeState.win_id` → `world_dict`
**File:** `runtime/executive_context.py`  
**Contract:** The current `win_id` from `GazeState` (or equivalent live gaze data) must be written into `world_dict` under the key `gaze_win_id`. This is one field addition to the world assembly pass.  
**Authoritative source:** `elo_spatial.json` gaze dict (already read at runtime — verify what key the current code reads, and confirm `win_id` is available).  
**Constraint:** Do not change GazeState structure. Only wire the existing field to world_dict.

### D-2 — SP-16: Navigation intent category in `intent_engine.py`
**File:** `runtime/router/intent_engine.py`  
**Contract:** Add a navigation intent pattern to the intent classification step. Navigation intent pattern must:
- Match phrases like "go to [location]", "jump to [platform]", "move to [target]", "navigate to [X]"
- Classify as intent category `"navigation"` (or the canonical intent category name already used in the system — verify before adding)
- Be placed BEFORE the catch-all pattern in the classification order (so it fires before generic intent)
- Not change any other intent category

**Constraint:** Do not modify the Executive or any code that depends on intent classification. Only add the pattern to the existing classification step.

### D-3 — SP-17: Referent resolver (speech deixis → win_id)
**File:** `runtime/router/intent_engine.py` or a new helper `runtime/referent_resolver.py` (Builder's choice — prefer the existing file if clean)  
**Contract:** A function that takes a natural-language referent ("that ledge", "over there", "the platform I'm looking at") and resolves it to a `win_id` from world_dict, using `gaze_win_id` as the primary signal.

Minimal resolution logic:
- Proximal deixis ("this", "here", "that") → `gaze_win_id` from world_dict
- Named surface → search `elo_spatial.json` surface_graph for label match
- If unresolvable → return `None` (caller handles)

**Constraint:** Referent resolver reads world_dict and elo_spatial.json only. It does not call the Executive, it does not call the LLM. It is a pure lookup function.

---

## Forbidden Scope

- No changes to `executive.py` or any file under the FREEZE_V1_LOCK
- No changes to GazeState data structure
- No changes to Unity side
- No new intent categories beyond `"navigation"`
- No changes to movement, ACK, or consequence chain

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | SP-6: gaze_win_id in world_dict | After gaze event, world_dict contains `gaze_win_id` with the correct platform id |
| AT-2 | SP-16: navigation intent fires | "go to that platform" classifies as navigation intent, not generic |
| AT-3 | SP-16: catch-all still fires for non-nav | "how are you doing" still routes correctly to non-navigation intent |
| AT-4 | SP-17: proximal deixis resolves | "that platform" → returns current `gaze_win_id` value from world_dict |
| AT-5 | SP-17: unresolvable returns None | "the invisible ledge" → returns None (does not raise, does not crash) |

---

## RTR Traceability

After implementation, update the relevant RTR entries in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-044: add WO-NAV-003, commit, AT-1 pass
- RTR-045: add WO-NAV-003, commit, AT-2/AT-3 pass
- RTR-046: add WO-NAV-003, commit, AT-4/AT-5 pass

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Commit:** 86fb000  
**Tests:** AT-1 through AT-5 — **13/13 PASS** (including sub-cases)

| Deliverable | File | Status |
|---|---|---|
| D-1 SP-6: gaze_win_id → world_dict | `runtime/executive_context.py` line 209 | ✅ |
| D-2 SP-16: navigation intent pattern | `runtime/router/intent_engine.py` before catch-all | ✅ |
| D-3 SP-17: referent resolver | `runtime/referent_resolver.py` (new file) | ✅ |

**RTR updates required:** RTR-044, RTR-045, RTR-046 — add WO-NAV-003 + commit 86fb000 + AT results.  
**Constraints obeyed:** Executive, GazeState structure, Unity side, movement/ACK/consequence chain — not touched.  
**RTR update:** Architect/Board lane (Builder reports, not writes RTR).
