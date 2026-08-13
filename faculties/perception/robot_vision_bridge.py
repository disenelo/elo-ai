"""
faculties/perception/robot_vision_bridge.py — INT-2

Robot vision bridge: physical camera capture → PerceptionResult.

Extends the Perception Faculty (WO-009) with a Pi-side entry point.
On the desktop, perception reads the screen; on the robot, it reads the room.
The same PerceptionResult contract applies — one frozen result per snapshot,
each modality independently degradable, no fabrication.

Hardware path (Pi only):
  picamera2 → JPEG bytes → vision_agent.describe() → perceive()

Graceful degradation (no Pi hardware):
  capture returns None → vision=absent → confidence lowered → turn proceeds.

This module has no hard dependency on picamera2 — it tries the import and
falls back silently. It can run on macOS for integration testing.
"""
from __future__ import annotations

import base64
import io
import time
from typing import Optional

from faculties.perception.perception_faculty import PerceptionResult, perceive

# ── Camera capture ────────────────────────────────────────────────────────────

def capture_frame(
    resolution: tuple = (640, 480),
    timeout_ms: int   = 3000,
) -> Optional[bytes]:
    """
    Capture one JPEG frame from the Pi camera.

    Returns raw JPEG bytes, or None if picamera2 is unavailable or capture fails.
    Never raises.
    """
    try:
        from picamera2 import Picamera2  # type: ignore  # Pi-only
        cam = Picamera2()
        config = cam.create_still_configuration(main={"size": resolution})
        cam.configure(config)
        cam.start()
        time.sleep(0.3)                   # brief settle
        buf = io.BytesIO()
        cam.capture_file(buf, format="jpeg")
        cam.stop()
        cam.close()
        return buf.getvalue()
    except ImportError:
        # Not a Pi — expected on macOS / CI
        return None
    except Exception:
        # Hardware error — degrade, don't crash
        return None


def describe_frame(
    frame_bytes: bytes,
    location_hint: str = "",
) -> Optional[str]:
    """
    Send a JPEG frame to the vision agent for a text description.

    Returns a short scene description, or None if the vision agent is unavailable.
    Never fabricates — a failure returns None (caller maps to vision=absent).
    """
    try:
        from tools import vision_agent  # type: ignore
        b64 = base64.b64encode(frame_bytes).decode()
        prompt = "Describe this physical room scene briefly. Focus on: "
        if location_hint:
            prompt += f"context is {location_hint}. "
        prompt += "Who or what is present, lighting, objects near the robot."
        result = vision_agent.describe_base64(b64, prompt=prompt)
        return result if isinstance(result, str) and result.strip() else None
    except (ImportError, AttributeError, Exception):
        return None


# ── Main bridge entry point ───────────────────────────────────────────────────

def robot_perceive(
    voice_transcript: Optional[str] = None,
    vision_permitted: bool = True,
    location_hint:    str  = "",
    frame_bytes:      Optional[bytes] = None,   # supply pre-captured frame for testing
) -> PerceptionResult:
    """
    Capture the robot's physical environment → PerceptionResult.

    This is the INT-2 entry point. Wraps capture_frame + describe_frame + perceive().

    Args:
        voice_transcript:  STT result from the robot's mic (optional).
        vision_permitted:  Set False if the robot's camera is disabled/unconsented.
        location_hint:     "living room", "workshop" etc. — feeds the vision prompt.
        frame_bytes:       Pre-captured JPEG bytes (for testing or buffered use).

    Returns:
        PerceptionResult — frozen, never raises.
    """
    vision_text: Optional[str] = None

    if vision_permitted:
        # Capture if not pre-supplied
        raw = frame_bytes if frame_bytes is not None else capture_frame()

        if raw is not None:
            vision_text = describe_frame(raw, location_hint=location_hint)
            # describe_frame returns None on failure → vision=absent below (correct)

    # Route through the canonical Perception Faculty.
    # Robot has no desktop window/app — those modalities are absent.
    return perceive(
        vision_text      = vision_text,
        window_app       = None,       # no desktop window on the robot
        window_title     = None,
        voice_transcript = voice_transcript,
        file_context     = location_hint or None,   # location as environmental context
        vision_permitted = vision_permitted,
    )


# ── Sensor health snapshot ────────────────────────────────────────────────────

def sensor_health() -> dict:
    """
    Return a quick health snapshot for the robot's perception sensors.
    Used by the Robot presence engine to report status.

    Returns dict: { "camera": bool, "mic": bool }
    """
    camera_ok = False
    try:
        from picamera2 import Picamera2  # type: ignore
        camera_ok = True
    except ImportError:
        pass

    mic_ok = False
    try:
        import speech_recognition  # type: ignore
        mic_ok = True
    except ImportError:
        pass

    return {"camera": camera_ok, "mic": mic_ok}
