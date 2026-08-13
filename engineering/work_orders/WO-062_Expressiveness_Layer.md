# WO-062 — Expressiveness layer (brain-routed micro-expressions + squash-and-stretch)

**Owner:** Designer (UI/Avatar) body — DONE/committed · Builder (eLo OS) emit half — WO-064 BP-4.
**Priority:** P2 (richness; after the two named goals). **Status:** DESIGNER-DONE (`8873b20`) · BUILDER-OPEN.
**Canon:** One-Brain (the face reflects the brain's emotion, not Unity randomness) · never contradict mood
valence · command-only, no ACK (ratified expression ruling, board 2026-08-06).

## What it is
eLo's face + body carry his emotional/cognitive state: brain-routed **micro-expressions**
(joy/worried/confident/curious/disgust/sad/satisfied) and **squash-and-stretch** on the moves
(anticipation crouch → launch stretch → land squash → spring settle).

## Halves (spec'd so neither ships alone)
- **Designer (DONE, committed `8873b20`):** `ApplyExpression` reads `expression.micro` (+`micro_ts`,
  edge-triggered) → `HeadLook.FlashMicro`; autonomous flashes yield while the brain is expressing and never
  contradict mood valence. `EloSquashStretch` anticipation/launch/land/settle wired on jumps.
- **Builder (OPEN = WO-064 BP-4):** the Self-Model EMITS `expression:{micro:'<emotion>', micro_ts}` to
  `blender_state.json` from eLo's real emotion state so the face is brain-driven.

## Definition of Done (full behaviour)
eLo shows the right micro-expression BECAUSE his cognitive state holds that emotion (not a random Unity
flash), and the moves read weighty (squash/stretch). Autonomous neutral jitter stays a Unity reflex; any
VALENCE-bearing expression originates in the brain.

## Test — WITHOUT David
- Builder half: `tests/test_wo064_expression_micro.py` (emotion X → `expression.micro==X` + fresh ts;
  neutral → no spam).
- Designer half: inject `expression.micro` → `FlashMicro` fires (inject-verified, already done).
David L3: the face feel + move weight (Inspector-tunable).
