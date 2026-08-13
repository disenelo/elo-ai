# WO-CANON-XXVII — Canon Governance: build the governed index + the four governance checks that actually run

**Owner:** **Architect** (Markdown — canon governance is the Architect's lane) with **Builder** for the two
code items (the governance check script + the pre-commit secret check). **Priority:** P4 — Tier C.
**Status:** OPEN — **REWRITTEN 2026-08-13.** The previous version was a **plan-to-plan**: blocked on eleven
rulings, **no "Files to touch" section** (breaking the rule its own volume states — Ch.1 §1.4 / Ch.3 §3.1:
*"every WO names its files to touch, must-not-touch, and Definition of Done"*), and **five of its six
acceptance criteria were unfalsifiable** (*"the 8-item DoD holds for a sample promotion"*, *"the six
Architecture Constants review passes"*, *"the freeze gate criteria apply to a sample freeze"*, *"coverage
floor + Presence Test demonstrated"*, *"honesty markers present"* — none names an artefact, an input, or a
failing condition). This version is buildable: named files, executable checks, and **only the ruling that
genuinely blocks**.

**Canon refs:** Volume XXVII — Ch.1 `01_Canon_Governance.md` (§1.4 the 8-item DoD; the WO rules), Ch.2
`02_Engineering_Standards.md`, Ch.3 `03_Release_and_Review_Process.md` (§3.1 non-negotiable WO rules,
§3.3.1 the six Architecture Constants, §3.4 freeze gate). ADR-0003 (scope) · D-M (Change Control) ·
D-LANES · **`docs/architecture/adr/LAW-017_Approval_Scope.md` O-17.1/O-17.2 (the ID-numbering question)**.
Governing habit: *this volume does not recreate — it consolidates and points; where chapter and source
disagree, the source wins.*

---

## IRV — verified 2026-08-13 (every source this WO points at was confirmed to exist)

**Present:** `docs/architecture/00_CANON_INDEX.md` · `DECISION_LOG.md` (32 IDs, append-only header, "These
are law") · `ARCHITECTURE_AUDIT.md` · `engineering/work_orders/CHANGE_CONTROL.md` · `README.md` ·
`COMPLETION_LOG.md` · `DISPATCH_BOARD.md` · `_TEMPLATE.md` (its §5 **is** "Files to TOUCH") ·
`engineering/standards/{architecture,coding,documentation,testing}.md` · `VERSIONING.md` ·
`FREEZE_V1_LOCK.md` · `Volume_V/CONTRACTS.md`. **Nothing this WO consolidates is missing.**

**Measured drift (this is what the checks must catch):**
- **103 of 110 Work Orders have no "Files to TOUCH" section** — the rule Ch.1 §1.4 and Ch.3 §3.1 both call
  non-negotiable is honoured by 7 WOs. Governance that nothing checks is governance that does not happen.
- **`DISPATCH_BOARD.md` contains 196 occurrences of `DONE`**, while Ch.1 §1.4 says DONE is conferred **only**
  in `COMPLETION_LOG.md` with David's sign-off. At least two of those board lines are demonstrably false
  (Vol XXV is dead code — see WO-CANON-XXV; Vol XV has no consumers — see WO-CANON-XV).
- **No pre-commit hook and no CI directory exist** (`.git/hooks` holds only `*.sample`). The Vol XXIII
  OQ-3.6.3 secret check has no host.
- **`LAW-017` now exists** and records that `LAW-001`…`LAW-016` **do not exist anywhere in the repo** — the
  `LAW-NNN` series has exactly one member. That is the live ID-numbering problem, and it is XXVII's.

## Problem / Goal

Almost all of the governance surface is live and correct in `engineering/` and `docs/architecture/`. What
is missing is (a) **one index that points at it without drifting from it**, and (b) **anything that
actually checks the rules**. The measured drift above is the proof: the rules are written, and 94% of WOs
break one of them, because no check exists.

Goal: a single governed index whose links are verified by a test, plus four executable governance checks
and one secret check. Consolidate and point — **do not duplicate the standards into the volume.**

## Scope to DoD

### A. The governed index (Ch.1) — Markdown, Architect

Write `docs/architecture/Volume_XXVII/04_Governed_Index.md` as **the routable index**: for each governance
concern, one row naming **the authoritative file and section** — never a restatement of its content.
Concerns: canon vs ADR vs audit · the change process (D-M) · the 8-item Definition of Done · engineering
standards · the WO lifecycle (`DRAFT→READY→BLOCKED→IN_PROGRESS→IN_REVIEW→DONE`) · release/review/freeze ·
versioning · the freeze lock · the contracts.

Enforce, in the index text, the four rules that already are canon:
1. **A promotion not reflected in `00_CANON_INDEX.md` did not happen** — the affected volume and the Index
   are updated in the same pass.
2. **Canon changes only via the Architect, by ADR** (D-LANES).
3. **Decision IDs are immutable and append-only** — superseded is marked in place, never deleted.
4. **Self-approval is forbidden. DONE is conferred only in `COMPLETION_LOG.md`, with David's sign-off.**
   A `DISPATCH_BOARD.md` line is a *status*, never a conferral.

Add an **OPEN REGISTER** table at the foot of the index: every governance question that is not yet ruled,
with its recommendation and its decider. Unruled items are **recorded there, not used as blockers** — that
is what turns the old plan-to-plan into a shippable document.

### B. The four governance checks (Builder — `scripts/governance_check.py`, run by a test)

Each check reads real files and fails on a real condition. These replace the five unfalsifiable criteria.

| Check | Reads | Fails when |
|---|---|---|
| **G-1 link integrity** | the governed index | any path or anchor it points at does not exist on disk |
| **G-2 index/volume drift** | every `Volume_*/00_Metadata.md` `status:` + `implementation:` vs `00_CANON_INDEX.md` | a volume's status in its own metadata disagrees with the Index's row for it |
| **G-3 WO shape lint** | `engineering/work_orders/WO-*.md` | a WO **raised on or after the cutoff date** lacks *Files to TOUCH*, *Files MUST-NOT-TOUCH*, or *Definition of Done*. Pre-cutoff WOs are **reported as a backlog count, not failed** (103 today) — the rule starts binding, the history is not rewritten |
| **G-4 DONE ownership** | `DISPATCH_BOARD.md` + `COMPLETION_LOG.md` | a WO is marked `DONE ✅` on the board with **no** corresponding `COMPLETION_LOG.md` entry carrying David's sign-off |

**G-4 will fail on the current board.** That is intended: it is the mechanism that would have caught Vol
XXV's false DONE. The Builder ships the check; **the Architect fixes the board lines** — do not "fix" G-4
by loosening it.

### C. The pre-commit secret check (Builder — the one item inherited from Vol XXIII OQ-3.6.3)

`scripts/check_secrets.py`, invoked from `.githooks/pre-commit` (with the repo configured to
`core.hooksPath=.githooks` so the hook is version-controlled rather than living in `.git/hooks`).
Rejects a staged diff containing an API-key-shaped literal or any tracked `.env`. Must be runnable
standalone so the test can call it on a fixture.

### D. Standards + lifecycle: point, do not copy (Ch.2/Ch.3)

The coding MUSTs, naming table, testing hierarchy, WO lifecycle, Change-Control's five hard rules and the
security floor **stay canonical in `engineering/standards/` and `CHANGE_CONTROL.md`**. Volume XXVII cites
them by file and section. Any duplicated paragraph is drift waiting to happen and fails review.
Record two observed facts rather than ruling on them: the Python version the repo actually runs on, and
that `engineering/standards/` is the standards home.

### E. Fold in what is already ruled (not open questions — closed ones)

- `LAW-017` exists and is the approval-scope authority; **Vol XXVII contains zero occurrences of `LG-2`**
  and must carry the software/hardware approval split (relayed from `WO-CANON-XXIII` §C).
- Freeze authority is a **David L3** act — already canon (`LAW-017` B3); state it, do not re-ask it.

## Files to TOUCH
- `docs/architecture/Volume_XXVII/04_Governed_Index.md` — **NEW** (the index + the OPEN REGISTER)
- `docs/architecture/Volume_XXVII/00_Metadata.md` — add Ch.4 to the chapter queue
- `docs/architecture/00_CANON_INDEX.md` — one row pointing at the governed index
- `scripts/governance_check.py` — **NEW** (G-1…G-4)
- `scripts/check_secrets.py` — **NEW**
- `.githooks/pre-commit` — **NEW**
- `tests/test_canon_xxvii_governance.py` — **NEW**
- `engineering/work_orders/DISPATCH_BOARD.md` — **Architect lane**: correct the board lines G-4 flags

## Files MUST-NOT-TOUCH
- `engineering/standards/*` (the standards home — cite it, never copy it into the volume)
- `docs/architecture/DECISION_LOG.md` **existing IDs** (immutable, append-only — new entries append only)
- `FREEZE_V1_LOCK.md` / `VERSIONING.md` (cited, not rewritten)
- `COMPLETION_LOG.md` (Architect + David only — no automated writes, ever)
- Any product/runtime code: this WO adds `scripts/` + a hook + a test, and nothing else

## Definition of Done
- The governed index exists, every link it makes resolves (**G-1 green**), and it duplicates no standard.
- **G-1…G-4 run from a test** and each has been demonstrated to fail on a planted violation *and* pass on a
  clean one. A check that cannot fail is not a check.
- The pre-commit secret check rejects a planted `.env` secret in a staged fixture and is wired via
  `core.hooksPath`.
- The WO-shape rule (G-3) binds from the cutoff date, and the 103-WO backlog is **reported**, not hidden.
- G-4's current failures are recorded as an explicit list of board lines to correct (starting with
  WO-CANON-XXV and WO-CANON-XV).
- The OPEN REGISTER carries every unruled governance question with its decider — **so the volume ships
  without waiting on any of them.**
- **This WO does not confer DONE and does not promote Volume XXVII to RATIFIED.** Promotion is CA
  first-pass → David L3, with the affected volume + `00_CANON_INDEX.md` + `DECISION_LOG.md` updated in the
  same pass.

## Tests (`tests/test_canon_xxvii_governance.py` — all falsifiable, all named)
- **GT-1** `governance_check.G1_links()` returns zero unresolved paths for the governed index; a test
  fixture with a deliberately broken link returns exactly one.
- **GT-2** `G2_drift()` flags a volume whose `00_Metadata.md` status disagrees with `00_CANON_INDEX.md`;
  verified against a planted mismatch. *(A real one exists today: `Volume_XV/00_Metadata.md` says
  `implementation: PENDING` while the file and wiring are on disk — see WO-CANON-XV.)*
- **GT-3** `G3_wo_shape()` fails a fixture WO dated after the cutoff with no *Files to TOUCH*, passes one
  with all three sections, and reports the pre-cutoff backlog as a number without failing.
- **GT-4** `G4_done_ownership()` flags a board line marked `DONE ✅` with no `COMPLETION_LOG.md` entry;
  asserted against a fixture board + log pair. **Documented expectation: it flags real lines on the current
  board.**
- **GT-5** `check_secrets.py` rejects a staged fixture containing an API-key-shaped literal and accepts a
  clean one; a tracked `.env` is rejected.
- **GT-6** No duplication: the governed index contains no verbatim paragraph ≥ 25 words copied from
  `engineering/standards/*` or `CHANGE_CONTROL.md` (cite, don't clone).
- **GT-7** Append-only: `DECISION_LOG.md` IDs are unique and no existing ID's text was modified relative to
  `HEAD` (git-diff assertion).

## Dependencies + blocked-by
- **Blocked by: NOTHING.** Every source file this WO consolidates was verified to exist; the checks and
  the secret hook need no ruling. The old WO's eleven blockers were mostly *preferences to confirm*, not
  gates, and they are now **rows in the OPEN REGISTER** instead: Governance-DoD variant · audit
  write-ownership · standards home · Python version · naming scope · testing-role mapping · CA Gate-1a ·
  release cadence · VERSIONING scope. Recording an unruled question is not the same as being blocked by it.
- **The one genuinely decision-pending item:** the **ID-numbering standard** — `LAW-017` **O-17.1** (one ID,
  two laws: keep `LAW-017` covering both parts, or split with a 25-citation sweep) and **O-17.2**
  (`LAW-001`…`LAW-016` do not exist — *do not back-fill sixteen laws to make the numbering look complete*).
  This blocks **only §A's ID-standard row**, which ships as `PENDING — David's call` in the OPEN REGISTER.
  The rest of the WO proceeds.
- Cross-volume: **Vol XXIII** (defers the pre-commit secret check up to here; XXVII must carry the `LG-2`
  software/hardware split it currently has zero mentions of) · Vol V CONTRACTS (cited by the index).
- **Gate:** CA first-pass → **David L3** ratification. Not IMPLEMENTATION READY nor COMPLETE on the
  Architect's promotion alone.

## Lane
Architect (Markdown — the governed index, the OPEN REGISTER, folding the ruled items, and correcting the
board lines G-4 flags: **this IS the Architect's lane**). Builder for `scripts/governance_check.py`,
`scripts/check_secrets.py`, `.githooks/pre-commit` and the test. Standards stay canonical in
`engineering/standards/` — do not duplicate.
