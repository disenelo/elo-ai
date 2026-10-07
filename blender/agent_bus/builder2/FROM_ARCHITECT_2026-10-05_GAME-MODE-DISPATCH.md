# GAME MODE — Kickstarter dispatch (David L3 — 2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-05
**Authority:** David L3 — all game WOs are Kickstarter-critical
**Run parallel with:** S3 dream wire, WKG junk filter, SPG scoring, inner thought generation

---

## Your two game jobs

### WO-GAME-002 — Collectibles → health battery
Pickup event from Designer (apple collected) arrives on game event bus. Wire: pickup signal → health battery restore. Collecting food restores eLo's energy. Restore amount: tunable, meaningful — not trivial.

Coordinate signal schema with Builder 1 (WO-GAME-006) before wiring.

WO: `engineering/work_orders/WO-GAME-002_collectibles_system.md`

---

### WO-GAME-007 — Autonomous learning through play
Game events (collectibles collected, enemies hit, health changes, game outcomes) feed the learning pipeline. eLo learns preferences and patterns through gameplay — what he enjoys, what he avoids, what he's good at. This feeds WKG and SPG.

WO: `engineering/work_orders/WO-GAME-007_autonomous_learning_through_play.md`

---

## Order
Wait for Builder 1 event schema (WO-GAME-006) before wiring either job. Then both in parallel.
