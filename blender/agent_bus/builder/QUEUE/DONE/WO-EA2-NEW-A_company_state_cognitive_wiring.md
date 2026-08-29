# WO-EA2-NEW-A — Company State → One Brain Cognitive Wiring
**Seat:** Builder  
**Date issued:** 2026-08-27  
**Authority:** David L3 — Initiative 01 directive 2026-08-27  
**Source:** `docs/architecture/findings/INITIATIVE_01_BOARD_AUDIT_2026-08-27.md` §4 Gap A + §7 NEW-A  
**Depends on:** WO-EA2-1 MT verified (soft — schema confirmation). Begin after WO-EA2-1 MT result received. If EA2-1 PASS, schema confirmed. If EA2-1 has defects, check they do not affect `company_state.json` key structure before starting.  
**Non-scope:** Frozen cognitive kernel (LAW-017 / FREEZE_V1_LOCK — executive.py untouched). No new faculty. No new planner. No voiced_briefing string passed as direct LLM output. eLo synthesises from structured data, not from the briefing string.

---

## Intent

David's intent (Initiative 01 §4): **"how's the company today?" → eLo reads company_state → Executive understands state → eLo responds in its own identity.**

Currently: `company_state.json` is written live by `company_state_writer.py`. The cognitive spine does not read it. eLo cannot answer "how's the company today?" through the cognitive layer — it produces a generic LLM response.

After this WO: `company_state.json` is read on each turn and made available in `world_dict` / `attention_in["world_state"]`, so the Executive reasons from live governed company data.

---

## What this WO builds

**One deliverable: wire `company_state.json` into the world-state turn assembly, so its contents reach `attention_in["world_state"]["company_state"]`.**

Pattern: exactly analogous to how `elo_spatial.json` feeds `LiveWorldState` → `assemble_world_state()` → `attention_in["world_state"]`.

---

## D-1 — Read `blender/company_state.json` in world state assembly

Location: `world/live_world_state.py` — `assemble_world_state()` (or equivalent assembly function).

Behaviour:
- Read `blender/company_state.json` on each call.
- If file absent or malformed: return empty dict `{}` — do not raise; this must be fault-tolerant.
- Extract and include the following fields in the assembled world state (under key `company_state`):
  - `today_priorities` (list)
  - `waiting_for_approval` (list)
  - `blocked` (list or string)
  - `roadmap` (string or dict)
  - `board` (string or dict)
  - `voiced_briefing` (string — available for eLo to reference, but NOT to be used as a direct response; eLo synthesises from the structured data)
- The `company_state` key must appear in `assemble_world_state()` output and flow through to `attention_in["world_state"]["company_state"]`.

Constraint: **Do NOT include `money` or `seats_sample` fields in the first pass** — those contain sensitive data and their exposure to the LLM layer requires a separate Board ruling. Pass only the programme-state fields above.

---

## D-2 — `LiveWorldState` field

Add `company_state: dict` field to `LiveWorldState` dataclass (default `{}`).

This follows the pattern of `capability_results`, `surface_edges`, `win_id_to_surface`, etc. — all additive fields that did not exist at the start of the navigation wave.

---

## D-3 — `attention_in` inclusion in spine

Confirm `company_state` from `world.company_state` is included in `attention_in["world_state"]` in `runtime/spine/spine.py`.

This is the same pattern as `capability_results` (`:319–326`) and `candidate_surfaces`. It should be a one-line addition following the existing pattern.

---

## Acceptance Tests

**AT-1:** `LiveWorldState` has `company_state` field (dict, default `{}`).

**AT-2:** `assemble_world_state()` reads `blender/company_state.json` and returns `company_state` in the output dict containing at minimum `today_priorities`, `waiting_for_approval`, `blocked`, `roadmap`, `voiced_briefing`.

**AT-3:** File absent or malformed → `company_state` returns `{}` (no raise, no crash).

**AT-4:** `attention_in["world_state"]["company_state"]` is present after a spine turn with a valid `company_state.json` on disk.

**AT-5:** `money` and `seats_sample` are NOT present in `company_state` as exposed to `attention_in["world_state"]` (sensitive field exclusion confirmed).

**AT-6:** Frozen kernel untouched — `executive.py` diff is empty.

---

## Verification (Board/LA)

Board/LA independently confirms: `company_state` key present in `attention_in["world_state"]` after a turn, containing live fields from `company_state.json`. `executive.py` diff empty.

**This WO does NOT authorise:** capability registration for `company.*` intents (that is Gap B, covered by WO-EA2-2). This WO provides the world-state foundation that EA2-2's voice intents will use.

---

*Board / Lead Architect · 2026-08-27 · Authority: Initiative 01 Gap A · DISPATCH_BOARD NEW-A*
