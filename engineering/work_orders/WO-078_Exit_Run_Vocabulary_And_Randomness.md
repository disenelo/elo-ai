# WO-078 — Exit-run: leave/space vocabulary (+ UK slang) + autonomous randomness

**Owner:** Builder (intent vocab → exit command) + Designer (autonomous exit-run frequency). **Priority:** P2.
**Status:** OPEN — spec'd 2026-08-07 (David live). **Extends:** WO-045 (take-five → embodied EXIT) + WO-045b
(exit-gate ordering). **Canon:** conversation is engagement; eLo grants space on request (Vision Spine).

## David's ask (2026-08-07)
1. The **exit run isn't random enough** — the autonomous version fires too predictably; it should be rarer /
   more varied.
2. The exit run should be **triggered by natural "leave / give me space" phrasing, including UK slang** — not
   just the literal "take five". e.g. "give me a moment", "give me a sec/minute", "give me a mo", "give me
   some space / room", "leave me be", "need a breather", "in a bit", "give us a minute", "make yourself
   scarce", "laters" — British everyday ways of asking someone to step off for a bit.

## Scope
### Builder — leave/exit intent vocabulary (+ guard the over-trigger)
- Broaden the leave/step-out intent to catch natural + UK-slang "give me space / take a break" phrasings
  (list above, non-exhaustive) → emit the EXIT command (take-five behaviour: pop off, return on call).
- GUARD the over-trigger David saw ("when I said exit you left again"): a bare mid-phrase "exit" shouldn't
  fire a leave — require it to be a real dismissal/leave intent, not the word appearing in other context.
- False-positive guards: "don't leave" / "give me a second to think" (settle, not dismissal) → NOT exit.

### Designer — autonomous exit-run randomness
- The AUTONOMOUS exit-run (eLo choosing to run off on his own) should be less frequent and more varied —
  lower base chance + jitter, not a predictable cadence. Commanded exit (the phrases above) is unaffected.

## Definition of Done
"give me a moment" / "give me some space" / "take five" / slang variants → eLo does the embodied EXIT and
returns on call. A bare "exit" mid-sentence or a settle-phrase does NOT trigger a leave. Autonomous exit-run
reads as occasional/spontaneous, not on a timer.

## Test — WITHOUT David
- Builder: ~12 leave/space + slang phrasings → `leave_command`/exit intent; 4 non-leave controls (incl.
  "give me a second to think", "don't leave") → NO exit.
- Designer: autonomous exit-run frequency measurably reduced + randomised (inject/log check).

## Lane
Builder (Python intent) + Designer (Unity autonomous frequency). Ties WO-045/045b (exit chain already built +
ACK-gated).
