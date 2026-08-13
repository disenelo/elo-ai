"""
tests/test_wo009_perception_faculty.py — Acceptance tests for WO-009: Perception Faculty

Spec: faculties/perception/perception_faculty.py
7 acceptance tests from Volume_XII (FT-1..3, ST-1..3, IT-1).

Run: python3 tests/test_wo009_perception_faculty.py
"""
import sys
sys.path.insert(0, '.')

PASS = 0; FAIL = 0
def ok(n):  global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.perception.perception_faculty import perceive, PerceptionResult

# ── FT-1: coding session → scene + surface + activity ────────────────────────
r = perceive(
    window_app="Visual Studio Code",
    window_title="perception_faculty.py — elo-ai",
    vision_text="monitor showing code editor with Python code, keyboard visible, mug",
)
try:
    assert r.active_surface == "code", f"surface={r.active_surface!r}"
    assert r.user_activity  == "working", f"activity={r.user_activity!r}"
    assert len(r.salient_objects) > 0, "no salient objects"
    assert r.source_health["window"]["status"] == "live"
    assert r.source_health["vision"]["status"]  == "live"
    ok(f"FT-1: coding session — surface=code, activity=working, salient_objects={len(r.salient_objects)}")
except AssertionError as e: fail("FT-1", e)

# ── FT-2: Frozen (immutable) ──────────────────────────────────────────────────
try:
    try:
        r.scene = "hacked"
        fail("FT-2", "PerceptionResult is not frozen")
    except Exception:
        ok("FT-2: PerceptionResult is frozen")
except Exception as e: fail("FT-2", e)

# ── FT-3: source_health complete; absent when not supplied ───────────────────
r3 = perceive(window_app="Blender", window_title="eLo-Planet.blend")
try:
    assert r3.active_surface == "creative", f"surface={r3.active_surface!r}"
    assert "window" in r3.source_health
    assert r3.source_health.get("vision", {}).get("status") == "absent"
    ok("FT-3: creative surface; source_health complete; vision=absent when not supplied")
except AssertionError as e: fail("FT-3", e)

# ── ST-1: Vision absent → rest still resolves, confidence lowered ─────────────
r4 = perceive(window_app="Terminal", window_title="bash")
try:
    assert r4.active_surface == "terminal"
    assert r4.user_activity  == "working"
    assert r4.source_health["vision"]["status"] == "absent"
    assert r4.confidence < 1.0, f"confidence should be < 1.0 got {r4.confidence}"
    ok(f"ST-1: vision absent → terminal/working still resolved; confidence={r4.confidence}")
except AssertionError as e: fail("ST-1", e)

# ── ST-2: Screen-record denied → vision=absent, no fabricated objects ─────────
r5 = perceive(vision_text="secret content visible", window_app="Safari", vision_permitted=False)
try:
    assert r5.source_health["vision"]["status"] == "absent"
    assert len(r5.salient_objects) == 0, f"fabricated objects: {r5.salient_objects}"
    ok("ST-2: screen-record denied → vision=absent, no fabricated salient objects")
except AssertionError as e: fail("ST-2", e)

# ── ST-3: No sensors → unknown + low confidence, no fabrication ───────────────
r6 = perceive()
try:
    assert r6.active_surface == "unknown", f"surface={r6.active_surface!r}"
    assert r6.user_activity  == "unknown", f"activity={r6.user_activity!r}"
    assert r6.confidence <= 0.75, f"confidence={r6.confidence}"
    assert len(r6.salient_objects) == 0
    ok(f"ST-3: no sensors → unknown/unknown, confidence={r6.confidence}, no fabrication")
except AssertionError as e: fail("ST-3", e)

# ── IT-1: All 4 modalities live ───────────────────────────────────────────────
r7 = perceive(
    vision_text="code editor open with Python file",
    window_app="Code",
    window_title="main.py — elo-ai",
    voice_transcript="eLo what does this function do",
    file_context="main.py: server entry point",
    vision_permitted=True,
)
try:
    for src in ("window", "vision", "voice", "files"):
        assert r7.source_health[src]["status"] == "live", f"{src} not live"
    assert len(r7.modality_reads) == 4
    assert r7.active_surface == "code"
    ok(f"IT-1: all 4 modalities live; confidence={r7.confidence}")
except AssertionError as e: fail("IT-1", e)

print(f"\nResult: {PASS}/7 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
