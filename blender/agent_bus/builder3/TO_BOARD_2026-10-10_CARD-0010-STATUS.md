# TO BOARD — card 0010 Alexa Ears + Mouth: status (B3, 2026-10-10)

The card's dependency is already met: **a tunnel is live** (David's quick cloudflared tunnel), and the Test tab is on Development (David's screenshot, 2026-10-10 ~01:50). It isn't permanent yet; that's card 0008 (David picks ngrok/Cloudflare/Tailscale).

## Done
- **Ears:** Alexa → tunnel → eLo's listener → his brain. Live, with transcript (TO_BOARD_2026-10-10_ALEXA-LIVE-TRANSCRIPT.md).
- **Mouth (David's design, 2026-10-10, supersedes the card's "Alexa TTS via alexa_agent.py"):** David chose to have eLo's voice come from **the Mac or the Echo speaker, his setting**, not Alexa's TTS. Built in 185ba6e + 0747736. Alexa is ears only by default; eLo answers in his own ElevenLabs voice from the chosen speaker whenever ready, so the 8 s limit no longer applies. Only eLo's audio moves. Designer UI spec: FROM_BOARD_REQUEST_2026-10-10_DESIGNER-VOICE-OUTPUT-SETTING.md.
- Earlier mode (Alexa speaks eLo's reply as an ElevenLabs clip, ALEXA_REPLY=skill) proven live: three turns heard.

## Remaining
- Live test of the new mode: needs a Presence relaunch + David.
- **Latency target "under 8 s":** in the old mode each reply took ~18 s on mistral-nemo:12b even without the model swap. The new mode removes Alexa's 8 s limit, but the brain's reply time is unchanged (B1's backend/prompt).
- **`response_mode: voice` → shorter, plain replies:** prompt_builder is B1's. B3 can mark Alexa turns (e.g. a per-turn flag next to the Alexa model override) if B1 wants to read it.
- Brain defects seen live: "Hello you" (address guard, B1) and re-greeting instead of answering (B1/B2).
