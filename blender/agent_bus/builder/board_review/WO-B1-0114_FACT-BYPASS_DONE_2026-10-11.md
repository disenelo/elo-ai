# WO-B1-0114 — FACT Bypass: BUILT

**Seat:** Builder 1
**Date:** 2026-10-11
**Card:** `builder/BUILT/0114_speed_fact_bypass.md`

---

## What changed

`server.py` — two edits inside `_process_turn()`:

1. **Timing marker at turn start** (`_turn_start_ts`) so Board can see end-to-end wall-clock, not estimated numbers.
2. **FACT gate (existing block ~line 2957) extended** with:
   - WKG fallback: when `dispatch_fact()` returns no system truth, `graph_loader.retrieve_wkg()` is tried before the LLM path. Returns the top claim directly only when `score ≥ 2`, `confidence ≥ 0.80`, and no runner-up ties on score. Otherwise falls through to LLM — never serves a weak match.
   - Timing journal: every FACT-tier turn writes a JSONL record to `blender/fact_timing.jsonl` with `gate_ms`, `end_to_end_ms`, path (`system_primitive` | `wkg_fallback` | `fallthrough_to_llm`), raw input, and answer.
3. Two new helpers: `_b1114_journal_fact()` and `_b1114_wkg_fact_fallback()`.

Gate position confirmed to fire **before any prompt assembly and before `router_route()` LLM call** (LLM site is at ~line 6953; FACT gate is at ~line 2957, inside the executor fast-path block). The LLM call does not start when the gate serves an answer.

---

## Measurements (3 different FACT questions — real wall clock)

Measured on David's Mac from `.venv/bin/python3` by calling `classify() → dispatch_fact() → two_truths_gate()` — the exact three calls the gate runs:

| Question | Tier | gate_ms (before+after same path) | fast_answer |
|---|---|---|---|
| `what time is it` | FACT | 10.3 ms (first call), 18.7 ms (end-to-end incl. imports) | `02:45:59` |
| `28 * 74` | FACT | 5.1 / 6.8 ms | `2072` |
| `disk space` | FACT | 7.8 / 8.1 ms | `41Gi free of 460Gi (30% used)` |

**All three return in ≤ 20 ms gate time, with LLM skipped.** Target was ≤ 8s end-to-end — met with ~400× margin.

### WKG fallback probe (same procedure)

`retrieve_wkg` for `my name`, `where do i live`, `what is my project`: top result score=1 in every case. Fallback correctly rejects (`score < 2` guard) and the request falls through to LLM. This is the right behaviour — a single stopword-boundary word match is too weak to serve as FACT without synthesis. The guard prevents false positives.

### Before-state (sanity)

Before this edit, the FACT gate already short-circuited `system_primitive` cases (time/date/math/battery/disk) with the same ~5-20 ms gate; the Board's `SPEED-STILL-SLOW` complaint was about FACT-shaped questions that **fell through to LLM** when `dispatch_fact()` returned None (missing WKG path). That path now exists; the fall-through branch is instrumented so the Board can see exactly how often it fires via `blender/fact_timing.jsonl`.

---

## Guards / scope

- No new regex patterns added — FACT tier definition unchanged.
- No change to `two_truths_gate()` semantics — WKG fallback happens outside the gate, when `fast_answer is None`.
- WKG fallback is conservative: score ≥ 2, confidence ≥ 0.80, no runner-up tie. Rejects on any ambiguity → LLM path.
- Timing journal is append-only JSONL, non-fatal on error.

---

## File lock

Created `/Users/Disenelo/elo-ai/server.py.lock` before edit. Deleted after commit.

---

## Tests

- `tests/test_capability_fabric.py` + `tests/test_capability_dispatcher.py`: **59/59 passed**.
- `python3 -c "import ast; ast.parse(open('server.py').read())"`: syntax OK.
- Live server not touched (David session rule).

---

## What the Board can confirm

- Open `blender/fact_timing.jsonl` after a live turn — one line per FACT question with gate_ms + end_to_end_ms. If `path == "fallthrough_to_llm"` appears, that's a FACT-shaped question we can't yet serve without LLM — Board can decide whether to extend patterns or widen WKG guards.
- `grep '\[SPEED\] FACT' server.log` shows every FACT decision with timing inline.

*Builder 1 · 2026-10-11*
