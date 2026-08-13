---
chapter: 1
title: "Canon Governance — Canon vs ADR vs Audit, the Change Process, and the Definition of Done"
volume: XXVII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - docs/architecture/00_CANON_INDEX.md (the master map + the Definition of Done — AUTHORITATIVE for DoD)
  - docs/architecture/DECISION_LOG.md (the ADR ledger — AUTHORITATIVE for ratified decisions)
  - docs/architecture/ARCHITECTURE_AUDIT.md (live conformance status — AUTHORITATIVE for the Audit)
  - docs/architecture/ARCHITECTURE_BIBLE.md (enduring philosophy — the Bible class)
  - docs/architecture/ARCHITECTURAL_PRINCIPLES.md (the constitution + Runtime Invariants)
  - engineering/work_orders/CHANGE_CONTROL.md (D-M — how change happens; the gates)
  - FREEZE_V1_LOCK.md · VERSIONING.md (repo root — freeze + versioning discipline)
---

# Chapter 1: Canon Governance

## 1.0 Purpose

Every other volume in this canon says *what eLo is*. This chapter says **how the canon
itself is governed** — how a document becomes law, how law is changed, how "done" is
decided, and how the three record-keeping systems (Decision Log, Canon Index, Audit)
interlock so that no fact is lost and no claim outruns reality.

This chapter **invents almost nothing.** The governance it describes is already live
across `docs/architecture/` and `engineering/`. Its job is to *name the constitution*
and point precisely at the artifacts that enforce it, so **David — or a seat that has just
lost its context to a compaction — reads one page and knows the rules.**

### 1.0.1 Who this governance is for — scope amendment (2026-08-10)

**eLo is David Charles's personal companion.** The Kickstarter / product / sharing track is
PARKED (`DISPATCH_BOARD.md`: *"PERSONAL tool — for David's own use, NOT for sharing"*). This
volume was written in the product era and assumed an organisation that does not exist: an
eight-seat role table, two architects with independent authority, and a review chain in which
a Chief Architect gate sits between the Architect and David.

What this amendment changes, and what it deliberately does not:

**RETIRED (product-era):**
- The eight-seat role table as a description of reality (§3.1 — corrected there).
- **CA first-pass as a *required* gate** for software canon. It contradicted the 08-10 ruling
  inside this same volume (§1.3.1).
- **The Chief Architect "issues rulings that become law."** Only David confers law (§1.3).
  The CA advises, stress-tests, and drafts; it does not legislate.
- The **stranger-onboarding bar** ("a person who has never seen the project can start
  implementing within one session") — Ch.2 §2.1, replaced there with the bar that actually
  matters: **future-me after a compaction.**
- Product-era release framing ("release cadence", "the Life Era" as a shipping concept) —
  Ch.3 §3.8 Q2.

**KEPT, unchanged, because it is good and load-bearing:**
- **Canon vs ADR vs Audit** (§1.1) — the three-class separation is the discipline that keeps
  claims honest, and it matters *more* with fewer people checking, not less.
- **The Definition of Done** (§1.4), including *"the Builder can implement without inventing
  anything"* — the operational test survives intact.
- **The Append Rule, ID immutability, evidence gates, FREEZE discipline, Verify-before-claim.**
- **`ARCHITECTURE_AUDIT` as reporting, never law.**

**The governing sentence, restated for the personal era:** governance here exists so *David*
can trust what the record says without re-reading the whole repo — not so an external
audience can be satisfied that a process was followed. Every rule that survives, survives
because it protects the record. Every rule that was protecting an audience is retired.

The one line that governs this entire chapter is already in
`ARCHITECTURAL_PRINCIPLES.md` §Governance:

> **Canon before implementation.** Nothing is "done" because it was described; it meets
> the bar and the audit marks it complete.

## 1.1 The Three Document Classes (Canon vs ADR vs Audit)

The **Executive Directive — three document classes** (`DECISION_LOG.md`, 2026-07-27) is
canon. Implementers build against the **Canon**, never against conversational prompts.
The classes, and where each lives:

| Class | What it is | Authority | Lives in |
|---|---|---|---|
| **Architecture Bible** | Enduring philosophy & vision — *why* eLo exists | Inspiration / intent | `ARCHITECTURE_BIBLE.md` (esp. Vols I–III); one-page constitution in `ARCHITECTURAL_PRINCIPLES.md` |
| **Architecture Canon** | The normative engineering spec = **law** | Binding — the source of truth | The Volume folders + `Volume_V/CONTRACTS.md` + the ADRs in `DECISION_LOG.md` |
| **Architecture Audit** | Live implementation status, compliance, technical debt | Reporting — never sets law | `ARCHITECTURE_AUDIT.md` |

**The rule (verbatim, `DECISION_LOG.md`):** *the Canon is the source of truth; the Audit
reports conformance to it.* The Audit never overrides the Canon; it measures the distance
between them. When they disagree, one of two things is true and must be recorded: either
the implementation drifted (an Audit finding → a Work Order to close the gap) or the Canon
was wrong (a decision → an ADR that amends the Canon). It is never resolved silently.

An **ADR** (Architecture Decision Record) is a *ratified change to the Canon*. It is not a
fourth class — it is the mechanism by which the Canon class evolves. All ADRs live in one
append-only ledger, `DECISION_LOG.md`, and are law once ratified (see §1.3).

### 1.1.1 Why the separation is load-bearing

- **Bible without Canon** = vision no one can build against (drifts into prose).
- **Canon without Audit** = law no one checks (drifts into fiction — the exact failure
  the Verify-before-claim rule exists to prevent).
- **Audit without Canon** = status reporting with no bar to report against.

The three only work as a triangle: Bible inspires → Canon specifies → Audit verifies →
findings feed decisions → decisions (ADRs) amend Canon. This mirrors the layering in
`ARCHITECTURAL_PRINCIPLES.md`: Constitution → Canon → Engineering → Runtime.

## 1.2 The Canon Index — the single map

`00_CANON_INDEX.md` is the **LIVING master index** of all 28 volumes: what each is,
whether it exists in the live system, its priority, and where its canonical spec lives.
It is the one file that turns "build 28 volumes" into a tracked programme.

Governance functions of the Index (all already live):

- **Status legend** — `✅ Live · ⚠️ Partial · 🔴 Future · 📝 Spec drafted · 🧩 Scaffold`.
  A volume's row states its true state, not its aspiration.
- **The DoD gate** (§1.4) is inherited from `Volume_V/00_Metadata.md` and restated in the
  Index. Volume V is the reference template for the bar.
- **Roadmap reconciliation** — before any *new* volume number is minted, the Index maps
  the topic onto what already exists ("most of the unfinished list already exists under
  another name"). This is the CHECK-BEFORE-BUILD principle applied to the canon itself
  (`ARCHITECTURAL_PRINCIPLES.md` §6 binds the Architect too).

**Rule:** the Index is updated after **every** volume/chapter promotion. A promotion that
is not reflected in the Index did not happen for governance purposes.

## 1.3 The Decision Log (ADR ledger)

`DECISION_LOG.md` is the append-only ledger of ratified governance decisions. Its opening
line is the law: *"Ratified governance decisions. **These are law.** Every volume,
faculty, and Work Order conforms."*

**Structure (as it stands live):**

- Each decision carries an **ID, date, status, and rationale.** IDs are immutable — the
  Thematic Index at the foot of the log is explicitly "a lens over them," never a rename.
- **Numeric/decision IDs are IMMUTABLE.** New decisions *append*; they never rewrite prior
  ones. A superseded decision is marked superseded in place (e.g. D-K's 07-27 ruling is
  struck through and annotated "superseded 07-31"), never deleted — the Append Rule from
  `engineering/standards/documentation.md`.
- **Status vocabulary in use:** `ACCEPTED · LAW`, `RATIFIED`, `RATIFIED (change)`,
  `ACCEPTED`, `RESOLVED`, `DRIFT FOUND`, `PENDING DAVID`, `REOPENED`. The status is the
  decision's legal state; only David (L3) confers ratification.
- **Fact Checks (FC-n)** live alongside ADRs — verified findings against live code (e.g.
  FC-2 significance-formula drift). A Fact Check is the Audit's voice inside the ledger:
  it records where Canon and code disagree and names the reconciliation action.

**Who may write it (LAW, D-LANES + Change Control §3.6):** *canon changes only by the
Architect, via ADR.* The **Lead Architect (Claude)** drafts canon and files the ADR; **David
(L3)** ratifies — and **only David confers law**. The **Chief Architect (ChatGPT)** advises,
stress-tests, and drafts rulings for David to accept or reject; **Gemini R&D** produces
research intake. Both produce **intake** (`docs/architecture/_intake/`, stored verbatim), which
is not canon until the Architect files it and David ratifies it.

> *Amended 2026-08-10.* This paragraph previously read *"the Chief Architect issues top-level
> rulings"*, which contradicted this same section's *"only David (L3) confers ratification"*
> and the Vision Spine's "David is sole L3". The contradiction is resolved in David's favour:
> **advice is not law.** The CA's value is that it argues with the Architect before David has
> to — not that it can rule.

### 1.3.1 Approval authority — David is the single L3, and how LG-2 works (2026-08-10)

The audit found **zero occurrences of `LG-2` in this entire volume**, meaning the constitution
structurally could not express David's own ruling on approvals. It is written here now.

**The ruling** (`CANON_RULINGS_2026-08-10.md` §XXIII, David L3, 2026-08-10):

| Scope | L3 | LG-2 (second review) | Effect on this volume |
|---|---|---|---|
| **Software** — desktop behaviour, **canon**, memory, personality, the OS | **David** | **David** — *collapsed; no second reviewer* | Canon promotion needs David alone. CA review is optional advice, not a gate. |
| **Robot hardware** — magnets, actuators, force, pump, thermal, battery, pinch points | **David** | **RETAINED — a real, separate second review** | Unchanged. These stay RESERVED and cannot be closed by David alone. |

**The rules that follow (MUST):**

1. **`LG-2` is a second *reviewer*, not a rank.** It is the requirement that a
   safety-relevant decision be looked at by someone other than the person who made it.
2. **Software RESERVED collapsed to David on 2026-08-10.** For anything in this volume's
   scope — canon, ADRs, volume promotion, memory, personality, desktop behaviour — David is
   both L3 and LG-2. **One yes is the whole gate.** A seat waiting for a second reviewer on
   software is waiting for nobody.
3. **Robot hardware RESERVED did NOT collapse.** *"The robot is a physical object."* The robot
   lane keeps LG-2 as a real second review, and **LG-2 must not be the same person who designed
   the part** (the Chief Architect may hold LG-2 for robot design review). **The force-limiter /
   soft-stop scope must be DONE before anything is powered near David.** No canon-governance
   convenience overrides that.
4. **Money · legal · safety stay RESERVED** and always require David explicitly.
5. **When in doubt about which side a change sits on, it is hardware.** Safety asymmetry: the
   cost of an unnecessary second review is a delay; the cost of a missing one is David.

Volume XXIII owns the full RESERVED taxonomy and trust boundaries; this section exists so the
*governance constitution* can express the split at all, and so no chapter here can be read as
requiring a second reviewer that the ruling abolished — or as waiving one it kept.

## 1.4 The Definition of Done (the bar)

**A volume/WO/faculty is done only when it meets the DoD — not when it is described.**
This is the Canon-before-implementation principle made checkable. The bar is inherited
from `Volume_V/00_Metadata.md` and restated in `00_CANON_INDEX.md`. A volume advances
`DRAFT → REVIEW → IMPLEMENTATION READY → COMPLETE` only when **all** of:

- [ ] Every chapter received and filed
- [ ] Every faculty contract defined (typed inputs / outputs / confidence / failure modes)
- [ ] Every state machine defined (universal lifecycle per `Volume_V/CONTRACTS.md` §3)
- [ ] Every API / message envelope defined (nine-field wire format per `CONTRACTS.md` §2)
- [ ] Every failure mode documented (graceful degradation)
- [ ] Acceptance tests written for each chapter (functional / stability / integration)
- [ ] The Builder Agent can implement without inventing anything
- [ ] The Audit can mark COMPLETE

**Volume V is the reference template for this bar.** The final line — *the Builder can
implement without inventing anything* — is the operational test: if a WO or chapter forces
the Builder to guess, it has not met the DoD.

At the **Work Order** level the same bar is expressed as the WO lifecycle
(`engineering/work_orders/README.md`): `DRAFT → READY → BLOCKED → IN_PROGRESS → IN_REVIEW
→ DONE`, where **"Evidence gates expansion" — a WO cannot go DONE until its acceptance
tests pass**, and every WO names its *files to touch*, *must-not-touch*, and *Definition
of Done*. (Full release/review mechanics are Chapter 3.)

### 1.4.1 Canon status vocabulary (this volume's own discipline)

Per the standing rule for this build: a document is never marked `RATIFIED` or `COMPLETE`
by the drafting Architect. The Architect promotes a document only as far as **READY FOR
REVIEW**; `IMPLEMENTATION READY` and `COMPLETE` are conferred by **David (L3)** (Chapter 3).
This chapter, and this whole volume, therefore sit at **READY FOR REVIEW**.

> *Amended 2026-08-10.* Previously: *"conferred … by the Chief Architect and David (L3)
> respectively."* Software RESERVED collapsed to David (§1.3.1) — **the CA confers nothing.**
> The self-promotion bar is unchanged and still absolute: the Architect never ratifies its own
> draft. That rule exists to stop the record flattering itself, and it survives the collapse
> intact — it is now the *only* thing standing between a draft and law, so it matters more.

## 1.5 The RFC / Change Process

There is exactly one path a change may take, and it is already law: **D-M — Change Control
Policy** (`engineering/work_orders/CHANGE_CONTROL.md`). This *is* the canon's RFC process;
Chapter 3 details the release/review mechanics. In brief:

```
PROPOSE → SPEC → APPROVE (Gate 1, David L3) → BUILD (one change, to spec, in lane)
        → VERIFY (0 errors + acceptance evidence) → HANDBACK → REVIEW (Gate 2, David L3) → DONE
```

The five hard rules that make it an RFC process rather than a suggestion box:

1. **David is the single approval gate.** Agents propose and build; David approves. The
   gate is a *final stamp, not a pipeline stall* — READY work whose functional
   dependencies are met keeps moving while approvals batch-clear.
2. **One change at a time.** One WO = one change, to spec, then wait. No multi-change
   batches (batches are what got reverted).
3. **Nothing chat-only.** Every change is committed **and** recorded (`COMPLETION_LOG.md`);
   specs/decisions are pinned in canon (`docs/architecture/_refs/`, `_intake/`), never left
   in conversation. Losing context is the failure mode the policy exists to prevent.
4. **Canon changes only by the Architect, via ADR** (§1.3).
5. **Revert-safe.** Every change works from a recorded clean baseline; a rejected change
   reverts cleanly, no half-states left running.

**For a canon change specifically** (a new/amended ADR, a volume promotion), the RFC flow is:

```
Architect proposal (or CA advice the Architect adopts)
  → drafted into the affected volume/ADR as READY FOR REVIEW
  → [optional: CA stress-test — advice, NOT a gate]
  → DAVID L3 ratification                                   ← the only gate
  → appended to DECISION_LOG.md + the volume + 00_CANON_INDEX.md updated in the same pass
```

No canon fact changes outside this flow.

> *Amended 2026-08-10.* The flow previously required a **Chief Architect first-pass** between
> the draft and David. Software RESERVED collapsed to David as both L3 and LG-2 (§1.3.1), so a
> required CA gate is retired: it is now an optional pre-read the Architect may request when it
> wants an argument, and David never waits on it. **For robot-hardware canon the second review
> is NOT optional** (§1.3.1 rule 3) — the CA may hold LG-2 there.
>
> One procedural finding recorded with this amendment: the 2026-08-10 rulings currently live in
> a standalone file (`CANON_RULINGS_2026-08-10.md`), not as numbered entries in
> `DECISION_LOG.md`. By this chapter's own test (§1.3, "all ADRs live in one append-only
> ledger") **they are not yet properly filed.** That is an Architect action, not a David one.

## 1.6 FREEZE discipline

Freeze is how the canon protects itself from re-litigation and how the runtime protects
itself from churn. Two distinct freezes exist and must not be conflated:

**(a) FREEZE_V1_LOCK — runtime code freeze.** `runtime/executive.py` and `prompts/` are
never modified; infrastructure evolves *around* them (`FREEZE_V1_LOCK.md`;
`engineering/standards/coding.md`; `engineering/standards/architecture.md` Invariant #7).
The only exception is a **scoped, logged unlock** David grants (precedent: D-K, the scoped
`prompts/` unlock — one change at a time, revert-safe baseline, David reviews each slice,
re-freeze on completion). A perceived *need* to edit a frozen file is treated as a signal
the design is wrong (`coding.md` §FREEZE_V1_LOCK).

**(b) Phase / canon freeze — architectural decision freeze.** Per
`engineering/Volume_1_Framework/04_freeze_standards.md`: *a freeze is a permanent
architectural decision… there is no "unfreeze," only ROLLBACK.* Frozen behaviour is the
regression baseline; architecture cannot be redesigned (bugs can be fixed, architecture
cannot change). The freeze gate, the four freeze decisions (`FROZEN / CONDITIONAL /
REJECTED / ROLLBACK`), and freeze versioning (`v1/v2/v3` audit trail) are all defined
there and are cited, not restated, here.

**Canon-level freeze precedent (D-FREEZE → D-BUILD-NOW, `DECISION_LOG.md`):** the canon
can be declared *stable* ("no re-litigating settled decisions") while the *build* stays
fully active. The lesson recorded there — "we were re-architecting faster than building" —
is why the Architect's job at a freeze becomes *protection, not authorship*: keep the board
honest, reconcile relays, and **refuse overhauls** (even well-meaning ones) until we ship.

## 1.7 How the three record-keepers interlock

```
                 amends (ADR, David L3)
   DECISION_LOG ─────────────────────────►  the VOLUMES / CONTRACTS   (the Canon = law)
        ▲                                          │
        │ files findings as ADR/FC                 │ specifies the bar (DoD)
        │                                          ▼
   ARCHITECTURE_AUDIT ◄───── reports conformance ── 00_CANON_INDEX  (the map + status)
        │                                          ▲
        └────── drift found → Work Order ──────────┘  (close the gap; board tracks it)
```

- A **drift** the Audit finds → either a WO (implementation must catch up to Canon) or an
  FC/ADR (Canon was wrong and is amended). Example live: FC-2 (significance formula) →
  "reconcile Vol V Ch.5 to the 9 live dimensions."
- A **decision** ratified in the Decision Log → the affected volume is edited *and*
  `00_CANON_INDEX.md` is updated in the same pass (e.g. ADR-0003 promoting XXIII–XXVII).
- A **promotion** (a volume reaching a new gate) → `00_CANON_INDEX.md` status row updates;
  the Audit begins tracking conformance for the newly-live spec.

No one of the three is authoritative alone: the Canon holds the law, the Index holds the
map, the Audit holds the truth about the gap between them, and the Decision Log is the only
place law changes.

## 1.8 Interaction with other volumes

- **Volume V / CONTRACTS.md** — supplies the two artifacts the DoD checks against (the
  nine-field envelope §2, the universal lifecycle §3). Chapter 2 formalises the wider
  engineering standards; this chapter governs the process by which any of them become law.
- **All 28 volumes** — every volume's `00_Metadata.md` carries the same frontmatter fields
  (`status`, `version`, `audit_status`, `owner`, `architect`, `implementation`). This
  chapter is where that shared shape and its status vocabulary are governed.
- **ADR-0003** placed Volumes XXIII–XXVII (this volume included) into official Canon; this
  chapter is that ADR's constitutional expansion.

## 1.9 Open questions for David

*(Heading amended 2026-08-10 — these are software-canon questions; David is the single gate.
The CA may advise on any of them; none waits on it.)*

1. **DoD ownership of governance volumes.** The Volume V DoD is written for *faculty*
   volumes (it demands faculty contracts, envelopes, lifecycles). Governance volumes
   (XXVII, and arguably XIX/XXVI) have no faculties. Do we (a) adopt a parallel
   "Governance DoD" for these, or (b) treat the faculty-specific DoD lines as N/A with a
   recorded justification? Recommendation: (a) — a short governance-DoD variant.
2. **ADR numbering scheme.** The log currently mixes `ADR-000n`, `ADR-Exec-00n`, and
   letter IDs (`D-A`…`D-M`). All are immutable and that is correct, but should *new* ADRs
   standardise on one prefix going forward? Recommendation: keep existing IDs frozen;
   adopt a single `ADR-YYYY-NNN` form for all new decisions, indexed thematically.
3. **Who owns `ARCHITECTURE_AUDIT.md` writes?** D-LANES says canon changes only by the
   Architect; the Audit is reporting, not canon. Confirm the Architect (or a read-only
   Debug Agent) is the sole Audit writer, so status is never edited to look better than
   reality (Verify-before-claim).
4. **Freeze authority.** Confirm that declaring a *canon-level* freeze (D-FREEZE class) is
   a David-L3 act, and that lifting it requires an explicit David decision, never an
   agent's judgement that "we're probably ready."

*Added 2026-08-10 with the personal-scope amendment:*

5. **Ruling filing (procedural, Architect to action).** The 08-10 rulings need numbering into
   `DECISION_LOG.md` with an index entry, per §1.3. No decision needed from David — flagged so
   it is not lost.
6. 🔴 **FLAGGED FOR DAVID L3 — how much governance does he actually want?** With the CA gate
   retired and one person approving, there is a real question this Architect will not answer
   alone: is the two-gate Change Control flow (approve-to-build **and** approve-completed)
   still worth David's attention on every WO, or should Gate 1 batch/auto-clear for anything
   that is neither RESERVED nor identity-touching? The Architect's recommendation is **keep
   both gates for RESERVED, identity, values, and robot hardware; batch Gate 1 elsewhere** —
   but this is David's time and his call, not an efficiency the Architect may grant itself.
7. **CA's standing role.** Confirmed as advisor/stress-tester for software, and available to
   hold **LG-2 for robot design review** (§1.3.1). Confirm David wants it kept in that second
   role — it is the one place a second reviewer still legally exists.

## 1.10 Canon References

- `docs/architecture/00_CANON_INDEX.md` — master map + Definition of Done.
- `docs/architecture/DECISION_LOG.md` — the ADR ledger (append-only, IDs immutable).
- `docs/architecture/ARCHITECTURE_AUDIT.md` — live conformance status.
- `docs/architecture/ARCHITECTURE_BIBLE.md` — the Bible class (Vols I–III).
- `docs/architecture/ARCHITECTURAL_PRINCIPLES.md` — the constitution + Runtime Invariants.
- `engineering/work_orders/CHANGE_CONTROL.md` — D-M, the change process (the RFC path).
- `engineering/work_orders/README.md` — WO lifecycle + evidence-gates-expansion.
- `FREEZE_V1_LOCK.md` · `VERSIONING.md` (repo root) — freeze + versioning.
- `engineering/Volume_1_Framework/04_freeze_standards.md` — freeze gate + decisions.
- `engineering/standards/documentation.md` — the Append Rule (never rewrite history).

---

```
Chapter 1 — Canon Governance
Status: READY FOR REVIEW  (amended 2026-08-10 — personal-scope re-scope; NOT ratified)
Files: Volume_XXVII/01_Canon_Governance.md
Formalises (does not recreate): 00_CANON_INDEX (DoD + map), DECISION_LOG (ADR ledger),
  ARCHITECTURE_AUDIT (conformance), CHANGE_CONTROL (RFC path), FREEZE standards.
Honours: One Brain → One Identity · Definition of Done bar · Canon vs ADR vs Audit · FREEZE discipline.
Amendment 2026-08-10: §1.0.1 who governance serves · §1.3 CA advises, does not legislate ·
  §1.3.1 NEW — David single L3 + the software/robot LG-2 split (volume previously had ZERO
  occurrences of LG-2) · §1.4.1 CA confers nothing · §1.5 CA first-pass retired as a gate.
Open Questions: 7 (for David) — Q6 🔴 David L3 (how much governance he wants)
```

READY FOR REVIEW
