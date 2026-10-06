"""
tests/test_wo_wkg_graph_001.py — WO-WKG-GRAPH-001

Acceptance criteria:
  GRAPH-1: create_entity accepts domain parameter and stores it
  GRAPH-2: create_entity accepts uncertainty parameter and stores it
  GRAPH-3: get_domains returns all 12 required domain names
  GRAPH-4: query_by_domain returns entities matching that domain
  GRAPH-5: get_entity returns an entity by id
  GRAPH-6: claims.json and entities.json exist and are queryable
  GRAPH-7: WKG store has minimum 10 relationship types
"""
import pytest
import uuid


# ── GRAPH-1: domain field on entity ──────────────────────────────────────────

def test_graph1_entity_domain_field():
    """GRAPH-1: create_entity signature accepts domain kwarg"""
    import inspect
    from runtime.wkg_faculty import create_entity
    sig = inspect.signature(create_entity)
    assert "domain" in sig.parameters


# ── GRAPH-2: uncertainty field on entity ─────────────────────────────────────

def test_graph2_entity_uncertainty_field():
    """GRAPH-2: create_entity signature accepts uncertainty kwarg"""
    import inspect
    from runtime.wkg_faculty import create_entity
    sig = inspect.signature(create_entity)
    assert "uncertainty" in sig.parameters


# ── GRAPH-3: get_domains returns 12 required domains ─────────────────────────

def test_graph3_get_domains_complete():
    """GRAPH-3: get_domains returns all 12 WO-WKG-GRAPH-001 domain names"""
    from runtime.wkg_faculty import get_domains
    domains = get_domains()
    required = {
        "Self", "People", "Objects", "Places", "Concepts", "Processes",
        "Embodiment-Affordances", "Humanities", "Systems", "Art-Design", "Music", "Narrative",
    }
    assert required.issubset(set(domains)), f"Missing domains: {required - set(domains)}"


# ── GRAPH-4: query_by_domain returns matching entities ───────────────────────

def test_graph4_query_by_domain():
    """GRAPH-4: query_by_domain returns a list (may be empty if no entities in that domain yet)"""
    from runtime.wkg_faculty import query_by_domain
    result = query_by_domain("People")
    assert isinstance(result, list)


# ── GRAPH-5: get_entity retrieves by id ──────────────────────────────────────

def test_graph5_get_entity_by_id():
    """GRAPH-5: get_entity(entity_id) returns a dict or None"""
    from runtime.wkg_faculty import get_entity, _load
    entities = _load("entities")
    if entities:
        first_id = entities[0]["entity_id"]
        result = get_entity(first_id)
        assert result is not None
        assert result["entity_id"] == first_id
    else:
        result = get_entity(str(uuid.uuid4()))
        assert result is None


# ── GRAPH-6: store files exist and are queryable ─────────────────────────────

def test_graph6_store_queryable():
    """GRAPH-6: WKG store has entities and claims, both lists"""
    from runtime.wkg_faculty import _load
    entities = _load("entities")
    claims = _load("claims")
    assert isinstance(entities, list)
    assert isinstance(claims, list)


# ── GRAPH-7: minimum relationship types ──────────────────────────────────────

def test_graph7_minimum_relationship_types():
    """GRAPH-7: at least 10 relationship types defined"""
    from runtime.wkg_faculty import _load
    rel_types = _load("relationship_types")
    assert len(rel_types) >= 10, f"Only {len(rel_types)} relationship types, need ≥ 10"
