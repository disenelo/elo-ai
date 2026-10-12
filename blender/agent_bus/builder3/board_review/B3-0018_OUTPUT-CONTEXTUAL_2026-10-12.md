# Board review — WO-B3-0018 eLo chooses output device (Builder 3, 2026-10-12) — e7e11fa

- `tools/echo_speaker.output_decision()` → (device, why). Default **auto**:
  1. Echo not connected → Mac (never silence).
  2. David just spoke through Alexa → Echo (60 s window, 68910a8).
  3. Presence setting "mac"/"echo" → override.
  4. auto: Mac keyboard/mouse idle ≥ 5 min (ELO_AWAY_IDLE_S) → Echo ("in the room, not at the desk"), else Mac.
- voice_engine (B1's file) already routes through `speaking()` (0747736), so no B1 change was needed.
- Board scenarios: (1) desk → Mac ✅ (2) through Alexa → Echo ✅, both tested. Live right now: ('mac', 'auto: David at the desk'). Scenario 2 was proven live 2026-10-11 23:01 (David heard eLo on the Echo).
- **Designer (not B3's file):** the voice setting UI should offer **Auto / Mac / Alexa speaker**, default Auto; event subject `"auto"` is now accepted.
