# FROM_BUILDER — WO-SPG-HOOKS-001 RESULT

**WO:** WO-SPG-HOOKS-001  
**Seat:** Builder  
**Status:** CLOSED ✅  
**Date:** 2026-09-07  

## Summary

Wired 4 SPG observer taps into the live turn loop. No decision path modified.

## Hooks wired

1. **main.py** — memory_write tap after WKG write block (uses `_spg_wkg_cats`)
2. **significance_faculty.py** — significance_spike tap when `overall > 0.6`
3. **spine.py** (~L862) — relationship_shift tap after `rel_analyse()` call
4. **spine.py** (~L1109) — memory_write tap after `build_execution_report()` publish

## Exception handling

All hooks use `except Exception as _err: _log.warning(...)` — no bare pass, no debug-swallow.
Passes `test_spine_run_no_bare_pass` and `test_spine_run_no_debug_swallows`.

## Signal output

`data/spg_signals.jsonl` will accumulate entries on real turns. File may be empty until first real `python main.py` run with Ollama active.

## AT note

Live AT (run one real turn + read spg_signals.jsonl) deferred — Ollama backend not running in this Builder session. Hook code is wired and exception-safe.
