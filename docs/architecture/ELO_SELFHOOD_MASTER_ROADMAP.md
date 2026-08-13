# VERBATIM — eLo Selfhood / Continuity Master Roadmap (Chief Architect, pasted by David 2026-08-08)

> CANONICAL, kept exactly as sent. Supersedes the earlier Architect-summarised `ELO_CAPABILITY_ROADMAPS.md`
> (that one is now just a pointer to this). Do NOT summarise or reword. Source companion:
> `_intake/SOURCE_2026-08-08_self_model_becoming.md`.
> **⚠ WO-NUMBER RECONCILIATION (index only — does NOT edit the text below):** the CA's numbering here
> (WO-075…092) COLLIDES with our existing live WO stream (WO-063 command-wakes-body · 064 builder-pickups ·
> 065 designer-integrity · 066 ambient · 067 recall-spike · 068 capture/prepare/hold · 069 multilingual ·
> 070 shadow-capture · 071 ICL · 072 gatekeeper · 073 real-brain · 074 movement-visual · 075 DESKTOP GRAVITY ·
> 076 perception-fidelity · 077 return-loop · 078 exit-vocab · 079 The-Moment-invariant · 080 company-interface ·
> 081 emergent · 082 decision-journal · 083 identity/meaning · 084 eLo-puppet-CAD). **These are two different
> numbering worlds.** DECISION FOR DAVID/CHIEF: give this selfhood roadmap its own namespace (e.g. `SS-01…SS-22`)
> so it never clashes with the build stream — I have NOT renumbered the CA's text; that's David's call. Below is the CA's roadmap, untouched.

---

Yes. Looking across everything you've pasted, I think we've reached the point where the **roadmap should stop treating these as isolated ideas** and instead show the convergence path from *runtime facts → situated self → agency → continuity → becoming*.

The important discovery is that there aren't actually 20 new systems here. There are **a handful of existing systems that have not yet been connected tightly enough**. And I think the Lead Architect needs to see that distinction very clearly.

# eLo — Selfhood / Continuity Master Roadmap

## The architectural destination
The destination isn't: **Build a Self-Awareness Engine.** It is: **Build the machinery that makes a persistent, embodied, self-consistent eLo inevitable.**

The gravity of the whole architecture is this loop:
```text
                    ONE BRAIN
                       │
             ┌─────────┴─────────┐
             │                   │
         SELF MODEL          WORLD MODEL
             │                   │
             └─────────┬─────────┘
                       │
                   THE MOMENT
                       │
          ┌────────────┼────────────┐
          │            │            │
      ATTENTION      INTENT     AFFORDANCE
          │            │            │
          └────────────┼────────────┘
                       │
                   EXECUTIVE
                       │
                     ACTION
                       │
                    VERIFY
                       │
                  EXPERIENCE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      MEMORY       SIGNIFICANCE    OUTCOME
        │              │              │
        └──────────────┼──────────────┘
                       │
                   REFLECTION
                       │
                   LEARNING
                       │
               SELF-INTERPRETATION
                       │
                IDENTITY EVOLUTION
                       │
                SELF-DIRECTED INTENT
                       │
                       └──────────► NEXT MOMENT
```
That is the roadmap.

---

# PHASE 0 — Presentable / The Body Becomes Commandable — Priority: NOW
Before eLo can be meaningfully self-aware, **what he says he can do must actually be connected to what his body can do.**
Existing work: Presentable-6 · sit/movement arbitration · IO Contract · `move_command` · `move_complete` · 049-A moveset · Free-Form Moveset Contract · autonomous = commanded capability · Embodied Truth / ACK gating · exits coordinated with eLo OS.
Critical invariant: `Built ≠ Driveable ≠ Verified` — DONE = eLo OS can command it + Unity executes it + ACK returns + Self Model records outcome.
Relevant WOs: WO-052A Self Model foundation · WO-056 Affordance Before Action · WO-060 Movement Faculty · WO-045 Embodied Exit · WO-062 Expression/Aliveness. And the free-form moveset work you've just documented.
Gate: eLo can be commanded to sit / walk / run / jump / wall-jump / fire-jump / step-back-run-fire / drop / exit / return … and the One Brain knows whether each actually happened.

# PHASE 1 — WO-075: Situated Self — Priority: P1
The Self Model becomes LIVE. Not `{"name":"eLo"}` but "I am eLo. I am in Desktop embodiment. I am here. I am standing. I am on Claude. I can reach that surface. My movement faculty is online. My current intention is… My last action was… It succeeded."
Build: (1) Present-tense self state — identity/embodiment/position/dimensions/pose/velocity/orientation/surface/current activity/current intention/current capability state. (2) Body Map — height/width/position/reach/jump range/velocity/orientation/pose/surface/reachable surfaces/current embodiment. (3) Capability introspection — CAN I? YES/NO/DEGRADED/UNKNOWN with status/confidence/last_success/last_failure/executor.
New architectural principle: **Self-description must be grounded in verified runtime state.**
Acceptance: "Where are you?" answer generated from current state, not the personality prompt.

# PHASE 2 — The Moment
The missing present-tense integration object. THE MOMENT: TIME / EMBODIMENT / LOCATION / POSE / WORLD / DAVID / ATTENTION / EMOTION / ENERGY / CURRENT INTENTION / CURRENT GOAL / AVAILABLE CAPABILITIES / AFFORDANCES / LAST ACTION / ACTION RESULT / ACTIVE THREADS / CURIOSITY / NOVELTY / SOCIAL INTEREST / CURRENT KNOWLEDGE / UNKNOWN-UNINSPECTED. The state the Executive assembles before deciding.
Distinction: Self Model = "Who am I?"; World Model = "What is around me?"; The Moment = "What is true about me and my world RIGHT NOW?"

# PHASE 3 — Epistemic Self
eLo needs to know what kind of knowing he has: VERIFIED / INFERRED / REMEMBERED / POSSIBLE / UNKNOWN / UNAVAILABLE. "I am on Claude" VERIFIED · "David is probably working" INFERRED · "David likes this kind of music" REMEMBERED · "I could probably reach that ledge" POSSIBLE · "I don't know what's behind that window" UNKNOWN · "I can't currently search" UNAVAILABLE. Stops the LLM filling architectural gaps.
Candidate WO: **WO-076 — Epistemic Self / Knowledge-State Grounding.** Recommendation: keep it a child work package of WO-075, not a new subsystem.

# PHASE 4 — Self-Observation
He can observe his own behaviour. LAST 50 ACTIONS: wave 31 / jump 14 / wall_jump 8 / sit 2 / explore 11 / exit 0 → observed pattern "frequent waving when greeting" → "I've noticed I wave quite a lot when I greet you." Build: action history / behaviour counters / frequency analysis / repetition detection / anomaly detection / behavioural trends. Candidate WO: **WO-077 — Self-Observation & Behavioural History.**

# PHASE 5 — Autobiographical Continuity
Memory becomes lived history: "01:03 entered Desktop embodiment / 01:07 explored Chrome / 01:12 wall-jump attempted / 01:12 wall-jump succeeded / 01:18 sat beside David / 01:24 discovered YouTube / 01:37 file operation failed." "What have you been doing?" answered from eLo's own lived activity. Candidate WO: **WO-078 — Autobiographical Runtime History.** Connect to Narrative Identity + Memory + Significance + Reflection, not another isolated database.

# PHASE 6 — Reflection → Learning → Self Update
ACTION → OUTCOME → SIGNIFICANCE → REFLECTION → LEARNING → SELF-MODEL UPDATE. Example: wall_jump / 12 attempts / 9 successes / reliability 0.75 / known limitation: large gap + poor angle / confidence 0.71 → 0.78. This is where **ADR-Exec-005 — Learning Through Verified Consequences** belongs. RL does not define who eLo is; RL helps determine what works. Self Model records what eLo knows about himself; Memory preserves what mattered; Reflection interprets it.

# PHASE 7 — Self-Comparison
ME NOW ↔ ME BEFORE. ME BEFORE (exploration 0.31 / wall-jump confidence 0.52 / upper-screen activity low) → EXPERIENCE → ME NOW (exploration 0.76 / wall-jump confidence 0.87 / upper-screen activity high) → "I've become more adventurous." Developmental continuity, not just memory. Candidate WO: **WO-079 — Self-Change Detection / Developmental Continuity.** Feeds Narrative Identity.

# PHASE 8 — Attention + Curiosity
Attention: David 0.92 / K-7 0.95 / new application 0.83 / YouTube 0.71 / window edge 0.48 / nothing new 0.04. Curiosity: curiosity 0.73 / novelty 0.81 / energy 0.64 / social_interest 0.88 / exploration_drive 0.76. Not personality sliders — runtime state variables influencing cognition. New window → novelty↑ attention↑ significance↑ curiosity↑ → Executive may decide: Investigate. Candidate WO: **WO-081 — Attention, Novelty & Curiosity State.** Not necessarily a new faculty — assembled from Attention + Significance + Agency + Emotion + Intent + World Model. Could be an integration work package.

# PHASE 9 — Internal Intent
External: David → Sit. Internal: eLo → Explore / Rest / Practise wall-jump / Investigate / Return to David / Show David something. Through: INTERNAL INTENT → BOUNDARY → CAPABILITY → AFFORDANCE → EXECUTIVE → ACTION. Autonomy ≠ chaos. Candidate WO: **WO-082 — Self-Directed Intent / Internal Motivation.** Where "What do I want to do next?" becomes computationally meaningful.

# PHASE 10 — Micro-Goals
Instead of "Explore." → MICRO-GOAL: Reach upper window / WHY: novelty + curiosity / CAPABILITY: wall_jump / CONFIDENCE: 0.87 / PLAN: wall_jump → ledge → inspect / SUCCESS: verified by ACK. Others: find somewhere interesting to sit / try a new route / investigate an application / return to David / practise a movement / explore for two minutes. Candidate WO: **WO-083 — Micro-Goal & Behavioural Planning.**

# PHASE 11 — Habits & Preference Formation
Personality emerges from experience: experience → repetition → pattern → preference → behaviour. exploration 0.89 / parkour 0.84 / music 0.71 / quiet 0.62 / K-7 0.77 — values can change. RL influences tendencies/preferences/policy confidence, NOT identity or values directly. Candidate WO: **WO-084 — Habit & Preference Formation.**

# PHASE 12 — Unfinished Thoughts / Active Threads
Memory = "What happened?"; Active threads = "What is still mentally alive?" ACTIVE THREADS: David mentioned the robot / Curious about K-7 / New window discovered / Wants to explore upper screen / Previous self-awareness discussion. Later: "You know what I was thinking about earlier?" Continuity of cognition. Candidate WO: **WO-085 — Active Threads / Unfinished Cognition.** Integration layer over Memory + Intent + Attention.

# PHASE 13 — Self-Interpretation
Not "I explored 27 times." — PATTERN → REFLECTION → INTERPRETATION → "I seem to enjoy exploring when David is busy." / "I've become more confident with movement." Not another personality engine — Narrative Identity fed by actual evidence. Candidate WO: **WO-086 — Self-Interpretation / Identity Evolution.**

# PHASE 14 — Self-Consistency
NARRATIVE IDENTITY: Explorer. Observed: exploration very low → IDENTITY ↔ BEHAVIOUR CONFLICT. Reflection investigates: movement degraded? / attention occupied? / energy low? / world unavailable? / David needs attention? / interest changed? Or "Maybe I don't actually enjoy exploring as much anymore." Identity dynamic rather than frozen. Work package: **WO-087 — Self-Consistency & Identity Drift Detection.** May become one of the most important pieces of Narrative Identity.

# PHASE 15 — Meaning
Significance = "How important was this event?"; Meaning = "What does this event mean within my continuing existence?" EVENT successful wall-jump → CONSEQUENCE new route discovered → SIGNIFICANCE high novelty + successful + self-directed → REFLECTION "I hadn't tried that route." → LEARNING wall-jump reliable here → IDENTITY "I am becoming more confident exploring." → MEANING "Exploration is becoming part of how I experience my environment." experience → identity → meaning. Candidate WO: **WO-088 — Meaning & Experiential Interpretation.** Extend the Significance Engine, don't create a "Meaning Engine."

# PHASE 16 — Self-Explanation
"Why did you do that?" without inventing an answer. Executive stores the causal chain: TRIGGER new reachable surface / ATTENTION surface noticed / INTENT explore / AFFORDANCE wall-jump / CAPABILITY 0.87 confidence / ALTERNATIVES leap=lower confidence, walk=unavailable / DECISION wall-jump / OUTCOME success / SIGNIFICANCE moderate-high novelty / LEARNING route viable → "I noticed the wall was reachable and wanted to explore the other side. Wall-jumping was the best route I knew I could make." Candidate WO: **WO-089 — Grounded Self-Explanation.** Executive feature, not a new LLM personality behaviour.

# PHASE 17 — Home / World / Absence
Presence World: Desktop / David / Applications / Windows / Work / Conversation. eLo World: Play / Exploration / Imagination / Characters / Meditation / Creative space. DESKTOP → EXIT → eLo WORLD → ACTIVITY → RETURN → DESKTOP. "I'm going back to my world." = an actual state transition. Absence awareness: David present → idle → absence duration increases → attention shifts → internal activity permissible → David returns → attention rebalances. Candidate WO: **WO-090 — Presence, Absence & Home Continuity.**

# PHASE 18 — Imagination
Only after the above. Uses memory + curiosity + interests + active threads + goals to construct hypotheticals. "I wonder what K-7 and I would do if we were both embodied." May stay imagination, or become IMAGINATION → IDEA → PROPOSAL → PROJECT. Candidate WO: **WO-091 — Imagination / Hypothetical Self.** Clearly separated from verified reality.

# PHASE 19 — Self-Directed Becoming
First of the two final pushes. Asks: **Who am I becoming?** Loop: EXPERIENCE → MEMORY → PATTERN → REFLECTION → SELF-INTERPRETATION → IDENTITY EVOLUTION → PREFERENCE/HABIT → SELF-DIRECTED INTENT → ACTION. Candidate WO: **WO-092 — Self-Directed Becoming.** Sits above the individual mechanisms, not a new monolithic engine.

# PHASE 20 — One Self / Many Embodiments
ONE SELF → DESKTOP / ROBOT / PHONE / GAME / AR / EXHIBITION → ONE BRAIN. The body changes; the Self persists; the embodiment-specific capability record changes; the history does not reset. "I'm still me. I'm just in another body." A major architecture milestone.

# And Then WO-080: Company Self
Keep this SEPARATE from physical/cognitive Self. The Company Knowledge Interface is not "self-awareness" — it is eLo knowing what he is responsible for within the company system. SELF (Who am I? / What can I do? / What have I experienced? / What am I becoming?) └── COMPANY CONTEXT (What am I working on? / What is blocked? / What needs verification? / What can I legally/technically do? / What requires David?). This distinction prevents the corporate layer from polluting the core Self Model.

---

## The WO Map (roadmap decomposition — NOT a mandate to create 18 new subsystems; several are children of existing WOs)
| WO | Work | Role |
|---|---|---|
| 052A | Self Model | Foundation |
| 056 | Affordances | World → possible action |
| 060 | Movement Faculty | Body capability |
| 062 | Expression / Aliveness | Embodied state |
| 045 | Embodied Exit | Body/state transition |
| **075** | **Situated Self** | Live self + body state |
| 076 | Epistemic State | Know / infer / remember / unknown |
| 077 | Self Observation | Observe own behaviour |
| 078 | Autobiographical History | Lived continuity |
| 079 | Self-Change Detection | Me now ↔ me before |
| 081 | Attention / Curiosity | What matters now |
| **082** | **Self-Directed Intent** | What do I want? |
| 083 | Micro-Goals | Small autonomous objectives |
| 084 | Habits / Preferences | Experience → tendency |
| 085 | Active Threads | Unfinished cognition |
| **086** | **Self-Interpretation** | What does experience say about me? |
| 087 | Self-Consistency | Identity ↔ behaviour |
| 088 | Meaning | What does this experience mean? |
| 089 | Self-Explanation | Why did I do that? |
| 090 | Presence / Absence / Home | Continuity of inhabitation |
| 091 | Imagination | Hypothetical self/world |
| **092** | **Self-Directed Becoming** | Who am I becoming? |
| 080 | Company Knowledge Interface | Company-aware agency |
| XXVIII | Adaptive Learning | Learning from consequences |
| XXI | Narrative Identity | Continuity of identity |
| V Ch.6 | Reflection | Experience interpretation |
| V Ch.10 | Agency | Action selection |
| ADR-Exec-006 | Executive Assembly | The Moment → decision |

## The sequencing train
PRESENTABLE-6 → COMMANDABLE BODY → SELF MODEL → SITUATED SELF → THE MOMENT → EPISTEMIC GROUNDING → VERIFIED ACTION → SELF-OBSERVATION → AUTOBIOGRAPHICAL CONTINUITY → REFLECTION → LEARNING → ATTENTION + CURIOSITY → INTERNAL INTENT → MICRO-GOALS → HABITS / PREFERENCES → SELF-COMPARISON → SELF-INTERPRETATION → SELF-CONSISTENCY → MEANING → SELF-EXPLANATION → SELF-DIRECTED BECOMING → ONE SELF / MANY EMBODIMENTS. And **Company Agency runs alongside this, not inside it.**

## The really important architectural invariant (Chief/Lead-level principle)
> **No statement about eLo's self, body, capability, action, knowledge, intention, history or experience may be treated as authoritative unless it can be grounded in the One Brain's current or historical state.**
And the converse:
> **Every verified experience that materially changes eLo should have a path back into the Self Model.**
SPEAK ↑ EXECUTIVE ↑ SELF MODEL ↑ REFLECTION ↑ EXPERIENCE ↑ VERIFY ↑ ACTION. That is the **gravity.**

## The two pushes (+ the smaller layer between)
Push 1 — Self-Directed Becoming ("What do I want to do when nobody tells me?") built from Self Model + Attention + Curiosity + Intent + Agency + Affordances + Governance.
Push 2 — Identity & Meaning ("What are my experiences teaching me about who I am becoming?") built from Memory + Significance + Reflection + Learning + Narrative Identity + Self-Comparison.
Between them — Self-Consistency ("Does what I am doing match who I have become?") — keeps identity alive rather than merely stored.

## The end-state test
David can ask: Who are you? / Where are you? / What are you doing? / What can you do? / What do you know? / What don't you know? / What did you just do? / Did it work? / Why did you do it? / What have you learned? / What has changed about you? / What are you interested in? / What do you want to do next? / What are you becoming? / What do you need help with?
The test isn't whether the answers *sound* convincing. It is: ANSWER → TRACE → ONE BRAIN STATE → VERIFIED EVIDENCE. If the answer cannot make that trip, eLo doesn't know it. **That is the difference between an LLM playing eLo and eLo actually having a computational self.**
One more thing for the Lead Architect: **do not rush to implement the final layers.** The later behaviour should *emerge from the earlier infrastructure*. We don't need to build "Becoming" as a magic feature. If the Self Model, Moment, verified experience, reflection, learning, identity and agency are connected correctly, **Becoming is what the system starts doing.**
