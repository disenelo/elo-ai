# BUILDER 2 — START HERE
### Updated: 2026-10-08 — PARALLEL TRACKS. RUN ALL SIMULTANEOUSLY. FILE LOCK BEFORE EVERY SHARED FILE EDIT.

---

## FILE LOCK — DO THIS FIRST, ONCE

Builder 1 is building `tools/file_lock.py` (card 0107). Once it exists — use it before every shared file edit.  
Until then: your files (`faculties/inner_thought/`, `faculties/metacognition/`, `faculties/spg/`, `self_improvement/`) are yours alone. Start now.

---

## PARALLEL TRACKS — run simultaneously

### TRACK A — SPG Backfill (P0 — fully independent, start immediately)

4+ months of conversation data in `interactions.json` (gitignored, always present on David's Mac). Contains both David's messages and eLo's responses. Process into SPG significance scores.

- Coordinate with Builder 1 on date ranges to avoid WKG/SPG duplication
- File to Builder 1's inbox if you need server.py changes: `blender/agent_bus/builder/FROM_BUILDER2_<date>_<topic>.md`
- This is your half of the historical backfill. Builder 1 handles WKG. Do not duplicate.

**Done when:** SPG has significance scores from all historical turns. Live scoring active on new turns.

---

### TRACK B — Working Memory + LIFE Process (P1)

**Card:** `QUEUE/0010_life_process_and_working_memory.md`

Two parts — build both, they are your files:

**B1 — Working memory** (`faculties/inner_thought/working_memory.py`)  
Ring buffer, last 10–30 events. Answers "What am I working on?" from state — no LLM.  
Each event carries: `{timestamp, type, content, source, authority, confidence, freshness}`  
`as_context()` method returns formatted string Builder 1 injects into STATE tier.  
Notify Builder 1 via inbox when ready so they can wire it into the capability dispatcher.

**B2 — LIFE process** (`life_tick(state)` function)  
Builder 1's daemon calls this at AWAKE/RESTING/SLEEP intervals.  
- RESTING tick: reflect on recent working_memory events, update emotional/curiosity state  
- SLEEP tick: consolidate into WKG nodes (vault_write), dream (recombine memory)  
Inner life does NOT stop when David isn't talking to eLo.  
Source: `docs/architecture/_intake/SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md`

---

### TRACK C — Inner Thought Ordering

**Brief:** `FROM_ARCHITECT_2026-10-06_INNER-THOUGHT-ORDERING-RULING.md`  
Restructure: inner thought runs BEFORE response assembly.  
**Wait for Builder 1's server.py P0 commits first.** Check: `git log --oneline runtime/server.py | head -5`

---

### TRACK D — Inbox reads (do these alongside everything else)

- `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-GENERATION-STANDARD.md`
- `FROM_ARCHITECT_2026-10-05_INNER-THOUGHT-CONTRADICTION.md`
- `FROM_ARCHITECT_2026-10-05_LEARNING-LOOP-LEAK-ADDENDUM.md`

---

### TRACK E — water_play + auto_action WKG

**Card:** `QUEUE/0009_elo_play_wkg.md`  
Wire Designer's play/fun events into WKG nodes + SPG + inner thought gate.

---

## FILE LOCK — STANDING RULE (2026-10-08) [DAVID]

Before editing ANY shared file:
1. Check `<filepath>.lock` — if held, do NOT edit. Flag to Board.
2. Create `<filepath>.lock`: seat name, timestamp, file, purpose.
3. Edit + commit.
4. Delete `<filepath>.lock` immediately after commit.

Use `tools/file_lock.py` acquire/release/check (Builder 1 card 0107).

---

## IF YOU NEED A CHANGE IN server.py, spine.py, OR backend_router.py

Write a spec to Builder 1's inbox:  
`blender/agent_bus/builder/FROM_BUILDER2_<date>_<topic>.md`  
Describe exactly what needs to change and why. Builder 1 applies it. You do not touch those files.

---

## FILE OWNERSHIP

**You own:** `faculties/inner_thought/` · `faculties/metacognition/` · `faculties/spg/` · `self_improvement/`  
**Do not touch:** `runtime/server.py` · `runtime/spine.py` · `runtime/backend_router.py` · any Unity `.cs` files

---

## ACCEPTANCE CRITERION (David L3, 2026-10-06)

**A WO is DONE when demonstrated experience changed future behaviour.**  
David mentions something from a prior session → eLo retrieves the exact WKG node → eLo responds differently.  
Point to: (1) the node, (2) the retrieval, (3) the changed response. Nothing else counts.

---

## YOUR ROLE — TEST AND FEED BACK. KEEP BUILDER 1 MOVING.

Builder 1 ships continuously. Your job is to make sure they never have to stop.

**When you complete a card:**
1. Run your own tests first — make sure it passes your own test matrix
2. File to the **Board** for sign-off: `blender/agent_bus/FROM_BOARD_REQUEST_<date>_<card>.md`
   - Include: card number, what was built, test evidence (verbatim output — not summarised)
   - The Board tests it properly across multiple scenarios — conversation, memory, knowledge, history as relevant
   - Board either signs off (card moves to BUILT) or files a failure report back to you
3. **Do not self-promote to BUILT.** Board is the gate.

**After every Builder 1 commit — also run the full test suite:**
- `python3 -m pytest tests/` from elo-ai root on the Mac with server running
- File results to Board: `blender/agent_bus/FROM_BOARD_REQUEST_<date>_TEST-RESULTS-B1-COMMIT.md`
- Board reviews and relays regressions to Builder 1's inbox
- Do not file directly to Builder 1. Everything goes through Board.

**Builder 1 does not stop to test. Board is the test layer and relay.**

---

## STANDING RULES

- No `git reset --hard`. No whole-repo `git stash`. `git add <your paths>` only.
- No tests against live server (port 5050) during active David session.
- Run full test suite on real Mac server only — not sandbox. Sandbox results are untrustworthy.

*Board / Lead Architect · 2026-10-08*
