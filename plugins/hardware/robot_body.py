"""
plugins/hardware/robot_body.py — maps PresenceState to robot body output.

Robot eLo has NO MOUTH — expression is body-only:
    - NeoPixel glow color + pattern  (emotional state)
    - Head lean via servo            (c_head.x equivalent — one servo)
    - Body energy level              (movement speed / idle pulse rate)
    - Omni-wheel base speed/direction (when motor control is added)

NOT ACTIVE YET. Scaffolding for Raspberry Pi 5 phase.
All hardware calls are marked # HARDWARE HOOK.

Robot does NOT use:
    - Shape keys (no mesh, no Blender)
    - Mouth phonemes
    - NLA animation clips
"""
from __future__ import annotations

# ── presence mode → NeoPixel glow profile ─────────────────────────────────────
# color: (R, G, B) target
# pattern: "pulse_slow" | "pulse_fast" | "solid" | "flicker" | "sweep"
# brightness: 0.0–1.0

PRESENCE_GLOW: dict[str, dict] = {
    "idle":        {"color": (100, 180, 255), "pattern": "pulse_slow",  "brightness": 0.4},
    "thinking":    {"color": (160, 140, 255), "pattern": "pulse_slow",  "brightness": 0.5},
    "observing":   {"color": (100, 220, 200), "pattern": "solid",       "brightness": 0.55},
    "building":    {"color": (255, 200,  80), "pattern": "solid",       "brightness": 0.7},
    "celebrating": {"color": (255, 220, 100), "pattern": "sweep",       "brightness": 1.0},
    "resting":     {"color": ( 80, 120, 200), "pattern": "pulse_slow",  "brightness": 0.25},
    "exploring":   {"color": (100, 255, 180), "pattern": "pulse_fast",  "brightness": 0.65},
}

# ── presence mode → head servo lean ──────────────────────────────────────────
# degrees from center (+ = right, - = left)
# robot head servo range: approximately -30 to +30 degrees

PRESENCE_HEAD_LEAN: dict[str, float] = {
    "idle":        0.0,
    "thinking":    8.0,    # slight right tilt — processing
    "observing":   5.0,
    "building":    0.0,    # forward
    "celebrating": -5.0,   # slight left open
    "resting":     7.0,    # settled lean
    "exploring":  -6.0,
}

# ── energy → base movement speed (0–1) ───────────────────────────────────────
# 0 = still, 1 = full omni-wheel speed
# not used until motor control is added

def energy_to_base_speed(energy: float) -> float:
    if energy < 0.2:
        return 0.0   # still
    if energy < 0.5:
        return 0.15  # gentle drift
    return round(energy * 0.4, 2)   # max ~0.4 — eLo floats, doesn't rush


# ── main signal builder ───────────────────────────────────────────────────────

def build_robot_signal(mode: str, energy: float, intensity: float) -> dict:
    """
    Build robot body output signal from presence state.

    Returns:
        {
            "glow":       dict  — color, pattern, brightness
            "head_lean":  float — servo degrees from center
            "base_speed": float — omni-wheel speed
            "mode":       str
        }
    """
    glow      = dict(PRESENCE_GLOW.get(mode, PRESENCE_GLOW["idle"]))
    head_lean = PRESENCE_HEAD_LEAN.get(mode, 0.0)
    base_spd  = energy_to_base_speed(energy)

    # intensity scales brightness and lean
    glow["brightness"] = round(glow["brightness"] * (0.6 + intensity * 0.4), 2)
    head_lean          = round(head_lean * intensity, 2)

    return {
        "glow":       glow,
        "head_lean":  head_lean,
        "base_speed": base_spd,
        "mode":       mode,
    }


# ── hardware hooks (Raspberry Pi 5 — future) ─────────────────────────────────

def apply_glow(signal: dict) -> None:
    """
    HARDWARE HOOK — drive NeoPixel strip from glow signal.

    from rpi_ws281x import PixelStrip, Color
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    r, g, b = signal["glow"]["color"]
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(r, g, b))
    strip.show()
    """
    print(f"[ROBOT] glow={signal['glow']['color']}  "
          f"pattern={signal['glow']['pattern']}  "
          f"brightness={signal['glow']['brightness']}")


def apply_head_lean(degrees: float) -> None:
    """
    HARDWARE HOOK — set head servo position.

    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SERVO_PIN, GPIO.OUT)
    pwm = GPIO.PWM(SERVO_PIN, 50)
    pwm.start(0)
    duty = 2.5 + (degrees + 90) / 18   # map -90..90 to 2.5..12.5
    pwm.ChangeDutyCycle(duty)
    """
    print(f"[ROBOT] head_lean={degrees}°")
