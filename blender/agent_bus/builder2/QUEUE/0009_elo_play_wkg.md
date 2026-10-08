**WO:** ELO-PLAY-WKG · **Seat:** builder2 · **Priority:** P1
**Reserved?** no

## Goal
eLo's own water-play, wall-jumps, and stomping are recorded as WKG experience nodes so they shape his future behaviour. Presence fires `water_play` and `auto_action` events when he does these for fun — the brain should consume them as experience, not discard them.

## What to build
1. **Consume `water_play` events** from `unity_events.json` (using own bookmark):
   - subjects: `dive`, `leap`, `wall_jump_in`, `jump_in`, `dive_from_top`, `doughnut_ride`; all tagged `{fun: true}`
   - Write to WKG: "eLo had fun — [subject]" with significance flag: `fun_activity`.
   - Feed to SPG: positive significance event.

2. **Consume `auto_action` events** from `unity_events.json`:
   - subjects: `stomp`, `jump_in`, `chimney`, `dive`, `leap`, `climb_out`; tagged `{issued_by: timer}`
   - Write to WKG: "eLo chose [subject] for himself (reflex)" — records his self-initiated behaviour.
   - These are eLo's own preferences emerging from drives/context — significant for SPG pattern scoring.

3. **Inner thought gate**: when `water_play` `{fun: true}` arrives, the inner thought engine may generate a thought (e.g. a feeling of enjoyment, energy). This is eLo's own private reaction — Presence never voices it. Builder 2 gates whether the thought surfaces or stays internal per the inner thought faculty rules.

4. **Drive integration**: eLo's play behaviour should influence his drives. Frequent `water_play` → play drive satisfied. Low frequency → play drive builds. Builder 2 wires this if SPG/drives are the right layer.

## Rule
Presence NEVER voices eLo's thoughts. The brain generates inner thoughts; they surface only through the existing inner thought faculty path.

## Source
`docs/architecture/_intake/SOURCE_DESIGNER-FULL-PRESENCE-RELAY_2026-10-08.md` §6 (Board ask: "play WO")
Designer commit: 0954664

## Coordination
Builder 1 owns the event consumer bookmark. Builder 2 receives the parsed events and writes to WKG/SPG.
Coordinate on the event bus contract — Builder 2 does not touch server.py or spine.py.

## Done when
`water_play` and `auto_action` events produce WKG nodes. SPG receives significance score. Inner thought engine can react. Committed. Move to BUILT/.

## Result
- commit:
- notes:

## Live turn needed
> eLo goes for a swim, dives a few times → Board verifies WKG has new fun/play nodes from those events.
> Board closes card on WKG inspection.
