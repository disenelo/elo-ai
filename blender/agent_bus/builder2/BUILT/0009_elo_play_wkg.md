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
- commit: `6ba0b30`
- test: `tests/test_play_experience.py` — 28 passed
- notes:
  1. **water_play consumed** — `core/play_experience.py`, own cursor
     (`blender/play_cursor.json`). All six relayed subjects accepted, with a
     parametrised test over each so a dropped one fails here.
  2. **auto_action consumed** — same path, all six subjects. Kept DISTINCT
     from water_play in the record: *"eLo had fun — dive"* vs *"eLo chose
     stomp for himself"*, and scored higher (0.65 vs 0.50). A preference
     surfacing with nobody asking says more about him than enjoying something
     he was already doing; flattening them makes "what does he do when nobody
     asks" unanswerable.
  3. **WKG** — claim `eLo —OBSERVED_AS→ <move> (play)`, episodic,
     `significance_score` carried. OBSERVED_AS not IS: he performed it, it is
     not what he is.
  4. **SPG** — `creation_event` signal with the significance and context tags
     (`play`, the subject, `self_initiated`/`fun`).
  5. **SIMULATED, non-negotiably** — every claim carries
     `memory_origin=SIMULATED_EXPERIENCE` per WO-CAP-EMB-051, with a test
     asserting it is not `PHYSICAL_EXPERIENCE`. eLo diving in Presence did not
     get wet.
  6. **Inner thought gate** — nothing forced. The faculty's existing rules
     decide whether a thought surfaces; this module writes experience and
     never voices anything, per the card's rule.
  7. **NOT BUILT — scope item 4, drive integration.** "Builder 2 wires this if
     SPG/drives are the right layer." There is no drive layer to wire to.
     Inventing one to satisfy a maybe is how the orphans in this codebase get
     made. SPG now carries the signal a drive layer would read.

  **Coordination note for Builder 1:** this uses its OWN cursor rather than a
  shared bookmark. server.py's poller already tracks `consumed_seq` against
  the same append-log, and one cursor between two readers means each silently
  eats the other's events. A test asserts the shared cursor is never written.
  If you want a single bookmark, it needs a fan-out, and that is your lane.

## Live turn needed
Board's version stands: eLo swims and dives a few times, then inspect WKG for
new play nodes.

Concrete check after he has played:

    python3 -c "import sys;sys.path.insert(0,'.');from runtime.wkg_faculty import all_claims;\
    print([c for c in all_claims() if c.get('context_action')=='play'])"

Expect claims with `memory_origin='simulated_experience'` and
`relationship_type='OBSERVED_AS'`. **Zero today** — the events have never had
a consumer, so anything that appears is new behaviour.

## Live turn needed
> eLo goes for a swim, dives a few times → Board verifies WKG has new fun/play nodes from those events.
> Board closes card on WKG inspection.
