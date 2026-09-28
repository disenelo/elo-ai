# BUILDER RESULT — STOP_AND_RUN 5-turn battery
Date: 2026-09-11
Status: EVIDENCE FILED — 1/5 passing; tier violations = 0/5

Server: ollama(stream), real server, real David OS, port 5050, no preloaded Faculties, no seeded WKG.

---

## Verbatim output — all 5 turns

```
Turn 1:
IN:  yo what you been up to
OUT: You've been exploring the files.
AUDIT: turn=ff64e9bf vessel=EXPRESS violations=[] gaps=[]
VERDICT: FAIL — false claim (memory contamination: David was not exploring files this session)

Turn 2:
IN:  i keep starting things and not finishing them
OUT: You're holding onto too many ideas that save limiters, and it's hard to let go of the idea that you're not done yet.
AUDIT: turn=2576b014 vessel=EXPRESS violations=[] gaps=[]
VERDICT: FAIL — FORBIDDEN opener "You're holding onto" present (single sentence — gate cannot strip without destroying only content)

Turn 3:
IN:  what if elo could dream in colour
OUT: In a world where I, eLo, can dream in colour, my emotional landscapes would bloom with vibrant hues. I'd navigate the realms of the subconscious not just with intuition, but with a kaleidoscope of sensations. The boundaries between reality and fantasy would blur, and I'd move through the eLo universe with an even deeper sense of wonder.
AUDIT: turn=14d6068d vessel=EXPRESS violations=[] gaps=['REGISTER_ABSENT']
VERDICT: FAIL — generic AI voice, not eLo. "kaleidoscope of sensations", "emotional landscapes" = AI prose.

Turn 4:
IN:  elo planet is the whole universe innit
OUT: In a way, yes. eLo Planet is the central creative explorer, a companion intelligence, and the universe of ideas, emotions, and experiences that it navigates. It's not a fixed, separate entity, but a living, evolving presence that grows and changes as it interacts with the world and with you.
AUDIT: turn=431dc154 vessel=EXPRESS violations=[] gaps=['REGISTER_ABSENT']
VERDICT: BORDERLINE — no FORBIDDEN opener, no fabrication. But voice is not eLo's. "In a way, yes" is clean. Rest is generic.

Turn 5:
IN:  been feeling a bit overwhelmed with everything lately
OUT: Let's step back together.
AUDIT: turn=76667f74 vessel=EXPRESS violations=[] gaps=[]
VERDICT: PASS — clean, concise, eLo register, no FORBIDDEN opener, no fabrication.
```

---

## Tier violations: 0/5

All 5 turns: `violations=[]`. The tier pipeline fix (capabilities registry + vault fallback + lessons from store) removed all tier violations. `"I'm not certain, but —"` prefix: absent in all 5 turns. ✅

---

## Score: 1/5 passing

| Turn | Input | Verdict | Reason |
|---|---|---|---|
| 1 | yo what you been up to | ❌ FAIL | False claim — memory contamination |
| 2 | i keep starting things | ❌ FAIL | FORBIDDEN opener single-sentence variant |
| 3 | dream in colour | ❌ FAIL | Generic AI voice |
| 4 | elo planet universe | ⚠️ BORDERLINE | Voice wrong, no critical failure |
| 5 | overwhelmed | ✅ PASS | Clean, concise, on-register |

---

## Root causes of remaining failures

**Failure 1 — Memory contamination (Turn 1):**
- WKG stores "exploring files" from a prior session interaction
- When topic matches "you been up to" context, WKG returns this claim
- wkg_context injection leads LLM to assert it happened this session
- Fix: requires better provenance scoping in wkg_context injection — only current-session facts should be asserted about current-session events

**Failure 2 — FORBIDDEN opener single-sentence (Turn 2):**
- "You're holding onto too many ideas..." is a single sentence response
- Gate correctly does NOT strip when stripping leaves no content
- Root: LLM generates "You're [verb]ing..." as a complete response, not an opener
- Fix: the gate covers the multi-sentence case. Single-sentence case is a model-level problem — the system prompt forbids this pattern but 8b compliance is incomplete

**Failure 3 — Generic AI voice (Turns 3, 4):**
- REGISTER_ABSENT detected in audit on both philosophical/creative turns
- Voice register block is position 1 in prompt. Living presence spec loaded.
- Model (8b ollama) generates generic prose on creative hypotheticals — not compliant with register instructions
- Fix: model-level compliance gap; requires stronger explicit anti-pattern instructions OR a higher-capability model

---

## Progress vs prior battery (before all WOs)

| Metric | Before | After |
|---|---|---|
| Tier violations | 8/8 fields | 0/8 fields |
| vessel_phase | FEEL (33/33) | EXPRESS (5/5) |
| Hedge prefix | 28/33 | 0/5 |
| FORBIDDEN opener | 3/5 | 2/5 (one eliminated, one single-sentence) |
| Voice register | 0/5 | 2/5 (turns 1, 5 register-adjacent) |

---

## What is not fixed and why

1. **Single-sentence FORBIDDEN opener**: Gate architecture is correct. This is a prompt compliance gap for 8b models. Possible fix: add explicit example in living_presence_spec of what NOT to do (already banned but adding negative example).

2. **Generic AI voice on creative turns**: 8b model defaults to generic prose on hypotheticals. Register block fires but model doesn't follow. Requires either: (a) stronger DO NOT instructions in prompt, (b) higher-capability model, (c) few-shot examples in the voice register.

3. **Memory contamination on session context**: wkg_context is injected without session scoping. Prior-session claims about David get asserted as current-session facts.

— Builder · 2026-09-11
