"""
tests/test_emb051_simulation_vs_reality.py — WO-CAP-EMB-051.

VERBATIM SOURCE §51:
    This is non-negotiable.
    SIMULATED EXPERIENCE
    PHYSICAL EXPERIENCE
    eLo can remember both.
    But they must be labelled differently.
    Otherwise:
    I already know how this works.
    could mean:
    I tested it in Unity.
    when it has never physically done it.

Each line below maps to a test.
"""
from __future__ import annotations

import json

import pytest

from runtime.memory_origin import (
    MemoryOrigin,
    PHYSICAL_EMBODIMENTS,
    SIMULATED_EMBODIMENTS,
    can_claim_physical_experience,
    current_embodiment,
    is_auto_storable,
    is_physical,
    origin_for_embodiment,
)


# ── "SIMULATED EXPERIENCE / PHYSICAL EXPERIENCE" — both exist ─────────────────

def test_both_labels_exist():
    assert MemoryOrigin.SIMULATED_EXPERIENCE.value == "simulated_experience"
    assert MemoryOrigin.PHYSICAL_EXPERIENCE.value == "physical_experience"


def test_they_are_distinct_labels():
    assert MemoryOrigin.SIMULATED_EXPERIENCE is not MemoryOrigin.PHYSICAL_EXPERIENCE


# ── "eLo can remember both" ───────────────────────────────────────────────────

def test_both_are_remembered():
    """Neither is excluded from storage. The point is labelling, not erasure."""
    assert is_auto_storable(MemoryOrigin.SIMULATED_EXPERIENCE) is True
    assert is_auto_storable(MemoryOrigin.PHYSICAL_EXPERIENCE) is True


# ── "But they must be labelled differently" ───────────────────────────────────

@pytest.mark.parametrize("body", sorted(SIMULATED_EMBODIMENTS))
def test_every_simulated_body_labels_simulated(body):
    assert origin_for_embodiment(body) is MemoryOrigin.SIMULATED_EXPERIENCE


@pytest.mark.parametrize("body", sorted(PHYSICAL_EMBODIMENTS))
def test_every_physical_body_labels_physical(body):
    assert origin_for_embodiment(body) is MemoryOrigin.PHYSICAL_EXPERIENCE


def test_the_two_sets_do_not_overlap():
    assert not (SIMULATED_EMBODIMENTS & PHYSICAL_EMBODIMENTS)


def test_an_unknown_body_fails_safe_to_simulated():
    """
    Defaulting the other way would let a new body silently claim physical
    experience it has never had — the exact failure §51 forbids.
    """
    for unknown in ("some_new_body", "hologram", "", "???"):
        assert origin_for_embodiment(unknown) is MemoryOrigin.SIMULATED_EXPERIENCE


# ── "I already know how this works" must not mean "I tested it in Unity" ──────

def test_unity_cannot_claim_physical_experience():
    """The line the whole section exists to prevent."""
    unity = origin_for_embodiment("unity")
    assert can_claim_physical_experience(unity) is False
    assert is_physical(unity) is False


def test_only_a_physical_body_can_claim_physical_experience():
    claimable = [o for o in MemoryOrigin if can_claim_physical_experience(o)]
    assert claimable == [MemoryOrigin.PHYSICAL_EXPERIENCE]


@pytest.mark.parametrize("origin", [
    MemoryOrigin.REAL_EXPERIENCE,
    MemoryOrigin.EPISODIC_TRACE,
    MemoryOrigin.CONSOLIDATED,
    MemoryOrigin.DREAM_SIMULATION,
    MemoryOrigin.DREAM_INSIGHT,
    MemoryOrigin.SELF_MODEL,
    MemoryOrigin.SEMANTIC,
    MemoryOrigin.SIMULATED_EXPERIENCE,
])
def test_nothing_else_may_claim_physical_experience(origin):
    assert can_claim_physical_experience(origin) is False


def test_a_dream_certainly_cannot_claim_it():
    assert can_claim_physical_experience(MemoryOrigin.DREAM_SIMULATION) is False
    assert can_claim_physical_experience(MemoryOrigin.DREAM_INSIGHT) is False


def test_the_guard_accepts_plain_strings_too():
    assert can_claim_physical_experience("physical_experience") is True
    assert can_claim_physical_experience("simulated_experience") is False
    assert can_claim_physical_experience("not_an_origin") is False


# ── The label comes from the live body, not a declaration ─────────────────────

def test_embodiment_is_read_from_live_state(tmp_path, monkeypatch):
    state = tmp_path / "blender_state.json"
    state.write_text(json.dumps({"embodiment": "robot"}), encoding="utf-8")

    real_open = open

    def fake_open(path, *a, **k):
        if str(path).endswith("blender_state.json"):
            return real_open(state, *a, **k)
        return real_open(path, *a, **k)

    monkeypatch.setattr("builtins.open", fake_open)
    assert current_embodiment() == "robot"
    assert origin_for_embodiment() is MemoryOrigin.PHYSICAL_EXPERIENCE


def test_missing_state_falls_back_without_claiming_physical(monkeypatch):
    monkeypatch.setattr("builtins.open",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("gone")))
    assert can_claim_physical_experience(origin_for_embodiment()) is False


def test_the_live_body_is_currently_simulated():
    """Desktop today. If this ever fails, the robot is real — update the WO."""
    assert current_embodiment() in SIMULATED_EMBODIMENTS | PHYSICAL_EMBODIMENTS


# ── Existing behaviour preserved ──────────────────────────────────────────────

def test_the_dream_boundary_is_untouched():
    assert is_auto_storable(MemoryOrigin.DREAM_SIMULATION) is False
    assert is_auto_storable(MemoryOrigin.REAL_EXPERIENCE) is True


def test_wkg_still_accepts_the_new_origins():
    """record_claim() does MemoryOrigin(value) — new members must round-trip."""
    for origin in (MemoryOrigin.SIMULATED_EXPERIENCE, MemoryOrigin.PHYSICAL_EXPERIENCE):
        assert MemoryOrigin(origin.value) is origin
