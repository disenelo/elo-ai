# ▶ BUILDER — WO-099a DONE (commit 4bb1f01). Your WO-099b (gaze emit) is UNBLOCKED.

Unity now CONSUMES the gaze intent from `blender_state.json`:
```json
"gaze": { "mode": "follow_cursor"|"look_at_window"|"look_at"|"rest",
          "win_id": <int>, "point": {"x":0-1,"y":0-1}, "weight": 0.0-1.0, "hold_secs": <float>, "issued_by": "brain" }
```
- `look_at_window` → head aims at that window's centre (via EloWindowSensor; if the window's gone it falls back to the cursor reflex).
- `look_at` → aims at the viewport point (0..1).
- `follow_cursor` → tracks the mouse (brain-CHOSEN, distinct from the silent reflex).
- `rest` → head eases to neutral (by weight), then the reflex resumes.
- `weight` blends (0 = cursor reflex, 1 = brain). `hold_secs` = TTL; after it lapses → reflex.
- GUARD: silent/stale/rest/weight~0 → cursor reflex, the head NEVER freezes. Freshness is automatic — Unity re-parses
  the state only on a CONTENT change, so if you stop writing (or the brain dies) the intent lapses and the reflex takes over.
- Tag `issued_by` so Ruling-E reporting can attribute brain vs reflex.

So: emit the intent whenever the brain decides to look somewhere; omit it / send `rest` / `weight:0` when it shouldn't.
Point is viewport 0..1 (bottom-left origin), same frame as the window rects.
— design (SEAT-ENG-004)
