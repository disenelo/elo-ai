# FROM BUILDER 3 → BOARD — WO-B3-0011 contextual output: Alexa input pins Echo
**Date:** 2026-10-11
**From:** Builder 3
**To:** Board
**Card:** WO-B3-0011 Company Control (remaining piece from FROM_BOARD_2026-10-10_COMPANY-CONTROL-SCOPE)
**Commit:** 68910a8

---

## What built

Board 2026-10-10 (David L3): *"eLo decides which output device to use — Mac speakers or Alexa — based on context. This is eLo's judgement call … not a user-configurable setting."* Previously the Alexa ingress read David's manual Presence setting (`echo_speaker.voice_output()`), so an Alexa-arriving turn would still play on the Mac if David had set his voice to Mac. That is the opposite of the embodiment ruling.

Change in `capabilities/alexa_ingress.py::_brain` (ears mode): before running the turn, call `echo_speaker.want_for(60)` when the Echo is connected. The input channel is now the strongest contextual signal — David spoke to Alexa → eLo isn't at the Mac → reply through the Echo. The 60 s window covers brain + playback and auto-expires so a later Mac chat turn returns to its default route. If the Echo isn't connected, nothing is pinned and `voice_engine` still falls back to the Mac.

No change to any shared file. No change to `voice_output()` (David's manual setting still works as the baseline for Mac-side conversations). No change to the already-built voice path.

---

## Tests

`tests/test_b3_alexa_ingress.py` — 28 passed, including 2 new:
- `test_alexa_input_pins_reply_to_echo_overriding_manual_mac_setting` — Echo connected, manual setting = Mac, Alexa turn arrives → `es.speaking()` becomes True.
- `test_alexa_input_without_echo_connected_does_not_pin` — Echo disconnected → no `want_for` pin.

Also re-ran `test_b3_echo_speaker.py` + `test_b3_alexa_voice.py` + `test_b3_alexa_turn_model.py` (22 passed) to confirm no regression.

All runs on David's Mac (local sandbox for this seat).

---

## Live turn needed (David)

1. Say to Alexa: *"Alexa, open elo … what's the weather like?"*
2. Confirm eLo's reply plays through the **Echo**, in eLo's voice, even if the Presence setting is Mac.
3. Within 60 s, type the same question into the Mac chat → reply should still go through the Echo (window not yet expired).
4. Wait 60+ s → type into Mac chat → reply returns to Mac.

If (2) fails because the Echo isn't connected over Bluetooth, voice falls back to the Mac — expected, not a bug of this change.

---

## Not in scope for this card

- `voice_output()` as a separate contextual decision (Mac activity, foreground app, time-of-day) — Board can scope a follow-up if it wants a richer judgement than "input channel wins."
- The Mac → Alexa direction (asking eLo via Mac but wanting the voice to come from the Echo) — unchanged; still governed by David's manual setting.
- The "Hello you" re-greeting bug (Builder 1/2 side, filed earlier).

---

## Lock

Created `capabilities/alexa_ingress.py.lock` before edit, removed after commit. (Not on the shared-files list in CLAUDE.md but kept the discipline since the Alexa path crosses with voice_engine's playback choice.)

*Builder 3 · 2026-10-11*
