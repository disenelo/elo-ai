"""
tests/test_dream_review.py — WO-DREAM-ENGINE-001 PHASE 8.

The wake transfer gate. These tests exist mostly to pin the two rules the WO
puts under "What must NOT happen":

  - Dream material is never silently written as fact.
  - The Dream Faculty does not speak to David directly.

The gate reuses the codebase's existing dream boundary
(runtime/memory_origin.py + wkg_faculty's WO-DREAM-VERIFY-001 write block)
rather than a second one, so these tests also guard that alignment.
"""
from __future__ import annotations

import pytest

from faculties.dream import dream_review as dr
from runtime.memory_origin import DREAM_RETENTION_THRESHOLD, MemoryOrigin, is_auto_storable


def _entry(**over) -> dict:
    base = {
        "dream_id": "a3f7c2b1",
        "insight": "the pattern was already there",
        "dream_intensity": 0.5,
        "cycle_count": 1,
        "scene_count": 2,
        "recurring_symbols": ["a machine breathing"],
        "cycles": [{
            "emotion_vector": {"wonder": 0.4, "joy": 0.1},
            "prompts": ["scene one prompt", "scene two prompt"],
            "seeds": [{
                "source": "the arm moved",
                "associated_concepts": ["robot", "workshop", "movement"],
                "spg_pattern": "Repeated theme around robot",
                "unresolved": "What does eLo become when physically embodied?",
            }],
            "dream_world": {"recurring_symbol": "a machine breathing"},
        }],
    }
    base.update(over)
    return base


# ── Nothing is ever a fact ────────────────────────────────────────────────────

def test_no_output_is_ever_epistemically_verified():
    rv = dr.review(_entry(dream_intensity=1.0))
    emitted = (
        [i.epistemic_class for i in rv.candidate_insights]
        + [a["epistemic_class"] for a in rv.new_associations]
        + [p["epistemic_class"] for p in rv.candidate_spg_patterns]
    )
    assert emitted, "review produced nothing to check"
    for cls in emitted:
        assert cls not in dr.FORBIDDEN_EPISTEMIC
        assert cls in (dr.EPISTEMIC_HYPOTHESIS, dr.EPISTEMIC_SYMBOLIC)


def test_clearing_the_gate_promotes_origin_but_not_epistemic_class():
    """VALIDATED means eligible for retention, NOT true."""
    rv = dr.review(_entry(), assessor=lambda e: 0.99)
    assert rv.retained is True
    insight = rv.candidate_insights[0]
    assert insight.memory_origin == MemoryOrigin.DREAM_INSIGHT.value
    assert insight.epistemic_class == dr.EPISTEMIC_HYPOTHESIS, (
        "a retained dream was promoted to a verified fact"
    )


def test_below_the_gate_stays_dream_simulation_and_unretained():
    rv = dr.review(_entry(), assessor=lambda e: 0.01)
    assert rv.retained is False
    insight = rv.candidate_insights[0]
    assert insight.memory_origin == MemoryOrigin.DREAM_SIMULATION.value
    assert insight.retained is False


def test_unretained_associations_are_not_auto_storable():
    """wkg_faculty blocks DREAM_SIMULATION at the write gate; agree with it."""
    rv = dr.review(_entry(), assessor=lambda e: 0.01)
    assert rv.new_associations
    for assoc in rv.new_associations:
        assert assoc["auto_storable"] is False
        assert is_auto_storable(MemoryOrigin(assoc["memory_origin"])) is False


def test_the_gate_threshold_is_the_canonical_one():
    """Not a second threshold invented here."""
    assert dr.DREAM_RETENTION_THRESHOLD == DREAM_RETENTION_THRESHOLD == 0.72

    just_under = dr.review(_entry(), assessor=lambda e: 0.719)
    just_over = dr.review(_entry(), assessor=lambda e: 0.72)
    assert just_under.retained is False
    assert just_over.retained is True


# ── The faculty does not speak ────────────────────────────────────────────────

def test_there_is_no_way_for_the_faculty_to_address_david():
    rv = dr.review(_entry())
    for forbidden in ("speak", "emit", "say", "send", "respond", "surface"):
        assert not hasattr(rv, forbidden), f"DreamReview exposes {forbidden}()"
    for forbidden in ("speak", "emit", "say"):
        assert not hasattr(dr, forbidden)


def test_executive_payload_declares_it_does_not_surface_directly():
    payload = dr.review(_entry()).for_executive()
    assert payload["surfaces_directly"] is False
    assert set(payload) == {"cognitive", "creative", "surfaces_directly"}


# ── Two output channels (WO section 46) ───────────────────────────────────────

def test_cognitive_channel_carries_the_six_wo_outputs():
    channel = dr.review(_entry()).cognitive_channel()
    for key in ("dream_record", "candidate_insights", "new_associations",
                "candidate_spg_patterns", "research_questions"):
        assert key in channel


def test_creative_channel_carries_prompts_and_does_not_fabricate_images():
    """PHASES 5-6 are not built; the keys report empty rather than inventing."""
    channel = dr.review(_entry()).creative_channel()
    assert channel["prompts"] == ["scene one prompt", "scene two prompt"]
    assert channel["scene_images"] == []
    assert channel["final_artwork"] is None
    assert channel["metadata"]["output_type"] == "DREAM"


def test_channels_are_disjoint_in_purpose():
    rv = dr.review(_entry())
    assert "prompts" not in rv.cognitive_channel()
    assert "candidate_insights" not in rv.creative_channel()


# ── Content extraction ────────────────────────────────────────────────────────

def test_research_questions_come_from_unresolved_seeds():
    questions = dr.review(_entry()).research_questions
    assert questions == ["What does eLo become when physically embodied?"]


def test_associations_are_deduplicated():
    entry = _entry()
    entry["cycles"].append(entry["cycles"][0])
    rv = dr.review(entry)
    pairs = [(a["subject"], a["object"]) for a in rv.new_associations]
    assert len(pairs) == len(set(pairs))


def test_recurring_symbol_becomes_a_candidate_pattern():
    patterns = [p["pattern"] for p in dr.review(_entry()).candidate_spg_patterns]
    assert any("a machine breathing" in p for p in patterns)


# ── Significance ──────────────────────────────────────────────────────────────

def test_significance_rises_with_intensity_emotion_and_unresolvedness():
    low = dr.assess_significance({"dream_intensity": 0.0, "cycles": []})
    high = dr.assess_significance(_entry(dream_intensity=1.0))
    assert 0.0 <= low < high <= 1.0


def test_a_vivid_dream_about_nothing_does_not_clear_the_gate():
    """No single signal may promote a dream on its own."""
    vivid_only = {
        "dream_id": "x", "dream_intensity": 1.0,
        "cycles": [{"emotion_vector": {}, "seeds": [{}]}],
    }
    assert dr.assess_significance(vivid_only) < DREAM_RETENTION_THRESHOLD


def test_significance_is_clamped():
    everything = _entry(dream_intensity=5.0)
    assert 0.0 <= dr.assess_significance(everything) <= 1.0


# ── Robustness ────────────────────────────────────────────────────────────────

def test_empty_entry_does_not_crash():
    rv = dr.review({})
    assert rv.retained is False
    assert rv.candidate_insights == []
    assert rv.for_executive()["surfaces_directly"] is False


def test_none_entry_does_not_crash():
    assert dr.review(None).significance >= 0.0


def test_review_writes_nothing(tmp_path, monkeypatch):
    """The gate is a decision, not a side effect."""
    import faculties.dream.symbol_history as sh
    from blender_bridge import state_writer as sw

    calls: list = []
    monkeypatch.setattr(sh, "save", lambda *a, **k: calls.append("lexicon"))
    monkeypatch.setattr(sw, "patch", lambda *a, **k: calls.append("state"))
    dr.review(_entry(), assessor=lambda e: 0.99)
    assert calls == []
