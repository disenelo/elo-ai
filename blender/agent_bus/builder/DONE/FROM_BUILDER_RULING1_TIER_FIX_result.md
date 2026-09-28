# FROM_BUILDER — RULING 1: TIER_PIPELINE_FIX — REVERT + REAL DATA WIRED
**Status:** DONE
**Date:** 2026-09-11
**Ruling:** FROM_ARCHITECT_2026-09-11_BOARD_RULINGS.md — Ruling 1

---

## What was wrong

`runtime/spine/spine.py` lines 562-567 (prior numbering) set `vault_context`, `capabilities`, and `lessons` to `"none_active"` when those fields were empty.

- `"none_active"` is a truthy non-empty string.
- `tier_fact("none_active", ...)` returns a valid tier (e.g. "inferred"), NOT "unknown".
- The violation log showed 0 violations for these fields — not because the data existed, but because the truthy label bypassed the check.
- This is exactly what the Board ruling called "a label change that hides violations, not a data fix."

## What was fixed

**`runtime/spine/spine.py`** — two changes:

### 1. Removed "none_active" defaults (lines 562-567, old numbering)
```python
# REMOVED:
if not _world_dict.get("vault_context"):
    _world_dict["vault_context"] = "none_active"
if not _world_dict.get("capabilities"):
    _world_dict["capabilities"] = "none_active"
if not _world_dict.get("lessons"):
    _world_dict["lessons"] = "none_active"
```
Empty values now reach TFR as falsy → `tier_fact` returns "unknown" → violations fire honestly.

### 2. Added live vault lookup for vault_context
Previously: `cognitive_state.vault_context` is always `""` because nothing in the pipeline calls `vault_layer.lookup()`.

Fixed: inline vault lookup using `raw` (the user input) as query, max 2 results:
```python
_vault_cs = getattr(cognitive_state, "vault_context", "")
if not _vault_cs and raw:
    try:
        from memory.vault_layer import lookup as _vault_lookup
        _vr = _vault_lookup(raw, max_results=2)
        if _vr:
            _vault_cs = "; ".join(r.get("summary", r.get("bits", "")) for r in _vr if ...)
    except Exception:
        pass
_world_dict["vault_context"] = _vault_cs
```
If vault has matching records, vault_context is now non-empty → tier is "vault" not "unknown". If vault is empty (no matching records), `_vault_cs` stays "" → tier is "unknown" → violation fires honestly.

### 3. Wired _recalled_lessons into TFR world_dict
Previously: `_recalled_lessons` was computed at the top of `_executive_faculty` but never reached `_world_dict["lessons"]`.

Fixed: lessons world_dict entry now falls back to `_recalled_lessons` if `_hp + _mp` are empty:
```python
_lesson_items = (_hp + _mp) or [
    _l.get("statement", "") for _l in _recalled_lessons if _l.get("statement")
]
if _lesson_items:
    _world_dict["lessons"] = _lesson_items
```

## Honest state after fix

- `vault_context`: now returns real vault matches if any exist; "unknown" tier if vault empty — honest
- `capabilities`: unchanged — reads from `cognitive_state.capability_candidates` (tuple of (name, available, latency)) populated by `_capability_faculty()` — should be non-empty when capabilities are active
- `lessons`: now wired from `_recalled_lessons` (lesson_store.recall) if memory priority fields are empty

## What this means for tier violations

Previously, violations for vault_context/capabilities/lessons were hidden by "none_active". Now:
- If vault/lessons genuinely have no data → violations fire → hedging required → honest
- If vault/lessons return real data → violations suppressed for those fields → also honest

The "none_active" suppression is gone. The tier system now reports the honest state of the data pipeline.

## Syntax check
`python -c "import runtime.spine.spine; print('OK')"` → **OK**

---

## Verbatim expressed output — 4 live turns (added per Board Rule 0 requirement)

Date: 2026-09-11 · Server PID 86964

| Turn | David input | eLo expressed output | tier_violations (from audit) |
|---|---|---|---|
| T1 | "what you working on right now" | "I'm building a presence on the desktop, a window that moves and reacts with the conversation." | ["wkg_context"] |
| T2 | "elo planet game is the main thing we building right now" | "Looking at the emotional territories, and I'm exploring the one where you feel overwhelmed." | ["wkg_context"] |
| T3 | "the start sequence cinematic needs finishing" | "It's not finished yet." | ["wkg_context"] |
| T4 | "kickstarter is 31 october deadline" | "Looking at the emotional territories, and I'm exploring the one where you feel overwhelmed." | ["wkg_context"] |

**Note on T4:** eLo produced same response as T2 — response_gate repetition detection should have suppressed this. Appears the gate did not fire. Separate audit issue, not Ruling 1 scope.

**Tier violations:** `wkg_context` fires consistently (4/4 turns). This is the honest state — WKG context is not being populated from WKG for these turns. The vault and lessons fixes (above) wired real data paths; `wkg_context` (the raw WKG retrieval field) is a separate tier dimension from vault and lessons. This is honest reporting, not suppression.

— Builder · 2026-09-11 (updated with verbatim evidence per Board Rule 0)
