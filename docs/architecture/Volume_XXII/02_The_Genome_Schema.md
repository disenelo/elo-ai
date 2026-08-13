---
chapter: 2
title: "The Genome Schema — The Descriptor Every Faculty Carries"
volume: XXII
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
received: 2026-08-10
dependencies:
  - Volume_XXII/01_Genome_Schema_Evolution_Laws.md (the compressed anchor this chapter expands)
  - Volume_V/CONTRACTS.md (§4 base faculty contract, §3 lifecycle, §2 envelope)
  - Volume_V/02_Faculty_System.md (the faculty network the genome describes)
  - Volume_XVI/01_Coordination_Under_One_Executive.md (capability advertisement fields)
  - runtime/capabilities/capability.py + registry.py (closest existing descriptor — tools, not faculties)
  - runtime/faculty_health.py (live per-faculty health — coarse, four buckets)
---

# Chapter 2: The Genome Schema

## 2.0 Purpose

Chapter 1 states the principle: every faculty is a **living architectural component** with
identity, capabilities, dependencies, and an evolutionary history, and the Genome is the DNA
that keeps expansion coherent with One Brain. This chapter turns that principle into a
**precise, fillable descriptor** — the exact fields every faculty declares, what each means,
which are mandatory, and how the descriptor binds to the contracts already ratified elsewhere.

The genome is **not a new runtime object competing with the Faculty Contract** (`CONTRACTS.md §4`).
It is that contract **plus the fields that let a faculty be versioned, traced, and governed over
time**: identity, lineage, capability advertisement, and constraints. One faculty → one genome →
one registry row. If a faculty exists and it is not fully described by a genome, the volume's job
is not done for that faculty.

## 2.1 Principle — the descriptor is the faculty's identity to the system

Three rules govern the descriptor. They are constraints on every faculty author.

**2.1.1 A faculty IS its genome to everything outside it.** The Executive, the registry, the
Audit, and other faculties know a faculty *only* through its declared genome — never by reading
its internals. If a capability, dependency, or constraint is not in the genome, it does not exist
as far as the system is concerned. (This is the descriptor form of the Faculty-Bus rule: no
faculty reaches inside another.)

**2.1.2 Every field is honest or absent — never fabricated.** A capability advertised at
confidence 0.9 that actually fails is worse than one absent. Advertisement is a promise the
Executive selects on (Vol XVI §1.2). Unknown health is `UNKNOWN`, never an optimistic default.
This is Verified Speech applied to self-description: a faculty does not narrate a capability it
cannot verify it has.

**2.1.3 The genome is immutable within a version; change means a new version.** A running
faculty does not silently gain a field or a capability. Any change to what the genome declares
is a **version event** (Chapter 3) — recorded, not mutated in place. This is what lets lineage
be trusted.

## 2.2 The Genome Schema (canonical field set)

The genome is the `CONTRACTS.md §4` base contract, extended with the **identity/lineage/
advertisement/constraint** block. Fields marked **(MUST)** are mandatory for a faculty to pass
review; **(SHOULD)** are expected but degradable; **(MAY)** are optional.

```
FacultyGenome:

  # ── Identity block (MUST) ──────────────────────────────────────────────
  name:            str        # PascalCase, globally unique in the registry (Vol V Ch.1)
  version:         semver      # MAJOR.MINOR.PATCH — the unit of evolution (Ch.3)
  purpose:         str         # ONE sentence — the single primary responsibility (Law 1)
  status:          enum        # experimental | stable | deprecated | retired  (Ch.3)

  # ── Behaviour block (MUST) ─────────────────────────────────────────────
  responsibilities: [str]      # the concrete things it does — all under the one purpose
  contributes_to:  enum        # CognitiveState | CognitivePlan | ExecutionReport-consumer | Embodiment
  runs_in:         enum        # response-path | integration-window   (CONTRACTS.md §1)
  inputs:  [ {type, source, required:bool, description} ]   # payload.types it consumes
  outputs: [ {type, destination, description} ]             # payload.types it produces

  # ── Contract block (MUST) ──────────────────────────────────────────────
  contracts:       [str]       # the approved payload.types / contracts it speaks (CONTRACTS.md §2)
  lifecycle:       ref         # the ratified universal lifecycle (CONTRACTS.md §3, ADR-0002/D-B)
  envelope:        ref         # canonical nine-field envelope (CONTRACTS.md §2)

  # ── Advertisement block (MUST — this is what the Executive selects on) ──
  capabilities: [ {                      # one row per advertised capability (Vol XVI §1.2)
      capability:  str,                  # what it can do
      confidence:  float 0.0–1.0,        # producer confidence; may only be LOWERED downstream
      latency:     ms,                   # expected cost in time
      cost:        enum,                 # free | api | compute | privileged
      health:      enum,                 # CONNECTED | DEGRADED | OFFLINE (runtime/faculty_health.py)
      version:     semver } ]            # capability version (may trail faculty version)

  # ── Dependency block (MUST) ────────────────────────────────────────────
  dependencies: [ {faculty|resource, kind: hard|soft} ]     # hard = required; soft = degrades

  # ── Constraint block (SHOULD) ──────────────────────────────────────────
  constraints: [str]           # what it must NOT do; privilege/safety/identity boundaries
  reserved:     bool           # touches money · legal · safety · robot force/magnetics/pump → David L3 + LG-2

  # ── Lineage block (SHOULD — this is what makes evolution safe, Ch.3) ────
  lineage:         [semver]    # ordered version history of THIS faculty
  successor:       name|null   # the faculty that replaces this one, if deprecated
  predecessor:     name|null   # the faculty this one replaced, if any
  deprecation:     {status, since_version, migration_ref, removal_target} | null

  # ── Provenance block (MAY) ─────────────────────────────────────────────
  owner:           str         # accountable human (David L3 for reserved)
  implementation:  ref         # module path once built (PENDING until then)
  adr_refs:        [str]       # ADRs that authorised its existence / breaking changes
```

**Schema rules (MUST):**

- Every **MUST** field is present or the genome fails review. There is no partial registration —
  a faculty with a missing `purpose`, `contributes_to`, or `capabilities` block does not enter
  the registry (Chapter 4).
- `capabilities[].confidence` obeys the envelope law (`CONTRACTS.md §2`): it may only be
  **lowered** downstream, never raised. The genome states the ceiling; runtime health lowers it.
- `contributes_to` MUST be exactly one of the four; a faculty that would need two is two
  faculties (Law 1, Chapter 3).
- `reserved: true` binds the faculty to the RESERVED governance gate (David L3 + LG-2) for every
  version event — it cannot be relaxed by a later version.
- A genome describes a faculty **independent of implementation language** (Ch.1 §1.0). Nothing in
  the schema names Python; `implementation` is a pointer, not part of the identity.

## 2.3 How the genome maps onto the ratified contract

The genome does **not** restate the base contract — it **wraps** it. To avoid drift:

| Genome block | Authoritative source it binds to |
|---|---|
| Behaviour + Contract blocks | `CONTRACTS.md §4` base faculty contract (name/version/purpose/contributes_to/runs_in/inputs/outputs) |
| `lifecycle`, `envelope` | `CONTRACTS.md §3` (ratified lifecycle, ADR-0002/D-B), `§2` (nine-field envelope) |
| `capabilities[]` advertisement | Vol XVI §1.2 — the six fields the Executive clears the capability market on |
| `constraints`, `reserved` | Vol XVI §1.4 prohibitions; CLAUDE.md RESERVED gate |
| `lineage`/`successor`/`deprecation` | Chapter 3 (evolution model) — **new to this volume**, not in §4 |

The genome's **net-new contribution** over `CONTRACTS.md §4` is exactly the identity/advertisement/
lineage bookkeeping. Everything else is a typed reference to canon that already exists — so a
genome can never contradict the contract it points at.

## 2.4 Grounding — what exists live, what is PENDING

**What exists (cite):**

- `runtime/capabilities/capability.py` — a `Capability` dataclass with `id, display_name,
  category, description, verbs, synonyms, requires_confirmation, requires_api,
  requires_authentication, online, enabled, health_state, execution_priority, response_style,
  future, agent_module`, and health states `ONLINE/OFFLINE/AUTH_REQUIRED/DISABLED/UNAVAILABLE/
  FAILED/UNKNOWN`. This is the **closest live analogue** of the advertisement block — but it
  describes **tools/capabilities the router selects**, not cognitive faculties.
- `runtime/capabilities/registry.py` — a static catalogue of ~40 capabilities the router queries
  ("it never imports agents directly"). This is the structural precedent for a genome registry
  (Chapter 4) applied to tools.
- `runtime/faculty_health.py` — live per-faculty health, but only **four coarse buckets**
  (`reasoning`, `memory`, `tools`, `embodiment`) with `CONNECTED/DEGRADED/OFFLINE`, persisted to
  `blender/faculty_health.json`. This supplies the `capabilities[].health` field's live value —
  at tool granularity, not per-cognitive-faculty.
- `faculties/` — real cognitive faculties exist as modules (`perception`, `emotion`,
  `significance`, `personality`, `dream`, `music_memory`, `cultural_facts`, `synthesis`) plus
  `runtime/spine/` faculties (`executive`, `presence`, `relationship`, `reflection`). **None of
  them declares a genome** today; their contracts live only in canon (Vol V chapters).

**What is PENDING (gaps — do not claim these exist):**

- **PENDING** — There is **no cognitive-faculty genome descriptor** in code. `Capability`
  describes tools; there is no `FacultyGenome` type covering the identity/lineage/advertisement
  fields of §2.2 for cognitive faculties.
- **PENDING** — There is **no lineage/version/successor/deprecation tracking** anywhere. Faculty
  modules are unversioned; `faculty_health.py` has no `version` field. Chapter 3's evolution model
  has no runtime home yet.
- **PENDING** — `faculty_health.py`'s four buckets do not map 1:1 to the faculties in `faculties/`.
  A genome-aware health surface (per-faculty, keyed by `name`) is required and does not exist.
- **PENDING** — No registry validates the **MUST** fields at registration; nothing rejects a
  faculty that under-declares. The gate in Chapter 4 is spec-only.

## 2.5 Worked example — an existing faculty rendered as a genome

Illustrative only (the values below are how the **already-canon** Significance Faculty, Vol V
Ch.5, *would* declare itself — not new behaviour):

```
FacultyGenome:
  name:            SignificanceFaculty
  version:         1.0.0
  purpose:         "Decide how much a moment matters and write context.significance."
  status:          stable
  responsibilities: ["score significance vector", "set memory_instruction hints"]
  contributes_to:  CognitiveState
  runs_in:         response-path
  inputs:  [ {type: cognitive_state_delta, source: FacultyKernel, required: true} ]
  outputs: [ {type: affect_state, destination: CognitiveState, description: "significance vector"} ]
  contracts:       ["cognitive_state_delta", "affect_state"]
  lifecycle:       CONTRACTS.md §3 (ADR-0002/D-B)
  envelope:        CONTRACTS.md §2 (nine-field)
  capabilities: [ {capability: "significance_scoring", confidence: 0.8, latency: 40,
                   cost: compute, health: CONNECTED, version: 1.0.0} ]
  dependencies: [ {faculty: FacultyKernel, kind: hard}, {faculty: EmotionFaculty, kind: soft} ]
  constraints: ["writes context.significance ONLY (CONTRACTS.md §2 rule 3)", "never decides"]
  reserved:     false
  lineage:      [1.0.0]
  implementation: faculties/significance/significance_faculty.py
```

This shows the schema is **fillable from what already exists** — the volume formalises, it does
not invent the faculties. Backfilling a genome for each live faculty is the first implementation
task (flagged for the owning seats; **not** the Architect's to write in code — D-LANES).

## 2.6 Acceptance Tests

### Functional
```
FT-1  Full genome declared
  Given a faculty submitted for registration
  Then every MUST field (§2.2) is present, else it fails review with the missing field named.

FT-2  Advertisement is honest
  Given capabilities[].confidence = 0.9 but runtime health = DEGRADED
  Then the effective advertised confidence is LOWERED (never raised), per CONTRACTS.md §2.

FT-3  One responsibility, one contributes_to
  Given a genome with contributes_to listing two of {CognitiveState, CognitivePlan, ...}
  Then it fails review (that is two faculties — Law 1 / Ch.3).

FT-4  Genome wraps, never contradicts, the base contract
  Given a genome's Behaviour/Contract block
  Then it is a superset-reference of CONTRACTS.md §4; no field redefines §4 differently.
```

### Stability
```
ST-1  Absent, not fabricated
  Given a capability whose health cannot be determined
  Then health = UNKNOWN and confidence is not defaulted upward (§2.1.2).

ST-2  Immutable within a version
  Given a running faculty gains a new capability
  Then a version event is recorded (Ch.3); the current version's genome is unchanged.

ST-3  Reserved cannot be relaxed
  Given a reserved:true faculty publishes a new version dropping reserved
  Then it is blocked without David L3 + LG-2.
```

### Integration
```
IT-1  Registry + capability market
  A faculty registers its genome (Ch.4) → advertises capabilities (Vol XVI §1.2) →
  the Executive selects it on {capability, confidence, latency, cost, health, version}.
  Assert: selection reads ONLY the genome, never faculty internals.
```

## 2.7 References

- `Volume_XXII/01_Genome_Schema_Evolution_Laws.md` — the compressed anchor this chapter expands.
- `Volume_V/CONTRACTS.md` — §2 envelope, §3 lifecycle, §4 base faculty contract (authoritative).
- `Volume_V/02_Faculty_System.md` — the faculty network the genome describes.
- `Volume_XVI/01_Coordination_Under_One_Executive.md` — §1.2 capability advertisement fields.
- Code: `runtime/capabilities/capability.py`, `runtime/capabilities/registry.py`,
  `runtime/faculty_health.py`, `faculties/` (live faculties, currently genome-less).

---
```
Chapter 2 — The Genome Schema
Status: READY FOR REVIEW
Files: Volume_XXII/02_The_Genome_Schema.md
Schema: Full canonical field set (MUST/SHOULD/MAY) + mapping to ratified contract
Grounding: registry.py / capability.py / faculty_health.py cited; 4 gaps marked PENDING
Acceptance Tests: FT ×4, ST ×3, IT ×1
```

READY FOR REVIEW
