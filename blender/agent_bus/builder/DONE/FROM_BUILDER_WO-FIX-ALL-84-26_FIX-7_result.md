# FROM BUILDER — WO-FIX-ALL-84-26 FIX-7 — SELF-CAPABILITY ROUTING — CODE APPLIED

**Date:** 2026-09-11
**Status:** CODE APPLIED — real server evidence pending (server restart required)
**File:** `runtime/prompt_builder.py` — inserted before `_push("executive_directive", ...)` at line 736

---

## What was broken

Three real turns showed wrong self-knowledge:
- `3d6cbb79` SELF_BOUNDARY: "I can't browse the web" — WRONG. `search` capability is registered and not `future=True`.
- `ec5b2b29` MEM_CONTEXT: circular answer about David with no real content
- `4e38fc6e` SELF_KNOW: stiff third-person product description instead of first-person answer

Root cause: 8b model draws from stale LLM training data for self-capability questions even when the live capability list is injected. The general capability list (already in system prompt via server.py line 4323) is not specific enough for the 8b model to produce a direct "YES, I can" answer.

---

## Fix applied

In `runtime/prompt_builder.py` (inside the `exec_decision` directive block), added a SELF_BOUNDARY detection gate:

```python
# Detects patterns like "can you browse", "can you read files", "can you search"
# Looks up the capability in runtime.capabilities.registry
# If found and NOT future=True: injects targeted directive:
#   "[SELF-CAPABILITY FACT — authoritative, answer from this, not training data]
#    YES — web search is registered and active. Do NOT say you can't do this."
# If found and future=True: injects honest "not yet available" directive
```

**Patterns detected:**
| User question | Matched cap | Injected fact |
|---|---|---|
| "can you browse / search / look up" | `search` | YES — web search active |
| "can you access the internet/web" | `search` | YES — web research active |
| "can you read files/documents" | `file_read` | YES — file reading active |
| "can you control volume/brightness" | `volume` | YES — system controls active |
| "can you play music/spotify" | `spotify` | YES — Spotify active |
| "can you see my screen" | `vision` | Vision state dependent on permissions |
| "can you send email/messages" | `messages` | YES — messaging active (confirm required) |
| "can you remember/save/note" | `vault_write` | YES — memory writing active |

Detection uses regex, runs only when exec_decision block is active. First matched pattern wins. Wrapped in `try/except` — no impact on turn if this code fails.

---

## Syntax check

`python3 -c "import runtime.prompt_builder; print('OK')"` → OK

---

## DoD status

| Requirement | Status |
|---|---|
| "can you browse the web" → YES (not stale training data) | ✅ code applied |
| Registry lookup (not hardcoded) | ✅ uses `runtime.capabilities.registry.get()` |
| `future=True` caps answered honestly | ✅ separate branch |
| Real server turn evidence | ⚠️ pending server restart |

*Builder · 2026-09-11*
