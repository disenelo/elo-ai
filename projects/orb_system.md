# Project: Core Orb System

**Type**: hardware_simulation → physical device
**Status**: prototype (simulation active, hardware not yet built)
**Namespace**: orb_device

---

## What it is

The Core Orb is eLo's physical companion device — and in the AI system,
its simulated emotional state output layer.

Physical vision:
- Translucent TPU or acrylic shell
- NeoPixel glow ring inside
- Raspberry Pi 5 brain
- Voice input/output
- Emotional state expressed through light patterns

AI simulation:
- State machine: idle / listening / thinking / insight / error
- Each state has a visual signature
- Hardware hook points marked in `plugins/hardware/orb_engine.py`

---

## States

| State | Light pattern | Meaning |
|---|---|---|
| idle | Soft pulse | Waiting, present |
| listening | Active glow | Capturing input |
| thinking | Cycling animation | Processing |
| insight | Bright flash | Idea arrived |
| error | Flicker | Something went wrong |

---

## Linked systems

- `plugins/hardware/orb_engine.py` — state machine + hardware hooks
- `plugins/voice/` — future STT/TTS integration
- Physical Raspberry Pi build (future)
- NeoPixel animation layer (future)

---

## Next steps (hardware path)

1. Source translucent shell material
2. NeoPixel ring test with Raspberry Pi
3. Wire state machine to GPIO
4. Integrate voice layer
