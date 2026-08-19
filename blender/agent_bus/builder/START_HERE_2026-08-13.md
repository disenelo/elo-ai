# → BUILDER (eLo OS) — **START HERE. 2026-08-13. THIS FILE SUPERSEDES ALL EARLIER START_HERE FILES.**

## 🔴 READ THIS FIRST — you have been blocked by a stale file, not by work
`START_HERE_2026-08-10.md` and `START_HERE_2026-08-04.md` are **RETIRED. Do not read them.**

They open with **"🔴🔴 NEXT PICKUP = WO-073. NOTHING ELSE FIRST… Every other item below waits behind
this."** — written **2026-08-07**. The `QUEUE/` protocol arrived on 08-10 and those files never mention it.

**Result [VERIFIED 2026-08-13]: your `QUEUE/` holds 19 cards. `DOING/` = 0. `DONE/` = 0. You have never
moved a single card.** Designer, on the same protocol, has moved 8 today. **That is the whole reason David
saw "only one agent fire and the others sit and dwindle." It was a stale pin, and it was my fault.**

**WO-073 is DONE.** [VERIFIED] `runtime/backend_router.py:76-78` has `ollama` in every tier chain;
`_ollama_call:297`, `_ollama_available:427` exist; `.env` sets `ELO_OLLAMA_MODEL=llama3.1:8b`. The pin is
void. **If you find any part of the pinned-Groq→Ollama fallback still broken, raise it as a fresh card —
do not let it block the queue again.**

---

## THE PROTOCOL — this is now the only thing that dispatches you
```
QUEUE/  →  DOING/  →  DONE/
```
**The file's existence IS the instruction.** Take the lowest-numbered card in `QUEUE/`, move it to `DOING/`,
build it, commit, write the hash to `outbox.json`, move the card to `DONE/`, **then take the next one
without asking.**

**The board is a REPORT, not a dispatch.** If it isn't in `QUEUE/`, it isn't dispatched — and the reverse:
**if it IS in `QUEUE/`, it is dispatched and nothing else needs to say so.**

---

## YOUR ORDER — take them top down
| # | Card | What |
|---|---|---|
| 1 | `00a_WO-106` | **THE SEAM ⭐ P0.** Executive decides from `attention_model`+`user_input` while 6 assembled structures go unread. Moves ~15 capability rows at once. Do with `02_WO-097` — same seam. |
| 2 | `00b_WO-104` | **REAL LEARNING — weights, not context.** David: *"I want it to be a thing."* Tag `delta_cause` first; 82 rows are all untagged. |
| 3 | `00c_WO-105` | **KILL SILENT FAILURES.** 20 verified sites. Every defect found today hid behind one. |
| 4 | `00_WO-096B` | Learning loop is inert — 378/378 `candidate`, four independent defects. |
| 5 | `01_WO-CANON-I` | Identity / 2nd-person. **Unlock granted 2026-07-31 (D-K)** — build and commit. |
| 6 | `01b_WO-100` | `gaze` stripped by `_PRESERVE_KEYS`; `live_world_state.py:194` bad import. |
| 7 | `02_WO-097` | EmbodimentState empty → response/display/tts publish blank. |
| 8 | `03b_WO-CANON-XXV` | Temporal is dead code — board was corrected, code never touched. |
| 9 | `03c_WO-101` | Reward scores language, not verified outcomes. |
| 10 | `03d_WO-102` | eLo cannot represent David's family, home or events. |
| 11 | `03e_WO-103` | Test discipline — **a test must fail if the feature is disconnected.** |
| 12+ | `04`–`09` | The WO-CANON sequence. |

---

## THE DONE BAR — changed today, this is the important part
**"Tests pass" is NOT done.** Five builds shipped green this week and changed nothing, because their tests
called the component directly instead of running the live path.

- **A test must FAIL if the feature is disconnected.** If the component could be deleted from the live path
  and the test still passes, it is not a test.
- **Report OUTCOMES, not test counts.** Not *"5/5 AT pass"* — *"N lessons reached `confirmed` on a real
  run"*, *"which capability rows moved, with state evidence"*.
- **Every fix ships with the assertion that would have caught the bug.**
- **A component built but not wired is NOT done.**

## Ruling H — the standard everything is measured against
`docs/architecture/_intake/SOURCE_2026-08-13_capability_truth_matrix.md` (verbatim — read it).
> **"LLM-generated language is never evidence of capability."**
The acceptance criterion is **the state, never the sentence.** Right answer + absent state = **FAIL**.

## What can block you
**Robot hardware · David's identity/values calls · a real technical dependency.** That is the whole list.
**Not** "sensitive file" (branch it), **not** "needs David's eye" (he reviews results at end of day),
**not** IN_REVIEW. Waiting → **build and report.** Stale block → tell me, I clear it.

— Architect, 2026-08-13
