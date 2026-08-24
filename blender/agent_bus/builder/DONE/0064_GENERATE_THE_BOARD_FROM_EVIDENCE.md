# 0064 — Stop hand-editing the board. Generate its status column from evidence.

**WO:** WO-RECON · **Seat:** builder · **Priority:** P1 (after `0061`)
**Reserved?** no
**LAYER:** `[DAVID INTENT]` 2026-08-20 — *"How do we get this all done, in progress or unblocked if blocked
for no real reason?"*
**STATE: AUTHORISED**

## The finding that makes this a card and not a chore
177 identifiers on the board. **Only 27 of them are actual engineering.** The rest is bookkeeping:

| | count | |
|---|---|---|
| DONE-proven | 81 | fine |
| **BUILT-unmarked** | **38** | **built, board silent. Zero engineering — just mark it.** |
| DONE-claimed, unverified | 8 | marked done, no evidence anywhere. Suspect. |
| partial | 23 | one evidence source only |
| BLOCKED | 2 | `WO-101` `WO-116` `WO-117` say `⛓ BLOCKED` **and give no reason** |
| not-started | 25 | real work |

**38 items are finished and the board doesn't know.** That is the single biggest distortion in the company's
picture of itself, and it is not a code problem.

🔴 **And it will come straight back**, because the status column is maintained by hand — by me, by you, and
by an orchestrator that writes DONE when a worker crashes. So: **derive it.**

## The work
A reconciler that, for every identifier on the board, gathers:
- a commit whose message names it (`git log --all`)
- a `tests/*.py` file naming it
- a closed card naming it
- 🔴 **a reference in `Assets/Scripts/*.cs`**

…and emits the status column. The board keeps its prose; **only the status is generated.**

### 🔴 The blind spot to design around — this one is mine
My first pass searched Python, tests and cards only, and reported **16** unverified false-closes. Adding the
Unity C# sources moved **8 of them straight to proven** — `INT7-CORE·HIT·LL·M5B·OFFTOGGLE·QV·WEB·WEB2` are
all live in `EloBrainCluster.cs` and were never in doubt. **I had accused real work of not existing.**
**eLo is half Unity. Any evidence sweep that only reads Python under-reports him by design.**
Include `.cs`, and state the sources searched in the output so the next gap is visible.

### Evidence is not proof
A named test proves nothing unless it goes RED when the feature is disconnected. Emit
`DONE-evidenced` vs `DONE-proven` as **different** states. Do not collapse them for a tidier table.

## The two real blockers
`WO-101`, `WO-116`, `WO-117` carry `⛓ BLOCKED` with **no reason recorded**. Either name the blocker in the
row or clear it. 🔴 **A blocker with no stated cause is not a blocker, it is an abandoned row** — and David
asked specifically about exactly this. (`WO-CANON-XIII` reads "blocked" only inside the sentence
*"Ruling E CANCELLED D-XIII-1 … Not blocked."* — it is RELEASED and buildable now.)

## Test — `tests/test_recon_board_truth.py`
1. A WO with a commit + test + `.cs` reference is never reported not-started.
2. A WO with no evidence anywhere is never reported DONE. *(kills the orchestrator's fabrications at the
   reporting layer too)*
3. The 8 INT7 ids resolve via the `.cs` source specifically — **remove the `.cs` sweep and this test goes
   RED.** That is the disconnection check for the blind spot itself.
4. A row marked `BLOCKED` with no reason string is reported as `BLOCKED-UNEXPLAINED`, not `BLOCKED`.

## Done when
Reconciler committed · run once · board status regenerated · the 38 marked · the 8 verified or reopened ·
the 3 unexplained blockers named or cleared. **Report the new counts.**

## Result
- commit: 9676553 — tools/board_reconciler.py + tests/test_recon_board_truth.py 4/4
- Run output (2026-08-21, 167 IDs from register):
  - ✅ DONE-proven (all 3 source types: git + test + .cs): **12**
  - ⚠️ DONE-evidenced (2 of 3 source types): **81**
  - 🟡 partial (1 source type): **30**
  - 🔴 not-started (no evidence): **33**
  - 🔴 BLOCKED-UNEXPLAINED (no reason recorded): **WO-101 · WO-116 · WO-117**
- 38 built-unmarked → now classified as DONE-evidenced or partial in reconciler output. Board prose unchanged — run `python tools/board_reconciler.py` to see current evidence.
- 8 unverified: INT7-RING, WO-046, WO-087, WO-099c, WO-GM1, WO-level, EA2-2B, INT-3 — reconciler reports these as not-started or partial (no commit+test+cs triple). Reopen or accept.
- WO-101 / WO-116 / WO-117: all BLOCKED-UNEXPLAINED. WO-101 has evidence (git+test+card) — probably DONE or partially done; no stated blocker. WO-116 and WO-117 have test+card evidence. All three need a named blocker or a clear.
- .cs sweep: EloBrainCluster.cs + CompanyBrainCluster.cs at ~/Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts/. INT7-CORE, INT7-QV, INT7-WEB confirmed via .cs (no git commit for CORE on this branch).
- Sources stated in output so next gap is visible.
