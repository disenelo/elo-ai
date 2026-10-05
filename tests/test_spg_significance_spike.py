"""
tests/test_spg_significance_spike.py — WO-SPG-SIGNIFICANCE-LIVE-001.

The WO's Part B ("wire live significance computation into SPG writes") is
already done: 15,213 of 15,255 live signals carry a computed 14-dimension
significance dict with 12 distinct `overall` values. Measured 2026-10-05,
so the WO's evidence line — "all 0.3 (backfill)" — is stale. The 984 rows
that ARE exactly 0.3 are the old backfill, not new writes.

What the measurement found instead: the SPG significance-spike tap has never
fired. Across the live log and its backup, 29,104 records:

    relationship_shift  14517
    memory_write        14503
    continuity_link        84
    significance_spike      0      <-- never, not once

    highest `overall` ever recorded : 0.3    (the backfill constant)
    highest COMPUTED value          : 0.042
    threshold                       : 0.6

Unreachable by construction. Each dimension already has its _WEIGHTS entry
applied, and `overall` is the MEAN of those weighted values, so the ceiling is
~0.09 even with every dimension maxed. 0.6 was written for an unweighted mean.

The threshold is NOT changed here — it is an [ESTIMATE], and the faculty says
those are D-gated to David L3 (SP-29). Picking the number is the ruling that
gate exists for.
"""
from __future__ import annotations

import pytest

import runtime.significance_faculty as sf


# ── debt register ───────────────────────────────────────────────────────────

def test_the_spike_tap_is_still_unreachable():
    """
    A TRIPWIRE, not a goal. This passes while the tap is dead and FAILS the
    moment SP-29 lands a threshold the weights can reach — which is when
    someone should come back here, delete this test, and check that spikes
    actually start appearing in data/spg_signals.jsonl.

    Dead and announced is better than dead and silent: audit_body_relay spent
    weeks reporting health for the same reason.
    """
    assert sf.SPIKE_THRESHOLD > sf.MAX_REACHABLE_OVERALL, (
        "the spike threshold is now reachable — SP-29 has presumably been "
        "ruled. Remove this tripwire and verify significance_spike signals "
        "appear in the live log."
    )


def test_the_ceiling_is_computed_from_the_weights_not_hardcoded():
    """A weight ruling must move the ceiling on its own."""
    original = dict(sf._WEIGHTS)
    try:
        for k in sf._WEIGHTS:
            sf._WEIGHTS[k] = 1.0
        recomputed = round(
            sum(min(1.0, w) for w in sf._WEIGHTS.values())
            / (len(sf._WEIGHTS) + 1), 4
        )
        assert recomputed > sf.MAX_REACHABLE_OVERALL
    finally:
        sf._WEIGHTS.clear()
        sf._WEIGHTS.update(original)


# ── the mechanism itself works; only the number is wrong ────────────────────

def test_the_tap_fires_once_the_threshold_is_reachable(monkeypatch):
    """
    Proves the wire is sound, so the D-gate is the only thing standing between
    this and live spikes. Without this, "unreachable" could be hiding a second
    defect in the tap itself.
    """
    logged: list = []

    class _Cap:
        def log(self, signal_type, **kw):
            logged.append((signal_type, kw))

    import memory.spg_capture as cap
    monkeypatch.setattr(cap, "get_capture", lambda: _Cap())
    monkeypatch.setattr(sf, "SPIKE_THRESHOLD", -1.0)   # anything clears it

    sf.compute_significance(
        {"any_change": True, "gaze_changed": True, "position_changed": True},
        {},
        text_input="this changed everything about how the seams work",
    )

    assert any(t == "significance_spike" for t, _ in logged), (
        "the tap did not fire even with the threshold removed — the defect "
        "is in the wire, not only in the number"
    )


def test_a_normal_turn_does_not_spike(monkeypatch):
    logged: list = []

    class _Cap:
        def log(self, signal_type, **kw):
            logged.append(signal_type)

    import memory.spg_capture as cap
    monkeypatch.setattr(cap, "get_capture", lambda: _Cap())

    sf.compute_significance({"any_change": False}, {}, text_input="ok")

    assert "significance_spike" not in logged
