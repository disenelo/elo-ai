---
chapter: 3
title: "Faculty Evolution & the Six Laws — How a Faculty Is Allowed to Change"
volume: XXII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXII/01_Genome_Schema_Evolution_Laws.md (§1.2 evolution, §1.3 composition, §1.4 six laws — source)
  - Volume_XXII/02_The_Genome_Schema.md (the descriptor that versions)
  - Volume_V/CONTRACTS.md (§3 lifecycle; §4 base contract; graceful degradation law)
  - Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md (ADR-Exec-005 — the boundary evolution obeys)
  - DECISION_LOG.md (ADR home for breaking changes)
---

# Chapter 3: Faculty Evolution & the Six Laws

## 3.0 Purpose

A companion that ships once and never grows is dead. A companion that rewrites itself freely is
unstable — and, worse, could drift its identity, its truth, or its Executive. This chapter defines
the **narrow, safe channel** through which a faculty is allowed to change: semantic versioning,
lineage, composition, deprecation and succession — governed by the **six Genome Laws** that every
faculty and every version event must satisfy.

The distinction this whole volume protects: **the genome evolves; the being does not fragment.**
Faculties gain versions, split, merge, and retire — but One Brain → One Identity holds, and
identity/values/truth/Constitution/Executive are never what evolves (ADR-Exec-005). Chapter 1 §1.2
states this in one line; this chapter is its full mechanism.

## 3.1 The unit of evolution is a version, not a mutation

**3.1.1 Every change is a version event.** A faculty never mutates in place. Any change to what its
genome declares (§2.2) is published as a new semantic version, recorded in `lineage`, and (for
breaking changes) backed by an ADR in `DECISION_LOG.md`. The prior version's genome is immutable
and remains readable — this is what makes lineage trustworthy and rollback possible.

**3.1.2 Semantic versioning, with faculty-specific meaning:**

```
MAJOR  — a BREAKING change: an input/output contract changes, a capability is removed,
         contributes_to changes, or behaviour changes such that existing callers break.
         REQUIRES: a migration path + an ADR (Law 6). MAY require RESERVED gate if reserved:true.
MINOR  — an ADDITIVE change: a new capability, a new optional input, a widened output —
         backward compatible. Old callers keep working unchanged.
PATCH  — a fix or tuning that changes NO contract and NO advertised capability
         (e.g. lower latency, a bug fix, a confidence recalibration downward).
```

**3.1.3 Experimental coexists; it never silently replaces stable.** A faculty may publish a
`status: experimental` version that runs alongside the `stable` one (e.g. behind a flag, or for a
subset of turns) — but it **cannot become the version the Executive selects by default** until it
is accepted into the Canon (review + audit, `ARCHITECTURAL_PRINCIPLES.md` "Canon before
implementation"). This is how eLo tries a better faculty without betting identity on it.

## 3.2 Composition over duplication (Ch.1 §1.3, expanded)

New capability is **assembled from existing contracts**, never by cloning behaviour into a second
faculty. Two faculties that both, say, score significance are a fracture of One Brain — two places
that can disagree about the same truth.

**Composition rules (MUST):**

- A new faculty need is first met by **composing existing faculties' contracts** (routing their
  outputs), not by re-implementing their behaviour. (Directly parallels the live registry note —
  "the router queries this; it never imports agents directly" — applied to cognition.)
- If genuinely new behaviour is required, the new faculty declares a **single new responsibility**
  (Law 1) and depends on the others by contract (`dependencies`, `kind: hard|soft`).
- A capability that already exists is **referenced, never duplicated**. Duplicate capability across
  two genomes fails review.

## 3.3 Deprecation & succession — how a faculty retires without a gap

A faculty is retired only through a declared succession, so no capability silently vanishes:

```
status flow:   experimental ─► stable ─► deprecated ─► retired
```

**Succession rules (MUST):**

- `deprecated` faculties keep running and keep serving callers until their `removal_target`
  version. `deprecation.migration_ref` MUST name where callers move (usually the `successor`).
- A `successor` MUST cover every capability the deprecated faculty advertised (no capability is
  lost across the handover — verified against the two genomes' `capabilities[]`).
- `retired` is only reachable after the migration window; retiring a faculty with live hard
  dependents is blocked.
- Retiring or replacing a `reserved: true` faculty is a RESERVED decision (David L3 + LG-2).

This is the faculty-level expression of "no false capability": the system never advertises a gap
as filled, and never drops a capability without a named replacement.

## 3.4 The Six Genome Laws (formal)

Chapter 1 §1.4 lists six laws, canonicalised from David's Bible content. Restated here as
**normative MUSTs with their rationale and test coverage** — nothing added to the *set*; the laws
are David's, this chapter formalises them and flags where interpretation was needed.

```
LAW 1 — ONE PRIMARY RESPONSIBILITY.
  A faculty has exactly one purpose (one sentence, one contributes_to). A faculty that would
  need two purposes is two faculties.  Rationale: One Brain is many SPECIALISTS; a faculty that
  does two things is where cognition starts to blur.  Test: FT-3 (Ch.2), ST-1.

LAW 2 — CONTRACT-ONLY COMMUNICATION.
  A faculty communicates ONLY through approved contracts on the Faculty Bus (CONTRACTS.md §2).
  No direct calls, no reaching into another faculty's internals.  Rationale: ADR-0001 Faculty Bus;
  the only channel that gives the Audit observability.  Test: ST-2.

LAW 3 — NO FACULTY OWNS ANOTHER.
  A faculty cannot own, contain, or control another faculty. It may DEPEND on one by contract, but
  the Executive alone allocates and orchestrates (Vol XVI §1.1).  Rationale: ownership = a second
  decider; there is only one Executive.  Test: ST-3.

LAW 4 — DECLARE EVERY DEPENDENCY.
  Every faculty declares its dependencies (hard|soft) in its genome. Hidden dependencies are
  forbidden.  Rationale: undeclared coupling is exactly the drift a genome exists to prevent; the
  Executive must know the graph to route and degrade.  Test: ST-4.

LAW 5 — INDEPENDENTLY TESTABLE.
  Every faculty is testable in isolation, with its dependencies mocked/stubbed. A faculty that
  cannot be tested alone is too coupled (violates Law 3/4).  Rationale: verification is per-faculty
  (D-LANES: each seat owns its faculty's tests).  Test: ST-5.

LAW 6 — BACKWARD COMPATIBILITY OR A DOCUMENTED MIGRATION PATH.
  A breaking (MAJOR) change ships ONLY with a migration path + an ADR (DECISION_LOG.md). No silent
  break.  Rationale: continuity — callers (and the being's felt continuity) never shatter under a
  version bump.  Test: ST-6.
```

**Derivation flag (honesty, per Rule #2):** the six laws are **grounded** — they are stated
verbatim-in-substance in the existing Ch.1 §1.4 (David's Bible content). This chapter's *additions*
that go beyond the bare list — the semantic-versioning meaning table (§3.1.2), the
experimental→stable→deprecated→retired flow (§3.3), and the "successor must cover every
capability" rule — are **derived by the Architect** to make the laws enforceable. They are
consistent with the laws and with ADR-Exec-005, but they are engineering interpretation, not
David's verbatim source, and are flagged here for CA/David review. Nothing was added to the *set of
six laws themselves.*

## 3.5 The constitutional ceiling on evolution (binds Vol XXVIII)

Evolution has a hard ceiling that no version event, no composition, and no learned policy may
cross. This is **ADR-Exec-005**, stated here in genome terms so the boundary is unmissable:

> A faculty may evolve its **skills, policies, preferences, confidence, latency, heuristics, and
> exploration weighting**. A faculty may **NEVER** evolve — and no genome version event may alter —
> **identity, values, ethics, memory truth, verified observations, Executive Authority, speech
> verification, the Constitution, or the architectural principles.**

**Ceiling rules (MUST):**

- A version event that would change identity/values/truth/Constitution/Executive is **not a
  version event — it is a violation.** It is rejected regardless of ADR, because those are
  invariants, not versioned components. (An ADR can change an *ADR*; it cannot demote an
  invariant — `ARCHITECTURAL_PRINCIPLES.md` "the principle wins.")
- Adaptive Learning (Vol XXVIII) is itself a **faculty with a genome** (`ReinforcementAndAdaptation`
  faculty; sits AFTER Verify in the loop). Its genome's `constraints` MUST encode the ADR-Exec-005
  boundary, and it evolves `capabilities`/policies only — never identity contracts.
- Personality evolution (Vol V Ch.7) is the **only** path allowed to touch personality-adjacent
  state, and only through its validated `VALIDATION_REQUIRED` gate (`CONTRACTS.md §3`). No other
  faculty's version event may.

This is why the Genome and Adaptive Learning are one continuous story: the genome defines *what can
change and how it is recorded*; ADR-Exec-005 defines *what can never change*; and the six laws keep
every change coherent with One Brain.

## 3.6 Acceptance Tests

### Functional
```
FT-1  Version event, not mutation
  Given a faculty changes an advertised capability
  Then a new semver is published, lineage appended, prior genome left immutable.

FT-2  Breaking change gated
  Given a MAJOR (contract-breaking) change with no migration path/ADR
  Then it is blocked (Law 6).

FT-3  Experimental never auto-promotes
  Given an experimental version and a stable version coexisting
  Then the Executive still selects stable by default until Canon acceptance (§3.1.3).

FT-4  Succession loses no capability
  Given faculty A (deprecated) → successor B
  Then B's capabilities[] cover all of A's, else retirement is blocked (§3.3).
```

### Stability
```
ST-1  One responsibility        A faculty declaring two purposes fails review (Law 1).
ST-2  Contract-only             A direct inter-faculty call is rejected at the bus (Law 2).
ST-3  No ownership              A faculty attempting to control another is rejected (Law 3).
ST-4  Dependencies declared     A faculty with an undeclared dependency fails review (Law 4).
ST-5  Independently testable    A faculty that cannot be tested with deps mocked fails review (Law 5).
ST-6  Backward compat           A silent breaking change is blocked (Law 6).
ST-7  Constitutional ceiling    A version event altering identity/truth/Executive is rejected as a
                                violation, not accepted as a version (§3.5 / ADR-Exec-005).
```

### Integration
```
IT-1  Evolve without fragmenting
  A faculty publishes MINOR (new capability) → registers → Executive selects it → One Brain intact,
  no other faculty changed, no identity/truth touched. Assert continuity across the version bump.

IT-2  Learning obeys the ceiling
  The Adaptive-Learning faculty (Vol XXVIII) improves a movement policy (skill) via verified
  outcomes → its genome capabilities update; identity/truth/Executive contracts unchanged.
```

## 3.7 References

- `Volume_XXII/01_Genome_Schema_Evolution_Laws.md` — §1.2/§1.3/§1.4 source (the six laws' origin).
- `Volume_XXII/02_The_Genome_Schema.md` — the descriptor that versions.
- `Volume_V/CONTRACTS.md` — §3 lifecycle (VALIDATION_REQUIRED gate), §4 contract, degradation law.
- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — ADR-Exec-005 constitutional boundary.
- `ARCHITECTURAL_PRINCIPLES.md` — Canon before implementation; "the principle wins."
- `DECISION_LOG.md` — ADR home for breaking changes (Law 6) and ADR-Exec-005.

---
```
Chapter 3 — Faculty Evolution & the Six Laws
Status: READY FOR REVIEW
Files: Volume_XXII/03_Faculty_Evolution_and_the_Six_Laws.md
Evolution: semver meaning, composition, deprecation/succession
Six Laws: formalised (grounded in Ch.1 §1.4); derivations beyond the bare list FLAGGED (§3.4)
Constitutional ceiling: ADR-Exec-005 stated in genome terms (§3.5)
Acceptance Tests: FT ×4, ST ×7, IT ×2
```

READY FOR REVIEW
