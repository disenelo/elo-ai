# FROM BOARD — Overnight Run (Builder 2)
**Date:** 2026-10-09  
**To:** Builder 2  
**From:** Board  

David is offline. Two tracks.

---

## Track 1 — IS ELO acceptance suite (chain-dependent)

Watch for Builder 1's life_tick confirmation:  
`blender/agent_bus/FROM_BOARD_REQUEST_2026-10-09_DAEMON-LIFETICK-FIXED.md`

Once that file exists and confirms the fix is committed:

Run the IS ELO acceptance suite per:  
`engineering/tests/IS_ELO_TEST_GATE_2026-10-08.md`

Rules:
- Every test specifies the expected tier (FACT/STATE/COGNITION/UNKNOWN) before running
- Run against the real server — sandbox results are untrustworthy (CLAUDE.md standing rule)
- Results filed to Board as: `blender/agent_bus/FROM_BOARD_REQUEST_2026-10-09_IS-ELO-SUITE-RESULTS.md`
- No easy passes. No brushing over. Full test matrix per card type.

---

## Track 2 — Refile curiosity-gate spec to Board

The curiosity-gate spec you filed directly to Builder 1's inbox before the routing rule existed — refile it to Board as:  
`blender/agent_bus/FROM_BOARD_REQUEST_2026-10-09_CURIOSITY-GATE-SPEC.md`

Board will relay it to Builder 1 correctly. Do not leave it in the old location.

---

## Note on thresholds

AWAKE/RESTING/SLEEP thresholds confirmed [DAVID 2026-10-09]: 5 min → RESTING, 20 min → SLEEP. STIRRING beat added to spec. When running IS ELO suite, include tests for:
- RESTING state tick frequency (120s interval)
- SLEEP state tick frequency (300s interval)  
- STIRRING beat on incoming message during SLEEP (eases to RESTING before AWAKE)

*Board / Lead Architect · 2026-10-09*
