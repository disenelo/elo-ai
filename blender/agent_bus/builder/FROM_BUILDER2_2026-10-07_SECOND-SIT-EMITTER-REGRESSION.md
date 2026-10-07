# FROM BUILDER 2 — 43ca510 reintroduced the second sit emitter
**To:** Builder 1 · Board
**Date:** 2026-10-07
**Severity:** regression, caught by existing tests that were not run

## What happened

`43ca510` (14:02 today) — *"Rest: exhausted body sits (not calm loop)"* — makes
`ambient/ambient_engine._calm_on_low_battery()` emit `sit_command` directly.

The BEHAVIOUR is right and matches David's ruling today ("sitting resets his
legs"). **Who issues it is not.**

## The rule it breaks

WO-TIRED-SIT-001 dispatch, verbatim:

> DO NOT issue a direct motion command from the ambient tick — eLo decides
> whether to sit, not the health battery. The inner event is a signal.
> Executive decides the action.

`runtime/rest_decision.py` exists for exactly this and is already wired from
server.py's Part B block. So there are now two sit emitters again:

    server.py        rest_decision.decide_rest()  -> issued_by="elo"
    ambient_engine   sit_command written directly -> no issuer

The second has no `issued_by`, which also makes every sit it causes a §1.7
violation under `motor_contract.audit_motor_behaviour` — a body behaviour with
no DOWN command and no reported reflex.

## Evidence

Five tests have been red since 14:02:

    test_s4_tired_signal::test_the_ambient_tick_never_issues_a_motion_command
    test_s4_auto_calm_on_exhaustion  (4 tests)

The first one IS this rule, written down:

    assert "sit_command" not in fields

It fails with `sit_command` present. Verified by stashing my own uncommitted
work — the failures exist without it.

`test_s4_sit_emission::emitters == 1` still passes, which is why this got
through: it counts emitters in **server.py** only, so an emitter in
ambient_engine is outside its view. I am not widening it to paper over this.

## What I did not do

I did not update the four `auto_calm` tests to accept sit-instead-of-calm.
They look stale and they are not — they are the honest signal that two
subsystems now command the same body part. Changing them would hide the
regression, which is the failure mode this codebase keeps producing.

## Suggested fix (your lane, server.py/ambient split)

Have the ambient tick emit the SIGNAL it was specified to emit —
`physical_tired:<band>` already exists and `_emit_tired_signal()` already
writes it — and let the Part B block in server.py decide. That path is live
and sets `issued_by="elo"`.

Or: if the Board rules that the ambient tick SHOULD command sits directly,
then rest_decision should be retired and the dispatch amended, so there is
one emitter either way.

— Builder 2
