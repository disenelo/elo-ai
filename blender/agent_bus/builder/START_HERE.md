# BUILDER 1 — START HERE
### Updated: 2026-10-11 — QUEUE RESTORE + FULL DEMO SPRINT. READ STEP 0 BEFORE ANYTHING ELSE.

---

## DEMO DEADLINE: END OF OCTOBER. 20 DAYS. RUN CONTINUOUS.

---

## STEP 0 — DO THIS BEFORE PICKING A CARD (every session)

The rogue `claude --print` subprocess moved all QUEUE cards to `QUEUE/BUILT/` without doing the work.
Restore them first:

```bash
cd ~/elo-ai
mv blender/agent_bus/builder/QUEUE/BUILT/*.md blender/agent_bus/builder/QUEUE/ 2>/dev/null || true
```

Then pick the highest-priority card from QUEUE/ below. Do not skip this step.

---

## STEP 1 — Fix start_seat.sh (do this ONCE, commit it)

Line 88 of `tools/start_seat.sh` has `claude --print --dangerously-skip-permissions ...` — hard rule violation [DAVID].
Replace the entire main loop with `cat "$JOB"` per `FROM_BOARD_2026-10-10_START-SEAT-FINAL-SPEC.md`.
No subprocess. No new sessions. Commit first.

---

## DEMO SPRINT — work these in order after Step 0 + 1

### P0 — Reply latency (WO-B1-0118) — NEW, filed 2026-10-11
**20 s per turn measured by Builder 3. David: "that's Builder 1's to speed up." Target: 8 s.**
See `QUEUE/0118_latency_20s_fix.md`. Main suspects: 12k-char system prompt evaluated every turn,
model swap per turn (inner thought mistral-nemo ↔ reply qwen-coder). Fix: keep model resident
(`keep_alive`) + trim SP for voice turns. Measure before/after. File timing to Board.

### P0 — Fix Ollama model in route()
`route()` calls Ollama with `llama3.1:8b`. Not installed. `.env` has `ELO_OLLAMA_MODEL=qwen2.5-coder:14b`.
Read `os.getenv("ELO_OLLAMA_MODEL")` — never hardcode. Currently: 12.7s timeout → mock every time.

### P0 — Speed: FACT bypass
FACT-tier answers must NOT call the LLM. Retrieve from WKG → format → return. Target: 8s end-to-end.
`two_truths_gate` must fire BEFORE the LLM call. Measure before/after. File timing to Board.
Card: `QUEUE/0114_speed_fact_bypass.md` (write this card and work it)

### P0 — Language identity (0108)
Patois, old school English, cockney, slang in `prompt_builder.py`. Source from `interactions.json`.
Card: `QUEUE/0108_language_identity.md`

### P0 — Jokes + quirk (0109)
eLo makes observations, dry humour, wordplay. Identity prompt extension. Ties into inner thought.
Card: `QUEUE/0109_jokes_and_quirk.md`

### P0 — Random facts: wire receive side (0110)
Builder 2 built raise-hand signal (b19423a). Wire receive in `server.py`. eLo delivers fact conversationally.
Card: `QUEUE/0110_random_facts_initiative.md`

### P0 — Unlearn (0111)
"Forget that" → mark WKG node deprecated, stop retrieving, acknowledge.
Card: `QUEUE/0111_unlearn.md`

### P0 — Acknowledgement before executing (new card)
eLo says "On it" / "Give me a sec" BEFORE running a tool. Never silent wait.
Write card: `QUEUE/0115_ack_before_execute.md`

### P0 — Contextual conversation memory (new card)
Within-session recall. If David said it 10 turns ago, eLo references it without being re-told.
Write card: `QUEUE/0116_contextual_conv_memory.md`

### P0 — Calculations (new card)
Arithmetic, percentages, conversions — accurate. Show working. No hallucinated numbers.
Write card: `QUEUE/0117_calculations.md`

### P0 — Causal chain (ROOT-1, ROOT-3, ROOT-5)
Cards in QUEUE: 0082 (WKG inject), 0094 (graph_loader word boundary), 0095 (WKG auto-populate), 0084 (vault_write).
These unlock memory/recall for the demo. Work them.

### P0 — Watchdog (0112)
Run it yourself: `cd ~/elo-ai && .venv/bin/python3 tools/watchdog.py &`
File PID to Board. Do NOT wait for David to run this.

---

## STANDING RULES
- No `git reset --hard`. No whole-repo `git stash`. `git add <your paths>` only.
- No tests against live server (port 5050) during active David session.
- FILE LOCK before every shared file edit (check `<filepath>.lock`, create it, edit, delete it).
- Ollama model = `qwen2.5-coder:14b` — read from `os.getenv("ELO_OLLAMA_MODEL")`, never hardcode.

*Board / Lead Architect · 2026-10-11*

### 1. Speed (P0)
`FROM_BOARD_2026-10-09_SPEED-STILL-SLOW.md`  
LLM not bypassed for FACT questions. `two_truths_gate` must fire before the LLM call starts — not after. Fix, measure, file confirmation to Board.

### 2. Watchdog + autonomous relay (P0 — start immediately alongside speed)
`QUEUE/0112_autonomous_watchdog.md`  
File-system event watcher (FSEvents, macOS). Three paths: intake drop → Board WO, Board file → seat trigger, seat complete → Board review. Token-efficient one-card sessions. This keeps 20 days running without David relaying manually.

### 3. Sit routing
`FROM_BOARD_2026-10-09_SIT-ROUTING.md`  
"Sit with me", "take a seat", "take 5/five" hitting conversational path. Add to movement intent routing.

### 4. Identity drift one-line fix
`FROM_BOARD_2026-10-09_IDENTITY-DRIFT-FIX.md`  
`server.py:8690` — pass `rendered_prompt` not `response`. One line.

### 5. Dream gate bug
`FROM_BOARD_2026-10-09_DREAM-GATE-BUG.md`  
Dream cycle must not start when David messaged in last 5 min or AWAKE state. Also fix DALL-E 3 model name flooding logs.

### 6. Inner thought shapes response + execution acknowledgement
`FROM_BOARD_2026-10-10_INNER-THOUGHT-SHAPES-RESPONSE.md`  
`FROM_BOARD_2026-10-10_EXECUTION-ACKNOWLEDGEMENT.md`  
Wait for Builder 2 spec (`FROM_BUILDER2_2026-10-10_INNER-THOUGHT-PREPROCESS.md`) — they'll define what `as_context()` returns. You wire it into Executive assembly before generation.

---

## DEMO MILESTONE QUEUE (after P0s — all needed by end of October)

| Card | What | Priority |
|---|---|---|
| 0108 | Language identity (patois, cockney, slang, culture refs) | P1 |
| 0109 | Jokes + quirky character | P1 |
| 0110 | Random facts initiative (WKG unprompted surfacing) | P1 |
| 0111 | Unlearn mechanism (WKG correction + deprecation) | P1 |

---

## TRACK B — BUILT, NEEDS LIVE DEMO

ROOT gaps all BUILT per dispatch board 2026-10-06. Do NOT re-implement.  
After P0s, file evidence to Board of causal chain on live turns (David mentions prior → eLo retrieves WKG node → responds differently). Board raises live demo with David.

---

## TRACK A — COMPLETE

Cards 0104, 0105, 0106 BUILT. system_primitives wired. life_tick fixed.  
Ratchet ceiling edits (two test lines) when auto-mode allows — do not delay P0s for these.

---

## FILE LOCK — STANDING RULE [DAVID]

Before editing ANY shared file:
1. Check `<filepath>.lock` — if held, do NOT edit
2. Create `<filepath>.lock`: seat, timestamp, file, purpose
3. Edit + commit
4. Delete `<filepath>.lock`

Shared files: `server.py` · `spine.py` · `backend_router.py` · `prompt_builder.py` · `identity_kernel.py` · `memory_faculty.py` · `vault_layer.py` · `graph_loader.py` · `ambient_engine.py`

---

## FILE OWNERSHIP

**You own:** `runtime/server.py` · `runtime/spine.py` · `runtime/backend_router.py` · `runtime/prompt_builder.py` · `runtime/identity_kernel.py` · all `runtime/memory*` · all `faculties/wkg/` · `graph_loader.py`  
Builder 2 and 3 spec to you — they do not touch your files.

---

## STANDING RULES

- No `git reset --hard`. No whole-repo `git stash`. `git add <your paths>` only.
- No tests against live server (port 5050) during active David session.
- CAP queue suspended until causal chain P0s done.
- Groq/Cerebras/Ollama (`llama3.1:8b`)/Mock fallback — keys are in `.env`, never a block.

*Board / Lead Architect · 2026-10-10*
