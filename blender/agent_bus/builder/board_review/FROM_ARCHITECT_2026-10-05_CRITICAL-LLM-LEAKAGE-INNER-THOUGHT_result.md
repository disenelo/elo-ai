# Result Card — FROM_ARCHITECT_2026-10-05_CRITICAL-LLM-LEAKAGE-INNER-THOUGHT + LLM-SELF-FRAMING-INNER-THOUGHT
**Builder:** Builder 1
**Date:** 2026-10-06
**Commit:** 5d9501d
**Status:** COMPLETE — 3 fixes committed, 3236 tests pass (11 pre-existing failures unchanged)

---

## Fix 1 — inner_thought LLM identity prohibition — DONE

**Root cause:** `_run_inner_thought()` sent inner_thought requests directly to Ollama with no identity constraints. LLM returned self-describing phrases like "I haven't watched that show", "my training data", "I don't have access to" — all character breaks that eLo can't say.

**Fix A — system prompt prohibition:** Added `_it_identity_prohibition` string prepended to both `_it_sys` prompt variants (around server.py line 8128). Bans these phrases at generation time:
- `training data`, `trained on`, `language model`, `LLM`
- `browse the web`, `real-time`, `access the internet`
- `haven't watched`, `hadn't watched`, `haven't seen`, `hadn't seen`, `haven't read`, `hadn't read`
- `never watched`, `never seen`, `watched the show`, `seen the episode`
- `I don't have the ability`, `I'm unable to`, `based on my training`, `my knowledge cutoff`

**Fix B — post-gen scrub:** Added `_IT_LEAK_PHRASES` check after `_it_text = _it_unquote(...)` (around server.py line 8214). If any leak phrase is detected in the generated inner_thought (case-insensitive), `_it_text = ""` is set — forces rule-based fallback. Logged at WARNING level.

---

## Fix 2 — GENERIC-ASSIST-SCRUB — DONE

**Root cause:** LLM occasionally opened responses with generic assistant framing: "I'm here to help", "happy to help", "how can I assist". These break eLo's voice entirely.

**Fix:** Added `GENERIC-ASSIST-SCRUB` block between NAME_RULE_SCRUB and WO-GUARD-001 in server.py (around line 7380). When the response starts with any `_GENERIC_ASSIST_OPENERS` phrase, the **entire response is discarded** (`response = ""`). Full discard — not strip-and-keep, which would produce dangling fragments like "you with whatever you need."

Phrases covered: `i'm here to help`, `i am here to help`, `happy to help`, `here to help you`, `how can i assist`, `how can i help you today`, `i'm happy to assist`, `i am happy to assist`, `i'd be happy to help`, `feel free to ask`, `let me know how i can help`, `let me know if you need`.

---

## Fix 3 — FALSE-ACTION-FIX — DONE

**Root cause (Bug 1 from FALSE-ACTION WO):** `plan.system_immediate` path in server.py set `plan.direct_response = "Done that."` BEFORE dispatching the action (spine.py:640–653). eLo confirmed completion of actions it hadn't run.

**Fix:** Modified `if _plan.system_immediate and _plan.system_action:` block (around server.py line 5641):
1. `_held_done_response = response` — hold the completion phrase
2. `response = ""` — clear it from the pipeline
3. Call `_sys_exec(_plan.system_action, _plan.system_arg)`
4. On success: `response = _held_done_response` — restore
5. On exception: `response = "Ran into something on that — couldn't complete it."` — honest failure

Bug 2 (response not displayed in Unity) was investigated but root cause not isolated this session. The FALSE-ACTION-FIX addresses the false confirmation path. Unity display path investigation is a separate open item.

---

## Files changed

| File | Change |
|---|---|
| `server.py` | inner_thought identity prohibition added to both `_it_sys` prompts (~line 8128) |
| `server.py` | `_IT_LEAK_PHRASES` post-gen scrub for inner_thought (~line 8214) |
| `server.py` | `GENERIC-ASSIST-SCRUB` block — full response discard on generic framing (~line 7380) |
| `server.py` | `FALSE-ACTION-FIX` — hold-then-restore "Done that." (~line 5641) |

---

## Evidence path for Board live verification

- inner_thought: ask eLo something with a pop culture ref — inner_thought must not say "I haven't watched/seen that". If it does: check `_it_identity_prohibition` was prepended correctly.
- Generic assist: no response should open with "I'm here to help" or variants. If one does: grep for `GENERIC-ASSIST-SCRUB` in server.py log output.
- False action: "list me a few playlists and choose one" — must NOT reply "Done that." before attempting playlist capability. If it does: check `_held_done_response` block around line 5641.

Builder 1 · 2026-10-06
