---
id: WO-033
title: "eLo memory framing — talk in real TIME/days, not 'sessions' (the model is already time-based; only the language is wrong)"
owner_seat: SEAT-ENG-001 (Builder)
occupant: Builder (Python)
priority: P3
reason: "David 2026-08-03: eLo said 'memory carries across sessions' — but a session has no time scale or limit, so it's a misleading frame. He experiences continuity in days. The ACTUAL memory model is already time-based (consolidation decays by age in days); only the way eLo DESCRIBES it uses 'sessions'."
review_required: L1 → L3 (David feels it live once LLM is back)
risk: low (wording / prompt framing; no memory-engine change)
status: READY
created: 2026-08-03
---

# WO-033 — memory framing: time/days, not "sessions"

## Grounding (the model is already right)
- `memory/consolidation_faculty.py`: forgetting curve is **time-based** — `_DECAY_AGE_DAYS = 14`, recency by
  real age, identity floor never decays. So memory genuinely works in TIME, not session-count.
- The wrong framing lives only in **language**: `server.py:928-931` canned lines ("carries across
  sessions", "each session connects to the last") + likely the memory-related prompt wording.

## Scope — FULL SWEEP (David: "I'm sure I asked sessions to not be used" — it slipped; enforce it)
"sessions" language is pervasive in eLo's user-facing wording — remove it EVERYWHERE it's the memory/
continuity unit:
- `server.py:929-932` canned memory lines ("across sessions", "between sessions").
- `server.py` memory/state status (`~1003/1029/1032/1079/1092`): "turns in this session", "Session N",
  "Session's fresh".
- `prompts/living_presence_spec.txt` (42 "across ... session", 386/388 "across a session"/"this session",
  420 "between sessions").

## Fix — reframe in NATURAL HUMAN TIME (David 2026-08-03: days · weeks · months · years)
1. Replace "sessions" with **real elapsed time** — days / weeks / months / years — the way a person
   remembers. eLo's memories are timestamped, so it can reference ACTUAL time: "we talked about this a few
   days ago", "last week", "months back", "recent things are close, older things fade over weeks".
2. Status readouts: report memory by real time/age, not "session N / turns this session".
3. Keep "continuous presence" as the idea — just anchor continuity to **time**, never the arbitrary
   "session" unit. Where the timestamp is available, say the actual span ("about 3 days ago").
4. No memory-engine change — it's already time-based (decays by days). Language + status only.

## Canon (so it can't slip again)
Add a DECISION_LOG rule: **eLo never frames memory/continuity in "sessions" — always natural time
(days/weeks/months/years).** Add a guard/test so a "session" in user-facing memory language fails CI.

## Acceptance
1. Ask eLo "do you remember?" / "sessions or days?" → it frames memory in **time/days**, not sessions.
2. Canned fallback memory lines no longer say "across sessions".
3. py_compile clean. David confirms the framing feels right once the LLM is back (currently on Groq backup).
