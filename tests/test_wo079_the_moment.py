"""
tests/test_wo079_the_moment.py — Acceptance tests for WO-079

Spec: WO-079 — The Situated Self Invariant / The Moment

  AT-1: compile() returns a well-formed dict with required fields
  AT-2: write() creates self/state/the_moment.json with correct schema
  AT-3: perch_fresh=True → surface_tier="verified"; False → "last-known"
  AT-4: pose_acked=True → pose_tier="verified"; False → "last-known"
  AT-5: situated_with_epistemic() returns [verified]/[last-known]/[live] tags
  AT-6: situated_with_epistemic() never asserts unverified state as verified
  AT-7: write() failure is silent — no exception propagated
  AT-8: py_compile clean on runtime/the_moment.py and server.py

Run: python3 tests/test_wo079_the_moment.py
"""
import sys, os, json, shutil, tempfile, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Minimal EloSelfState stand-in ─────────────────────────────────────────────

class _FakeState:
    embodiment = "desktop"
    pose = "sitting"
    surface = "bottom edge of Claude"
    location = "Claude"
    balance = "steady"
    size = {"height_cm": 18, "reach_cm": 30, "jump_cm": 30}
    available_actions = ["stand", "look", "wave"]
    current_action = "idle"
    locomotion_faculty_health = "OK"
    nearby_surfaces = ["VS Code top edge"]
    mood = 0.6
    curiosity = 0.8
    goal = ""
    last_updated = 0.0


import runtime.the_moment as _tm

_TMP = tempfile.mkdtemp(prefix="wo079_test_")
_orig_path = _tm._MOMENT_PATH
_tm._MOMENT_PATH = os.path.join(_TMP, "state", "the_moment.json")


def _read_moment() -> dict:
    with open(_tm._MOMENT_PATH, encoding="utf-8") as f:
        return json.load(f)


try:
    # ── AT-1: compile() shape ─────────────────────────────────────────────────
    try:
        m = _tm.compile(_FakeState())
        required = (
            "ts", "embodiment", "embodiment_tier", "pose", "pose_tier",
            "surface", "surface_tier", "balance", "size_cm",
            "available_actions", "current_action",
            "locomotion_health", "locomotion_tier",
            "capabilities", "capabilities_tier",
            "nearby_surfaces", "nearby_tier",
            "mood", "curiosity", "goal", "last_self_update",
        )
        missing = [k for k in required if k not in m]
        assert not missing, f"compile() missing fields: {missing}"
        assert m["embodiment"] == "desktop"
        assert m["pose"] == "sitting"
        ok(f"AT-1: compile() returns {len(required)}-field snapshot")
    except AssertionError as e:
        fail("AT-1", e)
    except Exception as e:
        fail("AT-1", e)

    # ── AT-2: write() creates JSON file ───────────────────────────────────────
    try:
        _tm.write(_FakeState())
        assert os.path.exists(_tm._MOMENT_PATH), "the_moment.json not created"
        m = _read_moment()
        assert "ts" in m and "pose" in m and "embodiment" in m
        ok(f"AT-2: write() created the_moment.json at {_tm._MOMENT_PATH}")
    except AssertionError as e:
        fail("AT-2", e)
    except Exception as e:
        fail("AT-2", e)

    # ── AT-3: perch_fresh flag → surface tier ─────────────────────────────────
    try:
        m_fresh  = _tm.compile(_FakeState(), perch_fresh=True)
        m_stale  = _tm.compile(_FakeState(), perch_fresh=False)
        assert m_fresh["surface_tier"]  == "verified",   f"expected verified, got {m_fresh['surface_tier']}"
        assert m_stale["surface_tier"]  == "last-known", f"expected last-known, got {m_stale['surface_tier']}"
        ok("AT-3: perch_fresh=True → surface_tier=verified; False → last-known")
    except AssertionError as e:
        fail("AT-3", e)
    except Exception as e:
        fail("AT-3", e)

    # ── AT-4: pose_acked flag → pose tier ─────────────────────────────────────
    try:
        m_acked   = _tm.compile(_FakeState(), pose_acked=True)
        m_unacked = _tm.compile(_FakeState(), pose_acked=False)
        assert m_acked["pose_tier"]   == "verified",   f"expected verified, got {m_acked['pose_tier']}"
        assert m_unacked["pose_tier"] == "last-known", f"expected last-known, got {m_unacked['pose_tier']}"
        ok("AT-4: pose_acked=True → pose_tier=verified; False → last-known")
    except AssertionError as e:
        fail("AT-4", e)
    except Exception as e:
        fail("AT-4", e)

    # ── AT-5: situated_with_epistemic() contains tier markers ─────────────────
    try:
        block_v = _tm.situated_with_epistemic(_FakeState(), perch_fresh=True, pose_acked=True)
        block_s = _tm.situated_with_epistemic(_FakeState(), perch_fresh=False, pose_acked=False)
        assert "[verified]" in block_v, "no [verified] tag in block when both fresh+acked"
        assert "[last-known]" in block_s, "no [last-known] tag in block when stale"
        assert "[live]" in block_v, "no [live] tag for capabilities"
        assert "[SITUATED SELF" in block_v, "missing SITUATED SELF header"
        ok(f"AT-5: epistemic tags present — [verified], [last-known], [live] all appear")
    except AssertionError as e:
        fail("AT-5", e)
    except Exception as e:
        fail("AT-5", e)

    # ── AT-6: stale state → NO [verified] on pose or surface ─────────────────
    try:
        block_stale = _tm.situated_with_epistemic(_FakeState(), perch_fresh=False, pose_acked=False)
        lines = block_stale.splitlines()
        pose_line    = next((l for l in lines if "pose:" in l), "")
        surface_line = next((l for l in lines if "where:" in l), "")
        assert "[verified]" not in pose_line, \
            f"pose line should NOT say [verified] when unacked: {pose_line!r}"
        assert "[verified]" not in surface_line, \
            f"surface line should NOT say [verified] when stale: {surface_line!r}"
        ok("AT-6: unverified state never tagged [verified] — epistemic honesty holds")
    except AssertionError as e:
        fail("AT-6", e)
    except Exception as e:
        fail("AT-6", e)

    # ── AT-7: write() failure is silent ───────────────────────────────────────
    try:
        bad_path = _tm._MOMENT_PATH
        _tm._MOMENT_PATH = "/nonexistent/readonly/path/the_moment.json"
        try:
            _tm.write(_FakeState())  # should not raise
            ok("AT-7: write() to unwritable path → silent, no exception")
        except Exception as e_inner:
            fail("AT-7", f"write() raised on bad path: {e_inner}")
        finally:
            _tm._MOMENT_PATH = bad_path
    except Exception as e:
        fail("AT-7", e)

    # ── AT-8: py_compile clean ────────────────────────────────────────────────
    try:
        py_compile.compile("runtime/the_moment.py", doraise=True)
        py_compile.compile("server.py", doraise=True)
        ok("AT-8: py_compile clean on runtime/the_moment.py and server.py")
    except py_compile.PyCompileError as e:
        fail("AT-8", e)

finally:
    _tm._MOMENT_PATH = _orig_path
    shutil.rmtree(_TMP, ignore_errors=True)


print()
print("=" * 50)
print(f"WO-079 The Moment  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
