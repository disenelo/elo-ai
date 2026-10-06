# Result Card — FALSE-ACTION-MISSING-RESPONSE
**Builder:** Builder 1
**Date:** 2026-10-06
**Commit:** 7ca6f8b
**Status:** Bug 1 FIXED; Bug 2 partially addressed (Unity-side gating is Designer lane)

---

## Bug 1 — False completion phrase from LLM — FIXED

**Root cause:** eLo generated "Done that." / "Sorted." / "Handled." as the entire LLM
response for requests it never executed (e.g. "List me playlists and choose one"). These
phrases come from the model's training distribution (short completion confirmation), not
from an actual capability dispatch. The existing FALSE-ACTION-FIX at server.py:5714 only
gates the `_plan.system_immediate` path (real system actions), leaving the LLM path open.

**Fix (two-layer):**

Layer 1 — Prompt rule (`runtime/backend_router.py` ~line 1264):
```
FALSE-ACTION RULE: NEVER say 'Done that', 'Done.', 'Sorted.', 'Handled.', 'On it.', 'Got it.',
'Yeah, done.', 'Sorted that.', 'Opening X', or any completion/confirmation phrase unless you
ACTUALLY executed the action successfully. ...
```

Layer 2 — Post-processing scrub (`server.py` after mirror-opener scrub):
- `_FA_COMPLETIONS` frozenset of known false-action phrases (lowercase)
- If the full response (stripped) matches a phrase in `_FA_COMPLETIONS` AND `_llm_turn` is
  True (i.e., the LLM generated this — not a pool-phrase from `_plan.direct_response`):
  → Replace with: `"Ran into something — didn't complete that. What did you need?"`
- Gated on `_llm_turn` so `_SYSTEM_DONE_POOL` phrases from successful system actions pass through.

**Evidence:**
- "Done that." with `_llm_turn=True` → replaced → honest admission ✓
- "Done that." from `_plan.direct_response` path (system_action succeeded) → not affected ✓
- Prompt rule active for all LLM calls → model now told not to generate these ✓

---

## Bug 2 — Response generated but not displayed in Unity — PARTIAL

The TEXT-REPLY-BUG dispatch (`WO-TEXT-REPLY-BUG_result.md`) covers the primary silence gate
race (fixed in 86b46e0). The dispatch says Builder 1 owns the server.py `response` field
population — that field is ALWAYS populated (or replaced with a fallback) before the HTTP
response is returned.

Remaining Unity-side display logic (EloOSProcess.cs parsing the JSON payload) is Designer
lane. If Unity drops a response from its display while the `response` field was non-empty in
the server payload, that is a Unity parsing/filtering bug outside Builder 1 scope.

Builder 1 scope confirmed complete: `response` field is never None, never empty from a
successful LLM turn without a fallback applied.

---

## Files changed

| File | Change |
|---|---|
| `runtime/backend_router.py` | FALSE-ACTION RULE added to system prompt (~line 1264) |
| `server.py` | `_FA_COMPLETIONS` scrub block after mirror-opener scrub (~line 7393) |

Builder 1 · 2026-10-06
