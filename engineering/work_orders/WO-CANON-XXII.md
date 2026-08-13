# WO-CANON-XXII — Faculty Genome: descriptor + registry + validation gate

**Owner:** Builder (eLo OS — `runtime/capabilities/`, `runtime/faculty_health.py`, `faculties/`, `runtime/spine/`).
**Priority:** P3 — Horizon-2 (post-Presentable v1), Tier B. **Status:** QUEUED behind Presentable v1 + Tier A.
**Blocked-by:** Vol XVI (Executive selection on advertised genome fields is Vol XVI §1.2). RESERVED version events need
David L3 + LG-2.

**Canon refs:** Volume XXII — Ch.1 `01_Genome_Schema_Evolution_Laws.md`, Ch.2 `02_The_Genome_Schema.md`, Ch.3
`03_Faculty_Evolution_and_the_Six_Laws.md`, Ch.4 `04_Genome_Governance.md`. Binds `Volume_V/CONTRACTS.md` §2/§3/§4;
ADR-Exec-005 (constitutional boundary). Live precedent: `runtime/capabilities/registry.py` + `capability.py`.

## Problem / Goal
Every cognitive faculty should carry a descriptor (its "DNA") and be admitted through one validating registry, so the
Executive selects faculties from advertised capability + health + version rather than hard-wired spine call order.
Today there is a LIVE structural precedent — `runtime/capabilities/registry.py` (a static ~40-capability catalogue the
router queries) + the `Capability` dataclass in `capability.py` — but it is for TOOLS, and no `faculties/` or
`runtime/spine/` faculty declares a genome. Goal: build the `FacultyGenome` type, the `GenomeRegistry`, and the
validation gate, then backfill genomes for the live faculties.

## Scope to DoD (grounded in Ch.1–Ch.4; extend the live precedent, do not fork)
- **Build the `FacultyGenome` descriptor (Ch.2 §2.2):** the field set every faculty carries — MUST blocks: Identity
  (`name` PascalCase globally unique, `version` semver, `purpose`, `status ∈ {experimental,stable,deprecated,retired}`),
  Behaviour (`responsibilities`, `contributes_to` ∈ exactly one of {CognitiveState, CognitivePlan,
  ExecutionReport-consumer, Embodiment}, `runs_in` ∈ {response-path, integration-window}), Contract
  (`inputs[]`/`outputs[]`/`contracts[]`/`lifecycle` ref/`envelope` ref), Advertisement (`capabilities[]` each
  capability/confidence/latency/cost/health/version), Dependency (`dependencies[]` hard|soft); SHOULD: `constraints[]`,
  `reserved` (bool), `lineage[]`, `successor`/`predecessor`, `deprecation{status, since_version, migration_ref,
  removal_target}`; MAY: `owner`, `implementation` (a pointer only — genome is language-independent),`adr_refs[]`. The
  genome **wraps** the CONTRACTS.md §4 base contract (net-new = identity/advertisement/lineage bookkeeping); must never
  contradict §4. `capabilities[].confidence` may only be lowered downstream, never raised.
- **Build the `GenomeRegistry` (Ch.4)** — single, authoritative, one row per faculty name; surface `register(genome)`,
  `version(genome')`, `advertise()`, `deprecate(name, succ)`, `health(name)`, `lineage(name)`, plus the
  `validate(genome)` gate. A faculty does not self-admit; the registry admits only if the genome passes the Ch.3 laws +
  Ch.2 MUST fields — validation is **total, not partial** (admit whole genome or reject naming the **first** failing
  law/field). One name → exactly one `stable` Executive-selectable version. Registry never executes a faculty (Executive
  does); it is the Audit's single source of truth for the faculty graph. `[L4]` dependency graph must be **acyclic on
  hard deps**.
- **Wire the validation gate checks:** `[S]` Schema, `[L1]`–`[L6]` the six laws (one responsibility / contract-only
  comms / no ownership / deps declared / independently testable / backward compat), `[C]` Constitutional (ADR-Exec-005 —
  auto-rejectable), `[R]` Reserved (David L3 + LG-2). `[C]` and `[R]` are hard human/constitutional gates the registry
  cannot auto-approve.
- **Evolution (Ch.3):** every change is a **version event**, never in-place mutation, recorded in `lineage` (prior
  genome immutable). Semver: MAJOR = breaking (migration path + ADR, Law 6; may need RESERVED gate); MINOR = additive;
  PATCH = no contract change. Experimental coexists but cannot become Executive-default until Canon acceptance.
  Composition over duplication (a capability that exists is referenced, never duplicated — duplicate fails review).
  Succession: `deprecated` runs to `removal_target`, `migration_ref` names where callers move, `successor` covers every
  advertised capability; retiring a faculty with live hard dependents is blocked; `reserved:true` faculties are RESERVED
  to retire/replace. Constitutional ceiling: may evolve skills/policies/preferences/confidence/latency/heuristics; may
  NEVER evolve identity/values/ethics/memory-truth/verified-observations/Executive-Authority/speech-verification —
  such a version event is rejected as a VIOLATION, not a version.
- **Backfill genomes for the live faculties** (`faculties/`: perception, emotion, significance, personality, dream,
  music_memory, cultural_facts, synthesis; `runtime/spine/`: executive, presence, relationship, reflection) — the "first
  implementation task." Extend `runtime/faculty_health.py` to a genome-aware per-faculty health surface keyed by `name`
  (today it has four coarse buckets and no `version` field). Executive selects **only** on advertised fields
  `{capability, confidence, latency, cost, health, version}`, never internals, never self-nomination.

## Definition of Done
- `FacultyGenome` + `GenomeRegistry` + total validation gate exist; every live faculty carries a validated genome; the
  Executive selects faculties from advertisements, not hard-wired call order.
- Version events recorded in lineage; the six laws + `[C]`/`[R]` gates enforced; constitutional ceiling holds.
- Registry is the Audit's single source of the faculty graph. Audit can mark Vol XXII COMPLETE.

## Tests to write (`tests/test_canon_xxii_genome.py`; namespace IDs e.g. V22-CH02-FT-1)
- Ch.2: full genome declared (missing MUST field named), advertisement honest (confidence lowered not raised on
  DEGRADED), one responsibility / one contributes_to, genome wraps not contradicts base contract, absent-not-fabricated
  health (UNKNOWN), immutable within a version, reserved cannot be relaxed, registry+market selection reads only the genome.
- Ch.3: version event not mutation, breaking change gated (Law 6), experimental never auto-promotes, succession loses no
  capability, the six laws (ST-1…ST-6), constitutional ceiling (ST-7 VIOLATION), evolve without fragmenting, learning
  obeys the ceiling.
- Ch.4: no self-admission (first failing check named), Executive selects on advertisement only, learned improvement
  registered only when verified, constitutional rejection, reserved gate holds (David L3 + LG-2), degraded faculty
  degrades the turn never blocks, registry is Audit's single source, register→advertise→select→act, evolve safely.

## Dependencies + blocked-by
- **Blocked by:** Vol XVI (WO-CANON-XVI — Executive capability-market selection is Vol XVI §1.2). Adaptive-Learning seam
  (Vol XXVIII) is itself PLANNED/scope-locked. Runs behind Presentable v1 + Tier A.
- **Gate:** any `reserved: true` version event → **David L3 + LG-2**. CA/David to review the Architect-derived semver
  table + experimental→stable→deprecated→retired flow + "successor covers every capability" rule (Ch.3 §3.4) before
  Vol XXII is promoted. `[C]` boundary is ADR-Exec-005.
- Cross-volume: Vol V CONTRACTS.md + 02_Faculty_System.md, Vol XXVIII (ADR-Exec-005).

## Lane
Builder (Python — genome type, registry, validation gate, genome backfill, health surface). Architect coordinates +
carries the derivation-review + RESERVED gate to CA/David. Backfilling genomes is the seat's, not the Architect's, code.
