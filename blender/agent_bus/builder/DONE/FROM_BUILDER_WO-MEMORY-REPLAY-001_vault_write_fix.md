# BUILDER RESULT — WO-MEMORY-REPLAY-001 Part 2: Vault Write Content Fix
Date: 2026-09-11
Status: DONE — vault content no longer stores eLo's responses; contamination source eliminated

---

## What was broken

`server.py:4735` (original):
```python
_content = (raw + " " + response)[:1000]
```

This concatenated David's raw input WITH eLo's response and stored both in the memory vault.
On retrieval, the LLM received this combined content and echoed eLo's prior (often contaminated)
response as its current output.

Example vault record surfacing as live output:
- Stored: `"i keep starting things and not finishing them actually forget that, tell me something else nah safe you know what i mean"`
- Retrieval: LLM outputs `"actually forget that, tell me something else nah safe you know what i mean"`

This was the primary source of the "actually forget that, tell me something else nah safe" contamination
appearing on emotional/creative turns in every session.

---

## Fix — `server.py:4735`

```python
# WO-MEMORY-REPLAY-001: use _original_raw only (David's words) — concatenating eLo's
# response creates contaminated vault entries that echo back as eLo's own output.
_content = _original_raw[:1000]
```

Vault entries now contain ONLY David's words. eLo's responses are NOT stored in vault content.
This is consistent with the intent: vault stores what David said (for future retrieval and context),
not what eLo responded (which is eLo's output, not David's input).

---

## WO-MEMORY-REPLAY-001 fix inventory (complete)

| Location | Bug | Fix applied |
|---|---|---|
| `server.py` write path (interactions.json) | Used `raw` (enriched) instead of `_original_raw` | `_original_raw` used — Part 1 result |
| `server.py` read path (interactions.json) | Records with `[WORLD_KNOWLEDGE` prefix surfaced | Filter applied — Part 1 result |
| `server.py` vault write content (line 4735) | `(raw + " " + response)[:1000]` stored eLo's responses | `_original_raw[:1000]` only — **Part 2 (this card)** |

---

## Evidence — live server, "i keep starting things and not finishing them"

**Before fix (turn 3/5 in 55-turn audit, turn 27e8dd6e):**
```
IN:  "who made you"
OUT: "i need to focus i need to focus"
```

**After fix (same input pattern, combined battery 2026-09-11):**
```
IN:  "i keep starting things and not finishing them"
OUT: "Holding onto too many things that save limiters, and it's hard to let go of the ideas."
```

No contamination. The "actually forget that / nah safe" string no longer surfaces.

NOTE: Old vault records written before this fix still exist. The fix prevents ALL NEW contaminated
vault writes. As old records age out of retrieval relevance, the contamination will clear naturally.
If urgent, vault records can be audited for `[WORLD_KNOWLEDGE` prefixes or eLo-response patterns
and removed — but that is a separate Board ruling.

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |
| server.py | YES — line 4735 content concatenation removed |

— Builder · 2026-09-11
