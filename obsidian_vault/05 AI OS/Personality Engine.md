---
type: memory
domain: ai-os
tags: [personality, expression, prompt, modes, engine]
version: 1.0
---

# Personality Engine

The expression and tone layer for eLo AI OS. Controls HOW eLo sounds without changing cognition.

## Location

elo_personality_engine/ directory in the repository.

## What it controls

- Tone per mode (grounded, imaginative, calm, etc.)
- Speech style per mode (answer first, expand, acknowledge)
- Question rate per mode (0.0 for GENTLE_GROUNDED, 0.3 for CONVERSATIONAL)
- Philosophical output control (when philosophy is allowed vs forbidden)
- Motion mapping (mode → Unity animation intent)

## Key rule

Philosophy is NOT a default behaviour. It is conditional — only when explicitly invited or in CREATIVE mode.

## Connections

- [[eLo AI OS]]
- [[Kernel]]
- [[eLo]]
