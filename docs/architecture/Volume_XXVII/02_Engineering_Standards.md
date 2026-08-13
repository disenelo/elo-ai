---
chapter: 2
title: "Engineering Standards — Documentation, Naming, Structure, Coding, Testing"
volume: XXVII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - engineering/standards/documentation.md (documentation standard — AUTHORITATIVE)
  - engineering/standards/coding.md (coding + naming standard — AUTHORITATIVE)
  - engineering/standards/testing.md (testing philosophy — AUTHORITATIVE)
  - engineering/standards/architecture.md (One Brain + component contract standard — AUTHORITATIVE)
  - docs/architecture/Volume_V/CONTRACTS.md (message envelope §2, lifecycle §3, base contract §4)
  - engineering/README.md (engineering programme + lifecycle + architecture constants)
  - docs/architecture/ARCHITECTURAL_PRINCIPLES.md (naming is architecture; One Brain)
---

# Chapter 2: Engineering Standards

## 2.0 Purpose

This chapter is the **single canonical entry point** to eLo OS's engineering standards. It
does not author new rules — the standards already live and are ACTIVE under the Lead
Systems Architect's authority in `engineering/standards/` and `Volume_V/CONTRACTS.md`.
Its job is to consolidate them into one governed reference, state which file is
authoritative for each domain, and bind them to the Runtime Invariants so a standard is
never read in isolation from the philosophy it serves.

The organising principle is from `ARCHITECTURAL_PRINCIPLES.md` and Volume XV: **naming is
architecture** — how a thing is documented, named, and placed is not cosmetic; it is part
of the design and is checked at review.

**Authoritative-source map (read the source; this chapter points):**

| Domain | Authoritative file | Status |
|---|---|---|
| Documentation | `engineering/standards/documentation.md` | ACTIVE |
| Coding + naming + security + git | `engineering/standards/coding.md` | ACTIVE |
| Testing philosophy + hierarchy | `engineering/standards/testing.md` | ACTIVE |
| Architecture / component contract | `engineering/standards/architecture.md` | ACTIVE |
| Runtime contracts (envelope · lifecycle · base contract) | `Volume_V/CONTRACTS.md` | READY FOR REVIEW (ADR-0001/0002 LAW) |
| Programme + engineering lifecycle | `engineering/README.md` | ACTIVE |

Where this chapter and a source ever disagree, **the source wins** and this chapter is the
one corrected (same deference model Volume V/CONTRACTS uses toward `16_runtime_contracts.md`).

## 2.1 Documentation standards

From `engineering/standards/documentation.md` (ACTIVE). The load-bearing rules:

- **Documentation is not optional.** *"A phase without documentation is not frozen — it is
  incomplete."* Every phase produces its required documents before freeze
  (Architecture Review, Implementation Plan, Diagnostics, Regression, Freeze Decision,
  Handover — each has a template in `engineering/templates/`).
- **The Append Rule (governs the whole canon).** *Never delete or rewrite history.* A wrong
  fact is annotated `— superseded YYYY-MM-DD: [new fact]`, not erased. Old docs are marked
  superseded and archived, never deleted. Change logs are append-only, newest at the bottom.
  This is the standard that makes the Decision Log's immutability (Ch.1 §1.3) possible.
- **Two documentation trees, kept separate:**
  - `docs/architecture/NN_name.md` — *what eLo IS* (cognitive structure). Sequential
    numbering, never reused; a superseded doc is marked in its header.
  - `engineering/work_packages/…` and phase playbooks — *how eLo is BUILT* (process).
  - The invariant, stated in `engineering/README.md`: *"`engineering/` defines how eLo
    evolves; `docs/architecture/` defines what eLo is. These are separate and stay separate."*
- **Architecture-doc required sections (9).** Every `docs/architecture/NN_name.md` carries:
  Purpose · Role in the One Brain · Interface · Runtime Flow · Invariants · What This
  Component Does Not Do · Interaction Map · Known Limitations · Freeze Status. (The Volume
  chapters extend this with contract + lifecycle + envelope + acceptance tests per the DoD.)
- **Handover quality bar — RE-SCOPED 2026-08-10.** The bar used to be *"a person who has never
  seen the project… can start implementing within one session."* **That reader does not exist
  and is not coming.** There is no team to onboard and no stranger to satisfy — eLo is David's
  personal companion and the sharing track is PARKED.

  The bar that replaces it is **harder, not softer**, because it describes the failure that
  actually happens here every week:

  > **A handover is complete only when a seat that has just lost its entire context to a
  > compaction — or David returning after two weeks away — can read
  > `engineering/README.md` → the last frozen handover → the board → its `START_HERE`, and
  > resume work in one session without asking David to re-explain anything he has already
  > said.** If any step would force a re-explanation, the handover is incomplete.

  Why this is the right bar: the agents in this project **do not persist.** Compaction is the
  routine amnesia the documentation exists to survive. "Onboard a stranger" was aiming at a
  hypothetical newcomer; "**survive a compaction**" aims at the reader who shows up daily and
  arrives with nothing. Same discipline, real audience.

  Corollary (already law elsewhere, restated here because it is the same rule): **durable facts
  get written down, not remembered**, and **David's own words are stored verbatim in
  `docs/architecture/_intake/`, never summarised** — a compressed source fails this bar even
  when it reads well.

## 2.2 Naming conventions

From `engineering/standards/coding.md` §Naming Conventions (ACTIVE). These are canon; new
code conforms:

| Item | Convention | Example |
|---|---|---|
| Module-level constants | `_UPPER_SNAKE` | `_FAREWELL_POOL` |
| Public functions | `snake_case` | `shadow_context()` |
| Private functions | `_snake_case` | `_detect_intent()` |
| Classes | `PascalCase` | `CognitivePlan` |
| Config keys | `snake_case` | `"refresh_interval_seconds"` |
| Response pools | `_NAME_POOL` | `_ANIM_REPLIES` |
| Regex patterns | `_NAME_RE` | `_INVADE_RE` |

Beyond code identifiers, two canon-level naming rules apply:

- **Faculty names** are `PascalCase`, unique in the registry (`Volume_V/CONTRACTS.md` §4,
  Ch.1 registry). A faculty is a versioned unit (semver on the faculty).
- **Naming is architecture (do not overload names).** The Vol XV precedent is binding:
  `world_state.py` (spatial graph) and `live_world_state.py` (cognitive world) must not
  share the name "World State" across two different objects. When two things differ in
  consumer or meaning, they get different names.
- **Work Order files:** `WO-NNN_Short_Name.md` from `_TEMPLATE.md`; work-package files
  `WP_[A-Z]_[NAME].md` (then `WP_A2_…` when the alphabet is exhausted).

## 2.3 Folder structure

Canonical layout from `engineering/standards/coding.md` §File Organisation (runtime) and
`engineering/README.md` §Directory Structure (programme). Summary:

```
~/elo-ai/                        — all eLo OS runtime code (Builder write-scope, D-I)
  runtime/        — cognitive spine, faculties, router
  tools/          — data agents (weather, vision, news…)
  ambient/        — background presence engine
  presence/       — presence scheduler
  desktop/        — desktop shadow (window state, app context)
  blender_bridge/ — state writer to blender_state.json
  memory/         — memory files (JSON)
  config/         — runtime configuration
  tests/          — unit and integration tests
  prompts/        — FREEZE_V1_LOCK (scoped unlock only, D-K)
  runtime/executive.py — FREEZE_V1_LOCK

docs/architecture/  — WHAT eLo is (canon: Volumes + ADRs + CONTRACTS)
engineering/        — HOW eLo evolves (standards, phases, freezes)
  standards/  templates/  playbooks/  proofs/  Volume_1_Framework/  work_packages/  work_orders/
```

**Write-scope law (D-I):** the Builder may create/edit files only under `~/elo-ai/`. The
DISENELO apps in `~/Desktop/Output/` (Unity DesktopBuddy, EloRetargeter, etc.) are a
separate setup, off-limits to the Builder; changes there are filed to the Architect. Unity
C# lives in the DISENELO Presence repo and is handled by the Unity Agent only — never
edited directly in Claude Code (`coding.md` §Language and Environment). This is the
folder-structure expression of D-LANES.

## 2.4 Coding standards

From `engineering/standards/coding.md` (ACTIVE). The hard rules, each tied to a principle:

- **No silent scope creep.** Build exactly what the implementation plan / WO says; a noticed
  improvement is *documented*, not fixed alongside. (Mirrors Change Control §3.1 "one change
  at a time" and the DoD "no inventing.")
- **No fallback unless specified.** Empty input → empty output. A component never invents a
  default or fires a pool response unless the spec explicitly requires it. This is the
  code-level face of the runtime invariant *"Silence is valid output"* and of
  Truth-before-fluency (`ARCHITECTURAL_PRINCIPLES.md`).
- **Never raise to the user.** Every component catches its own exceptions, logs, and returns
  the interface's empty shape. No Python traceback ever reaches the person. (Graceful
  degradation — the same contract law as `Volume_V/CONTRACTS.md` §4.)
- **FREEZE_V1_LOCK.** `runtime/executive.py` and `prompts/` are never modified; *"if a
  change to these files seems necessary, that is a signal the design is wrong. Revise the
  design."* (Ch.1 §1.6; scoped unlock only, D-K.)
- **No hard-coded user-facing strings.** Response pools live named in `server.py`; no
  user-facing string is buried in logic.
- **State writes are atomic.** All writes to `blender/blender_state.json` use
  read-merge-write-atomic (`state_writer.patch`); never raw-write, never truncate-and-rewrite.
  (Also enforced as a WO rule in `work_orders/README.md`.)
- **Threading.** Background loops (vision, ambient, presence) are daemon threads with a clean
  `threading.Event` shutdown; they never block the main request thread.
- **No new dependencies without review** — constrained by miniconda, Raspberry-Pi-5 robot
  deployment, and offline mode.
- **Comments** — only where the *why* is non-obvious; names carry the *what*; one line max.

### 2.4.1 Security (coding.md §Security — ACTIVE)

- `.env` is GITIGNORED — never read in tests, never printed, never committed. Keys
  (ElevenLabs, Cerebras, AccuWeather, OpenAI, Gemini, Groq) live in `.env` only, read at
  runtime via `os.environ.get()`, never hard-coded.
- **David's** birth data is never stored in memory files. *(Amended 2026-08-10: read "user" as
  "David" throughout this volume — there is exactly one person, and the abstraction was hiding
  whose data was being protected. Volume XXIV §1.3.5–§1.3.7 now also governs durable facts about
  the **other** people in David's life, with two questions flagged for David's L3.)*
- Git: the system never auto-commits (`logs/pending_commits.jsonl`); commit messages
  describe *why*, not *what*; no force-push to main without authorisation; no amending
  published commits.

> These are the *coding-level* security rules. The full identity/auth/secret/threat-model
> canon is **Volume XXIII (Security & Trust)** — this chapter defers to it for anything
> beyond the shop-floor coding rules above.

## 2.5 Architecture / component-contract standards

From `engineering/standards/architecture.md` (ACTIVE) — the runtime-shape rules that every
new component obeys, all expressions of the One Brain invariant:

- **The One Brain Principle.** *The Executive Faculty is the sole decision-maker. Every
  other component observes, computes, or contributes information. Nothing else decides.* The
  only permitted exceptions are explicitly-documented pre-spine interceptors (farewell/anim/
  scale pools) that bypass the LLM for speed and draw from a fixed pool — never decide on
  internal state.
- **Faculty roles table** — Language/Memory/Attention/Relationship/Capability/Connection
  observe; **only the Executive decides**; the Spine assembles; Embodiment executes.
- **Interface contracts** — every new component documents exact input schema, output schema,
  and its invariants: never decides · empty→empty · never raises · never writes to the user
  directly. (This is the same shape as `Volume_V/CONTRACTS.md` §4 base contract.)
- **Routing exists to understand, not to restrict** — a routing failure degrades gracefully;
  the Executive still decides with less context.
- **Embodiment follows cognition** — Desktop/Unity/Robot are output surfaces for one brain;
  a new surface *reads state*, it does not add a cognitive layer.
- **Extension over creation** — prefer adding a signal to an existing faculty over minting a
  new faculty (new faculties add coordination complexity; new signals add data only). This
  is CHECK-BEFORE-BUILD at the runtime level.

### 2.5.1 The runtime contract standard (Volume V / CONTRACTS)

The three cross-cutting contracts every faculty binds to (LAW; do not restate per chapter):

- **§2 Message envelope** — the canonical nine-field wire format `{id, sender, receiver,
  priority, context, payload, confidence, expires, trace}` (ADR-0001 / D-A). `confidence`
  may only be *lowered* downstream; `trace` is append-only; malformed envelopes are rejected
  at the bus boundary.
- **§3 Universal lifecycle** — `BOOT → REGISTER → INITIALISE → READY → ACTIVE → WAITING →
  SLEEPING → ACTIVE`; exception `ACTIVE → ERROR → RECOVERY → READY`; `READY → SHUTDOWN`
  (ADR-0002 / D-B). Recovery MUST pass through READY; faculties never terminate unexpectedly;
  learning/updating never runs in the response path.
- **§4 Base faculty contract** — name/version/purpose/contributes_to/runs_in + typed
  Inputs/Outputs/Dependencies/Failure-Modes, with the contract law: *every faculty degrades
  gracefully* (a missing dependency yields a lower-confidence but valid contribution, never a
  stalled turn).

## 2.6 Testing philosophy

From `engineering/standards/testing.md` (ACTIVE):

- **Test behaviour, not implementation.** *"A passing test on broken behaviour is worse than
  no test."* Tests must pass before freeze.
- **The test hierarchy:** Unit → Conversation → Desktop/Embodiment → Unity → Robot →
  Regression → Stress. Each layer has an owner and a protocol in the source file.
- **Unit-test coverage floor** — every new component covers: happy path · empty input
  (`None`/`""`/`{}` → empty, no raise) · malformed input · long input · component isolation
  (Executive mocked). Unit tests never assert LLM content, never call real external APIs,
  never depend on `blender_state.json` or `.env`.
- **Conversation-test acceptance criteria** encode the behaviour invariants: conversational
  length, project-anchor only when relevant, never self-refer as "the system", never echo
  raw context/headlines/data, **anti-fabrication (never invents errors, events, or details)**
  — the testing-level enforcement of Verified Speech (ADR-Exec-001).
- **Regression is zero-tolerance.** Every prior frozen-phase baseline must pass; if it does
  not, *the implementation is rolled back, not the baseline* (`testing.md`;
  `Volume_1_Framework/04_freeze_standards.md`).
- **The Presence Test (Phase 2.5+).** Any phase touching presence/avatar/embodiment also
  asks the non-technical question *"Does this feel like someone sharing the space?"*
  Anything below "kind of, sometimes" is a finding to address before freeze
  (`Volume_1_Framework/03_review_standards.md`). This is the testing-level guardian of
  *"eLo does not exist to answer prompts. He exists to share space."*

**Evidence discipline (Honesty Markers, `03_review_standards.md`):** `✅` means *I ran it and
saw the output* — *"if you didn't run it, it's ⚠️ at best."* This is the review-level form of
the Verify-before-claim rule.

## 2.7 Interaction with other volumes

- **Volume XXVII Ch.1** governs *how* these standards become/stay law; this chapter is the
  standards themselves.
- **Volume XXVII Ch.3** governs the review gates and freeze that *enforce* these standards on
  the way to release.
- **Volume V / CONTRACTS.md** owns the runtime-contract standards (§2.5.1); this chapter
  defers to it and to `16_runtime_contracts.md`.
- **Volume XXIII (Security & Trust)** owns the full security architecture; §2.4.1 here is only
  the coding-floor subset.
- **Every faculty volume** inherits §2.1 (doc sections), §2.2 (naming), §2.5.1 (contracts),
  §2.6 (acceptance tests) via the Definition of Done.

## 2.8 Open questions for David

*(Heading amended 2026-08-10 — software canon, David's single gate; CA advises, does not gate.)*

1. **Standards home — one copy or two?** The standards live in `engineering/standards/*`
   (ACTIVE, Lead Systems Architect authority). This chapter deliberately *points* rather than
   copies, to avoid the drift the Append Rule warns against. Confirm the standards stay
   canonical in `engineering/standards/` with XXVII as the governed index — not duplicated
   into the volume (recommended).
2. **Python version drift.** `coding.md` says Python 3.11+ (miniconda). Confirm this still
   holds for the current build and the Raspberry-Pi-5 robot target, or file the update.
3. **Naming-scheme scope.** Should the naming table (§2.2) be promoted to bind non-runtime
   code too (e.g. Unity C# handled by the Unity Agent), or does the Unity lane keep its own
   naming standard? Recommendation: Unity lane documents its own, cross-referenced here.
4. **Testing owners as roles vs agents — NARROWED 2026-08-10.** `testing.md` names human-style
   roles ("Conversation Reviewer", "Regression Engineer") that describe a staffed QA function
   which does not exist. Map them onto the seats that *do* exist — **Builder (eLo OS Python) ·
   Designer (Unity) · Game** — with the Lead Architect verifying against acceptance tests and
   **David as the only Conversation Reviewer** (he is the one the conversation is with; the
   Presence Test in §2.6 is literally his judgement). There is no "Debug" seat; read the
   Debug-Agent role as a mode the Lead Architect runs read-only. Recommendation: rewrite the
   role names in `testing.md` to the live seats so no test layer has a fictional owner.

## 2.9 Canon References

- `engineering/standards/documentation.md` · `coding.md` · `testing.md` · `architecture.md`.
- `docs/architecture/Volume_V/CONTRACTS.md` — envelope §2, lifecycle §3, base contract §4.
- `engineering/README.md` — programme, engineering lifecycle, six architecture constants.
- `engineering/Volume_1_Framework/03_review_standards.md` — honesty markers, presence test.
- `docs/architecture/ARCHITECTURAL_PRINCIPLES.md` — One Brain, naming-is-architecture,
  Truth-before-fluency, silence-is-valid.
- `docs/architecture/DECISION_LOG.md` — D-A/D-B (contracts LAW), D-I (write-scope),
  D-LANES, ADR-Exec-001 (anti-fabrication).

---

```
Chapter 2 — Engineering Standards
Status: READY FOR REVIEW  (amended 2026-08-10 — personal-scope re-scope; NOT ratified)
Files: Volume_XXVII/02_Engineering_Standards.md
Amendment 2026-08-10: §2.1 stranger-onboarding bar RETIRED → "survive a compaction" bar ·
  §2.4.1 "user" birth data named as David's · §2.8 Q4 mapped to the seats that exist.
Consolidates (points to, does not recreate): engineering/standards/{documentation,coding,testing,architecture}.md
  + Volume_V/CONTRACTS.md + engineering/README.md.
Honours: One Brain · naming-is-architecture · Silence-is-valid · anti-fabrication · Definition of Done.
Open Questions: 4 (for CA / David)
```

READY FOR REVIEW
