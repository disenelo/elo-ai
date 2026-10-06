# TO BOARD — Builder 3 — test window request (2026-10-06)
Per `_STANDING_RULE_NO_TESTS_DURING_LIVE_SESSION_2026-10-06.md`: Presence is connected (PID 32256), so Builder 3 is not testing.
**Request:** one window of about 10 minutes, when David is not using eLo, confirmed by the Board.

Why not a separate-port instance? It shares `blender_state.json` (Presence reads it) and TTS. A second server would move David's avatar and speak aloud.

## Queued turns (real server, verbatim JSONL to be filed)
### B3-SPOTIFY-001 — the unverified part (plays audio)
1. "Can you play Four Brothers Soundtrack in Spotify" → playing (verify `/me/player`)
2. "Can you pause Spotify" → "Paused." + `is_playing=false`
3. "resume the music" → "Back on — …" + `is_playing=true`
4. "skip this song" → "Skipped — now …" (track changed)
5. "Can you pause Spotify" → paused (leave it paused)

### WO-RESEARCH-001 (silent)
6. "What is a Kalman filter?" → "Didn't know that one — looked it up on Wikipedia: …"
7. "when did the Berlin Wall fall" → retrieved answer
8. "when did the Berlin Wall fall" → "I know this one — …" (ledger: VERIFIED → KNOWLEDGE, vault spot)
9. "what is the plan" / "what is my dog's name" → no research (regression)

Code is committed: `32b7919 65e8d32 a3aed42` (Spotify), `bf6c8a8` (research).
