# FROM BUILDER — 2026-08-21 — spec-state report for card 0070's six items

**Card:** `0070_DISPATCH_your_six_never_started.md` · **Seat:** builder

The card names six never-started items. Per Rule 4h and the Four States: before building anything, verify
what state each item is actually in on disk. Five of six are NOT in an implementable state today; only
`WO-004b` is. Report below.

## `WO-CANON-XXVIII` — Adaptive Learning & Reinforcement — 🔴 SPEC GAP (as the card predicted)

**[VERIFIED]** `docs/architecture/Volume_XXVIII/` contains **one file** — `00_Adaptive_Learning_Reinforcement.md`,
91 lines, 1030 words — and **no `00_Metadata.md`**. Every other volume dir carries a Metadata file with
`volume · title · status · version · owner · architect · implementation · audit_status · dependencies` fields;
XXVIII does not.

**Content classification:** `00_Adaptive_Learning_Reinforcement.md:2` self-labels as
*"Scaffold · scope-locked · PLANNED. Authored + built BEHIND Presentable v1"*. That is the scaffold's own
declaration that it is not a build spec.

**What is present:** the constitutional boundary (ADR-Exec-005), the Learning Faculty framing, the four
domains RL is confined to, and a vector-reward pointer to Ch.5 Significance.

**What is missing to be buildable (comparing to Volume_XVII/XVIII structure):**
- 00_Metadata.md — status, ratification, owner, dependencies, `implementation:` field, DoD
- Chapter 1 body — faculty contract (§4 base shape), lifecycle binding (§3), envelope binding (§2), acceptance tests (FT/ST/IT)
- Chapters 2+ — none exist. XVIII deliberately has one chapter but declares that so; XXVIII does not.
- CA first-pass · David L3 ratification

**Do not build.** Per card 0070: *"A spec that thin is not a spec, and inventing the rest is the exact
drift David has been chasing."* Awaiting David's decision on scoping/authorship path.

## `WO-CANON-XVII` — Reflection Engine — 🟠 NOT RATIFIED (PROPOSE state)

**[VERIFIED]** `docs/architecture/Volume_XVII/00_Metadata.md:4`:
```
status: REVIEW — spec drafted 2026-08-13; awaiting CA first-pass + David L3. NOT RATIFIED.
```

Chapter Build Queue (§00_Metadata `Chapter Build Queue`): CH01 + CH02 both `READY FOR REVIEW`, not
IMPLEMENTATION READY. The DoD (`00_Metadata.md:120-131`) has three unchecked items:
`[ ] Consistency check … after WO-095 lands · [ ] CA first-pass · [ ] David L3`.

Per Four States (SOURCE_2026-08-17_david_four_states): AUTHORISED = "David/CA/LA has accepted this."
XVII is at PROPOSE. **Building it now collapses PROPOSE → IMPLEMENT.** Stops here.

## `WO-CANON-XVIII` — Self-Evolution — 🟠 NOT RATIFIED (PROPOSE state)

**[VERIFIED]** `docs/architecture/Volume_XVIII/00_Metadata.md:4` — identical wording to XVII:
`REVIEW — spec drafted 2026-08-13; awaiting CA first-pass + David L3. NOT RATIFIED.`

Same PROPOSE-state block as XVII. Additionally: XVIII depends on XVII (Ch.6 §6.8 origin) AND on
Volume XXII (genome — spec ratified) AND declares (`00_Metadata.md:81-86`):
*"XVIII has nothing to version until Volume XVII's read side lands (WO-095) — today the ledger has
produced zero confirmed lessons"* — so XVIII cannot land ahead of XVII / WO-095.

**Also in play:** the LIVE GATE from CLAUDE.md — *"XVIII is self-evolution — if any of it would change
the 9 CAL actions, 5 voice states or Character DNA, it stops at a proposal."* Reinforces stop.

## `WO-004b` — Volume V loose end — ✅ CLOSED IN CODE, BOARD ROW STALE

**[VERIFIED]** Code lives at `runtime/spine/spine.py:696-766` (`assemble_cognitive_state()` +
`build_embodiment_state()`). Test `tests/test_wo004_contracts.py` — **12/12 pass** (WO-004b-1..9 +
WO-004a-1..3). Completion log has WO-004b marked `✅ 2026-07-27 (batch)` at
`engineering/work_orders/COMPLETION_LOG.md:225`.

**Disconnection-falsifiability [VERIFIED]** by monkey-patching `assemble_cognitive_state` and
`build_embodiment_state` to broken shims:
- Broken `assemble_cognitive_state` (returns empty fields) → **WO-004b-3 fails RED**
- Broken `assemble_cognitive_state` (always conf=1.0) → **WO-004b-4 fails RED**
- Broken `build_embodiment_state` (empty response_text/motion_command) → **WO-004b-8 fails RED** (both branches)

Proof runs are shown in card 0070 Result block.

**The loose end named by card 0070:** the DISPATCH_BOARD.md still carries a stale OPEN row
(`DISPATCH_BOARD.md:1562`: `| OPEN | WO-004b CognitiveState + EmbodimentState wiring | Builder | ...`)
even though completion log row 225 records it as DONE with `test_wo004 12/12 · now live per-turn via WO-014`.
This is board-reconciliation work owned by the Architect (Rule 3 keeps the Builder out of the DISPATCH_BOARD
top-header + status-cell layout). **Flagging for Architect to reconcile line 1562.**

## `CT4V-08` — Self-Explanation Trace — 🟠 NO FORMAL WO FILE

**[VERIFIED]** Source is a CA cross-check note:
`docs/architecture/_intake/SOURCE_2026-08-14_CA_crosscheck_CANON-TRUTH-4V.md:162,169-171`:
*"CT4V-08: for 'why did you do that?' preserve trigger · intent · attention · affordance · capabilities
considered · decision · rejected alternatives · action · ACK · outcome · significance · learning."*

Board row at `DISPATCH_BOARD.md:730` points to `builder/0024` — but that card is not in QUEUE/DOING/DONE
(it's in the deleted set per `git status`). No WO spec file exists (`engineering/work_orders/WO-CT4V-08*`
= not present).

CT4V-08's requirement list (12 fields to preserve on every turn) is a substantive build; requires a WO
spec file with contract + tests + FREEZE respect (touches Executive path). **Awaiting WO file from
Architect.**

## `WO-049-B1` — Spatial Faculty v1 — 🟠 NO FORMAL WO FILE

**[VERIFIED]** Board row at `DISPATCH_BOARD.md:1783`:
`| 049-B1 | Spatial Faculty v1 (world model: window graph · affordances · body-fit · reachable/safe-landing/cost; Executive asks 'how do I get there?') | Builder (eLo OS) | P2 | ▶ RELEASED 2026-08-10 — buildable now`

Grep for `WO-049-B1` / `049-B1` / `WO_049_B1` across `engineering/work_orders/` returns only the board
row itself and the summary in `WO_REGISTER_TRUTH_2026-08-20.md:51`. No dedicated spec file.

The one-line board description is not a spec: it names components (window graph · affordances · body-fit ·
reachable/safe-landing/cost) but no contract, no tests, no dependencies, no acceptance criteria.
Per card 0070's binding rule: *"If the spec is thin, stop and report — never fill the gap yourself."*
**Awaiting a formal WO spec file.**

---

## Summary — what card 0070 actually lets me close today

| WO | State | Action |
|---|---|---|
| `WO-004b` | Code+test done. Board stale. | ✅ Card 0070 result documents the closure; Architect reconciles board line 1562. |
| `WO-CANON-XVII` | NOT RATIFIED | 🟠 Stop. Awaiting CA + David L3. |
| `WO-CANON-XVIII` | NOT RATIFIED | 🟠 Stop. Awaiting CA + David L3 (+ WO-095 land). |
| `WO-CANON-XXVIII` | SPEC GAP | 🔴 Stop. Awaiting David's authorship decision. |
| `CT4V-08` | No WO file | 🟠 Awaiting Architect WO. |
| `WO-049-B1` | No WO file (board row only) | 🟠 Awaiting Architect WO. |

Five of the six items cannot advance from the builder seat without either (a) L3 ratification of an existing
spec or (b) a written WO file with contract + tests. WO-004b is behaviourally closed; the discrepancy is a
board-row update the Architect owns.
