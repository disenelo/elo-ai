# WO-B1-0117 — Calculations
**Seat:** Builder 1  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

eLo does arithmetic, percentages, unit conversions — accurately. Never hallucinates numbers.

## How

- Check if a calculation tool exists in `tools/`. If yes: wire it into the capability routing so "what's 15% of £340" routes to the tool, not to LLM generation
- If no calculation tool exists: eLo must reason step-by-step and show working. The LLM must not return a bare number — it must show the chain so errors are visible
- For unit conversions: same approach — tool if available, step-by-step if not

## Acceptance

Board tests: 5 different calculations (basic arithmetic, percentage, currency, unit conversion, compound). All must return correct answers. Any that shows step-by-step working counts as passing even if the tool isn't wired — as long as the answer is right.
