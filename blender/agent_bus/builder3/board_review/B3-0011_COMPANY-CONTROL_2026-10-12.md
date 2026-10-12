# Board review — WO-B3-0011 Company control (Builder 3, 2026-10-12)

## Status: ready, live command deliberately NOT fired overnight
TRIGGER_GO asks for "one confirmed live command". The only working route to David's lights today is eLo saying **"Alexa … turn off the lights" out loud on the Mac speakers** (his lights are Alexa-only; David parked Voice Monkey: "no more APIs"). Doing that at night, with David asleep, means an audible voice in his home plus a physical change to his lights with nobody to confirm it. B3 won't do that unattended.

## Verified overnight (everything except the spoken command)
- Route `speak` (default). Controllable: Lights On, Lights Out, Design Mode, Living Room Sounds.
- "turn off the lights" → Lights Out; "lights on" → Lights On; "are the lights on?" → nothing (questions never act).
- Mac speakers found (CoreAudio index 4); phrase "turn off the lights"; capability `devices` enabled (WO-018).
- Tests: device_control 22 (+ lights wiring 6/6). Spoken path stubbed in tests.

## Live check for David (one line, morning)
Mac volume up, Echo in earshot → type to eLo: **"turn off the lights"** → eLo says "Alexa… turn off the lights" from the Mac → lights go off → eLo: "Asked Alexa: “turn off the lights”."

## Context for the Board
- David called the spoken route "pointless" for himself (an accessibility idea). The real target is **direct** control. A Tuya-protocol device was found on his network (192.168.1.169, `0x00006699` packets), so direct local control is likely possible, but it needs a one-time free Tuya developer sign-in to fetch device keys (David's decision, given "no new APIs without reason").
