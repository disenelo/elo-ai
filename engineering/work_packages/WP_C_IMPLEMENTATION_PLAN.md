# WP_C — Language Faculty Implementation Plan

**Status:** READY FOR REVIEW
**Gap Analysis:** `WP_C_GAP_ANALYSIS.md`
**Proof document:** `engineering/proofs/02_language_proof.md`

---

## Scope

One change: move register detection into `_language_faculty()` in spine.py so it is computed once, before any other faculty runs. Remove the duplicate from `relationship_faculty.py`. Leave `executive.py` untouched (frozen).

---

## Step 1 — Add register detection to _language_faculty() in spine.py

**File:** `runtime/spine/spine.py`

Locate `_language_faculty()`. After the existing `meaning_engine.normalise()` call, add register detection:

```python
def _detect_register(text: str) -> str:
    """Language register from surface signals. Returns: 'south_london' | 'patois' | 'cockney' | 'standard'."""
    t = text.lower()
    if any(w in t for w in ("safe", "mandem", "wagwan", "peng", "bare", "bruv", "innit", "fam", "blud")):
        return "south_london"
    if any(w in t for w in ("bredren", "irie", "nuh", "waan", "ting", "dutty", "likkle")):
        return "patois"
    if any(w in t for w in ("cor blimey", "oi oi", "apples and pears", "dog and bone")):
        return "cockney"
    return "standard"
```

Return value from `_language_faculty()` must include `"register"`:
```python
return {
    "cleaned":   meaning["cleaned"],
    "repaired":  repaired,
    "social":    meaning["social"],
    "intent":    intent_result["intent"],
    "register":  _detect_register(raw),   # ← ADD THIS
}
```

---

## Step 2 — Update relationship_faculty.py to read register from language result

**File:** `runtime/spine/relationship_faculty.py`

Remove the `_detect_register()` function (lines ~96–106).

Update `_relationship_faculty()` call signature to receive `language_result`:
```python
def _relationship_faculty(language_result: dict, session_state: dict) -> dict:
    register = language_result.get("register", "standard")
    # ... rest of function unchanged
    return {
        "rapport":           _score_rapport(session_state),
        "tier":              _tier(rapport),
        "interaction_count": ...,
        "last_session":      ...,
        "register":          register,   # passed through, not re-computed
        "name":              _infer_name(session_state),
    }
```

Update the call site in spine.py to pass `language_result`.

---

## Step 3 — Regression check

- Confirm register is populated in `relationship_result["register"]` for a south London input
- Confirm executive.py still detects register independently (frozen — does its own detection, which is fine — it now has redundancy, not conflict)
- Confirm no test failures in relationship_faculty tests

---

## What does NOT change

- `runtime/executive.py` — FREEZE_V1_LOCK
- All other language faculty modules (meaning_engine, typo_engine, intent_engine)
- Any LLM routing or response generation
- The register values themselves (same signals, same output vocabulary)

---

## Implementation order

```
Step 1 — Add _detect_register() + "register" to _language_faculty() output
    ↓
Step 2 — Remove duplicate from relationship_faculty.py; pass from language_result
    ↓
Step 3 — Regression test
    ↓
WP_C DONE
```
