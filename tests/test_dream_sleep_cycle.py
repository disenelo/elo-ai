"""
tests/test_dream_sleep_cycle.py — WO-DREAM-ENGINE-001 PHASE 1.

Exercises the multi-cycle sleep schedule directly (acceptance criteria 1 and 2).
No LLM, no server, no network.
"""
from __future__ import annotations

from faculties.dream import sleep_cycle as sc


def test_schedule_has_five_cycles_three_phases_each():
    schedule = sc.build_schedule()
    assert len(schedule) == 15
    assert sorted({p.cycle_number for p in schedule}) == [1, 2, 3, 4, 5]
    for n in range(1, 6):
        phases = [p.phase for p in schedule if p.cycle_number == n]
        assert phases[0] == "nrem"
        assert phases[2] == "rem"


def test_cycles_1_to_3_go_deep_4_and_5_go_light():
    schedule = sc.build_schedule()
    middles = {p.cycle_number: p.phase for p in schedule if p.phase in ("deep", "light")}
    assert middles == {1: "deep", 2: "deep", 3: "deep", 4: "light", 5: "light"}


def test_rem_duration_grows_each_cycle_10min_to_40min():
    rems = sc.rem_phases()
    durations = [p.rem_duration_s for p in rems]
    assert durations == sorted(durations)
    assert durations == [600, 1050, 1500, 1950, 2400]
    assert durations[0] == 10 * 60      # cycle 1 REM ~10 min
    assert durations[-1] == 40 * 60     # cycle 5 REM ~40 min
    assert rems[-1].long_rem is True
    assert [r.long_rem for r in rems[:-1]] == [False] * 4


def test_rem_intensity_rises_monotonically_to_one():
    intensities = [p.dream_intensity for p in sc.rem_phases()]
    assert intensities == sorted(intensities)
    assert intensities[-1] == 1.00
    assert intensities[0] < 0.25        # cycle 1 REM stays near fragmented memory


def test_deep_sleep_dreams_less_than_nrem_and_rem_in_same_cycle():
    schedule = sc.build_schedule()
    c1 = {p.phase: p.dream_intensity for p in schedule if p.cycle_number == 1}
    assert c1["deep"] < c1["nrem"] < c1["rem"]


def test_intensity_is_clamped_to_unit_range():
    for n in (0, 1, 3, 5, 99):
        for phase in ("nrem", "deep", "light", "rem"):
            v = sc.intensity_for(n, phase)
            assert 0.0 <= v <= 1.0


def test_intensity_labels_match_canonical_scale():
    assert sc.intensity_label(1.00) == "maximum surreal / emotional synthesis"
    assert sc.intensity_label(0.50) == "associative dream"
    assert sc.intensity_label(0.02) == "waking residue"


def test_content_band_weighting():
    assert sc.content_band(1) == "early"
    assert sc.content_band(2) == "early"
    assert sc.content_band(3) == "middle"
    assert sc.content_band(4) == "late"
    assert sc.content_band(5) == "late"


def test_state_machine_advances_through_every_phase_then_stops():
    machine = sc.SleepCycle()
    assert machine.current() is None
    seen = list(machine)
    assert len(seen) == 15
    assert machine.is_complete
    assert machine.advance() is None


def test_state_fields_are_the_three_unity_reads():
    machine = sc.SleepCycle()
    machine.advance()
    fields = machine.state_fields()
    assert set(fields) == {"dream_cycle", "dream_phase", "dream_intensity"}
    assert fields["dream_cycle"] == 1
    assert fields["dream_phase"] == "nrem"


def test_short_sleep_truncates_and_never_reaches_late_band():
    schedule = sc.build_schedule(cycles=2)
    assert len(schedule) == 6
    assert {p.content_band for p in schedule} == {"early"}
    assert max(p.dream_intensity for p in schedule) < 1.0


def test_publish_is_best_effort_and_never_raises(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def boom(name, *args, **kwargs):
        if name == "blender_bridge.state_writer":
            raise ImportError("bridge unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", boom)
    assert sc.publish(sc.build_schedule()[0]) is False
    assert sc.publish(None) is False
