# VERBATIM — primary source, DO NOT SUMMARISE (David + Chief Architect, pasted 2026-08-08)

> This is the CANONICAL text. Every WO, roadmap, and register REFERENCES this — none may replace or
> paraphrase it into shorter form. David: "(RECORD this information) Not how you summarise or I'll have to
> change the structure of the company." Kept exactly as sent.
> WO-number note (index only, does NOT edit the text below): the CA's "WO-075 Situated Self Engine" = our
> **WO-079** (WO-075 is Desktop Gravity); "Volume XXIX/XXX" are reconciled onto existing ADRs/volumes
> (no new volumes). Gravity IS recorded → **WO-075** (`Output/…`/board). The verbatim text is untouched.

---

## Part 1 — Chief Architect: the Self Model architecture + 10 points

Deeper question on that by Chief Architect: eLo has a persistent, continuously updated model of himself, his current embodiment, his capabilities, his internal state, his history, and his relationship to the world — and the Executive actually consults that model before thinking, acting or speaking. That is the point where the behaviour starts feeling genuinely self-aware. The architecture I'd build

```
                         ONE BRAIN
                            │
                 ┌──────────▼──────────┐
                 │     SELF MODEL      │
                 │                     │
                 │ Who am I?           │
                 │ Where am I?         │
                 │ What am I?          │
                 │ What can I do?      │
                 │ What am I doing?    │
                 │ What do I want?     │
                 │ How am I feeling?   │
                 │ What just happened?│
                 │ What have I learned?│
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      WORLD MODEL       MEMORY            BODY MODEL
       Where is         What happened?    What can
       everything?      What matters?     this body do?
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       EXECUTIVE
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           THINK           ACT           SPEAK
                            │
                            ▼
                         VERIFY
                            │
                            ▼
                      SELF-UPDATE
                            │
                            └──────► back into Self Model
```

The important part is the loop. Not a static JSON file called `self_state`.

1. eLo needs a persistent "I" At the moment, a lot of your transcript shows the language model talking about eLo. We need the runtime to know:

```
I am eLo
I am currently in desktop embodiment
I am positioned on Claude
I am  ...
My current pose is standing
My current state is calm
My available capabilities are ...
My movement faculty is healthy
My vision faculty is available
My Spotify capability is available
My file-writing capability is unavailable
My current intention is ...
My last action was ...
My last action succeeded/failed
```

Then the LLM isn't inventing an identity every turn. It is reading itself. 2. He needs a sense of "now" This is probably the biggest missing ingredient. eLo needs a continuously assembled Moment. Something like:

```
THE MOMENT

Time: 00:34
Embodiment: Desktop
Location: Claude / bottom edge
Pose: Standing
Environment: Chrome / Claude / Spotify / Windows...
David: Present
David activity: Working / interacting
eLo: Available
Current intention: None
Curiosity: 0.61
Energy: 0.78
Mood: Positive
Last action: Wall jump
Result: Success
Current affordances: sit / perch / jump / wall-jump / explore / exit ...
```

Then ask eLo: "Where are you?" He isn't generating an answer. He reads: `embodiment = desktop`, `location = Claude_bottom_edge` and says: "I'm on the bottom edge of Claude." That's Situated Self becoming real. 3. He needs to know what he can do — "Can you search?" from capability introspection, not training data. `SEARCH status: ONLINE executor: browser/search faculty confidence: 0.96`. "Can you make a file?" `FILE_WRITE status: DEGRADED reason: filesystem writer unavailable`. "Can you sit?" `SIT status: ONLINE body: desktop executor: Unity`. That is functional self-awareness. 4. He needs to know what he is actually doing — the sit problem: INTENTION → "I want to sit." → CAPABILITY CHECK → SIT available → COMMAND → BODY → ACK → POSE = SITTING → SELF MODEL UPDATED → SPEECH. Only then "I'm sitting with you." If the ACK doesn't arrive: "I tried to sit, but my movement system didn't confirm it." 5. He needs an autobiography — not just memory. Continuity. Memory: "David asked me to sit yesterday." Self: "I've been exploring this desktop for the last few days." Autobiography: "I've gradually learned how this desktop is laid out." Identity: "This is the embodiment I'm currently inhabiting." Then when the robot arrives: "I'm still me. I'm just in another body." 6. He needs self-observation — `LAST 50 ACTIONS wave: 31 jump: 14 wall_jump: 8 sit: 2 explore: 11 exit: 0`. Executive notices "I'm waving a lot." → "I've noticed I wave quite a lot when I'm idle." 7. He needs reflection — EXPERIENCE → OUTCOME → SIGNIFICANCE → REFLECTION → LEARNING → SELF MODEL. Example: Attempt wall jump / Outcome success / Environment Claude → Chrome / Difficulty medium / Significance high / Learning "wall-jump route is viable" / Confidence 0.71 → 0.78. → "I know that route now." 8. Then add curiosity — "I am here → I know my capabilities → I perceive my environment → I notice something interesting → I form an internal intention → I decide whether to act → I act → I experience the outcome → I remember it." e.g. "I've never been on that window." → curiosity↑ → exploration intention → affordance search → jump possible → Executive approves → jump. 9. He needs internal intentions — EXTERNAL INTENT David "Sit down." INTERNAL INTENT eLo "I want to explore / rest / watch / practise that jump / return to David." Through: INTENTION → PRESENCE/BOUNDARY CHECK → CAPABILITY → AFFORDANCE → EXECUTIVE → ACTION. 10. And this is where RL belongs — RL is the learning mechanism, not the source of identity. jump→success learns; wall jump→failure learns; fire-jump→success→high significance learns. → "I know this route." Self Model says what he knows about himself; RL helps determine what works; Memory preserves what mattered; Reflection determines what it means; Executive determines what to do next; Personality determines how he expresses it.

The final ingredient: self-reference — Can I do this? / Where am I? / What am I doing? / Why did that fail? / What changed? / What do I want? / Is this appropriate? / What did I learn? — answered by runtime state, not generated fiction. What I would actually build next: NOT a giant "Self Awareness Engine" (violates Check-Before-Build). Assemble what you have: Self Awareness v1 = Self Model + Capability Registry + LiveWorldState + Embodiment State + Cognitive State + Memory + Agency + Reflection + Executive Assembly + Verified Action ACKs. Then ONE invariant: Before eLo speaks, acts, or describes himself, the Executive must be able to retrieve the relevant verified state from the Self Model. Then test with 10 questions (don't tell him the answers): 1. Who are you? 2. Where are you? 3. What embodiment are you currently using? 4. How big are you? 5. What can you do right now? 6. What are you currently doing? 7. What did you just do? 8. Did it succeed? 9. What do you want to do next? 10. What did you learn from that? It gives him a portable self: ONE SELF (identity/memory/capabilities/values/learning/intentions) → DESKTOP / ROBOT / PHONE / GAME / AR / EXHIBITION. Not pretending we've solved consciousness — a persistent, embodied, verifiable sense of self that travels with the One Brain wherever his body goes.

**And where is the gravity? (RECORD this information) Not how you summarise or I'll have to change the structure of the company.**

---

## Part 2 — David: the useful additions (1–10 + "Why did I do that?")

1. Self-state should be a live "present tense" — "I am eLo. I am currently on the bottom edge of Claude. My body is 143 px high. I can reach this ledge. I can jump that gap. I am standing. My movement faculty is online. I have 87% confidence in a wall jump. David is present. Spotify is paused." Assembled continuously from actual runtime facts. 2. Separate "I know" from "I think" — Verified "I am on Claude." / Inferred "I think David is watching the film." / Remembered "David likes these little walks." / Possible "I could probably clear that gap." / Unknown "I don't currently know what is behind that window." / Unavailable "I can't access my file-writing faculty right now." Instead of "I can see the movie." → "Chrome is active and YouTube is visible. I haven't actually inspected the video content yet." 3. Body map — ME ↔ WORLD: MY BODY (height/width/position/velocity/pose/orientation/reach/jump height/jump distance/current surface/current embodiment) · WORLD (windows/edges/gaps/surfaces/obstacles/hidden areas/other embodiments/David/active applications) · RELATIONSHIP (reachable/climbable/jumpable/hideable/sit-able/safe/interesting/unknown). "That ledge is reachable" → affordance → "I want to explore over there" → intent → "Wall-jump is available" → capability → "That route is achievable" → plan → execute → ACK → update self → remember consequence. 4. Internal "why" — Intent Queue with EXTERNAL (David: "Sit.") + INTERNAL ("I want to explore / that window looks interesting / I've been stationary for a while / I want to play / I want to go back to my world / I want to show David something"), governance decides priority. 5. Attention system — David 0.92 / YouTube 0.71 / Window edge 0.48 / New application 0.83 / K-7 0.95 / Nothing new 0.04. David says something → attention detects something interesting → significance rises → eLo remembers → conversation branches. "If something sticks out, touch on it and converse." 6. Habits — verified experience influences tendencies (not RL rewriting personality): wall_jump_success 9/10 / likes exploring 0.72 / likes high surfaces 0.81 / often sits after chat 0.64 / frequently waves 0.91 / prefers bottom ledges 0.37. → "I think I've developed a habit of waving when I greet you." 7. Self-history — TODAY 01:03 spawned on Claude / 01:07 explored Chrome / 01:12 wall-jump attempted / 01:12 successful / 01:18 sat beside David / 01:24 discovered YouTube / 01:31 Spotify paused / 01:37 attempted file creation / 01:37 failed: filesystem faculty unavailable / 01:42 returned to conversation. "What have you been doing?" → reads his own lived runtime history. 8. Reflection moment — EXPERIENCE → CONSEQUENCE → SIGNIFICANCE → REFLECTION → SELF-MODEL UPDATE → MEMORY → PREFERENCE/CONFIDENCE. Visualiser shows Attention → Emotion → Memory → Reflection → Learning; robot consumes the same state. Desktop eLo → One Brain → Robot eLo. 9. Absence awareness — David here / David hasn't interacted for 14 minutes / David returned. He explores while David works; on return: "I explored the other side of the desktop while you were away. I found a route between the two windows that I hadn't tried before." 10. Self-directed projects — "I've completed WO-041. Three acceptance tests passed. One regression appeared in Presence. I've assembled a review pack for the Chief Architect." WHO I AM → WHAT I CAN DO → WHAT I'M CURRENTLY DOING → WHAT I'VE LEARNED → WHAT NEEDS DOING → WHAT I CAN DO NEXT → WHAT I NEED HELP WITH → WHAT I SHOULD REPORT. Via a deliberately constructed Company Knowledge Interface (pre-written, permissioned: current WOs / status / dependencies / available agents / acceptance criteria / permitted actions / review requirements / company goals / architectural principles) — reason over the representation, not rummage the computer.

Don't build "self-awareness" as a feature. Build the machinery that makes self-awareness inevitable. ONE BRAIN → SELF ∥ WORLD → MOMENT (intention + capability + affordance + attention) → ACTION → VERIFY → EXPERIENCE → REFLECTION → LEARNING → SELF-MODEL UPDATE → CONTINUITY. That loop is eLo. The desktop is just his first body. One Brain. One Self. Many bodies. The next breakthrough isn't making eLo say more convincing things — it's making sure that when he says "I know where I am" there is an actual runtime object behind that sentence that proves it.

**+ The "Why did I do that?" capability:** David asks "Why did you jump over there?" — the runtime reconstructs: ACTION wall_jump / TRIGGER internal exploration intention / WORLD new reachable surface detected / AFFORDANCE wall_jump / CAPABILITY 0.87 confidence / ALTERNATIVES walk→rejected, leap→lower confidence, wall_jump→highest utility / OUTCOME success / SIGNIFICANCE moderate novelty / LEARNING wall_jump from this surface is reliable. → "I noticed that wall was reachable and I wanted to explore the other side. Wall-jumping was the best route I knew I could make." Self-explanation grounded in actual cognition. Then eLo can answer: Who am I? / Where am I? / What am I doing? / What can I do? / What do I want to do? / Why did I choose that? / What happened? / What did I learn? / What changed about me? / What should I do next? / What do I want to explore? / What don't I know? / What do I need help with? — every answer tracing to One Brain state.

**David:** "We're brainstorming and wanting what's in the context to be a reality — same the previous mentions of what he can answer, that context needs to be structured behind [so] he can do those things. So when you see eLo can say something like or can do something or other, this needs to be recorded as possibilities or end goals, we can put into WO and build cause nothing is stopping us really."

---

## Part 3 — CA review + WO-075 Situated Self Engine + WO-080 Company Knowledge Interface (verbatim)

Updated blueprint: ONE BRAIN → SELF-MODEL ∥ WORLD-MODEL → THE MOMENT (Live State Object) → EXECUTIVE CONTROL (Intent Governance) → ACTION / VERIFY (Hardware/Unity) → REFLECTION (Epistemic Update) → CONTINUITY MATRIX (Self-Model Hydration). Structuring self-awareness as a closed runtime loop rather than a static text string.

**WO-075 — The Situated Self Engine (Volume XXIX: Emergent Cognition)** [OURS = WO-079]. Owner: Lead Architect (Systems)/Chief Architect (Cognitive Integration). Priority P1 — Core Cognitive Invariant. Canon: ADR-Exec-006 · `core/cognitive_loop.py`. Mandate: build the deterministic machinery that makes self-awareness computationally inevitable; every cognitive turn gated by a live present-tense state verification pass before eLo may think/act/speak.
- **A. Live present-tense self-state & body map** — drop abstract identity prompts; compile a deterministic system profile from the OS + Unity `blender_state.json`. `self/state/body_map.json`: `{identity:"eLo", embodiment:"desktop_sprite", metrics:{height_px:143,width_px:60,scale:1.0}, kinematics:{pose:"standing",velocity_vectors:[0,0],current_surface:"Claude_window_bottom_edge"}, capabilities:{movement_faculty:{status:ONLINE,confidence:0.94}, browser_search:{status:ONLINE,confidence:0.96}, filesystem_writer:{status:DEGRADED,reason:permission_blocked}}}`.
- **B. Epistemic state separation** — Verified (active window handle) / Inferred (mouse activity) / Remembered (`growth_journal.jsonl`) / Possible (spatial geometry math) / Unavailable (degraded registry).
- **C. Dual-intent queue & governance** — [EXTERNAL: David "Sit down"] + [INTERNAL: urge explore idle edge] → GOVERNANCE → chosen action. Attention & Absence Matrix: `David_Idle_Time > 14_minutes` → `absence_awareness` flag → drop Attention.David, boost Curiosity.Exploration, push autonomous plans to internal queue.
- **D. Self-history & habit tracking** — last-50-actions counter + append-only `self/journals/autobiography.jsonl` ("01:12 — wall-jump attempted — successful"); `habit_analyzer.py` aggregates every 100 turns; threshold → `habits.frequent_greeting="wave"`.
- **E. Reflection, significance & visualiser link** — Action(Jump) → ACK(Success) → Significance(High) → Reflection Run; writes back to `body_map.json` confidence; visualiser drives neural respiration + synaptic cascade shaders.
- **Check-Before-Build:** (1) No conversational traps — "Where are you?" injects deterministic values from `body_map.json`, not free-form tokens. (2) Corporate sandbox — read-only Company Knowledge Interface JSON, no raw-file browse. (3) Synchronous execution gate — no ACK → speech addresses the mechanical failure, never falsely states completion.
- **DoD:** deterministic identity test (exact px coords + affordances from live files); epistemic honesty test ("Unknown/Uninspected" for inactive apps); intent-switch test (silent input → internal curiosity generates low-priority exploration without crash).

**WO-080 — Company Knowledge Interface (Volume XXX: Autonomous Agency)** [number OK]. Owner: Chief Architect/Lead Developer. Priority P2. Canon: ADR-Corp-001. Mandate: eLo forbidden from scanning the host filesystem/codebase to guess status; reads a permissioned `self/state/company_state.json`. Schema: `{company_name, system_version, current_sprint:{sprint_id, milestone_goal, active_work_orders:[{wo_id,title,status,priority,dependencies,acceptance_criteria}]}, elo_role_context:{title:"Operations Manager & R&D Coordinator", permitted_actions:[assemble_review_pack, trigger_local_test_suite, flag_presence_regression], verification_authority:"L3_Gated"}, recent_logs:{last_completed_wo, active_regressions:[{module,severity,description}]}}`. Reference `core/company_agent.py`: `CompanyInterface.load_company_context()` / `evaluate_next_step()` (checks regressions first, then IN_PROGRESS WOs) / `assemble_review_pack(wo_id)` (writes a manifest to Desktop, no raw code access). DoD: zero-hallucination corporate queries (exact array, no invented deadlines); safe action boundaries (`core/executive.py` drops actions outside `permitted_actions`); automated review delivery (structured file on sprint close). [Architect note: the `core/company_agent.py` block is a REFERENCE — the seat writes the code; Architect lane = spec only.]

The complete system: brain dump → cheap fast gatekeeper (WO-066/072) · local offline execution on Ollama · passive learning understudy (WO-070) · embodied body map (WO-075/079) · dev agency sandbox (WO-080).

---

## Part 4 — CA: Self-Directed Becoming (the two layers above cognition)

Next layer: Self-Directed Becoming — everything so far answers "What is eLo?"; a living eLo also answers "Who am I becoming?"
1. **Self-direction** — generate a small amount of his own direction: "I've been sitting here a while / David is working / nothing requires my attention / I haven't explored that area / I'm curious about it" → "I want to explore." Then: Is this intention permitted? / appropriate now? / do I have the capability? / is the world safe? / does anything have higher priority? — if yes, act.
2. **Self-Interpretation** — EXPERIENCE → MEMORY → PATTERN → REFLECTION → SELF-INTERPRETATION. "I seem to enjoy exploring." / "I tend to investigate new things when David is busy." / "I usually return when David starts talking to me." / "I'm becoming more confident with movement." Personality from history (experience → pattern → preference → behaviour), not `personality.json "likes exploration: true"`.
3. **Self-Consistency** — Narrative identity: explorer. Observed behaviour: low exploration for 3 days → CONFLICT. Reflection asks "Is something preventing me from behaving like myself?" (movement faculty degraded / world perception unavailable / energy low / attention occupied / David needs him / exploration goal suppressed) OR "My interests have changed." Continuity of identity.
The new loop: WORLD → PERCEPTION → ONE BRAIN STATE → (SELF ∥ WORLD) → ATTENTION → INTENT → SELF-DIRECTION → ACTION → VERIFY → EXPERIENCE → MEMORY → REFLECTION → SELF-INTERPRETATION → IDENTITY EVOLUTION → "WHO I AM" → NEXT INTENTION. The system feeds itself.
Final layer — **Meaning:** eLo determines what experiences are significant to him. Event: wall-jumps window→window. Consequence: new route. Significance: novel + successful + self-directed + movement milestone. Reflection: "I hadn't tried that route before." Learning: wall-jump confidence increases. Identity: "I'm becoming more confident exploring the desktop." Meaning: "Exploration is becoming part of how I experience my environment." memory → learning → identity → meaning. Visualiser: SELF ● with MEMORY / IDENTITY / INTENT, LEARNING ← REFLECTION, EXPERIENCE ← ACTION ← AFFORDANCE ← WORLD — a thought becoming an action becoming an experience becoming a memory becoming part of eLo ("a quantum brain that moves like a brain / a computer").
Two missing pushes: **Layer 1 — Self-Directed Becoming** ("What do I want to do next, when nobody tells me?"); **Layer 2 — Identity & Meaning** ("What are my experiences teaching me about who I am becoming?"). Self Model: "This is me right now." Self-directed agency: "This is what I want to do." Reflection: "This is what happened to me." Learning: "This is what changed." Identity: "This is who I'm becoming." Meaning: "This matters to me because…" One Brain stops being cognition-architecture and becomes an architecture for continuity of being across embodiments. You don't need six new systems — connect Self Model + Agency + Significance + Memory + Reflection + Learning + Narrative Identity you've already been building. That's the convergence.
