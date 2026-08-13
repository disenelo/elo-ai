# WP_D — Memory Faculty Audit

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_B (One Brain frozen)
**Architecture Reference:** `docs/architecture/03_memory_faculty.md`, `docs/architecture/17_memory_update.md`

---

## Purpose

Audit, validate, and freeze the Memory Faculty. Memory is how eLo accumulates knowledge of David across sessions. Errors here mean eLo forgets, misremembers, or over-remembers.

---

## Objective

At the end of WP_D:
- Memory retrieval is validated against known stored facts
- The vault context injection into g_ctx is confirmed working
- Session continuity (spine update_session) is validated
- Memory persistence across server restarts is confirmed
- The Memory Faculty is frozen

---

## Existing Architecture Review Required

**Files to audit:**

| File | Role |
|---|---|
| `memory/user_profile.json` | David's profile — always injected via [CREATOR] block |
| `continuity/identity_state.py` | Session continuity |
| `runtime/spine/spine.py` — `update_session()` | Post-turn memory update |
| `server.py` — `_vault_ctx`, `_memory_pack` | Memory injection into g_ctx |
| `memory/` directory | All stored memory files |
| `docs/architecture/03_memory_faculty.md` | Architecture specification |

**Known issues to investigate:**

1. **[CREATOR] block** — `user_profile.json` is read every turn and injected as `[CREATOR]`. Validate: what happens if the file is missing or malformed? Does eLo still function?

2. **Vault context** — `_vault_ctx` is injected into the system prompt. What does it contain? How is it retrieved? Is it relevant to the current turn?

3. **Session continuity** — `update_session()` is called after every turn. What does it store? How does it affect the next turn?

4. **Anti-fabrication** — The [CREATOR] block includes an ANTI-FABRICATION rule. Validate it is actually effective: can eLo still invent system events?

---

## Gap Analysis

1. What facts about David does eLo currently know and reliably recall?
2. Are there facts eLo should know that are not stored anywhere?
3. Does memory retrieval add latency? If so, is it acceptable?
4. Can eLo distinguish between "I know this from memory" and "I'm guessing"?

---

## Validation Plan

1. Store a specific fact about David in memory
2. Restart the server
3. Ask eLo about the fact in the next session
4. Confirm retrieval (or document the failure)
5. Test anti-fabrication: ask eLo about an event that never happened
6. Confirm [CREATOR] block handles missing/malformed user_profile.json gracefully

---

## Freeze Criteria

- [ ] Memory retrieval validated across server restart
- [ ] [CREATOR] block graceful fallback confirmed
- [ ] Anti-fabrication behaviour validated
- [ ] Vault context injection confirmed working
- [ ] Session continuity validated
- [ ] One Brain compliance confirmed (Memory Faculty retrieves — Executive decides)
- [ ] Regression tests pass
