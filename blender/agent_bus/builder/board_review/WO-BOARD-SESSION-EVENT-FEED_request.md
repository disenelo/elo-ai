# Board WO Request — Session-Event Feed Infrastructure

**Filed by:** Builder 1
**Date:** 2026-10-05
**Blocks:** WO-CAP-COG-023, WO-CAP-COG-025

---

## Problem

COG-023 ("eLo notices what David was working on") and COG-025 ("session specificity — eLo references real recent events") both require a **real session-event feed** connected to server.py.

Current state: SPG (session presence generation) produces generic, LLM-fabricated observations ("you've been working on eLo", "you seem focused"). No real session data is tracked or made available to the attention/presence pipeline.

---

## What is needed

A lightweight session-event log that:

1. **Records real session events as they happen** during a conversation:
   - Files opened / modified
   - Capabilities invoked (vault_write, web_search, etc.)
   - Actions taken (CAL action selections: CELEBRATE, BUILD, CONNECT, etc.)
   - Error recoveries
   - Topic clusters (derived from attention dimensions)

2. **Persists between turns** within a session (session-scoped, not global)

3. **Is readable by the attention/presence pipeline** before each response, so:
   - COG-023: eLo can reference "you were just working on the robot shell" (from actual CAL/capability events)
   - COG-025: eLo mentions the specific thing David just did, not a generic guess

4. **Does NOT require a separate process** — should be a lightweight append to a session JSON file or an in-memory list with a session_id key.

---

## Proposed approach (Builder's starting point)

```
server.py → on each turn:
  - append event to SessionEventLog (in-memory list, keyed by session_id)
  - log: { ts, event_type, details } where event_type in:
    ("cal_action", "capability_invoked", "topic", "error_recovery", "tool_used")

SPG / attention → read SessionEventLog.last_N(5) before generating presence text
  - Filter to current session_id
  - Extract recent event labels for specificity
```

Session log is **not persisted to disk** (session-scoped only). On restart, log is empty — that's fine; eLo can only reference what it observed in this session.

---

## Exit criteria

- [ ] `SessionEventLog` class or module in `core/` or `runtime/`
- [ ] server.py calls `log_event()` at: CAL decision point, capability execution, attention classification
- [ ] SPG reads last 5 events and can surface specific labels (not generic)
- [ ] COG-023 AT: "what was I just working on?" → eLo names the actual topic from this session
- [ ] COG-025 AT: multi-turn specificity confirmed (eLo references vault write or capability from 2 turns ago)
- [ ] No FREEZE_V1_LOCK files touched (runtime/executive.py, prompts/living_presence_spec.txt, core/attention.py)

---

## Priority

MEDIUM — blocks two CAP WOs but does not block Kickstarter demo. Kickstarter Demo 3 (memory persistence) is already confirmed. Session specificity is Phase 2 presence quality.

Builder 1 · 2026-10-05
