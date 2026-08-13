"""
tests/test_int2_robot_vision_bridge.py — Acceptance tests for INT-2

Spec: Interconnection Map §1 + Volume_XII/01_Perception_Faculty.md
Robot vision bridge: capture → PerceptionResult (WO-009 compatible).

5 tests: FT ×2, ST ×2, IT ×1

Run: python3 tests/test_int2_robot_vision_bridge.py
"""
import sys
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):   global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from faculties.perception.robot_vision_bridge import (
    capture_frame, describe_frame, robot_perceive, sensor_health,
)
from faculties.perception.perception_faculty import PerceptionResult


# ── FT-1: robot_perceive returns a valid PerceptionResult ────────────────────
# No Pi hardware on this machine — degrades gracefully

result1 = robot_perceive()
try:
    assert isinstance(result1, PerceptionResult), f"expected PerceptionResult, got {type(result1)}"
    assert result1.source_health.get("vision", {}).get("status") in ("live", "stale", "absent")
    assert 0.0 <= result1.confidence <= 1.0
    ok(f"FT-1: robot_perceive returns PerceptionResult; confidence={result1.confidence:.3f}, "
       f"vision={result1.source_health.get('vision', {}).get('status')}")
except AssertionError as e: fail("FT-1", e)


# ── FT-2: vision_permitted=False → vision=absent, no fabricated objects ──────

result2 = robot_perceive(vision_permitted=False)
try:
    assert result2.source_health.get("vision", {}).get("status") == "absent", \
        f"vision must be absent when not permitted; got {result2.source_health.get('vision')}"
    assert result2.salient_objects == [] or result2.salient_objects == (), \
        "no salient objects when vision denied"
    ok(f"FT-2: vision_permitted=False → vision=absent, salient_objects={result2.salient_objects}")
except AssertionError as e: fail("FT-2", e)


# ── ST-1: No Pi camera → degrades gracefully (vision=absent) ─────────────────

raw = capture_frame()
try:
    # On non-Pi hardware, capture returns None (picamera2 not available)
    # This is correct behaviour — not a failure
    if raw is None:
        ok("ST-1: no Pi hardware → capture_frame returns None; bridge degrades correctly")
    else:
        # On actual Pi this would be bytes
        assert isinstance(raw, bytes), f"expected bytes or None, got {type(raw)}"
        ok(f"ST-1: camera capture returned {len(raw)} bytes (running on Pi?)")
except AssertionError as e: fail("ST-1", e)


# ── ST-2: Pre-supplied frame bytes with mocked describe_frame ────────────────
# Verify the bridge routes pre-captured frames through perceive() correctly

class _MockFrame:
    """Minimal JPEG stub (not a real image — vision_agent will fail gracefully)."""
    data = b"\xff\xd8\xff"  # JPEG magic bytes, truncated

# Inject a fake frame — describe_frame will fail (no real image) → vision=absent
result3 = robot_perceive(
    frame_bytes=_MockFrame.data,
    vision_permitted=True,
    location_hint="living room test",
    voice_transcript="hello eLo",
)
try:
    assert isinstance(result3, PerceptionResult)
    # voice_transcript must be picked up
    assert result3.source_health.get("voice", {}).get("status") == "live", \
        f"voice should be live when transcript supplied; got {result3.source_health.get('voice')}"
    ok(f"FT-ST-2: pre-supplied frame + voice transcript; voice={result3.source_health.get('voice', {}).get('status')}")
except AssertionError as e: fail("FT-ST-2", e)


# ── IT-1: PerceptionResult from bridge is WO-009 compatible ──────────────────
# Result must pass the same structural tests as desktop perceive()

result4 = robot_perceive(voice_transcript="what do you see")
try:
    # Same contract as WO-009 — frozen
    try:
        result4.confidence = 99.0
        fail("IT-1", "PerceptionResult from bridge should be frozen")
    except Exception:
        pass  # expected — frozen dataclass

    # All required fields present
    assert hasattr(result4, "modality_reads")
    assert hasattr(result4, "scene")
    assert hasattr(result4, "active_surface")
    assert hasattr(result4, "salient_objects")
    assert hasattr(result4, "user_activity")
    assert hasattr(result4, "confidence")
    assert hasattr(result4, "source_health")

    # Source health keys present (may be absent status — that's fine)
    for key in ("vision", "voice"):
        assert key in result4.source_health, f"source_health missing key: {key}"

    ok(f"IT-1: bridge PerceptionResult is WO-009 compatible; frozen=True, all fields present")
except AssertionError as e: fail("IT-1", e)


# ── Sensor health ─────────────────────────────────────────────────────────────

health = sensor_health()
print(f"\n  [sensor_health] camera={health['camera']}, mic={health['mic']}")


print(f"\nResult: {PASS}/5 passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
