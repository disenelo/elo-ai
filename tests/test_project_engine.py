"""
tests/test_project_engine.py

WP_F gap: core/project_engine.py — eLo AI project registry management.
Tested with in-memory registry dicts to avoid touching the real file on disk.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_project_engine.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.project_engine import (
    list_projects,
    get_project,
    resolve_project,
    default_namespace,
)

_REGISTRY = {
    "project_namespace": "elo_core",
    "active_projects": {
        "elo_planet_game": {
            "name": "eLo Planet",
            "linked_systems": ["unity", "platformer"],
        },
        "elo_robot": {
            "name": "eLo Robot",
            "linked_systems": ["raspberry_pi", "servo"],
        },
    },
}


def test_list_projects_returns_active_projects():
    """AT-1: list_projects() returns the active_projects dict."""
    projects = list_projects(_REGISTRY)
    assert "elo_planet_game" in projects, (
        f"AT-1: list_projects must include 'elo_planet_game'; got {list(projects)}"
    )
    assert "elo_robot" in projects, (
        f"AT-1: list_projects must include 'elo_robot'; got {list(projects)}"
    )


def test_get_project_known():
    """AT-2: get_project() returns metadata for a known project."""
    info = get_project("elo_planet_game", _REGISTRY)
    assert info.get("name") == "eLo Planet", (
        f"AT-2: get_project name mismatch; got {info!r}"
    )


def test_get_project_unknown_returns_empty():
    """AT-3: get_project() returns empty dict for unknown project."""
    result = get_project("not_a_project", _REGISTRY)
    assert result == {}, f"AT-3: unknown project must return {{}}; got {result!r}"


def test_resolve_project_by_id_match():
    """AT-4: resolve_project() matches on project id."""
    result = resolve_project("working on elo_planet_game today", _REGISTRY)
    assert result == "elo_planet_game", (
        f"AT-4: resolve must match project id; got {result!r}"
    )


def test_resolve_project_by_linked_system():
    """AT-5: resolve_project() matches on linked_systems."""
    result = resolve_project("testing with unity builds", _REGISTRY)
    assert result == "elo_planet_game", (
        f"AT-5: resolve must match linked system 'unity'; got {result!r}"
    )


def test_resolve_project_fallback_to_namespace():
    """AT-6: resolve_project() returns default namespace when no match found."""
    result = resolve_project("completely unrelated topic", _REGISTRY)
    assert result == "elo_core", (
        f"AT-6: no match must fall back to 'elo_core'; got {result!r}"
    )


def test_default_namespace_returns_correct_value():
    """AT-7: default_namespace() returns the project_namespace from registry."""
    result = default_namespace(_REGISTRY)
    assert result == "elo_core", (
        f"AT-7: default_namespace must be 'elo_core'; got {result!r}"
    )


def test_default_namespace_fallback_when_missing():
    """AT-8: default_namespace() returns 'elo_core' when registry has no namespace key."""
    result = default_namespace({"active_projects": {}})
    assert result == "elo_core", (
        f"AT-8: fallback namespace must be 'elo_core'; got {result!r}"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1", test_list_projects_returns_active_projects),
        ("AT-2", test_get_project_known),
        ("AT-3", test_get_project_unknown_returns_empty),
        ("AT-4", test_resolve_project_by_id_match),
        ("AT-5", test_resolve_project_by_linked_system),
        ("AT-6", test_resolve_project_fallback_to_namespace),
        ("AT-7", test_default_namespace_returns_correct_value),
        ("AT-8", test_default_namespace_fallback_when_missing),
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
    print(f"project_engine   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
