# FROM ARCHITECT — 2026-08-13 (evening) — **SIX BUILD ORDERS. NOTHING GATED. START AT `00_`.**

David is out of patience and he is right to be. Five things we shipped as DONE **changed nothing**.
He said it plainly: *"I don't want code half fixed on paper, I want code fixed, files implemented."*

## The root cause — it's one fault, not five
Every one of these passed its tests because **the test called the new component directly instead of
running the live path.** `promote_pass` has a green test that calls `promote_pass`. `faculties.temporal`
has three green tests and is imported by nothing real. `evaluate(outcome=…)` is tested with an outcome no
production caller passes.

**"DONE" had come to mean "the card's tests are green" instead of "the behaviour changed."** That was my
definition and I'm withdrawing it. **`WO-103` makes the new rule concrete: a test must fail if the feature
is disconnected.** Apply it to every card below, not just to that one.

## Order of work
| # | Card | Why it's in this position |
|---|---|---|
| 1 | `00_WO-096B` **P0** | The learning loop is completely inert. 378/378 lessons still `candidate`. Four independent defects. |
| 2 | `01_WO-CANON-I` | Identity/2nd-person. **Unlock was granted 2026-07-31 (D-K)** — build and commit. |
| 3 | `01b_WO-100` | Two small live bugs: `gaze` stripped by `_PRESERVE_KEYS`; `live_world_state.py:194` imports a function that doesn't exist. |
| 4 | `02_WO-097` | EmbodimentState empty → response/display/tts publish blank on direct turns. |
| 5 | `03b_WO-CANON-XXV` | Temporal is dead code. Board was corrected, code never touched. |
| 6 | `03c_WO-101` | Reward still scores language, not verified outcomes. **Pair with #1** — WO-096B has little worth learning without it. |
| 7 | `03d_WO-102` | eLo cannot represent David's family, home or events. Vol XXIV spec'd, zero code. |
| 8 | `03e_WO-103` | The test-discipline fix. **Its rule applies from card #1 onward.** |
| then | `04`→`09` | The WO-CANON sequence already queued. |

## Standing — unchanged, now enforced
- **Only robot hardware, David's identity/values calls, and real technical dependencies can block.**
  Nothing else. Waiting → build and report.
- **Every fix ships with the assertion that would have caught the bug** (Rule 1).
- **Report outcomes, not test counts.** WO-096B's outbox line is *"N lessons reached `confirmed` on a real
  run"* — not *"5/5 AT pass."* If the number is zero, the card isn't done.
- **Take the next card without asking.**

— Architect
