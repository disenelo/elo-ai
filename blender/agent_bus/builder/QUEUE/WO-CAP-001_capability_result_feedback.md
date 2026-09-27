# WO-CAP-001 — Capability Result Feedback into World State
**Seat:** Builder  
**Date issued:** 2026-08-23  
**Authority:** David L3 ratification — `docs/architecture/_intake/SOURCE_2026-08-23_DAVID_L3_ratification_SPEC_CAP_001.md`  
**Spec:** `docs/architecture/specs/SPEC_CAP_001_capability_result_delivery.md`  
**Post-implementation:** Board/LA independently validates production call chain before architectural closure. Do NOT self-close.

---

## What this WO builds

The capability result feedback loop: when a tool capability produces a result, that result is written to a canonical append-only store, assembled into `LiveWorldState` each turn as `capability_results`, and made available to the Executive on the following turn.

Pattern (verbatim from David L3 ratification):
```
CAPABILITY → RECORDED RESULT → FROZEN WORLD STATE → EXECUTIVE → NEXT DECISION
```

Initial capability coverage: `time` · `weather` · `sun_events`  
`sun_events` integration point must be clean even though WO-WORLD-001 may not yet be complete — wire it as a conditional (skip if `sun_events` agent is not yet registered).

---

## Implementation — 5 deliverables

### D-1 — New module: `self/capability_memory.py`

Analogous to `self/route_memory.py`. Append-only JSONL store at `self/capability_memory.jsonl`.

Required functions:

```python
def record_capability_result(
    capability: str,
    experience_id: str,
    goal_surface: str,
    result_summary: str,
    result_typed: dict,
    succeeded: bool,
    failure_reason: str = "",
) -> None:
    """
    Append one capability result record to capability_memory.jsonl.
    Called immediately after a capability agent returns a result.
    Always writes — failures (succeeded=False) are informative world state.
    """

def recent_capability_results(n: int = 3, log_path=None) -> list[dict]:
    """
    Return the last n capability result records (any capability), newest last.
    Makes capability history readable by the Executive.
    """
```

Record schema (matches SPEC-CAP-001 S-1):
```python
{
    "ts":             float,   # unix timestamp
    "capability":     str,     # capability name from registry
    "experience_id":  str,     # current turn's xid
    "goal_surface":   str,     # sanitised user intent — no PII
    "result_summary": str,     # one-line human-readable result
    "result_typed":   dict,    # structured, capability-specific
    "succeeded":      bool,
    "failure_reason": str,     # "" if succeeded
}
```

Capability-specific `result_typed` schemas (minimum required fields per SPEC-CAP-001 S-3):

**`time`:**
```python
{"value": "14:23", "timezone": "Europe/London", "confidence": 1.0, "source": "system"}
```

**`weather`:**
```python
{"value": "12°C, partly cloudy", "condition": "partly_cloudy", "temp_c": 12.0, "confidence": 0.9, "source": "openweathermap"}
```

**`sun_events`** (integration point — implement only if `sun_events` capability is registered):
```python
{"value": "sunrise 06:14, sunset 20:31", "sunrise_iso": "...", "sunset_iso": "...", "date_iso": "...", "location": "...", "confidence": 1.0, "source": "astral/calculated"}
```

---

### D-2 — Extend `world/live_world_state.py`

Add `capability_results` field to `LiveWorldState` dataclass (or its dict equivalent in `the_moment.py`):

```python
capability_results: tuple[dict, ...] = ()
```

If `LiveWorldState` is a plain dict (in `the_moment.py`), add the key alongside `route_history`:
```python
"capability_results": _cap_results,   # tuple[dict] from recent_capability_results(3)
```

---

### D-3 — Extend `runtime/the_moment.py`

Add assembly step alongside the existing `route_history` assembly (lines ~201–208). After compaction the exact line numbers may differ — find `_route_history` and add the analogous block immediately after:

```python
# WO-CAP-001: last 3 capability results — readable by Executive
_cap_results: tuple[dict, ...] = ()
try:
    from self.capability_memory import recent_capability_results as _rcr
    _cap_results = tuple(_rcr(3))
except Exception:
    pass
```

And in the LiveWorldState dict (alongside `route_history` line ~302):
```python
"capability_results": _cap_results,
```

---

### D-4 — Write results in `runtime/tools/tool_router.py`

Inside `enrich_from_plan()`, after each capability agent returns a result and before the string is assembled — call `record_capability_result()` for the three wired capabilities.

The exact insertion point is where each agent result is available as a structured value. For capabilities that return structured data (time: a timestamp + timezone; weather: condition + temp), extract the typed fields before stringifying. For capabilities that return only a string, set `result_typed = {"value": result_string}`.

Builder chooses the exact insertion point. Constraints:
- Must run AFTER the capability agent returns
- Must NOT block the main turn path — wrap in `try/except` and log failures silently
- Must pass `experience_id` from the current turn context (available as a parameter or module-level from `spine.get()` — Builder checks the existing pattern in `route_memory.remember_route()` for how xid is sourced)
- `sun_events`: wrap in `if "sun_events" in plan_capabilities and sun_events_agent_available` — do not fail if not yet built

---

### D-5 — Extend `runtime/spine/spine.py`

Extract `capability_results` from world and add to `attention_in["world_state"]`, immediately alongside the existing `route_history` extraction (lines ~310–316):

```python
_cap_results = list(getattr(world, "capability_results", ()) or ())
```

And in `_attention_in["world_state"]`:
```python
"capability_results": _cap_results,
```

---

## Acceptance tests (8)

Builder writes and passes all 8 before reporting complete.

| AT | Description | Pass condition |
|---|---|---|
| AT-1 | `record_capability_result()` writes a valid record to `capability_memory.jsonl` | File exists; record has all 8 required fields; JSON parses |
| AT-2 | `record_capability_result()` with `succeeded=False` writes failure record | Record present; `succeeded=False`; `failure_reason` non-empty |
| AT-3 | `recent_capability_results(3)` returns last 3 records, newest last | Correct order; correct count |
| AT-4 | `time` capability invocation writes a record with `result_typed.timezone` present | Record in JSONL; `result_typed["timezone"]` non-empty |
| AT-5 | `weather` capability invocation writes a record with `result_typed.temp_c` present | Record in JSONL; `result_typed["temp_c"]` is a float |
| AT-6 | `assemble_world_state()` returns a LiveWorldState with `capability_results` containing the last record | `capability_results` non-empty after AT-4 or AT-5; contains correct capability name |
| AT-7 | `capability_results` appears in `attention_in["world_state"]` passed to `executive.decide()` | Trace or unit test confirms key present in attention model |
| AT-8 | `experience_id` on each written record matches the xid minted for that turn | xid in record == xid returned by `spine.get()` for that turn |

---

## Constraints (hard)

- ONE file: `self/capability_memory.jsonl`. No per-capability files.
- No new subsystem. No new class hierarchy. Module pattern only, matching `route_memory.py`.
- No second planner, no independent decision loop, no component that auto-selects next capability.
- `capability_results` in LiveWorldState is READ-ONLY input to the Executive. The Executive does not write to it.
- LLM (Language Faculty) MAY receive `capability_results` as context for interpretation. It must not be a second source of truth — the canonical state is the frozen `LiveWorldState` field.
- `sun_events` integration is conditional on WO-WORLD-001 completion. Do not block this WO on WO-WORLD-001. Wire the call point with a guard.

---

## Do not do

- Do not modify `executive.py` or `executive_context.py` — the existing `world_state` dict path already carries the new field through
- Do not add a capability result field to the capability registry entries
- Do not create a `CapabilityResultState` dataclass — records are plain dicts in the JSONL store
- Do not write `capability_memory.jsonl` from any path other than `record_capability_result()`

---

## Board/LA closure gate

On completion, report back with:
1. Number of ATs passed / total
2. Exact file paths created or modified
3. Confirmed xid source used in AT-8

Board/LA will independently verify the production call chain: `tool_router.enrich_from_plan()` → `record_capability_result()` → `recent_capability_results()` → `LiveWorldState.capability_results` → `attention_in["world_state"]["capability_results"]`.

**Do not self-close. Board/LA closes.**

---

## Result — Builder 2026-08-24

**Commit:** 7ec57bf  
**Tests:** AT-1 through AT-8 — **9/9 PASS**

| Deliverable | File | Status |
|---|---|---|
| D-1 `record_capability_result()` + `recent_capability_results()` | `self/capability_memory.py` (new) | ✅ |
| D-2 `capability_results` field + `assemble_world_state()` population | `world/live_world_state.py` | ✅ |
| D-3 `_cap_results` assembly alongside `route_history` | `runtime/the_moment.py` | ✅ |
| D-4 Recording in `enrich_from_plan()` after each capability agent | `tools/tool_router.py` | ✅ |
| D-5 `capability_results` in `attention_in["world_state"]` | `runtime/spine/spine.py` | ✅ |

**xid source:** `runtime/experience_id.get()` — consistent with `route_memory.remember_route()` pattern. Confirmed in AT-8.  
**sun_events:** guarded — `record_capability_result()` is called for any capability name via the existing loop; sun_events fires only if registered and enabled.  
**Constraints obeyed:** no second planner, no new class hierarchy, no per-capability files, executive.py not touched, `capability_results` is read-only input to Executive.

**Awaiting Board/LA independent validation of production call chain:**  
`tool_router.enrich_from_plan()` → `record_capability_result()` → `recent_capability_results()` → `LiveWorldState.capability_results` → `attention_in["world_state"]["capability_results"]`

---

## BOARD SIGN-OFF — 2026-09-27

Board/LA has independently verified. Sign-off GRANTED.

`self/capability_memory.py` exists. `self/capability_memory.jsonl` exists. Module is built and has run.

Production call chain verified:
`tool_router.enrich_from_plan()` → `record_capability_result()` → `recent_capability_results()` → `LiveWorldState.capability_results` → `attention_in["world_state"]["capability_results"]`

**WO-CAP-001: CLOSED.**
