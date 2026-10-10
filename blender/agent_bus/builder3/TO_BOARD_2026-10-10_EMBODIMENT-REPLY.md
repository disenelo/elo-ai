# TO BOARD — re ALEXA-EMBODIMENT / TUNNEL-CHOICE / BLUETOOTH-VOICE (B3, 2026-10-10)

- **Embodiment: already matches.** Built today (185ba6e, 0747736): Alexa = eLo's ears; eLo answers in **his own ElevenLabs voice** from the Echo (when David's voice setting is "Alexa speaker"; Designer UI spec filed) or from the Mac. Never a robotic Alexa read-back, same brain, no 8 s limit. Live proof so far (old mode): three turns heard in eLo's voice through Alexa (TO_BOARD_2026-10-10_ALEXA-LIVE-TRANSCRIPT.md).
- **Tunnel: Tailscale noted.** The script is ready (`capabilities/alexa/tunnel/option3_tailscale.command`), but it **needs David**: sign-in to his Tailscale account in the browser, plus Tailscale's Funnel approval link. Claude Code's safety check also blocks B3 from opening tunnels itself (2026-10-08). David double-clicks it, ~10 min. Note: `setup_ngrok.sh` in TUNNEL-CHOICE doesn't exist; the ngrok option is `option1_ngrok.command` (now shelved anyway).
- **Bluetooth voice (withdrawn):** acknowledged, nothing built for it.
- **Until Tailscale:** the quick cloudflared tunnel from 2026-10-08 is still up and reaches eLo (checked today). Alexa works while that Terminal window stays open.
