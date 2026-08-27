"""
tests/test_visual_memory.py

WP_F gap: core/visual_memory.py — spatial cluster graph from interactions.
Pure Python — no file I/O, no LLM. Pass interactions= directly to build_world().

Run: ~/miniconda3/bin/python3 -m pytest tests/test_visual_memory.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.visual_memory import build_world, render_terminal, world_to_elo_speech, _size_hint


def _record(concept, project="elo_core", user="hello"):
    return {"concepts": [concept], "project_tag": project, "user": user, "timestamp": "2026-08-27T00:00:00", "mode": "companion"}


_INTERACTIONS = [
    _record("creation", user="let's build the module"),
    _record("creation", user="how do we wire the router"),
    _record("creation", user="add the bridge layer"),
    _record("narrative", user="what is the story arc"),
    _record("emotion",   user="I feel good about this"),
    {"concepts": ["creation", "narrative"], "project_tag": "elo_core", "user": "build story", "timestamp": "2026-08-27T00:00:00", "mode": "companion"},
]


def test_build_world_empty_interactions():
    """AT-1: empty interactions → empty world with total_items=0 and no clusters."""
    world = build_world(interactions=[])
    assert world["total_items"] == 0, f"AT-1: total_items must be 0; got {world['total_items']}"
    assert world["clusters"] == [], f"AT-1: clusters must be []; got {world['clusters']}"
    assert world["bridges"] == [], f"AT-1: bridges must be []; got {world['bridges']}"


def test_build_world_clusters_by_concept():
    """AT-2: interactions grouped into clusters by dominant_concept."""
    world = build_world(interactions=_INTERACTIONS)
    assert world["total_items"] == len(_INTERACTIONS)
    cluster_concepts = {c["dominant_concept"] for c in world["clusters"]}
    assert "creation" in cluster_concepts, f"AT-2: creation cluster missing; got {cluster_concepts}"
    assert "narrative" in cluster_concepts, f"AT-2: narrative cluster missing; got {cluster_concepts}"


def test_build_world_largest_cluster_first():
    """AT-3: clusters sorted largest first (creation has 4 records in _INTERACTIONS)."""
    world = build_world(interactions=_INTERACTIONS)
    counts = [c["count"] for c in world["clusters"]]
    assert counts == sorted(counts, reverse=True), (
        f"AT-3: clusters must be sorted largest first; got {counts}"
    )


def test_build_world_filters_by_project():
    """AT-4: project= filter limits clusters to that project_tag."""
    interactions = [
        _record("creation", project="proj_a"),
        _record("narrative", project="proj_b"),
    ]
    world = build_world(project="proj_a", interactions=interactions)
    assert world["total_items"] == 1, (
        f"AT-4: only 1 record for proj_a; got total_items={world['total_items']}"
    )
    for c in world["clusters"]:
        assert c.get("dominant_concept") != "narrative", (
            "AT-4: proj_b narrative must not appear when filtering proj_a"
        )


def test_build_world_bridges_from_co_occurrence():
    """AT-5: record with 2 concepts generates at least 1 bridge."""
    world = build_world(interactions=_INTERACTIONS)
    assert len(world["bridges"]) >= 1, (
        f"AT-5: co-occurrence of creation+narrative must produce >=1 bridge; got {world['bridges']}"
    )
    for bridge in world["bridges"]:
        assert "from" in bridge and "to" in bridge, f"AT-5: bridge missing from/to; got {bridge}"
        assert 0.0 <= bridge["strength"] <= 1.0, (
            f"AT-5: bridge strength must be in [0,1]; got {bridge['strength']}"
        )


def test_size_hint_thresholds():
    """AT-6: _size_hint returns correct label for each threshold."""
    assert _size_hint(1) == "island_small"
    assert _size_hint(2) == "island_small"
    assert _size_hint(3) == "island_medium"
    assert _size_hint(5) == "island_medium"
    assert _size_hint(6) == "island_large"
    assert _size_hint(10) == "island_large"
    assert _size_hint(11) == "island_hub"


def test_render_terminal_returns_string():
    """AT-7: render_terminal() returns a string containing the world name."""
    world = build_world(interactions=_INTERACTIONS, world_name="Test World")
    output = render_terminal(world)
    assert isinstance(output, str), f"AT-7: render_terminal must return str; got {type(output)}"
    assert "Test World" in output, f"AT-7: world_name must appear in output; got:\n{output}"


def test_world_to_elo_speech_empty():
    """AT-8: world_to_elo_speech on empty world returns the no-memory message."""
    world = build_world(interactions=[])
    speech = world_to_elo_speech(world)
    assert isinstance(speech, str), f"AT-8: speech must be str; got {type(speech)}"
    assert "empty" in speech.lower() or "start" in speech.lower(), (
        f"AT-8: empty world speech must mention 'empty' or 'start'; got {speech!r}"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_build_world_empty_interactions),
        ("AT-2", test_build_world_clusters_by_concept),
        ("AT-3", test_build_world_largest_cluster_first),
        ("AT-4", test_build_world_filters_by_project),
        ("AT-5", test_build_world_bridges_from_co_occurrence),
        ("AT-6", test_size_hint_thresholds),
        ("AT-7", test_render_terminal_returns_string),
        ("AT-8", test_world_to_elo_speech_empty),
    ]
    _passed = _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"visual_memory   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
