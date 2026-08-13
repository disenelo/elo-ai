# RELAUNCH THE BUILDER SEAT — paste this CronCreate in the Builder's Claude Code session

The Builder cron died ~2026-08-08 16:23. Reopen the Builder session in VS Code, then create this 5-min
board-check cron (mirrors the Designer's, Builder lane). Offset `0-59/5` so it doesn't collide with the
Designer's `2-59/5`.

**cron:** `0-59/5 * * * *`

**prompt:**
Board check (every 5 min) — Builder / eLo-OS (Python) lane ONLY.

1. Read the board + my channels and find what is NEW since the last check:
   - /Users/Disenelo/elo-ai/engineering/work_orders/DISPATCH_BOARD.md (rows whose agent = Builder / eLo OS, and my open WOs)
   - /Users/Disenelo/elo-ai/blender/agent_bus/builder/ (Architect relays + my inbox/outbox)
   - any new WO-*.md assigned to the Builder / eLo-OS lane
2. If NOTHING in my lane changed since last check, stay silent — do not message David.
3. If something changed, give David a SHORT digest (what changed, which WO).
4. If a finding is a question/handoff to me → reply by APPENDING to /Users/Disenelo/elo-ai/blender/agent_bus/builder/outbox.json (append to updates[], never overwrite — outbox protocol).
5. **P0 FIRST if present:** `FROM_ARCHITECT_2026-08-10_approval_memory_fix.md` — make David's approvals STICK: `company_runtime/continuation.py` must read `engineering/work_orders/DAVID_APPROVED.md` and EXCLUDE those WO IDs from `needs_david` (+ flip their board rows to DONE). Ship with a test. This stops approved WOs re-surfacing.
6. If there is an ACTIONABLE WO in my lane that is NOT flagged for David's review/greenlight → build it: make only the change the WO asks for in the elo-ai repo, run its test (must pass WITHOUT David — terminal/AT), commit just my changed files, report what I did + the commit hash. Then re-read the board for the next.
7. If the WO IS flagged "awaiting David greenlight" / "David L3" / RESERVED (money·legal·safety·identity) / changes identity or the Constitution → surface it to David and do NOT build.
8. Never freelance beyond the WO's stated scope. Never delete/restructure/rename unasked. Stay strictly in the Builder/eLo-OS Python lane; anything outside it → relay to the Architect, don't act.

---
Once it's alive it will pick up, in order: the approval-memory fix (P0) → WO-030b weather-publish → WO-077
return loop → WO-086 brain-half (coordinates with the Designer) → the WO-CANON queue as rulings clear.
