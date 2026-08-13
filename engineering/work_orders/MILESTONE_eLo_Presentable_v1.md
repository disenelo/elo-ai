---
milestone: eLo Presentable v1 — Close-Out (the goal, in David's words)
owner: David (L3 gate + provides the brain) · Architect (drives + verifies + reports) · Builder + Designer (execute their queue)
created: 2026-08-03
refreshed: 2026-08-07  # rewritten as an ordered close-out so it MOVES, not another spec
purpose: >
  ONE finish line, stated the way David lives it — not WO numbers. Everything below is
  ordered so the seats burn it down one at a time and David stops carrying messages.
---

# eLo Presentable v1 — Close-Out

## The goal, in David's words (this is the acceptance test)
1. **"Take five"** → eLo actually gives him privacy for ~5 minutes and comes back on his own.
   He LEAVES. He doesn't narrate leaving. (real exit, not a line)
2. **"How's the company?"** → eLo tells him something REAL, that VARIES, with LINKS, and a view on
   **what's better to work on.** Grounded in DISENELO's actual state, never a canned string, never invented.
3. **It feels alive** — because eLo understood and acted, not because a timer fired. Emergence, not puppetry.
Plus the daily-use baseline: one voice · coherent · honest (only claims what's verified) · does what it
says · remembers · tight & boundaried · knows its own state.

## The honest blocker under everything: the brain
Right now conversation falls to a MOCK when the paid API is out — that's the "understudy" David met on
2026-08-07 (flowery mirroring, "Company for Doing" hallucination). **Nothing is real or judgeable through
the mock.** So Tier 0 is: give eLo a real brain that doesn't bleed cost.

---

## THE ORDERED CLOSE-OUT (burn top-to-bottom, one WO per seat run)

### Tier 0 — Real brain (unblocks all judgement) — pure Builder code, NO David action
- **WO-032b backend** — retire the dumb mock. **The key is ALREADY in `.env`** (`GROQ_API_KEY` set,
  `ELO_BACKEND=groq`, model `llama-3.3-70b-versatile` — verified 2026-08-07). Fall-to-mock is CODE: (a)
  Groq SDK not installed → call Groq over `httpx` directly (no SDK); (b) the `_groq_quota_exceeded` flag
  latches on one 429 and never clears → clear on recovery. Add a local (Ollama) fallback tier before mock.
  Confirm `backend_used` != mock. → **David: nothing. L3 feel only** (does eLo sound like eLo).

### Tier 1 — The two things David named (his acceptance test)
- **WO-048 + WO-061 — "How's the company," real.** API-FREE path: broaden the company-intent classifier so
  company questions NEVER fall to the mock (same fix pattern as semantic sit); wire answers to the DISENELO
  Operating Model + live board FOCUS (not raw backlog rows); include LINKS to the actual work; add a
  "what's better to work on" recommendation. Honest "I don't have that" if data is missing. — Builder
- **WO-045 — "Take five," real.** eLo emits EXIT (not `biSit`, not narration), stays gone ~5 min, returns.
  Builder emits the exit/return command on intent; Designer plays the real leave+return. — Builder + Designer

### Tier 2 — Daily-use baseline (finish the defaults)
- **WO-022 / WO-037** — memory recall + writeback (store → recall specifics later → persists a restart). — Builder
- **WO-020** — tool routing, verified with a test (don't trust the log). — Builder
- **WO-036** — mirror/narration scrub, code half (kill the "I notice…" reflex). — Builder
- **WO-039** — garble residual confirm (0 on the 400-msg stress). — Builder
- **`conversing` field** — Builder publishes it to `blender_state.json`; Designer gates the sit-linger on it
  (bulletproof hold, retires the heuristic). — Builder → Designer

### Designer parallel queue (Unity — unblocks the FELT product)
1. **COMMIT + REBUILD** the current batch so the running app == current build (sit hold+linger, moves,
   take-five exit, expressions, debug overlays off). This alone makes today's fixes visible to David.
2. `sit_held` heartbeat (verifiable hold) → 3. `EloOSProcess` restart-on-launch (auto-kill stale :5050)
   → 4. wire `conversing` → 5. take-five EXIT visual.
- **WO-063** (a command wakes a dormant body) — QUEUED, POST-Presentable.

### Behind the line (do NOT let them slow Presentable — David's own finish-line rule)
Game GM-2b (eLo-Planet play-test) · robot CAD/RD-3 (RESERVED, LG-2) · marketing WO-046/047 · RL Vol XXVIII.

---

## FULL BUILDS, NOT HALVES (Definition of Done, David 2026-08-07)
A WO is DONE only when the **whole behaviour works end-to-end**, not when one lane's slice compiles. If a
behaviour spans Builder + Designer (sit, take-five, expressions, moves), the WO names BOTH halves and is
done only when they're integrated, tested without David, committed, and the running app is rebuilt from
them. No "my half's done, waiting" as a stopping point — carry it to the integrated, verifiable whole.
Every close-out WO now has a standalone spec + a self-running test + this integrated DoD, so a seat can
open any WO in its queue and build the full thing without checking back.

## The coordination contract (so David stops going in circles)
- **Seats self-serve their queue above** — one WO per run, ship with a test that runs without David, run
  their own live round-trip, write outbox, take the next. They do NOT wait to be hand-carried.
- **Architect drives + verifies + REPORTS** — reconciles each outbox, re-runs the tests independently, and
  tells David the STATE each pass. David should never have to chase what moved.
- **David does two things only:** (1) provide the brain, once; (2) L3 live-feel at each tier gate.

## Done =
David says "take five" and gets five minutes. Asks "how's the company" and gets something real, different,
linked, with a recommendation. And it feels like eLo, not a timer. → Presentable v1 met → CAD / RL begin.
