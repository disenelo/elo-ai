---
id: WO-037
title: "Memory wired but NOT learning — interaction write-back dead since 2026-06-09; eLo reads a stale pack."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P1
review_required: L3 (tell eLo something new; he recalls it a day later)
status: OPEN — grounded
created: 2026-08-03
---

# WO-037 — memory isn't learning (write-back is dead)

## Grounded evidence (Architect inspected the stores, 2026-08-03)
- `runtime/prompt_builder.py` DOES fold a memory pack into the prompt (attention-filtered,
  "MEMORY PRINCIPLE" block). So the READ path is wired.
- But the WRITE path is stale:
  - `memory/interactions.json` — last modified **2026-06-09** (24KB, ~2 months old).
  - `memory/session.json` — last modified **2026-06-09**.
  - `memory/user_profile.json` — 2026-06-07 (static, hand-authored).
  - `memory/memory_pack.json` — regenerates (today) but outputs generic **"neutral"**
    patterns + a placeholder identity line → it's rebuilding from thin/stale sources.
- Net: new app conversations are **not being persisted**. eLo reads a frozen June snapshot.
  He "remembers" the old profile but learns nothing new from David.

## Fix (Builder's lane — eLo OS: memory write path)
1. Re-connect the per-turn write-back: every real exchange (app path, not just CLI) appends
   to `interactions.json` / updates `session.json`. Confirm why it stopped ~06-09 (did the
   app `/chat` path skip the memory-commit the CLI path runs?).
2. Feed live interactions into `memory_pack` consolidation so recall reflects recent days,
   not a two-month-old neutral summary.
3. Keep it meaning-based per canon (recurring projects/values/emotions), and time-framed per
   WO-033 (days/weeks, never "sessions").

## Acceptance
1. `interactions.json` mtime updates after a live app conversation.
2. Tell eLo a new fact today → he recalls it in a fresh conversation tomorrow.

## CA FIX FOLD-IN (P1) — Memory must fail DETERMINISTICALLY
Chief Architect: memory answers oscillate (yes/no/backup) across consecutive turns. Memory routing
must resolve to a deterministic health state — CONNECTED / DEGRADED / OFFLINE (via the WO-042
registry) — and the Executive must KNOW that state, not guess per call. Ties write-back (this WO)
to health-aware routing (WO-042).

---
## PROGRESS + REMAINING (David live-test 2026-08-03)
✅ **Write-back LANDED.** `interactions.json` / `session.json` now update on live app turns
(server.py `/chat`: "never wrote to interactions.json — reconnected here"; files stamped 2026-08-04).
The recording that was dead (frozen 2026-06-09) is now firing. This half is DONE — David can verify
by talking then checking the mtime.

⚠️ **STILL WEAK — two parts remain:**
1. **Recall is vague.** eLo returns generic summaries ("exploring the look of progress") not the
   specific things said. Improve retrieval so recall surfaces concrete facts/events, not a mood gloss.
2. **No discrete FACT SNAPSHOT (semantic memory).** David: "I'll save that locally to memory so I
   can remember that detail." When David states a durable fact ("the studio is in Hackney Wick",
   "my location is X"), eLo should write it as a persistent semantic fact (queryable later), distinct
   from the rolling conversation log. This is the "memory snapshot" David keeps asking for.

### Acceptance (add)
1. Tell eLo a specific fact today → recalled specifically (not paraphrased into a gloss) next day.
2. A stated durable fact is saved as a named snapshot and survives restart.
