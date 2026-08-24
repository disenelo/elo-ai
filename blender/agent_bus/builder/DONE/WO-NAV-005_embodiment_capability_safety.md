# WO-NAV-005 — Embodiment Capability Safety
**From:** Board / Lead Architect  
**To:** Builder  
**Authority:** David L3 — Execution Directive 2026-08-24  
**Date issued:** 2026-08-24  
**Priority:** HIGH — Wave 1 independent  
**RTR:** RTR-049  
**SPEC basis:** `specs/SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` — SP-35, SP-37, SP-36

---

## Context

Currently the capability faculty does not know what embodiment eLo is operating in. Capabilities like `jump`, `navigate`, `reach_physical_object` only exist in some embodiments. Without an embodiment scope filter, the Executive could attempt to call a physical capability when eLo is running in a non-physical embodiment.

This WO adds the embodiment safety layer in three steps: SP-35 (tag capabilities with their scope) → SP-37 (put current_embodiment in world_dict) → SP-36 (filter capabilities by scope before offering to Executive).

---

## Deliverables

### D-1 — SP-35: `embodiment_scope: frozenset` on `Capability` dataclass
**File:** `runtime/capability.py`  
**Contract:**
- Add field `embodiment_scope: frozenset = frozenset({"desktop"})` to the `Capability` dataclass
- Default value: `frozenset({"desktop"})` — so all existing capabilities default to desktop-only without requiring individual updates
- Canonical embodiment identifiers: `"desktop"` · `"robot"` · `"phone"` · `"game"` · `"ar"` · `"any"` (use `"any"` for capabilities valid in all embodiments — e.g. language capabilities)
- Update the capability definitions for existing capabilities with appropriate scope values (Builder judges which capabilities are desktop-only vs. universal)

### D-2 — SP-37: `current_embodiment` in `world_dict`
**File:** `runtime/executive_context.py`  
**Contract:**
- Add `current_embodiment` to world_dict during world assembly
- Source: the current embodiment identifier string — check how this is currently tracked in the system (look for EloSelfState or equivalent)
- Default: `"desktop"` if not otherwise specified
- Value type: `str` matching the embodiment identifier set above

### D-3 — SP-36: Filter `_capability_faculty()` by `embodiment_scope`
**File:** wherever `_capability_faculty()` or the capability list is assembled for the Executive  
**Contract:**
- Before capabilities are offered to the Executive, filter them: only offer capabilities whose `embodiment_scope` contains `world_dict["current_embodiment"]` or `"any"`
- This is a safety filter — wrong-embodiment capabilities never reach the Executive's decision space

**Constraint:** This filter does not change Executive logic. It operates before the Executive sees the capability list.

---

## Forbidden Scope

- No changes to `executive.py` or FREEZE_V1_LOCK files
- No changes to capability invocation — only filter which capabilities are offered
- Do not change any existing capability behaviour

---

## Verification

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | embodiment_scope field exists | All Capability objects have `embodiment_scope` frozenset field |
| AT-2 | desktop-only capability blocked | A capability tagged `frozenset({"robot"})` does not appear in the capability list when `current_embodiment = "desktop"` |
| AT-3 | universal capability passes | A capability tagged `frozenset({"any"})` appears in all embodiment contexts |
| AT-4 | current_embodiment in world_dict | world_dict contains `current_embodiment` with value `"desktop"` (or current actual embodiment) |
| AT-5 | Existing capabilities unaffected | All current desktop capabilities remain available when current_embodiment = "desktop" |

---

## RTR Traceability

After implementation, update RTR-049 in `RECOVERY_TRACEABILITY_REGISTER_2026-08-24.md`:
- RTR-049: add WO-NAV-005, commit, AT-1 through AT-5 pass

---

*Board / Lead Architect — 2026-08-24*  
*Authority: David L3 — Execution Directive 2026-08-24*

---

## Result — Builder 2026-08-24

**Commit:** f3f5ff7  
**Tests:** AT-1 through AT-5 — **10/10 PASS**

| Deliverable | File | Status |
|---|---|---|
| D-1 SP-35: `embodiment_scope: frozenset` on `Capability` | `runtime/capabilities/capability.py` | ✅ |
| D-2 SP-37: `current_embodiment` in `world_dict` | `runtime/executive_context.py` | ✅ |
| D-3 SP-36: embodiment scope filter in `_capability_faculty()` + call site | `runtime/spine/spine.py` | ✅ |

**Default:** `frozenset({"desktop"})` — all existing capabilities default to desktop-only; `"any"` for universal  
**Source for current_embodiment:** `EloSelfState.embodiment` via try/except; default `"desktop"`  
**Regression:** WO-111 ack contract — 12/12 PASS  
**Constraints obeyed:** `executive.py` not touched, capability invocation not changed, existing capability behaviour unchanged
