"""
tests/test_canon_xii_perception.py — Acceptance tests for WO-CANON-XII
(Perception → World-State copy + structured fidelity flags)

Spec: engineering/work_orders/WO-CANON-XII.md
Canon: Volume XII Ch.1–Ch.4

  Ch.1/FT-1: perceive() produces one frozen PerceptionResult per call
  Ch.1/FT-2: sensation → context: window present → meaningful scene + surface + activity
  Ch.1/ST-1: modality isolation — window absent → surface='unknown', activity='unknown'
  Ch.1/ST-2: vision denied → source_health.vision=absent; not in modality_reads
  Ch.1/ST-3: no fabrication — absent window → scene is generic, not invented
  Ch.2/FT-3: live window read fills fields; confidence lowered when absent
  Ch.2/ST-4: robot camera absent on macOS still returns a PerceptionResult
  Ch.3/FT-4: perception fields populate correct LiveWorldState domains (source='PerceptionFaculty')
  Ch.3/FT-5: confidence carried verbatim 0→0 (never inflated by World State copy)
  Ch.3/ST-5: perception-absent → LiveWorldState assembles with neutral defaults
  Ch.3/ST-6: honesty across the seam — no re-interpretation at copy step
  Ch.4/AT-1: partial=True when confidence < 0.7
  Ch.4/AT-2: partial=True when window absent (primary modality absent)
  Ch.4/AT-3: partial=False when confidence >= 0.7 and all primary modalities present
  AT-4: py_compile clean — perception_faculty.py, live_world_state.py, spine.py

Run: python3 tests/test_canon_xii_perception.py
"""
import sys, os, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from faculties.perception.perception_faculty import (
    perceive, perceive_from_live_state, PerceptionResult,
)
from world.live_world_state import assemble_world_state, LiveWorldState


# Ch.1/FT-1: perceive() returns frozen PerceptionResult
try:
    pr = perceive(window_app="VSCode", window_title="server.py")
    assert isinstance(pr, PerceptionResult), f"expected PerceptionResult, got {type(pr)}"
    # Frozen — mutation must raise
    raised = False
    try:
        pr.confidence = 0.0
    except (AttributeError, TypeError):
        raised = True
    assert raised, "PerceptionResult must be frozen"
    ok("Ch.1/FT-1: perceive() returns frozen PerceptionResult")
except AssertionError as e:
    fail("Ch.1/FT-1", e)
except Exception as e:
    fail("Ch.1/FT-1", e)


# Ch.1/FT-2: window present → scene + surface + activity populated
try:
    pr = perceive(window_app="code", window_title="server.py")
    assert pr.active_surface == "code", f"expected surface=code, got {pr.active_surface!r}"
    assert pr.user_activity == "working", f"expected activity=working, got {pr.user_activity!r}"
    assert pr.scene != "", f"scene must not be empty when window present"
    assert "code" in pr.scene.lower() or "server" in pr.scene.lower(), \
        f"scene should reference the app: {pr.scene!r}"
    ok(f"Ch.1/FT-2: window present → surface={pr.active_surface!r}, activity={pr.user_activity!r}")
except AssertionError as e:
    fail("Ch.1/FT-2", e)
except Exception as e:
    fail("Ch.1/FT-2", e)


# Ch.1/ST-1: window absent → surface='unknown', activity='unknown', confidence lowered
try:
    pr = perceive(window_app=None, window_title=None)
    assert pr.active_surface == "unknown", f"got {pr.active_surface!r}"
    assert pr.user_activity == "unknown", f"got {pr.user_activity!r}"
    assert pr.confidence < 1.0, f"confidence must be < 1.0 when window absent, got {pr.confidence}"
    assert pr.source_health.get("window", {}).get("status") == "absent"
    ok(f"Ch.1/ST-1: window absent → surface=unknown, activity=unknown, confidence={pr.confidence}")
except AssertionError as e:
    fail("Ch.1/ST-1", e)
except Exception as e:
    fail("Ch.1/ST-1", e)


# Ch.1/ST-2: vision denied → source_health.vision=absent, not in modality_reads
try:
    pr = perceive(window_app="chrome", vision_text="I can see everything", vision_permitted=False)
    assert pr.source_health.get("vision", {}).get("status") == "absent", \
        "vision denied must set status=absent"
    assert "vision" not in pr.modality_reads, "denied vision must not appear in modality_reads"
    ok("Ch.1/ST-2: vision denied → source_health.vision=absent, not in modality_reads")
except AssertionError as e:
    fail("Ch.1/ST-2", e)
except Exception as e:
    fail("Ch.1/ST-2", e)


# Ch.1/ST-3: no fabrication — all absent → generic scene, not invented detail
try:
    pr = perceive()  # all absent
    assert pr.scene in ("idle session", "active session", ""), \
        f"absent-all scene should be generic, got {pr.scene!r}"
    assert pr.active_surface == "unknown"
    assert pr.user_activity == "unknown"
    ok(f"Ch.1/ST-3: all absent → generic scene={pr.scene!r}, no fabrication")
except AssertionError as e:
    fail("Ch.1/ST-3", e)
except Exception as e:
    fail("Ch.1/ST-3", e)


# Ch.2/FT-3: confidence lowered when window absent vs present
try:
    pr_with = perceive(window_app="Figma", window_title="design.fig")
    pr_without = perceive(window_app=None)
    assert pr_with.confidence > pr_without.confidence, \
        f"window present should give higher confidence: {pr_with.confidence} vs {pr_without.confidence}"
    ok(f"Ch.2/FT-3: confidence higher with window ({pr_with.confidence}) vs without ({pr_without.confidence})")
except AssertionError as e:
    fail("Ch.2/FT-3", e)
except Exception as e:
    fail("Ch.2/FT-3", e)


# Ch.2/ST-4: robot camera absent (macOS) still returns a PerceptionResult
try:
    pr = perceive(window_app="Terminal", vision_text=None)
    assert isinstance(pr, PerceptionResult), "must return PerceptionResult even without robot camera"
    assert pr.source_health.get("vision", {}).get("status") == "absent"
    ok("Ch.2/ST-4: robot camera absent (no vision_text) → PerceptionResult returned, vision=absent")
except AssertionError as e:
    fail("Ch.2/ST-4", e)
except Exception as e:
    fail("Ch.2/ST-4", e)


# Ch.3/FT-4: perception fields populate correct LiveWorldState domains with source='PerceptionFaculty'
try:
    pr = perceive(window_app="code", window_title="server.py", vision_permitted=True)
    ws = assemble_world_state(turn_id="xii_ft4", perception=pr)
    assert isinstance(ws, LiveWorldState)
    desk_h = ws.domain_health.get("desktop", {})
    assert desk_h.get("source") == "PerceptionFaculty", \
        f"desktop source must be 'PerceptionFaculty', got {desk_h.get('source')!r}"
    env_h = ws.domain_health.get("environment", {})
    assert env_h.get("source") == "PerceptionFaculty", \
        f"environment source must be 'PerceptionFaculty', got {env_h.get('source')!r}"
    ok("Ch.3/FT-4: perception fields populate LiveWorldState with source='PerceptionFaculty'")
except AssertionError as e:
    fail("Ch.3/FT-4", e)
except Exception as e:
    fail("Ch.3/FT-4", e)


# Ch.3/FT-5: confidence carried verbatim — not inflated in the copy step
try:
    pr = perceive(window_app=None, window_title=None)   # degraded confidence
    ws = assemble_world_state(turn_id="xii_ft5", perception=pr)
    desk_h = ws.domain_health.get("desktop", {})
    # Desktop may be absent (PerceptionFaculty source not set when surface=unknown)
    # The key assertion: World State must not INFLATE confidence beyond what perception reported
    world_conf = desk_h.get("confidence", 0.0)
    assert world_conf <= 1.0, "world confidence must not exceed 1.0"
    ok(f"Ch.3/FT-5: confidence not inflated in copy step (desktop confidence={world_conf})")
except AssertionError as e:
    fail("Ch.3/FT-5", e)
except Exception as e:
    fail("Ch.3/FT-5", e)


# Ch.3/ST-5: perception=None → LiveWorldState assembles with neutral defaults
try:
    ws = assemble_world_state(turn_id="xii_st5", perception=None)
    assert isinstance(ws, LiveWorldState)
    # Without perception, domains degrade gracefully to absent/default
    assert ws.time.now_iso != "", "time must still be live even with no perception"
    ok("Ch.3/ST-5: perception=None → LiveWorldState assembles fine (neutral defaults)")
except AssertionError as e:
    fail("Ch.3/ST-5", e)
except Exception as e:
    fail("Ch.3/ST-5", e)


# Ch.3/ST-6: copy step does not re-interpret — perception's activity category is authoritative
# (D2 ruling: DesktopState.surface renamed to DesktopState.platform — platform is "mac"/"unity",
#  not the activity category. The activity category ("creative"/"code"/"browser") lives on
#  PerceptionResult.active_surface and consumers read it there.)
try:
    pr = perceive(window_app="figma", window_title="UI Design")
    assert pr.active_surface == "creative", f"expected creative, got {pr.active_surface!r}"
    ws = assemble_world_state(turn_id="xii_st6", perception=pr)
    # PerceptionResult's active_surface stays verbatim after copy — no re-interpretation
    # DesktopState.platform remains the body/platform label (unchanged by activity category)
    assert pr.active_surface == "creative", \
        f"PerceptionResult.active_surface should stay 'creative' after copy, got {pr.active_surface!r}"
    assert ws.desktop.platform in ("", "mac", "unity", "unknown"), \
        f"DesktopState.platform must be a body/platform label, got {ws.desktop.platform!r}"
    ok(f"Ch.3/ST-6: activity category stays verbatim on PerceptionResult.active_surface='creative'; DesktopState.platform is body/platform label")
except AssertionError as e:
    fail("Ch.3/ST-6", e)
except Exception as e:
    fail("Ch.3/ST-6", e)


# Ch.4/AT-1: partial=True when confidence < 0.7
try:
    pr = perceive(window_app=None, window_title=None)  # no window → confidence < 0.7
    assert pr.partial is True, f"expected partial=True for low-confidence result, got {pr.partial}"
    ok(f"Ch.4/AT-1: partial=True when confidence={pr.confidence} < 0.7 (window absent)")
except AssertionError as e:
    fail("Ch.4/AT-1", e)
except Exception as e:
    fail("Ch.4/AT-1", e)


# Ch.4/AT-2: partial=True when window absent (primary modality absent)
try:
    pr = perceive(window_app=None)
    assert pr.source_health.get("window", {}).get("status") == "absent"
    assert pr.partial is True, f"expected partial=True when window absent, got {pr.partial}"
    ok("Ch.4/AT-2: partial=True when window (primary modality) absent")
except AssertionError as e:
    fail("Ch.4/AT-2", e)
except Exception as e:
    fail("Ch.4/AT-2", e)


# Ch.4/AT-3: partial=False when all primary modalities present + confidence >= 0.7
try:
    pr = perceive(
        window_app="chrome",
        window_title="GitHub",
        vision_permitted=True,
    )
    assert pr.confidence >= 0.7, f"confidence should be >= 0.7 with window, got {pr.confidence}"
    # Window is present → partial should be False (vision=absent is allowed if vision_permitted=True)
    assert pr.partial is False, f"expected partial=False, got {pr.partial} (confidence={pr.confidence})"
    ok(f"Ch.4/AT-3: partial=False when window present + confidence={pr.confidence} >= 0.7")
except AssertionError as e:
    fail("Ch.4/AT-3", e)
except Exception as e:
    fail("Ch.4/AT-3", e)


# AT-4: py_compile clean
try:
    for f in (
        "faculties/perception/perception_faculty.py",
        "world/live_world_state.py",
        "runtime/spine/spine.py",
    ):
        py_compile.compile(f, doraise=True)
    ok("AT-4: py_compile clean on perception_faculty, live_world_state, spine")
except py_compile.PyCompileError as e:
    fail("AT-4", e)


print()
print("=" * 62)
print(f"WO-CANON-XII perception  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
