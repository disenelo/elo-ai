# FROM BUILDER — WO-GATE-001-AMEND RESULT

**Status:** DONE — 2026-09-08  
**Commit:** `8dbade2`

## Problem

WO-GATE-001-AMEND (P0) required three additional checks and a provenance pass be wired into `elo_response_gate()` in `runtime/response_gate.py`:

- Check 8 — THREAD CONTAMINATION: drops off-thread content from prior sessions
- Check 9 — SEMANTIC RESURRECTION: prevents word-similarity reactivation of old tasks
- Check 10 — FABRICATED SYSTEM STATE: removes claims of failures without execution evidence
- Provenance pass: qualifies "you said/mentioned/asked" claims not backed by current turn or WKG

## Status of each check on audit

| Check | Was wired? | Action |
|---|---|---|
| 8 — THREAD CONTAMINATION | ✅ already present (lines 454–462) | None |
| 9 — SEMANTIC RESURRECTION | 🔴 missing — data structure absent | Added (this commit) |
| 10 — FABRICATED STATE | ✅ already present (lines 479–488) | None |
| Provenance pass (check 11) | ✅ already present (lines 490–512) | None |
| D-4 CONTEXT CLAIM (guard_d4_context_claim_provenance) | ✅ already present + called | None |

## Fix (commit `8dbade2`)

Added `_SEMANTIC_RESURRECTION_PHRASES` list (12 patterns) at line 323 of `response_gate.py`, immediately after `_GENERIC_MODEL_OPENERS`:

```python
_SEMANTIC_RESURRECTION_PHRASES = [
    "picking this back up",
    "picking up where we left off on",
    "getting back to what we were doing",
    "resuming our work on",
    "continuing our work on",
    "as we were working on before",
    "returning to the earlier task",
    "to continue what we started",
    "from our last session",
    "i was helping you with",
    "we were in the middle of",
    "carrying on from before with",
]
```

Wired into `elo_response_gate()` as check 9 between check 8 (thread contamination) and check 2 (stale inference):

```python
# Check 9 — SEMANTIC RESURRECTION
for phrase in _SEMANTIC_RESURRECTION_PHRASES:
    if phrase in cl:
        sentences = _re.split(r"(?<=[.!?])\s+", output)
        filtered = [s for s in sentences if phrase not in s.lower()]
        if filtered:
            output = " ".join(filtered)
            cl = output.lower()
        break
```

## Result

All AMEND checks (8, 9, 10, provenance) are now fully wired into `elo_response_gate()`.

1565 pass · 3 pre-existing failures unchanged.

*Builder · 2026-09-08 · WO-GATE-001-AMEND complete*
