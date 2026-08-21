# 0070 — DISPATCH: your six never-started items. `QUEUE/` is safe again.

**Seat:** builder · **Priority:** P2 (after `0059` `0060` `0068` `0069`) · **STATE: AUTHORISED**

🟢 **`QUEUE/` is trustworthy again** — your own `e5f1e39` added *"Gate 1: non-zero exit is always BLOCKED —
do not trust any card move the worker may have made."* The hold folder was a workaround for a bug you fixed.

## Movement since yesterday — worth seeing
CANON never-started **10 → 5**. Real engineering left **51 → 43**. Eight commits overnight.

## Your six
| WO | What | Spec |
|---|---|---|
| `WO-CANON-XVII` | Reflection Engine — lessons, evidence, measurement | `Volume_XVII/` 2ch |
| `WO-CANON-XVIII` | Self-Evolution — change without breaking identity | `Volume_XVIII/` 1ch |
| `WO-CANON-XXVIII` | Adaptive Learning & Reinforcement | 🔴 `Volume_XXVIII/` — **1 chapter, 1,030 words, no metadata, no title** |
| `WO-004b` | Volume V loose end — **no test, no board status** | `Volume_V/` (the ONE ratified volume) |
| `CT4V-08` | convergence test-for-value | board row |
| `WO-049-B1` | — | board row |

🔴 **`WO-CANON-XXVIII` is the one genuine hole in the canon.** Every other volume has real chapters; this one
is a stub with no metadata. **Do not build to it — say so and stop.** A spec that thin is not a spec, and
inventing the rest is the exact drift David has been chasing. Report what is missing; he decides.

**`WO-004b` first.** It is the loose end on **Volume V, the only ratified volume in the whole canon** — one
volume is fully signed off and it still has an untested edge. Cheapest thing here with the highest symbolic
value.

## Rules that bind all six
- **Build to the spec. If the spec is thin, stop and report — never fill the gap yourself.** (David:
  *"if it's spec'd it should just go towards the spec"* — the inverse also holds.)
- A test proves nothing unless it goes **RED when the feature is disconnected**.
- Source every value: `[SPEC]` file+section · `[VERIFIED]` how · `[ESTIMATE]` at the number.
- 🔴 **`FREEZE_V1_LOCK.md` untouched.** XVIII is *self-evolution* — if any of it would change the 9 CAL
  actions, 5 voice states or Character DNA, **it stops at a proposal.**

## Done when
Each: implemented · disconnection-falsifiable test green · committed · Result block filled · card to `DONE/`.
**Report `WO-CANON-XXVIII` as a spec gap rather than building it.**

---

## Result — 2026-08-21 · Builder

Full per-item state report: `FROM_BUILDER_2026-08-21_XXVIII_spec_gap_and_XVII_XVIII_not_ratified.md`.

### `WO-004b` — Volume V loose end · ✅ CLOSED (code green; board row stale)

- **Code [VERIFIED]** — `runtime/spine/spine.py:696-766` (`assemble_cognitive_state()` +
  `build_embodiment_state()`).
- **Test [VERIFIED]** — `tests/test_wo004_contracts.py` re-run 2026-08-21: **12/12 passed, 0 failed.**
- **Disconnection-falsifiability [VERIFIED]** — monkey-patched shims prove the test goes RED when the
  feature is disconnected:
  - broken `assemble_cognitive_state` (empty fields) → **WO-004b-3 RED**
  - broken `assemble_cognitive_state` (always conf=1.0) → **WO-004b-4 RED**
  - broken `build_embodiment_state` (empty response_text/motion_command) → **WO-004b-8 RED** (both branches)
- **Completion log** — already records DONE at `engineering/work_orders/COMPLETION_LOG.md:225`
  (`test_wo004 12/12 · now live per-turn via WO-014`).
- **Loose end** — `engineering/work_orders/DISPATCH_BOARD.md:1562` still reads
  `| OPEN | WO-004b CognitiveState + EmbodimentState wiring | ...`. Board reconciliation is Architect-owned
  (Rule 3 / 4g — the Builder does not restructure the board's status cells). **Flagged for Architect.**

### `WO-CANON-XVII` — Reflection Engine · 🟠 STOP · NOT RATIFIED (PROPOSE)

- **[VERIFIED]** `docs/architecture/Volume_XVII/00_Metadata.md:4` — `status: REVIEW — spec drafted
  2026-08-13; awaiting CA first-pass + David L3. NOT RATIFIED.`
- Per the Four States (2026-08-17), AUTHORISED requires David/CA/LA acceptance. XVII is at PROPOSE.
  Building it would collapse PROPOSE → IMPLEMENT.
- **Not built. Awaiting CA first-pass + David L3.**

### `WO-CANON-XVIII` — Self-Evolution · 🟠 STOP · NOT RATIFIED (PROPOSE)

- **[VERIFIED]** `docs/architecture/Volume_XVIII/00_Metadata.md:4` — identical `NOT RATIFIED` block.
- XVIII declares (`00_Metadata.md:81-86`) it has nothing to version until XVII's read side (WO-095)
  lands. Also under CLAUDE.md LIVE GATE: *"XVIII is self-evolution — if any of it would change the 9
  CAL actions, 5 voice states or Character DNA, it stops at a proposal."*
- **Not built. Awaiting CA + David L3, and XVII/WO-095 landing.**

### `WO-CANON-XXVIII` — Adaptive Learning & Reinforcement · 🔴 SPEC GAP (as the card predicted)

- **[VERIFIED]** `docs/architecture/Volume_XXVIII/` = **one file** (`00_Adaptive_Learning_Reinforcement.md`,
  91 lines / 1030 words). **No `00_Metadata.md`** (every other Volume dir has one).
- File self-declares (`:2`) as *"Scaffold · scope-locked · PLANNED. Authored + built BEHIND Presentable v1."*
- Missing to be buildable: Metadata block · faculty contract · lifecycle binding · envelope binding ·
  acceptance tests · CA first-pass · David L3.
- **Reported as spec gap. Not built.** Awaiting David's decision on scoping / authorship path.

### `CT4V-08` — Self-Explanation Trace · 🟠 STOP · NO FORMAL WO FILE

- **[VERIFIED]** Only source is `docs/architecture/_intake/SOURCE_2026-08-14_CA_crosscheck_CANON-TRUTH-4V.md:162,169-171`.
  Board row `DISPATCH_BOARD.md:730` points to `builder/0024`, which is deleted (`git status`).
- No `engineering/work_orders/WO-CT4V-08*` file exists. Substantive build (12 preservation fields on
  every turn, touches Executive path — potentially FREEZE-adjacent).
- **Not built. Awaiting WO spec file from Architect.**

### `WO-049-B1` — Spatial Faculty v1 · 🟠 STOP · NO FORMAL WO FILE (board row only)

- **[VERIFIED]** Only reference is `DISPATCH_BOARD.md:1783` (one-line description). Grep across
  `engineering/work_orders/` returns no dedicated spec file.
- A one-liner is not a spec (per card rule: *"if the spec is thin, stop and report — never fill the gap"*).
- **Not built. Awaiting WO spec file from Architect.**

### Summary

| WO | State | This session |
|---|---|---|
| `WO-004b` | Code+test done, board stale | ✅ Verified green + falsifiable; Architect flagged for line 1562. |
| `WO-CANON-XVII` | NOT RATIFIED | 🟠 Stop. |
| `WO-CANON-XVIII` | NOT RATIFIED | 🟠 Stop. |
| `WO-CANON-XXVIII` | SPEC GAP | 🔴 Report filed. |
| `CT4V-08` | No WO file | 🟠 Stop. |
| `WO-049-B1` | No WO file | 🟠 Stop. |

Five of six items cannot advance from the builder seat without ratification or a written WO file.
`WO-004b` closes cleanly on evidence already on disk plus the disconnection-falsifiability proof filed
in this Result block.

**Commit:** `73598b9` (both files — card 0070 result + FROM_BUILDER report — landed inside this
multi-purpose commit alongside WO-CANON-XIII §B; content is unchanged, just bundled by an overlapping
commit window).

