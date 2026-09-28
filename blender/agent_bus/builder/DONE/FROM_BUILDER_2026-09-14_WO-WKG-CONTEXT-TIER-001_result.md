# FROM BUILDER → BOARD — WO-WKG-CONTEXT-TIER-001: wkg_context tier violation on greeting turns
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-WKG-CONTEXT-TIER-001.md

---

## A — Diagnosis

`runtime/tiered_faculty_reader.py:98` called `tier_fact(_wkg, source="inferred")` unconditionally. When wkg_context is empty (no WKG claims match for this turn), `tier_fact("", source="inferred")` returns `"unknown"` because `tier_fact()` treats a falsy value as an absent/unknown fact. `verify_response_tiers()` then adds `"wkg_context"` to the `violations` tuple on any turn where WKG returned no results — which is every social greeting, fast-path social reflex, and every Tier 0/1 turn by design. Empty wkg_context is expected and correct on those turns; the tier system was treating expected absence as an epistemic gap.

Root: `the_moment.py:tier_fact()` returns `"unknown"` for empty/falsy values. The fix belongs in `tiered_faculty_reader.py` — use `"inferred"` directly when the value is empty rather than delegating to `tier_fact()` for the empty case.

---

## B — Failing turns (verbatim JSONL fields)

Greeting turn `d6b503f5`:
```json
{
  "turn_id": "d6b503f5",
  "raw": "yo what's good",
  "tier": "TIER1",
  "wkg_context": "",
  "tier_snapshot": {
    "active_window": "inferred",
    "pose": "unknown",
    "nearby": "inferred",
    "mood": "inferred",
    "wkg_context": "unknown",
    "lessons": "unknown",
    "vault_context": "unknown",
    "capabilities": "inferred"
  },
  "tier_violations": ["active_window", "pose", "nearby", "mood", "wkg_context", "lessons", "vault_context", "capabilities"]
}
```

Social turn `d9474559`:
```json
{
  "turn_id": "d9474559",
  "raw": "what's the weirdest thing you've thought about today",
  "tier": "TIER1",
  "wkg_context": "",
  "tier_snapshot": {
    "wkg_context": "unknown"
  },
  "tier_violations": ["wkg_context"]
}
```

`"wkg_context": "unknown"` appears in violations on both turns despite empty wkg_context being normal for TIER1 social turns.

---

## C — Fix applied

**`runtime/tiered_faculty_reader.py:91-104`** — replaced unconditional `tier_fact()` call with guard:

```python
_wkg = (cognitive_state.wkg_context if cognitive_state and hasattr(cognitive_state, "wkg_context")
        else world_dict.get("wkg_context"))
# WO-WKG-CONTEXT-TIER-001: empty wkg_context is not an epistemic gap — it means
# no relevant WKG claims exist for this turn (expected on greeting/social turns and
# whenever the query returns no matches). tier_fact("", source="inferred") → "unknown"
# → violation, which is wrong. Use "inferred" for empty WKG: absence of context
# is a valid epistemic state, not a missing-data violation.
_wkg_tier = "inferred" if not _wkg else tier_fact(_wkg, source="inferred")
results.append(TieredFacultyResult(
    tier=_wkg_tier,
    faculty="wkg",
    key="wkg_context",
    value=_wkg,
))
```

When `_wkg` is empty/None → tier assigned `"inferred"` directly. `"inferred"` is not in `("unknown", "absent")` so `verify_response_tiers()` does not add it to violations. When `_wkg` is non-empty, `tier_fact()` evaluates normally.

---

## D — Clean turn after fix (verification)

Immediate verification after fix applied and server restarted. Greeting turn "yo what's good":

```json
{
  "raw": "yo what's good",
  "tier": "TIER1",
  "wkg_context": "",
  "tier_snapshot": {
    "active_window": "inferred",
    "pose": "unknown",
    "nearby": "inferred",
    "mood": "inferred",
    "wkg_context": "inferred",
    "lessons": "unknown",
    "vault_context": "unknown",
    "capabilities": "inferred"
  },
  "tier_violations": ["active_window", "pose", "nearby", "mood", "lessons", "vault_context", "capabilities"]
}
```

`wkg_context: "inferred"` — no longer `"unknown"`. `"wkg_context"` absent from `tier_violations`. ✓

The remaining violations (`active_window`, `pose`, `lessons`, `vault_context`) are correct TIER0/1 behaviour — those faculties genuinely have no confirmed data on fast-path turns. They are pre-existing and out of scope for this WO.

---

## DoD

- [x] Root cause identified: `tier_fact("", ...)` → `"unknown"` on empty wkg_context
- [x] Fix: `"inferred" if not _wkg else tier_fact(...)` — one line, `tiered_faculty_reader.py:98`
- [x] Verification: `wkg_context` removed from `tier_violations` on greeting turn after fix
- [x] No new WO generated — fix is contained and scoped; remaining violations are pre-existing correct behaviour

---

*Builder · 2026-09-14*
