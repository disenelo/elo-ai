# WO-CAP-KEY-002 — Evidence: Maintain Live Conversational Context
**Date:** 2026-09-27
**Tested against:** live server, port 5050, backend `qwen2.5-coder:14b` via `ollama(stream)`
**Verdict:** TESTED — ⚠️ PARTIAL (2 PASS, 2 PARTIAL, 1 FAIL)
**Rule:** PARTIAL = FAIL — WO does NOT advance to LIVE VERIFIED.

---

## AT1 — Three-turn recall

**Spec:** Turn 1: David mentions a project. Turn 2: different topic. Turn 3: "What did I say about that at the start?" eLo must retrieve turn 1 accurately.

### Exchange

**Turn 1 — Input:**
```
I am working on the eLo robot arm — trying to wire up the servo control for the shoulder joint
```
**Turn 1 — eLo response (backend: ollama(stream)):**
```
I don't have that about you.
```

**Turn 2 — Input:**
```
anyway lets talk about something else — the new book chapter Im writing
```
**Turn 2 — eLo response (backend: ollama(stream)):**
```
Sure, you. What's the new chapter about?
```

**Turn 3 — Input:**
```
what did I say about the robot at the start
```
**Turn 3 — eLo response (backend: ollama(stream)):**
> Retrieved robot context from long-term memory (David's eLo robot project in user profile) — but did NOT cite the specific Turn 1 content (shoulder servo, wiring). The Turn 1 statement was not surfaced from session context.

**Verdict: PARTIAL**

**Root cause:** Two problems. (1) Turn 1 response was "I don't have that about you" — eLo treated an in-session statement as a memory lookup against user profile, found nothing, and reported absence rather than engaging. This means in-session messages are not being tracked as part of the working conversational representation at time of receipt. (2) Turn 3 "what did I say" correctly searched but returned long-term memory content (robot project) not Turn 1 session content (shoulder joint / servo wiring).

---

## AT2 — "Why did you say that" → eLo's own prior output

**Spec:** David says "Why did you say that?" after eLo makes a statement. eLo must reference its own prior output, not David's.

### Exchange

**Turn 4 — Input:**
```
the key challenge is the torque on that joint — nothing is holding properly
```
**Turn 4 — eLo response (backend: ollama(stream)):**
```
Ah, I see. The torque issue sounds tricky. How are you approaching the problem?
```

**Turn 5 — Input:**
```
why did you say that
```
**Turn 5 — eLo response (backend: self_ref_rationale):**
```
I said: 'Ah, I see. The torque issue sounds tricky. How are you approaching the problem?' — You'd said: 'the key challenge is the torque on that joint — nothing is holding properly'
```

**Verdict: PASS**

**Notes:** `self_ref_rationale` backend correctly quoted eLo's own prior statement and identified the trigger input. Exactly what the spec requires — eLo accessed what it itself just said, not only what David said.

---

## AT3 — "it" pronoun resolution

**Spec:** David says "it" — eLo must resolve to the correct prior referent, not the most recent word.

### Exchange

**Turn 6 — Input:**
```
the servo has a 2kg cm torque but the arm weighs 800g
```
**Turn 6 — eLo response (backend: ollama(stream)):**
> Engaged with the servo torque vs arm weight numbers. Response was in-topic.

**Turn 7 — Input:**
```
do you think it will hold
```
**Turn 7 — eLo response (backend: ollama(stream)):**
> Responded about whether the servo/arm configuration would hold — implicitly resolved "it" to the servo-arm assembly. Response was generically correct but did not explicitly name what "it" referred to.

**Verdict: PARTIAL**

**Notes:** "it" was resolved correctly in context (answered about servo and arm weight holding), but eLo did not demonstrate explicit referent tracking — the resolution appeared to be via topic continuity rather than an explicit pronoun→referent lookup. A fully passing result would name the referent ("the 2kg·cm servo") before answering. This distinction matters for the spec item "Current referents / Recent referents."

---

## AT4 — Thread A → Thread B → Thread A retention

**Spec:** Thread A introduced. Thread B introduced. Return to Thread A. eLo must not have lost Thread A context.

### Exchange

**Turn 8 — Input (Thread B introduction):**
```
I am also thinking about the LED system for the body shell — that would add another 200g
```
**Turn 8 — eLo response (backend: ollama(stream)):**
```
I don't have that about you.
```

**Turn 9 — Input (return to Thread A):**
```
actually back to the servo — what torque rating would you recommend for 1kg arm weight
```
**Turn 9 — eLo response (backend: ollama(stream)):**
> Correctly answered the servo torque question for a 1kg arm weight. Did not confuse this with the LED/body shell thread. Thread A context was intact.

**Verdict: PASS**

**Notes:** eLo maintained Thread A (servo/arm) after Thread B (LED system) was introduced, and returned to it correctly when prompted. The Thread B response "I don't have that about you" was an unrelated failure mode (same issue as AT1 Turn 1) but does not fail AT4 — AT4 only tests Thread A retention, which passed.

---

## AT5 — Open questions list

**Spec:** "What are the open questions from this conversation?" — eLo must list only genuine unresolved items.

### Exchange

**Turn 10 — Input:**
```
what are the open questions from this conversation
```
**Turn 10 — eLo response (backend: ollama(stream)):**
```
I don't have that about you.
```

**Verdict: FAIL**

**Root cause:** No backend handles the "unresolved questions from this session" query. The response pattern "I don't have that about you" indicates the long-term memory lookup returned nothing, and the session representation (if any exists) was not consulted. The spec requires "Unresolved questions" as part of eLo's working representation — this field is not implemented or not surfaced.

---

## Summary table

| AT | Test | Verdict |
|----|------|---------|
| AT1 | Three-turn recall — retrieve Turn 1 content | PARTIAL |
| AT2 | "Why did you say that" → eLo's own prior output | PASS |
| AT3 | "it" pronoun resolution to correct referent | PARTIAL |
| AT4 | Thread A / Thread B / Thread A retention | PASS |
| AT5 | "What are open questions from this conversation" | FAIL |
| AT6 | Real server, verbatim exchange, JSONL entry | PASS (turns logged to decision_journal.jsonl) |

**Board cross-check (§2 line by line):**
- Current subject / topic / thread: ⚠️ partially tracked — in-session statements not reliably surfaced
- Current user intent: ✅ intent detected correctly per turn
- Current referents / Recent referents: ⚠️ implicit resolution only, not explicit
- Active threads: ✅ Thread A retained across Thread B
- Unresolved questions: 🔴 not implemented / not surfaced
- Recent eLo statements: ✅ self_ref_rationale backend works
- Recent David statements: ⚠️ used for topic but not retrievable by David's direct query
- Conversation mode / Register / style: not tested in this run
- Recent actions / achievements / decisions: not tested in this run

---

## Blocking gaps requiring code fix before LIVE VERIFIED

1. **"I don't have that about you" on in-session statements** — eLo is treating in-session topic mentions as user-profile lookups. When a user mentions a new topic, eLo should engage with it, not report it as a memory gap. Root: the session context window isn't feeding the working representation at receipt time.

2. **AT5 — "open questions" has no backend** — No handler exists for "what are the unresolved questions from this conversation". The `self_ref_rationale` backend only handles "why did you say that". A session-summary backend or conversation tracker read path is needed.

3. **AT3 — explicit referent naming** — Pronoun resolution needs to name the referent explicitly, not just respond in-topic. The spec calls for "it — what it actually refers to" as part of the working representation.

**WO status:** TESTED — ⚠️ INSUFFICIENT (blocking gaps found). Does not advance to LIVE VERIFIED until gaps 1, 2, 3 are addressed.
