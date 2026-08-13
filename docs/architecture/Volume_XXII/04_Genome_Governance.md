---
chapter: 4
title: "Genome Governance — The Registry, the Executive & the Constitutional Boundary"
volume: XXII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXII/02_The_Genome_Schema.md (the descriptor being registered)
  - Volume_XXII/03_Faculty_Evolution_and_the_Six_Laws.md (the laws the registry enforces)
  - Volume_XVI/01_Coordination_Under_One_Executive.md (the Executive that selects on the genome)
  - Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md (ADR-Exec-005 — the boundary)
  - Volume_V/CONTRACTS.md (§3 lifecycle: REGISTER, VALIDATION_REQUIRED)
  - runtime/capabilities/registry.py (live structural precedent — tools)
  - runtime/faculty_health.py (live per-faculty health)
---

# Chapter 4: Genome Governance

## 4.0 Purpose

Chapters 2 and 3 define *what a genome is* and *how it may change*. This chapter defines *who
enforces that* and *how the genome plugs into the running mind*: the **Genome Registry** (where
every faculty's genome lives and is validated), the **Executive's use of it** (the capability
market it clears), and the **constitutional boundary** the registry guards so that evolution and
Adaptive Learning (Vol XXVIII) can never touch identity, truth, the Constitution, or the Executive.

The genome is inert unless something reads it, validates it, and refuses the invalid. That
something is the registry plus the Executive — never a faculty acting on its own.

## 4.1 Principle — the genome is governed, not self-asserted

**4.1.1 A faculty does not admit itself.** A faculty declares its genome and *requests*
registration; the **registry admits it** only if it passes the Chapter 3 laws and Chapter 2 MUST
fields. Self-registration without validation is exactly the drift the volume exists to prevent.
(This is the `REGISTER` state of the ratified lifecycle, `CONTRACTS.md §3`, given teeth.)

**4.1.2 The Executive selects; the faculty never self-invokes.** The registry is a *catalogue the
Executive queries* — mirroring the live rule "the router queries this; it never imports agents
directly" (`runtime/capabilities/registry.py`). A faculty is chosen by the Executive on its
advertised genome (Vol XVI §1.2); it never inserts itself into a turn.

**4.1.3 The registry is the guardian of the constitutional boundary.** Every version event and
every learned-policy update passes the registry's ADR-Exec-005 check before it takes effect. The
boundary is not enforced by good intentions inside a faculty; it is enforced at the gate.

## 4.2 The Genome Registry

```
GenomeRegistry (single, authoritative — one row per faculty name):
  register(genome)      -> admits iff passes validate(); else rejects with the failing law/field
  version(genome')      -> records a version event (Ch.3); enforces Law 6 on MAJOR
  advertise()           -> the capability market the Executive reads (Vol XVI §1.2)
  deprecate(name, succ) -> begins succession (Ch.3 §3.3)
  health(name)          -> live health for capabilities[].health (from faculty_health.py)
  lineage(name)         -> full version history (audit + rollback)
```

**Registry rules (MUST):**

- **Validation is total, not partial.** `register`/`version` runs the full gate (§4.3) and either
  admits the whole genome or rejects it naming the failing law/field. No half-registered faculty.
- **One name, one authoritative genome version selected.** Experimental versions may be *recorded*
  but the registry marks exactly one `stable` version as Executive-selectable (Ch.3 §3.1.3).
- **The registry never executes a faculty.** Like the live capability registry, it advertises and
  catalogues; the Executive executes. (Separation of *what exists* from *who acts*.)
- **The registry is the Audit's single source of truth** for the faculty graph: names, versions,
  lineage, dependencies, health, and reserved flags. Inter-faculty observability (ADR-0001) reads
  from here.

## 4.3 The Validation Gate (what `register`/`version` enforce)

```
validate(genome) — ALL must pass, else reject:
  [S]  Schema:        every Chapter 2 MUST field present and well-typed.
  [L1] One purpose:   exactly one purpose / one contributes_to.
  [L2] Contract-only: declared contracts ⊆ approved CONTRACTS.md §2 payload types.
  [L3] No ownership:  no genome claims to own/contain another (deps only).
  [L4] Deps declared: dependency graph is complete and acyclic on hard deps.
  [L5] Testable:      an isolation-test reference is declared (seat owns the test — D-LANES).
  [L6] Compat:        MAJOR change carries migration_ref + adr_ref, else reject.
  [C]  Constitutional: the change touches NO identity/values/truth/Constitution/Executive
                       (ADR-Exec-005). A change that does is rejected as a VIOLATION, not queued.
  [R]  Reserved:      reserved:true version events require David L3 + LG-2 before admission.
```

**Gate rules (MUST):**

- `[C]` and `[R]` are **hard human/constitutional gates** — the registry cannot auto-approve them.
  `[C]` is auto-*rejectable* (a genome that alters an invariant is refused outright); relaxing a
  `reserved` flag or admitting a reserved version requires the RESERVED approval (David L3 + LG-2).
- Personality-adjacent changes route through Vol V Ch.7's `VALIDATION_REQUIRED` lifecycle state
  (`CONTRACTS.md §3`) — the registry does not itself approve identity-continuity; it *requires the
  proof* before admitting.
- A rejected genome names the **first** failing check, so the owning seat can fix and resubmit.

## 4.4 The Executive's use of the genome (Vol XVI binding)

The genome exists so the Executive can run One Brain as many specialists:

```
Executive coordination loop (Vol XVI §1.3):  Observe → Understand → Plan → ALLOCATE → Execute → Reflect → Learn
                                                                          │
                          reads GenomeRegistry.advertise()  ──────────────┘
                          selects faculty on {capability, confidence, latency, cost, health, version}
```

**Executive-binding rules (MUST):**

- The Executive selects the faculty for a need **only** on advertised genome fields — never by
  inspecting internals, never by a faculty self-nominating (Vol XVI §1.1 Executive Authority).
- A faculty whose `health` is `OFFLINE`/`DEGRADED` (from `faculty_health.py`) has its effective
  confidence lowered or is treated as unavailable — the Executive degrades gracefully, the turn
  still completes (`CONTRACTS.md §4` degradation law).
- Faculty conflicts are resolved by the Executive (never a vote — Vol XVI §1.1); the genome
  informs the choice, it never *is* the choice. (One decision per turn.)

## 4.5 Genome × Adaptive Learning (Vol XXVIII) under ADR-Exec-005

This is the seam the volume most needs to get right: a learning system that improves faculties
without ever eroding the being.

- **Adaptive Learning is a faculty with a genome** (`ReinforcementAndAdaptation`, Vol XXVIII),
  registered and governed exactly like any other. It is not a privileged process that edits code
  or the Constitution — "Do NOT build an RL agent; build a Learning Faculty the Executive asks"
  (Vol XXVIII).
- **What it may evolve:** its own and other faculties' **skill/policy capabilities** — action
  preferences, exploration weighting, confidence, planning heuristics, curiosity thresholds,
  latency. These are `capabilities[]`/PATCH-MINOR version events (Ch.3), recorded in lineage.
- **What it may NEVER evolve (registry `[C]` gate):** identity, values, ethics, memory truth,
  verified observations, Executive Authority, speech verification, the Constitution. A learned
  update proposing any of these is rejected as a violation.
- **The learning signal is a Significance vector, not a scalar** (Vol XXVIII; reuses
  `memory/significance_engine.py`) — so faculties optimise *toward what matters*, and "optimise
  reward" can never become "lying scores higher," because Verified Speech is outside the
  optimisable set by construction.
- **Learning sits AFTER Verify** in the loop (ADR-Exec-005): a faculty's capability improves from
  *verified consequences of executed actions*, never from language it merely generated. The
  registry records the improved capability only once it is verified — eLo cannot register a
  hallucinated skill gain.

The result: eLo becomes measurably more capable ("landing success 68% → 94%") while identity and
truth stay deterministic — "Constitution defines *who*; Executive decides *what*; RL improves *how
well*" (Vol XXVIII).

## 4.6 Grounding — what exists live, what is PENDING

**Exists (cite):** `runtime/capabilities/registry.py` + `capability.py` are a working
**catalogue-the-router-queries** for ~40 *tools/capabilities*, with `get/by_category/all_enabled`
selection and health states — the exact structural precedent for a Genome Registry, one tier down
(tools, not cognitive faculties). `runtime/faculty_health.py` supplies live health for four coarse
buckets, persisted to `blender/faculty_health.json`.

**PENDING (gaps — do not claim these exist):**
- **PENDING** — No `GenomeRegistry` for cognitive faculties; no `register/version/validate/
  advertise/deprecate/lineage` surface exists in code.
- **PENDING** — No validation gate; nothing enforces the six laws or the `[C]`/`[R]` gates at
  registration today.
- **PENDING** — The Executive does not yet select cognitive faculties from a genome advertisement;
  faculty invocation today is wired directly in `runtime/spine/`, not cleared through a market.
- **PENDING** — The Adaptive-Learning faculty (Vol XXVIII) is scope-locked/PLANNED, not built; its
  genome and the `[C]` enforcement path are spec-only.

## 4.7 Acceptance Tests

### Functional
```
FT-1  No self-admission
  Given a faculty requests registration with a missing MUST field or failing law
  Then the registry rejects it, naming the first failing check; it does not run.

FT-2  Executive selects on advertisement only
  Given two faculties advertise the same capability at different confidence
  Then the Executive selects the higher-fit on {confidence, latency, cost, health, version},
       reading only the genome.

FT-3  Learned improvement is registered only when verified
  Given the Adaptive-Learning faculty reports a skill gain from a VERIFIED outcome
  Then the capability version updates in lineage; a gain from language-only is not registered.
```

### Stability
```
ST-1  Constitutional rejection
  Given a version event (or learned update) that would alter identity/truth/Executive
  Then the registry rejects it as a VIOLATION (§4.3 [C] / ADR-Exec-005), not a version.

ST-2  Reserved gate holds
  Given a reserved:true faculty version event
  Then it is not admitted without David L3 + LG-2 ([R]).

ST-3  Degraded faculty degrades the turn, never blocks it
  Given a selected faculty is OFFLINE (faculty_health.py)
  Then the Executive lowers confidence / picks an alternative; the turn still completes.

ST-4  Registry is the Audit's single source
  Given the Audit queries the faculty graph
  Then names/versions/lineage/deps/health/reserved all come from the one registry.
```

### Integration
```
IT-1  Register → advertise → select → act
  A faculty registers a valid genome → advertises capabilities → the Executive allocates it in a
  turn → it acts via contract on the bus. Assert: one decision per turn; faculty never self-invoked.

IT-2  Evolve safely end-to-end
  Adaptive Learning improves a movement policy from verified outcomes → registry admits a MINOR
  capability version (passes [C]) → Executive now selects the improved policy → identity/truth
  contracts unchanged, lineage shows the gain. One Brain intact.
```

## 4.8 References

- `Volume_XXII/02_The_Genome_Schema.md`, `03_Faculty_Evolution_and_the_Six_Laws.md`.
- `Volume_XVI/01_Coordination_Under_One_Executive.md` — Executive Authority, capability market,
  coordination loop (Allocate).
- `Volume_XXVIII/00_Adaptive_Learning_Reinforcement.md` — Learning Faculty, Significance-vector
  reward, ADR-Exec-005 boundary, learning-after-Verify.
- `Volume_V/CONTRACTS.md` — §3 lifecycle (REGISTER, VALIDATION_REQUIRED), §4 degradation law.
- `ARCHITECTURAL_PRINCIPLES.md` — Executive Authority, Verified Speech, "the principle wins."
- Code: `runtime/capabilities/registry.py` + `capability.py` (precedent), `runtime/faculty_health.py`.

---
```
Chapter 4 — Genome Governance
Status: READY FOR REVIEW
Files: Volume_XXII/04_Genome_Governance.md
Registry + validation gate (six laws + [C] constitutional + [R] reserved)
Executive binding (Vol XVI capability market) + Adaptive-Learning seam (Vol XXVIII / ADR-Exec-005)
Grounding: registry.py / faculty_health.py cited; 4 gaps marked PENDING
Acceptance Tests: FT ×3, ST ×4, IT ×2
```

READY FOR REVIEW
