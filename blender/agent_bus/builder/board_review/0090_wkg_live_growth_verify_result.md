**WO:** WKG-LIVE-GROWTH-VERIFY · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
Confirm WKG is actually growing from live conversation turns (ROOT-1 acceptance). The fact extractor (6d5f5e4) is built — this card proves it runs on every turn and writes nodes.

## Scope
1. Read `faculties/wkg/` — find where `wkg_fact_extractor.py` is called from `server.py` or `spine.py`
2. Confirm it is wired into the live turn path (not just a one-off backfill script)
3. Check `obsidian_vault/09 Memory/` or the WKG graph store — confirm node count has grown since 2026-10-06
4. Run `tests/test_wkg_auto_populate.py` (or equivalent) — confirm it passes
5. Report: node count before vs after one simulated turn

## Files to touch
None — read and verify only.

## Done when
Confirmed in-turn wiring exists + test passes + node count evidence. If NOT wired into live turns: file `FROM_BUILDER_WKG-GROWTH-NOT-WIRED_<date>.md` to board_review and write a fix spec.

## Result
- commit: no fix needed — already wired and working
- test: tests/test_wo_wkg_auto_populate_001.py — all 7 tests PASS (327 total passed this session)
- notes: |
    WKG store: memory/wkg/ (NOT relationships/world_graph.json which is the legacy corpus).
    Wiring confirmed: server.py:6800 calls extract_and_write() on every turn.
    Node count 2026-10-08 session start: ~47 entities (pre-session).
    Node count after session: 319 entities, 2620+ claims (+272 entities, +372 claims since 2026-10-06).
    Simulated turn test: BEFORE entities=318 claims=2620 → AFTER entities=319 claims=2621 (+1/+1).
    Written claim_id: fe302d14-12df-4d7b-ae0c-68b52f07f79c.
    ROOT-1 acceptance: ✅ CONFIRMED.
