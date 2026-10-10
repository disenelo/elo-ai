**WO:** FALSE-ACTION-GUARD-AUDIT · **Seat:** builder · **Priority:** P2
**Reserved?** no

## Goal
eLo must not claim he did something when he didn't. WO-122 (8db420e) built the executive deference rule for B3 data answers. This card audits all remaining false-action paths.

## Scope
1. Read `runtime/server.py` — find all places where a response is sent that includes a completion phrase ("Done.", "Sorted.", "I've set that.", etc.)
2. For each: confirm an actual successful tool result preceded it — not just LLM generation
3. Check `tools/tool_router.py` `_direct_intercepts` — confirm no false completions remain after 8db420e
4. Run `tests/test_canon_vii_executive.py` — note pass/fail
5. File a list of any remaining false-action paths to board_review

## Files to touch
Read-only audit. If fixes needed, spec them as follow-up cards — do NOT fix here (one card one scope).

## Done when
Audit complete. List filed (even if list is empty = clean). Commit if any cleanup applied.

## Result
- commit: none (read-only audit)
- test: test_canon_vii_executive.py — 0 tests collected (file exists but no test functions); test_canon_alignment.py — 36/36 PASS
- notes: |
    AUDIT COMPLETE 2026-10-08.

    Paths examined and disposition:

    1. spine.py:664-672 → server.py:5957-5992 — System done via direct_response+system_action.
       ✅ CLEAN — WO-122 gate holds "Done." in _held_done_response, restores only on
       _sys_exec success, replaces with honest message on exception.

    2. server.py:3240-3262 — Animation command path.
       ✅ CLEAN — ack_contract.honest_outcome() replaces "Done." with "That didn't…" if
       anim_trigger.fire returns False.

    3. server.py:3264-3283 — Scale command path (get bigger / get smaller).
       ⚠️ FALSE ACTION — except Exception at line 3276 sets _scale_reply = "Done." even
       when _su()/_sd() raised. Scale may have failed but user hears confirmation.
       Severity: LOW (scale is cosmetic, no data loss).
       Recommended fix card: wrap in honest fallback ("Couldn't scale that.") on exception.

    4. server.py:7827-7849 — LLM completion scrub gate.
       ✅ CLEAN — frozenset _FA_COMPLETIONS catches "Done.", "Sorted." etc. as whole
       responses from LLM path, replaces with honest fallback.

    5. _SYSTEM_DONE_POOL (server.py:1791) — defined, only used via spine.py through gated
       path #1 above. No unguarded direct usage.
       ✅ CLEAN (dead ref in server.py itself, live in spine through gate).

    6. tool_router._direct_intercepts — returns context injection tuples, no completion
       phrases emitted as standalone responses.
       ✅ CLEAN.

    VERDICT: 1 remaining false-action path (scale exception fallback). All others gated.
    Follow-up needed: new card "SCALE-HONEST-FALLBACK" to fix line 3276.
