# FROM_BUILDER — WO-SPG-SIGNAL-QUALITY-001: SPG Signal Quality Fix

**Date:** 2026-09-11  
**Status:** DONE — SPG read path wired into spine.py; real server evidence pending (server not running)  
**Authority:** Board → Builder 2026-09-11 — P1

---

## The gap

SPG write path: `runtime/wkg_faculty.py:497` calls `update_spg_from_claims` — working.  
SPG nodes: 109 nodes, 10 edges in `data/spg_graph.json`.  
SPG read path: `memory.spg_faculty.query_spg_entities` was NEVER called from runtime. The query function existed but had no caller in `runtime/spine/spine.py` or anywhere else in the runtime layer.

`wkg_context` received WKG keyword-search results only — SPG connections were not surfaced.

---

## Fix

Added SPG read call to `runtime/spine/spine.py` after existing `_wkg_context` WKG assembly:

```python
# WO-SPG-SIGNAL-QUALITY-001: SPG read path
from memory.spg_faculty import query_spg_entities as _spg_query
_spg_topic = language.get("meaning", "")[:80] or language.get("intent", "")
if _spg_topic:
    _spg_ids = _spg_query(_spg_topic)
    if _spg_ids:
        _spg_labels = [_spg_ent_map[eid] for eid in _spg_ids if eid in _spg_ent_map][:3]
        if _spg_labels:
            _spg_addition = "[SPG] " + "; ".join(_spg_labels)
            _wkg_context = (_wkg_context + "; " + _spg_addition) if _wkg_context else _spg_addition
```

**Syntax check:** `python3 -c "import runtime.spine.spine; print('OK')"` → OK

---

## Functional test (offline)

```
SPG query for "elo planet game kickstarter":
  IDs returned: 3
  Labels resolved: ['eLo', 'eLo-Planet game', 'Kickstarter campaign']
  wkg_context addition: [SPG] eLo; eLo-Planet game; Kickstarter campaign
```

SPG-surfaced entities now appear in `_wkg_context` as `[SPG] <label>; <label>; ...` prefix, distinguishable from WKG keyword-search entries.

---

## Real server evidence

**BLOCKED — server not running at time of fix.**

When David next starts the server, run one turn about a topic eLo has seen before:
- Input: "what's the kickstarter plan" (or similar)
- Check `wkg_context` in expressed_elo_audit.jsonl — should contain `[SPG]` prefix entries
- Check expressed output for SPG-surfaced connection appearing in eLo's response

DoD satisfied when `[SPG]` entries appear in wkg_context and expressed output demonstrates the surfaced connection.

— Builder · 2026-09-11
