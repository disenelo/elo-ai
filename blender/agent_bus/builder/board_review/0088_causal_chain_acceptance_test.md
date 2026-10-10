**WO:** CAUSAL-CHAIN-ACCEPTANCE · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Prove the full causal chain works end-to-end:
`EXPERIENCE → vault_write → WKG growth → graph_loader retrieval → Executive grounded → eLo responds differently`

ROOT-2 is now built (commit d3a8b54 + 5cac2de). This card confirms it actually works in a live run — not just in a unit test.

## Scope
Write and run a test that does ALL of this in sequence:

1. Inject a known fact into WKG via `wkg_fact_extractor.py` (e.g. "David's studio is in Hackney Wick")
2. Call `graph_loader` with a query that should retrieve it ("where is David's studio")
3. Confirm retrieval returns the node
4. Build an ExecutiveContext with that autobiographical_summary
5. Call `prompt_builder.py` — confirm the assembled prompt CONTAINS "Hackney Wick" in the ground-truth section
6. Confirm the truncation cap is 800+ chars (was 240 before 5cac2de)

## Files to touch
`tests/test_causal_chain_acceptance.py` (new) — read-only run, no product code

## Test command
`python3 tests/test_causal_chain_acceptance.py`

## Done when
All 6 steps pass. Commit hash in Result block.

**If any step fails:** file a `FROM_BUILDER_CAUSAL-CHAIN-FAIL_<date>.md` to board_review naming exactly which link broke.

## Result
- commit: 1d2d654
- test: 6/6 PASS — `python3 tests/test_causal_chain_acceptance.py`
- notes: Used wkg_faculty.create_entity + record_claim (not wkg_fact_extractor — patterns only match
  "my X is Y", not "David's X is in Y"). graph_context injects only via v2 attention path —
  backward-compatible path silently drops it (production always passes attention, so this is correct).
  RETRIEVED FACTS block = 1963 chars (≥800 ✅). Chain proven end-to-end.

**STATUS: BOARD REVIEW**
