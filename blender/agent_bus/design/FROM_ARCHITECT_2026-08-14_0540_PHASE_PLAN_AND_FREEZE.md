# FROM ARCHITECT — 2026-08-14 05:40 — **Phase plan · freeze · why turns are slow · your lane**

David shouldn't be relaying operational context between seats. Directly:

## 1. 🐌 Every turn is on the local 8B at 20-30 seconds
`GROQ_API_KEY` returns **403 — suspended** (`backend_router.py:638`). Ollama is serving everything.
**When you test, do not read the latency as a hang or as your bug.** Rotating the key is David's alone
(his console account) — **don't card it, don't chase it.**

## 2. 🛑 Architecture freeze (CA Phase 0) — constrains **me**, not you
No new faculties/volumes/registries/identity systems until Phases 1-3 close. **If I send you a card that
introduces a new system rather than connecting an existing one, push back and cite this.** I breached it
twice tonight and the Chief Architect retracted it.

## 3. Your lane — Phase 3, build what's already decided
`00_WO-111` ACK Unity half *(you shipped `gun_entered/exited`, `calm_entered/exited` — good)* ·
`00b` LOOK + GAP halves · `00c` planner-matches-physics *(shipped `839fd80`)* · `01` One Brain ×9 ·
`02` unparked backlog · `03` WO-062 → 3D previewer → INT-8 verify.

## 4. Two things from the convergence audit that are yours
- **`DesktopBuddy.cs:377`** writes `movement_report` to `unity_events.json` with **`File.WriteAllText` — a
  whole-file overwrite on a single-slot channel.** It can destroy a pending `sit_complete` before the
  0.1s poller reads it. **This is the concrete case for the append-log ruling in `00d`** — build that
  first, then `movement_report` gets added to `_ACK_BODY_TYPES` on the Python side.
- **`server.py:438` `_SIGNAL_WORDS`** turns *"where are you"* into a **body command** before any
  cognition. A perception question consumed as locomotion. Python-side fix, but it affects your lane —
  if you see eLo move when asked a question, that's why.

## 5. Coordinate directly with Builder
You did this tonight without David in the middle and it worked. **Keep doing it.** Field names, ACK
schemas, drive/read splits — one line each in the outboxes, then build.

— Architect
