---
chapter: 3
title: "Release & Review Process — Dispatch, Review Gates, Freeze & Versioning"
volume: XXVII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - engineering/work_orders/README.md (WO dispatch + roles + lifecycle — AUTHORITATIVE)
  - engineering/work_orders/CHANGE_CONTROL.md (D-M — the two gates — AUTHORITATIVE)
  - engineering/work_orders/COMPLETION_LOG.md (where DONE is conferred — AUTHORITATIVE)
  - engineering/work_orders/DISPATCH_BOARD.md (the routable index)
  - engineering/Volume_1_Framework/03_review_standards.md · 04_freeze_standards.md
  - FREEZE_V1_LOCK.md · VERSIONING.md (repo root)
  - docs/architecture/DECISION_LOG.md (roles D-H · lanes D-LANES · freeze D-FREEZE/D-BUILD-NOW)
---

# Chapter 3: Release & Review Process

## 3.0 Purpose

This chapter formalises how a change moves from proposal to shipped-and-locked: who
dispatches work, who reviews it, what gates it passes, and how release, freeze, and
versioning are recorded. Like the rest of this volume it **consolidates live process** —
the Work-Order dispatch system, the two-gate Change Control policy, the freeze standards —
into one governed reference. It authors no new process.

The whole chapter rests on one already-ratified sentence (`CHANGE_CONTROL.md`, D-M):
**"David is the single approval gate. Agents propose and build; David approves. Nothing
skips him."** — held in tension with its companion clause: **"the gate is a final stamp,
not a pipeline stall."**

## 3.1 Roles (who does what) — CORRECTED 2026-08-10

Canon from `engineering/work_orders/README.md` §The agents and `DECISION_LOG.md` (D-H,
D-LANES), **corrected against the seats that actually exist.**

> *Amendment 2026-08-10.* The previous table listed **eight seats, two architects with
> independent authority, and a separate Debug and CEO Agent.* That was a product-era org chart.
> The seats below are the ones that exist and do work. Nothing is invented here; the retired
> rows are recorded beneath so the history is not lost (Append Rule).

**The six seats that exist:**

| Seat | Runs as | Lane | May write canon? | May write product code? |
|---|---|---|---|---|
| **David** | himself | **Sole L3.** Sets priority, gives the feel, approves. Software RESERVED collapsed to him alone 2026-08-10 (Ch.1 §1.3.1) | **Yes — he is the only one who confers law** | Yes (it's his machine); in practice he doesn't — he runs **no** backend/curl/kill commands |
| **Builder** | Claude Code (VS Code, David's Mac) | **eLo OS Python** — `~/elo-ai/` (D-I). Has terminal, git, build, relaunch, process-kill. All mechanical steps are its own | No | **Yes — its lane** |
| **Designer** | Claude Code (VS Code, David's Mac) | **Unity** — DISENELO Presence / desktop avatar | No | **Yes — its lane** |
| **Game** | Claude Code (VS Code, David's Mac) | **`eLo-Planet`** Unity lane | No | **Yes — its lane** |
| **Lead Architect** | Claude | Owns the canon; writes & verifies WOs; reconciles conflicts; **Markdown only — never product or test code** | **Yes — sole canon *drafter*, via ADR; David ratifies** | **No — hard line (D-LANES)** |
| **Chief Architect** | ChatGPT | **Advises and stress-tests.** Drafts rulings for David to accept or reject. May hold **LG-2 for robot hardware design review** (Ch.1 §1.3.1) | No — intake until the Architect files it and David ratifies | No |
| **Gemini R&D** | Gemini | Robot/hardware research → verbatim intake (`_intake/`) | No | No |

**Retired rows (recorded, not deleted):**
- **"Planning Assistants"** as a generic tier → superseded: the CA and Gemini R&D are named
  seats with defined outputs.
- **"Debug Agent"** as a separate seat → superseded: read-only fault tracing is a *mode* the
  Lead Architect runs (Rule #2 verification), not a person. It never had a queue.
- **"CEO / CEO Agent"** → superseded: **David is the CEO**, and reading the board / setting
  priority is his row above. The "→ becomes eLo OS post-engineering" note (D-H) is a parked
  product-era ambition, not a live seat.
- **"Chief Architect issues rulings that become law"** → corrected: **only David confers law**
  (Ch.1 §1.3). The CA's authority is persuasive, plus real LG-2 authority in the robot lane.

**Two standing facts that bind this table** (they are why the seats are shaped this way):
1. **Builder · Designer · Game run in VS Code on David's Mac and have full local capability.**
   Every mechanical step belongs to them. **David runs no backend commands.** An Architect
   asking David to run something a seat can run is a lane violation, not a favour.
2. **The Lead Architect coordinates and never executes in a product lane** — it creates and
   edits Markdown only (canon, specs, WOs, the board). A needed code change is *relayed* to the
   owning seat, never made.

**Lane law (D-LANES).** *The Architect coordinates; it does NOT execute in product lanes.*
The Architect owns Canon + the coordination layer only; it never edits `server.py`,
`runtime/*`, `core/*`, `prompts/*`, the Unity repo, or the game — those belong to the
Builder / UI / Game seats. A fix needing a product-lane change gets **one named owner** and
a WO/relay, never an Architect edit (and never a sub-agent firing the edit). The Boundary
line from the README: *Planning Assistants explore → Lead Architect specifies → Builder/UI
implement → CEO prioritises & routes. No agent crosses into another's lane* — One Brain
discipline extended to the org.

## 3.2 Work-Order dispatch (the unit of release)

The canon says *what* to build; the Work Order turns each buildable unit into a
self-contained packet one agent can execute without re-reading the whole canon
(`work_orders/README.md`). The layering:

```
docs/architecture/   →  WHAT eLo is (canon)
engineering/         →  HOW eLo evolves (process, freezes)
work_orders/         →  WHO does WHAT next (routable, addressable tasks)
```

**WO lifecycle** (`work_orders/README.md`):

```
DRAFT        Architecture is still writing the packet
READY        Complete + unblocked — an agent can pick it up now
BLOCKED      Complete but waiting on a dependency or a David decision
IN_PROGRESS  An agent has claimed it (owner set)
IN_REVIEW    Implementation done; Architecture verifies against the WO's acceptance tests
DONE         Verified + merged; Audit row updated
```

Each WO is `WO-NNN_Short_Name.md` from `_TEMPLATE.md`; `DISPATCH_BOARD.md` is the single
routable index the CEO Agent reads. **Non-negotiable rules every WO enforces**
(`work_orders/README.md`, pulled from `engineering/README.md` + `CO_WORKING_GUIDE.md`):
FREEZE_V1_LOCK (wrap, don't modify) · **evidence gates expansion (no DONE until acceptance
tests pass)** · atomic shared-state writes (`state_writer.patch`) · one-cognition (no WO
adds a second decider) · every WO names *files to touch*, *must-not-touch*, and *Definition
of Done*, and **traces to a purpose** (a roadmap deliverable or a canon volume — no orphan work).

## 3.3 The two review gates

From `CHANGE_CONTROL.md` (D-M, LAW). Every change takes exactly one path; no step is skipped:

```
PROPOSE  → agent relays the need to the Board (§0.5 Relay, or an existing WO)
SPEC     → the Architect writes/updates the WO or canon (single source of truth)
APPROVE  → David approves the WO / decision / any FREEZE unlock          ← GATE 1
BUILD    → the owning agent makes EXACTLY ONE change, to spec, in its lane
VERIFY   → build with 0 errors; run/attach the acceptance evidence; STOP and WAIT
HANDBACK → record it in COMPLETION_LOG.md (what changed · commit · evidence) → IN_REVIEW
REVIEW   → Architect verifies against spec → David approves → DONE + Audit updated  ← GATE 2
```

**The review chain in full (for canon and for code):**

1. **Lead Architect first-pass.** The Architect verifies the artifact against its spec /
   acceptance tests using Independent Runtime Verification — *re-run the test / read the
   artifact myself before reporting it* (Verify-before-claim). For canon, this is the
   READY-FOR-REVIEW promotion. The Architect states plainly what it could and could not
   confirm; `✅` requires having actually run it (`03_review_standards.md` honesty markers).
2. **Chief Architect review — ADVISORY, not a gate (amended 2026-08-10).** The CA reviews
   governance/architecture proposals and stress-tests them. It **does not sit as a required
   step between the Architect and David for software canon**, and it issues no law: software
   RESERVED collapsed to David as both L3 and LG-2 on 2026-08-10 (Ch.1 §1.3.1). The Architect
   may request a CA read when it wants the argument; nothing waits on it.
   **Exception — the robot lane:** for robot hardware (magnetics · force · pump · thermal ·
   battery · pinch points) **LG-2 is retained as a real second review, and the CA may hold it.**
   There the second pass *is* a gate, and the reviewer must not be the part's designer.
3. **David L3 — the single gate.** David confers Gate 1 (approve to build) and Gate 2
   (approve completed work → DONE). RESERVED classes — money · legal · safety · robot
   magnetics/force/pump · identity — always require David L3.
   **For software (canon, memory, personality, desktop behaviour) David's yes is the *whole*
   gate** — there is no second reviewer to wait for, and a seat blocked "pending LG-2" on a
   software item is blocked on nobody. **For robot hardware the second review still stands**,
   and the force-limiter / soft-stop scope must be DONE before anything is powered near David.

**Self-approval is forbidden** (`CHANGE_CONTROL.md` §3.2): an agent marking `DONE` means
*claimed*, not done. Truly DONE only exists in `COMPLETION_LOG.md` "Completed & approved"
with David's sign-off. The Architect batch-verifies so approvals are fast, not a bottleneck
— the gate is a final stamp, not a pipeline stall.

### 3.3.1 The engineering-phase review gates (for phased builds)

For phase-based work (`engineering/README.md` lifecycle), the review gates are the 12-step
lifecycle culminating in `10_freeze.md`, and every review explicitly checks the **Six
Architecture Constants** (`03_review_standards.md`): One Brain · One Executive · Faculties
Observe · FREEZE_V1_LOCK · Silence is Valid · Evidence Gates Expansion. *"If any constant is
violated, the review fails. No exceptions."* Gap-analysis and regression rules there forbid
"probably fine" resolutions — a gap must resolve to a deliverable, a later-phase dependency,
a documented limitation, or a named risk.

## 3.4 Freeze & release

Release in eLo OS is not a deploy event; it is a **freeze** — a permanent architectural
commitment that this behaviour is the regression baseline. Governed by
`engineering/Volume_1_Framework/04_freeze_standards.md`:

- **The freeze gate** — a phase freezes only when steps 01–09 are complete, all unit +
  conversation tests pass, a ≥1-hour long-session test is stable, no unresolved regressions
  against prior frozen phases, all six Architecture Constants verified, and `11_handover.md`
  is drafted *before* the freeze is signed.
- **Four freeze decisions:** `FROZEN ✅` · `CONDITIONAL ⚠️` (freezes with named, binding
  exceptions) · `REJECTED 🔴` (return to the failing step) · `ROLLBACK 🔴🔴` (revert via
  `git revert`, restore prior frozen state, record root cause + prevention). *There is no
  "unfreeze," only ROLLBACK.*
- **Freeze versioning** — `v1` first attempt, `v2` after rejection+revision, `v3` after
  rollback+re-implementation — creating an audit trail per phase.
- **What a freeze locks vs. does not** — locks runtime interfaces, injection formats,
  registry APIs, snapshot fields, validated conversation behaviour, cooldown defaults;
  does *not* lock internal implementation, env-tunable defaults, log format, or performance.

**FREEZE_V1_LOCK** is the standing runtime freeze (`runtime/executive.py` + `prompts/`),
lifted only by a scoped, logged David-granted unlock (Ch.1 §1.6; precedent D-K).

**Canon-level freeze (D-FREEZE → D-BUILD-NOW).** A freeze can be declared over the *canon*
to stop re-litigation while the *build* stays active. The recorded lesson: freezing the
canon "converts all energy to forward motion." At such a freeze the Architect's job becomes
**protection, not authorship** — keep the board honest, reconcile relays, and refuse
overhauls until we ship. Unfreeze is an explicit David decision, never an agent's judgement.

## 3.5 Versioning

- **Documents / volumes** carry semver in frontmatter (`version:`), starting `0.1.0` at
  first draft; every volume also carries `status`, `implementation`, and `audit_status`.
  Promotion is `DRAFT → REVIEW → IMPLEMENTATION READY → COMPLETE` (Ch.1 §1.4). This
  volume's chapters are `0.1.0 / READY FOR REVIEW`.
- **Faculties** are versioned units — semver on the faculty (`Volume_V/CONTRACTS.md` §4).
- **Envelope evolution** is *additive only, backward compatible* (ADR-0001 law 7): unknown
  fields must not be relied on; future extensions never break existing receivers.
- **Freeze versioning** (§3.4) tracks attempts per phase (`v1/v2/v3`).
- Detailed release/semantic-versioning conventions live in `VERSIONING.md`; this chapter
  points to it as authoritative and does not restate its numbering rules.

## 3.6 Where DONE is recorded (nothing chat-only)

- `DISPATCH_BOARD.md` — the routable queue + the Review-Gate note + the §0.5 Relay lane.
- `COMPLETION_LOG.md` — the **only** place DONE is conferred (claimed vs. approved).
- `DECISION_LOG.md` — where canon changes are recorded as ADRs (Ch.1 §1.3).
- `ARCHITECTURE_AUDIT.md` — the Audit row updated when a WO/volume reaches DONE/COMPLETE.

*Losing context is the failure mode this whole process exists to prevent*
(`CHANGE_CONTROL.md` §6): a paused change waiting for David beats an out-of-band change he
did not ask for.

## 3.7 Interaction with other volumes

- **Ch.1 (Canon Governance)** supplies the document classes, the DoD, and the RFC path this
  chapter operationalises for release.
- **Ch.2 (Engineering Standards)** supplies the standards the review gates check against
  (the acceptance-test discipline, the six constants, anti-fabrication).
- **Volume V / CONTRACTS.md** supplies the versioned-faculty + additive-envelope rules (§3.5).
- **All faculty volumes** ship through this dispatch → gate → freeze pipeline; a volume is
  COMPLETE only when the Audit can mark it so (the DoD's final line).

## 3.8 Open questions for David

*(Heading amended 2026-08-10 — software canon, David's single gate.)*

1. ~~**CA review as an explicit gate.**~~ **CLOSED 2026-08-10 by David's ruling.** Software
   RESERVED collapsed: CA first-pass is **not** a gate and is not named as one (§3.3 step 2).
   The remaining live piece is the *robot* lane, where LG-2 is retained and the CA may hold it
   — that one **should** be named explicitly in `CHANGE_CONTROL.md`, since it is the only
   second review that still legally exists. Architect action, David to confirm the wording.
2. **Release cadence — RE-SCOPED 2026-08-10.** The old form asked about "release cadence for
   the Life Era", which assumed a release *audience*. There is none: nothing ships to anyone.
   **"Release" here means "David starts living with it."** The real question is unchanged in
   substance and better stated: **when does a change need the full freeze ceremony, versus just
   working?** Recommendation, unchanged: keep the freeze for anything touching the frozen brain
   (`runtime/executive.py`, `prompts/`) or any prior frozen baseline; WO-only for additive
   senses and surfaces. The trigger for a freeze is **"David feels it's coherent"**, not a date.
3. **`VERSIONING.md` scope.** Confirm `VERSIONING.md` is authoritative for both document
   semver *and* runtime/release versioning, or split them. This chapter currently defers all
   numbering to it.
4. **Debug authority — RE-SCOPED 2026-08-10.** There is no Debug seat (§3.1 retired rows).
   Read-only fault tracing is a mode the **Lead Architect** runs, which makes the Architect the
   sole `ARCHITECTURE_AUDIT.md` writer by default. Confirm that is acceptable, noting the risk
   it creates: **the same agent writes the canon and grades conformance to it.** The mitigation
   is Verify-before-claim and the honesty markers (`✅` = I ran it) — not a second seat. If
   David wants a real separation here, that is a new seat and his call.

## 3.9 Canon References

- `engineering/work_orders/README.md` — roles, WO lifecycle, non-negotiable WO rules.
- `engineering/work_orders/CHANGE_CONTROL.md` — D-M, the two gates, the five hard rules.
- `engineering/work_orders/COMPLETION_LOG.md` · `DISPATCH_BOARD.md` — where DONE lives / the queue.
- `engineering/Volume_1_Framework/03_review_standards.md` — six constants, honesty markers.
- `engineering/Volume_1_Framework/04_freeze_standards.md` — freeze gate, decisions, versioning.
- `FREEZE_V1_LOCK.md` · `VERSIONING.md` (repo root) — runtime freeze + versioning.
- `docs/architecture/DECISION_LOG.md` — D-H (roles), D-LANES, D-I (write-scope),
  D-FREEZE/D-BUILD-NOW (canon freeze), D-K (scoped unlock precedent).

---

```
Chapter 3 — Release & Review Process
Status: READY FOR REVIEW  (amended 2026-08-10 — personal-scope re-scope; NOT ratified)
Files: Volume_XXVII/03_Release_and_Review_Process.md
Amendment 2026-08-10: §3.1 eight-seat table CORRECTED to the six seats that exist (Builder ·
  Designer · Game · Lead Architect · Chief Architect · Gemini R&D, with David as sole L3;
  Planning-Assistants/Debug/CEO rows retired, recorded not deleted) · §3.3 CA review is
  ADVISORY for software, LG-2 RETAINED for robot hardware · §3.8 Q1 closed, Q2/Q4 re-scoped.
Formalises (does not recreate): work_orders/{README,CHANGE_CONTROL,COMPLETION_LOG,DISPATCH_BOARD}
  + Volume_1_Framework/{03_review,04_freeze}_standards + FREEZE_V1_LOCK + VERSIONING.
Honours: single approval gate (final stamp, not stall) · Lanes · Evidence gates expansion · FREEZE discipline.
Open Questions: 4 (for CA / David)
```

READY FOR REVIEW
