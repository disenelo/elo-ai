# BUILDER PROGRAMME — everything outstanding, before the Drift Audit opens

**David 2026-08-20:** *"before we start that audit I need to fix the rest of the stuff outstanding via Builder"*

**Work top-to-bottom. Do not reorder.** The order is not by severity — it is by what makes the next thing
knowable. Two phases of cheap work come first specifically so you don't build things that are already built.

🔴 **`QUEUE/` IS UNSAFE.** The orchestrator closed card `0059` sixty seconds after it was written, with an
empty Result and nothing built. Your live cards are in **`_HOLD_ORCHESTRATOR_UNSAFE/`**. Work them direct,
the way MT is working direct. Do not move them back until Phase 0 is closed.

---

## PHASE 0 — make state trustworthy (nothing downstream is real until this lands)

| Card | Why first |
|---|---|
| **`0061`** orchestrator false-close | It fabricates DONE. Every number, every board row and every "finished" card is suspect while it runs. **An audit against fabricated state is worth nothing.** |

**Exit:** a card can only reach DONE on positive evidence — resolving commit hash **and** non-empty Result
**and** clean worker exit. Failure goes to `BLOCKED/` with stderr attached, never DONE.

---

## PHASE 1 — turn 68 unknown rows into a real list (cheap, and it shrinks everything after)

| Card | Why here |
|---|---|
| **`0064`** generate the board from evidence | 177 identifiers. **Only ~48 are actual engineering.** |

Of the 68 rows the board does not mark done:

| | count | action |
|---|---|---|
| **built, board silent** | **38** | **mark them. Zero engineering.** |
| marked done, no evidence | 8 | verify or reopen |
| `⛓ BLOCKED`, **no reason recorded** | 3 | `WO-101` `WO-116` `WO-117` — name the blocker or clear it |
| partial | 23 | check |
| never started | 25 | Phase 4 |

🔴 **Include `Assets/Scripts/*.cs` in the evidence sweep.** My first pass searched Python only and reported
16 false-closes; adding Unity moved 8 straight to proven — the `INT7-*` work was never in doubt and I had
accused it of not existing. **eLo is half Unity. A Python-only sweep under-reports him by design.**

**Exit:** the 38 marked, the 8 resolved, the 3 blockers named or cleared, and a truthful count reported.

---

## PHASE 2 — the live defects David is actually experiencing

| Card | |
|---|---|
| **`0060`** eLo jammed in GROUND | Seven consecutive turns of restatement, a confabulation, and a repeat. **Run the §E A/B before touching code** — same model direct vs through the pipeline. §C/§D are yours; §A/§B stop at a written proposal with the routing table. |
| **`0063`** chatlog replay harness | *"I use chatlogs as diagnostic tests."* Fixture already written — 10 turns, 7 failing. **This is the only C→D instrument that exists**, and it is what proves `0062` and `0060` actually worked. |
| **`0062`** WO-036b, the mirroring rule | ⚠️ **Read the CORRECTION at the top first.** The rule is NOT missing — it exists and is being ignored from 2,400 tokens deep while the GROUND directive wins on recency. Do not add another rule. |

**Exit:** the fixture replays with materially fewer than 7 failures, and the improvement is attributable.

---

## PHASE 3 — speed, and then who authors

| Card | |
|---|---|
| **`0059`** streaming + deadline | **Router half already implemented by the Architect (154 insertions) and unverified live — verify it, do not rebuild it.** Remaining work is the real one: `prompt_eval` re-reads **7,086 tokens every turn** (`backend_health.json`, 23:25) despite a correct prefix layout. **The cache is missing. Fix the cache, never the prompt.** |
| **`0065`** WO-BRAIN-AUTHORS | 🔴 **DECIDED BY DAVID — not a proposal.** *"Feeds into Brain, Brain see's whats needed, brain applies model, spine, execution (elo output) with his identity intact."* Start with step 1: separate `elo_raw_gen` from `elo_final`. They are the same object today, and until they differ nothing else on that card is measurable. |

**Exit:** first audible word measured before/after · tier supplied by the Executive · raw ≠ final.

---

## PHASE 4 — the 25 never-started, CANON block first

**10 of the 25 are canon volumes:** `WO-CANON-III XIII XVII XVIII XIX XXII XXIII XXVI XXVII XXVIII`.
Plus `WO-CANON-XIII` is **RELEASED and buildable now** — its row only reads "blocked" inside the sentence
*"Ruling E CANCELLED D-XIII-1 … Not blocked."*

**David's reasoning, and the data supports it:** every unimplemented volume is a standing omission — exactly
*"what was taken out or omitted"* — so the audit would surface it as a finding anyway. **Building the CANON
block converts ~10 future findings into completed work before the audit runs.** Highest drift-prevention per
unit of effort. *"It refines the diamond."*

Also here: **`WO-004b`** (Volume V's loose end — no test, no board status) and **Volume IX**, which has **no
work order at all** (D-5 — dream faculty live, `executive.py` has zero dream references, so eLo has a
faculty he cannot invoke).

---

## STANDING RULES ON EVERY CARD ABOVE

- 🔴 **Never buy speed or tidiness with eLo.** *"buy speed by giving eLo less of himself - do not do this at
  all."* No smaller model for his voice, no lower token budget, no trimming context or memory. If measurement
  says that is the only lever left — **stop and report.**
- 🔴 **`FREEZE_V1_LOCK.md` is David's.** 9 CAL actions, 5 voice states, Character DNA — untouched. Anything
  that changes *who eLo is* stops at a proposal.
- **Source every change** (Rule 4d): `[SPEC]` `[DAVID]` `[VERIFIED]` `[ESTIMATE]` `[PROPOSAL]`, at the value.
- **A test proves nothing unless it goes RED when the feature is disconnected.**
- **Chat logs outrank passing tests.** Every AT was green while eLo answered David in one register for seven
  turns.

## WAITING ON DAVID (do not block on these — build around them)
1. CAL routing order (`executive.py:219`) — frozen rule, his L3, table comes from `0060`
2. Six Company Brain mood words not in `MoodPalette`
