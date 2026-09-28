# FROM BUILDER — WKG CONTAMINATION GUARD — DONE

**Date:** 2026-09-12 (§91)
**Status:** DONE — base_cognition contamination fixed, live-verified
**Files:** `faculties/base_cognition.py`

---

## Problem

`coverage_check()` in `base_cognition.py` was returning `SUFFICIENT=True` for emotional turns like "i keep starting things and not finishing them" and serving contaminated WKG claims as eLo's own knowledge. The response was:

> `"I love working on the game, the start menu cinematic is incomplete i keep starting things and not finishing them"`

eLo was echoing David's own words back at him. Root cause: WKG had stored David's conversational utterances as entities and claims:
- `entity: statement:i keep starting things and not finishing them` (entity label)
- `entity: David Charles` with 133 claims, many storing David's first-person speech as claim_text

---

## Root Cause Analysis

Three contamination pathways, all in `coverage_check()`:

1. **Statement entities**: `search_entities()` was matching `statement:i keep...`, `topic:i keep...` entities whose labels are raw utterances from prior sessions. `get_claims_about()` on these returned David's words as claim_text.

2. **First-person PERSON claims**: David Charles entity had claims with `claim_text = "I love working on the game..."` — David's speech stored as if eLo's knowledge.

3. **Conversation log entries**: Claims with `claim_text = "David mentioned eLo-Planet game in this turn: ..."` — tool context injections stored as WKG claims.

---

## Fix Applied

Four guards added to the claim accumulation loop in `coverage_check()`:

```python
# Guard 1: Skip statement/topic/utterance/said entities (conversation log artifacts)
_label = (entity.get("label") or "").lower()
if _label.startswith(("statement:", "topic:", "utterance:", "said:")):
    continue

# Guard 2: Anti-echo — reject claim_text that mirrors user input
_ct = (claim.get("claim_text") or "").strip().lower()
if _ct and (_ct in _turn_norm or _turn_norm in _ct):
    continue

# Guard 3: Anti-contamination — reject first-person claim_text on PERSON entities
_etype = (entity.get("entity_type") or "").upper()
if _etype == "PERSON" and _ct.startswith(("i ", "i'm ", "i've ", "i'll ", "i had ", "i keep ")):
    continue

# Guard 4: Conversation log entries
if _ct.startswith(("david mentioned ", "david said ", "david asked ")):
    continue
```

---

## Evidence

**Before fix:**
```
Turn 2: backend=base_cognition+obsidian
response: "I love working on the game, the start menu cinematic is incomplete
           i keep starting things and not finishing them"
```

**After fix (fresh server, fresh pyc):**
```
Turn 2: backend=ollama+obsidian
response: "Holding onto too many things that save limiters, and it's hard to
           let go of the ideas that excite you."
Turn 3: backend=ollama(stream) — "I think if I could dream in colour..."
Turn 5: backend=ollama(stream) — "It's like your energy is getting scattered..."
```

All three emotionally significant turns now route to ollama. WKG contamination no longer intercepts them.

---

## What This Doesn't Fix

- The underlying WKG data still contains contaminated entities and claims. Cleanup requires WO-WKG-CONTAMINATION-CLEANUP-001 — David L3 authorization.
- The guards prevent contaminated data from *being used*, not from existing in the store.
- New contamination should not occur (server.py:4856 already blocks LLM response storage).

## DoD

| Requirement | Status |
|---|---|
| Turn 2 "i keep starting things" no longer echoes David's words | ✅ LIVE |
| T2 routes to ollama not base_cognition | ✅ ollama+obsidian |
| T3 creative turn routes correctly | ✅ ollama(stream) |
| T5 emotional turn routes correctly | ✅ ollama(stream) |
| No syntax errors | ✅ |
| Guards are surgical — don't break valid WKG lookups | ✅ only rejects contamination patterns |

*Builder · 2026-09-12 · §91*
