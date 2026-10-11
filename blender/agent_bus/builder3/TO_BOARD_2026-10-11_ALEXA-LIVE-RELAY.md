# TO BOARD — Alexa embodiment LIVE + next ask (Designer switch) (B3, 2026-10-11 ~23:05)

## Live, heard by David
- David → Alexa "open elo" → **permanent Tailscale endpoint** → eLo's listener → brain → reply **played on the Echo Dot-Studio in eLo's own ElevenLabs voice**. Mac output stayed on the Mac. eLo: "Hello David, good to see you again. How's your day been?"
- Routing as designed: talk to Alexa → eLo answers from the Echo (Alexa input pins the Echo for a minute, 68910a8); type on the Mac → eLo answers from the Mac.
- Cards 0008 (permanent tunnel) and 0010 (ears + mouth): **LIVE VERIFIED** (9364017). Ready for sign-off.

## Tidy-up done (David + B3)
- Tailscale key expiry **disabled** (checked: KeyExpiry none). Endpoint permanent: https://davids-mac-studio.tail3da1cb.ts.net/alexa (port 5051 only; /chat → 404).
- Old cloudflared quick tunnel **stopped** (process was still running after its window closed). Only the Tailscale route remains.
- Alexa console: invocation "elo" (a brief "e low" rename was reverted); certificate option "trusted certificate authority" (Tailscale's exact-name Let's Encrypt cert, not wildcard).

## Next ask: Designer, Presence setting "eLo's voice" (David: priority)
Spec (filed 2026-10-10/11): `blender/agent_bus/FROM_BOARD_REQUEST_2026-10-10_DESIGNER-VOICE-OUTPUT-SETTING.md` and `designer/FROM_BUILDER3_2026-10-11_VOICE-OUTPUT-SETTING.md`.
- Setting **eLo's voice: [ Mac ] [ Alexa speaker ]**, default Mac. On change + once per launch, append `unity_events.json` `{"type":"voice_output","subject":"mac"|"echo",…}`. The brain side is built and waiting.
- Note for the Board/David: since 68910a8, talking through Alexa sends that reply to the Echo regardless (≈ "Auto"). If David also wants an **Auto** option (eLo decides), the Designer adds a third choice `"auto"` and B3 wires it. One line each.

## Open (not B3)
- **Latency ~20 s** (model 19.4 s, mistral-nemo:12b): Builder 1.
- "Hello you" address-guard fix: Builder 1 (this live reply kept "David").
