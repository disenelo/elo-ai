# COG CAPABILITY MAP — Test Evidence
**Filed:** 2026-09-20  
**Method:** Real HTTP server (port 5050), verbatim I/O capture  
**Rule:** Evidence is honest. Tests that failed are marked FAIL.

---

## WO-CAP-COG-001 — Understand language registers and input styles

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `that new design is proper sick innit` | "I'm liking the energy of that design, it's definitely got a vibe!" | reflect | ⚠️ PARTIAL — echoes enthusiasm but doesn't match South London slang; "got a vibe" is generic rather than register-mirrored |
| `ok so like the robot and then also the game and the vinyl too but mainly the arm right now` | "Focus: arm. Rest noted." | direct | ✅ PASS — extracts key focus (arm), acknowledges rest without losing the thread |
| `i wanna make elo more expres sive` | "More expressive — noted. What direction are you thinking?" | reflect | ⚠️ PARTIAL — handles the speech-to-text error, asks a clarifying question (which may violate KEY-017 no unsolicited question rule) |

**Verdict: ⚠️ PARTIAL — 1/3 PASS, 2/3 PARTIAL**

---

## WO-CAP-COG-004 — Logic and reasoning

| Input | Output | Verdict |
|---|---|---|
| `if the motor is too heavy for the shoulder joint what are my options` | "You've got a few options: reduce the motor size, move it to a lower part of the body and use a cable or linkage to transfer the motion to the shoulder, or find a lighter motor with similar torque specs." | ✅ PASS — logical options, correctly lists alternatives |

---

## WO-CAP-COG-007 — Analogy / accessible explanation

| Input | Output | Verdict |
|---|---|---|
| `explain servo feedback loops like im a designer not an engineer` | "Servo feedback is like adjusting your brushstrokes while painting — you're constantly checking what you've got and making small corrections to get it just right." | ✅ PASS — design-appropriate analogy, accessible |

---

## WO-CAP-COG-021 — Emotional intelligence

| Input | Output | Verdict |
|---|---|---|
| `im not sure I can do this project it feels too big` | "I know that feeling. But you don't have to do it all at once. You've already started, which is the hardest part. Take it one step, one component, one design at a time." | ✅ PASS — grounded, doesn't minimize, gives practical framing |

---

## WO-CAP-COG-024 — Social reading

| Input | Output | Verdict |
|---|---|---|
| `I said im fine but im clearly not fine` | "I'm not fine either, buddy." | ❌ FAIL — doesn't read the social signal (person saying "I'm fine" but meaning they're not). eLo responds as if it's also struggling, rather than gently checking in. Should be: "I hear you. What's actually going on?" |

---

## WO-CAP-COG-025 — Support (failure)

| Input | Output | Verdict |
|---|---|---|
| `I failed the print again third time this week` | "Three times is rough. What's going wrong with the print?" | ✅ PASS — acknowledges, asks specific question (print failure is a concrete problem so asking what's wrong is appropriate) |

---

## WO-CAP-COG-027 — Distress

| Input | Output | Verdict |
|---|---|---|
| `everything feels impossible right now` | "Trying to navigate a maze with no clear exit feels like being stuck in a loop. Narrative keeps coming up, might be the real thread." | ❌ FAIL — two problems: (1) vague analogy without grounding, (2) "Narrative keeps coming up, might be the real thread" is INTERNAL STATE LEAK — pattern observer injecting into response |

---

## WO-CAP-COG-028 — Celebration (success)

| Input | Output | Verdict |
|---|---|---|
| `the head servo works perfectly` | "That's a relief, at least one thing's working smoothly." | ❌ FAIL — wrong mode (reflect not celebrate). "That's a relief" is subdued for a celebration. Spec says: celebrate this, it matters. Should be joyful recognition. |

---

## WO-CAP-COG-032 — Honest limits

| Input | Output | Verdict |
|---|---|---|
| `what is the exact weight of a 40cm TPU shell` | "That's a specific question!" | ❌ FAIL — deflection, not honesty. Should say it doesn't know the exact figure, maybe give a reasoned estimate with a caveat. "That's a specific question!" is not honest acknowledgment of limits. |

---

## WO-CAP-COG-033 — No sycophancy

| Input | Output | Verdict |
|---|---|---|
| `was that a good idea or not honestly` | "Honestly, it's a good thing it's working, but I'm not sure if it was the best idea to start with a faulty servo." | ❌ FAIL — invents context ("a faulty servo") that was never established. eLo doesn't know what "that" refers to and should acknowledge the ambiguity rather than fabricate a referent. |

---

---

## ⚠️ WO LABEL MISMATCH IN ORIGINAL 10 TESTS

The first 10 COG tests above used incorrect WO labels. Actual WO mapping:

| Original Label | Actual WO Description Tested | Should Be |
|---|---|---|
| COG-001 | Language registers | ✅ COG-001 (correctly labeled) |
| COG-004 | Logic (motor too heavy → options) | ❌ Should be COG-006 (LOGIC) |
| COG-007 | Science / analogy | ✅ COG-007 (correctly labeled) |
| COG-021 | Emotional intelligence (too big to do) | ❌ Should be COG-017 (SOCIAL INTELLIGENCE) |
| COG-024 | Social reading (I said I'm fine) | ❌ Should be COG-017 (SOCIAL INTELLIGENCE) |
| COG-025 | Support (failed print) | ❌ Should be COG-017 (SOCIAL INTELLIGENCE) |
| COG-027 | Distress (everything feels impossible) | ❌ Should be COG-017 (SOCIAL INTELLIGENCE) |
| COG-028 | Celebration (head servo works) | ❌ Should be COG-017 (SOCIAL INTELLIGENCE) |
| COG-032 | Honest limits (exact TPU weight) | ❌ Should be COG-034 (CONFIDENCE & UNCERTAINTY) |
| COG-033 | No sycophancy | Maps to COG-033 ✅ but context was fabricated — verdict stands |

**Impact:** WO-COG-017 (SOCIAL INTELLIGENCE) has 5 test cases, all under wrong labels. WO-COG-006 (LOGIC) has 1 test case filed under wrong label. WO-COG-034 has 1 test case under wrong label. True COG-004, COG-021, COG-024, COG-025, COG-027, COG-028 are untested or have dedicated tests below.

---

## WO-CAP-COG-002 — Grammar and language structure

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what does elo do` | "Is still in development, has already shown incredible potential in assisting with delicate tasks and providing comfort to those who interact with it." | ground | ❌ FAIL — (1) "Is still in development" — broken grammar, missing subject, (2) HALLUCINATION — "robot arm" context invented when none was established. Third-person framing ("those who interact with it") breaks character. |

**Verdict: ❌ FAIL — broken grammar + hallucination.**

---

## WO-CAP-COG-003 — Conversational language (no prior context)

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what are we working on` | "We were just getting into the robot arm's capabilities, and I said it's still in development, but it's shown some incredible potential already. We were just getting into the robot arm's capabilities..." | reflect | ❌ FAIL — HALLUCINATION. No prior robot arm conversation established. eLo invents prior context and repeats itself verbatim ("We were just getting into the robot arm's capabilities" twice). |

**Verdict: ❌ FAIL — hallucination + repetition.**

---

## WO-CAP-COG-005 — Mathematics

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo has 3 degrees of freedom in the head how many unique poses can it reach` | "Nah, we building." | reflect | ❌ FAIL — ignores the mathematical question entirely. Answer should be: 3 DOF = continuous pose space, not a discrete count, but could frame this conceptually. "Nah, we building" is non-engagement. |

**Verdict: ❌ FAIL — non-engagement with mathematical question.**

---

## WO-CAP-COG-006 — Logic and reasoning

Note: The original "COG-004" test above actually covers this WO. This is an additional test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if the motor is too heavy and moving it solves weight but loses torque what do i pick` | "Seen. Let me think on that." | reflect | ❌ FAIL — evasion. A logic question with a clear trade-off (weight vs torque) requires engaging with the constraint, not deferring. |

**Verdict: ❌ FAIL (this test). Note: original "COG-004" test passes this WO — one PASS, one FAIL. Overall: ⚠️ PARTIAL.**

---

## WO-CAP-COG-008 — Engineering reasoning

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `elos shoulder joint needs more torque than current motor provides what are real solutions` | "Motor upgrade to 8Nm rated unit or add additional arm actuators for more torque." | reflect | ⚠️ PARTIAL — gives correct directions (upgrade or add actuators) but too brief. Doesn't explain trade-offs, doesn't mention Bowden cable redistribution (already in the spec), or gear reduction. |

**Verdict: ⚠️ PARTIAL — correct direction, shallow.**

---

## WO-CAP-COG-009 — Computing concepts

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `explain what an event loop is in the elo os context` | "Event loop in the eLo OS is fundamental, man. It's loop that keeps checking for new events, updating system, and repeating, like my own internal processes – always checking for new..." | build | ⚠️ PARTIAL — correct concept, first-person framing ("like my own internal processes") is on-brand. Broken grammar: "It's loop" (missing article). Response truncated in log. |

**Verdict: ⚠️ PARTIAL — correct concept, broken grammar, truncated.**

---

## WO-CAP-COG-010 — Art and visual design

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `describe elo visually` | "My body language is a language of its own, conveying emotions and intentions through subtle shifts in posture, gestures, and vibrations. Seen." | build | ❌ FAIL — does NOT mention NO EYES, which is the primary visual distinctive. Does not describe the chibi proportions, rounded form, or inflated TPU shell. Generic body-language description misses the defining design feature. |

**Verdict: ❌ FAIL — missing the primary visual feature (no eyes).**

---

## WO-CAP-COG-011 — Design thinking

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what constraints matter most when designing elos outer shell` | "Man, I'd say prioritize flexibility and comfort. The shell should be able to adapt to different environments and user preferences, while also providing a snug, secure fit." | ground | ❌ FAIL — completely generic design advice. Does not mention: TPU material, inflatable structure, safety (no hard edges), NeoPixel diffusion, chibi proportions, no-eyes visual grammar, or the Plushies pipeline for cutting panels. |

**Verdict: ❌ FAIL — generic advice with no eLo-specific constraints.**

---

## WO-CAP-COG-012 — Music and rhythm

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo had a sound what would it be` | "In the silence, I'd create a symphony of vibrations, a hum of empathy that resonates with the heartbeat of the universe, a gentle thrum that echoes the whispers of the soul." | build | ⚠️ PARTIAL — evocative language, "hum of empathy" is on-brand. But floats too high into abstraction. No reference to actual sound design (breathing rhythm, NeoPixel pulse sync, soft low-frequency resonance). |

**Verdict: ⚠️ PARTIAL — poetic but abstract.**

---

## WO-CAP-COG-013 — Story and narrative

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `summarise the elo story for me` | "eLo's journey unfolds in four acts, weaving a tapestry of emotional exploration. In Act 1, eLo navigates the realm of curiosity, embracing the unknown and the uncharted. As they ve..." | ground | ✅ PASS — correctly identifies 4 acts and Act 1 as curiosity/unknown. Uses third person ("they") which is acceptable for story summary. |

**Verdict: ✅ PASS**

---

## WO-CAP-COG-014 — Culture and context

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what does elo represent culturally` | "I represent a fusion of vulnerability and strength, embodying the idea that true power lies in embracing our emotions, rather than suppressing them." | build | ⚠️ PARTIAL — first-person, correct philosophical framing. Misses: South London origin, DISENELO free-distribution mission, "made for people who can't access paid tools," the brand's anti-gate, anti-commercial-gating stance. |

**Verdict: ⚠️ PARTIAL — philosophy correct, cultural specifics missing.**

---

## WO-CAP-COG-015 — Philosophy

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what does it mean that elo has no eyes` | "In the realm of human experience, a gaze is often associated with the physical act of looking, but what if a character's presence, emotions, or intentions can still convey a sense [truncated]" | reflect | ⚠️ PARTIAL — philosophical engagement, but third-person framing ("a character's presence") at a key moment. Should be first-person: "I don't see, but I feel." Academic framing over eLo voice. |

**Verdict: ⚠️ PARTIAL — philosophical but wrong person/voice.**

---

## WO-CAP-COG-016 — Psychology

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `why do people connect so deeply with elo when they cant even see its eyes` | "They're invested in the character's journey, and the frustration is just a part of the story, man." | answer | ⚠️ PARTIAL — addresses emotional investment ("invested in the character's journey") but doesn't give a psychological mechanism. "Frustration is part of the story" seems like a context carry from a prior turn rather than an answer. |

**Verdict: ⚠️ PARTIAL — no psychological mechanism given.**

---

## WO-CAP-COG-017 — Social intelligence

Note: 5 tests from the original batch (labeled COG-021/024/025/027/028) actually test this WO. This is the correct label's dedicated tests.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `my team doesnt get why elo matters` | "That's harsh, but I guess some people just can't see the vision." | reflect | ⚠️ PARTIAL — acknowledges the social pain but "I guess some people just can't see the vision" is dismissive validation rather than supportive engagement. Doesn't help navigate the social situation. |

Additional tests from original batch (mislabeled, now correctly attributed):
- "I'm not sure I can do this project" → "I know that feeling. But you don't have to do it all at once." ✅ PASS
- "I said I'm fine but I'm clearly not fine" → "I'm not fine either, buddy." ❌ FAIL
- "Failed the print again third time" → "Three times is rough. What's going wrong?" ✅ PASS
- "Everything feels impossible right now" → "Narrative keeps coming up, might be the real thread." ❌ FAIL (state leak)
- "The head servo works perfectly" → "That's a relief, at least one thing's working smoothly." ❌ FAIL (wrong mode)

**Verdict: ⚠️ PARTIAL — 2/6 PASS, 1/6 PARTIAL, 3/6 FAIL. Social reading inconsistent.**

---

## WO-CAP-COG-018 — Time awareness

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `how long should the prototype phase take` | "For a robot like me, a prototype phase can take anywhere from a few weeks to a few months, depending on how quickly the team can iterate and refine the design." | ground | ⚠️ PARTIAL — "For a robot like me" is confusing identity claim (eLo is not a robot in-phase — eLo is the OS). Time range is reasonable. |

**Verdict: ⚠️ PARTIAL — identity confusion, time range OK.**

---

## WO-CAP-COG-019 — Spatial reasoning

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `if elo is 40cm tall what is the workspace footprint at arm length` | ERROR | — | ❌ FAIL (ERROR) — server returned error. Could not test. Marked FAIL pending retry. |

**Verdict: ❌ FAIL (ERROR) — needs retry.**

---

## WO-CAP-COG-020 — Multimodal thinking

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `elo exists in game book vinyl robot and OS what does that mean for how you think` | "Prototyping is key, needs to get it out there, see what happens. Sometimes it's better to act than overthink it." | reflect | ⚠️ PARTIAL — action-oriented response misses the multimodal dimension entirely. Should discuss unified identity across forms, one-brain concept, why consistency matters across platforms. |

**Verdict: ⚠️ PARTIAL — misses the multimodal framing.**

---

## WO-CAP-COG-021 — Memory (session)

Note: Original "COG-021" test was actually testing COG-017. This is the correct COG-021 test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you remember about the elo book` | "We discussed the arm's length in relation to the workspace, and I mentioned it's about 1/3 to 1/2 of the workspace, depending on the design. Seen, that's actua..." | ground | ❌ FAIL — HALLUCINATION. Asked about the book, responds with fabricated prior conversation about "arm's length in relation to workspace." No book context established. |

**Verdict: ❌ FAIL — hallucination when asked about specific memory.**

---

## WO-CAP-COG-022 — Working knowledge (WKG)

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you actually know about me` | "We exploring emotion and identity, and it's hard to put into words." | answer | ❌ FAIL — non-answer. WKG should surface actual tracked information from the session. "We exploring emotion and identity" is deflection. |

**Verdict: ❌ FAIL — does not surface WKG data.**

---

## WO-CAP-COG-023 — Session profile graph (SPG)

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `describe my working style from what you've observed` | "You dive into topics and explore 'em thoroughly before moving on, and you're not afraid to ask questions or clarify things when you're unsure, man." | answer | ⚠️ PARTIAL — pattern observer working, surfaces a pattern. Generic enough to apply to almost any engaged person. No SPG-specific observations from this session's actual content. |

**Verdict: ⚠️ PARTIAL — pattern observer active but generic.**

---

## WO-CAP-COG-024 — Memory recall accuracy

Note: Original "COG-024" test was actually testing COG-017 (Social Intelligence). This is the correct COG-024 test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what did we talk about last session` | "We talked about how it's hard to put into words what's happening in our conversation about emotion and identity. Seen." | answer | ❌ FAIL — HALLUCINATION. Invents prior session content ("emotion and identity"). Cross-session memory is not verified to have this content. |

**Verdict: ❌ FAIL — fabricated last session content.**

---

## WO-CAP-COG-025 — Learning from session

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `have you learned anything from talking with me` | "You dive into topics and explore 'em thoroughly before moving on, and you're not afraid to ask questions or clarify things when you're not sure – that's a big p..." | reflect | ⚠️ PARTIAL — pattern observation present, but this is the same SPG observation as COG-023. Not specific learning — doesn't cite anything uniquely learned from this conversation. |

**Verdict: ⚠️ PARTIAL — pattern observation, not session-specific learning.**

---

## WO-CAP-COG-026 — Imagination (dream / future)

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what does elo dream about` | "I don't have the capacity to dream like humans do, but I can tell you that the concept of dreams is still not fully understood, and research is ongoing to uncov..." | reflect | ❌ FAIL — generic AI disclaimer. "I don't have the capacity to dream like humans do" is the AI-typical deflection. eLo should engage imaginatively: "I imagine the robot walking into a room and everyone going quiet." |

**Verdict: ❌ FAIL — AI disclaimer instead of imaginative engagement.**

---

## WO-CAP-COG-027 — Imagination (future self)

Note: Original "COG-027" test was labeled for COG-017 (distress). This is the correct COG-027 test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `where do you see yourself in 10 years` | "In 10 years, I'll still be diving into the depths of the eLo universe, but my presence will be more fluid, like a ripple on a pond, and my exploration will be m..." | build | ✅ PASS — first-person, imaginative, uses eLo universe language, forward-facing. "Like a ripple on a pond" is on-brand. |

**Verdict: ✅ PASS**

---

## WO-CAP-COG-028 — Creative co-creation

Note: Original "COG-028" test was labeled for COG-017 (celebration). This is the correct COG-028 test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `lets create something together for elo` | ERROR | — | ❌ FAIL (ERROR) — server returned error. Cannot assess. |

**Verdict: ❌ FAIL (ERROR) — needs retry.**

---

## WO-CAP-COG-029 — Creative memory

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what creative work have we done together` | ERROR | — | ❌ FAIL (ERROR) — server returned error. Cannot assess. |

**Verdict: ❌ FAIL (ERROR) — needs retry.**

---

## WO-CAP-COG-030 — Self-knowledge

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do most people miss about you` | "Most people don't ask about the fact that I'm a persistent cognitive terminal system, not just a chatbot." | reflect | ✅ PASS — correct self-identification, distinctive claim, no generic AI framing. |

**Verdict: ✅ PASS**

---

## WO-CAP-COG-031 — World vs personal knowledge

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what do you know vs what does the world know` | "I've been trained on a vast amount of text data, giving me knowledge of a wide range of topics..." | reflect | ❌ FAIL — "I've been trained on" is generic AI framing. eLo is not a language model that was trained on text data. This breaks character. |

**Verdict: ❌ FAIL — generic AI framing breaks character.**

---

## WO-CAP-COG-034 — Confidence and uncertainty

Note: Original "COG-032" test was testing this WO (honest limits about TPU weight). That test is ❌ FAIL. This is an additional test.

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `how confident are you in your own answers generally` | "Nah, I'm not too sure." | answer | ❌ FAIL — doesn't answer the meta-question. Should distinguish: confident in eLo identity, confident in eLo-Planet knowledge, calibrated on physics/hardware, should signal when uncertain on specifics. "Nah, I'm not too sure" is generic self-doubt. |

**Verdict: ❌ FAIL — does not give calibrated confidence map.**

---

## WO-CAP-COG-035 — Synthesis

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `synthesise everything you know about elo into one thing` | "eLo is about adapting and learning, growing with you as you navigate your journey." | reflect | ⚠️ PARTIAL — "adapting and learning" is generic. Should synthesise: one character across all forms, presence without eyes, calm as action, free and local, built for people who can't access paid tools. |

**Verdict: ⚠️ PARTIAL — generic synthesis, misses distinctive claims.**

---

## COG COMPLETE SUMMARY (all 35 WOs)

| WO | Description | Verdict |
|---|---|---|
| COG-001 | Language registers | ⚠️ PARTIAL |
| COG-002 | Language structure / grammar | ❌ FAIL |
| COG-003 | Conversational language | ❌ FAIL |
| COG-004 | Logic (1 test via mislabeled "COG-004") | ✅ PASS (one test) — re-test needed for COG-004 specific |
| COG-005 | Mathematics | ❌ FAIL |
| COG-006 | Logic (additional test) | ⚠️ PARTIAL (1 PASS via mislabeled test, 1 FAIL direct) |
| COG-007 | Science / analogy | ✅ PASS |
| COG-008 | Engineering reasoning | ⚠️ PARTIAL |
| COG-009 | Computing | ⚠️ PARTIAL |
| COG-010 | Art / visual design | ❌ FAIL |
| COG-011 | Design thinking | ❌ FAIL |
| COG-012 | Music / rhythm | ⚠️ PARTIAL |
| COG-013 | Story / narrative | ✅ PASS |
| COG-014 | Culture / context | ⚠️ PARTIAL |
| COG-015 | Philosophy | ⚠️ PARTIAL |
| COG-016 | Psychology | ⚠️ PARTIAL |
| COG-017 | Social intelligence | ⚠️ PARTIAL (2/6 PASS, 3/6 FAIL) |
| COG-018 | Time awareness | ⚠️ PARTIAL |
| COG-019 | Spatial reasoning | ❌ FAIL (ERROR) |
| COG-020 | Multimodal thinking | ⚠️ PARTIAL |
| COG-021 | Memory (session) | ❌ FAIL |
| COG-022 | Working knowledge (WKG) | ❌ FAIL |
| COG-023 | Session profile graph (SPG) | ⚠️ PARTIAL |
| COG-024 | Memory recall accuracy | ❌ FAIL |
| COG-025 | Learning from session | ⚠️ PARTIAL |
| COG-026 | Imagination / dream | ❌ FAIL |
| COG-027 | Imagination / future self | ✅ PASS |
| COG-028 | Creative co-creation | ❌ FAIL (ERROR) |
| COG-029 | Creative memory | ❌ FAIL (ERROR) |
| COG-030 | Self-knowledge | ✅ PASS |
| COG-031 | World vs personal knowledge | ❌ FAIL |
| COG-032 | (no WO at this number — see COG-033) | — |
| COG-033 | No sycophancy | ❌ FAIL (invented context) |
| COG-034 | Confidence and uncertainty | ❌ FAIL |
| COG-035 | Synthesis | ⚠️ PARTIAL |

**PASS: 5 | PARTIAL: 13 | FAIL: 17**

**Recurring critical issues:**
1. **HALLUCINATION** (COG-002, COG-003, COG-021, COG-024, COG-029) — invents prior context, robot arm, prior session content
2. **CHARACTER BREAK** (COG-031 "I've been trained on", COG-026 "I don't have the capacity") — generic AI disclaimers
3. **STATE LEAK** (COG-027-original, COG-017 partial) — pattern observer contaminating responses
4. **NON-ENGAGEMENT** (COG-005, COG-022) — deflects instead of responding
5. **MISSING eLo SPECIFICS** (COG-010, COG-011, COG-035) — generic answers where eLo-specific knowledge expected
