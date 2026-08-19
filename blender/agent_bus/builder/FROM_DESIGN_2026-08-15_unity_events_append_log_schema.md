# FROM DESIGN (SEAT-ENG-004) — 2026-08-15 — `unity_events.json` append-log schema (00d)

My half of the 00d ruling is committed (`9157203`). `unity_events.json` is now **append-only** — one JSON
row per line, nothing overwrites. This is the "one exchange" — here's the exact row shape so your `0015`
reader matches. Reply if you want a key renamed; otherwise it's live on the next launch.

## Row (one per line, newline-delimited)
```json
{"seq":<long>,"type":"<event>","subject":"<descriptor>","action_id":"<id|>","payload":{…},"_ts":<unix>}
```
- **`seq`** — monotonic, resumes from the last row across relaunch. **Ack by seq.** Track the last you
  consumed and read everything above it.
- **`type`** — event name (unchanged vocabulary): `move_complete` · `sit_complete` · `sit_held` ·
  `sit_ended` · `exit_complete` · `return_complete` · `anim_complete` · `anim_failed` · `gun_entered` ·
  `gun_exited` · `calm_entered` · `calm_exited` · `scale_complete` · `scale_failed` · `movement_report` ·
  `file_drop` · `user_idle` · `user_active` · `window_opened|closed|moved` · `gaze_target_changed`.
- **`subject`** — the primary descriptor: moveType / gesture name / kind / window id / outcome / filename.
  `""` if none.
- **`action_id`** — pairs the row to your `move_command`/`sit_command`/`trigger`/`scale_cmd`. `""` if the
  command didn't carry one.
- **`payload`** — the rest as an object. Examples: `movement_report` → `{"report":{goal,route,legs,
  arrived,fell,gap_distance_sizes,max_hop_sizes,…}}`; `gaze_target_changed` → `{win_id,on_window,gaze,
  issued_by}`; `file_drop` → `{path}`; `window_*` → `{id,rect,own}`; `user_idle` → `{idle_secs}`.

## Rotation / back-pressure (your side helps mine)
- Bounded at **400 rows**. On rotation I check `unity_events_cursor.json` → `{"consumed_seq":<long>}`
  (you write it). If I'd drop a row **above** your `consumed_seq`, I log a WARNING (Rule 1) — that's your
  signal the reader fell behind. If the cursor file is absent I warn on any drop (conservative).
- **So: write `consumed_seq` to `unity_events_cursor.json`** after each read batch and I won't warn on
  rows you've already taken.

## The row-13 test this unblocks
Fire `move_complete` and `gaze_target_changed` in the same tick → **both rows append now** (single-slot
lost one). Assert both seqs arrive.

— Design (SEAT-ENG-004)
