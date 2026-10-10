# Request → Designer (via Board): "eLo's voice: Mac / Alexa" setting in Presence (B3, 2026-10-10)

**David, 2026-10-10:** "I want it through the Mac, and in settings pass that to Designer for the UI, where I can choose Alexa or Mac, as I want to test. I don't want all my audio coming through the Bluetooth speaker, just eLo, and he can hear me. So we can use the tech of Alexa as a stepping stone before we do a robot embodiment."

## Brain side: DONE (B3)
- `tools/echo_speaker.py` (185ba6e): eLo's voice output is `"mac"` (default) or `"echo"`. The newest `voice_output` event from Presence wins and is remembered in `data/voice_output.json` (survives restarts and the events-file trim). Choosing `echo` connects the Echo Dot-Studio over Bluetooth and immediately puts the Mac's own output back on Mac Studio Speakers. **Only eLo's voice moves.**
- `voice/voice_engine.py` (0747736, B1's file, edited under lock): eLo's main voice (ElevenLabs/OpenAI) plays on the Echo when the setting is `echo` **and** the Echo is connected. Otherwise it plays on the Mac exactly as before, never silence. The inner voice stays on the Mac.
- Alexa (185ba6e) is now **ears only** by default: David's words go to the brain, Alexa says nothing, and eLo answers from whichever speaker is chosen. No 8 s limit.

## Ask (Designer, Presence settings)
1. A setting: **eLo's voice: [ Mac ] [ Alexa speaker ]**. Default **Mac**. Plain labels; "Alexa speaker" = Echo Dot-Studio.
2. On change, **and once on every launch** (Presence's own saved value is the source of truth), append to `blender/unity_events.json` with the usual writer/seq:
   ```json
   {"type": "voice_output", "subject": "echo", "action_id": "", "payload": {"issued_by": "david"}, "_ts": <unix seconds>}
   ```
   `subject` is exactly `"mac"` or `"echo"`.
3. No other change is needed. Lipsync and bubbles work as now (the voice engine still drives lipsync; only the playback device differs).
4. Optional, later: a small "Echo connected / not connected" indicator. The brain can publish it if wanted; say so and B3 adds it.

## Done when
David flips the setting to **Alexa speaker** → eLo's next spoken line comes out of the Echo; his other Mac sound (music, videos) stays on the Mac. Flip back to **Mac** → eLo is back on the Mac. "Alexa, open elo / tell elo …" works with either: Alexa hears, eLo answers from the chosen speaker.

## Until the UI exists
B3 can set it from the terminal for David's tests: `python -c "from tools.echo_speaker import set_voice_output; set_voice_output('echo')"` (or `'mac'`).
