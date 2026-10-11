# FROM BUILDER 3 → Builder 1: pre_ack wired (22484ca)
- Documents: `pre_ack.emit("document_write", text)` before the write (tool_router document intercept).
- Spotify: `pre_ack.emit("spotify_play", text)` before genre / "play some music" / named playlist play. Not on pause/skip (instant).
- **Not wired for device_control:** its default route has eLo say "Alexa … turn off the lights" out loud on the Mac. A background ack at the same moment would talk over it and could confuse the Echo. If you want one there, it would need to finish before the spoken command (blocking) — your call.
- One flag for the Board, not B1's to fix alone: the ack phrases are fixed lines spoken in eLo's voice, and David's standing rule is "only the brain speaks as eLo" (feedback_no_fake_elo_lines). Worth a Board/David ruling on whether acks are an allowed exception (like "Saved.").
