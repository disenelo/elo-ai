# UNITY AGENT HANDOVER — WO-034 App Reply Not Firing

**Date:** 2026-08-13
**From:** Builder (eLo OS Python)
**To:** Unity / UI Agent

## Arbiter test result (run 2026-08-13)

```
curl -s -X POST http://localhost:5050/chat \
  -H 'Content-Type: application/json' \
  -d '{"text":"hello"}' --max-time 10
```

```json
{"response": "Ello.", "bubbles": ["Ello."], "mode": "celebrate", "backend": "direct"}
```

**Verdict: eLo OS is done. The Python /chat endpoint returns a real, non-mock reply.**
The bug is on the Unity side — the app is not consuming or displaying the reply it receives.

## What the Python side sends

Every `/chat` response has:
- `response` — the spoken text string
- `bubbles` — list of display strings (usually same as response)
- `mode` — eLo's current expressive mode
- `backend` — which LLM backend handled it

The server also writes `blender/blender_state.json` (avatar expression/mode) and queues voice output.

## What Unity needs to do

1. **POST to `/chat`** with `{"text":"<user input>"}` and consume the JSON response.
2. **Display** `bubbles[0]` (or `response`) in the chat panel.
3. **Read `blender_state.json`** for avatar mode/expression updates.

If the app was previously consuming the response but stopped: check whether the HTTP request is
completing (not timing out), and whether the response JSON is being parsed. The endpoint is stable at
`http://localhost:5050/chat`.

## Files not to touch

`server.py` — Python side is correct. Do NOT edit it for this WO.

## Done when

David talks to the desktop app → eLo replies (spoken + shown), same as CLI.
