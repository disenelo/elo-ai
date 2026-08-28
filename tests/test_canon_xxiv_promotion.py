"""
tests/test_canon_xxiv_promotion.py — WO-CANON-XXIV §A/§B/§D
Knowledge graph promotion threshold, demotion/retraction path, and epistemic kind fix.

PT-1: strength>=0.70 + 3 verified refs (2 sessions) → promoted_memory node written
PT-2: 3 refs but all text-only (verified=False) → never promotes
PT-3: promotion_pass not importable from server.py or spine.run() response path
PT-4: world-state-derived claim (about_world=False) never promotes directly
DT-1: 3 consecutive contradictions → demote promoted_memory to contested
DT-2: retracted node excluded from retrieve()
DT-3: david_correction() → immediate retraction with reason="david_correction: ..."
DT-4: retracted node kept with retracted_at + reason + original evidence
DT-5: Consolidation cannot demote authored fact node (epistemic_kind="fact")
DT-6: re-promotion from retracted requires fresh verified episode + re-earns §A bar
AG-1: numeric constants agree with LEARNING_LOOP_v1.md §3.4
KT-1: epistemic_kind distinct from type; fact/pm with empty evidence rejected
KT-2: referential integrity — dangling from/to detected
KT-3: empty retrieval returns "" (build_context); never backfills from LLM
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.consolidation_faculty import (
    promotion_pass,
    demotion_pass,
    david_correction,
    _KG_STRENGTH_MIN,
    _KG_REFS_MIN,
    _KG_SESSIONS_MIN,
    _KG_VERIFIED_MIN,
    _KG_CONFIDENCE_WEAKEN,
    _KG_DEMOTE_THRESHOLD,
    _KG_RETRACT_THRESHOLD,
    _KG_RETRACT_CONSECUTIVE,
    _KG_RETRACT_IDLE_DAYS,
)
from knowledge.graph_loader import (
    retrieve,
    build_context,
    validate_graph_write,
    check_referential_integrity,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _empty_graph_path(tmp_path) -> str:
    p = str(tmp_path / "world_graph.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"entities": [], "relationships": []}, f)
    return p


def _graph_with(tmp_path, entities, relationships=None) -> str:
    p = str(tmp_path / "world_graph.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({
            "entities": entities,
            "relationships": relationships or [],
        }, f)
    return p


def _load_graph(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _good_refs(n_refs=3, n_sessions=2, n_verified=2):
    """Build a list of n_refs episode refs spanning n_sessions, n_verified verified."""
    refs = []
    for i in range(n_refs):
        refs.append({
            "ref":     f"SPOT_{i:04d}",
            "session": f"sess_{i % n_sessions}",
            "verified": i < n_verified,
        })
    return refs


# ── PT-1 ─────────────────────────────────────────────────────────────────────

def test_pt1_promotion_threshold_met(tmp_path):
    """strength>=0.70 + 3 refs (2 sessions, 2 verified) → promoted_memory node written."""
    gpath = _empty_graph_path(tmp_path)

    record = {
        "id":           "pm_test_001",
        "fact":         "eLo loves music",
        "strength":     0.75,
        "episode_refs": _good_refs(),
        "about_world":  True,
    }
    result = promotion_pass([record], graph_path=gpath)

    assert result["errors"] == [], f"unexpected errors: {result['errors']}"
    assert "pm_test_001" in result["promoted"], f"node not promoted: {result}"

    graph = _load_graph(gpath)
    node = next((e for e in graph["entities"] if e["id"] == "pm_test_001"), None)
    assert node is not None, "promoted node not in graph"
    assert node["status"] == "promoted_memory", f"wrong status: {node['status']}"
    assert node["epistemic_kind"] == "promoted_memory"
    assert len(node["evidence"]) >= 3, "evidence must point at SPOT codes"


# ── PT-2 ─────────────────────────────────────────────────────────────────────

def test_pt2_text_only_episodes_never_promote(tmp_path):
    """All text-only (verified=False) episodes → never promotes (counts toward nothing)."""
    gpath = _empty_graph_path(tmp_path)

    refs = [
        {"ref": f"SPOT_{i:04d}", "session": f"sess_{i % 2}", "verified": False}
        for i in range(4)
    ]
    record = {
        "id":           "pm_text_only",
        "fact":         "some unverified claim",
        "strength":     0.80,
        "episode_refs": refs,
        "about_world":  True,
    }
    result = promotion_pass([record], graph_path=gpath)

    assert "pm_text_only" not in result["promoted"], "text-only episodes must not promote"
    assert result["skipped"] >= 1


# ── PT-3 ─────────────────────────────────────────────────────────────────────

def test_pt3_promotion_not_in_response_path():
    """
    promotion_pass is defined only in memory.consolidation_faculty (timed path).
    server.py and spine must not directly call it in the response path.
    Verified by asserting neither file imports promotion_pass by name.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for fname in ("server.py", os.path.join("runtime", "spine.py")):
        fpath = os.path.join(root, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        assert "promotion_pass" not in text, (
            f"{fname} must NOT call promotion_pass (response-path guard)"
        )
        assert "demotion_pass" not in text, (
            f"{fname} must NOT call demotion_pass (response-path guard)"
        )


# ── PT-4 ─────────────────────────────────────────────────────────────────────

def test_pt4_world_state_derived_claim_does_not_promote(tmp_path):
    """about_world=False → never promotes (World State must travel through Memory first)."""
    gpath = _empty_graph_path(tmp_path)

    record = {
        "id":           "pm_ws_derived",
        "fact":         "active window is browser",
        "strength":     0.90,
        "episode_refs": _good_refs(),
        "about_world":  False,
    }
    result = promotion_pass([record], graph_path=gpath)

    assert "pm_ws_derived" not in result["promoted"]
    assert result["skipped"] >= 1


# ── DT-1 ─────────────────────────────────────────────────────────────────────

def test_dt1_contradictions_demote_to_contested(tmp_path):
    """3 consecutive contradictions → promoted_memory demoted to contested."""
    node = {
        "id":              "pm_node_dt1",
        "name":            "some fact",
        "type":            "promoted_fact",
        "epistemic_kind":  "promoted_memory",
        "description":     "some fact",
        "keywords":        [],
        "confidence":      0.70,
        "evidence":        [{"episode_ref": "SPOT_0001", "verified": True}],
        "status":          "promoted_memory",
        "contradicting_count": 3,
    }
    gpath = _graph_with(tmp_path, [node])

    result = demotion_pass(graph_path=gpath)

    assert result["errors"] == [], f"unexpected errors: {result['errors']}"
    graph = _load_graph(gpath)
    updated = next(e for e in graph["entities"] if e["id"] == "pm_node_dt1")
    assert updated["status"] in ("retracted", "contested"), (
        f"expected demoted/retracted, got {updated['status']!r}"
    )
    assert "pm_node_dt1" in result["demoted"] or "pm_node_dt1" in result["retracted"]


# ── DT-2 ─────────────────────────────────────────────────────────────────────

def test_dt2_retracted_excluded_from_retrieve(tmp_path, monkeypatch):
    """A retracted node is excluded from retrieve() — retraction is behaviourally real."""
    import knowledge.graph_loader as gl

    retracted_entity = {
        "id":            "pm_retracted",
        "name":          "retracted fact",
        "type":          "promoted_fact",
        "epistemic_kind": "retracted",
        "description":   "This claim was retracted",
        "keywords":      ["retracted", "fact", "claim", "knowledge"],
        "confidence":    0.1,
        "evidence":      [{"episode_ref": "SPOT_0001", "verified": True}],
        "status":        "retracted",
    }

    # Monkeypatch graph loader to serve this retracted entity
    original_graph = gl._graph.copy()
    original_graph_entities = list(gl._graph.get("entities", []))
    gl._graph = {"entities": [retracted_entity], "relationships": []}

    try:
        results = retrieve("retracted fact claim knowledge")
        assert all(r.get("status") != "retracted" for r in results), (
            "retracted node must not appear in retrieve() results"
        )
    finally:
        gl._graph = {"entities": original_graph_entities, "relationships": []}


# ── DT-3 ─────────────────────────────────────────────────────────────────────

def test_dt3_david_correction_immediate_retraction(tmp_path):
    """david_correction() retracts the node in the same turn with reason=david_correction."""
    node = {
        "id":             "pm_node_dt3",
        "name":           "wrong claim",
        "type":           "promoted_fact",
        "epistemic_kind": "promoted_memory",
        "description":    "wrong claim",
        "keywords":       [],
        "confidence":     0.80,
        "evidence":       [{"episode_ref": "SPOT_0002", "verified": True}],
        "status":         "promoted_memory",
    }
    gpath = _graph_with(tmp_path, [node])

    ok = david_correction("pm_node_dt3", "David said this is wrong", graph_path=gpath)

    assert ok is True, "david_correction should return True on success"
    graph = _load_graph(gpath)
    updated = next(e for e in graph["entities"] if e["id"] == "pm_node_dt3")
    assert updated["status"] == "retracted"
    assert "david_correction" in updated.get("reason", "")
    assert "retracted_at" in updated


# ── DT-4 ─────────────────────────────────────────────────────────────────────

def test_dt4_retracted_node_preserved_with_provenance(tmp_path):
    """After retraction: node exists, has retracted_at, reason, and original evidence."""
    node = {
        "id":             "pm_node_dt4",
        "name":           "some claim",
        "type":           "promoted_fact",
        "epistemic_kind": "promoted_memory",
        "description":    "some claim",
        "keywords":       [],
        "confidence":     0.65,
        "evidence":       [
            {"episode_ref": "SPOT_A", "verified": True},
            {"episode_ref": "SPOT_B", "verified": True},
        ],
        "status":         "promoted_memory",
    }
    gpath = _graph_with(tmp_path, [node])

    david_correction("pm_node_dt4", "factually incorrect", graph_path=gpath)

    graph = _load_graph(gpath)
    updated = next(e for e in graph["entities"] if e["id"] == "pm_node_dt4")
    assert updated["status"] == "retracted", "must be retracted"
    assert "retracted_at" in updated, "must have retracted_at"
    assert "reason" in updated, "must have reason"
    assert len(updated.get("evidence", [])) == 2, "original evidence must be preserved"


# ── DT-5 ─────────────────────────────────────────────────────────────────────

def test_dt5_consolidation_cannot_demote_authored_fact(tmp_path):
    """Authored fact (epistemic_kind='fact') is refused by demotion_pass (Architect lane only)."""
    authored_node = {
        "id":              "authored_001",
        "name":            "eLo is a character",
        "type":            "character",
        "epistemic_kind":  "fact",
        "description":     "eLo is a character",
        "keywords":        ["elo"],
        "confidence":      1.0,
        "evidence":        [{"episode_ref": "CANON", "verified": True}],
        "status":          "promoted_memory",
        "contradicting_count": 5,
    }
    gpath = _graph_with(tmp_path, [authored_node])

    result = demotion_pass(graph_path=gpath)

    assert result["errors"] == [], f"unexpected errors: {result['errors']}"
    graph = _load_graph(gpath)
    node = next(e for e in graph["entities"] if e["id"] == "authored_001")
    # Must be unchanged — Consolidation must refuse authored facts
    assert node["epistemic_kind"] == "fact", "authored fact epistemic_kind must not change"
    assert "authored_001" not in result["demoted"], "authored fact must not be demoted"
    assert "authored_001" not in result["retracted"], "authored fact must not be retracted"


# ── DT-6 ─────────────────────────────────────────────────────────────────────

def test_dt6_re_promotion_requires_fresh_verified_episode(tmp_path):
    """A retracted node cannot be re-promoted without meeting the full §A bar again."""
    gpath = _empty_graph_path(tmp_path)

    # Load a previously retracted node id
    graph = _load_graph(gpath)
    graph["entities"].append({
        "id":            "pm_retracted_001",
        "name":          "old claim",
        "type":          "promoted_fact",
        "epistemic_kind": "retracted",
        "description":   "old claim",
        "keywords":      [],
        "confidence":    0.10,
        "evidence":      [],
        "status":        "retracted",
    })
    with open(gpath, "w", encoding="utf-8") as f:
        json.dump(graph, f)

    # Attempt re-promotion using the same retracted id — should be skipped (already in graph)
    record = {
        "id":           "pm_retracted_001",
        "fact":         "old claim revised",
        "strength":     0.80,
        "episode_refs": _good_refs(),
        "about_world":  True,
    }
    result = promotion_pass([record], graph_path=gpath)
    assert "pm_retracted_001" not in result["promoted"], (
        "Re-promotion of existing id must be skipped; "
        "retracted nodes must re-earn their id independently"
    )
    assert result["skipped"] >= 1


# ── AG-1 ─────────────────────────────────────────────────────────────────────

def test_ag1_constants_agree_with_learning_loop():
    """
    Numeric constants in consolidation_faculty agree with LEARNING_LOOP_v1.md §3.4.
    If a number changes in one, it must change in both.
    """
    assert _KG_STRENGTH_MIN == 0.70,    f"strength min must be 0.70 per §3.4, got {_KG_STRENGTH_MIN}"
    assert _KG_REFS_MIN == 3,           f"refs min must be 3 per §3.4, got {_KG_REFS_MIN}"
    assert _KG_SESSIONS_MIN == 2,       f"sessions min must be 2 per §3.4, got {_KG_SESSIONS_MIN}"
    assert _KG_VERIFIED_MIN == 2,       f"verified min must be 2 per §3.4, got {_KG_VERIFIED_MIN}"
    assert _KG_DEMOTE_THRESHOLD == 0.50, f"demote threshold must be 0.50 per §3.4, got {_KG_DEMOTE_THRESHOLD}"
    assert _KG_RETRACT_THRESHOLD == 0.20, f"retract threshold must be 0.20 per §3.4, got {_KG_RETRACT_THRESHOLD}"
    assert _KG_RETRACT_CONSECUTIVE == 3, f"retract consecutive must be 3 per §3.4, got {_KG_RETRACT_CONSECUTIVE}"
    assert _KG_RETRACT_IDLE_DAYS == 60,  f"retract idle days must be 60 per §3.4, got {_KG_RETRACT_IDLE_DAYS}"

    # Cross-ref: read LEARNING_LOOP_v1.md and verify the same numbers
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ll_path = os.path.join(root, "docs", "architecture", "LEARNING_LOOP_v1.md")
    if os.path.exists(ll_path):
        with open(ll_path, encoding="utf-8") as f:
            text = f.read()
        assert "0.70" in text, "LEARNING_LOOP_v1.md must contain strength threshold 0.70"
        assert "0.50" in text, "LEARNING_LOOP_v1.md must contain demote threshold 0.50"
        assert "0.20" in text, "LEARNING_LOOP_v1.md must contain retract threshold 0.20"
        assert "60 days" in text, "LEARNING_LOOP_v1.md must contain 60 days idle threshold"


# ── KT-1 ─────────────────────────────────────────────────────────────────────

def test_kt1_epistemic_kind_distinct_from_type():
    """
    epistemic_kind is distinct from ontology type.
    fact and promoted_memory with empty evidence[] are rejected.
    perspective needs no evidence but must carry kind="perspective".
    """
    # retrieve() result now has kind=epistemic, type=ontology — verify by inspection
    from knowledge import graph_loader as gl
    saved = gl._graph.copy()
    gl._graph = {
        "entities": [
            {
                "id":            "test_entity",
                "name":          "test entity",
                "type":          "character",
                "epistemic_kind": "fact",
                "description":   "a test entity",
                "keywords":      ["test", "entity"],
                "confidence":    1.0,
                "evidence":      [],
            }
        ],
        "relationships": [],
    }
    try:
        results = retrieve("test entity")
        if results:
            r = results[0]
            assert r.get("kind") == "fact", f"kind should be epistemic 'fact', got {r.get('kind')!r}"
            assert r.get("type") == "character", f"type should be ontology 'character', got {r.get('type')!r}"
            assert r["kind"] != r["type"], "epistemic kind must differ from ontology type"
    finally:
        gl._graph = saved

    # validate_graph_write: fact with empty evidence → ValueError
    with pytest.raises(ValueError, match="evidence"):
        validate_graph_write({"epistemic_kind": "fact", "evidence": []})

    # validate_graph_write: promoted_memory with empty evidence → ValueError
    with pytest.raises(ValueError, match="evidence"):
        validate_graph_write({"epistemic_kind": "promoted_memory", "evidence": []})

    # validate_graph_write: perspective with no evidence → OK (no error)
    validate_graph_write({"epistemic_kind": "perspective", "evidence": []})

    # validate_graph_write: unknown epistemic_kind → ValueError
    with pytest.raises(ValueError, match="Unknown epistemic_kind"):
        validate_graph_write({"epistemic_kind": "secret_belief", "evidence": ["x"]})


# ── KT-2 ─────────────────────────────────────────────────────────────────────

def test_kt2_referential_integrity_detects_dangling():
    """check_referential_integrity() flags relationships with dangling from/to."""
    graph_clean = {
        "entities": [
            {"id": "A"}, {"id": "B"},
        ],
        "relationships": [
            {"id": "r1", "from": "A", "to": "B"},
        ],
    }
    problems = check_referential_integrity(graph_clean)
    assert problems == [], f"clean graph should have no problems, got {problems}"

    graph_dangling = {
        "entities": [{"id": "A"}],
        "relationships": [
            {"id": "r2", "from": "A", "to": "MISSING"},
        ],
    }
    problems = check_referential_integrity(graph_dangling)
    assert len(problems) >= 1, "dangling to= must be detected"
    assert any("MISSING" in p for p in problems), f"problem must name the missing id: {problems}"


# ── KT-3 ─────────────────────────────────────────────────────────────────────

def test_kt3_empty_retrieval_returns_empty_string_not_backfill(tmp_path, monkeypatch):
    """build_context() returns '' when nothing matches — never backfills from LLM."""
    import knowledge.graph_loader as gl

    saved_graph     = gl._graph
    saved_concepts  = gl._concepts
    saved_viewpoints = gl._viewpoints
    gl._graph     = {"entities": [], "relationships": []}
    gl._concepts  = {}
    gl._viewpoints = {}

    try:
        ctx = build_context("xyzzy_unfindable_query_zorkmid_frobnicate")
        assert ctx == "", f"empty match must return '', got {ctx!r}"
    finally:
        gl._graph      = saved_graph
        gl._concepts   = saved_concepts
        gl._viewpoints = saved_viewpoints
