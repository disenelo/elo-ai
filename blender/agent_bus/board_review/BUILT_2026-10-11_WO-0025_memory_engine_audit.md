# Board Review — 0025: Second memory store + Ruling B audit
**Date:** 2026-10-11
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW (builder work done; two L3 decisions pending David)

## Builder work — done

### P0-1: AT-8 whole-repo durable-write scan
`tests/test_canon_viii_memory.py::AT-8` already present and correctly FAILING with:
> Vol VIII §4 Runtime Invariant 7 violated — 1 unauthorised permanent-store writer(s) found:
>   core/memory_engine.py

The test correctly identifies the violation. It is designed to fail until David's L3 ruling
resolves the store. The violation is now VISIBLE — it cannot silently pass.

### P0-3: reinforce() moved out of hot-loop
`vault_layer.lookup()` no longer calls `reinforce()` directly (comment at vault_layer.py:523).
Reinforcement now runs in the integration window:
- `server.py:120–122` — `_vault_reinforce_queue` collects spots retrieved AND used this turn
- `server.py:6657–6663` — spots added when vault context is injected into the system prompt
- `server.py:9905–9931` — `_maybe_run_reinforce_vault()` drains queue in a background thread,
  post-response (lines 9645, 9713)

This satisfies Vol VIII §3.4: reinforce only on records retrieved AND actually used.

## Pending — David L3 decisions

### P0-1 — memory_engine disposition
Three options:
- **(a) RETIRE** — migrate interactions.json into vault, route callers through MemoryFaculty.submit()
- **(b) ABSORB** — name memory_engine in Vol VIII as an explicit non-durable interaction log
- **(c) SPLIT** — two stores with a written boundary (Architect recommends against — same as Ruling A problem)

AT-8 will continue to FAIL until this is resolved. That is correct — it keeps the violation visible.

### P0-2 — Ruling B is fiction
`wm_winner` is raw input truncated to 80 chars. Competition hardcoded (raw always wins at 0.475 > 0.400).
`carry_wm()` has no caller. SEED re-runs every turn — frames never exceeds 1. Working memory pinning never fires.

David's call: reopen Ruling B (implement properly) or retract it (accept core/attention.py as the driver).
A ruling on the books that code contradicts is worse than no ruling.

## Board verify

Run: `python3 tests/test_canon_viii_memory.py`
Expected: 15 pass, 3 fail (AT-8 + Ch.4/FT-4 + Ch.4/ST-6 — all known violations).
AT-8 should show core/memory_engine.py as the one violating file.

*Builder 1 · 2026-10-11*
