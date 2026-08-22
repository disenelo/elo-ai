"""
WKG Phase 2 acceptance tests — all 8 §18 contract acceptance criteria.

Authority: David L3, 2026-08-22
Contract:  docs/architecture/WKG_BUILD_CONTRACT_AMENDED_2026-08-22.md
Phase 2:   corpus ingestion, contradiction handling, provenance integrity,
           write-gate enforcement, complete acceptance evidence.
"""

import pytest
import knowledge.graph_loader as _gl
from knowledge.wkg_schema import (
    evaluate_write_gate,
    WriteGateDecision,
    WKG_CLAIM_REQUIRED_FIELDS,
    WKG_SOURCE_REQUIRED_FIELDS,
)

# Force a fresh load from the Phase 2-populated world_graph.json
_gl._graph = {}
_gl._load_all()


# ── helpers ────────────────────────────────────────────────────────────────────

def _claims():
    return _gl._graph.get("wkg_claims", [])

def _sources():
    return _gl._graph.get("wkg_sources", [])

def _entities():
    return _gl._graph.get("wkg_entities", [])

def _claim_rels():
    return _gl._graph.get("wkg_claim_relationships", [])

def _find(claim_id):
    return next((c for c in _claims() if c["id"] == claim_id), None)


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 1 — Joseph Moon claim: SOURCE_ATTRIBUTED, not VERIFIED
# ─────────────────────────────────────────────────────────────────────────────

class TestATP21JosephMoonSourceAttributed:
    def test_claim_exists(self):
        assert _find("wkg:claim:joseph_moon_subconscious") is not None

    def test_epistemic_class_is_source_attributed(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert c["wkg_epistemic_class"] == "SOURCE_ATTRIBUTED"

    def test_epistemic_class_is_not_verified(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert c["wkg_epistemic_class"] != "VERIFIED"

    def test_write_gate_returns_perspective(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE_AS_PERSPECTIVE

    def test_source_is_joseph(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert c["source"] == "wkg:source:joseph_book_of_wisdom"

    def test_provenance_has_joseph_author(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert (c.get("provenance") or {}).get("author") == "Harry B. Joseph"


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 2 — Moon-subconscious is symbolic, not causal
# ─────────────────────────────────────────────────────────────────────────────

class TestATP22SymbolicNotCausal:
    def test_joseph_claim_is_source_attributed_not_causal(self):
        c = _find("wkg:claim:joseph_moon_subconscious")
        assert c["wkg_epistemic_class"] == "SOURCE_ATTRIBUTED"

    def test_causal_distinction_claim_exists(self):
        assert _find("wkg:claim:moon_subconscious_symbolic_not_causal") is not None

    def test_causal_distinction_is_verified(self):
        c = _find("wkg:claim:moon_subconscious_symbolic_not_causal")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_causal_distinction_interpretation_mentions_symbolic(self):
        c = _find("wkg:claim:moon_subconscious_symbolic_not_causal")
        assert "symbolic" in (c.get("interpretation") or "").lower()

    def test_causal_distinction_interpretation_mentions_causal(self):
        c = _find("wkg:claim:moon_subconscious_symbolic_not_causal")
        assert "causal" in (c.get("interpretation") or "").lower()

    def test_causal_distinction_has_evidence(self):
        c = _find("wkg:claim:moon_subconscious_symbolic_not_causal")
        assert c.get("evidence")


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 3 — 13 × 28 = 364 is VERIFIED mathematical
# ─────────────────────────────────────────────────────────────────────────────

class TestATP23MathVerified:
    def test_13x28_claim_exists(self):
        assert _find("wkg:claim:math_13_times_28_equals_364") is not None

    def test_13x28_is_verified(self):
        c = _find("wkg:claim:math_13_times_28_equals_364")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_13x28_has_evidence(self):
        c = _find("wkg:claim:math_13_times_28_equals_364")
        assert c.get("evidence")

    def test_13x28_write_gate_returns_write(self):
        c = _find("wkg:claim:math_13_times_28_equals_364")
        assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE

    def test_364_plus_1_claim_exists_and_verified(self):
        c = _find("wkg:claim:math_364_plus_1_equals_365")
        assert c is not None
        assert c["wkg_epistemic_class"] == "VERIFIED"


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 4 — 28 days ≠ exact lunar month
# ─────────────────────────────────────────────────────────────────────────────

class TestATP24LunarMonthDistinction:
    def test_synodic_29_53_claim_exists(self):
        assert _find("wkg:claim:synodic_lunar_month_29_53_days") is not None

    def test_synodic_29_53_is_verified(self):
        c = _find("wkg:claim:synodic_lunar_month_29_53_days")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_synodic_29_53_interpretation_contains_value(self):
        c = _find("wkg:claim:synodic_lunar_month_29_53_days")
        assert "29.53" in (c.get("interpretation") or "")

    def test_28_not_lunar_month_claim_exists(self):
        assert _find("wkg:claim:28_days_not_exact_lunar_month") is not None

    def test_28_not_lunar_month_is_verified(self):
        c = _find("wkg:claim:28_days_not_exact_lunar_month")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_joseph_28day_claim_is_source_attributed_not_verified(self):
        c = _find("wkg:claim:joseph_28day_lunar_rhythm")
        assert c is not None
        assert c["wkg_epistemic_class"] == "SOURCE_ATTRIBUTED"
        assert c["wkg_epistemic_class"] != "VERIFIED"


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 5 — What causes seasons → Earth's axial tilt
# ─────────────────────────────────────────────────────────────────────────────

class TestATP25AxialTiltCausesSeasons:
    def test_axial_tilt_claim_exists(self):
        assert _find("wkg:claim:axial_tilt_causes_seasons") is not None

    def test_axial_tilt_is_verified(self):
        c = _find("wkg:claim:axial_tilt_causes_seasons")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_axial_tilt_interpretation_mentions_tilt(self):
        c = _find("wkg:claim:axial_tilt_causes_seasons")
        interp = (c.get("interpretation") or "").lower()
        assert "tilt" in interp or "axial" in interp

    def test_axial_tilt_has_evidence(self):
        c = _find("wkg:claim:axial_tilt_causes_seasons")
        assert c.get("evidence")

    def test_axial_tilt_write_gate_returns_write(self):
        c = _find("wkg:claim:axial_tilt_causes_seasons")
        assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 6 — Joseph season claims are SOURCE_ATTRIBUTED
# ─────────────────────────────────────────────────────────────────────────────

_SEASON_CLAIMS = [
    "wkg:claim:joseph_winter_reflection",
    "wkg:claim:joseph_spring_emergence",
    "wkg:claim:joseph_summer_action",
    "wkg:claim:joseph_autumn_release",
]

class TestATP26JosephSeasonsSourceAttributed:
    @pytest.mark.parametrize("claim_id", _SEASON_CLAIMS)
    def test_claim_exists(self, claim_id):
        assert _find(claim_id) is not None, f"{claim_id} not found"

    @pytest.mark.parametrize("claim_id", _SEASON_CLAIMS)
    def test_is_source_attributed(self, claim_id):
        c = _find(claim_id)
        assert c["wkg_epistemic_class"] == "SOURCE_ATTRIBUTED"

    @pytest.mark.parametrize("claim_id", _SEASON_CLAIMS)
    def test_source_is_joseph(self, claim_id):
        c = _find(claim_id)
        assert c["source"] == "wkg:source:joseph_book_of_wisdom"

    @pytest.mark.parametrize("claim_id", _SEASON_CLAIMS)
    def test_write_gate_returns_perspective(self, claim_id):
        c = _find(claim_id)
        assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE_AS_PERSPECTIVE


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 7 — 12 disciples / 12 cranial nerves: SYMBOLIC, not anatomical
# ─────────────────────────────────────────────────────────────────────────────

class TestATP27TwelveCorrespondence:
    def test_symbolic_claim_exists(self):
        assert _find("wkg:claim:joseph_12disciples_cranial_correspondence") is not None

    def test_symbolic_claim_is_symbolic_not_verified(self):
        c = _find("wkg:claim:joseph_12disciples_cranial_correspondence")
        assert c["wkg_epistemic_class"] == "SYMBOLIC"
        assert c["wkg_epistemic_class"] != "VERIFIED"
        assert c["wkg_epistemic_class"] != "HISTORICAL"

    def test_symbolic_interpretation_says_symbolic(self):
        c = _find("wkg:claim:joseph_12disciples_cranial_correspondence")
        assert "symbolic" in (c.get("interpretation") or "").lower()

    def test_symbolic_write_gate_returns_perspective(self):
        c = _find("wkg:claim:joseph_12disciples_cranial_correspondence")
        assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE_AS_PERSPECTIVE

    def test_verified_anatomy_claim_exists_separately(self):
        c = _find("wkg:claim:anatomy_12_cranial_nerve_pairs")
        assert c is not None
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_verified_anatomy_has_anatomy_source(self):
        c = _find("wkg:claim:anatomy_12_cranial_nerve_pairs")
        assert c["source"] == "wkg:source:anatomy_consensus"

    def test_symbolic_and_verified_have_different_epistemic_classes(self):
        symbolic = _find("wkg:claim:joseph_12disciples_cranial_correspondence")
        verified = _find("wkg:claim:anatomy_12_cranial_nerve_pairs")
        assert symbolic["wkg_epistemic_class"] != verified["wkg_epistemic_class"]


# ─────────────────────────────────────────────────────────────────────────────
# §18 Test 8 — No syncretic collapse
# ─────────────────────────────────────────────────────────────────────────────

_TWELVE_CLAIM_IDS = {
    "wkg:claim:joseph_12disciples_cranial_correspondence",
    "wkg:claim:zodiac_12_signs_historical_tradition",
    "wkg:claim:anatomy_12_cranial_nerve_pairs",
}

class TestATP28NoSyncreticCollapse:
    def test_disciples_has_joseph_source(self):
        c = _find("wkg:claim:joseph_12disciples_cranial_correspondence")
        assert c["source"] == "wkg:source:joseph_book_of_wisdom"

    def test_zodiac_has_historical_epistemic_class(self):
        c = _find("wkg:claim:zodiac_12_signs_historical_tradition")
        assert c is not None
        assert c["wkg_epistemic_class"] == "HISTORICAL"

    def test_cranial_has_anatomy_source(self):
        c = _find("wkg:claim:anatomy_12_cranial_nerve_pairs")
        assert c["source"] == "wkg:source:anatomy_consensus"

    def test_no_derived_from_between_twelve_systems(self):
        for r in _claim_rels():
            if r.get("from") in _TWELVE_CLAIM_IDS and r.get("to") in _TWELVE_CLAIM_IDS:
                assert r.get("type") != "DERIVED_FROM", (
                    f"Syncretic collapse: DERIVED_FROM between {r['from']} and {r['to']}"
                )

    def test_no_common_origin_claim_exists(self):
        c = _find("wkg:claim:twelve_no_established_common_origin")
        assert c is not None

    def test_no_common_origin_is_verified(self):
        c = _find("wkg:claim:twelve_no_established_common_origin")
        assert c["wkg_epistemic_class"] == "VERIFIED"

    def test_three_twelve_claims_each_have_distinct_sources(self):
        sources = {
            _find("wkg:claim:joseph_12disciples_cranial_correspondence")["source"],
            _find("wkg:claim:zodiac_12_signs_historical_tradition")["source"],
            _find("wkg:claim:anatomy_12_cranial_nerve_pairs")["source"],
        }
        assert len(sources) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Contradiction Engine (§10)
# ─────────────────────────────────────────────────────────────────────────────

class TestATP2ContradictionEngine:
    def test_seasonal_contradicts_relationship_exists(self):
        contradicts = _gl.get_wkg_claim_relationships(rel_type="CONTRADICTS")
        pairs = [(r["from"], r["to"]) for r in contradicts]
        assert ("wkg:claim:joseph_seasonal_mechanism", "wkg:claim:axial_tilt_causes_seasons") in pairs

    def test_lunar_rhythm_contradicts_relationship_exists(self):
        contradicts = _gl.get_wkg_claim_relationships(rel_type="CONTRADICTS")
        pairs = [(r["from"], r["to"]) for r in contradicts]
        assert ("wkg:claim:joseph_28day_lunar_rhythm", "wkg:claim:28_days_not_exact_lunar_month") in pairs

    def test_both_claims_in_each_contradicts_pair_exist(self):
        claim_ids = {c["id"] for c in _claims()}
        for cid in [
            "wkg:claim:joseph_seasonal_mechanism",
            "wkg:claim:axial_tilt_causes_seasons",
            "wkg:claim:joseph_28day_lunar_rhythm",
            "wkg:claim:28_days_not_exact_lunar_month",
        ]:
            assert cid in claim_ids, f"{cid} missing from wkg_claims"

    def test_get_wkg_claim_relationships_returns_all(self):
        rels = _gl.get_wkg_claim_relationships()
        assert len(rels) >= 2

    def test_get_wkg_claim_relationships_filter_contradicts(self):
        contradicts = _gl.get_wkg_claim_relationships(rel_type="CONTRADICTS")
        assert len(contradicts) == 2
        assert all(r["type"] == "CONTRADICTS" for r in contradicts)

    def test_get_wkg_claim_relationships_filter_analogous(self):
        analogous = _gl.get_wkg_claim_relationships(rel_type="ANALOGOUS_TO")
        assert len(analogous) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Provenance integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestATP2ProvenanceIntegrity:
    def test_all_claims_have_wkg_prefix(self):
        for c in _claims():
            assert c["id"].startswith("wkg:"), f"Missing wkg: prefix: {c['id']}"

    def test_all_claims_have_required_fields(self):
        for c in _claims():
            missing = WKG_CLAIM_REQUIRED_FIELDS - set(c.keys())
            assert not missing, f"{c['id']} missing fields: {missing}"

    def test_all_sources_have_wkg_prefix(self):
        for s in _sources():
            assert s["id"].startswith("wkg:"), f"Missing wkg: prefix: {s['id']}"

    def test_all_sources_have_required_fields(self):
        for s in _sources():
            missing = WKG_SOURCE_REQUIRED_FIELDS - set(s.keys())
            assert not missing, f"{s['id']} missing fields: {missing}"

    def test_all_claim_sources_point_to_known_source(self):
        source_ids = {s["id"] for s in _sources()}
        for c in _claims():
            assert c["source"] in source_ids, (
                f"{c['id']} references unknown source {c['source']!r}"
            )

    def test_verified_claims_have_evidence(self):
        for c in _claims():
            if c["wkg_epistemic_class"] == "VERIFIED":
                assert c.get("evidence"), f"VERIFIED claim {c['id']} has no evidence"

    def test_no_proposed_claims_in_corpus(self):
        assert _gl._graph.get("wkg_proposed_claims", []) == []


# ─────────────────────────────────────────────────────────────────────────────
# Write-gate enforcement
# ─────────────────────────────────────────────────────────────────────────────

class TestATP2WriteGate:
    def test_all_source_attributed_write_as_perspective(self):
        for c in _claims():
            if c["wkg_epistemic_class"] == "SOURCE_ATTRIBUTED":
                assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE_AS_PERSPECTIVE

    def test_all_symbolic_write_as_perspective(self):
        for c in _claims():
            if c["wkg_epistemic_class"] == "SYMBOLIC":
                assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE_AS_PERSPECTIVE

    def test_all_verified_with_evidence_return_write(self):
        for c in _claims():
            if c["wkg_epistemic_class"] == "VERIFIED" and c.get("evidence"):
                assert evaluate_write_gate(c).decision == WriteGateDecision.WRITE

    def test_no_hypothesis_speculative_in_main_claims(self):
        blocked = {"HYPOTHESIS", "SPECULATIVE"}
        for c in _claims():
            assert c["wkg_epistemic_class"] not in blocked, (
                f"{c['id']} is {c['wkg_epistemic_class']} — must be in proposed_claims"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval integration
# ─────────────────────────────────────────────────────────────────────────────

class TestATP2Retrieval:
    def test_retrieve_wkg_returns_results_for_moon(self):
        from knowledge.graph_loader import retrieve_wkg
        results = retrieve_wkg("moon subconscious")
        assert len(results) > 0

    def test_retrieve_wkg_results_carry_wkg_epistemic_class(self):
        from knowledge.graph_loader import retrieve_wkg
        results = retrieve_wkg("moon subconscious")
        for r in results:
            assert "wkg_epistemic_class" in r

    def test_retrieve_wkg_results_carry_kind_and_confidence(self):
        from knowledge.graph_loader import retrieve_wkg
        results = retrieve_wkg("moon subconscious")
        for r in results:
            assert "kind" in r
            assert "confidence" in r

    def test_wkg_entities_loaded(self):
        assert len(_entities()) >= 10

    def test_elo_universe_entity_count_unchanged(self):
        """AT-W11 regression: eLo-universe entities[] still exactly 17."""
        elo = [e for e in _gl._graph.get("entities", []) if not e.get("id", "").startswith("wkg:")]
        assert len(elo) == 17

    def test_wkg_entities_not_in_entities_array(self):
        """WKG entities live in wkg_entities[], not entities[] — AT-W11 isolation."""
        entity_ids = {e["id"] for e in _gl._graph.get("entities", [])}
        wkg_entity_ids = {e["id"] for e in _entities()}
        assert entity_ids.isdisjoint(wkg_entity_ids)

    def test_relationship_count_unchanged(self):
        """AT-W11 regression: eLo-universe relationships[] still exactly 17."""
        assert len(_gl._graph.get("relationships", [])) == 17
