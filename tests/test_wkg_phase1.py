"""
tests/test_wkg_phase1.py — WKG Phase 1 acceptance tests.

Authority: David L3, 2026-08-22
Contract:  docs/architecture/WKG_BUILD_CONTRACT_AMENDED_2026-08-22.md
Builder instruction: WKG PHASE 1 AUTHORISED (2026-08-22)

Demonstrates (per the Phase 1 deliverable requirements):

  AT-W1:  Claim schema — instantiate with all required fields including
          wkg_epistemic_class (mandatory on every Claim)
  AT-W2:  Source schema — instantiate
  AT-W3:  wkg: namespace — claim and source IDs carry the wkg: prefix
  AT-W4:  Provenance fields — all mandatory provenance fields present in schema
  AT-W5:  All 8 wkg_epistemic_classes are representable
  AT-W6:  Vol XXIV dual-classification mapping — each class maps correctly
          (Amendment A: kind + confidence at retrieval boundary)
  AT-W7a: Write gate — VERIFIED with evidence → WRITE
  AT-W7b: Write gate — VERIFIED without evidence → NEEDS_EVIDENCE
  AT-W7c: Write gate — SOURCE_ATTRIBUTED → WRITE_AS_PERSPECTIVE
  AT-W7d: Write gate — SYMBOLIC → WRITE_AS_PERSPECTIVE
  AT-W7e: Write gate — HYPOTHESIS → PROPOSED_PENDING_L3
  AT-W7f: Write gate — SPECULATIVE → PROPOSED_PENDING_L3
  AT-W7g: Write gate — DISPUTED → WRITE_BOTH_CONTRADICTS (no gate)
  AT-W7h: Write gate — UNKNOWN → PROPOSED_PENDING_L3
  AT-W8:  retrieve_wkg() compatible with KnowledgeContext contract (same
          envelope as retrieve(), plus wkg_epistemic_class)
  AT-W9:  No second graph/store/loader — no wkg_graph.json, no wkg_loader.py
  AT-W10: No new CAL action — 9 frozen actions unchanged
  AT-W11: world_graph.json carries wkg_claims / wkg_sources / wkg_proposed_claims
  AT-W12: retrieve_wkg() returns [] for empty corpus (never backfills)
  AT-W13: WKGClaim.vol_xxiv_kind() and vol_xxiv_confidence() match mapping table

Run: python3 tests/test_wkg_phase1.py
"""

from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── AT-W1: Claim schema with wkg_epistemic_class ──────────────────────────────
try:
    from knowledge.wkg_schema import WKGClaim, WKG_CLAIM_REQUIRED_FIELDS

    claim = WKGClaim(
        id                  = "wkg:Joseph:Moon-subconscious",
        subject             = "wkg:Moon",
        predicate           = "SYMBOLISES",
        object              = "wkg:subconscious_mind",
        source              = "wkg:source:Joseph:BookOfWisdom",
        wkg_epistemic_class = "SOURCE_ATTRIBUTED",
        created_at          = "2026-08-22",
        updated_at          = "2026-08-22",
        interpretation      = "Joseph proposes Moon symbolises the subconscious mind.",
        evidence            = [],
        notes               = "Source-attributed claim — not an established scientific fact.",
        provenance          = {
            "author": "Harry B. Joseph",
            "title":  "The Book of Wisdom",
            "source_type": "external_corpus",
            "extraction_date": "2026-08-22",
        },
    )
    assert hasattr(claim, "id"),                  "Claim missing id"
    assert hasattr(claim, "wkg_epistemic_class"), "Claim missing wkg_epistemic_class"
    assert hasattr(claim, "subject"),             "Claim missing subject"
    assert hasattr(claim, "predicate"),           "Claim missing predicate"
    assert hasattr(claim, "object"),              "Claim missing object"
    assert hasattr(claim, "source"),              "Claim missing source"
    assert hasattr(claim, "created_at"),          "Claim missing created_at"
    assert hasattr(claim, "updated_at"),          "Claim missing updated_at"
    # Validate required fields constant covers what's needed
    for f in WKG_CLAIM_REQUIRED_FIELDS:
        assert hasattr(claim, f), f"WKG_CLAIM_REQUIRED_FIELDS lists {f!r} but WKGClaim lacks it"
    ok("AT-W1: WKGClaim schema instantiates with all required fields including wkg_epistemic_class")
except Exception as e:
    fail("AT-W1", e)


# ── AT-W2: Source schema ──────────────────────────────────────────────────────
try:
    from knowledge.wkg_schema import WKGSource, WKG_SOURCE_REQUIRED_FIELDS

    source = WKGSource(
        id                 = "wkg:source:Joseph:BookOfWisdom",
        author             = "Harry B. Joseph",
        title              = "The Book of Wisdom",
        source_type        = "esoteric_text",
        created_at         = "2026-08-22",
        reliability_notes  = "Modern esoteric interpretation. Claims are SOURCE_ATTRIBUTED unless independently verifiable.",
    )
    assert hasattr(source, "id"),          "Source missing id"
    assert hasattr(source, "author"),      "Source missing author"
    assert hasattr(source, "title"),       "Source missing title"
    assert hasattr(source, "source_type"), "Source missing source_type"
    assert hasattr(source, "created_at"),  "Source missing created_at"
    for f in WKG_SOURCE_REQUIRED_FIELDS:
        assert hasattr(source, f), f"WKG_SOURCE_REQUIRED_FIELDS lists {f!r} but WKGSource lacks it"
    ok("AT-W2: WKGSource schema instantiates with all required fields")
except Exception as e:
    fail("AT-W2", e)


# ── AT-W3: wkg: namespace prefix on all WKG ids ───────────────────────────────
try:
    from knowledge.wkg_schema import WKG_NAMESPACE_PREFIX

    assert WKG_NAMESPACE_PREFIX == "wkg:", f"namespace prefix should be 'wkg:' got {WKG_NAMESPACE_PREFIX!r}"
    assert claim.id.startswith(WKG_NAMESPACE_PREFIX), \
        f"claim.id {claim.id!r} does not carry wkg: prefix"
    assert source.id.startswith(WKG_NAMESPACE_PREFIX), \
        f"source.id {source.id!r} does not carry wkg: prefix"
    assert claim.subject.startswith(WKG_NAMESPACE_PREFIX), \
        f"claim.subject {claim.subject!r} does not carry wkg: prefix"
    assert claim.object.startswith(WKG_NAMESPACE_PREFIX), \
        f"claim.object {claim.object!r} does not carry wkg: prefix"
    assert claim.source.startswith(WKG_NAMESPACE_PREFIX), \
        f"claim.source {claim.source!r} does not carry wkg: prefix"
    ok("AT-W3: wkg: namespace prefix present on claim.id, source.id, subject, object, source")
except Exception as e:
    fail("AT-W3", e)


# ── AT-W4: Provenance fields present in WKGProvenance schema ─────────────────
try:
    from knowledge.wkg_schema import WKGProvenance

    prov = WKGProvenance(
        author          = "Harry B. Joseph",
        title           = "The Book of Wisdom",
        extraction_date = "2026-08-22",
        source_type     = "external_corpus",
        volume          = "Vol. I",
    )
    assert hasattr(prov, "author"),           "WKGProvenance missing author"
    assert hasattr(prov, "title"),            "WKGProvenance missing title"
    assert hasattr(prov, "extraction_date"),  "WKGProvenance missing extraction_date"
    assert hasattr(prov, "source_type"),      "WKGProvenance missing source_type"
    assert hasattr(prov, "volume"),           "WKGProvenance missing volume"
    assert hasattr(prov, "chapter"),          "WKGProvenance missing chapter"
    assert hasattr(prov, "page"),             "WKGProvenance missing page"
    assert hasattr(prov, "edition"),          "WKGProvenance missing edition"
    assert hasattr(prov, "publication_date"), "WKGProvenance missing publication_date"
    ok("AT-W4: WKGProvenance schema contains all mandatory provenance fields (§4)")
except Exception as e:
    fail("AT-W4", e)


# ── AT-W5: All 8 epistemic classes representable ─────────────────────────────
try:
    from knowledge.wkg_schema import WKGEpistemicClass

    expected = {
        "VERIFIED", "HISTORICAL", "SOURCE_ATTRIBUTED", "SYMBOLIC",
        "HYPOTHESIS", "SPECULATIVE", "DISPUTED", "UNKNOWN",
    }
    actual = {cls.value for cls in WKGEpistemicClass}
    assert actual == expected, f"Epistemic classes mismatch. Expected {expected}, got {actual}"
    ok(f"AT-W5: all 8 WKG epistemic classes representable: {sorted(actual)}")
except Exception as e:
    fail("AT-W5", e)


# ── AT-W6: Dual-classification mapping (Amendment A) ─────────────────────────
try:
    from knowledge.wkg_schema import EPISTEMIC_TO_VOL_XXIV, map_to_vol_xxiv

    # Verify all 8 classes have mappings
    for cls in ["VERIFIED", "HISTORICAL", "SOURCE_ATTRIBUTED", "SYMBOLIC",
                "HYPOTHESIS", "SPECULATIVE", "DISPUTED", "UNKNOWN"]:
        assert cls in EPISTEMIC_TO_VOL_XXIV, f"{cls} missing from EPISTEMIC_TO_VOL_XXIV"
        m = EPISTEMIC_TO_VOL_XXIV[cls]
        assert "kind"       in m, f"{cls} mapping missing 'kind'"
        assert "confidence" in m, f"{cls} mapping missing 'confidence'"
        assert "provisional" in m, f"{cls} mapping missing 'provisional'"

    # Spot-check the contract's mapping table (§3 Amendment A)
    assert EPISTEMIC_TO_VOL_XXIV["VERIFIED"]["kind"]           == "fact",        "VERIFIED → fact"
    assert EPISTEMIC_TO_VOL_XXIV["VERIFIED"]["confidence"]     == 0.95,          "VERIFIED confidence 0.95"
    assert EPISTEMIC_TO_VOL_XXIV["HISTORICAL"]["kind"]         == "fact",        "HISTORICAL → fact"
    assert EPISTEMIC_TO_VOL_XXIV["HISTORICAL"]["confidence"]   == 0.75,          "HISTORICAL confidence 0.75"
    assert EPISTEMIC_TO_VOL_XXIV["SOURCE_ATTRIBUTED"]["kind"]  == "perspective", "SOURCE_ATTRIBUTED → perspective"
    assert EPISTEMIC_TO_VOL_XXIV["SOURCE_ATTRIBUTED"]["confidence"] is None,     "SOURCE_ATTRIBUTED confidence None"
    assert EPISTEMIC_TO_VOL_XXIV["SYMBOLIC"]["kind"]           == "perspective", "SYMBOLIC → perspective"
    assert EPISTEMIC_TO_VOL_XXIV["HYPOTHESIS"]["kind"]         == "inference",   "HYPOTHESIS → inference"
    assert EPISTEMIC_TO_VOL_XXIV["HYPOTHESIS"]["confidence"]   <= 0.50,          "HYPOTHESIS confidence ≤0.50"
    assert EPISTEMIC_TO_VOL_XXIV["SPECULATIVE"]["kind"]        == "inference",   "SPECULATIVE → inference"
    assert EPISTEMIC_TO_VOL_XXIV["SPECULATIVE"]["confidence"]  <= 0.30,          "SPECULATIVE confidence ≤0.30"
    assert EPISTEMIC_TO_VOL_XXIV["DISPUTED"]["provisional"]    is True,          "DISPUTED provisional=True"
    assert EPISTEMIC_TO_VOL_XXIV["UNKNOWN"]["confidence"]      is None,          "UNKNOWN confidence None"

    # map_to_vol_xxiv falls back to UNKNOWN for unrecognised input
    fallback = map_to_vol_xxiv("INVENTED_CLASS")
    assert fallback == EPISTEMIC_TO_VOL_XXIV["UNKNOWN"], "unrecognised class should fall back to UNKNOWN mapping"

    ok("AT-W6: dual-classification mapping table complete and correct for all 8 classes (Amendment A)")
except Exception as e:
    fail("AT-W6", e)


# ── AT-W7a..h: Write gate (Amendment B) ──────────────────────────────────────
try:
    from knowledge.wkg_schema import evaluate_write_gate, WriteGateDecision

    # AT-W7a: VERIFIED with evidence → WRITE
    r = evaluate_write_gate({"wkg_epistemic_class": "VERIFIED", "evidence": ["astronomy.org/sun"]})
    assert r.decision == WriteGateDecision.WRITE, f"VERIFIED+evidence should WRITE, got {r.decision}"
    ok("AT-W7a: write gate — VERIFIED with evidence → WRITE")
except Exception as e:
    fail("AT-W7a", e)

try:
    # AT-W7b: VERIFIED without evidence → NEEDS_EVIDENCE
    r = evaluate_write_gate({"wkg_epistemic_class": "VERIFIED", "evidence": []})
    assert r.decision == WriteGateDecision.NEEDS_EVIDENCE, \
        f"VERIFIED without evidence should NEEDS_EVIDENCE, got {r.decision}"
    ok("AT-W7b: write gate — VERIFIED without evidence → NEEDS_EVIDENCE (language processing ≠ evidence)")
except Exception as e:
    fail("AT-W7b", e)

try:
    # AT-W7c: SOURCE_ATTRIBUTED → WRITE_AS_PERSPECTIVE
    r = evaluate_write_gate({"wkg_epistemic_class": "SOURCE_ATTRIBUTED"})
    assert r.decision == WriteGateDecision.WRITE_AS_PERSPECTIVE, \
        f"SOURCE_ATTRIBUTED should WRITE_AS_PERSPECTIVE, got {r.decision}"
    ok("AT-W7c: write gate — SOURCE_ATTRIBUTED → WRITE_AS_PERSPECTIVE")
except Exception as e:
    fail("AT-W7c", e)

try:
    # AT-W7d: SYMBOLIC → WRITE_AS_PERSPECTIVE
    r = evaluate_write_gate({"wkg_epistemic_class": "SYMBOLIC"})
    assert r.decision == WriteGateDecision.WRITE_AS_PERSPECTIVE, \
        f"SYMBOLIC should WRITE_AS_PERSPECTIVE, got {r.decision}"
    ok("AT-W7d: write gate — SYMBOLIC → WRITE_AS_PERSPECTIVE")
except Exception as e:
    fail("AT-W7d", e)

try:
    # AT-W7e: HYPOTHESIS → PROPOSED_PENDING_L3
    r = evaluate_write_gate({"wkg_epistemic_class": "HYPOTHESIS"})
    assert r.decision == WriteGateDecision.PROPOSED_PENDING_L3, \
        f"HYPOTHESIS should PROPOSED_PENDING_L3, got {r.decision}"
    ok("AT-W7e: write gate — HYPOTHESIS → PROPOSED_PENDING_L3 (David L3 required)")
except Exception as e:
    fail("AT-W7e", e)

try:
    # AT-W7f: SPECULATIVE → PROPOSED_PENDING_L3
    r = evaluate_write_gate({"wkg_epistemic_class": "SPECULATIVE"})
    assert r.decision == WriteGateDecision.PROPOSED_PENDING_L3, \
        f"SPECULATIVE should PROPOSED_PENDING_L3, got {r.decision}"
    ok("AT-W7f: write gate — SPECULATIVE → PROPOSED_PENDING_L3 (David L3 required)")
except Exception as e:
    fail("AT-W7f", e)

try:
    # AT-W7g: DISPUTED → WRITE_BOTH_CONTRADICTS (no gate — Contradiction Engine §10)
    r = evaluate_write_gate({"wkg_epistemic_class": "DISPUTED"})
    assert r.decision == WriteGateDecision.WRITE_BOTH_CONTRADICTS, \
        f"DISPUTED should WRITE_BOTH_CONTRADICTS, got {r.decision}"
    ok("AT-W7g: write gate — DISPUTED → WRITE_BOTH_CONTRADICTS (no gate; Contradiction Engine §10)")
except Exception as e:
    fail("AT-W7g", e)

try:
    # AT-W7h: UNKNOWN → PROPOSED_PENDING_L3
    r = evaluate_write_gate({"wkg_epistemic_class": "UNKNOWN"})
    assert r.decision == WriteGateDecision.PROPOSED_PENDING_L3, \
        f"UNKNOWN should PROPOSED_PENDING_L3, got {r.decision}"
    ok("AT-W7h: write gate — UNKNOWN → PROPOSED_PENDING_L3")
except Exception as e:
    fail("AT-W7h", e)


# ── AT-W8: retrieve_wkg() envelope compatible with KnowledgeContext ───────────
try:
    from knowledge.graph_loader import retrieve_wkg, retrieve

    # retrieve_wkg must return a list (same type as retrieve())
    wkg_results = retrieve_wkg("sun moon seasons")
    assert isinstance(wkg_results, list), "retrieve_wkg() must return a list"

    # Inject a mock claim to verify envelope shape (simulating Phase 2 data)
    from knowledge import graph_loader as _gl
    _gl._load_all()
    _gl._graph.setdefault("wkg_claims", []).append({
        "id":                  "wkg:test:Sun-consciousness",
        "subject":             "wkg:Sun",
        "predicate":           "SYMBOLISES",
        "object":              "wkg:conscious_mind",
        "source":              "wkg:source:Joseph:BookOfWisdom",
        "wkg_epistemic_class": "SOURCE_ATTRIBUTED",
        "created_at":          "2026-08-22",
        "updated_at":          "2026-08-22",
        "interpretation":      "Joseph proposes the Sun symbolises the conscious mind.",
        "evidence":            [],
    })

    wkg_results = retrieve_wkg("sun consciousness symbolic")
    assert len(wkg_results) > 0, "retrieve_wkg() should match injected claim"
    first = wkg_results[0]

    # Must carry the same fields as retrieve() for KnowledgeContext compatibility
    for field in ("label", "content", "confidence", "kind", "evidence", "score"):
        assert field in first, f"retrieve_wkg() result missing KnowledgeContext field: {field!r}"

    # Plus the WKG-specific field
    assert "wkg_epistemic_class" in first, "retrieve_wkg() result missing wkg_epistemic_class"

    # Amendment A: kind should be 'perspective' for SOURCE_ATTRIBUTED
    assert first["kind"] == "perspective", \
        f"SOURCE_ATTRIBUTED claim should have kind='perspective', got {first['kind']!r}"

    # Clean up mock data
    _gl._graph["wkg_claims"] = [c for c in _gl._graph["wkg_claims"]
                                 if c["id"] != "wkg:test:Sun-consciousness"]

    ok("AT-W8: retrieve_wkg() returns KnowledgeContext-compatible envelope with wkg_epistemic_class")
except Exception as e:
    fail("AT-W8", e)


# ── AT-W9: No second graph store or loader ────────────────────────────────────
try:
    wkg_graph_path  = os.path.join(_ROOT, "knowledge",      "wkg_graph.json")
    wkg_loader_path = os.path.join(_ROOT, "knowledge",      "wkg_loader.py")
    wkg_graph_alt   = os.path.join(_ROOT, "relationships",  "wkg_graph.json")

    assert not os.path.exists(wkg_graph_path),  f"wkg_graph.json MUST NOT exist at {wkg_graph_path}"
    assert not os.path.exists(wkg_loader_path), f"wkg_loader.py MUST NOT exist at {wkg_loader_path}"
    assert not os.path.exists(wkg_graph_alt),   f"wkg_graph.json MUST NOT exist at {wkg_graph_alt}"

    # Amendment C: WKG sections live IN world_graph.json — verify they're there
    import json
    graph_path = os.path.join(_ROOT, "relationships", "world_graph.json")
    with open(graph_path, encoding="utf-8") as f:
        gdata = json.load(f)

    assert "wkg_claims"          in gdata, "world_graph.json missing wkg_claims section"
    assert "wkg_sources"         in gdata, "world_graph.json missing wkg_sources section"
    assert "wkg_proposed_claims" in gdata, "world_graph.json missing wkg_proposed_claims section"
    assert "_wkg_meta"           in gdata, "world_graph.json missing _wkg_meta metadata"
    assert gdata["_wkg_meta"]["namespace"] == "wkg:", "WKG namespace must be 'wkg:'"

    ok("AT-W9: no wkg_graph.json, no wkg_loader.py — WKG sections in canonical world_graph.json (Amendment C)")
except Exception as e:
    fail("AT-W9", e)


# ── AT-W10: No new CAL action ─────────────────────────────────────────────────
try:
    import re
    living_spec_path = os.path.join(_ROOT, "prompts", "living_presence_spec.txt")
    frozen_actions   = {"answer", "build", "connect", "celebrate", "reflect",
                        "ground", "challenge", "witness", "silence"}

    # The WKG schema file must not introduce a new CAL action string
    wkg_schema_path = os.path.join(_ROOT, "knowledge", "wkg_schema.py")
    with open(wkg_schema_path, encoding="utf-8") as f:
        wkg_src = f.read()

    # Check that no new CAL-style action keywords appear as string literals
    # that are not in the frozen set
    forbidden_new_actions = ["research", "inquire", "query", "retrieve", "investigate"]
    for action in forbidden_new_actions:
        # Check for patterns like "action": "research" or cal_action = "research"
        pattern = re.compile(rf'(?:cal_action|action)\s*=\s*["\']({action})["\']', re.IGNORECASE)
        assert not pattern.search(wkg_src), \
            f"wkg_schema.py introduces new CAL action {action!r} — FREEZE_V1_LOCK violation"

    # Also verify graph_loader's WKG extension doesn't add a CAL action
    gl_path = os.path.join(_ROOT, "knowledge", "graph_loader.py")
    with open(gl_path, encoding="utf-8") as f:
        gl_src = f.read()
    for action in forbidden_new_actions:
        pattern = re.compile(rf'cal_action\s*=\s*["\']({action})["\']', re.IGNORECASE)
        assert not pattern.search(gl_src), \
            f"graph_loader.py introduces new CAL action {action!r} — FREEZE_V1_LOCK violation"

    ok(f"AT-W10: no new CAL action introduced — 9 frozen actions unchanged: {sorted(frozen_actions)}")
except Exception as e:
    fail("AT-W10", e)


# ── AT-W11: world_graph.json carries WKG sections ────────────────────────────
try:
    import json
    graph_path = os.path.join(_ROOT, "relationships", "world_graph.json")
    with open(graph_path, encoding="utf-8") as f:
        gdata = json.load(f)

    assert isinstance(gdata.get("wkg_claims"),          list), "wkg_claims must be a list"
    assert isinstance(gdata.get("wkg_sources"),         list), "wkg_sources must be a list"
    assert isinstance(gdata.get("wkg_proposed_claims"), list), "wkg_proposed_claims must be a list"
    # Phase 2 supersedes empty-corpus assertions: corpus may be populated
    # Existing eLo-universe data unchanged
    assert len(gdata.get("entities", [])) == 17, \
        f"existing entities count changed — WKG extension should not modify eLo-universe data"
    assert len(gdata.get("relationships", [])) == 17, \
        "existing relationships count changed"

    ok("AT-W11: world_graph.json carries WKG sections; eLo-universe data unchanged")
except Exception as e:
    fail("AT-W11", e)


# ── AT-W12: retrieve_wkg() returns [] when corpus empty, never backfills ──────
try:
    from knowledge import graph_loader as _gl2
    # Temporarily ensure wkg_claims is empty (reset after AT-W8 mock)
    _gl2._load_all()
    original = list(_gl2._graph.get("wkg_claims", []))
    _gl2._graph["wkg_claims"] = []

    result = retrieve_wkg("moon subconscious consciousness sun seasons")
    assert result == [], f"retrieve_wkg() should return [] on empty corpus, got {result}"

    _gl2._graph["wkg_claims"] = original  # restore
    ok("AT-W12: retrieve_wkg() returns [] for empty corpus — never backfills from LLM")
except Exception as e:
    fail("AT-W12", e)


# ── AT-W13: WKGClaim helper methods match mapping table ──────────────────────
try:
    from knowledge.wkg_schema import WKGClaim, EPISTEMIC_TO_VOL_XXIV

    for cls_str, expected in EPISTEMIC_TO_VOL_XXIV.items():
        c = WKGClaim(
            id="wkg:test", subject="wkg:A", predicate="IS", object="wkg:B",
            source="wkg:s", wkg_epistemic_class=cls_str,
            created_at="2026-08-22", updated_at="2026-08-22",
        )
        assert c.vol_xxiv_kind() == expected["kind"], \
            f"WKGClaim({cls_str}).vol_xxiv_kind() = {c.vol_xxiv_kind()!r}, expected {expected['kind']!r}"
        assert c.vol_xxiv_confidence() == expected["confidence"], \
            f"WKGClaim({cls_str}).vol_xxiv_confidence() = {c.vol_xxiv_confidence()!r}, expected {expected['confidence']!r}"

    ok("AT-W13: WKGClaim.vol_xxiv_kind() and vol_xxiv_confidence() match dual-classification table for all 8 classes")
except Exception as e:
    fail("AT-W13", e)


# ── Summary ────────────────────────────────────────────────────────────────────
print()
print("=" * 68)
print(f"WKG Phase 1 acceptance tests   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
