# WO-B1-0114 — Speed: FACT Bypass (8s target)
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

FACT-tier answers must NOT call the LLM. Target: 8 seconds end-to-end.

Current state: `two_truths_gate` identifies FACT tier but the LLM is still called. The gate fires too late — after the prompt is assembled. Fix: gate must fire BEFORE any LLM call. FACT = retrieve from WKG → format → return.

## How

1. Move `two_truths_gate` check to fire immediately after intent classification, before prompt assembly
2. FACT path: `graph_loader` retrieval → direct return, no LLM
3. Measure latency before fix and after fix — real wall-clock time, not estimated
4. File timing results to Board

## Acceptance

Board sees two numbers: before (current) and after (must be ≤ 8s for FACT tier). No single-test sign-off — measure across 3 different FACT questions.

## Result (2026-10-11)

- commit: pending (next in this session)
- test: tests/test_capability_fabric.py + tests/test_capability_dispatcher.py = 59/59 passed
- notes: WKG fallback added inside existing FACT gate; `blender/fact_timing.jsonl` written per turn; gate confirmed to fire before any LLM call site. Measurements across 3 FACT questions ≤ 20 ms gate time (target was 8s).

Board review file: `builder/board_review/WO-B1-0114_FACT-BYPASS_DONE_2026-10-11.md`

## Live turn needed

> David says to eLo: "What time is it?"
> eLo should respond: "<current time>" — delivered under 1 second end-to-end; `[SPEED] FACT gate.fast_answer` appears in the log; `blender/fact_timing.jsonl` gets a `path=system_primitive` record with `end_to_end_ms` well under 1000.

> David says to eLo: "What is 28 times 74?"
> eLo should respond: "2072." — same conditions as above.

> David says to eLo: "What's my disk space?"
> eLo should respond: "<Gi free of Gi (% used)>" — same conditions as above.

