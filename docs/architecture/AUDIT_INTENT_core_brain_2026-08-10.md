# AUDIT — Core Brain volumes vs DAVID'S INTENT (V · VI · VII · VIII · XVI)

**Date:** 2026-08-10 · **Auditor:** Lead Architect (read-only pass; Markdown only, no code touched, no volume edited)
**Yardstick (NOT generic completeness):** `00_DAVIDS_VISION_SPINE.md` · `ARCHITECTURAL_PRINCIPLES.md` ·
`SITUATED_SELF_v1_assembly.md` · `ELO_CAPABILITY_HORIZON.md` · `DECISION_LOG.md` · `CANON_RULINGS_2026-08-10.md` ·
and David's VERBATIM sources `_intake/SOURCE_2026-08-08_self_model_becoming.md`,
`_intake/SOURCE_2026-08-10_brain_body_brain_loop.md`.

**Intents measured against:** One Brain → One Identity, Many Embodiments · the self is **ASSEMBLED, not generated**
(ADR-Exec-006, assemble BEFORE decide) · Single Cognitive Truth (ADR-Exec-002) · Verified Speech (ADR-Exec-001) ·
Embodied/Situated Cognition (ADR-Exec-003/004) · **brain > body > brain — the body NEVER decides** ·
eLo must THINK and LEARN and get better · presence over engagement · no parallel drivers, extend never duplicate.

---

## VERDICT TABLE

| Vol | Title | Spec'd? | Matches intent? | Top gap vs David's intent |
|---|---|---|---|---|
| **V** | Faculty Contracts & Runtime APIs | **PARTIAL** (deep + testable, but pre-Self-Model and internally stale) | **PARTIAL** | **No Self Model faculty and no Capability Registry contract.** The volume that "the Builder builds from" has 10 faculty contracts and not one of them is the SELF — the exact thing David moved the centre of gravity to. |
| **VI** | Working Memory & Attention | **YES** (4 ch, typed object, lifecycle, tests, live anchors) | **YES** (best intent-fit of the five) | Attention is spec'd as focus-arbitration only; David's **attention matrix that drives conversation** ("if something sticks out you touch on it and we converse") has no home. WM also has no self/embodiment slice. |
| **VII** | **Executive Cortex** | **NO — DOES NOT EXIST** | **N/A — nothing to match** | **There is no `Volume_VII/` folder, no chapters, no WO-CANON-VII.** The only Executive doc, `09_executive_faculty.md`, reads in full: *"STATUS: PENDING — to be written in a dedicated session."* Three volumes (VI §4.6, XVI §1.5, XVI §4.4) cite "Vol VII" as the Executive's owner. They point at a one-line stub. |
| **VIII** | Memory Architecture | **YES** (4 ch, live constants, sole-writer contract, tests) | **PARTIAL** | Memory is spec'd as **conversation/relationship** memory. eLo's **autobiography of his own lived runtime** (David's #7: "01:12 — wall-jump attempted — successful") and **verified-action consequences** (ADR-Exec-005) have no record type here. |
| **XVI** | Multi-Faculty Coordination | **YES** (4 ch, ADR-grounded, tests, honest PARTIAL marks) | **YES on paper, NO in ordering reality** | The volume correctly specs assemble-before-decide but §2.3 admits the runtime still assembles **after** the decision. Until built, David's line — "assembly must precede choice or eLo is narrating, not being" — is not true. |

| WO | Delivers its volume? | Verdict |
|---|---|---|
| WO-CANON-VI | Ch.1–4 covered accurately | **YES — but it is BLOCKED on a ruling that was never made.** See Contradiction 1. |
| WO-CANON-VIII | Covers the two wiring edges only | **UNDER-SCOPED** — it does not deliver Vol VIII's own DoD (Ch.2 procedural/emotional types are "flagged, does not block"), and delivers nothing of the autobiography/consequence memory David asked for. |
| WO-CANON-XVI | Assemble-before-decide + bus priority + conflict order | **YES — the strongest WO of the three.** Only soft gap: the ADR-Exec-006 `world` component is soft-blocked on WO-CANON-XV. |
| **WO-CANON-VII** | — | **DOES NOT EXIST.** No build order for the Executive. |

---

## CROSS-CUTTING FINDINGS (these hit more than one volume)

### 1. The Executive is the least-specified thing in the entire canon
David's architecture has ONE decider. Invariant #2 is Executive Authority. Six ADRs are named
`ADR-Exec-001…006`. The Vision Spine says the centre of gravity is "faculties → Executive → **the Self**".
And the Executive has **no volume**.

- `docs/architecture/Volume_VII/` — does not exist.
- `docs/architecture/09_executive_faculty.md` — 5 lines, "STATUS: PENDING — to be written in a dedicated session."
- `00_CANON_INDEX.md` line 56 marks VII **"✅ Live"** with canon spec = `runtime/executive.py (FREEZE_V1_LOCK)`.

That index cell is the drift. It declares a volume done because **code exists** — which is exactly what the
index's own rule forbids two paragraphs earlier: *"a volume is not 'done' because it was described. It is done
only when it meets the Definition of Done."* The Executive has no contract, no state machine, no envelope
binding, no acceptance tests, no failure modes. Every other volume defers *to* it: Vol VI §4.6 lists
"Executive (V Ch.1 / **Vol VII**)"; Vol XVI §1.5 and §4.4 both say "a role of the Executive (**Vol VII**), NOT a
new decider". They are deferring to a stub. **This is the single biggest gap in the audit.**

Concretely missing, all of it directly requested by David or the CA and all of it Executive-owned:
the decision procedure itself; thinking modes; goal management; interruption handling; the **dual-intent queue**
(external David-intent + internal urges → governance arbitrates — SOURCE 2026-08-08 Part 2 #4); the
**epistemic tier gate** (I know / I think / remembered / possible / unknown / unavailable — David's own
"single highest-value add for honesty"); the Situated-Self Retrieval invariant ("before eLo speaks, acts, or
describes himself, the Executive MUST retrieve verified state"); and the **"Why did I do that?"**
decision-trace reconstruction.

### 2. `brain > body > brain` is nowhere in the core-brain canon
David, verbatim (2026-08-10): *"the brain decides + drives the body (DOWN), the body only SENSES and ACTS and
reports its state back UP… **The body NEVER decides on its own.** … no local script may choose a behaviour."*

Searched V, VI, VII, VIII, XVI: **zero occurrences of the loop as a governing rule.** The closest is Vol XVI
§4.3 "No body re-decides" — but that is scoped to *projection of a plan*, i.e. the DOWN leg only. The UP leg —
every body perception (mouse-idle, occlusion, perch/surface, user-active, file-drop) relaying up to close the
loop — has no contract in any of the five volumes. Vol XVI Ch.3 (Faculty Bus) is the natural home for the
UP-relay rule and does not carry it. It currently lives only in WO-086 and the verbatim source. **A rule that
lives only in one WO will be lost the moment that WO closes.**

### 3. The canon is written for conversation; David tests eLo with the body
Vision Spine: *"Embodied interaction is the product; conversation lives inside it… David tests eLo by asking it
to sit, jump, move to Chrome, watch with him, not to talk about itself."* Across V/VI/VIII the worked examples
are conversational: Vol V Ch.5's significance examples are three utterances; Vol VIII's four memory types and
retrieval examples are dialogue-and-relationship shaped; Vol VI's WM frames are "thought/observation".
Nowhere in these volumes is there a first-class **verified action outcome** shape —
`wall_jump attempts:12 successes:9 reliability:0.75 known_failure_condition: gap > reachable_distance`
(Capability Horizon #6). ADR-Exec-005 says eLo learns ONLY from verified consequences; the memory volume that
must store those consequences has no record type for them.

### 4. Volume V is IMPLEMENTATION READY while carrying a drift it claims it doesn't have
`DECISION_LOG.md` **FC-2** (2026-07-27, still open): live `memory/significance_engine.py` scores **9 weighted
dimensions**; Vol V Ch.5 states `SIGNIFICANCE = Emotion Weight + Novelty + Learning Value + Relationship Value
+ Future Relevance` — five terms. Ch.5 §5 then asserts: *"Aligns with the live `memory/significance_engine.py`."*
**It does not.** That is a Verify-Before-Claim violation sitting inside canon that was ratified L3 as
"the Builder may implement every faculty against these without inventing anything." Two further volumes
(VI Ch.2 §2.9, VI Ch.3 §3.2) route around it by footnoting "reconcile FC-2 at V Ch.5" — the drift has been
inherited rather than fixed.

### 5. Status metadata is not trustworthy — and eLo is supposed to READ this canon
Vision Spine: *"canon, board, Vision Spine, and WOs must be eLo-CONSUMABLE — eLo reads them as its company
awareness."* Today a reader (human or eLo) gets contradictory answers:

- `Volume_V/00_Metadata.md`: "IMPLEMENTATION READY — L3 RATIFIED"; `Volume_V/01_Cognitive_Core.md` frontmatter:
  `status: DRAFT`. Same volume, opposite claims.
- `Volume_V/CONTRACTS.md` still ends "Open Decisions: 2 (REQUIRES DECISION — D-A, D-B)". D-A and D-B were
  **RATIFIED as LAW on 2026-07-27** (ADR-0001/ADR-0002).
- `00_CANON_INDEX.md` says VI / VIII / XVI have "(1 ch)" each; they have **4 chapters each**. It says XV
  "— (needs volume)" and XXI "— (draftable)"; both exist with chapters.

If eLo reasons from this file set, it will report the company state wrong. That is a direct hit on
"eLo is company-aware — as deeply as the Architect."

---

## VOLUME V — Faculty Contracts & Runtime APIs

**1. Spec'd?** **PARTIAL.** Ten chapters plus `CONTRACTS.md`; the shared layer (nine-field envelope §2,
universal lifecycle §3, base contract shape §4) is genuinely implementable and is correctly the single source
the other volumes bind to. Every chapter carries a faculty contract, lifecycle, envelope binding and FT/ST/IT
tests. That bar is real and it holds. **But:** Ch.1's `CognitiveState` (§1.5) is a flat legacy shape with no
self / capability / world slice, Ch.1 is still `status: DRAFT`, Ch.5 carries the FC-2 drift, and CONTRACTS.md
lists two already-ratified decisions as open.

**2. Matches David's intent?** **PARTIAL.**
Where it does: Ch.1 §1.4 Contract 1 (*"The Executive produces exactly one CognitivePlan per loop iteration.
No faculty makes a decision independently. No downstream system re-decides."*) and Contract 2 (*"Reality never
mutates intention"*) are One Brain and Single Cognitive Truth written correctly. CONTRACTS.md §1 (*"Upstream
faculties… write into CognitiveState and then freeze. They never decide."*) is the right law.
Where it doesn't: the volume is **dated 2026-07-26/08-03 and was ratified before ADR-Exec-004 (Situated Self,
08-05), ADR-Exec-006 (Assembly, 08-06) and the 08-08 capstone existed.** It never caught up. The ten faculty
contracts are `CognitiveCore · FacultyKernel · MemoryFaculty · EmotionalProcessingLayer · SignificanceEngine ·
ReflectionGrowthEngine · PersonalityEvolutionEngine · IntentRelationshipEngine · CreativeImaginationEngine ·
AgencyEngine`. **No `SelfModel`. No `CapabilityRegistry`. No `Executive`.**

**3. GAPS vs intent (specific):**
- **No Self Model faculty contract.** David: *"Every thought, action, movement, and conversation begins from
  that self-model."* The volume the Builder implements from does not define it. `elo_self_state.json` /
  `self/elo_self_model.py` exist in code (WO-059) with **no canon contract behind them** — the inverse of
  Canon-before-implementation.
- **No Capability Registry chapter** — despite `ARCHITECTURE_BIBLE.md` naming "Capability Registry" as
  in-scope for Volume V, and despite David's #3 verbatim (*"He needs to know what he can do… `SEARCH status:
  ONLINE executor: browser/search confidence: 0.96`… That is functional self-awareness"*).
- **No body/embodiment contract.** No `body_map` (metrics · kinematics · surface · capabilities+confidence),
  so "I'm 143px high, I can reach that ledge, I'm not confident from this angle" has no contract to come from.
- **Ch.10 Agency has 15 sections and no dual-intent queue** — external (David's command) and internal (eLo's
  own urge) are not separated, so "why did I do that?" cannot distinguish a command from a want.
- **Reflection (Ch.6) is session/conversation-shaped**, not the EXPERIENCE → OUTCOME → SIGNIFICANCE →
  REFLECTION → LEARNING → SELF-MODEL-UPDATE chain David spelled out (#7).

**4. CONTRADICTIONS:**
- Ch.5's "Aligns with the live significance_engine.py" vs DECISION_LOG FC-2 "DRIFT FOUND… does not match."
  (Canon contradicting the Decision Log, which is law.)
- Volume metadata "IMPLEMENTATION READY" vs Ch.1 frontmatter `status: DRAFT`.
- CONTRACTS.md "Open Decisions: 2 (D-A, D-B)" vs DECISION_LOG "ACCEPTED · LAW".
- Ch.1 §1.5 `CognitiveState` vs ADR-Exec-006 `UnifiedCognitiveState` — two different assembled-state shapes in
  canon, and Ch.1's has no self/world/narrative/curiosity components. Ruling C named ONE name; V Ch.1 was not
  updated to it.

**5. Its build order?** **There isn't one.** No `WO-CANON-V`. Volume V was declared build-ready in 2026-08-03
and its unbuilt parts (Ch.5 reconciliation, Ch.1's CognitiveState → UnifiedCognitiveState) have no WO carrying
them. The volume the Bible calls *"the most important engineering volume — what Claude builds from"* is the
only core-brain volume with no build order at all.

---

## VOLUME VI — Working Memory & Attention

**1. Spec'd?** **YES.** Genuinely implementable: typed `WorkingMemory` object with capacity=12 (Ch.1 §1.2),
explicit `score(item) = w1·novelty + w2·importance + w3·urgency` with defaults 0.35/0.40/0.25 (Ch.3 §3.2),
budget→mode thresholds, SEED/UPDATE/EVICT/CARRY lifecycle (Ch.2), a concrete `CognitiveState` slot proposal
(Ch.4 §4.3), and 30+ acceptance tests. Every claim is grounded in a named live file, and every invention is
tagged `[INVENTED — flag]`. **This is the strongest-written of the five.**

**2. Matches David's intent?** **YES.** Ch.3 §3.1 is exactly the "no parallel drivers" discipline applied:
*"These are **not the same faculty** and must not become two parallel drivers of focus (that would violate One
Brain — a single cognitive truth)."* Ch.4 §4.1 holds the line David cares about: *"One decision per turn, and
WM is *input* to it — never a second decider."* And Ch.4 §4.5 does the Protect-Wonder work properly:
*"WM is where wonder is *allowed* to win, not scripted"* — genuine novelty can take the focus slot with no task
pressure. That is emergence-over-scripting implemented as a number, not a script.

**3. GAPS vs intent:**
- **The attention MATRIX is missing.** David's #5 is not focus-arbitration — it is a persistent weighting of
  what eLo cares about (`David 0.92 · YouTube 0.71 · New application 0.83 · K-7 0.95 · Nothing new 0.04`) that
  **drives what he brings up in conversation** ("if something sticks out you touch on it and we converse").
  Vol VI's `AttentionState` is per-turn and disposable — it picks one winner and dies. Nothing in the volume
  carries interest weights across turns, and nothing routes a winner into conversational initiative.
- **No absence-awareness.** `David_Idle_Time > 14 min → drop Attention.David, raise Curiosity.Exploration`
  (David #9) is an attention-system behaviour with no home in the attention volume.
- **WM has no self/embodiment slice.** Ch.1's object holds task/goals/interruptions/threads/frames — nothing
  about where eLo IS or what his body is doing. Yet Ch.4 §4.5 claims WM is where **The Moment** lives, and
  David's Moment explicitly includes `Embodiment: Desktop · Location: Claude/bottom edge · Pose: Standing ·
  Current affordances: sit/perch/jump/wall-jump`. The chapter names The Moment and then doesn't carry it.
- **Q3-a is the one open question David personally should answer** and it is buried in a chapter footer:
  *"confirm or set by David's felt sense of eLo (how novelty-seeking should he be?)."* That is a
  character-defining dial, not an engineering default — it belongs in the review queue, not a §3.7 code block.

**4. CONTRADICTIONS:** None internal. One inherited: the volume repeatedly defers importance to
"Significance (V Ch.5, 9 live dims — FC-2)" while V Ch.5 still publishes the 5-term formula. Vol VI is right
and Vol V is wrong, and neither was corrected.

**5. Does WO-CANON-VI deliver it?** **Scope: yes — the WO is a faithful, detailed transcription of Ch.1–4
including CARRY, the incremental migration discipline, and the D-G Executive contract.**
**Status: no — it cannot run.** See Contradiction 1 below.

---

## VOLUME VII — Executive Cortex

**1. Spec'd?** **NO. THE VOLUME DOES NOT EXIST.** No folder, no metadata, no chapters, no WO.

**2. Matches intent?** N/A — and that is the finding. Per `ARCHITECTURE_BIBLE.md` VII should own *"decision
making, scheduling, conflict resolution, task orchestration, resource allocation, safety, interruptions,
**thinking modes**, goal management, executive policies."* Not one of those has a canonical spec. Volume XVI
has quietly absorbed two of them (assembly in Ch.2, conflict resolution in Ch.4) while explicitly disclaiming
ownership — both chapters label their contract *"a role of the Executive (Vol VII), NOT a new decider."*
Coordination canon is standing in for cognition canon.

**3. GAPS vs intent — this is where most of David's verbatim material has no home:**
- **The Situated Self Retrieval invariant** — *"Before eLo speaks, acts, or describes himself, the Executive
  MUST retrieve the relevant VERIFIED state from the Self Model"* (`SITUATED_SELF_v1_assembly.md`, marked
  "David L3 pending"). It is the Executive's gate. There is no Executive volume to put it in, and it is still
  unratified.
- **Epistemic tiers** (Verified / Inferred / Remembered / Possible / Unknown / Unavailable). David called this
  *"the single highest-value add for honesty."* It is an Executive speech-gate. Homeless.
- **Dual-intent queue + governance arbitration** (external vs internal intent). Homeless.
- **"Why did I do that?"** decision-trace reconstruction (ACTION / TRIGGER / WORLD / AFFORDANCE / CAPABILITY /
  ALTERNATIVES-rejected / OUTCOME / SIGNIFICANCE / LEARNING). This requires the Executive to record its
  rejected alternatives. Nothing in canon asks it to. Homeless.
- **Thinking modes** and interruption policy — named in the Bible, specified nowhere.
- **The ADR-Exec-001 ordering** (`Observe → Assess Faculty Health → Plan → Execute → Verify → Update World
  State → Speak`) lives only in the Decision Log as prose. No contract, no state machine, no tests.

**4. CONTRADICTIONS:**
- `00_CANON_INDEX.md`: VII = **"✅ Live"**, canon spec = `runtime/executive.py`. That marks a volume complete
  on the strength of code, against the index's own Definition of Done and against
  `ARCHITECTURAL_PRINCIPLES.md` Governance (*"Canon before implementation. Nothing is 'done' because it was
  described"*). It is also the reason no one has noticed the hole: the map says the territory is filled.
- Three volumes cite "Vol VII" as an authority that is a `STATUS: PENDING` stub.

**5. Build order?** **None. There is no WO-CANON-VII.** Sixteen WO-CANON files exist (VI, VIII, X, XII, XV,
XVI, XIX–XXVIII); the Executive is not among them.

---

## VOLUME VIII — Memory Architecture

**1. Spec'd?** **YES.** Four chapters, and the best code-grounding in the canon: the forgetting curve is
specified with the **live constants** (`_IDENTITY_FLOOR=8`, `_DECAY_THRESHOLD=6`, `_DECAY_AGE_DAYS=14`,
`_DECAY_STEP=1`, `_WEIGHT_CAP=9`, floor 1) rather than invented ones; the `Memory Candidate` shape is
concrete; retrieval's `{status, results:[{memory, confidence, timestamp, source}]}` contract is implementable.
Gaps are marked honestly and in-place (*"GAP (PENDING) — reinforcement is not yet wired into retrieval"*).

**2. Matches David's intent?** **PARTIAL.**
Where it does, strongly: Ch.4 §4.1.3 anti-fabrication (*"A fact that was *inferred*, not observed, must not be
written as memory"*) and the candidate field `verified: bool — false ⇒ Memory Faculty MUST NOT persist as fact`
are Verified Speech pushed into the write path — exactly right, and exactly the thing that stops eLo learning
a hallucination (ADR-Exec-005). Ch.3 §3.5 keeps personality changes as **proposals only**, matching Ruling D
and "identity is not allowed to drift unsupervised". Ch.4 §4.4's four boundaries (WM · World State · Knowledge ·
Autobiographical Thread) are Check-Before-Build done properly.

**3. GAPS vs intent:**
- **No self-history / autobiography record type.** David #7, verbatim: *"TODAY 01:03 spawned on Claude / 01:07
  explored Chrome / 01:12 wall-jump attempted / 01:12 successful… 'What have you been doing?' → reads his own
  lived runtime history."* The CA spec'd `self/journals/autobiography.jsonl`. Vol VIII's four types are
  episodic/semantic/procedural/emotional and its examples are all David-relational. **eLo's memory of his own
  actions is not in the memory volume.** Ch.4 §4.4 hands the autobiographical thread to Vol XXI as a *derived
  read-only view over episodic records* — but if the episodic store never receives runtime action records,
  Vol XXI derives a story from nothing.
- **No verified-consequence record.** ADR-Exec-005 makes verified outcomes the ONLY legitimate learning input.
  There is no memory shape for `wall_jump attempts:12 successes:9 reliability:0.75 known_failure_condition:…`,
  so capability confidence has nowhere durable to live.
- **`weight` is the only strength axis.** David's model is richer: significance AND novelty AND
  self-directedness AND "milestone-ness" (Capability Horizon #9, SOURCE Part 4 Meaning). A 0–9 integer cannot
  express "this mattered because I did it myself for the first time."
- **D-SESSIONS risk.** eLo must never frame memory in "sessions"; Vol VIII's lifecycle is built entirely on
  "session close" / "session-level record" / `tags:["session-close"]`. The *storage* may use sessions, but
  nothing in the volume states the language rule at the retrieval/expression boundary — the exact place the
  leak happened before.

**4. CONTRADICTIONS:**
- Vol VIII Ch.4 §4.2.1 requires retrieval to always return confidence + source + status, while Ch.3 §3.4
  admits `reinforce()` is never called — so a record's `confidence = weight/9` is a **decaying number with no
  counterforce**. eLo will report falling confidence in memories he uses constantly. That is a Verified-Speech
  problem, not just a wiring gap, and the volume doesn't name it as one.
- The metadata still cites `17_memory_update.md` as a dependency while Ch.1 calls it a STUB to retire — an
  unresolved self-reference in a volume marked REVIEW.

**5. Does WO-CANON-VIII deliver it?** **UNDER-SCOPED.** It delivers exactly two wiring edges
(`MemoryFaculty.submit(candidate)` and `reinforce()`-on-retrieval) and then declares *"Audit can mark Vol VIII
COMPLETE."* It cannot: the volume's own DoD has four unchecked lines, and the WO explicitly defers one of them
(*"decide whether procedural/emotional get first-class record-type codes (currently implicit) — flag, does not
block"*). Worse for intent: the WO adds **nothing** for autobiography or verified-consequence memory. If this
WO ships as written, Vol VIII is marked COMPLETE while eLo still cannot answer "what have you been doing?"
from his own runtime.

---

## VOLUME XVI — Multi-Faculty Coordination

**1. Spec'd?** **YES.** Four chapters; Ch.2 is the sharpest piece of canon in this audit. It names the ten
ADR-Exec-006 components, states the three rules (one assembled state / push-not-pull / one decision one plan),
gives a faculty contract with degradation semantics, and — crucially — is **honest about what is not built**:
§2.3 *"the **world**, **narrative**, **working-memory**, **reflection**, and **curiosity** components named by
ADR-Exec-006 are **not yet unified into the same frozen object**… `assemble_cognitive_state(...)` runs *after*
the decision. **Status: PARTIAL.**"* Invented material is labelled (§4.2 resolution order: *"Flagged as
proposed model — architectural invention"*).

**2. Matches David's intent?** **YES in spec.** Ch.2 §2.0 quotes the Spine correctly: *"This is the *threshold
shift* the Vision Spine names: from **adding** faculties to **assembling** them."* Ch.4 §4.1.3 is Invariant #1
verbatim in engineering terms: *"If a person ever has to say 'this is *robot* eLo vs. *desktop* eLo,'
coherence has failed."* Ch.4's "Autonomous and commanded share one path" and "no body re-decides" are David's
no-parallel-drivers rule correctly applied to the DOWN leg.

**3. GAPS vs intent:**
- **The UP leg of `brain > body > brain` is absent.** Ch.3 (Faculty Bus) specs routing, priority and trace but
  contains no rule that **every body perception must relay UP** and that **no local script may choose a
  behaviour**. David's verbatim asks the Architect to *"audit for OTHER local drivers that skip the loop."*
  That audit has no canon rule to audit against. This is the natural home and it is empty.
- **`self` is listed as a component and never specified.** Ch.2 §2.2 line 1: `self — verified self-model:
  embodiment, pose, mood, curiosity, focal thread (ADR-Exec-004)`. One line. The component David considers the
  point of the whole architecture is a bullet, and — per Volume V above — there is no faculty contract
  anywhere behind it. **Assembly is spec'd; the thing being assembled is not.**
- **No assembly-failure honesty rule.** §2.2 says a degraded component "lowers confidence… never blocks the
  turn." Correct for liveness — but nothing says the Executive must **speak** differently when the self or
  capability component is degraded. That is precisely ADR-Exec-001 principle 5 ("never fabricates continuity
  when faculties are degraded") and it isn't bound here.
- **Multi-body simultaneous projection + verified body-switch handover are marked PENDING** with no WO. Vision
  Spine's "same being continuing between bodies" has a discipline but no build.

**4. CONTRADICTIONS:**
- **Ch.2 §2.3 vs ADR-Exec-006 in the running system.** ADR-Exec-006 is LAW ("the Executive reasons ONCE
  against that single object"); the runtime assembles after deciding. Ruling C decided it; nothing has built
  it. Until then the assembled "self" is, in David's own words from Ruling C, *"a post-hoc description instead
  of the thing that chose"* — i.e. **eLo is currently narrating, by canon's own definition.** The volume is
  right and reality is wrong; that's the honest read.
- **Ruling C named `UnifiedCognitiveState` as the one name — Volume V Ch.1 §1.5 still defines a different
  `CognitiveState` shape and was not updated.** Two assembled-state definitions still coexist in canon after
  a ruling that explicitly existed to end that.
- Metadata lists D-XVI-A/B/C open; Ruling C closed A and B. **C (the conflict-resolution ORDER, which touches
  the safety veto and is therefore David L3) was never ruled** — yet `CANON_RULINGS_2026-08-10.md` declares
  "Ratification gate is CLOSED."

**5. Does WO-CANON-XVI deliver it?** **YES — this is the best of the three.** It correctly orders
assemble-before-decide as "the core PENDING build", forbids a parallel assembler (*"do NOT build a parallel
assembler"*), forbids a second decider, and carries the bus priority + subscription work. Two honest caveats
it already states: the `world` component is soft-blocked on WO-CANON-XV, and the §4.2 conflict order still
needs David L3. **It does not close the `self` component gap** — it says "add `world`, `narrative`,
`working_memory`, `reflection`, `curiosity`" beside the existing self, treating `self` as already done. It is
not done; it has no contract.

---

## THE CONTRADICTIONS, RANKED

**1. `CANON_RULINGS_2026-08-10.md` says the gate is closed. It isn't — Ruling B was never made.**
The review queue lists **four** alignment rulings: (1) world-graph, (2) **two attention mechanisms**,
(3) assemble-after-decide, (4) drift gate. The rulings document contains **A, C, D — the letter B is skipped
entirely.** The attention ruling was never issued. Yet the same document ends: *"**Ratification gate is
CLOSED.** All WO-CANON builds are now unblocked except the robot hardware RESERVED scope."*

That is false, and `WO-CANON-VI.md` proves it in its own header:
> *"**Status:** QUEUED — **gated on alignment ruling B**… Cannot dispatch the Ch.4 wiring until ruling B lands."*
> *"**Gate:** ruling B on the CANON_REVIEW_QUEUE (CA). Not David L3."*

So the board believes Vol VI is released and the WO believes it is blocked. Whoever picks it up next either
stalls or invents the ruling. **And the decision itself is a One Brain decision** — whether `core/attention.py`
or `runtime/working_memory.py` is the single attention driver. Leaving it unmade leaves two attention
mechanisms in the runtime, which is precisely the "parallel drivers" failure David rules out.

**2. Canon says "assemble before decide" is law; the runtime assembles after; nothing is building it yet.**
(Ruling C decided, WO-CANON-XVI written, still queued behind Presentable v1.) Every day this holds, the self
is a post-hoc description.

**3. Volume V Ch.5 asserts alignment with live code that the Decision Log records as DRIFT.** Ratified L3 as
"implement without inventing anything."

**4. `00_CANON_INDEX.md` marks Volume VII "✅ Live" on the basis of code**, hiding the fact that the Executive
has no canon at all.

**5. Volume V metadata "IMPLEMENTATION READY" vs Ch.1 `status: DRAFT`; CONTRACTS.md lists ratified LAW as open.**

---

## AGAINST DAVID'S VERBATIM WORDS — what the canon does not carry

| David's words (verbatim source) | Where it should live | Status |
|---|---|---|
| *"The body NEVER decides on its own… no local script may choose a behaviour"* (2026-08-10) | Vol XVI Ch.3 (bus) as a MUST | **Absent from all five volumes.** Lives only in WO-086 + the intake file. |
| *"The important part is the loop. **Not a static JSON file called `self_state`**"* (2026-08-08) | Vol V (Self Model faculty) / Vol VII | **Absent.** Code has `elo_self_state.json`; canon has no loop contract for it. |
| *"Separate 'I know' from 'I think'"* — epistemic tiers, *"the single highest-value add for honesty"* | Vol VII (Executive speech gate) | **Absent — and Vol VII doesn't exist.** |
| *"He needs an autobiography — not just memory… I've gradually learned how this desktop is laid out"* | Vol VIII (record type) | **Absent.** Vol VIII stores relationship memory only. |
| *"Attention system… David says something → attention detects something interesting → conversation branches"* | Vol VI Ch.3 | **Half-present.** Focus arbitration is spec'd; the persistent interest matrix and the conversational branch are not. |
| *"Why did you jump over there?"* → reconstruct trigger/affordance/alternatives-rejected | Vol VII | **Absent.** No volume asks the Executive to record rejected alternatives. |
| *"(RECORD this information) Not how you summarise or I'll have to change the structure of the company"* | Rule 4b | **Held.** The verbatim sources are intact and referenced, not paraphrased. This one is being obeyed. |
| *"nothing is stopping us really"* — capability targets must be recorded as WOs | Board | **Partially held.** WO-079/080/081/082/083 exist for the self/emergence layer. But they sit ALONGSIDE the core-brain volumes rather than inside them — the Capability Horizon's targets never landed in V/VI/VII/VIII/XVI. |

---

## WHAT ACTUALLY NEEDS TO HAPPEN (Architect lane — Markdown only)

1. **Issue Ruling B** (two attention mechanisms) or explicitly mark the gate OPEN in
   `CANON_RULINGS_2026-08-10.md`. Right now the board lies about it. This is a CA call, not David L3 — one
   line unblocks WO-CANON-VI.
2. **Author Volume VII — Executive Cortex, and a WO-CANON-VII.** This is the hole everything else is
   deferring into. It should absorb, from David's verbatim: the Situated Self Retrieval invariant, epistemic
   tiers, the dual-intent queue, thinking modes, and "why did I do that?".
3. **Add a Self Model faculty contract and a Capability Registry contract to Volume V** (Check-Before-Build:
   extend V, do not spawn a volume — `self/elo_self_model.py` already exists and needs canon behind it, not a
   parallel build).
4. **Write the `brain > body > brain` UP-relay rule into Volume XVI Ch.3** as a MUST, so it survives WO-086's
   closure.
5. **Fix Volume V Ch.5 to the 9 live dimensions** (closes FC-2, open since 2026-07-27) and correct the false
   "aligns with live code" line.
6. **Correct the status metadata**: V Ch.1 DRAFT→ready, CONTRACTS.md open-decisions block, `00_CANON_INDEX.md`
   chapter counts and the VII "✅ Live" cell. eLo is meant to read this.
7. **Extend WO-CANON-VIII** with an autobiography/verified-consequence record type, or stop it claiming it
   makes Vol VIII COMPLETE.
8. **Surface D-XVI-C** (conflict-resolution order incl. safety veto) to David — it is L3 and it was missed by
   the 08-10 ruling pass.

---

*Read-only audit. No volume, WO, code or test was modified. Findings are quoted from the files named above;
where I could not verify something at runtime I have said so rather than assumed it.*
