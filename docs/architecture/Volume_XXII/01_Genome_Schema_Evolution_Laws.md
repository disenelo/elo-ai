---
chapter: 1
title: "Genome Schema, Evolution & Laws"
volume: XXII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "David Charles Bible content 2026-07-27"
dependencies: [Volume V/CONTRACTS.md, Volume XVI]
---

# Chapter 1: Genome Schema, Evolution & Laws

## 1.0 Philosophy
Every faculty is a **living architectural component** with identity, capabilities,
dependencies, and an evolutionary history. The Genome defines *what a faculty is*,
independent of implementation language. It is the DNA that keeps expansion coherent with
the One Brain Principle.

## 1.1 Genome Schema (every faculty declares)
```
FacultyGenome:
  Identity          # unique name
  Purpose           # one primary responsibility
  Responsibilities
  Inputs · Outputs
  Dependencies
  Contracts         # the approved contracts it speaks (CONTRACTS.md)
  Lifecycle         # ratified lifecycle (CONTRACTS.md §3, D-B)
  Capabilities      # advertised: capability/confidence/latency/cost/health/version (Vol XVI)
  Constraints
  Version           # semver
  Lineage · Successor · Deprecation Status
```
This is the Faculty Contract of `CONTRACTS.md §4` extended with lineage/versioning — a
genome is a versioned, registry-tracked contract.

## 1.2 Evolution
- Faculties evolve through **semantic versioning**.
- **Breaking changes** require a migration path + an ADR (`DECISION_LOG.md`).
- **Experimental** faculties may coexist with stable versions but cannot replace them
  until accepted into the Canon.

## 1.3 Composition
New faculties are **assembled from existing contracts**, never by duplicating behaviour —
preserving One Brain while allowing growth.

## 1.4 Genome Laws (MUST)
1. A faculty has **one** primary responsibility.
2. A faculty communicates **only through approved contracts** (the bus/envelope).
3. A faculty **cannot own** another faculty.
4. Every faculty **declares its dependencies**.
5. Every faculty is **independently testable**.
6. Every faculty **preserves backward compatibility or provides a documented migration path**.

## 1.5 Genome Registry
A registry tracks every faculty's genome (identity, version, lineage, deprecation). The
live `runtime/capabilities/registry.py` (tools today) is the closest existing structure;
this volume extends the concept to *cognitive faculties*.

## 1.6 Acceptance Tests
```
FT-1  Full genome declared    Given a faculty, Then all schema fields are present (incl. version + lineage).
FT-2  Composition over dup      Given a new faculty need, Then it composes existing contracts rather than duplicating.
ST-1  One responsibility        Given a faculty with two primary responsibilities, Then it fails review (Law 1).
ST-2  Contract-only comms       Given a faculty makes a direct call, Then it violates Law 2 and is rejected.
ST-3  Backward compat           Given a breaking change without a migration path/ADR, Then it is blocked (Law 6).
IT-1  Registry + bus            A faculty registers its genome, advertises capabilities (Vol XVI), and the Executive selects it.
```

## 1.7 References
`ARCHITECTURE_BIBLE.md` (Vol XXII), `CONTRACTS.md` (§3 lifecycle, §4 base contract), Vol XVI (capability advertisement), `runtime/capabilities/registry.py`, `DECISION_LOG.md`.

---
**Status: READY FOR REVIEW** — genome schema, evolution, composition, six laws + tests. Canonicalised from David's Bible content.