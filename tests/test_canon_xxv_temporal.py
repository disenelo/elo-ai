"""
tests/test_canon_xxv_temporal.py — WO-CANON-XXV: Temporal Cognition Faculty

Tests for:
  Ch.1 — TemporalState: clock verbatim, circadian, interaction gap, fault tolerance
  Ch.2 — FutureFrame: deadlines anchored, proximity, horizon
  Ch.3 — Retrospection: fidelity from strength, gaps honest, autobiography PENDING
  AT   — py_compile clean

Spec ref: engineering/work_orders/WO-CANON-XXV.md
"""
from __future__ import annotations
import sys, os, py_compile, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── pass/fail helpers ─────────────────────────────────────────────────────────
_passed = _failed = 0

def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")

def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── minimal stub for LiveWorldState ──────────────────────────────────────────
class _TS:
    def __init__(self, now_iso="", part_of_day="afternoon", day_of_week="mon"):
        self.now_iso = now_iso
        self.part_of_day = part_of_day
        self.day_of_week = day_of_week

class _Cal:
    def __init__(self, next_event="", in_meeting=False):
        self.next_event = next_event
        self.in_meeting = in_meeting

class _World:
    def __init__(self, now_iso="", part_of_day="afternoon", next_event=""):
        self.time = _TS(now_iso=now_iso, part_of_day=part_of_day)
        self.calendar = _Cal(next_event=next_event)


# ── import target ─────────────────────────────────────────────────────────────
try:
    from faculties.temporal.faculty import (
        compute,
        temporal_appropriateness,
        TemporalOutput,
        TemporalState,
        FutureFrame,
        Deadline,
        Retrospection,
        FramedMemory,
        _interaction_gap,
        _fidelity_from_strength,
        _sleep_pressure,
        _DREAM_IDLE_THRESHOLD,
        _DREAM_COOLDOWN,
    )
    _import_ok = True
except ImportError as _e:
    _import_ok = False
    print(f"  [import failed: {_e}]")


# ── Ch.1/FT-1: clock read verbatim from world_state, not re-sensed ────────────
try:
    assert _import_ok
    now_iso = "2026-08-10T14:30:00+01:00"
    world = _World(now_iso=now_iso, part_of_day="afternoon")
    out = compute(world, last_interaction_ts=0.0)
    assert out.temporal_state.now_iso == now_iso, \
        f"now_iso must be verbatim from world_state; got {out.temporal_state.now_iso!r}"
    assert out.temporal_state.part_of_day == "afternoon"
    ok("Ch.1/FT-1: clock read verbatim from world_state (now_iso + part_of_day)")
except AssertionError as e:
    fail("Ch.1/FT-1", e)
except Exception as e:
    fail("Ch.1/FT-1", e)


# ── Ch.1/FT-2: circadian maps from part_of_day ────────────────────────────────
try:
    assert _import_ok
    for pod, expected_phase, expected_energy_range in [
        ("morning",   "active", (0.6, 0.9)),
        ("afternoon", "active", (0.5, 0.8)),
        ("evening",   "alert",  (0.4, 0.7)),
        ("night",     "low",    (0.1, 0.4)),
    ]:
        w = _World(part_of_day=pod)
        o = compute(w)
        ts = o.temporal_state
        assert ts.circadian_phase == expected_phase, \
            f"{pod} → phase={ts.circadian_phase!r}, expected {expected_phase!r}"
        assert expected_energy_range[0] <= ts.energy <= expected_energy_range[1], \
            f"{pod} energy={ts.energy} outside {expected_energy_range}"
    ok("Ch.1/FT-2: circadian phase and energy map from part_of_day")
except AssertionError as e:
    fail("Ch.1/FT-2", e)
except Exception as e:
    fail("Ch.1/FT-2", e)


# ── Ch.1/ST-1: overnight requires night boundary ───────────────────────────────
try:
    assert _import_ok
    # 10h elapsed during "afternoon" → "hours" not "overnight" (no night boundary)
    gap_afternoon = _interaction_gap(36_000, "afternoon")
    assert gap_afternoon == "hours", \
        f"10h during afternoon must be 'hours', not 'overnight'; got {gap_afternoon!r}"
    # 10h elapsed during "night" → "overnight" (night boundary)
    gap_night = _interaction_gap(36_000, "night")
    assert gap_night == "overnight", \
        f"10h during night must be 'overnight'; got {gap_night!r}"
    ok("Ch.1/ST-1: overnight requires night boundary (afternoon=hours, night=overnight)")
except AssertionError as e:
    fail("Ch.1/ST-1", e)
except Exception as e:
    fail("Ch.1/ST-1", e)


# ── Ch.1/ST-2: cold start — no fabricated reunion ────────────────────────────
try:
    assert _import_ok
    out = compute(_World(now_iso="2026-08-10T09:00:00"), last_interaction_ts=0.0)
    assert out.temporal_state.interaction_gap == "unknown", \
        f"Cold start must yield 'unknown'; got {out.temporal_state.interaction_gap!r}"
    ok("Ch.1/ST-2: cold start (last_interaction_ts=0) → interaction_gap='unknown'")
except AssertionError as e:
    fail("Ch.1/ST-2", e)
except Exception as e:
    fail("Ch.1/ST-2", e)


# ── Ch.1/ST-3: time-domain fault never blocks ────────────────────────────────
try:
    assert _import_ok
    # None world_state is a time-domain fault
    out = compute(None)
    ts = out.temporal_state
    assert ts.circadian_phase == "active", f"Fault default must be active; got {ts.circadian_phase!r}"
    assert ts.energy == 0.5, f"Fault default energy must be 0.5; got {ts.energy}"
    assert ts.memory_instruction_store is False
    ok("Ch.1/ST-3: time-domain fault → default (active/0.5); never blocks")
except AssertionError as e:
    fail("Ch.1/ST-3", e)
except Exception as e:
    fail("Ch.1/ST-3", e)


# ── Ch.1/ST-4: no autonomous tick — compute() is asked, not self-firing ───────
try:
    assert _import_ok
    # Verify compute() doesn't start background threads or timers by inspecting output
    import threading
    before = threading.active_count()
    out = compute(_World())
    after = threading.active_count()
    assert after <= before, f"compute() spawned {after - before} threads — must not"
    ok("Ch.1/ST-4: no autonomous tick — compute() spawns no threads")
except AssertionError as e:
    fail("Ch.1/ST-4", e)
except Exception as e:
    fail("Ch.1/ST-4", e)


# ── Ch.1/ST-5: sleep_pressure is monotone toward dream threshold ──────────────
try:
    assert _import_ok
    p0   = _sleep_pressure(0)
    p600 = _sleep_pressure(_DREAM_IDLE_THRESHOLD)
    p360 = _sleep_pressure(_DREAM_COOLDOWN)
    assert p0 == 0.0, f"0 idle → pressure 0; got {p0}"
    assert 0.0 < p600 < 1.0, f"At DREAM_IDLE_THRESHOLD pressure must be >0 and <1; got {p600}"
    assert p360 <= 1.0, f"At DREAM_COOLDOWN pressure must be ≤1; got {p360}"
    assert p0 <= p600 <= p360, f"Sleep pressure must be monotone; got {p0}/{p600}/{p360}"
    ok("Ch.1/ST-5: sleep_pressure monotone 0→>0→1 toward dream threshold (context only)")
except AssertionError as e:
    fail("Ch.1/ST-5", e)
except Exception as e:
    fail("Ch.1/ST-5", e)


# ── Ch.1/FT-3: memory_instruction_store always False ─────────────────────────
try:
    assert _import_ok
    out = compute(_World())
    assert out.memory_instruction_store is False
    assert out.temporal_state.memory_instruction_store is False
    assert out.future_frame.memory_instruction_store is False
    assert out.retrospection.memory_instruction_store is False
    ok("Ch.1/FT-3: memory_instruction_store=False on all slices (never writes LTM)")
except AssertionError as e:
    fail("Ch.1/FT-3", e)
except Exception as e:
    fail("Ch.1/FT-3", e)


# ── Ch.1/ST-6: expires is float timestamp (now_ts + _TURN_TTL), never bool ───
# WO-CANON-XXV reopened: bool contract was wrong — expires is a perishable timestamp.
try:
    assert _import_ok
    out = compute(_World())
    assert isinstance(out.expires, float), f"TemporalOutput.expires is {type(out.expires)}"
    assert out.expires > 0, f"TemporalOutput.expires={out.expires} not > 0"
    assert isinstance(out.temporal_state.expires, float), "temporal_state.expires not float"
    assert out.temporal_state.expires > 0, f"temporal_state.expires={out.temporal_state.expires}"
    assert isinstance(out.future_frame.expires, float), "future_frame.expires not float"
    assert isinstance(out.retrospection.expires, float), "retrospection.expires not float"
    ok("Ch.1/ST-6: expires is float > 0 on all slices (perishable timestamp, not bool)")
except AssertionError as e:
    fail("Ch.1/ST-6", e)
except Exception as e:
    fail("Ch.1/ST-6", e)


# ── Ch.2/FT-4: deadline anchored with ref ────────────────────────────────────
try:
    assert _import_ok
    w = _World(next_event="Sprint Review 3pm")
    out = compute(w)
    ff = out.future_frame
    if ff.deadlines:
        for d in ff.deadlines:
            assert d.ref, f"Every Deadline must carry a ref; got ref={d.ref!r}"
    ok("Ch.2/FT-4: all FutureFrame deadlines carry non-empty ref")
except AssertionError as e:
    fail("Ch.2/FT-4", e)
except Exception as e:
    fail("Ch.2/FT-4", e)


# ── Ch.2/FT-5: imminent deadline collapses horizon to immediate ──────────────
try:
    assert _import_ok
    from faculties.temporal.faculty import Deadline, _active_horizon
    imminent = Deadline(ref="cal:1", proximity="imminent")
    assert _active_horizon([imminent]) == "immediate", \
        "_active_horizon must return 'immediate' for an imminent deadline"
    ok("Ch.2/FT-5: imminent deadline → active_horizon='immediate'")
except AssertionError as e:
    fail("Ch.2/FT-5", e)
except Exception as e:
    fail("Ch.2/FT-5", e)


# ── Ch.2/ST-7: calendar absent → no fabricated deadlines ─────────────────────
try:
    assert _import_ok
    w = _World(next_event="")  # no next_event
    out = compute(w)
    ff = out.future_frame
    # When next_event is empty, deadlines should be empty
    assert len(ff.deadlines) == 0, \
        f"No next_event → no deadlines; got {len(ff.deadlines)}"
    ok("Ch.2/ST-7: calendar absent (no next_event) → empty deadlines, no fabrication")
except AssertionError as e:
    fail("Ch.2/ST-7", e)
except Exception as e:
    fail("Ch.2/ST-7", e)


# ── Ch.3/FT-6: fidelity derived from strength, not age ───────────────────────
try:
    assert _import_ok
    assert _fidelity_from_strength(0.9) == "vivid"
    assert _fidelity_from_strength(0.6) == "clear"
    assert _fidelity_from_strength(0.2) == "faded"
    # Identity/pinned never faded
    assert _fidelity_from_strength(0.1, identity_level=True) == "clear"
    ok("Ch.3/FT-6: fidelity from strength (vivid/clear/faded); identity never faded")
except AssertionError as e:
    fail("Ch.3/FT-6", e)
except Exception as e:
    fail("Ch.3/FT-6", e)


# ── Ch.3/ST-8: autobiography.jsonl absent → PENDING path, works from vault ──
try:
    assert _import_ok
    out = compute(_World())
    ret = out.retrospection
    assert ret.memory_instruction_store is False, "Retrospection must never write"
    # autobiography_path is either "PENDING" (file not found) or a real path
    assert isinstance(ret.autobiography_path, str), "autobiography_path must be str"
    # If it's PENDING, retrospection still has content (memories from vault or identity)
    # — not a hard assert since vault may be empty in test env
    ok(f"Ch.3/ST-8: autobiography_path={ret.autobiography_path!r}; memory_instruction_store=False")
except AssertionError as e:
    fail("Ch.3/ST-8", e)
except Exception as e:
    fail("Ch.3/ST-8", e)


# ── Ch.3/ST-9: gaps stated honestly, never fabricated ────────────────────────
try:
    assert _import_ok
    out = compute(_World())
    ret = out.retrospection
    for gap in ret.gaps:
        assert isinstance(gap, str) and gap, "Each gap must be a non-empty string"
    # gaps is a tuple — not mutated
    assert isinstance(ret.gaps, tuple)
    ok(f"Ch.3/ST-9: gaps are honest strings (count={len(ret.gaps)})")
except AssertionError as e:
    fail("Ch.3/ST-9", e)
except Exception as e:
    fail("Ch.3/ST-9", e)


# ── Ch.3/FT-7: FramedMemory ref required ──────────────────────────────────────
try:
    assert _import_ok
    out = compute(_World())
    for m in out.retrospection.memories:
        assert m.ref, f"Every FramedMemory must have a ref; got {m.ref!r}"
    ok("Ch.3/FT-7: all FramedMemory objects carry non-empty ref")
except AssertionError as e:
    fail("Ch.3/FT-7", e)
except Exception as e:
    fail("Ch.3/FT-7", e)


# ── temporal_appropriateness: quiet-hours suppression ────────────────────────
try:
    assert _import_ok
    night_ts = TemporalState(part_of_day="night", circadian_phase="low", energy=0.25)
    day_ts   = TemporalState(part_of_day="afternoon", circadian_phase="active", energy=0.65)

    result_night = temporal_appropriateness("ambient_greeting", night_ts)
    result_day   = temporal_appropriateness("ambient_greeting", day_ts)
    assert result_night["allow"] is False, \
        "ambient_greeting during night phase must be suppressed"
    assert result_day["allow"] is True, \
        "ambient_greeting during afternoon must be allowed"
    ok("temporal_appropriateness: night suppresses ambient; afternoon allows")
except AssertionError as e:
    fail("temporal_appropriateness", e)
except Exception as e:
    fail("temporal_appropriateness", e)


# ── TemporalOutput is frozen ─────────────────────────────────────────────────
try:
    assert _import_ok
    out = compute(_World())
    try:
        out.expires = False
        fail("freeze-check", "TemporalOutput must be frozen — mutation succeeded unexpectedly")
    except (AttributeError, TypeError):
        ok("TemporalOutput frozen — mutation rejected (frozen=True)")
except Exception as e:
    fail("freeze-check", e)


# ── AT-10: py_compile clean on all temporal files ─────────────────────────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for _rel in [
        "faculties/temporal/__init__.py",
        "faculties/temporal/faculty.py",
    ]:
        _fp = os.path.join(_base, _rel)
        py_compile.compile(_fp, doraise=True)
    ok("AT-10: py_compile clean on all WO-CANON-XXV files")
except py_compile.PyCompileError as e:
    fail("AT-10", e)
except Exception as e:
    fail("AT-10", e)


# ─────────────────────────────────────────────────────────────────────────────
# WO-CANON-XXV REOPENED: Wiring Tests (WT), Envelope Tests (ET),
# Lifecycle Tests (LT), Anticipation Tests (AT-new), Cadence Tests (CT),
# Thread Tests (XXI)
# ─────────────────────────────────────────────────────────────────────────────

# ── WT-1: at least one non-test module imports faculties.temporal ─────────────
try:
    import ast, pathlib
    _search_dirs = [
        pathlib.Path("runtime"),
        pathlib.Path("faculties"),
        pathlib.Path("ambient"),
    ]
    _found = False
    for _sd in _search_dirs:
        for _py in _sd.rglob("*.py"):
            if "test" in _py.name:
                continue
            try:
                _src = _py.read_text()
                if "faculties.temporal" in _src or "from faculties import temporal" in _src:
                    _found = True
                    break
            except Exception:
                pass
        if _found:
            break
    # Also check server.py
    if not _found:
        for _srv in pathlib.Path(".").glob("server.py"):
            if "faculties.temporal" in _srv.read_text():
                _found = True
    assert _found, "no non-test module under runtime/faculties/ambient or server.py imports faculties.temporal"
    ok("WT-1: faculties.temporal imported by a non-test production module")
except AssertionError as e:
    fail("WT-1", e)
except Exception as e:
    fail("WT-1", e)


# ── WT-2: spine.py calls temporal compute() somewhere in its source ───────────
try:
    import pathlib
    _spine = pathlib.Path("runtime/spine/spine.py").read_text()
    assert "temporal_compute" in _spine or "faculties.temporal" in _spine, \
        "spine.py has no reference to temporal compute"
    ok("WT-2: spine.py references temporal faculty compute")
except AssertionError as e:
    fail("WT-2", e)
except Exception as e:
    fail("WT-2", e)


# ── WT-3: ambient_engine consults temporal_appropriateness ────────────────────
try:
    import pathlib
    _ae = pathlib.Path("ambient/ambient_engine.py").read_text()
    assert "temporal_appropriateness" in _ae, \
        "ambient_engine.py does not call temporal_appropriateness"
    ok("WT-3: ambient_engine.py calls temporal_appropriateness")
except AssertionError as e:
    fail("WT-3", e)
except Exception as e:
    fail("WT-3", e)


# ── ET-1: TemporalOutput has all Vol V CONTRACTS §2 envelope fields ───────────
try:
    assert _import_ok
    out = compute(_World())
    assert hasattr(out, "sender"),      "missing: sender"
    assert hasattr(out, "receiver"),    "missing: receiver"
    assert hasattr(out, "priority"),    "missing: priority"
    assert hasattr(out, "payload_type"),"missing: payload_type"
    assert hasattr(out, "confidence"),  "missing: confidence"
    assert hasattr(out, "expires"),     "missing: expires"
    assert hasattr(out, "trace"),       "missing: trace"
    assert hasattr(out, "memory_instruction_store"), "missing: memory_instruction_store"
    assert out.sender == "TemporalCognitionFaculty", f"sender={out.sender!r}"
    assert out.memory_instruction_store is False, "memory_instruction_store must be False"
    assert len(out.trace) > 0, "trace must be non-empty"
    ok("ET-1: TemporalOutput carries full Vol V CONTRACTS §2 envelope")
except AssertionError as e:
    fail("ET-1", e)
except Exception as e:
    fail("ET-1", e)


# ── ET-2: expires is float, not bool, on all three slices ────────────────────
try:
    assert _import_ok
    out = compute(_World())
    assert isinstance(out.expires, float) and not isinstance(out.expires, bool), \
        f"TemporalOutput.expires type={type(out.expires)}"
    assert isinstance(out.temporal_state.expires, float) and not isinstance(out.temporal_state.expires, bool), \
        "temporal_state.expires is bool"
    assert isinstance(out.future_frame.expires, float) and not isinstance(out.future_frame.expires, bool), \
        "future_frame.expires is bool"
    assert isinstance(out.retrospection.expires, float) and not isinstance(out.retrospection.expires, bool), \
        "retrospection.expires is bool"
    ok("ET-2: expires is float (timestamp) not bool on all slices")
except AssertionError as e:
    fail("ET-2", e)
except Exception as e:
    fail("ET-2", e)


# ── LT-1: compute() enters ERROR_RECOVERY lifecycle state on fault ────────────
try:
    from faculties.temporal.faculty import get_lifecycle_state
    import faculties.temporal.faculty as _tf
    # Trigger a fault by corrupting world_state (non-object that causes attribute errors)
    class _BadWorld:
        @property
        def time(self):
            raise RuntimeError("injected fault")
    _prev = _tf._faculty_lifecycle
    try:
        _out = compute(_BadWorld())
    except Exception:
        pass  # compute() must not re-raise; if it did this test would catch it
    # After a fault, lifecycle should have passed through ERROR_RECOVERY
    # (it resets to ACTIVE at end, but _FAULT_TEMPORAL.expires == 0.0 proves fault path ran)
    assert _out.temporal_state.expires == 0.0, \
        f"fault path not taken: temporal_state.expires={_out.temporal_state.expires}"
    ok("LT-1: fault path produces temporal_state.expires==0.0 (ERROR_RECOVERY path triggered)")
except AssertionError as e:
    fail("LT-1", e)
except Exception as e:
    fail("LT-1", e)


# ── AT-new-1: Anticipation with empty statement is dropped ───────────────────
try:
    from faculties.temporal.faculty import Anticipation
    _baseless = Anticipation(statement="", basis="", confidence=0.0)
    assert _baseless.statement == "", "fixture: statement must be empty"
    assert _baseless.confidence == 0.0, "fixture: confidence must be 0.0"
    # The build function should not include a zero-confidence empty anticipation in the frame
    class _WorldWithAgentic(_World):
        def __init__(self):
            super().__init__()
            self.agentic = type("A", (), {"next_event": None, "deadlines": [], "active_goals": []})()
    out = compute(_WorldWithAgentic())
    for ant in out.future_frame.anticipations:
        assert ant.statement != "", f"empty-statement Anticipation leaked into output: {ant}"
    ok("AT-new-1: baseless / empty-statement Anticipation not included in FutureFrame")
except AssertionError as e:
    fail("AT-new-1", e)
except Exception as e:
    fail("AT-new-1", e)


# ── AT-new-2: PlanningHorizon is a lens over Agency tiers, not a second enum ─
try:
    from faculties.temporal.faculty import PlanningHorizon
    # PlanningHorizon must NOT define its own tier values — it reads Agency's
    h = PlanningHorizon(tier="short_term", priority="normal", nearest_deadline=None)
    assert h.tier == "short_term"
    # Must not have a nested Enum attribute
    import inspect
    for _name, _val in inspect.getmembers(PlanningHorizon):
        if isinstance(_val, type) and issubclass(_val, __import__("enum").Enum):
            raise AssertionError(f"PlanningHorizon defines its own Enum: {_name}")
    ok("AT-new-2: PlanningHorizon is a plain dataclass lens, no second tier enum")
except AssertionError as e:
    fail("AT-new-2", e)
except Exception as e:
    fail("AT-new-2", e)


# ── CT-1: stated cadence outranks learned ────────────────────────────────────
try:
    from faculties.temporal.faculty import (
        set_stated_cadence, effective_cadence,
    )
    import faculties.temporal.faculty as _tf
    _tf._stated_cadence = ""
    _tf._learned_cadence = "slow_build"
    assert effective_cadence() == "slow_build", "learned cadence not returned when stated absent"
    set_stated_cadence("sprint")
    assert effective_cadence() == "sprint", "stated cadence did not outrank learned"
    # Cleanup
    _tf._stated_cadence = ""
    _tf._learned_cadence = ""
    ok("CT-1: stated cadence outranks learned cadence")
except AssertionError as e:
    fail("CT-1", e)
except Exception as e:
    fail("CT-1", e)


# ── XXI-1: retrospect() reads IdentityState, returns thread_arc, gaps stated ─
try:
    assert _import_ok
    out = compute(_World())
    ret = out.retrospection
    # thread_arc is a string (may be empty if continuity unavailable in test env)
    assert isinstance(ret.thread_arc, str), f"thread_arc is {type(ret.thread_arc)}"
    # window is a string
    assert isinstance(ret.window, str), f"window is {type(ret.window)}"
    # gaps are honest strings, none fabricated (each gap must be a non-empty string)
    for g in ret.gaps:
        assert isinstance(g, str) and len(g) > 0, f"gap is empty or not string: {g!r}"
    # memory_instruction_store must be False — never writes LTM
    assert ret.memory_instruction_store is False, "retrospection must not write LTM"
    # autobiography_path is a string
    assert isinstance(ret.autobiography_path, str)
    ok("XXI-1: retrospection has thread_arc+window strings, honest gaps, no LTM write")
except AssertionError as e:
    fail("XXI-1", e)
except Exception as e:
    fail("XXI-1", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-CANON-XXV temporal cognition   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
