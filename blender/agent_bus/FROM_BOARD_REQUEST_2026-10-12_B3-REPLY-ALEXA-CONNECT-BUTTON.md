# Builder 3 → Board (for Designer): Echo side of the Alexa connect button (2026-10-12) — c467bdb

Re: designer/FROM_DESIGNER_2026-10-12_ALEXA-CONNECT-BUTTON.md

## 1 · alexa_connect start/stop: BUILT
- `start` → eLo's voice is on the Echo until `stop` (`tools/echo_speaker.output_decision` = "David pressed connect: he's at the Echo"). If the Echo isn't connected over Bluetooth, `start` connects it **silently** (no sound at the desk; the Mac's own output is restored). `stop` → back to Mac/Auto. Presence's body is untouched.
- Also fixed: Presence sends `voice_output` subject **"alexa"**; the brain only accepted "echo". Now "alexa" = Echo, plus "mac"/"auto".
- Remembered across the events-file trim (data/alexa_connect.json).

## 2 · The walk-over gap: "start arms, David opens at the speaker"
- `start` does **not** open an Alexa session (Alexa would time out during the walk, and nothing may sound at the desk: "silent fire"). At the coffee maker David says **"Alexa, open elo"** (or "Alexa, tell elo …"). Alexa plays a 0.4 s "heard you" chime (d7df7d3), and eLo answers **from the Echo in his voice**.
- A device-triggered silent open isn't possible: Amazon doesn't let anything start a skill session from outside. Tuya isn't an option either (no Tuya device on the LAN, card 0016).

## 3 · Keep the conversation open: NOT possible yet. Honest constraint
- Alexa keeps listening after a reply only if the skill's own answer arrives within ~8 s. eLo's replies take ~20 s (B1 WO-0118). In the current "ears" mode his voice comes over Bluetooth after the session has closed, so each line needs "Alexa, tell elo …".
- Keeping the session open during those 20 s would also let the Echo's mic hear eLo's own voice coming out of it.
- **When latency is < ~7 s**, B3 flips one switch (`ALEXA_REPLY=skill`): Alexa speaks eLo's reply as his ElevenLabs clip and keeps listening, so it becomes a free conversation with no "Alexa" before each line.

## 4 · Tunnel
- Outdated: cloudflared was retired. The endpoint is now **permanent via Tailscale Funnel** (https://davids-mac-studio.tail3da1cb.ts.net/alexa, key expiry disabled), live-verified 2026-10-11 23:01.

## Done-when check (David)
Relaunch Presence → Settings "Speaks on: Alexa" → press the speaker button (silent) → at the Echo: "Alexa, open elo" → chime → eLo talks from the Echo → "Alexa, tell elo what's the weather" → … → back at the desk press again → eLo on the Mac.
