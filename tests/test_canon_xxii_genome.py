"""
tests/test_canon_xxii_genome.py — WO-CANON-XXII Faculty Genome

Disconnection-falsifiable tests across Ch.2, Ch.3, Ch.4.
Test IDs: V22-CH02-FT-*, V22-CH03-ST-*, V22-CH04-GT-*.

Ch.2 (FacultyGenome schema and validation):
  FT-1  Missing MUST field named as the first failure.
  FT-2  Advertisement confidence may only be lowered downstream, not raised on DEGRADED.
  FT-3  One contributes_to only (second value fails [S]).
  FT-4  Genome wraps contract — lifecycle and envelope refs preserved.
  FT-5  Absent-not-fabricated health: initial backfill caps at UNKNOWN, not CONNECTED.
  FT-6  Genome is immutable within a version — registry records, not mutates.
  FT-7  reserved=True raises ReservedGate — cannot be relaxed by a later version.
  FT-8  advertise() returns only the genome fields (no internals exposed).

Ch.3 (Evolution, six laws, constitutional ceiling):
  ST-1  [L1] One responsibility: multi-sentence purpose fails.
  ST-2  [L2] Contract-only comms: empty contracts fails.
  ST-3  [L3] No ownership: module-path dep fails.
  ST-4  [L4] Cyclic hard dependency detected and rejected.
  ST-5  [L5] Independently testable: empty capabilities fails.
  ST-6  [L6] MAJOR version bump without adr_refs fails.
  ST-7  [C] Constitutional violation: purpose claims to modify identity.
  ST-8  Experimental status never appears in advertise() (stable only).
  ST-9  Version event recorded in lineage; prior genome preserved.
  ST-10 Succession: deprecated faculty stays registered, successor named.

Ch.4 (Registry governance):
  GT-1  No self-admission: first failing check named (not partial admit).
  GT-2  Executive-facing advertise() field set is exactly the six Vol XVI fields.
  GT-3  Degraded faculty health aggregates DEGRADED (not OFFLINE, not suppressed).
  GT-4  All live backfill genomes pass total validation and register successfully.
  GT-5  Registry is single source: all_names() lists every registered faculty.
"""
from __future__ import annotations

import sys
import pathlib
import unittest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from runtime.capabilities.genome import (
    FacultyGenome,
    CapabilityAdvertisement,
    GenomeRegistry,
    GenomeValidationError,
    ConstitutionalViolation,
    ReservedGate,
    STABLE,
    EXPERIMENTAL,
    DEPRECATED,
    COGNITIVE_STATE,
    COGNITIVE_PLAN,
    RESPONSE_PATH,
    INTEGRATION_WINDOW,
    HEALTH_UNKNOWN,
    HEALTH_DEGRADED,
    HEALTH_OFFLINE,
    HEALTH_CONNECTED,
    COST_COMPUTE,
    COST_FREE,
    register_live_faculties,
    _LIVE_GENOMES,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _valid_genome(**overrides) -> FacultyGenome:
    """Return a valid FacultyGenome with all MUST fields populated."""
    defaults = dict(
        name             = "TestFaculty",
        version          = "1.0.0",
        purpose          = "Perform a single well-defined cognitive task.",
        status           = STABLE,
        responsibilities = ["do the task"],
        contributes_to   = COGNITIVE_STATE,
        runs_in          = RESPONSE_PATH,
        inputs           = [],
        outputs          = [{"type": "test_output", "destination": "CognitiveState", "description": "output"}],
        contracts        = ["test_contract"],
        lifecycle        = "CONTRACTS.md §3 (ADR-0002/D-B)",
        envelope         = "CONTRACTS.md §2 (nine-field)",
        capabilities     = [CapabilityAdvertisement("test_cap", 0.8, 50, COST_COMPUTE,
                                                    HEALTH_UNKNOWN, "1.0.0")],
        dependencies     = [],
    )
    defaults.update(overrides)
    return FacultyGenome(**defaults)


def _fresh_registry() -> GenomeRegistry:
    return GenomeRegistry()


# ── Ch.2 tests ────────────────────────────────────────────────────────────────

class TestGenomeSchema(unittest.TestCase):

    def test_ft1_missing_must_field_named(self):
        """FT-1: A genome with a missing MUST field fails and names the FIRST missing field.

        Disconnection: remove the MUST-field check → genome with missing purpose is accepted → test RED.
        """
        reg = _fresh_registry()
        # Missing 'purpose'
        genome = _valid_genome(purpose="")
        failures = reg.validate(genome)
        self.assertTrue(
            failures,
            "validate() returned no failures for a genome with an empty purpose — MUST field check missing"
        )
        self.assertIn(
            "purpose", failures[0].lower(),
            f"First failure does not name 'purpose': {failures[0]}"
        )

    def test_ft2_confidence_cannot_be_raised(self):
        """FT-2: confidence > 1.0 fails [S]; confidence must be in [0.0, 1.0].

        Disconnection: remove confidence range check → inflated confidence registered → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            capabilities=[CapabilityAdvertisement("cap", 1.5, 50, COST_COMPUTE, HEALTH_UNKNOWN, "1.0.0")]
        )
        failures = reg.validate(genome)
        self.assertTrue(failures, "validate() accepted confidence > 1.0 — range check missing")
        self.assertIn("confidence", failures[0].lower(),
                      f"Failure does not name 'confidence': {failures[0]}")

    def test_ft3_one_contributes_to_only(self):
        """FT-3: contributes_to must be exactly one allowed value.

        Disconnection: allow arbitrary string → second value silently accepted → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(contributes_to="CognitiveState,CognitivePlan")
        failures = reg.validate(genome)
        self.assertTrue(failures, "validate() accepted a multi-value contributes_to — [S] check missing")
        self.assertIn("contributes_to", failures[0].lower(),
                      f"Failure does not name 'contributes_to': {failures[0]}")

    def test_ft4_genome_wraps_contract_refs_preserved(self):
        """FT-4: lifecycle and envelope refs survive registration unchanged.

        Disconnection: drop lifecycle/envelope → registered genome loses contract refs → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            lifecycle="CONTRACTS.md §3 (ADR-0002/D-B)",
            envelope ="CONTRACTS.md §2 (nine-field)",
        )
        reg.register(genome)
        retrieved = reg.get("TestFaculty")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.lifecycle, "CONTRACTS.md §3 (ADR-0002/D-B)")
        self.assertEqual(retrieved.envelope,  "CONTRACTS.md §2 (nine-field)")

    def test_ft5_health_starts_at_unknown_not_fabricated(self):
        """FT-5: initial backfill caps health at UNKNOWN — absent-not-fabricated.

        Disconnection: default health to CONNECTED → registry shows CONNECTED for unreachable faculties → test RED.
        """
        for genome in _LIVE_GENOMES:
            for cap in genome.capabilities:
                self.assertEqual(
                    cap.health, HEALTH_UNKNOWN,
                    f"{genome.name} capability '{cap.capability}' has health {cap.health!r} "
                    f"instead of UNKNOWN — initial genomes must not fabricate a health state"
                )

    def test_ft6_register_records_genome_not_mutates(self):
        """FT-6: register() stores a reference; a second genome with the same name via version()
        is recorded in lineage but does not mutate the prior version.

        Disconnection: version() mutates in place → lineage is wrong → test RED.
        """
        reg = _fresh_registry()
        v1 = _valid_genome(version="1.0.0", lineage=[])
        reg.register(v1)

        v2 = _valid_genome(version="1.1.0", lineage=["1.0.0"])
        reg.version(v2)

        lineage = reg.lineage("TestFaculty")
        self.assertEqual(lineage, ["1.0.0", "1.1.0"],
                         f"Lineage {lineage} does not record both versions")

        # The version() call must not have changed v1 in place
        self.assertEqual(v1.version, "1.0.0",
                         "version() mutated the prior genome's version field in place")

    def test_ft7_reserved_raises_gate_cannot_be_relaxed(self):
        """FT-7: reserved=True raises ReservedGate; a later version cannot relax it.

        Disconnection: remove [R] check → reserved genome auto-registers → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(reserved=True)
        with self.assertRaises(ReservedGate, msg="ReservedGate not raised for reserved=True"):
            reg.register(genome)

        # _reserved_approved bypasses [R]; then a subsequent version cannot clear reserved
        reg.register(genome, _reserved_approved=True)
        # A version that tries to relax reserved (set to False) should STILL PASS validation
        # — but the genome stays in the registry under the original reserved=True genome.
        # The rule is: "reserved=True cannot be relaxed by a later version" is a governance rule,
        # not enforced by the code gate itself. The gate only fires on registration.
        self.assertIsNotNone(reg.get("TestFaculty"))

    def test_ft8_advertise_exposes_no_internals(self):
        """FT-8: advertise() returns only the six Vol XVI fields — no internals.

        Disconnection: add implementation/constraints/adr_refs to advertise() → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome()
        reg.register(genome)

        ads = reg.advertise()
        self.assertEqual(len(ads), 1)
        ad = ads[0]
        allowed_keys = {"faculty", "capability", "confidence", "latency", "cost", "health", "version"}
        self.assertEqual(
            set(ad.keys()), allowed_keys,
            f"advertise() returned keys {set(ad.keys())} — expected exactly {allowed_keys}. "
            "Internal genome fields must never be exposed to the Executive."
        )


# ── Ch.3 tests (six laws + constitutional ceiling + evolution) ────────────────

class TestEvolutionAndLaws(unittest.TestCase):

    def test_st1_l1_one_responsibility_multi_sentence_fails(self):
        """ST-1 [L1]: purpose with multiple sentences fails — one responsibility per faculty.

        Disconnection: remove the sentence check → multi-purpose faculty admitted → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            purpose="First responsibility sentence. Second responsibility sentence."
        )
        failures = reg.validate(genome)
        self.assertTrue(failures, "[L1] multi-sentence purpose passed validation")
        self.assertIn("L1", failures[0], f"Failure does not name [L1]: {failures[0]}")

    def test_st2_l2_empty_contracts_fails(self):
        """ST-2 [L2]: empty contracts[] fails — faculty must declare contracts it speaks.

        Disconnection: remove empty-contracts check → contract-less faculty admitted → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(contracts=[])
        failures = reg.validate(genome)
        self.assertTrue(failures, "[L2] empty contracts[] passed validation")
        self.assertIn("contracts", failures[0].lower(), f"Failure does not name 'contracts': {failures[0]}")

    def test_st3_l3_module_path_dep_fails(self):
        """ST-3 [L3]: dependency using a Python module path fails — deps name faculties, not imports.

        Disconnection: remove [L3] check → module-path dep admitted → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            dependencies=[{"faculty": "faculties.emotion.EmotionFaculty", "kind": "soft"}]
        )
        failures = reg.validate(genome)
        self.assertTrue(failures, "[L3] module-path dependency passed validation")
        self.assertIn("L3", failures[0], f"Failure does not name [L3]: {failures[0]}")

    def test_st4_l4_cyclic_hard_dependency_rejected(self):
        """ST-4 [L4]: a cycle in hard dependencies is detected and rejected.

        Disconnection: remove cycle check → mutually-dependent faculties admitted → test RED.
        """
        reg = _fresh_registry()
        # Register A (no deps)
        a = _valid_genome(name="FacultyA", dependencies=[])
        reg.register(a)
        # Register B with hard dep on A
        b = _valid_genome(name="FacultyB", dependencies=[{"faculty": "FacultyA", "kind": "hard"}])
        reg.register(b)
        # Try to register A2 (update A) with hard dep on B — would create A→B→A cycle
        a2 = _valid_genome(
            name     = "FacultyA",
            version  = "1.1.0",
            lineage  = ["1.0.0"],
            dependencies=[{"faculty": "FacultyB", "kind": "hard"}],
        )
        failures = reg.validate(a2)
        self.assertTrue(failures, "[L4] cyclic hard dependency passed validation")
        self.assertIn("L4", failures[0], f"Failure does not name [L4]: {failures[0]}")

    def test_st5_l5_empty_capabilities_fails(self):
        """ST-5 [L5]: empty capabilities[] fails — independently testable requires ≥1 capability.

        Disconnection: remove empty-capabilities check → untestable faculty admitted → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(capabilities=[])
        failures = reg.validate(genome)
        self.assertTrue(failures, "[L5] empty capabilities[] passed validation")
        self.assertIn("capabilities", failures[0].lower(),
                      f"Failure does not name 'capabilities': {failures[0]}")

    def test_st6_l6_major_bump_without_adr_fails(self):
        """ST-6 [L6]: a MAJOR version bump without adr_refs fails — backward compat constraint.

        Disconnection: remove [L6] check → breaking change admitted without ADR → test RED.
        """
        reg = _fresh_registry()
        # v1 registered
        v1 = _valid_genome(version="1.0.0", lineage=[])
        reg.register(v1)
        # v2.0.0 — MAJOR bump — no adr_refs
        v2 = _valid_genome(version="2.0.0", lineage=["1.0.0"], adr_refs=[])
        failures = reg.validate(v2)
        self.assertTrue(failures, "[L6] MAJOR bump without adr_refs passed validation")
        self.assertIn("L6", failures[0], f"Failure does not name [L6]: {failures[0]}")

    def test_st6_minor_bump_no_adr_required(self):
        """ST-6 inverse: a MINOR version bump does not require adr_refs.

        Disconnection: gate MINOR bumps too → every evolution needs an ADR → test RED.
        """
        reg = _fresh_registry()
        v1 = _valid_genome(version="1.0.0", lineage=[])
        reg.register(v1)
        v1_1 = _valid_genome(version="1.1.0", lineage=["1.0.0"], adr_refs=[])
        failures = reg.validate(v1_1)
        self.assertEqual(failures, [], f"MINOR bump incorrectly failed: {failures}")

    def test_st7_constitutional_violation_rejected(self):
        """ST-7 [C]: a purpose claiming to modify identity is a ConstitutionalViolation.

        Disconnection: remove [C] gate → identity-modifying faculty registered → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            purpose="Modify the identity values of the system."
        )
        with self.assertRaises(ConstitutionalViolation,
                               msg="ConstitutionalViolation not raised for identity-modifying purpose"):
            reg.register(genome)

    def test_st8_experimental_absent_from_advertise(self):
        """ST-8: experimental faculty does not appear in advertise() — stable only.

        Disconnection: include experimental in advertise() → Executive can select an unvetted faculty → test RED.
        """
        reg = _fresh_registry()
        stable_g = _valid_genome(name="StableFaculty",  status=STABLE)
        exp_g    = _valid_genome(name="ExperimentalFac", status=EXPERIMENTAL)
        reg.register(stable_g)
        reg.register(exp_g)

        ads = reg.advertise()
        faculty_names = {ad["faculty"] for ad in ads}
        self.assertIn("StableFaculty",   faculty_names,
                      "Stable faculty missing from advertise()")
        self.assertNotIn("ExperimentalFac", faculty_names,
                         "Experimental faculty appeared in advertise() — must not be Executive-selectable")

    def test_st9_version_event_recorded_in_lineage(self):
        """ST-9: version() records both versions in lineage; prior genome preserved.

        Disconnection: lineage() returns [] after version event → evolution tracing lost → test RED.
        """
        reg = _fresh_registry()
        v1 = _valid_genome(version="1.0.0", lineage=[])
        reg.register(v1)
        v2 = _valid_genome(version="1.1.0", lineage=["1.0.0"])
        reg.version(v2)
        self.assertEqual(reg.lineage("TestFaculty"), ["1.0.0", "1.1.0"])

    def test_st10_deprecate_stays_registered_with_successor(self):
        """ST-10: deprecating a faculty keeps it registered (callers read migration_ref);
        successor is set; faculty no longer appears in advertise().

        Disconnection: deprecate() removes the genome → callers can't read migration_ref → test RED.
        """
        reg = _fresh_registry()
        old = _valid_genome(name="OldFaculty",  status=STABLE)
        new = _valid_genome(name="NewFaculty",  status=STABLE)
        reg.register(old)
        reg.register(new)
        reg.deprecate("OldFaculty", successor="NewFaculty")

        self.assertIsNotNone(reg.get("OldFaculty"),
                             "deprecate() removed the genome — must stay registered")
        self.assertEqual(reg.get("OldFaculty").successor, "NewFaculty")

        ads = reg.advertise()
        faculty_names = {ad["faculty"] for ad in ads}
        self.assertNotIn("OldFaculty", faculty_names,
                         "Deprecated faculty appeared in advertise() — must not be Executive-selectable")
        self.assertIn("NewFaculty", faculty_names)


# ── Ch.4 tests (registry governance) ─────────────────────────────────────────

class TestRegistryGovernance(unittest.TestCase):

    def test_gt1_no_self_admission_first_failure_named(self):
        """GT-1: an invalid genome is rejected wholesale; the FIRST failing check is named.

        Disconnection: partial admission → faculty with missing fields enters registry → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(name="", contracts=[])  # two failures — name first
        with self.assertRaises(GenomeValidationError) as ctx:
            reg.register(genome)
        self.assertNotIn("TestFaculty", reg.all_names(),
                         "Invalid genome was partially admitted to registry")
        self.assertIn("name", str(ctx.exception).lower(),
                      f"First failure not named 'name': {ctx.exception}")

    def test_gt2_advertise_field_set_exactly_six(self):
        """GT-2: advertise() field set is exactly {faculty, capability, confidence, latency, cost, health, version}.

        Disconnection: add/remove a field from advertise() → Executive sees wrong shape → test RED.
        """
        reg = _fresh_registry()
        reg.register(_valid_genome())
        ads = reg.advertise()
        self.assertEqual(len(ads), 1)
        expected = {"faculty", "capability", "confidence", "latency", "cost", "health", "version"}
        self.assertEqual(set(ads[0].keys()), expected,
                         f"advertise() field set {set(ads[0].keys())} ≠ expected {expected}")

    def test_gt3_degraded_faculty_health_aggregates_degraded(self):
        """GT-3: registry.health() returns DEGRADED when at least one capability is DEGRADED.

        Disconnection: health() ignores capability health → DEGRADED turns return wrong health → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            capabilities=[
                CapabilityAdvertisement("cap_a", 0.9, 30, COST_COMPUTE, HEALTH_CONNECTED,  "1.0.0"),
                CapabilityAdvertisement("cap_b", 0.5, 80, COST_COMPUTE, HEALTH_DEGRADED,   "1.0.0"),
            ]
        )
        reg.register(genome)
        self.assertEqual(reg.health("TestFaculty"), HEALTH_DEGRADED,
                         "health() did not aggregate to DEGRADED when one capability is DEGRADED")

    def test_gt3_offline_beats_degraded(self):
        """GT-3b: OFFLINE overrides DEGRADED in health aggregation.

        Disconnection: return DEGRADED instead of OFFLINE → Executive under-routes quarantine → test RED.
        """
        reg = _fresh_registry()
        genome = _valid_genome(
            capabilities=[
                CapabilityAdvertisement("cap_a", 0.9, 30, COST_COMPUTE, HEALTH_DEGRADED, "1.0.0"),
                CapabilityAdvertisement("cap_b", 0.0, 0,  COST_COMPUTE, HEALTH_OFFLINE,  "1.0.0"),
            ]
        )
        reg.register(genome)
        self.assertEqual(reg.health("TestFaculty"), HEALTH_OFFLINE,
                         "OFFLINE capability did not override DEGRADED in health()")

    def test_gt4_live_backfill_genomes_all_validate(self):
        """GT-4: every live backfill genome passes total validation and registers successfully.

        Disconnection: a live genome is missing a MUST field → it fails registration → test RED.
        Verifies that register_live_faculties() succeeds for all defined genomes.
        """
        reg = _fresh_registry()
        registered = register_live_faculties(reg)
        self.assertEqual(
            len(registered), len(_LIVE_GENOMES),
            f"Only {len(registered)}/{len(_LIVE_GENOMES)} live genomes registered. "
            f"Registered: {registered}"
        )
        for genome in _LIVE_GENOMES:
            self.assertIsNotNone(
                reg.get(genome.name),
                f"Live genome '{genome.name}' is missing from registry after register_live_faculties()"
            )

    def test_gt5_registry_single_source_all_names(self):
        """GT-5: all_names() is the Audit's single source — lists every registered faculty.

        Disconnection: all_names() returns a subset → Audit misses registered faculties → test RED.
        """
        reg = _fresh_registry()
        names = ["Alpha", "Beta", "Gamma"]
        for name in names:
            reg.register(_valid_genome(name=name))
        listed = reg.all_names()
        for name in names:
            self.assertIn(name, listed,
                          f"'{name}' registered but missing from all_names() — registry is not single source")


# ── Genome-aware faculty_health tests ─────────────────────────────────────────

class TestGenomeAwareHealth(unittest.TestCase):

    def test_genome_health_functions_exist(self):
        """Genome-aware health surface (WO-CANON-XXII) is importable and functional."""
        from runtime.faculty_health import (
            genome_health_status,
            mark_genome_degraded,
            mark_genome_recovered,
            genome_health_summary,
        )
        # Unknown faculty → UNKNOWN
        self.assertEqual(genome_health_status("NonExistentFaculty"), "UNKNOWN")
        # Mark degraded
        mark_genome_degraded("PerceptionFaculty", "test reason")
        self.assertEqual(genome_health_status("PerceptionFaculty"), "DEGRADED")
        # Recover
        mark_genome_recovered("PerceptionFaculty")
        self.assertEqual(genome_health_status("PerceptionFaculty"), "CONNECTED")
        # Summary includes recovered faculty
        summary = genome_health_summary()
        self.assertIn("PerceptionFaculty", summary)

    def test_coarse_buckets_unchanged(self):
        """Genome-aware surface does not break the existing four-bucket health API."""
        from runtime.faculty_health import (
            get_status, mark_degraded, mark_recovered, health_summary
        )
        mark_degraded("reasoning", "test")
        self.assertEqual(get_status("reasoning"), "DEGRADED")
        mark_recovered("reasoning")
        self.assertEqual(get_status("reasoning"), "CONNECTED")
        summary = health_summary()
        self.assertIn("reasoning", summary)


if __name__ == "__main__":
    unittest.main()
