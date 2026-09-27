"""
tests/test_dream_journal_schema.py — WO-DREAM-ENGINE-001 PHASE 7 + PHASE 8 wiring.

PHASE 7 is the extended journal schema. PHASE 8 is the wake transfer gate,
now run on the real dream path with its cognitive channel folded into the
journal entry.

The hard constraint is that this is ADDITIVE. Existing journal readers
depend on the original keys, so nothing is renamed — `phase` stays `phase`
and `sleep_phase` is added alongside it because §7 names it that.
"""
from __future__ import annotations

import json

import pytest

import faculties.dream.dream_faculty as df

# Every field the WO §7 schema names.
WO_SCHEMA = (
    "dream_id", "date", "duration_s", "cycle_number", "sleep_phase",
    "dream_intensity", "seeds", "memories_used", "wkg_relationships",
    "spg_patterns", "emotion_vector", "dream_world", "dream_rule",
    "transformations", "prompts", "scene_images", "final_artwork",
    "unresolved_questions", "new_associations", "recurring_symbols",
    "personality_delta_proposed", "insight", "memory_refs", "output_type",
)

# Keys that existed before PHASE 7 and must survive it.
ORIGINAL_KEYS = (
    "dream_id", "timestamp", "theme", "phase", "symbols", "narrative",
    "insight", "memory_refs", "personality_delta_proposed", "image_ref",
    "mood", "curiosity", "session_read", "focal_thread",
)


class _Self:
    inner_events = ["creative_spark"]
    focal_thread = "still unresolved — what does eLo become when embodied?"
    session_read = "we got the robot arm moving"
    mood = 0.5
    curiosity = 0.6
    lifetime_threads = [("making imagined things physical", 1)]


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "_JOURNAL_PATH", tmp_path / "journal.jsonl")
    monkeypatch.setattr(df, "_SYMBOL_HISTORY_PATH", tmp_path / "symbols.json")
    monkeypatch.setattr(df, "_generate_dream_image", lambda s: None)
    df._last_dream_ts = 0.0
    yield
    df._last_dream_ts = 0.0


def _dream(idle: float = 9000):
    df._last_dream_ts = 0.0
    return df.run_dream(
        _Self(), ["robot arm", "the childhood workshop"],
        lambda m: '{"narrative":"drifting","insight":"the arm stalls at the same angle"}',
        idle_seconds=idle,
    ).journal_entry


# ── PHASE 7 — schema completeness ─────────────────────────────────────────────

@pytest.mark.parametrize("field", WO_SCHEMA)
def test_every_wo_schema_field_is_present(field):
    assert field in _dream(), f"§7 schema field missing: {field}"


def test_schema_is_complete_even_on_a_short_dream():
    entry = _dream(idle=700)          # NREM only, no cycles
    for field in WO_SCHEMA:
        assert field in entry, f"missing on NREM-only dream: {field}"


def test_artwork_fields_are_empty_not_absent_when_no_images_ran():
    entry = _dream()
    assert entry["scene_images"] == []
    assert entry["final_artwork"] is None


# ── Additive: nothing renamed ─────────────────────────────────────────────────

@pytest.mark.parametrize("key", ORIGINAL_KEYS)
def test_original_keys_survive(key):
    assert key in _dream(), f"PHASE 7 dropped an original key: {key}"


def test_phase_is_not_renamed_to_sleep_phase():
    entry = _dream()
    assert entry["phase"] == "NREM+REM"
    assert entry["sleep_phase"] == entry["phase"]


def test_entry_is_json_serialisable():
    json.loads(json.dumps(_dream()))


# ── Flattening ────────────────────────────────────────────────────────────────

def test_seeds_are_flattened_out_of_the_cycles():
    entry = _dream()
    nested = sum(len(c.get("seeds") or []) for c in entry["cycles"])
    assert len(entry["seeds"]) == nested > 0


def test_prompts_are_flattened_and_match_the_scene_count():
    entry = _dream()
    assert len(entry["prompts"]) == entry["scene_count"] > 0


def test_dream_rule_comes_from_the_first_dream_world():
    entry = _dream()
    assert entry["dream_rule"] == entry["cycles"][0]["dream_world"]["physical_rule"]


def test_transformations_are_deduplicated_across_cycles():
    entry = _dream()
    assert entry["transformations"] == list(dict.fromkeys(entry["transformations"]))
    assert set(entry["transformations"]) <= {
        "condensation", "displacement", "symbolic_transformation"}


def test_memories_used_are_the_seed_sources():
    entry = _dream()
    sources = {s["source"] for s in entry["seeds"]}
    assert set(entry["memories_used"]) <= sources


def test_emotion_vector_has_seven_dimensions():
    from faculties.dream.dream_input import EMOTION_DIMENSIONS
    assert set(_dream()["emotion_vector"]) == set(EMOTION_DIMENSIONS)


# ── PHASE 8 folded in ─────────────────────────────────────────────────────────

def test_review_outputs_are_in_the_journal():
    entry = _dream()
    for key in ("significance", "retained", "candidate_insights",
                "new_associations", "spg_patterns", "unresolved_questions"):
        assert key in entry, f"PHASE 8 output not folded in: {key}"


def test_candidate_insights_carry_the_promotion_stage():
    from faculties.dream import dream_review as dr
    insights = _dream()["candidate_insights"]
    assert insights
    for i in insights:
        assert i["stage"] in dr.PROMOTION_LADDER
        assert i["epistemic_class"] in (dr.EPISTEMIC_HYPOTHESIS,
                                        dr.EPISTEMIC_SYMBOLIC)


def test_nothing_in_the_journal_is_a_verified_fact():
    entry = _dream()
    assert entry["output_type"] == "DREAM"
    assert "VERIFIED" not in json.dumps(entry)


def test_the_journal_records_that_the_faculty_does_not_speak():
    assert _dream()["surfaces_directly"] is False


def test_unresolved_questions_come_from_the_review():
    entry = _dream()
    assert entry["unresolved_questions"]
    assert all(isinstance(q, str) for q in entry["unresolved_questions"])


# ── Robustness ────────────────────────────────────────────────────────────────

def test_a_review_failure_does_not_lose_the_journal_entry(monkeypatch):
    """The dream is still journaled even if the gate blows up."""
    import faculties.dream.dream_review as dr
    monkeypatch.setattr(dr, "review", lambda e, **k: (_ for _ in ()).throw(RuntimeError("x")))
    entry = _dream()
    assert entry["dream_id"]
    assert entry["output_type"] == "DREAM"


def test_completion_is_idempotent():
    entry = _dream()
    before = dict(entry)
    df._complete_journal_entry(entry)
    assert entry["sleep_phase"] == before["sleep_phase"]
    assert len(entry["seeds"]) == len(before["seeds"])
