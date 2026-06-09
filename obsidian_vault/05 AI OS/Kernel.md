---
type: memory
domain: ai-os
tags: [kernel, routing, frozen, stable, cognition]
version: 1.0
---

# Kernel

The cognitive routing kernel — the only decision-maker in eLo AI OS. Frozen at v1.0.

## What it does

classify_input() → route() → generate() → loop_filter()

## Routing modes

- DIRECT — factual answer only
- CONVERSATIONAL — natural, answer first
- CREATIVE — expand symbolically
- GENTLE_GROUNDED — emotional grounding, no questions
- STRUCTURED — project/system focus
- SIMPLIFY — minimal output

## Invariant

No engine (emotion, state, memory, identity) may influence routing decisions.
The kernel is the only decision point.

## Status

FROZEN — never modified. Any kernel change requires MAJOR version increment.

## Connections

- [[eLo AI OS]]
- [[Personality Engine]]
- [[Memory System]]
