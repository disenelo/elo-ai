# Board Review — DEMO-SPRINT: voice_output event routing
**Date:** 2026-10-11
**Builder:** Builder 1
**Commit:** c125cb7
**Status:** READY FOR BOARD REVIEW

## What was built

`server.py` unity_events poller now handles `{type:"voice_output", subject:"mac"|"alexa"|"auto"}` events from the Presence UI.

- `"mac"` → forces Mac speakers via `echo_speaker.set_voice_output("mac")`
- `"alexa"` → forces Echo Dot via `echo_speaker.set_voice_output("echo")`
- `"auto"` → clears to system default (`"mac"`, letting existing contextual Echo logic decide)
- Unknown subjects → logged and ignored (no crash)

## Server-side status

Builder 1 half is ready. This wires the server side of the designer's demo-sprint item 2 (voice output setting UI). No further work needed from Builder 1 — the moment Designer writes `{type:"voice_output", subject:"mac"|"alexa"|"auto"}` to `unity_events.json`, routing updates immediately on the next poller tick (< 100ms).

## Board verify

Send `{"type":"voice_output","subject":"alexa","_ts":1234567890,"seq":99}` to `unity_events.json` → `tools/echo_speaker.voice_output()` returns `"echo"`.

*Builder 1 · 2026-10-11*
