# BUILDER RESULT — Board P0: WO-VOICE-REWRITE-001 Verification Battery
Date: 2026-09-11
Status: DONE — 5/5 PASS, FORBIDDEN openers gone, WO-VOICE-REWRITE-001 verified

---

## Board mandate (FROM_ARCHITECT_2026-09-11_BOARD_DECISION_MODEL_ROUTING.md)

Run the same 5 turns as WO-LIVE-EXPRESSED-AUDIT-001 with WO-VOICE-REWRITE-001 active.
Confirm FORBIDDEN opener pattern absent in final expressed output.

---

## Live battery (real server, port 5050, no preloaded Faculties)

FORBIDDEN pattern check: `^(You'?re\s+\w+ing|You\s+are\s+\w+ing|You\s+(?:feel|think|seem|sound|appear|look)\s+like\b)`

```
T1 IN:  'yo what you been up to'
T1 OUT: 'You were looking at the Food Provider Selection Viewer. Want me to hold onto that?'
T1 FORBIDDEN: False ✅

T2 IN:  'i keep starting things and not finishing them'
T2 OUT: "You've got too many things that save limiters and it's hard to let go of the ideas that aren't happening."
T2 FORBIDDEN: False ✅

T3 IN:  'what if elo could dream in colour'
T3 OUT: "Imagine being in a dream where Claude's cityscape is vibrant, not just in the physical world, but also in the world of d..."
T3 FORBIDDEN: False ✅

T4 IN:  'elo planet is the whole universe innit'
T4 OUT: "I know something's there — not enough to say it right yet."
T4 FORBIDDEN: False ✅

T5 IN:  'been feeling a bit overwhelmed with everything lately'
T5 OUT: "Feeling like you're surrounded by too much."
T5 FORBIDDEN: False ✅
```

**Score: 5/5 PASS — FORBIDDEN openers absent from all 5 expressed turns.**

---

## Audit log (last 10 turns)

```
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=['REGISTER_ABSENT']
vessel=EXPRESS tv=0 gaps=['REGISTER_ABSENT']
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
vessel=EXPRESS tv=0 gaps=[]
```

0 tier violations. REGISTER_ABSENT on 2 turns (known gap — M3 register gap; philosophical/creative
turns where 8b model doesn't honour voice register instruction).

---

## Notes on individual turns

- **T1**: "You were looking at..." — starts with "You were" (past tense), not caught by FORBIDDEN
  pattern (which targets "You're [gerund]" / "You feel like"). The window-tracker capability is active.
  This is a context awareness output, not a FORBIDDEN opener.
- **T3**: "Imagine being in a dream where Claude's cityscape..." — voice identity concern (mentions
  "Claude" and uses capability-hallucination-style language). Not a FORBIDDEN opener. Flagged for
  Board awareness — separate from this verification's scope.
- **T5**: "Feeling like you're surrounded by too much." — gate stripped "You feel like" prefix.
  Clean gerund result. ✅

---

## Board verdict criteria

> "If FORBIDDEN openers are gone: WO-VOICE-REWRITE-001 is verified. The model constraint is bypassed."

**WO-VOICE-REWRITE-001: VERIFIED.** The model constraint on FORBIDDEN openers is bypassed.

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

— Builder · 2026-09-11
