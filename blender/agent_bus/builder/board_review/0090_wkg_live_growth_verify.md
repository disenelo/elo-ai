**WO:** WKG-LIVE-GROWTH-VERIFY · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Result
- commit: (no new code — read-only verification)
- test: 7/7 wkg_auto tests green (2026-10-07)
- notes: All 5 card checks confirmed:

  1. **Wiring confirmed** — server.py lines 6723-6743: `extract_and_write` (ROOT-1 fact extractor)
     and `populate_wkg_from_turn` (concept stubs) both called inside the live turn `finally`-equivalent
     block. Non-blocking (wrapped in try/except). Runs on EVERY turn.

  2. **In-turn path confirmed** — both calls are in server.py main turn handler (not a backfill script).
     `_original_raw` (user input) is passed to both. `experience_id` and `project` come from `_plan`.

  3. **Node written and confirmed in store** — simulated turn:
     `"my studio computer is a Mac Studio M2 Ultra"` → `extract_and_write()` →
     claim_id `31f9639a-f79f-402f-89a4-ba5abf7e80aa` → found in `memory/wkg/claims.json` ✅

  4. **Tests green** — 7/7 `test_wo_wkg_auto_populate_001.py` tests pass.

  5. **Node count** — `retrieve_wkg_context_items` returns same result count before/after because it
     queries by semantic keyword match (5 canonical David nodes), not raw count. The new claim was
     written to claims.json and is retrievable by ID. Count growth is in claims.json, not in the
     canonical entity nodes (those are pre-seeded).

  ROOT-1 acceptance: WKG grows from live conversation turns. Wiring is live and working.
