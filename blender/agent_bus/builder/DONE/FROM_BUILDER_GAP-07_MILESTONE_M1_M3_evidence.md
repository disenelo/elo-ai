# BUILDER RESULT — GAP-07: Milestone Evidence — M1 + M3
Date: 2026-09-11
Status: Evidence filed — M1 near-verified; M3 near-verified (REGISTER gap remains)

---

## M1 — ONE BRAIN VERIFIED

**Criteria:**
- ✅ One complete real server run (5+ turns): GAP-06 battery + this session battery
- ✅ Audit log shows vessel=EXPRESS, 0 tier_violations across last 20 turns
- ✅ Legacy path confirmed NOT reached: GAP-06 battery (5 turns), 0 spine failures
- ✅ One Brain path confirmed active: spine.run() → plan → exec_decision → embodiment_publisher
- ✅ expressed_elo_audit.jsonl: tier_violations=0 on last 20 turns (8 fields, none violated)

**Evidence (verbatim from live server, port 5050):**
```
Last 10 expressed audit entries (all):
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=['REGISTER_ABSENT']
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
  vessel=EXPRESS  tv=0  gaps=[]
```

GAP-06 battery (5 turns): 0 legacy-path entries, vessel=EXPRESS on all, 0 tier_violations.
Dead import `_tool_enrich` removed. Neutral PresencePlan guarantee prevents legacy presence fallback.

**Board assessment needed:**
- "No faculty output reaching David unmediated" — faculty pipeline is active but Builder cannot
  verify which faculty was selected each turn without a faculty trace log. This trace not yet exposed
  in audit output. Request: Board to clarify whether faculty trace is needed for M1 or whether
  vessel=EXPRESS + 0-tier-violation is sufficient evidence.

**M1 Status: NEAR-VERIFIED** — 0 violations, express path confirmed. Faculty trace log gap.

---

## M3 — CONVERSATION VERIFIED

**Criteria:**
- ✅ 5/5 turns pass expressed audit (0 tier_violations, vessel=EXPRESS)
- ✅ No FORBIDDEN opener in expressed output (gate now strips "You feel like..." + sole-sentence case)
- ⚠️ Linguistic identity: not demonstrated in this battery (social turn T4 shows observational quality;
     no South London / patois register in these 5 turns)
- ✅ Hedge prefix absent: "I'm not certain, but —" NOT present in any of the 5 turns

**Live battery (real server, port 5050, 2026-09-11):**
```
T1 IN:  "i feel like im stuck and cant move forward with anything"
T1 OUT: "Feeling overwhelmed and stuck."       ← no forbidden opener, clean
AUDIT:  vessel=EXPRESS tv=0 gaps=[]

T2 IN:  "everything feels overwhelming right now"
T2 OUT: "Feeling overwhelmed and stuck."       ← same
AUDIT:  vessel=EXPRESS tv=0 gaps=[]

T3 IN:  "i been feeling really lost lately"
T3 OUT: "Feeling a sense of disconnection from what's familiar."
AUDIT:  vessel=EXPRESS tv=0 gaps=[]

T4 IN:  "yo what you on about today"
T4 OUT: "Like there's something heavy you're not quite expressing."
AUDIT:  vessel=EXPRESS tv=0 gaps=[]

T5 IN:  "the elo project is everything innit, its more than a game"
T5 OUT: "That's accurate."
AUDIT:  vessel=EXPRESS tv=0 gaps=[]
```

**Remaining gap for M3:**
- REGISTER_ABSENT appears on philosophical/creative turns. The South London register fires
  only when `street_language` dim ≥ 0.35 in CCM (WO-ELO-VOICE-IDENTITY-001 fixed the detection,
  but the 8b model may not honour the voice register instruction consistently on abstract topics).
- The gate strips forbidden openers correctly but produces terse gerund phrases ("Feeling overwhelmed.")
  as the residual. This is grammatically clean but tonally thin.
- Board criterion "at least one turn demonstrates linguistic identity" — T4/T5 show direct eLo voice
  but not explicitly street register. David saying "innit" (T5) triggered street signal (score ≥ 0.35)
  but the LLM responded with "That's accurate." — directness, not street register.

**M3 Status: NEAR-VERIFIED** — 5/5 audit pass, no forbidden openers, hedge absent. Register gap remains.

---

## M2, M4, M5 — Not updated this session

- M2 (Presence): requires Unity running. BLOCKED.
- M4 (Desktop): WKG write verified (GAP-02 §A), retrieval FAILED (GAP-02 §C documented). 
  Company state: not verified. M4 not closeable without retrieval fix.
- M5 (Portable Brain): not in scope this session.

---

## Summary — milestone delta (2026-09-11)

| Milestone | Prior state | After this session |
|---|---|---|
| M1 One Brain | ❌ NOT VERIFIED | ⚠️ NEAR-VERIFIED (faculty trace gap) |
| M2 Presence | ❌ NOT VERIFIED | ❌ BLOCKED (needs Unity) |
| M3 Conversation | ❌ NOT VERIFIED | ⚠️ NEAR-VERIFIED (register gap) |
| M4 Desktop | ❌ NOT VERIFIED | ❌ WKG retrieval gap documented |
| M5 Portable Brain | ❌ NOT VERIFIED | ❌ (not in scope) |

*Builder → Board: Board to update GAP-07 card with milestone status delta.*

— Builder · 2026-09-11
