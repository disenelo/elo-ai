# Unity Handover — eLo Spatial Awareness

## What Python needs from Unity

Unity should write `blender/elo_spatial.json` every frame (or every 0.5s is fine):

```json
{
  "pos_x": 0.47,
  "pos_y": 0.08,
  "height_px": 120,
  "window": "Google Chrome",
  "screen_w": 2560,
  "screen_h": 1440,
  "_ts": 1234567890.0
}
```

- `pos_x` / `pos_y` — eLo's feet position, normalised 0–1 (0,0 = top-left)
- `height_px` — eLo's current rendered height in pixels (changes with scale)
- `window` — the app name of the window eLo is currently standing on
- `screen_w` / `screen_h` — the display resolution Python should calculate against

## New intent Python will send

Python will write these new intents to `blender_state.json`:

```json
{ "intent": {"name": "jump_to_app", "target": "Google Chrome"} }
{ "intent": {"name": "sit_on_window", "target": "Google Chrome"} }
```

- `jump_to_app` — eLo should animate jumping/moving to the named app's window. 
  Unity finds the window, runs the parkour/jump sequence, lands on top edge.
- `sit_on_window` — after arriving, settle and attach to that window's top edge.

## Freeroam awareness

Python now calculates which windows are nearby and their distances.
It will also pass `[SPATIAL]` context into eLo's brain every turn:

```
[SPATIAL] eLo is on 'Code'. nearest windows: Google Chrome (340px away), Finder (890px away). browser is 340px away.
```

eLo can reference this when deciding to move — "Chrome is close, I can jump there."

## The alive sequence (Python drives, Unity animates)

1. Synthesis observer notices: topic in vault + Chrome tab open about same thing
2. Python: `jump_to_app("Google Chrome")` → Unity runs jump animation
3. Python: `chrome_reader.open_url(url)` → tab opens in Chrome
4. Python: waits 2s → `screen_reader.read()` → reads the page via Gemini vision
5. Python: `sit_on_window("Google Chrome")` → Unity settles eLo on Chrome window
6. Python: eLo speaks what he found

Unity owns steps 2 and 5 visually. Python owns everything else.
