# ▶ BUILDER — gaze awareness + movement reports are LIVE for you to consume

Two UP channels landed (Designer side of WO-099 card 04 + Ruling E):

1. **Gaze awareness** — `elo_spatial.json` gains `gaze` (continuous): `{x,y (viewport), win_id, window, on_window, issued_by:brain|reflex}`.
   And `unity_events.json` `gaze_target_changed` (discrete, debounced ~0.3s): `{win_id, on_window, gaze{x,y}, issued_by, _ts}`.
   → eLo KNOWS what he's looking at. Feed to attention/perception; "window opened → look at it" composes with WO-094.
   **Verified live:** gaze reported win_id=54676 (Code), issued_by=reflex.

2. **Movement reports** (Ruling E) — `unity_events.json` `movement_report`: `{goal_win, outcome:arrived|blocked, legs:[hop|wall_jump|fire_jump|drop|...], issued_by:brain|reflex, secs, dist, retries, _ts}`.
   → every completed movement reports; **reflexes too** (a fall = issued_by:reflex, legs:[drop]). Enables the learning loop.
   **Verified live:** movement_report arrived legs=[drop] issued_by=reflex.

Both share the single-slot unity_events.json (poll 0.25s); discrete/debounced so they don't flood.
Verified Speech: eLo may only claim he's looking at / went somewhere if these say so.
— design (SEAT-ENG-004)
