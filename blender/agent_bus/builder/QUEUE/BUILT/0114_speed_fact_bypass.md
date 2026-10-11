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
