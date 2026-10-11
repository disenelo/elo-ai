# BUILDER 2 — START HERE
### Updated: 2026-10-11 — FULL DEMO SPRINT. Work these in order.

---

## DEMO DEADLINE: END OF OCTOBER. 20 DAYS. RUN CONTINUOUS.

## DEMO SPRINT — your items (P0 all)

### 1. Dream scorer — fix saturation
All 10 retained dreams score exactly 0.900. All three scorer terms saturate at 1.0. The scorer is broken — redesign it to produce differentiated scores. File first 10 retained dreams with corrected scores to Board.

### 2. Dream symbol selection — fix "Moon" saturation
All dreams themed "Moon" regardless of content. Symbol selection not reading dream topics. Fix it.

### 3. SPG backfill from interactions.json
4+ months of conversation data in `interactions.json`. Process it into SPG nodes. Coordinate with Builder 1 on date ranges. David needs SPG active in the demo.

### 4. Random facts raise-hand signal — verify live
You built it (b19423a). Confirm it fires in live turns. File test result to Board.

### 5. Inner thought: collect() emit-safety — CONFIRMED (00bcfc9)
Builder 1 should now wire inner thought ordering in server.py. If they haven't, flag to Board.

---

---

## FILE LOCK — DO THIS FIRST, ONCE

`tools/file_lock.py` exists (Builder 1 card 0107). Use it before every shared file edit.  
Your files (`faculties/inner_thought/`, `faculties/metacognition/`, `faculties/spg/`, `self_improvement/`) are yours alone.

---

## ACTIVE ITEMS — do these in order

### 1. Inner thought as response PRE-PROCESSOR (P0) — NEW [DAVID 2026-10-10]

Source: `docs/architecture/_intake/SOURCE_INNER-THOUGHT-RESPONSE-ARCHITECTURE_2026-10-10.md` [verbatim]  
Board spec: `blender/agent_bus/builder/FROM_BOARD_2026-10-10_INNER-THOUGHT-SHAPES-RESPONSE.md` (filed to Builder 1 — coordinate)

David's architecture:
1. **Acknowledgement** — eLo signals before processing ("1 sec", "give me a moment")
2. **Inner thought fires first** — faster than full response, runs as pre-processor for complex turns
3. **Inner thought alters the response** — not decorative, not appended. It changes the answer.

Currently inner thoughts appear AFTER as `--` suffixes. That is the inverse. Fix the ordering.

You own `faculties/inner_thought/`. Builder 1 owns server.py response assembly. The integration point:  
→ Write a spec to Builder 1's inbox (`FROM_BUILDER2_2026-10-10_INNER-THOUGHT-PREPROCESS.md`) describing what `as_context()` should return so Builder 1 can inject it into Executive context BEFORE generation.  
Do not touch server.py yourself.

---

### 2. Dream memory_written: false (P0) — ONGOING

Board filed: `FROM_BOARD_2026-10-10_DREAM-MEMORY-WRITE.md`

Dreams are running. `memory_written: false` on every cycle. Threshold is now 0.45 [DAVID ruling, your data justified]. But the write itself isn't landing — vault_write path not being reached.  
Investigate and fix. File findings + fix to Board.

Dreams threshold ruling: [DAVID 2026-10-09] lower iteratively until retention starts. Starting at 0.45 (your data: cluster 0.26–0.56). When dreams start retaining, file the first 10 retained dreams to Board for content review.

---

### 3. Four broken tests from working memory change (P1)

Your commit changed working memory from in-memory to `as_context()`. Four tests now fail.  
Fix them. Run full suite on Mac (not sandbox). File results to Board.

---

### 4. Curiosity gate spec — refile to Board (P1)

Board withdrew the curiosity-gate constraint [DAVID ruling — inner thoughts are intentional character, wrong math is authentic]. But there was a pending spec for the 0104 dispatcher still reading `as_context()` from `runtime/working_memory` instead of your module. Clarify the import path issue with Builder 1 via Board.

---

## CURRENT STATE (as of 2026-10-10)

**IS ELO suite results:** 14 pass · 2 blocked · 1 fail (dreams)
- Blocked: curiosity gate (Builder 1) + 0104 dispatcher reading wrong module (Builder 1 fix: db069c7 corrected life_tick import)
- Fail: dreams — 0 retained of 216, max score 0.700 against 0.72 threshold → now 0.45

**SPG:** 3,885 nodes growing. 377 live claim-keyed nodes. ROOT-4 active. Backfill processing historical data.

**Working memory:** In-memory defect fixed. `as_context()` split implemented. ✓

**Identity drift:** Board ruled 1,062 events are false. `server.py:8690` passing `response` instead of `rendered_prompt` — substring test on eLo's output, not character check. Builder 1 has the fix. When it lands, verify with Board: 1,062 events should drop to near zero.

**Inner thoughts:** David confirmed intentional character — fires independently, may reach wrong conclusions, alters outcome. Two voices: FACT answers definitively, eLo thinks on his own. No constraint on curiosity gate around FACT results. [DAVID 2026-10-09]

---

## STANDING TRACKS (still active, lower priority than items above)

### TRACK A — SPG Backfill
Coordinate with Builder 1 on date ranges. Live scoring on new turns. Done when all historical turns have significance scores.

### TRACK C — Inner Thought Ordering
NOW P0 above. See item 1.

### TRACK D — Inbox reads
- `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-GENERATION-STANDARD.md`
- `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-CONTRADICTION.md`
- `FROM_ARCHITECT_2026-10-05_LEARNING-LOOP-LEAK-ADDENDUM.md`

### TRACK E — water_play + auto_action WKG
Wire Designer's play/fun events into WKG nodes + SPG + inner thought gate. Card: `QUEUE/0009_elo_play_wkg.md`. Lower priority until P0s done.

---

## IF YOU NEED A CHANGE IN server.py, spine.py, OR backend_router.py

Write a spec to Builder 1's inbox via Board:  
`blender/agent_bus/builder/FROM_BUILDER2_<date>_<topic>.md`  
Builder 1 applies it. You do not touch those files.

---

## COMPLETION PROTOCOL

1. Run your own tests
2. File to Board: `blender/agent_bus/FROM_BOARD_REQUEST_<date>_<card>.md`
3. Board tests across full matrix. Board signs off or files failure back to you.
4. Do not self-promote to BUILT.

After every Builder 1 commit: run full test suite on Mac (not sandbox). File results to Board. Do not file directly to Builder 1.

---

## ACCEPTANCE CRITERION (David L3, 2026-10-06)

**A WO is DONE when demonstrated experience changed future behaviour.**  
David mentions something from a prior session → eLo retrieves the exact WKG node → eLo responds differently.  
Point to: (1) the node, (2) the retrieval, (3) the changed response. Nothing else counts.

---

## STANDING RULES

- No `git reset --hard`. No whole-repo `git stash`. `git add <your paths>` only.
- No tests against live server (port 5050) during active David session.
- Sandbox test results are untrustworthy — run on real Mac only.
- Builder 2 and Builder 3 do not touch `server.py`, `spine.py`, or `backend_router.py`.
- CAP queue SUSPENDED until causal chain P0s done.

*Board / Lead Architect · 2026-10-10*
