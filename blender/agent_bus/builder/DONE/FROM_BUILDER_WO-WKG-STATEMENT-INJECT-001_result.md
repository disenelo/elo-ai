# FROM BUILDER — WO-WKG-STATEMENT-INJECT-001 — DONE

**Date:** 2026-09-12 (§91 continued)
**Status:** DONE + VERIFIED
**Files changed:** `knowledge/graph_loader.py` (retrieve_wkg function), `memory/memory_pack_builder.py` (_PACK_CONTAMINATED)

---

## Problem

`retrieve_wkg_context_items()` in server.py's chat path injected contaminated statement-type entities into the `[KNOWLEDGE — VERIFIED FACTS — HIGHEST AUTHORITY]` system prompt block. Items like:
- `"eLo STATED topic:what do you think about"`
- `"David Charles DECIDED statement:i want to build something new today but don't know"`

These are conversation-log artifacts written to runtime WKG as structural entities, not knowledge facts. Injecting them as "verified facts" caused the LLM to potentially echo David's words back as eLo's knowledge.

The same contamination guard existed in `base_cognition.coverage_check()` but was ABSENT from `retrieve_wkg()`, so it only blocked the WKG-first path, not the full system prompt injection path.

---

## Root Cause

`knowledge/graph_loader.py:retrieve_wkg()` pulled runtime claims from `memory/wkg/claims.json` without filtering:
1. Entities whose labels start with `"statement:"`, `"topic:"`, `"utterance:"`, `"said:"` — conversation log artifacts
2. Claims with empty `claim_text` — structural edges with no narrative content

These then became `interpretation` strings like `"{subject_label} {relationship_type} {object_label}"` and were injected as ContextItems.

---

## Fix

Added two guards inside `retrieve_wkg()` before appending each runtime claim:

```python
_CONV_LOG_PREFIXES = ("statement:", "topic:", "utterance:", "said:")
# Skip if either entity label is a conversation-log artifact
if _subj_label.startswith(_CONV_LOG_PREFIXES) or _obj_label.startswith(_CONV_LOG_PREFIXES):
    continue
# Skip empty-text stubs — structural edges with no narrative content
if not _c.get("claim_text", ""):
    continue
```

Also added preventative contamination patterns to `memory/memory_pack_builder.py:_PACK_CONTAMINATED`:
- `"world_knowledge"` — LLM echoing system prompt block label
- `"i keep returning to world"` — same echo pattern, shorter form

---

## Verification

Before fix (python3):
```
item: eLo STATED topic:what do you think about
item: David Charles DECIDED statement:i want to build something new today...
item: eLo STATED topic:what are you thinking about?
...
```

After fix:
```
item: eLo embodies the design principle that calm is the action...
item: 13 multiplied by 28 equals 364...
...
```
— Contaminated statement entities gone. Legitimate canonical WKG facts remain.

*Builder · 2026-09-12 · §91 continued*
