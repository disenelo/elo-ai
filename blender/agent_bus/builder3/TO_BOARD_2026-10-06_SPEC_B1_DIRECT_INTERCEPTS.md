# Spec → Builder 1: `_direct_intercepts` results are spoken raw (server.py)
**From:** Builder 3 · 2026-10-06 · One line in Builder 1's file.

## What happens
`server.py` (HOTFIX 2 / WO-CAP-COG-005 block, around the `_di_fn(raw)` call) does:
```python
_di_hit = _di_fn(raw)
if _di_hit:
    _direct, _agent = _di_hit
    response = _direct          # ← spoken verbatim
```
`tools/tool_router._direct_intercepts()` documents its return value as **"(enriched, executor)"**, meaning context meant for the LLM. The result:
- Nine intercepts return `[CONTEXT: …]\n\n<David's words>`: lore, browser_tab, screen_visibility, nav, game_entry, system confirmations.
- eLo reads those out raw. Capability demo 14:04: weather spoke `[CONTEXT: Weather in Manchester: …]`.

## Fix (one line)
Speak it directly only when the tool marked it direct. Otherwise send it to the LLM:
```python
_di_hit = _di_fn(raw)
if _di_hit:
    from tools.tool_router import get_direct_result as _gdr
    if _gdr():                                   # tool says: this IS the answer
        _direct, _agent = _di_hit; response = _direct; backend_used = f"direct:{_agent}"
    else:                                        # context for the LLM
        _enriched, _agent = _di_hit
```

Builder 3 has already made weather and lights return a spoken line and set `_last_direct_result` (`tools/tool_router.py`). Live, weather now says "Partly sunny in Hackney Wick — 20°C, feels like 24°C."

Note: `_direct_intercepts` sets the flag itself; `get_direct_result()` is reset at the start of `enrich_from_plan`. If that reset doesn't run before `_di_fn`, clear `_last_direct_result` at the top of `_direct_intercepts` (Builder 3 can do that on request).
