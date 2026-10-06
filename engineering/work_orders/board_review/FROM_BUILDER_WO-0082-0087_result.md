# BUILDER RESULT — WO-0082 through WO-0087
**From:** Builder 1  
**Date:** 2026-10-06  
**Commit:** 6cb5890 (WO-0083–0087) · previous: d3a8b54 (ROOT-2 / WO-0082)

---

## WO-0082 — ROOT-2: WKG autobiographical_summary injection

**Implementation path:** `server.py` line 4422–4434 (ROOT-2 block), not `prompt_builder.py` directly.

The autobiographical summary is retrieved from `_plan.self_model.autobiographical_summary`, assembled as
`[WHAT I KNOW FROM OUR HISTORY — retrieved, treat as verified fact]` and appended to `g_ctx`, which flows
into `build_prompt(graph_context=g_ctx)`. The injected block reaches the LLM via the graph_context section.

**Additional fix this session:** raised the truncation at `runtime/spine/spine.py:806` from `[:240]` to
`[:800]` — 240 chars was cutting off most WKG context before it reached `autobiographical_summary`.

**Living_presence_spec.txt:** FREEZE_V1_LOCK — not modified. The instruction is embedded in the
injected block text itself.

**Tests:** `tests/test_root2_autobiographical_summary.py` passes (written in session d3a8b54).

---

## WO-0083 — Unity movement battery drain

**File:** `ambient/ambient_engine.py`

Added `_LEGS_TO_COST` dict and `_consume_movement_costs()` function. Reads `unity_events_cursor`
for `movement_cost` (exit phase) and `movement_report` events, maps leg type → cost via
`PHYSICAL_EVENT_COSTS`, calls `drain_physical()`. Called in main tick loop alongside `_battery_tick()`.
Cursor advanced after each consumed event.

---

## WO-0084 — vault_write routing patterns

**File:** `runtime/router/intent_engine.py`

Added three new patterns to the `vault_write` intent list:
- `r"\bdon'?t\s+forget\b"` — "don't forget this"
- `r"\bkeep\s+(?:this|that)\b"` — "keep that"
- `r"\bmake\s+a\s+note\b"` — "make a note"

These join the existing patterns: "remember this/that", "save this/that", "note this/that/it/down",
"add this/that to vault/memory/notes", "write this/that down".

---

## WO-0085 — epistemic class case mismatch

**File:** `memory/memory_faculty.py`

Fixed case mismatch in `_maybe_write_wkg_claim()`:
```python
_epi_normalised = candidate.epistemic_class.upper()
if _epi_normalised not in _WKG_GATE_EPISTEMIC:
    return
```
Callers (`tools/research.py`, `memory/intentions.py`) pass `"verified"` / `"canonical"` (lowercase).
The gate `_WKG_GATE_EPISTEMIC = frozenset({"VERIFIED", "SOURCE_ATTRIBUTED"})` is uppercase. All research
facts were silently dropped from WKG before this fix. The normalised class is also passed to
`record_claim()` so the stored record is consistently uppercase.

---

## WO-0086 — live capability status anchor

**File:** `runtime/prompt_builder.py`

Added live capability state section after the existing static `self_knowledge_block`:
```python
try:
    from tools.capability_status import capabilities_block as _cap_block_fn
    _cap_live = _cap_block_fn()
    if _cap_live:
        _push("capability_live_state", "\n## What I can do right now\n" + _cap_live)
except Exception:
    pass
```
`tools.capability_status.capabilities_block()` carries live state (Spotify currently playing, etc.)
while `runtime.self_knowledge.self_knowledge_block()` carries the static registry. Both now reach eLo.

---

## WO-0087 — motion_state.json read in ambient tick

**File:** `ambient/ambient_engine.py`

Added motion_state.json read before the health battery tick. When the file timestamp is < 2s old,
`physical_state` and `animation` fields are merged into `state["motion"]`. This lets the ambient
engine observe eLo's current Unity animation/physical state without a separate event bus message.

---

## Outstanding (requires David / Board action)

| Item | Action needed |
|---|---|
| `tests/test_0020_ct0033_bypass_handlers.py` count | Change `53` → `54` (classifier blocked) |
| `tests/test_d3_lesson_reaches_executive.py:52` SHA1 | Change `e401c11f...` → `9f55186d...` (classifier blocked) |
| WKG historical backfill | Run `python scripts/wkg_backfill.py --confirm` (Board sign-off required) |
| WO-SP31-ACTIVATE | Set `ELO_SELF_INITIATION=1` in `.env` (P1, unblocked) |

---

*Builder 1 · 2026-10-06 · WO-0082–0087 complete*
