"""
tests/test_company_brain_state_writer.py

WP_F gap: company_runtime/company_brain_state_writer.py — Company Brain brain_state/v1 writer.
All pure-Python transformers tested in isolation; no filesystem writes.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_company_brain_state_writer.py -q
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from company_runtime.company_brain_state_writer import (
    _slot_keys,
    _mood,
    _agent_index,
    _division_vortex,
    _VALENCE,
    _PALETTE_WORDS,
    _ELO_SLOTS,
    build,
)


def _div(label="Creative", div_id="DIV-1", mood="curious", seats=None):
    return {
        "id":     div_id,
        "label":  label,
        "mood":   mood,
        "seats":  seats or [{"id": "builder", "label": "Builder", "occ": "builder", "status": "WORKING"}],
    }


def _state(divisions=None, agents=None, approvals=None, blocked=None):
    return {
        "graph": {
            "divisions": divisions or [_div()],
        },
        "agents": agents or [],
        "waiting_for_approval": approvals or [],
        "blocked": blocked or [],
    }


def test_slot_keys_reuses_elo_names_for_first_8():
    """AT-1: _slot_keys() uses eLo's slot names for positions 1-8, generates names beyond."""
    keys = _slot_keys(8)
    assert keys[0] == "intent", f"AT-1: core slot must be 'intent'; got {keys[0]!r}"
    # slots 1-8 should match _ELO_SLOTS[1:]
    for i in range(1, 9):
        assert keys[i] == _ELO_SLOTS[i], (
            f"AT-1: slot {i} must be {_ELO_SLOTS[i]!r}; got {keys[i]!r}"
        )


def test_slot_keys_generates_beyond_elo_slots():
    """AT-2: _slot_keys() generates division_N keys for divisions beyond eLo's 9 slots."""
    keys = _slot_keys(10)  # 10 divisions — exceeds eLo's 8 non-core slots
    assert "division_9" in keys or "division_10" in keys, (
        f"AT-2: keys beyond eLo's 9 must use division_N naming; got {keys}"
    )


def test_slot_keys_no_silent_drop():
    """AT-3: _slot_keys(n) always returns n+1 keys (core + one per division)."""
    for n in range(0, 15):
        keys = _slot_keys(n)
        assert len(keys) == n + 1, (
            f"AT-3: _slot_keys({n}) must return {n+1} keys; got {len(keys)}"
        )


def test_mood_known_palette_word():
    """AT-4: _mood() returns ('word', 'word', 'PALETTE') for a known palette word."""
    w, raw, src = _mood("curious")
    assert w == "curious", f"AT-4: palette word must be returned unchanged; got {w!r}"
    assert src == "PALETTE", f"AT-4: known word must have source='PALETTE'; got {src!r}"


def test_mood_unknown_word_flags_missing():
    """AT-5: _mood() returns the raw word with source='MISSING_FROM_MOODPALETTE' for unknown words."""
    _, _, src = _mood("momentum")
    assert src == "MISSING_FROM_MOODPALETTE", (
        f"AT-5: unknown mood word must be flagged MISSING_FROM_MOODPALETTE; got {src!r}"
    )


def test_mood_empty_input_falls_back_to_neutral():
    """AT-6: _mood('') or _mood(None) returns 'neutral' without crashing."""
    w, _, _ = _mood("")
    assert w == "neutral", f"AT-6: empty mood must return 'neutral'; got {w!r}"


def test_valence_map_has_expected_keys():
    """AT-7: _VALENCE has all 7 expected status keys."""
    for status in ("WORKING", "READY", "REVIEW", "BLOCKED", "DAVID_REQUIRED", "IDLE", "DONE"):
        assert status in _VALENCE, f"AT-7: _VALENCE missing '{status}'"
    assert _VALENCE["BLOCKED"] == -1.0, f"AT-7: BLOCKED must have valence -1.0"
    assert _VALENCE["WORKING"] ==  1.0, f"AT-7: WORKING must have valence 1.0"


def test_agent_index_maps_seat_to_agent():
    """AT-8: _agent_index() creates seat_id → agent entry mapping."""
    agents = [{"seats": ["builder", "design"], "pending": 3, "active": 1, "fresh": True}]
    idx = _agent_index({"agents": agents})
    assert "builder" in idx, f"AT-8: 'builder' must be in index; got {list(idx)}"
    assert "design"  in idx, f"AT-8: 'design' must be in index; got {list(idx)}"
    assert idx["builder"]["pending"] == 3, f"AT-8: pending must propagate; got {idx['builder']}"


def test_division_vortex_shape():
    """AT-9: _division_vortex() returns a dict with all required brain_state/v1 keys."""
    div = _div()
    vortex = _division_vortex(div, {})
    required = ("energy", "valence", "active", "rate", "confidence", "label", "mood_raw", "_division")
    for key in required:
        assert key in vortex, f"AT-9: vortex must have '{key}'; got {list(vortex)}"


def test_division_vortex_energy_in_range():
    """AT-10: _division_vortex() energy is always clamped to [0, 1]."""
    div = _div(seats=[
        {"id": "s1", "status": "WORKING"},
        {"id": "s2", "status": "WORKING"},
        {"id": "s3", "status": "WORKING"},
    ])
    vortex = _division_vortex(div, {})
    assert 0.0 <= vortex["energy"] <= 1.0, (
        f"AT-10: energy must be in [0,1]; got {vortex['energy']}"
    )


def test_build_schema_and_required_keys():
    """AT-11: build() returns brain_state/v1 dict with all required top-level keys."""
    result = build(_state())
    required = ("schema", "mode", "systems", "cluster_energy", "divisions_in", "vortices_out")
    for key in required:
        assert key in result, f"AT-11: build() result missing '{key}'; got {list(result)}"
    assert result["schema"] == "brain_state/v1", f"AT-11: schema wrong; got {result['schema']!r}"
    assert result["mode"] == "company", f"AT-11: mode must be 'company'; got {result['mode']!r}"


def test_build_divisions_in_equals_vortices_out():
    """AT-12: build() reports divisions_in == vortices_out — no silent cap."""
    divs = [_div(div_id=f"DIV-{i}", label=f"Div{i}") for i in range(5)]
    result = build(_state(divisions=divs))
    assert result["divisions_in"] == 5, (
        f"AT-12: divisions_in must be 5; got {result['divisions_in']}"
    )
    assert result["vortices_out"] == 5, (
        f"AT-12: vortices_out must be 5; got {result['vortices_out']}"
    )


def test_build_no_founder_core():
    """AT-13: build() core system ('intent') has _founder_core=False — no David node."""
    result = build(_state())
    core = result["systems"].get("intent", {})
    assert core.get("_founder_core") is False, (
        f"AT-13: core system must have _founder_core=False; got {core.get('_founder_core')!r}"
    )


if __name__ == "__main__":
    _tests = [
        ("AT-1",  test_slot_keys_reuses_elo_names_for_first_8),
        ("AT-2",  test_slot_keys_generates_beyond_elo_slots),
        ("AT-3",  test_slot_keys_no_silent_drop),
        ("AT-4",  test_mood_known_palette_word),
        ("AT-5",  test_mood_unknown_word_flags_missing),
        ("AT-6",  test_mood_empty_input_falls_back_to_neutral),
        ("AT-7",  test_valence_map_has_expected_keys),
        ("AT-8",  test_agent_index_maps_seat_to_agent),
        ("AT-9",  test_division_vortex_shape),
        ("AT-10", test_division_vortex_energy_in_range),
        ("AT-11", test_build_schema_and_required_keys),
        ("AT-12", test_build_divisions_in_equals_vortices_out),
        ("AT-13", test_build_no_founder_core),
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
    print(f"company_brain_state_writer   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
