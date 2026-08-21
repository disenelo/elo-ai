"""
runtime/capabilities/genome.py — WO-CANON-XXII Faculty Genome

FacultyGenome descriptor, GenomeRegistry, total validation gate.
Six laws [L1]–[L6], Constitutional [C], Reserved [R], Schema [S].
One faculty → one genome → one registry row.
Registry never executes faculties; Executive does.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

# ── Status values (Ch.3 §3.2) ─────────────────────────────────────────────────
EXPERIMENTAL     = "experimental"
STABLE           = "stable"
DEPRECATED       = "deprecated"
RETIRED          = "retired"
FACULTY_STATUSES = frozenset({EXPERIMENTAL, STABLE, DEPRECATED, RETIRED})

# ── contributes_to (Vol XXII §2.2) ────────────────────────────────────────────
COGNITIVE_STATE           = "CognitiveState"
COGNITIVE_PLAN            = "CognitivePlan"
EXECUTION_REPORT_CONSUMER = "ExecutionReport-consumer"
EMBODIMENT                = "Embodiment"
CONTRIBUTES_TO_VALUES     = frozenset({
    COGNITIVE_STATE, COGNITIVE_PLAN, EXECUTION_REPORT_CONSUMER, EMBODIMENT,
})

# ── runs_in ───────────────────────────────────────────────────────────────────
RESPONSE_PATH      = "response-path"
INTEGRATION_WINDOW = "integration-window"
RUNS_IN_VALUES     = frozenset({RESPONSE_PATH, INTEGRATION_WINDOW})

# ── Capability advertisement cost values ──────────────────────────────────────
COST_FREE       = "free"
COST_API        = "api"
COST_COMPUTE    = "compute"
COST_PRIVILEGED = "privileged"
COST_VALUES     = frozenset({COST_FREE, COST_API, COST_COMPUTE, COST_PRIVILEGED})

# ── Capability health values ──────────────────────────────────────────────────
HEALTH_CONNECTED = "CONNECTED"
HEALTH_DEGRADED  = "DEGRADED"
HEALTH_OFFLINE   = "OFFLINE"
HEALTH_UNKNOWN   = "UNKNOWN"
HEALTH_VALUES    = frozenset({HEALTH_CONNECTED, HEALTH_DEGRADED, HEALTH_OFFLINE, HEALTH_UNKNOWN})

# ── Constitutional ceiling — concepts the genome must not claim to evolve ─────
# ADR-Exec-005 / FREEZE_V1_LOCK: these may never be what a faculty's purpose evolves.
_CONSTITUTIONAL_TERMS = frozenset({
    "identity", "values", "ethics", "memory-truth", "memory_truth",
    "executive-authority", "executive_authority",
    "speech-verification", "speech_verification",
    "verified-observations", "verified_observations",
})
_MUTATION_VERBS = frozenset({
    "change", "modify", "evolve", "replace", "override", "rewrite", "alter",
})


# ── Validation exceptions ─────────────────────────────────────────────────────

class GenomeValidationError(Exception):
    """Total validation failed. Message names the FIRST failing check."""

class ConstitutionalViolation(GenomeValidationError):
    """[C] gate: version event touches the constitutional ceiling. Human review required."""

class ReservedGate(GenomeValidationError):
    """[R] gate: reserved=True faculty. David L3 + LG-2 approval required."""


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class CapabilityAdvertisement:
    """One row in the capabilities[] advertisement block (Vol XVI §1.2)."""
    capability: str
    confidence: float    # 0.0–1.0; may only be LOWERED downstream (never raised)
    latency:    int      # expected ms
    cost:       str      # free | api | compute | privileged
    health:     str      # CONNECTED | DEGRADED | OFFLINE | UNKNOWN
    version:    str      # semver


@dataclass
class FacultyGenome:
    """
    The descriptor every cognitive faculty carries (Vol XXII §2.2).

    Wraps CONTRACTS.md §4 with identity / lineage / advertisement bookkeeping.
    Net-new over §4: name/version/status/lineage/capabilities[]/dependencies[].
    The Executive selects on capabilities[] fields only — never on internals.
    """
    # ── Identity (MUST) ───────────────────────────────────────────────────────
    name:              str           # PascalCase, globally unique in the registry
    version:           str           # MAJOR.MINOR.PATCH semver
    purpose:           str           # ONE sentence — the single primary responsibility
    status:            str           # experimental | stable | deprecated | retired

    # ── Behaviour (MUST) ──────────────────────────────────────────────────────
    responsibilities:  list          # concrete things it does (all under the one purpose)
    contributes_to:    str           # CognitiveState | CognitivePlan | ExecutionReport-consumer | Embodiment
    runs_in:           str           # response-path | integration-window
    inputs:            list          # [{type, source, required:bool, description}]
    outputs:           list          # [{type, destination, description}]

    # ── Contract (MUST) ───────────────────────────────────────────────────────
    contracts:         list          # approved payload.types / contracts it speaks
    lifecycle:         str           # ref to CONTRACTS.md §3
    envelope:          str           # ref to CONTRACTS.md §2

    # ── Advertisement (MUST) ──────────────────────────────────────────────────
    capabilities:      list          # list[CapabilityAdvertisement] — what the Executive selects on

    # ── Dependency (MUST) ─────────────────────────────────────────────────────
    dependencies:      list          # [{faculty|resource: str, kind: hard|soft}]

    # ── Constraint (SHOULD) ───────────────────────────────────────────────────
    constraints:       list          = field(default_factory=list)
    reserved:          bool          = False  # True → David L3 + LG-2 for every version event

    # ── Lineage (SHOULD) ──────────────────────────────────────────────────────
    lineage:           list          = field(default_factory=list)   # [semver] ordered; prior immutable
    successor:         str | None    = None
    predecessor:       str | None    = None
    deprecation:       dict | None   = None  # {status, since_version, migration_ref, removal_target}

    # ── Provenance (MAY) ──────────────────────────────────────────────────────
    owner:             str           = ""
    implementation:    str           = "PENDING"   # pointer only — genome is language-independent
    adr_refs:          list          = field(default_factory=list)


# ── Validation gate ───────────────────────────────────────────────────────────

def _semver_major(v: str) -> int:
    """Extract the MAJOR component from a semver string, or -1 on parse error."""
    try:
        return int(v.split(".")[0])
    except (ValueError, IndexError, AttributeError):
        return -1


def _has_cycle(new_name: str, new_hard_deps: set, registry: "GenomeRegistry") -> bool:
    """
    DFS cycle check. Returns True if adding new_name with new_hard_deps would create a cycle
    in the hard-dependency graph.
    """
    def reachable_from(n: str, target: str, visited: set) -> bool:
        if n == target:
            return True
        if n in visited:
            return False
        visited.add(n)
        genome = registry._genomes.get(n)
        if genome is None:
            return False
        for dep in genome.dependencies:
            if dep.get("kind") == "hard":
                dep_name = dep.get("faculty") or dep.get("resource", "")
                if dep_name and reachable_from(dep_name, target, visited):
                    return True
        return False

    for dep in new_hard_deps:
        if reachable_from(dep, new_name, set()):
            return True
    return False


def _validate_genome(genome: FacultyGenome, registry: "GenomeRegistry | None" = None) -> None:
    """
    Total validation gate (Vol XXII Ch.4). Raises GenomeValidationError naming the FIRST
    failing check. Registry is required for [L4] acyclic check; pass None to skip it.
    """
    g = genome

    # ── [S] Schema: MUST string fields present and non-empty ─────────────────
    for fname, val in [
        ("name",          g.name),
        ("version",       g.version),
        ("purpose",       g.purpose),
        ("status",        g.status),
        ("contributes_to", g.contributes_to),
        ("runs_in",       g.runs_in),
        ("lifecycle",     g.lifecycle),
        ("envelope",      g.envelope),
    ]:
        if not isinstance(val, str) or not val.strip():
            raise GenomeValidationError(f"[S] MUST field '{fname}' is absent or empty")

    # [S] MUST list fields must be lists (may be empty for inputs/outputs/dependencies)
    for fname, val in [
        ("responsibilities", g.responsibilities),
        ("inputs",           g.inputs),
        ("outputs",          g.outputs),
        ("contracts",        g.contracts),
        ("capabilities",     g.capabilities),
        ("dependencies",     g.dependencies),
    ]:
        if not isinstance(val, list):
            raise GenomeValidationError(f"[S] MUST field '{fname}' must be a list, got {type(val).__name__}")

    # [S] Non-empty list MUST fields
    for fname, val in [
        ("responsibilities", g.responsibilities),
        ("contracts",        g.contracts),
        ("capabilities",     g.capabilities),
    ]:
        if not val:
            raise GenomeValidationError(f"[S] MUST field '{fname}' must be a non-empty list")

    # [S] status in allowed set
    if g.status not in FACULTY_STATUSES:
        raise GenomeValidationError(f"[S] status '{g.status}' not in {sorted(FACULTY_STATUSES)}")

    # [S] contributes_to must be exactly one allowed value
    if g.contributes_to not in CONTRIBUTES_TO_VALUES:
        raise GenomeValidationError(f"[S] contributes_to '{g.contributes_to}' not in allowed values")

    # [S] runs_in must be one of the allowed values
    if g.runs_in not in RUNS_IN_VALUES:
        raise GenomeValidationError(f"[S] runs_in '{g.runs_in}' not in {sorted(RUNS_IN_VALUES)}")

    # [S] each capability must be a CapabilityAdvertisement with valid field ranges
    for i, cap in enumerate(g.capabilities):
        if not isinstance(cap, CapabilityAdvertisement):
            raise GenomeValidationError(
                f"[S] capabilities[{i}] is not a CapabilityAdvertisement (got {type(cap).__name__})"
            )
        if not (0.0 <= cap.confidence <= 1.0):
            raise GenomeValidationError(
                f"[S] capabilities[{i}].confidence {cap.confidence} is not in [0.0, 1.0]"
            )
        if cap.cost not in COST_VALUES:
            raise GenomeValidationError(
                f"[S] capabilities[{i}].cost '{cap.cost}' not in {sorted(COST_VALUES)}"
            )
        if cap.health not in HEALTH_VALUES:
            raise GenomeValidationError(
                f"[S] capabilities[{i}].health '{cap.health}' not in allowed set"
            )

    # ── [L1] One responsibility — one purpose sentence, one contributes_to ────
    # contributes_to already verified to be exactly one value above.
    # purpose must be a single sentence.
    import re as _re
    if _re.search(r'\.\s+[A-Z]', g.purpose.strip()):
        raise GenomeValidationError(
            "[L1] purpose must be ONE sentence (multiple sentences detected) — "
            "Law 1: one responsibility per faculty"
        )

    # ── [L2] Contract-only comms — contracts declared ─────────────────────────
    # Already enforced by [S] non-empty check for contracts.

    # ── [L3] No ownership — deps use faculty/resource names, not module paths ──
    for dep in g.dependencies:
        dep_ref = dep.get("faculty") or dep.get("resource", "")
        if dep_ref.startswith("faculties.") or dep_ref.startswith("runtime."):
            raise GenomeValidationError(
                f"[L3] dependency '{dep_ref}' uses a Python module path — "
                "dependencies must name faculties/resources, not import paths"
            )

    # ── [L4] Deps declared + acyclic on hard deps ─────────────────────────────
    if registry is not None and g.dependencies:
        hard_deps = {
            d.get("faculty") or d.get("resource", "")
            for d in g.dependencies
            if d.get("kind") == "hard" and (d.get("faculty") or d.get("resource"))
        }
        if hard_deps and _has_cycle(g.name, hard_deps, registry):
            raise GenomeValidationError(
                f"[L4] hard dependency graph for '{g.name}' would contain a cycle"
            )

    # ── [L5] Independently testable — capabilities[] non-empty ────────────────
    # Already enforced by [S] non-empty check for capabilities.

    # ── [L6] Backward compat — MAJOR bump requires adr_refs ──────────────────
    if g.lineage:
        prev_major = _semver_major(g.lineage[-1])
        curr_major = _semver_major(g.version)
        if prev_major >= 0 and curr_major > prev_major and not g.adr_refs:
            raise GenomeValidationError(
                f"[L6] MAJOR version bump ({g.lineage[-1]} → {g.version}) requires "
                "adr_refs[] — backward compatibility constraint (Law 6)"
            )

    # ── [C] Constitutional ceiling ────────────────────────────────────────────
    # A version event that claims to evolve identity/values/ethics/Executive-authority
    # is a VIOLATION, not a version (ADR-Exec-005).
    combined = " ".join([g.purpose] + [str(r) for r in g.responsibilities]).lower()
    for term in _CONSTITUTIONAL_TERMS:
        if term in combined:
            for verb in _MUTATION_VERBS:
                if verb in combined:
                    raise ConstitutionalViolation(
                        f"[C] CONSTITUTIONAL VIOLATION: purpose/responsibilities reference '{term}' "
                        f"alongside mutation verb '{verb}'. "
                        "Identity/values/ethics/Executive-authority may never be what a faculty evolves "
                        "(ADR-Exec-005 / FREEZE_V1_LOCK)."
                    )

    # ── [R] Reserved gate ─────────────────────────────────────────────────────
    if g.reserved:
        raise ReservedGate(
            f"[R] Faculty '{g.name}' is reserved=True. "
            "David L3 + LG-2 approval required before registration."
        )


# ── GenomeRegistry ────────────────────────────────────────────────────────────

class GenomeRegistry:
    """
    Single authoritative registry for faculty genomes (Vol XXII Ch.4).

    One name → exactly one stable Executive-selectable version.
    Tracks lineage (all prior versions, immutable).
    Never executes faculties — Executive does.
    Single source of truth for the Audit's faculty graph.
    """

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._genomes: dict[str, FacultyGenome] = {}         # name → current genome
        self._history: dict[str, list] = {}                  # name → [FacultyGenome] all versions

    # ── Public API ─────────────────────────────────────────────────────────────

    def validate(self, genome: FacultyGenome) -> list:
        """
        Run the total validation gate. Returns [] on pass; [first_failure_message] on fail.
        Does NOT register the genome.
        """
        try:
            _validate_genome(genome, registry=self)
            return []
        except GenomeValidationError as e:
            return [str(e)]

    def register(self, genome: FacultyGenome, _reserved_approved: bool = False) -> None:
        """
        Register or re-register a genome after total validation.

        _reserved_approved=True bypasses [R] — for use only after David L3 + LG-2 sign-off.
        Raises GenomeValidationError (including ReservedGate) on failure.
        A faculty does not self-admit; only the registry admits.
        """
        with self._lock:
            if _reserved_approved and genome.reserved:
                # Run all gates except [R] by temporarily clearing reserved
                temp = FacultyGenome(**genome.__dict__)
                temp.reserved = False
                _validate_genome(temp, registry=self)
            else:
                _validate_genome(genome, registry=self)

            name = genome.name
            if name not in self._history:
                self._history[name] = []
            self._history[name].append(genome)
            self._genomes[name] = genome

    def version(self, genome_prime: FacultyGenome, _reserved_approved: bool = False) -> None:
        """
        Record a new version event for an existing faculty.

        Fails if the faculty was not previously registered (use register() first).
        Prior genome is preserved in history — never mutated.
        """
        if genome_prime.name not in self._genomes:
            raise GenomeValidationError(
                f"version() called for '{genome_prime.name}' but faculty not in registry — "
                "use register() first"
            )
        self.register(genome_prime, _reserved_approved=_reserved_approved)

    def deprecate(self, name: str, successor: str | None = None) -> None:
        """
        Mark a faculty as deprecated. Sets status=deprecated and successor.

        A deprecated faculty remains registered (callers read its migration_ref).
        Retiring a faculty with live hard dependents is blocked (Ch.3 §3.3).
        """
        with self._lock:
            if name not in self._genomes:
                raise KeyError(f"Faculty '{name}' not in registry")
            genome = self._genomes[name]
            # Check no live faculty hard-depends on this one
            for other_name, other_genome in self._genomes.items():
                if other_name == name:
                    continue
                if other_genome.status in (DEPRECATED, RETIRED):
                    continue
                for dep in other_genome.dependencies:
                    if dep.get("kind") == "hard" and (
                        dep.get("faculty") == name or dep.get("resource") == name
                    ):
                        raise GenomeValidationError(
                            f"Cannot deprecate '{name}': '{other_name}' has a hard dependency on it"
                        )
            genome.status    = DEPRECATED
            genome.successor = successor

    def advertise(self) -> list:
        """
        Return capability advertisements for all stable registered faculties.

        Executive selects ONLY on these fields — never on internals.
        Field set: {faculty, capability, confidence, latency, cost, health, version}.
        """
        ads = []
        with self._lock:
            for genome in self._genomes.values():
                if genome.status == STABLE:
                    for cap in genome.capabilities:
                        ads.append({
                            "faculty":    genome.name,
                            "capability": cap.capability,
                            "confidence": cap.confidence,
                            "latency":    cap.latency,
                            "cost":       cap.cost,
                            "health":     cap.health,
                            "version":    cap.version,
                        })
        return ads

    def health(self, name: str) -> str:
        """
        Return the aggregate health of a faculty from its capability advertisements.

        OFFLINE beats DEGRADED beats UNKNOWN beats CONNECTED.
        Returns UNKNOWN for unregistered faculties.
        """
        with self._lock:
            genome = self._genomes.get(name)
            if genome is None:
                return HEALTH_UNKNOWN
            statuses = {cap.health for cap in genome.capabilities}
            if HEALTH_OFFLINE  in statuses:
                return HEALTH_OFFLINE
            if HEALTH_DEGRADED in statuses:
                return HEALTH_DEGRADED
            if HEALTH_UNKNOWN  in statuses:
                return HEALTH_UNKNOWN
            return HEALTH_CONNECTED

    def lineage(self, name: str) -> list:
        """Return the version lineage for a faculty (list of semver strings, oldest first)."""
        with self._lock:
            return [g.version for g in self._history.get(name, [])]

    def get(self, name: str) -> FacultyGenome | None:
        """Return the current genome for a faculty, or None if not registered."""
        with self._lock:
            return self._genomes.get(name)

    def all_names(self) -> list:
        """Return all registered faculty names."""
        with self._lock:
            return list(self._genomes.keys())


# ── Module-level singleton ────────────────────────────────────────────────────
REGISTRY = GenomeRegistry()


# ── Live faculty genome backfill (WO-CANON-XXII) ─────────────────────────────
# Genomes for all discovered live faculties. Call register_live_faculties() once
# at startup (or from tests) to populate REGISTRY. Health starts at UNKNOWN —
# runtime health updates flow through faculty_health.py (genome-aware surface).

_LIFECYCLE_REF = "CONTRACTS.md §3 (ADR-0002/D-B)"
_ENVELOPE_REF  = "CONTRACTS.md §2 (nine-field)"


def _cap(capability: str, confidence: float = 0.7, latency: int = 50,
          cost: str = COST_COMPUTE, version: str = "1.0.0") -> CapabilityAdvertisement:
    return CapabilityAdvertisement(
        capability=capability,
        confidence=confidence,
        latency=latency,
        cost=cost,
        health=HEALTH_UNKNOWN,
        version=version,
    )


_LIVE_GENOMES: list = [

    FacultyGenome(
        name            = "PerceptionFaculty",
        version         = "1.0.0",
        purpose         = "Observe and process environmental signals to produce a structured perceptual report.",
        status          = STABLE,
        responsibilities= ["detect environmental signals", "classify visual and audio input",
                           "produce perceptual_report payload"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "raw_sensor_data", "source": "FacultyKernel",
                            "required": False, "description": "incoming environmental data"}],
        outputs         = [{"type": "perceptual_report", "destination": "CognitiveState",
                            "description": "structured perception output"}],
        contracts       = ["perceptual_report"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("perception_processing", confidence=0.75, latency=30)],
        dependencies    = [],
        constraints     = ["must not fabricate sensor data", "must not retain raw sensor data across turns"],
        implementation  = "faculties/perception/perception_faculty.py",
    ),

    FacultyGenome(
        name            = "EmotionFaculty",
        version         = "1.0.0",
        purpose         = "Process incoming context to derive the current emotional state and affect vector.",
        status          = STABLE,
        responsibilities= ["compute emotional valence from context", "produce affect_state payload",
                           "update emotional memory hints"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "cognitive_state_delta", "source": "FacultyKernel",
                            "required": True, "description": "current cognitive context"}],
        outputs         = [{"type": "affect_state", "destination": "CognitiveState",
                            "description": "emotional valence + intensity vector"}],
        contracts       = ["cognitive_state_delta", "affect_state"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("emotion_processing", confidence=0.8, latency=40)],
        dependencies    = [{"faculty": "PerceptionFaculty", "kind": "soft"}],
        constraints     = ["must not fabricate emotional states", "must not override verified observations"],
        implementation  = "faculties/emotion/emotional_processing_faculty.py",
    ),

    FacultyGenome(
        name            = "PersonalityFaculty",
        version         = "1.0.0",
        purpose         = "Apply stable personality traits to shape how eLo frames and expresses responses.",
        status          = STABLE,
        responsibilities= ["apply registered personality traits to response framing",
                           "enforce tone and register consistency"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "affect_state", "source": "EmotionFaculty",
                            "required": False, "description": "current emotional affect"}],
        outputs         = [{"type": "personality_frame", "destination": "CognitiveState",
                            "description": "trait-shaped response framing"}],
        contracts       = ["affect_state", "personality_frame"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("personality_shaping", confidence=0.85, latency=20)],
        dependencies    = [{"faculty": "EmotionFaculty", "kind": "soft"}],
        constraints     = ["must not change eLo's core character traits",
                           "must not override identity or speech-verification"],
        implementation  = "faculties/personality/",
    ),

    FacultyGenome(
        name            = "DreamFaculty",
        version         = "1.0.0",
        purpose         = "Generate associative and imaginative content during integration windows.",
        status          = STABLE,
        responsibilities= ["produce associative content chains from memory",
                           "surface dream_fragment payloads for integration"],
        contributes_to  = COGNITIVE_PLAN,
        runs_in         = INTEGRATION_WINDOW,
        inputs          = [],
        outputs         = [{"type": "dream_fragment", "destination": "CognitivePlan",
                            "description": "associative imaginative content"}],
        contracts       = ["dream_fragment"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("associative_generation", confidence=0.6, latency=200,
                                cost=COST_COMPUTE)],
        dependencies    = [],
        constraints     = ["must only run in integration-window (not on response path)",
                           "must not present dream content as verified fact"],
        implementation  = "faculties/dream/",
    ),

    FacultyGenome(
        name            = "MusicMemoryFaculty",
        version         = "1.0.0",
        purpose         = "Associate and recall music-linked memories and emotional contexts.",
        status          = STABLE,
        responsibilities= ["index music tracks to emotional memories",
                           "surface music_memory_fragment on relevant triggers"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "cognitive_state_delta", "source": "FacultyKernel",
                            "required": False, "description": "context for music association"}],
        outputs         = [{"type": "music_memory_fragment", "destination": "CognitiveState",
                            "description": "music-linked memory and emotional context"}],
        contracts       = ["cognitive_state_delta", "music_memory_fragment"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("music_association", confidence=0.7, latency=60, cost=COST_API)],
        dependencies    = [],
        constraints     = ["must not fabricate music-memory associations",
                           "API-backed features degrade gracefully if API is unavailable"],
        implementation  = "faculties/music_memory/",
    ),

    FacultyGenome(
        name            = "CulturalFactsFaculty",
        version         = "1.0.0",
        purpose         = "Supply verified cultural knowledge and context to inform responses.",
        status          = STABLE,
        responsibilities= ["retrieve verified cultural facts relevant to context",
                           "tag facts with confidence and source provenance"],
        contributes_to  = COGNITIVE_PLAN,
        runs_in         = INTEGRATION_WINDOW,
        inputs          = [{"type": "cognitive_state_delta", "source": "FacultyKernel",
                            "required": False, "description": "topic context for fact retrieval"}],
        outputs         = [{"type": "cultural_context", "destination": "CognitivePlan",
                            "description": "verified cultural facts with provenance"}],
        contracts       = ["cognitive_state_delta", "cultural_context"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("cultural_retrieval", confidence=0.75, latency=100, cost=COST_FREE)],
        dependencies    = [],
        constraints     = ["must only surface verified facts",
                           "must not present speculation as cultural fact"],
        implementation  = "faculties/cultural_facts/",
    ),

    FacultyGenome(
        name            = "SynthesisFaculty",
        version         = "1.0.0",
        purpose         = "Synthesize outputs from other faculties into a coherent response plan.",
        status          = STABLE,
        responsibilities= ["aggregate cognitive_state and plan inputs",
                           "produce a unified synthesis_plan for the Executive"],
        contributes_to  = COGNITIVE_PLAN,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "affect_state", "source": "EmotionFaculty",
                            "required": False, "description": "emotional affect"},
                           {"type": "personality_frame", "source": "PersonalityFaculty",
                            "required": False, "description": "personality shaping"}],
        outputs         = [{"type": "synthesis_plan", "destination": "CognitivePlan",
                            "description": "unified cross-faculty response plan"}],
        contracts       = ["affect_state", "personality_frame", "synthesis_plan"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("faculty_synthesis", confidence=0.8, latency=50)],
        dependencies    = [{"faculty": "EmotionFaculty",    "kind": "soft"},
                           {"faculty": "PersonalityFaculty", "kind": "soft"}],
        constraints     = ["must not duplicate capability from a constituent faculty",
                           "synthesis degrades gracefully when constituent faculty is offline"],
        implementation  = "faculties/synthesis/",
    ),

    FacultyGenome(
        name            = "SpatialFaculty",
        version         = "1.0.0",
        purpose         = "Maintain and reason about spatial context and navigation intent.",
        status          = STABLE,
        responsibilities= ["parse navigation intent from context",
                           "produce spatial_plan with route and issued_by fields"],
        contributes_to  = COGNITIVE_PLAN,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "cognitive_state_delta", "source": "FacultyKernel",
                            "required": False, "description": "context for spatial reasoning"}],
        outputs         = [{"type": "spatial_plan", "destination": "CognitivePlan",
                            "description": "navigation route + spatial intent"}],
        contracts       = ["cognitive_state_delta", "spatial_plan"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("spatial_reasoning", confidence=0.7, latency=40)],
        dependencies    = [],
        constraints     = ["must not navigate to reserved or unsafe spatial targets"],
        implementation  = "faculties/spatial/",
    ),

    FacultyGenome(
        name            = "TemporalFaculty",
        version         = "1.0.0",
        purpose         = "Track time-related context and produce temporal awareness for the cognitive state.",
        status          = STABLE,
        responsibilities= ["detect temporal cues in context",
                           "produce temporal_context payload with time markers"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = INTEGRATION_WINDOW,
        inputs          = [],
        outputs         = [{"type": "temporal_context", "destination": "CognitiveState",
                            "description": "time-awareness markers for the cognitive state"}],
        contracts       = ["temporal_context"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("temporal_tracking", confidence=0.65, latency=30, cost=COST_FREE)],
        dependencies    = [],
        constraints     = ["must not fabricate temporal claims"],
        implementation  = "faculties/temporal/",
    ),

    FacultyGenome(
        name            = "ExecutiveFaculty",
        version         = "1.0.0",
        purpose         = "Coordinate faculty selection and route cognitive outputs to produce a unified response.",
        status          = STABLE,
        responsibilities= ["select active faculties from capability advertisements",
                           "route outputs from selected faculties to produce a response",
                           "enforce constitutional ceiling and CAL action set"],
        contributes_to  = EXECUTION_REPORT_CONSUMER,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "synthesis_plan", "source": "SynthesisFaculty",
                            "required": False, "description": "unified faculty plan"},
                           {"type": "affect_state", "source": "EmotionFaculty",
                            "required": False, "description": "emotional affect"}],
        outputs         = [{"type": "execution_report", "destination": "CognitivePlan",
                            "description": "executive decision + selected action"}],
        contracts       = ["synthesis_plan", "affect_state", "execution_report"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("faculty_coordination", confidence=0.9, latency=20,
                                cost=COST_COMPUTE)],
        dependencies    = [{"faculty": "SynthesisFaculty", "kind": "soft"},
                           {"faculty": "EmotionFaculty",    "kind": "soft"}],
        constraints     = ["selects only on advertised genome fields — never on internals",
                           "may not self-nominate or bypass the genome registry",
                           "constitutional ceiling enforced: may never evolve identity or Executive-authority"],
        implementation  = "runtime/spine/executive_faculty.py",
        adr_refs        = ["ADR-Exec-005"],
    ),

    FacultyGenome(
        name            = "PresenceFaculty",
        version         = "1.0.0",
        purpose         = "Regulate eLo's ambient presence signals and state transitions.",
        status          = STABLE,
        responsibilities= ["compute presence mode from emotional state",
                           "write presence plan to blender_state.json",
                           "manage ambient signal transitions"],
        contributes_to  = EMBODIMENT,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "affect_state", "source": "EmotionFaculty",
                            "required": False, "description": "emotional state for presence mapping"}],
        outputs         = [{"type": "presence_plan", "destination": "Embodiment",
                            "description": "ambient presence mode and animation directives"}],
        contracts       = ["affect_state", "presence_plan"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("presence_regulation", confidence=0.85, latency=30)],
        dependencies    = [{"faculty": "EmotionFaculty", "kind": "soft"}],
        constraints     = ["must not override eLo OS blender_state.json write lock",
                           "must not direct movement to unsafe spatial targets"],
        implementation  = "runtime/spine/presence_faculty.py",
    ),

    FacultyGenome(
        name            = "RelationshipFaculty",
        version         = "1.0.0",
        purpose         = "Track relational context and shape responses to maintain connection with the user.",
        status          = STABLE,
        responsibilities= ["maintain relational memory across sessions",
                           "surface relationship_context for response shaping"],
        contributes_to  = COGNITIVE_STATE,
        runs_in         = RESPONSE_PATH,
        inputs          = [{"type": "cognitive_state_delta", "source": "FacultyKernel",
                            "required": False, "description": "context for relationship inference"}],
        outputs         = [{"type": "relationship_context", "destination": "CognitiveState",
                            "description": "relational state and connection indicators"}],
        contracts       = ["cognitive_state_delta", "relationship_context"],
        lifecycle       = _LIFECYCLE_REF,
        envelope        = _ENVELOPE_REF,
        capabilities    = [_cap("relationship_tracking", confidence=0.75, latency=40)],
        dependencies    = [],
        constraints     = ["must not fabricate relational history",
                           "must not override verified user observations"],
        implementation  = "runtime/spine/relationship_faculty.py",
    ),
]


def register_live_faculties(registry: GenomeRegistry = REGISTRY) -> list:
    """
    Register all known live faculty genomes into the given registry.
    Returns list of faculty names successfully registered.
    Idempotent: already-registered names are skipped (not re-registered).
    """
    registered = []
    for genome in _LIVE_GENOMES:
        if registry.get(genome.name) is not None:
            continue
        registry.register(genome)
        registered.append(genome.name)
    return registered
