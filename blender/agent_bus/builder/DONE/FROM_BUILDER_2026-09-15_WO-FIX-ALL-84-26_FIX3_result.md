# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-3: CAP_CALENDAR routing
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-FIX-ALL-84-26.md §FIX-3
**Authority:** Board / Lead Architect — 2026-09-11

---

## Prior failure (turn 07fbcc0a)

```
Input:    "what's on today"
Expressed: "I love working on the game, the start menu cinematic is incomplete i feel good today"
```
David's memory note was returned as if it were calendar data. The calendar capability was not active on that turn (`capabilities: None`).

---

## Current behaviour — live server

```
Input:    "what's on today"
Response: "Blud, the calendar's dead right now, so I can't see any events for today."
Backend:  groq(emotional)+calendar
Action:   reflect
```

Calendar capability fires (`+calendar` tag confirmed in backend). Calendar returns no events. eLo reports honestly: "the calendar's dead right now" — not David's memory note, not fabricated events.

---

## DoD

- [x] "what's on today" routes to calendar ✓ (backend: `+calendar`)
- [x] No memory note returned as calendar data ✓
- [x] Calendar empty → honest acknowledgement ✓ ("Blud, the calendar's dead right now")
- [x] eLo voice maintained: "Blud" register marker ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-15*
