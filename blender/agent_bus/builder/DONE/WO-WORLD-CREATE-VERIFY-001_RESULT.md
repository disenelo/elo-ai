# WO-WORLD-CREATE-VERIFY-001 · RESULT CARD

**Status**: COMPLETE — GAP CONFIRMED — follow-up WO filed  
**Filed**: 2026-09-15  
**Builder**: Claude Code (session b15c1e7a)

---

## Summary

`WORLD_CREATE` / `dispatch_create` is a dead capability. It is registered in `capability_registry.py` and implemented in `tools/elo_create.py`, but it is **never selected by the Executive** and **has no executor in `tool_router._AGENTS`**. No file-creation intent from a live turn reaches `dispatch_create()`.

---

## DoD-A — All 4 turns expressed response + file on disk

**FAIL.** Neither of the two live turns triggered `WORLD_CREATE`. Files were not written to `~/Desktop/Output/`.

### Turn 1 — "write a quick note about what we've been building today and save it"

```json
{
  "turn_id": "beb1a653",
  "expressed_text": "Saved to Obsidian vault: 'World_knowledge From Elos Own Works Verified'",
  "capabilities": [["vault_write", "..."]],
  "backend": "mock+vault_write"
}
```

**Actual routing**: Executive selected `vault_write` (Obsidian), not `WORLD_CREATE`.  
**File on disk**: No file written to `~/Desktop/Output/`. Audit line 699.

### Turn 2 — "create a new file on my desktop called session-notes.txt and write todays build summary in it"

```json
{
  "turn_id": "5301997c",
  "expressed_text": "I'll use the capabilities I have to create the file and write a summary.",
  "capabilities": [["vault_write", "..."]],
  "backend": "ollama(stream)"
}
```

**Actual routing**: Executive selected `vault_write` again. LLM acknowledged intent verbally; no file created.  
**File on disk**: No file written to `~/Desktop/Output/`. Audit line 700.

Turns 3 and 4 (read back / save note) not attempted — prerequisite (file creation) never succeeded.

---

## DoD-B — `dispatch_create()` called with return dict

**FAIL.** `dispatch_create()` was never called in either live turn. `vault_write` executed instead.

### Static analysis confirming the gap

**`tool_router._AGENTS` (line 864)** — complete table:

```python
_AGENTS = {
    "time", "calculator", "weather", "search", "translate", "news",
    "obsidian", "spotify", "github", "calendar", "calendar_add",
    "vision", "draft", "file_read", "vault_write", "timer",
    "reminders", "clipboard", "notes", "messages", "truth_sync"
}
```

No entry for `create`, `world_create`, `dispatch_create`, or `elo_create`.

**`enrich_from_plan()` line 1582** — unknown capability path:

```python
ag_fn = _AGENTS.get(ag_name)
if ag_fn is None:
    _logger.warning(
        "WO-122 ROUTE: Executive selected UNKNOWN capability %r "
        "(no executor in _AGENTS) — not dispatching, no keyword fallback.",
        ag_name,
    )
    continue
```

If the Executive ever did select `WORLD_CREATE`, this path would fire and `dispatch_create` would still never be reached.

---

## DoD-C — Failure step identification

Two distinct failure layers, both must be fixed:

### Layer 1 — Executive never selects WORLD_CREATE (primary failure)

Both test turns had unambiguous file-creation intent ("create a file", "save it"). The Executive selected `vault_write` in both cases. `WORLD_CREATE` was never in the plan's `capabilities` list. The Executive does not have a signal path that routes file-creation-to-disk intent to `WORLD_CREATE`.

**Exact failure step**: `runtime/executive.py` — capability selection — `WORLD_CREATE` is not selected.

### Layer 2 — No executor in `_AGENTS` (secondary failure, defence-in-depth)

Even if the Executive did select `WORLD_CREATE`, `tool_router.enrich_from_plan()` at line 1582 would log "UNKNOWN capability" and skip. `dispatch_create()` at `capability_registry.py:246` has no route from `tool_router._AGENTS`.

**Exact failure step**: `tools/tool_router.py:1582` — `_AGENTS.get("world_create")` returns `None`.

### Follow-up WO filed

`WO-WORLD-CREATE-WIRE-001` (see below) — wire `dispatch_create` into `_AGENTS` as the `create` executor, AND diagnose why Executive routes file-creation intent to `vault_write` instead of `WORLD_CREATE`.

---

## DoD-D — `confirmation_required=True` behaviour

**Not observable.** `WORLD_CREATE` never fires in a live turn, so `confirmation_required=True` (set in `capability_registry.py:94`) cannot be tested. Current behaviour: no confirmation prompt is shown for file-creation inputs because `vault_write` handles them without a confirmation gate.

---

## Live run summary

| Turn | Input | Capability fired | WORLD_CREATE? | dispatch_create? | File on disk? |
|---|---|---|---|---|---|
| 1 | "write a quick note... save it" | vault_write | No | No | No |
| 2 | "create a new file on my desktop..." | vault_write | No | No | No |
| 3–4 | (not attempted) | — | — | — | — |

Audit grew from 698 → 700. Both expressed turns real. Server: `ELO_VISION=false ELO_VISION_PASSIVE=0`.

---

## Verdict

WORLD_CREATE is a dead capability. Built, registered, implemented — never reached from a live turn. Two failure layers confirmed:

1. Executive routes file-creation intents to `vault_write` (not `WORLD_CREATE`)
2. Even if selected, no executor exists in `_AGENTS` to call `dispatch_create`

FREEZE_V1_LOCK respected. `executive.py` not modified. `living_presence_spec.txt` not modified.

---

## Follow-up: WO-WORLD-CREATE-WIRE-001

Filed in builder inbox. Priority P2.
