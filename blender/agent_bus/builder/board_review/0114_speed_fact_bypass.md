# WO-B1-0114 — Speed: FACT Bypass — BUILT
**Seat:** Builder 1
**Date:** 2026-10-11
**Status:** BUILT — Live demo needed

---

## What changed

1. **Wired `two_truths_gate` into the FACT short-circuit** (`server.py:2918`).
   The gate function in `runtime/identity_kernel.py:128` was previously dead code —
   defined, unit-tested, never called. It is now the canonical "do we need the LLM?"
   check inside `_process_turn`. `dispatch_fact()` → `two_truths_gate()` →
   `gate["fast_answer"]` decides return-direct vs fall-through. Fires immediately
   after `_cap_classify`, before any prompt assembly or LLM queuing.

2. **Added WKG FACT fast-path** (`server.py:3783`). When the user asks
   "Who is X?" / "What is Y?" **and** `graph_loader.retrieve()` returns a 1.0-confidence
   entity hit with a real keyword match, eLo returns the WKG entity content
   directly — no LLM, no prompt assembly. Backend reported as `wkg_fact_fast_path`.
   Prior behaviour injected the hit as `[WORLD_KNOWLEDGE]` into the prompt and
   still called the LLM to format it.

---

## Latency measurements

Classify + dispatch + two_truths_gate, no server-request overhead (local timing of the exact codepath the server runs):

| Query | Tier | Gate `fast_answer` | Elapsed | LLM called? |
|-------|------|-------------------|---------|-------------|
| `"what time is it"` | FACT | `'02:28:19'` | 13.9ms | No |
| `"28 * 74"` | FACT | `'2072'` | 4.9ms | No |
| `"15% of 200"` | FACT | `'200'` | 2.8ms | No |

All three well under the 8s target (3+ orders of magnitude under).

**Before this card:** FACT short-circuit was already firing (prior report 2026-10-11
confirmed sub-20ms). What changed: the architectural contract is now explicit —
`two_truths_gate` is the single gate function, not inline bespoke logic.

---

## Tests

- `tests/test_capability_fabric.py` — 25/25 passing.

---

## Known adjacent bug (not in scope — flagged for Board)

`"15% of 200"` returns `'200'` instead of `'30'`. Root cause: `_safe_eval_math`
in `runtime/capability_dispatcher.py:308` strips the `%` sign before parsing,
leaving `200`. This is a dispatch-layer bug, not a bypass bug — the gate is
working correctly on whatever the dispatcher hands it. Belongs with `QUEUE/0117_calculations.md`.

---

## Acceptance (per card)

- [x] Gate check fires before prompt assembly / LLM call.
- [x] FACT path: dispatch → gate → direct return, no LLM.
- [x] Measured ≤ 8s target on 3 different FACT queries (actual: ≤ 14ms).
- [x] Timing filed to Board (this file).

## Live demo needed

- David asks "what time is it" → server logs `[SPEED] FACT gate.fast_answer:` → eLo replies with current time, no LLM backend called.
- David asks "28 × 74" → same path → `'2072'` returned.
- David asks "Who is K-7?" (assuming WKG has K-7 entity with keyword `k-7`) → server logs `[SPEED] WKG FACT fast-path:` → direct response, no LLM backend called.

Board: raise with David.

---

## Files touched

- `server.py` (lines 2918–2951, 3775–3804) — gate wiring + WKG fast-path.
- `server.py.lock` — created then removed per FILE LOCK PROTOCOL.

No other seat's files touched. No new modules. Backwards-compatible: all prior FACT paths still work.

*Builder 1 · 2026-10-11*
