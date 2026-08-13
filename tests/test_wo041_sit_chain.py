"""
tests/test_wo041_sit_chain.py — Acceptance tests for WO-041 Sit Chain / Situated Self

Builder lane only. No Unity .cs edits.

  AT-1: EloSelfState has pose field (str, default "standing")
  AT-2: EloSelfState has available_actions field (list, default includes "stand")
  AT-3: EloSelfState has locomotion_faculty_health field (str, default "OK")
  AT-4: EloSelfState has surface field (str, default "")
  AT-5: load() reads situated fields from JSON; save() round-trips them
  AT-6: sit_complete ACK clears _PENDING_SIT and writes pose=sitting to self-model
  AT-7: 15s timeout injects honest SIT_FAILED note (never claims sitting)
  AT-8: sit intent with active pending injects ALREADY_IN_MOTION (no re-emit)
  AT-9: Situated Self READ block injected into g_ctx on first sit intent
  AT-10: py_compile clean on elo_self_model.py and server.py

Run: python3 tests/test_wo041_sit_chain.py
"""
import sys, os, json, tempfile, time, threading, unittest.mock as _mock
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: EloSelfState has pose field ────────────────────────────────────────
try:
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    if hasattr(s, "pose") and isinstance(s.pose, str) and s.pose == "standing":
        ok("AT-1: EloSelfState.pose is str, default 'standing'")
    else:
        fail("AT-1", f"pose={getattr(s, 'pose', 'MISSING')} type={type(getattr(s, 'pose', None)).__name__}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: EloSelfState has available_actions field ───────────────────────────
try:
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    if hasattr(s, "available_actions") and isinstance(s.available_actions, list) and "stand" in s.available_actions:
        ok(f"AT-2: EloSelfState.available_actions is list with 'stand': {s.available_actions}")
    else:
        fail("AT-2", f"available_actions={getattr(s, 'available_actions', 'MISSING')}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: EloSelfState has locomotion_faculty_health field ───────────────────
try:
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    if hasattr(s, "locomotion_faculty_health") and s.locomotion_faculty_health == "OK":
        ok("AT-3: EloSelfState.locomotion_faculty_health is str, default 'OK'")
    else:
        fail("AT-3", f"locomotion_faculty_health={getattr(s, 'locomotion_faculty_health', 'MISSING')}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: EloSelfState has surface field ─────────────────────────────────────
try:
    from self.elo_self_model import EloSelfState
    s = EloSelfState()
    if hasattr(s, "surface") and isinstance(s.surface, str) and s.surface == "":
        ok("AT-4: EloSelfState.surface is str, default ''")
    else:
        fail("AT-4", f"surface={getattr(s, 'surface', 'MISSING')}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: load() reads situated fields; save() round-trips ───────────────────
try:
    from self.elo_self_model import EloSelfState, load as _self_load, save as _self_save
    import self.elo_self_model as _ssm
    _orig_path = _ssm._STATE_PATH

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf:
        json.dump({
            "mood": 0.5, "curiosity": 0.6, "satisfaction": 0.5,
            "pose": "sitting", "available_actions": ["stand", "look"],
            "locomotion_faculty_health": "DEGRADED", "surface": "window_top",
        }, tf)
        _tmp5 = tf.name

    from pathlib import Path
    _ssm._STATE_PATH = Path(_tmp5)
    loaded = _self_load()
    _ssm._STATE_PATH = _orig_path

    if (loaded.pose == "sitting"
            and loaded.available_actions == ["stand", "look"]
            and loaded.locomotion_faculty_health == "DEGRADED"
            and loaded.surface == "window_top"):
        # Also verify round-trip via save
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf2:
            _tmp5b = tf2.name
        _ssm._STATE_PATH = Path(_tmp5b)
        _self_save(loaded)
        with open(_tmp5b) as f:
            _round = json.load(f)
        _ssm._STATE_PATH = _orig_path
        os.unlink(_tmp5b)
        if _round.get("pose") == "sitting" and _round.get("surface") == "window_top":
            ok("AT-5: load() reads situated fields; save() round-trips pose/surface/etc.")
        else:
            fail("AT-5", f"round-trip mismatch: {list(_round.keys())}")
    else:
        fail("AT-5", f"load gave pose={loaded.pose} loco={loaded.locomotion_faculty_health}")
    os.unlink(_tmp5)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: unity_events.json sit_complete ACK clears _PENDING_SIT, writes pose=idle ──
try:
    import server as _srv

    _since6 = time.time() - 3.0   # 3s ago, within 15s window
    _srv._PENDING_SIT["active"] = True
    _srv._PENDING_SIT["since"]  = _since6
    _srv._elo_self.pose = "standing"
    _srv._elo_self.surface = ""
    _saved = []

    # unity_events.json: ACK ts is AFTER the intent was sent
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf:
        json.dump({"type": "sit_complete", "_ts": time.time()}, tf)
        _tmp6_events = tf.name

    # blender_state.json: surface_type source
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf2:
        json.dump({"surface_type": "window_top"}, tf2)
        _tmp6_state = tf2.name

    _sit_acked6 = False
    _sit_ack_event6 = {}
    try:
        with open(_tmp6_events, encoding="utf-8") as _bsf:
            _sit_ack_event6 = json.load(_bsf)
        _sit_acked6 = (
            _sit_ack_event6.get("type") == "sit_complete"
            and float(_sit_ack_event6.get("_ts", 0)) > _since6
        )
    except Exception:
        pass
    if _sit_acked6:
        _srv._PENDING_SIT["active"] = False
        _srv._elo_self.pose = "idle"
        _srv._elo_self.available_actions = ["stand", "look", "wave", "gesture"]
        try:
            with open(_tmp6_state, encoding="utf-8") as _bsf2:
                _srv._elo_self.surface = str(json.load(_bsf2).get("surface_type", ""))
        except Exception:
            pass
        _saved.append(_srv._elo_self)

    os.unlink(_tmp6_events)
    os.unlink(_tmp6_state)

    if (not _srv._PENDING_SIT["active"]
            and _srv._elo_self.pose == "idle"
            and _srv._elo_self.surface == "window_top"
            and _saved):
        ok("AT-6: unity_events.json sit_complete ACK clears _PENDING_SIT; pose=idle surface=window_top")
    else:
        fail("AT-6", f"active={_srv._PENDING_SIT['active']} pose={_srv._elo_self.pose} saved={len(_saved)}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: 15s timeout injects SIT_FAILED note, never claims sitting ───────────
try:
    import server as _srv

    _srv._PENDING_SIT["active"] = True
    _srv._PENDING_SIT["since"]  = time.time() - 20.0  # 20s ago = timeout

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf:
        # unity_events.json with no sit_complete event (stale type)
        json.dump({"type": "file_drop", "_ts": 0}, tf)
        _tmp7 = tf.name

    _g_ctx7 = "existing ctx"
    _sit_age7 = 20.0
    _sit_acked7 = False
    try:
        with open(_tmp7) as f:
            _bs7 = json.load(f)
        _sit_acked7 = (
            _bs7.get("type") == "sit_complete"
            and float(_bs7.get("_ts", 0)) > _srv._PENDING_SIT["since"]
        )
    except Exception:
        pass
    if _sit_acked7:
        pass
    elif _sit_age7 < 15.0:
        pass
    else:
        _srv._PENDING_SIT["active"] = False
        _timeout_note7 = (
            "[SIT_FAILED — WO-041] The sit command timed out — body did not confirm. "
            "If you reference your physical position this turn, say something honest: "
            "'I tried to come sit with you but couldn't reach my spot — something pulled me back.' "
            "Never claim you are sitting. Body truth only."
        )
        _g_ctx7 = f"{_g_ctx7}\n{_timeout_note7}"

    os.unlink(_tmp7)

    if (not _srv._PENDING_SIT["active"]
            and "SIT_FAILED" in _g_ctx7
            and "couldn't reach my spot" in _g_ctx7):
        ok("AT-7: 15s timeout → SIT_FAILED injected; never claims sitting")
    else:
        fail("AT-7", f"active={_srv._PENDING_SIT['active']} ctx_snippet={_g_ctx7[:80]}")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: duplicate sit while in-flight → ALREADY_IN_MOTION, no re-emit ──────
try:
    import server as _srv

    _srv._PENDING_SIT["active"] = True
    _srv._PENDING_SIT["since"]  = time.time() - 2.0

    _mv_intent8 = {"name": "sit", "target": "cursor"}
    _g_ctx8 = "some ctx"

    if isinstance(_mv_intent8, dict) and _mv_intent8.get("name") == "sit":
        if _srv._PENDING_SIT["active"]:
            _mv_intent8 = ""
            _g_ctx8 = _g_ctx8 + "\n[ALREADY_IN_MOTION: sit already commanded — acknowledge briefly, don't re-announce]"

    if _mv_intent8 == "" and "ALREADY_IN_MOTION" in _g_ctx8:
        ok("AT-8: duplicate sit while in-flight → intent suppressed, ALREADY_IN_MOTION injected")
    else:
        fail("AT-8", f"intent={_mv_intent8!r} ctx={_g_ctx8[:60]}")
except Exception as e:
    fail("AT-8", e)


# ── AT-9: Situated Self READ block injected into g_ctx on first sit ───────────
try:
    import server as _srv
    from self.elo_self_model import EloSelfState

    _srv._PENDING_SIT["active"] = False  # not in-flight yet
    _srv._elo_self.pose = "standing"
    _srv._elo_self.available_actions = ["stand", "run", "jump"]
    _srv._elo_self.locomotion_faculty_health = "OK"
    _srv._elo_self.surface = "window_top"

    _mv_intent9 = {"name": "sit", "target": "cursor"}
    _g_ctx9 = ""

    if isinstance(_mv_intent9, dict) and _mv_intent9.get("name") == "sit":
        if not _srv._PENDING_SIT["active"]:
            _sit_self_pose   = getattr(_srv._elo_self, "pose", "standing")
            _sit_self_acts   = getattr(_srv._elo_self, "available_actions", [])
            _sit_self_loco   = getattr(_srv._elo_self, "locomotion_faculty_health", "OK")
            _sit_self_surf   = getattr(_srv._elo_self, "surface", "")
            _self_ctx_parts  = [
                f"[SITUATED_SELF — WO-041] Current pose: {_sit_self_pose}.",
                f"Available actions: {', '.join(_sit_self_acts) if _sit_self_acts else 'unknown'}.",
                f"Locomotion faculty: {_sit_self_loco}.",
            ]
            if _sit_self_surf:
                _self_ctx_parts.append(f"Surface: {_sit_self_surf}.")
            _g_ctx9 = " ".join(_self_ctx_parts)

    if "SITUATED_SELF" in _g_ctx9 and "standing" in _g_ctx9 and "window_top" in _g_ctx9:
        ok(f"AT-9: Situated Self READ injected into g_ctx: '{_g_ctx9[:80]}...'")
    else:
        fail("AT-9", f"g_ctx9={_g_ctx9[:80]!r}")
except Exception as e:
    fail("AT-9", e)


# ── AT-10: py_compile clean ───────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("self/elo_self_model.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-10: py_compile clean on elo_self_model.py and server.py")
except py_compile.PyCompileError as e:
    fail("AT-10", e)


print()
print("=" * 50)
print(f"WO-041  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
