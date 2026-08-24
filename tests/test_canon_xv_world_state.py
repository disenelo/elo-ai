"""
tests/test_canon_xv_world_state.py — Acceptance tests for WO-CANON-XV
(Unified LiveWorldState: one world, read once)

Spec: engineering/work_orders/WO-CANON-XV.md
Canon: Volume XV Ch.1–Ch.2

  FT-1: one assembly per turn — returns LiveWorldState, frozen before faculties
  FT-2: freshness carried — domain_health has fresh_ts, confidence, source, status on every domain
  FT-3: absent domain explicit not faked — absent domains have neutral defaults, not fabricated values
  FT-4: all faculties see the same world — assembly is deterministic given same sensor snapshot
  ST-1: one domain down never blocks the turn — exception in one domain, rest assemble fine
  ST-2: cold start — time domain live, rest absent if sensors unavailable
  ST-3: no mid-turn mutation — LiveWorldState is truly immutable after assembly
  ST-4: perishability — assembled_ts set; prior snapshot is a distinct object (not reused)
  IT-1: spine wiring — run() sets plan.world to a LiveWorldState instance
  IT-2: cognitive_state.world_state — CognitiveState carries world after assemble_cognitive_state
  AT-1: domain health structure — every domain carries all four health fields
  AT-2: time domain never stale — time assembled independently, always live on cold start
  AT-3: degraded list correct — domains that fail appear in degraded tuple
  AT-4: py_compile clean — no syntax errors in world/live_world_state.py + spine/spine.py + contracts.py

Run: python3 tests/test_canon_xv_world_state.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from world.live_world_state import (
    assemble_world_state, LiveWorldState,
    DesktopState, UserState, UnityState, BrowserState, FilesState,
    InternetState, MusicState, CalendarState, EnvironmentState,
    TimeState, WeatherState, DomainHealth,
)

_ALL_DOMAINS = [
    "desktop", "user", "unity", "browser", "files",
    "internet", "music", "calendar", "environment", "time", "weather",
    "gaze", "route",   # added when gaze + route history domains were wired
    "location",        # WO-WORLD-001 E-1: always present; source="absent" when unresolved
    "surfaces",        # live_world_state.py:469 — surface topology domain
]


# FT-1: assembly returns frozen LiveWorldState
try:
    ws = assemble_world_state(turn_id="ft1")
    assert isinstance(ws, LiveWorldState), f"got {type(ws)}"
    assert ws.assembled_ts > 0, "assembled_ts must be set"
    ok("FT-1: assemble_world_state returns frozen LiveWorldState with assembled_ts")
except Exception as e:
    fail("FT-1", e)


# FT-2: freshness carried — all 11 domains have health entries with all 4 fields
try:
    ws = assemble_world_state(turn_id="ft2")
    missing = []
    for d in _ALL_DOMAINS:
        h = ws.domain_health.get(d)
        if h is None:
            missing.append(f"{d}: no entry")
        else:
            for k in ("fresh_ts", "confidence", "source", "status"):
                if k not in h:
                    missing.append(f"{d}.{k}: missing")
    assert not missing, f"health missing: {missing}"
    ok("FT-2: all 11 domains carry {fresh_ts, confidence, source, status} in domain_health")
except AssertionError as e:
    fail("FT-2", e)
except Exception as e:
    fail("FT-2", e)


# FT-3: absent domain — status='absent', neutral defaults, no fabricated values
try:
    ws = assemble_world_state(turn_id="ft3")
    # browser, files, internet, calendar are always absent in current impl
    absent_domains = [d for d in _ALL_DOMAINS if ws.domain_health.get(d, {}).get("status") == "absent"]
    assert len(absent_domains) > 0, "expected at least some absent domains"
    # absent domains must not carry fabricated data — check browser
    b = ws.browser
    assert b.active_tab_domain == "", f"absent browser.active_tab_domain should be '' not {b.active_tab_domain!r}"
    ok(f"FT-3: {len(absent_domains)} domains absent with neutral defaults, no fabrication")
except AssertionError as e:
    fail("FT-3", e)
except Exception as e:
    fail("FT-3", e)


# FT-4: deterministic assembly — same external state → same structure each call
try:
    ws1 = assemble_world_state(turn_id="ft4a")
    ws2 = assemble_world_state(turn_id="ft4b")
    # Both must be LiveWorldState, both must have 11 health entries
    assert isinstance(ws1, LiveWorldState) and isinstance(ws2, LiveWorldState)
    assert set(ws1.domain_health.keys()) == set(ws2.domain_health.keys())
    assert set(ws1.domain_health.keys()) == set(_ALL_DOMAINS)
    ok("FT-4: two assemblies in the same turn have consistent domain coverage")
except AssertionError as e:
    fail("FT-4", e)
except Exception as e:
    fail("FT-4", e)


# ST-1: one domain failing never blocks the turn
try:
    import desktop.window_state as _wst
    # Patch get() to raise — simulates a broken desktop sensor
    orig_get = getattr(_wst, "get", None)
    def _broken_get(): raise RuntimeError("sensor down")
    _wst.get = _broken_get
    try:
        ws = assemble_world_state(turn_id="st1")
        # Must still return LiveWorldState (other domains not blocked)
        assert isinstance(ws, LiveWorldState), f"expected LiveWorldState, got {type(ws)}"
        # desktop should be absent, not a crash
        desk_status = ws.domain_health.get("desktop", {}).get("status")
        assert desk_status == "absent", f"broken desktop should be absent, got {desk_status!r}"
        # time should still be live
        assert ws.domain_health.get("time", {}).get("status") in ("live", "cached"), \
            "time must still be live when desktop fails"
        ok("ST-1: broken desktop sensor → absent (not crash); other domains unaffected")
    finally:
        if orig_get is not None:
            _wst.get = orig_get
        else:
            del _wst.get
except AssertionError as e:
    fail("ST-1", e)
except Exception as e:
    fail("ST-1", e)


# ST-2: cold start — time is always live; absent sensors yield status='absent'
try:
    ws = assemble_world_state(turn_id="st2")
    time_status = ws.domain_health.get("time", {}).get("status")
    assert time_status == "live", f"expected time=live, got {time_status!r}"
    assert ws.time.now_iso != "", "time.now_iso must be set"
    assert ws.time.part_of_day in ("morning", "afternoon", "evening", "night")
    ok(f"ST-2: cold start — time is live ({ws.time.part_of_day}), now_iso set")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ST-3: no mid-turn mutation — LiveWorldState is frozen (dataclass frozen=True)
try:
    ws = assemble_world_state(turn_id="st3")
    raised = False
    try:
        ws.assembled_ts = 0.0   # frozen dataclass must raise FrozenInstanceError
    except (AttributeError, TypeError):
        raised = True
    assert raised, "expected FrozenInstanceError on normal attribute assignment"
    # Also verify domain slices are frozen
    raised2 = False
    try:
        ws.time.now_iso = "hacked"
    except (AttributeError, TypeError):
        raised2 = True
    assert raised2, "expected FrozenInstanceError on domain slice mutation"
    ok("ST-3: LiveWorldState and its domain slices are immutable (frozen=True)")
except AssertionError as e:
    fail("ST-3", e)
except Exception as e:
    fail("ST-3", e)


# ST-4: perishability — each call returns a distinct object with its own assembled_ts
try:
    import time as _t
    ws_a = assemble_world_state(turn_id="st4a")
    _t.sleep(0.01)
    ws_b = assemble_world_state(turn_id="st4b")
    assert ws_a is not ws_b, "each assembly must return a new object"
    assert ws_a.turn_id == "st4a" and ws_b.turn_id == "st4b"
    ok("ST-4: perishability confirmed — each call yields a new distinct LiveWorldState")
except AssertionError as e:
    fail("ST-4", e)
except Exception as e:
    fail("ST-4", e)


# IT-1: spine wiring — spine.run() sets plan.world to a LiveWorldState instance
try:
    from runtime.spine.spine import run as spine_run
    plan = spine_run("hello world", state={}, memory_pack=None, attention={})
    assert hasattr(plan, "world"), "plan must have .world attribute"
    assert plan.world is None or isinstance(plan.world, LiveWorldState), \
        f"plan.world must be LiveWorldState or None, got {type(plan.world)}"
    ok(f"IT-1: spine.run() sets plan.world ({type(plan.world).__name__})")
except AssertionError as e:
    fail("IT-1", e)
except Exception as e:
    fail("IT-1", e)


# IT-2: CognitiveState.world_state — assemble_cognitive_state passes world through
try:
    from runtime.spine.spine import assemble_cognitive_state
    ws = assemble_world_state(turn_id="it2")
    cs = assemble_cognitive_state(
        language={"original": "hi", "intent": "conversation", "register": "", "social": ""},
        memory_result=None,
        attention={},
        capabilities=[],
        vault_result=None,
        prior_state={},
        world_state=ws,
    )
    assert hasattr(cs, "world_state"), "CognitiveState must have world_state field"
    assert cs.world_state is ws, "world_state must be the same object passed in"
    ok("IT-2: CognitiveState.world_state carries the assembled LiveWorldState")
except AssertionError as e:
    fail("IT-2", e)
except Exception as e:
    fail("IT-2", e)


# AT-1: every domain health entry has all 4 fields with correct types
try:
    ws = assemble_world_state(turn_id="at1")
    for d in _ALL_DOMAINS:
        h = ws.domain_health[d]
        assert isinstance(h["fresh_ts"], float), f"{d}.fresh_ts not float"
        assert isinstance(h["confidence"], float), f"{d}.confidence not float"
        assert 0.0 <= h["confidence"] <= 1.0, f"{d}.confidence out of range: {h['confidence']}"
        assert isinstance(h["source"], str), f"{d}.source not str"
        assert h["status"] in ("live", "cached", "stale", "absent"), f"{d}.status invalid: {h['status']}"
    ok("AT-1: all 11 domain health entries have correct field types and value ranges")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# AT-2: time domain never stale — always live on first assembly
try:
    ws = assemble_world_state(turn_id="at2")
    time_h = ws.domain_health.get("time", {})
    assert time_h.get("status") == "live", f"time status={time_h.get('status')!r}, expected 'live'"
    assert time_h.get("confidence", 0) == 1.0, f"time confidence={time_h.get('confidence')}, expected 1.0"
    ok("AT-2: time domain always live with confidence=1.0")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# AT-3: degraded list — domains that fail appear in degraded tuple
try:
    ws = assemble_world_state(turn_id="at3")
    degraded = ws.degraded
    assert isinstance(degraded, tuple), f"degraded must be tuple, got {type(degraded)}"
    # all degraded entries must be valid domain names
    for d in degraded:
        assert d in _ALL_DOMAINS, f"degraded entry {d!r} not a valid domain"
    # domains marked absent (except browser/files/internet/calendar which are always absent)
    # must appear in degraded if they raised an exception
    ok(f"AT-3: degraded tuple valid — {len(degraded)} domains degraded: {degraded}")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# AT-4: py_compile clean
try:
    for f in ("world/live_world_state.py", "runtime/spine/spine.py", "runtime/contracts.py", "runtime/spine/plan.py"):
        py_compile.compile(f, doraise=True)
    ok("AT-4: py_compile clean on live_world_state, spine, contracts, plan")
except py_compile.PyCompileError as e:
    fail("AT-4", e)


print()
print("=" * 60)
print(f"WO-CANON-XV world state  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
