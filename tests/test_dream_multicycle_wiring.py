"""
tests/test_dream_multicycle_wiring.py — WO-DREAM-ENGINE-001, dream_faculty wired.

The five faculty modules (sleep_cycle / dream_input / dream_work /
prompt_builder) existed but nothing called them — run_dream() ran its original
single-cycle path. They are now on the real dream path.

The hard constraint: this is ADDITIVE. `phase` keeps its original two values
and every original journal key keeps its name and meaning, because existing
callers and journal readers depend on them.
"""
from __future__ import annotations

import json

import pytest

import faculties.dream.dream_faculty as df
from faculties.dream.dream_faculty import run_dream


class _Self:
    inner_events = ["creative_spark", "restless"]
    focal_thread = "the arm stops at the same angle"
    session_read = "we got the robot arm moving"
    mood = 0.5
    curiosity = 0.6
    lifetime_threads = [("making imagined things physical", 1)]


def _llm(_messages):
    return '{"narrative": "something drifts", "insight": "it was there already"}'


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    df._last_dream_ts = 0.0
    # never append to the real self/dream_journal.jsonl from a test
    monkeypatch.setattr(df, "_JOURNAL_PATH", tmp_path / "dream_journal.jsonl")
    # never call the image generator (network + openai dependency)
    monkeypatch.setattr(df, "_generate_dream_image", lambda symbols: None)
    yield
    df._last_dream_ts = 0.0


def _dream(idle: float):
    df._last_dream_ts = 0.0
    return run_dream(_Self(), ["robot arm", "the childhood workshop"], _llm,
                     idle_seconds=idle)


# ── The additive contract ─────────────────────────────────────────────────────

def test_phase_keeps_its_original_two_values():
    assert _dream(700).journal_entry["phase"] == "NREM"
    assert _dream(2000).journal_entry["phase"] == "NREM+REM"


def test_every_original_journal_key_survives():
    entry = _dream(2000).journal_entry
    for key in ("dream_id", "timestamp", "theme", "phase", "symbols",
                "narrative", "insight", "memory_refs",
                "personality_delta_proposed", "image_ref", "mood",
                "curiosity", "session_read", "focal_thread"):
        assert key in entry, f"original journal key lost: {key}"


def test_journal_entry_is_json_serialisable():
    """It is written to a .jsonl — an unserialisable object would break it."""
    entry = _dream(9000).journal_entry
    json.loads(json.dumps(entry))


# ── Multi-cycle behaviour ─────────────────────────────────────────────────────

def test_short_idle_runs_no_cycles():
    entry = _dream(700).journal_entry
    assert entry["cycle_count"] == 0
    assert entry["scene_count"] == 0
    assert entry["dream_intensity"] == 0.0


def test_cycle_count_grows_with_idle():
    assert _dream(2000).journal_entry["cycle_count"] == 1
    assert _dream(3600).journal_entry["cycle_count"] == 2
    assert _dream(9000).journal_entry["cycle_count"] == 5


def test_cycles_for_idle_mapping_is_bounded():
    assert df._cycles_for_idle(0) == 0
    assert df._cycles_for_idle(1799) == 0
    assert df._cycles_for_idle(1800) == 1
    assert df._cycles_for_idle(10**9) == 5


def test_full_night_reaches_maximum_intensity_and_many_scenes():
    entry = _dream(9000).journal_entry
    assert entry["dream_intensity"] == 1.00
    assert entry["scene_count"] >= 2          # WO acceptance criterion 6
    intensities = [c["dream_intensity"] for c in entry["cycles"]]
    assert intensities == sorted(intensities)


def test_each_cycle_carries_world_seeds_scenes_and_prompts():
    for cycle in _dream(9000).journal_entry["cycles"]:
        assert cycle["seeds"]
        assert cycle["dream_world"]["physical_rule"]
        assert cycle["scenes"]
        assert cycle["prompts"]
        assert len(cycle["prompts"]) == len(cycle["scenes"])


def test_prompts_carry_the_mandated_closing_line():
    from faculties.dream.prompt_builder import FINAL_LINE
    for cycle in _dream(9000).journal_entry["cycles"]:
        for prompt in cycle["prompts"]:
            assert prompt.endswith(FINAL_LINE)


def test_recurring_symbol_carries_across_the_night():
    """One symbol threads the whole sleep — that is what PHASE 10 tracks."""
    entry = _dream(9000).journal_entry
    assert len(entry["recurring_symbols"]) == 1


def test_nothing_is_tagged_fact():
    entry = _dream(9000).journal_entry
    assert entry["output_type"] == "DREAM"
    for cycle in entry["cycles"]:
        assert cycle["output_type"] == "DREAM"
    assert "FACT" not in json.dumps(entry)


def test_same_dream_id_reproduces_the_same_dream(monkeypatch):
    import uuid
    monkeypatch.setattr(uuid, "uuid4", lambda: uuid.UUID(int=0x5eed5eed5eed5eed))
    a = _dream(9000).journal_entry["cycles"]
    b = _dream(9000).journal_entry["cycles"]
    assert a == b


# ── Safety ────────────────────────────────────────────────────────────────────

def test_phase_publishing_is_off_by_default():
    """
    blender_state.json is live — the server writes it every cycle and
    DesktopBuddy reads it every frame. A dream run from a test must not
    touch it.
    """
    import inspect
    sig = inspect.signature(run_dream)
    assert sig.parameters["publish_phases"].default is False


def test_multicycle_failure_cannot_break_the_original_dream(monkeypatch):
    """The original narrative path must survive a fault in the new engine."""
    def boom(*a, **k):
        raise RuntimeError("sleep schedule exploded")
    monkeypatch.setattr(df, "_run_sleep_cycles", boom)

    result = _dream(2000)
    assert result.journal_entry["phase"] == "NREM+REM"
    assert result.narrative                      # original path still ran
    assert result.journal_entry["cycle_count"] == 0


def test_empty_self_state_does_not_crash():
    class _Bare:
        pass
    df._last_dream_ts = 0.0
    result = run_dream(_Bare(), [], _llm, idle_seconds=9000)
    assert result.journal_entry["phase"] == "NREM+REM"


def test_context_leaves_unavailable_sources_empty(monkeypatch):
    """An empty source is honest; a plausible substitute is not."""
    # Isolated from the live turn store on purpose. _dream_context now also
    # feeds real conversation into recent_conversation, and without this the
    # test asserts against whatever David said most recently.
    monkeypatch.setattr(df, "_INTERACTIONS_PATH", "/nonexistent/interactions.json")
    ctx = df._dream_context(_Self(), ["a topic"])
    assert ctx["recent_conversation"] == ["a topic"]
    for unavailable in ("wkg", "emotional_significance", "novelty",
                        "failure", "achievement", "relationship", "embodiment"):
        assert ctx[unavailable] == [], unavailable


def test_real_conversation_joins_the_topics_without_replacing_them():
    """
    Topic labels alone are not dreamable material. Measured 2026-10-10: of
    1,489 seeds ever written the commonest sources were 'y' (360) and 'x'
    (270) -- single tokens carrying no emotion cue and no unfinishedness cue,
    which is why both of those scorer terms read 0.0 on every dream eLo has
    ever had.

    Real turns are added; the topics are NOT dropped.
    """
    ctx = df._dream_context(_Self(), ["a topic"])
    assert "a topic" in ctx["recent_conversation"]
    real = [t for t in ctx["recent_conversation"] if len(t) >= 12]
    assert real, "no real conversation reached the dream context"
