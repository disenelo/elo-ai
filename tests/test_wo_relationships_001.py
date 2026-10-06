"""
tests/test_wo_relationships_001.py — WO-RELATIONSHIPS-001: relationship profile

Acceptance criteria:
  REL-1: get_relationship_profile() returns a non-empty string for David's entity_id
  REL-2: The barkcloth backfill fact appears in the profile (known good SOURCE_ATTRIBUTED claim)
  REL-3: Contaminated category-label stubs ("identity", "projects") do NOT appear
  REL-4: UUID-only labels (orphaned object entity IDs) do NOT appear
  REL-5: Write a new fact, verify it appears immediately in the profile
"""

import re
import pytest

DAVID_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


def _profile():
    from runtime.wkg_faculty import get_relationship_profile
    return get_relationship_profile(DAVID_ID, max_facts=12)


def test_rel1_profile_non_empty():
    """REL-1: profile is non-empty string for David's entity_id"""
    p = _profile()
    assert isinstance(p, str) and len(p) > 0


def test_rel2_barkcloth_fact_present():
    """REL-2: the barkcloth backfill fact appears"""
    p = _profile()
    assert "barkcloth" in p.lower(), f"barkcloth not found in profile:\n{p}"


def test_rel3_no_junk_labels():
    """REL-3: contaminated category-label stubs do not appear"""
    p = _profile()
    for junk in ("- identity", "- projects", "- world", "- creative", "- plans",
                 "- preferences", "- learning", "- relationship", "- commitments", "- user"):
        assert junk not in p.lower(), f"Junk label {junk!r} found in profile:\n{p}"


def test_rel4_no_uuid_labels():
    """REL-4: UUID-only labels do not appear (orphaned object entity references)"""
    p = _profile()
    for line in p.splitlines():
        if line.startswith("- "):
            label = line[2:].strip()
            assert not _UUID_RE.match(label), f"UUID label in profile: {label!r}"


def test_rel5_new_fact_appears_immediately():
    """REL-5: a fact written now appears immediately in the next profile call"""
    from runtime.wkg_faculty import create_entity, record_claim, get_relationship_profile, deprecate_entity
    import time

    unique = f"test_label_{int(time.time())}"
    ent = create_entity(
        "CONCEPT",
        unique,
        description=f'Stated: "this is a test fact {unique}"',
    )
    # The cleanup below sat AFTER the assert, so a failing run never reached
    # it. Measured 2026-10-06: 22 test_label_ artifacts in the live WKG store
    # and 5 of them never deprecated — live, searchable junk in eLo's
    # knowledge graph, left by the runs where this test failed.
    #
    # It also writes the LIVE store on every pass, which is why
    # test_spg_feedback_loop::test_unrelated_turn_retrieves_nothing fails in
    # the suite and passes alone.
    try:
        record_claim(
            subject_entity_id=DAVID_ID,
            relationship_type="HAS_PROPERTY",
            object_entity_id=ent["entity_id"],
            epistemic_class="SOURCE_ATTRIBUTED",
            source_id="test_rel5",
            confidence=0.72,
            memory_type="semantic",
            memory_origin="real_experience",
        )
        profile_after = get_relationship_profile(DAVID_ID, max_facts=20)
        assert unique in profile_after, f"New fact not found in profile:\n{profile_after}"
    finally:
        deprecate_entity(
            ent["entity_id"],
            reason="test artifact — WO-RELATIONSHIPS-001 test_rel5",
        )
