# ▶ BUILDER (the moment you're relaunched) — WO-APPROVAL-MEMORY: make David's approvals STICK

**Problem (David live 2026-08-10, and he's rightly furious):** he approves DAVID/CONFIRM-tier WOs and they
"sit there" — because `company_runtime/continuation.py` recomputes `needs_david` every run purely from tier
(`green and tier != "AUTO"`), with NO memory of approvals. So approved WOs re-appear as "still need David"
forever. This is THE reason overnight felt like nothing moved.

**Fix (small, Builder lane — you own continuation.py / wo_test_runner.py):**
1. Read `engineering/work_orders/DAVID_APPROVED.md` (a simple dated ledger of approved WO IDs — already
   created by the Architect).
2. In `run_once()` / the `needs_david` computation: **exclude any WO listed in DAVID_APPROVED.md**, and on
   the board flip its row to `DONE ✅ David-approved` (like `auto_close` does for AUTO greens, but keyed off
   the ledger, not the tier).
3. Result: once David approves a WO (Architect appends it to the ledger), it closes and NEVER re-surfaces.
4. Ship with a test: a WO in the ledger does not appear in `needs_david` and shows DONE on the board.

This is the highest-value Builder task right now — it's what makes David's L3 actually mean something.
Priority P0. (The Architect can't touch this — it's runtime code, your lane.)
