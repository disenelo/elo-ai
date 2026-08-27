"""
tests/test_company_graph.py

WP_F gap: company_runtime/company_graph.py — DISENELO org connectome.
Static org structure: divisions → faculties → seats → MoodPalette colours.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_company_graph.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_runtime.company_graph import DIVISIONS, build_graph, lane_for


def test_nine_divisions_defined():
    """AT-1: org has 9 divisions (matches eLo's 9 cognitive systems — same visualiser)."""
    assert len(DIVISIONS) == 9, (
        f"AT-1: DISENELO org must have 9 divisions; got {len(DIVISIONS)}"
    )


def test_division_tuples_have_required_fields():
    """AT-2: each division tuple has id, label, faculty, mood, hex colour."""
    for div in DIVISIONS:
        assert len(div) == 5, (
            f"AT-2: each division must have 5 fields; got {len(div)}: {div!r}"
        )
        div_id, label, faculty, mood, hex_col = div
        assert div_id.startswith("DIV-"), (
            f"AT-2: division id must start with 'DIV-'; got {div_id!r}"
        )
        assert hex_col.startswith("#") and len(hex_col) == 7, (
            f"AT-2: hex colour must be #RRGGBB; got {hex_col!r} for {label}"
        )


def test_build_graph_returns_dict_with_nodes():
    """AT-3: build_graph() returns a dict with at least 9 nodes."""
    graph = build_graph()
    assert isinstance(graph, dict), f"AT-3: build_graph() must return a dict; got {type(graph)}"
    nodes = graph.get("nodes", graph.get("divisions", []))
    assert len(nodes) >= 9, (
        f"AT-3: graph must have >=9 nodes; got {len(nodes)}"
    )


def test_lane_for_known_seat():
    """AT-4: lane_for() returns a non-empty string for a known seat."""
    result = lane_for("Builder")
    assert isinstance(result, str) and result, (
        f"AT-4: lane_for('Builder') must return a non-empty string; got {result!r}"
    )


def test_lane_for_unknown_seat_does_not_crash():
    """AT-5: lane_for() with an unknown seat returns a string (no exception)."""
    try:
        result = lane_for("AlienSeat")
        assert isinstance(result, str), (
            f"AT-5: lane_for('AlienSeat') must return a string; got {result!r}"
        )
    except Exception as e:
        assert False, f"AT-5: lane_for must not raise for unknown seats; got {e!r}"


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_nine_divisions_defined),
        ("AT-2", test_division_tuples_have_required_fields),
        ("AT-3", test_build_graph_returns_dict_with_nodes),
        ("AT-4", test_lane_for_known_seat),
        ("AT-5", test_lane_for_unknown_seat_does_not_crash),
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
    print(f"company_graph   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
