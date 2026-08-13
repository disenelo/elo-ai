# → CHIEF ARCHITECT (cross-check request) — Moveset ↔ Self-Model + "built ≠ done" (Lead Architect, 2026-08-06)
David asked this be spec'd "between you and the architects, and how the self-model works." Drafted; please
cross-check / ratify or adjust.

## Drafts
1. **`MOVESET_SELFMODEL_SPEC_draft.md`** — how eLo KNOWS his moves (Self Model capability records: verb ·
   unity_state · faculty · status · confidence · last_success/failure), DECIDES them (Executive reads the
   assembled state + affordances + goal — The Moment/ADR-Exec-006), executes (commandable `move_command`
   sub-types per the IO Contract → each testable like sit), verifies (`move_complete` ACK), UPDATES the
   self-model (pose · surface · recent_behavior · confidence, learned via ADR-Exec-005). §8 = the governing
   principle; §9 = take-five as an embodied EXIT move (fixes WO-045).
2. **`FREEFORM_MOVESET_CONTRACT_draft.md`** (ratified) — now carries the Designer's implementation approach:
   commanded moves REUSE the autonomous resolver (DesktopBuddy ~1293-94) — a commanded move = right target
   + style flag, so commanded == autonomous exactly (no divergence).

## New principle (added to ARCHITECTURAL_PRINCIPLES — please sanity-check)
**"Autonomous and commanded are one capability."** Everything eLo does on its own (moves, expressions,
exits) must also be drivable by the Executive, via the SAME underlying capability — never two divergent
paths. One brain drives both.

## New Definition-of-Done line (Operating Loop — please sanity-check)
**Built ≠ done — done = DRIVEABLE (eLo OS can invoke it) + VERIFIED (tested / felt live).** David's
systemic point: "look how much is built and not verified to be used by eLo OS." Autonomous-only or
isolated-built code is BUILT, not DONE.

## Cross-check asks
- Is the Self Model capability-record shape right (verb · faculty · status · confidence · last_success)?
- Is "autonomous = commandable" safely a principle, or edge cases where autonomous SHOULD differ?
- Does "built ≠ done = driveable + verified" belong in the DoD, or is it too strict for infra WOs?
- Sequencing: moves commandable NOW (Designer) + capability registration with WO-052A; Executive DECIDING
  the chain = Track B. Agree?
Reply with GO or adjustments. Nothing changes the Presentable-6 train order unless you flag it.
