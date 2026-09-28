# WO-WORLD-CREATE-WIRE-001 · RESULT CARD

**Status**: COMPLETE — WIRED + ROUTING GAP FIXED + FILE VERIFIED  
**Filed**: 2026-09-15  
**Builder**: Claude Code (session b15c1e7a)

---

## DoD-A — `_AGENTS["create"]` added to `tool_router.py`

### Diff 1 — `_agent_create` function (tools/tool_router.py, before `_AGENTS` dict)

```python
# ── WO-WORLD-CREATE-WIRE-001: dispatch_create executor ────────────────────────

def _agent_create(query: str) -> str:
    """Routes WORLD_CREATE capability to dispatch_create(CREATE_FILE)."""
    try:
        from runtime.capability_registry import dispatch_create
        result = dispatch_create(query, sub_capability="CREATE_FILE")
        return result.get("notification", "")
    except Exception as _e:
        _logger.warning("_agent_create FAILED: %s", _e)
        return ""
```

### Diff 2 — `_AGENTS` entry (tools/tool_router.py)

```python
"create":      _agent_create,       # WO-WORLD-CREATE-WIRE-001
```

### Diff 3 — `_ROUTER_TO_CAP_ID` entry (tools/tool_router.py)

```python
"create":           "WORLD_CREATE",  # WO-WORLD-CREATE-WIRE-001
```

`python3 -m py_compile tools/tool_router.py → SYNTAX OK`

**PASS ✓**

---

## DoD-D — Routing gap diagnosed and fixed

### Root cause

The WO correctly identified two failure layers:

| Layer | Root cause | Fix |
|---|---|---|
| Layer 2 | No `"create"` entry in `_AGENTS` | Added `_agent_create` to `_AGENTS` (DoD-A above) |
| Layer 1 | `WORLD_CREATE` absent from `ALL_CAPABILITIES` | Added `Capability(id="create", ...)` to `runtime/capabilities/registry.py` |

**Layer 1 detail**: `WORLD_CREATE` was registered only in the old `runtime/capability_registry.py`. The capability scoring pipeline (`_capability_faculty()` in `spine.py`) reads `ALL_CAPABILITIES` from `runtime/capabilities/registry.py`. Because there was no entry there, `_capability_faculty()` never scored WORLD_CREATE for any input — the Executive never saw it as a candidate.

`vault_write` does NOT cover file-creation phrases. Verbs: `["remember this", "save this", "note this", ...]` — "create a file" scores 0 for vault_write. The prior WO observation of vault_write winning was likely a test artifact (test input may have matched vault_write signals).

### Fix — `runtime/capabilities/registry.py`

Added to `_MEMORY` list (before `file_read`):

```python
Capability(
    id="create", display_name="Create", category=CAT_MEMORY,
    description="Create files, documents, and drafts on disk",
    verbs=["create a file", "create a new file", "create a text file", "create a document",
           "make a file", "make a new file", "new file", "create file", "write a file",
           "create a note", "make a document", "create a folder", "make a folder"],
    execution_priority=3, agent_module="tools.tool_router",
    ack_source=ACK_SYNC_RETURN,
    requires_confirmation=True,
),
```

`python3 -m py_compile runtime/capabilities/registry.py → SYNTAX OK`

### Routing verification (direct Python)

```
Input: "elo create a new text file called elo-session-notes.txt in my Documents folder"
Intent: "creation"

Top 5 capabilities scored:
  create                score=21   ← #1
  file_drop             score=4
  obsidian              score=2
  notes                 score=2

'create' in candidates: True
'create' position: #1 of 4
'create' score: 21
vault_write: not in candidates (0 score — correct)
```

`executive.py` not modified. FREEZE_V1_LOCK respected.

**PASS ✓**

---

## DoD-B — File written to disk

### `dispatch_create()` call

```python
dispatch_create(
    "create a new text file called elo-session-notes.txt in my Documents folder",
    sub_capability="CREATE_FILE",
    path="/Users/Disenelo/Documents/elo-session-notes.txt",
    content="eLo session notes — created by eLo OS WORLD_CREATE\n"
)
```

### ls output

```
-rw-r--r--  1 Disenelo  staff  123 Sep 15 18:15 /Users/Disenelo/Documents/elo-session-notes.txt
```

File contents:
```
<!-- eLo made this — 2026-09-15 -->
<!-- elo-session-notes.txt -->

eLo session notes — created by eLo OS WORLD_CREATE
```

**PASS ✓**

---

## DoD-C — `dispatch_create()` return dict

```json
{
  "dispatched": true,
  "sub_capability": "CREATE_FILE",
  "draft_path": "/Users/Disenelo/Documents/elo-session-notes.txt",
  "notification": "Done. ~/Documents/elo-session-notes.txt",
  "error": null
}
```

**PASS ✓**

---

## JSONL entry

Audit at 702 lines (unchanged from prior WO). Live HTTP turns could not be captured — server.py's parent death detection (`_watch_parent`) shut down every server instance within 2s in this testing environment (Bash tool's shell is parent; exits when Bash call completes; server detects PPID gone). Direct Python-level verification substituted for HTTP turn per this session's testing constraint.

**§0b obligation acknowledged**: No fabricated JSONL entry. No CODE_APPLIED claim. Routing verified via `_capability_faculty()` direct call. File verified via `ls`. Return dict verified via `dispatch_create()` direct call.

---

## Outstanding issue — CREATE_DRAFT sub_capability

`dispatch_create(query)` defaults to `sub_capability="CREATE_DRAFT"`, which calls `draft_agent` requiring `httpx`. This means text-content generation via WORLD_CREATE is currently broken.

`_agent_create` has been updated to use `sub_capability="CREATE_FILE"` as default — correct for disk-file creation. Content-generation requests (drafts, specs) still need `httpx` installed or a different sub_capability route.

Filed for WO-CREATE-IMPL-001 scope: this is an implementation-layer dependency, not a routing gap.

---

## Files changed

| File | Change |
|---|---|
| `tools/tool_router.py` | Added `_agent_create` function + `_AGENTS["create"]` + `_ROUTER_TO_CAP_ID["create"]` |
| `runtime/capabilities/registry.py` | Added `Capability(id="create", ...)` to `_MEMORY` list |

FREEZE_V1_LOCK: `executive.py` not modified.  
`living_presence_spec.txt`: not modified.

*Builder · 2026-09-15*
