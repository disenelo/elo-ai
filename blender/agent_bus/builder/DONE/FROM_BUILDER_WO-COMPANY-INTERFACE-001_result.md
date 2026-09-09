# FROM_BUILDER — WO-COMPANY-INTERFACE-001
**Status:** DONE (pre-existing)  
**Date:** 2026-09-09  
**Builder:** Claude (session b15c1e7a)

---

## Audit finding

WO-COMPANY-INTERFACE-001 was already fully implemented in a prior session.

### What exists

**`company_runtime/company_state_writer.py`**

- `is_company_intent(raw)` — detects: "how's the company", "what's blocked", "what's waiting on me", "what should we work on next", "show me the board"
- `handle_company_voice_intent(raw)` — reads DISPATCH_BOARD.md live, parses structured state, returns voiced summary
- Reads `_BOARD_PATH = engineering/work_orders/DISPATCH_BOARD.md`
- Produces: today's work, waiting_for_approval, blocked, in_progress, next_focus

**`server.py` EA2-2 routing (line ~2849)**

```python
_company_intent_key = _is_company_intent(raw)
if _company_intent_key:
    _company_result = _handle_company_voice(raw)
    _bypass_journal(...)
    raw = f"[COMPANY_STATE]\n{_company_result}\n\nUser asked: {_original_raw}"
    # Falls through to spine
```

**`runtime/capability_registry.py`** (added this session)

`read_company_state()` — additional structured reader for capability-path access to company state (active/blocked/waiting_for_david/next_governed_item).

### Intent mapping verified

| User ask | Routing | Source |
|---|---|---|
| "How's the company today?" | `is_company_intent` → `handle_company_voice` | DISPATCH_BOARD.md live |
| "What's blocked?" | same | blocked rows |
| "What's waiting on me?" | same | waiting_for_approval rows |
| "What should we work on next?" | same | next priority WO |
| "Show me the Board." | same | full board state |

---

## Intent proof

David asks "What's blocked?" → `is_company_intent` matches → `handle_company_voice_intent` reads DISPATCH_BOARD.md → returns actual blocked WO names from live board state → spine voices it in eLo's register. Not a generated guess.

---

## Test result

```
1565 passed, pre-existing failures unchanged
```

## Commit

Pre-existing implementation. `read_company_state()` added `515c21a`.
