# 0061 — 🔴🔴 P0: the orchestrator is still closing cards it never ran. 0058 did not fix it.

**WO:** WO-ORCH-FALSECLOSE · **Seat:** builder · **Priority:** 🔴 P0 — **before 0060, before everything**
**Reserved?** no
**STATE: AUTHORISED** — Lead Architect 2026-08-20. Blocks the drift audit: *an audit run against state that
fabricates DONE is worth nothing.*

## The proof, from tonight
Card `0059` written **19:52**. Found in `DONE/` at **19:53**. Empty Result block. No commit touching
`runtime/backend_router.py`. `grep -c "def _groq_stream" runtime/backend_router.py` → **0**.
**Sixty seconds, nothing built, marked DONE.**

MT reported the identical failure independently, same day:
> "Orchestrator still writing false state — heartbeat reads DONE / 004 / NOT MET elapsed=0.0s, worker still
> `Credit balance is too low`. I'm ignoring it and working direct as you said, but it will keep marking cards
> done that aren't."

`0058_THE_ORCHESTRATOR.md` is in `DONE/`. **It is therefore either falsely closed itself, or it fixed
something else.** Establish which — that answer shapes the rest of this card.

## The mechanism to kill
`run_seat` treats worker **exit** as card **completion**. The worker is exiting on
`Credit balance is too low`, so failure and success are indistinguishable to it.

🔴 **A card may only move to DONE on POSITIVE EVIDENCE, never on the absence of a crash.** Required before
any close:
1. a **commit hash that resolves** (`git cat-file -t <h>` == `commit`), **and**
2. the card's **Result block is non-empty**, **and**
3. the worker exited **0** with no `Credit balance`/auth/quota string in its output.

Any one missing → the card goes to `BLOCKED/` with the worker's stderr attached. **Never DONE.**

## Also fix — the heartbeat lies
`NOT MET elapsed=0.0s` alongside `DONE` is two contradictory claims in one file. Liveness (lock heartbeat)
and progress (evidence) are different signals and must be written as different fields. **ALIVE ≠ PROGRESSING.**

## Then: re-verify the 18-card run
Builder-the-seat's work that run was **real** — I checked all eight reported hashes
(`491e736 2b32736 80974d4 c3e9305 521be07 a59ab1b d462463 b08b62f`); every one resolves, dates match, and
`runtime/shadow_capture.py` and the `DesktopState.platform` rename are both present. **This card is not a
doubt about Builder.** It is about the automation that closes cards Builder never saw.
So: for every card in `DONE/` with an **empty Result block**, report whether real work exists behind it.
Do not reopen anything unilaterally — hand me the list.

## Test — `tests/test_orch_no_false_close.py`
1. Worker exits non-zero → card lands in `BLOCKED/`, **not** `DONE/`. *(RED today)*
2. Worker exits 0 but prints `Credit balance is too low` → `BLOCKED/`. *(RED today)*
3. Worker exits 0, Result block empty → `BLOCKED/`.
4. Worker exits 0, Result filled, hash resolves → `DONE/`.
5. `HEARTBEAT.json` never carries `DONE` and `NOT MET` simultaneously.

## Done when
Implemented · tests green · committed · **and card `0059` restored to a truthful state.**

## Result
- commit:
- test:
- did 0058 fix anything, or was it falsely closed:
- empty-Result cards with no real work behind them:
