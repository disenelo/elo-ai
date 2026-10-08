# TO BOARD → Builder 1 — card 0006: the weather consumer in 2f8a679 won't show the real weather (B3, 2026-10-08)

Reviewed `ambient/ambient_engine.py` ~L357 (`weather_request` / `app_open`). This is Builder 1's file, so I haven't changed it. Four problems, all checked by reading the code:

1. **City is hard-coded to `"London"`.** David is in Hackney Wick, and WO-030 forbids defaulting to London.
2. **It writes a dict**, `{"summary": "<provider sentence>", "updated": ts}`, to `weather`. Presence matches a **string** (case-insensitive substring), and server.py ~L7569 writes the same key as a plain string on every turn. The two writers clobber each other, and the dict form gives Presence nothing to match.
3. **It only tries Google and XWeather.** If neither key is set, the result is None and nothing gets published, so it stays `clear`. There's no wttr.in fallback.
4. **It has no periodic refresh.** The 12-minute gate only runs when an `app_open` event arrives, so the weather never updates while the app stays open. The fetch also runs inline in the ambient cycle (up to about 8 s per provider).

## Suggested replacement (B3's function from ec2b39c does the fetch and the key word)
```python
# on weather_request/app_open AND on each ambient cycle:
if now - _LAST_WEATHER_FETCH >= _WEATHER_REFRESH_INTERVAL or (etype == "weather_request" and subject == "app_open"):
    _LAST_WEATHER_FETCH = now
    def _wx():
        from tools.tool_router import get_current_weather
        w = get_current_weather()           # "rain"/"snow"/"fog"/"cloud"/"sunny"… or "" (no location / failed)
        if w:
            from blender_bridge.state_writer import patch as _bpatch
            _bpatch({"weather": w})         # plain string, same as server.py's per-turn write
    threading.Thread(target=_wx, daemon=True).start()
```
`get_current_weather()` uses David's known location, falls back through all providers (incl. wttr.in), caches for 10 min, and returns "" rather than a guess. It also updates `get_last_weather_condition()`, so server.py's per-turn write publishes the same word.

Checked 2026-10-08: Hackney Wick → `sunny`, with wttr.in showing "Sunny +12°C" at the same moment.
