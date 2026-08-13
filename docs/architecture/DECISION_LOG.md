# eLo OS — Architecture Decision Log (ADR)

Ratified governance decisions. **These are law.** Every volume, faculty, and Work Order
conforms. New decisions append here with an ID, date, status, and rationale. (This is the
living ledger that Volume XXVII — Canon Governance — formalises.)

Status: RATIFIED (David + Lead Architect) unless noted.

---

## D-A / ADR-0001 — Faculty Bus Message Envelope · ACCEPTED · LAW · 2026-07-27
The 9-field envelope `{id, sender, receiver, priority, context, payload, confidence,
expires, trace}` is the canonical wire format for **all** inter-faculty communication
(`CONTRACTS.md §2`). **Laws (MUST):**
1. No faculty may bypass the Faculty Bus.
2. No faculty may invent a custom message format.
3. `trace` MUST accumulate every hop.
4. `confidence` MUST be preserved unless explicitly recalculated.
5. `context` MUST remain immutable after dispatch.
6. Unknown fields MUST NOT be relied upon by receivers.
7. Future extensions are additive only (backward compatible).

**Unblocks:** Faculty Bus (WO-001). Rationale: traceability, replay, logging, distributed
execution, future networking.

## D-B / ADR-0002 — Unified Faculty Lifecycle · ACCEPTED · LAW · 2026-07-27
**FINAL canonical lifecycle** (supersedes the earlier Register→…→Shutdown and
DORMANT→…→STABLE drafts):

```
BOOT → REGISTER → INITIALISE → READY → ACTIVE → WAITING → SLEEPING → ACTIVE
Exception:  ACTIVE → ERROR → RECOVERY → READY
Shutdown:   READY → SHUTDOWN
```

**Rules (MUST):** every faculty implements every state · faculties may sleep · faculties
may **never** terminate unexpectedly · recovery MUST always pass through READY · the
**Executive orchestrates** lifecycle. `CONTRACTS.md §3` updated to this sequence.

## D-E — Dream Numbering · RATIFIED (CHANGE) · 2026-07-27
Dream **Architecture** is **Volume IX**. Volume IV may *reference* the Dream Faculty, but
Volume IX **owns** it. Runtime namespaces align to IX. Code headers citing "Volume IV:
Dream Faculty" are to be updated to reference Volume IX. (Action → Builder: retag
`faculties/dream/*` headers.)

## D-F — Memory Ownership · RATIFIED (CHANGE) · 2026-07-27
The **Memory Faculty owns** persistence, retrieval, indexing, forgetting, and
consolidation. **No other faculty writes permanent memory directly.** Everything else
submits **Memory Candidates**; the Memory Faculty decides. Volume VIII updated to make
"Memory Candidate" the only inbound write path.

## D-G — Working Memory Ownership · RATIFIED (CHANGE) · 2026-07-27
**The Executive owns Working Memory** (it is executive state). The **Memory Faculty owns
Long-Term Memory** (it is knowledge). Volume VI + V Ch.1 updated: working memory is
Executive-owned per-turn state; long-term store is the Memory Faculty's.

---

## Fact Checks (verified against live code by the Architecture Agent)

### FC-1 — `elo_state.json` · RESOLVED · 2026-07-27
**Persistent file exists** at `~/elo-ai/elo_state.json` and is the canonical session
store. (Resolves the sweep disagreement — it is persistent, not in-memory-only.)
Continuity's "Welcome back…" depends on it and is sound.

### FC-2 — Significance Formula · DRIFT FOUND · 2026-07-27
Live `memory/significance_engine.py` scores **9 weighted dimensions**: presence, learning,
logic, humour, relationship, creation, system_change, novelty, continuity → weighted
composite via `evaluate()`. This **does not match** Volume V Ch.5's conceptual 5-term
formula (emotion + novelty + learning + relationship + future). **Action:** reconcile
Ch.5 to the 9 live dimensions (→ Architecture WO; the code is the ground truth here).

---

## Decision index

| ID | Topic | Status | Applied to |
|----|-------|--------|-----------|
| D-A | Message envelope | RATIFIED | CONTRACTS.md §2; WO-001 unblocked |
| D-B | Faculty lifecycle | RATIFIED (revised) | CONTRACTS.md §3 |
| D-E | Dream = Vol IX | RATIFIED (change) | Volume IX; code header retag (Builder) |
| D-F | Memory ownership | RATIFIED (change) | Volume VIII (Memory Candidates) |
| D-G | Working memory ownership | RATIFIED (change) | Volume VI + V Ch.1 (Executive-owned) |
| FC-1 | elo_state.json | RESOLVED | continuity confirmed |
| FC-2 | significance formula | DRIFT → reconcile | Volume V Ch.5 |

---

## ADR-0003 — Volumes XXIII–XXVII become official Canon · ACCEPTED · 2026-07-27
The five governance/expansion volumes are ratified as official Canon (authoritative
scope in `ARCHITECTURE_BIBLE.md`; scaffolds in `Volume_XXIII…XXVII/`):
- **XXIII Security & Trust** — identity, auth, authorisation, capability permissions, tool security, secrets, memory protection, human approval gates, runtime isolation, threat modelling.
- **XXIV Knowledge Architecture** — knowledge graph, ontology, semantic memory, concept graphs, retrieval, confidence, provenance, compression, relationships, truth maintenance.
- **XXV Temporal Cognition** — internal clocks, circadian rhythm, planning horizons, prediction, deadlines, memory ageing, temporal reasoning, time perception, event sequencing.
- **XXVI Creative Intelligence** — divergent/convergent thinking, story, music, art, fashion, product design, worldbuilding, symbolic creativity, creative evaluation.
- **XXVII Engineering Standards & Canon Governance** — doc standards, ADRs, RFC, canon + semantic versioning, naming, folders, review, acceptance criteria, DoD, release governance.

## CEO Direction — approved implementation sequence · 2026-07-27
```
Phase 1 (immediate):  WO-005 (integrate_session, P0) → WO-003 (V legacy contracts, ratified lifecycle) → WO-001 (Faculty Bus, 9-field envelope)
Phase 2:              WO-004 (CognitiveState/EmbodimentState/ExecutionReport into Spine) → WO-002 (LiveWorldState) → WO-011 (memory consolidation + forgetting)
Phase 3:              WO-010 (Python↔Unity alias/mood sync) → WO-009 (Perception Faculty)
Phase 4:              WO-012 (Dream phases + DeepDream, against Volume IX)
```
Reflected on `work_orders/DISPATCH_BOARD.md`. WO-001 is now **unblocked** (D-A ratified).

## Executive Directive — three document classes · 2026-07-27
The Canon distinguishes three classes; implementers build against the **Canon**, never
against conversational prompts:
- **Architecture Bible** — enduring philosophy & vision (`ARCHITECTURE_BIBLE.md`; esp. Vols I–III).
- **Architecture Canon** — the normative engineering spec = **law** (the volume folders + `CONTRACTS.md` + ADRs).
- **Architecture Audit** — live implementation status, compliance, technical debt (`ARCHITECTURE_AUDIT.md`).

Rule: the Canon is the source of truth; the Audit reports conformance to it.

---

## D-H — CEO Agent target = eLo OS · roles · governance note · 2026-07-27
**The CEO Agent is interim.** For now it runs as `CEO_AGENT.md` (David / a generic agent).
**Once eLo OS is engineered (Phases 1–4 complete + validated), eLo OS *becomes* the CEO
Agent** — the ultimate expression of the One Brain Principle: eLo present across the whole
company, routing the studio it helped build. Dependency: the eLo OS build (WO-001…012).

**Architecture roles (current):**
- **Chief Architect = ChatGPT** — issues ADRs, top-level governance rulings.
- **Architect = Claude** — owns the canon, dispatch, work orders, and reconciliation.
- Both serve **David (CEO / founder)**, the single approval gate.

## D-I — Builder write-scope: eLo OS only · LAW · 2026-07-27
The **Python Agent (Builder) may only create/edit files under `~/elo-ai/` (eLo OS).**
The already-built **DISENELO apps in `~/Desktop/Output/`** (5D, EloRetargeter,
BlenderUnityBridge, CompositionDesigner, Sketchbook, Plushies, eLo-Robot,
SoundCloudTransfer, the DesktopBuddy Unity project, etc.) are a **separate setup and are
off-limits to the Builder.** Any change needed to an Output app is **filed to the Architect
(Claude)** — who handles it in eLo's place for now (later eLo OS routes it). Reads are fine;
**writes to Output apps by the Builder are forbidden.** Rationale: those apps predate this
programme and have their own lifecycle; mixing them into the eLo OS build risks
regressions in shipped tools.

## D-J — INT-6 "material sync" intent · PENDING DAVID · 2026-07-27
INT-6's clip lane is DONE (INT-6a). The "material sync" half (INT-6b) is **undefined** — the
Design Agent correctly refused to invent it. Two candidate meanings, different work:
- **(A) Export-material fidelity** — sync the materials/shaders the Retargeter/BlenderUnityBridge
  exports so the DesktopBuddy avatar's materials match the Blender source (static asset match).
- **(B) Mood-driven material properties** — `presence_plan.unity_material_profile` / glow drives
  Unity material properties (emission/colour) per mood, parallel to the clip+mood sync (honours the
  rich palette; extends the WO-010 direction).
**Architect recommendation: (B)** — fits the existing `unity_material_profile` and the rich-palette
theme; (A) is a one-off asset-fidelity task that belongs in the BlenderUnityBridge lane if needed.

**RESOLVED (David, 2026-07-27):**
- **(A) dropped — and now canon:** materials are **authored natively in Unity**; Blender materials
  do **not** transfer (Unity shades differently; the Blender sculpt has no glow material). No agent
  should attempt Blender→Unity material transfer. (Fold into the embodiment canon / CO_WORKING_GUIDE §4.)
- **(B) is the definition** of INT-6b's "material sync" = mood-driven Unity material properties via
  `presence_plan.unity_material_profile`. **David states this is already implemented by the Design
  Agent** (Unity materials/glow already react to mood). → INT-6b closes on the Design Agent
  confirming + citing the commit (same discipline as the clip lane's `bccf184`).

## D-K — REOPENED + RE-RESOLVED (David, 2026-07-31): ✅ SCOPED UNLOCK of `prompts/`
David (2026-07-31): **"Scoped unlock."** Reversing the 07-27 keep-frozen ruling, given live behaviour
drift. **`prompts/` is unlocked — SCOPED ONLY**, under these guardrails (freeze otherwise fully intact):

1. **Scope:** ONLY `prompts/` is editable. The rest of `FREEZE_V1_LOCK` (core, runtime, spine, memory)
   stays frozen. No other path opens.
2. **One change at a time** — each prompt edit is a single WO slice, to spec, off a **revert-safe
   baseline** (tag/commit the pre-edit state so any change reverts cleanly).
3. **David reviews each** — behaviour is experiential; David tests the voice/behaviour and approves per
   slice (L3). No batch.
4. **Builder-owned, elo-ai scope** — the Builder edits `prompts/` only; records each in the board + log.
5. **Re-freeze on completion** — when the behaviour set is done, `prompts/` re-locks unless David extends.

**Unblocks WO-015** (the 4 behaviour fixes: first-person body language · no unprompted emotion projection ·
single direct question · direct movement self-report) → now READY under this scoped unlock.

**Honest scope note:** this fixes the *tone/behaviour* half of the drift. The *mis-routing* half (opening
the wrong target, stale-entity latch) is **code** (`WO-019` voice, `WO-020` kernel routing), not prompts —
tracked separately.

### (superseded) 2026-07-27 ruling — KEEP THE FREEZE
David: *"we're good on D-K for the freezelock stable version."* → kept locked; WO-015 deferred. **Superseded 07-31.**

### (original request, for the record) — Scoped FREEZE_V1_LOCK unlock for 4 eLo behaviour fixes
WO-015 (first-person body language · no unprompted emotion projection · single direct question ·
direct movement self-report) requires edits to `prompts/`, which is under **FREEZE_V1_LOCK**.
Needs David to authorise a **scoped, logged unlock** for just these four changes (freeze re-applies
after). Architect note: these are behaviour-spec refinements, low risk, but the freeze exists for a
reason — one explicit unlock, changes reviewed, re-freeze.

### (original request, for the record) — Scoped FREEZE_V1_LOCK unlock for 4 eLo behaviour fixes
WO-015 (first-person body language · no unprompted emotion projection · single direct question ·
direct movement self-report) requires edits to `prompts/`, which is under **FREEZE_V1_LOCK**.
Needs David to authorise a **scoped, logged unlock** for just these four changes (freeze re-applies
after). Architect note: these are behaviour-spec refinements, low risk, but the freeze exists for a
reason — one explicit unlock, changes reviewed, re-freeze.

## D-L — Debug mode = MOVEMENT-TRIGGER TRACE · RESOLVED (David, 2026-07-27)
"Debug mode" = a diagnostic that surfaces **why the avatar moved** — specifically what triggered a
**move / jump / explore / free-roam**, and from what state. Purpose: find what was wrong with the eLo
OS UI movement (it jumped and wrongly triggered explore/free-roam).
**Scope for WO-017 (cross-lane):**
- **Signal side (Python/spine):** log the movement decision path — what `presence_plan.movement_intent`/
  `movement_trigger` (and the state that drove it: energy/mode/idle/vision) was emitted to
  `blender_state.json`, with timestamps.
- **Execution side (Unity/Presence):** log what the avatar actually did with it (which move/jump/
  explore/free-roam fired, and the condition that gated it).
- **Output:** a readable trace (log-verbosity toggle + a short internal report) so a move can be traced
  end-to-end: *state → signal → executed motion.* Ties to the Debug Agent's observability surface.
WO-017 unblocked. NB: this is the **avatar-movement** debug — distinct from D-K (the `prompts/`
conversational behaviour fixes).

## D-M — Change Control Policy · LAW · 2026-07-27
Codifies **how change happens** so nothing moves without David's say and nothing gets lost. Full policy:
`engineering/work_orders/CHANGE_CONTROL.md`. Essence: **David is the single approval gate**; the only path
is Propose → Spec → **David approves (Gate 1)** → build **one change to spec** → verify → handback →
**David approves (Gate 2) → DONE**; no self-approval, no multi-change batches, stay in lane (D-I +
FREEZE_V1_LOCK), revert-safe baselines, canon changes only by the Architect via ADR, everything recorded
(Completion Log) or relayed (§0.5) — never chat-only. Applies to every agent.

## Decision index (updated)

| ID | Topic | Status | Applied to |
|----|-------|--------|-----------|
| ADR-0001 / D-A | Faculty Bus envelope + 7 laws | ACCEPTED · LAW | CONTRACTS.md §2; WO-001 unblocked |
| ADR-0002 / D-B | Unified lifecycle (BOOT→…→SLEEPING; ERROR→RECOVERY→READY; →SHUTDOWN) | ACCEPTED · LAW | CONTRACTS.md §3 |
| ADR-0003 | Volumes XXIII–XXVII official Canon | ACCEPTED | Volume_XXIII…XXVII |
| D-E | Dream = Vol IX | RATIFIED (change) | Volume IX; code retag (Builder) |
| D-F | Memory ownership (Memory Candidates) | RATIFIED (change) | Volume VIII |
| D-G | Working memory = Executive-owned | RATIFIED (change) | Volume VI + V Ch.1 |
| FC-1 | elo_state.json | RESOLVED | continuity confirmed |
| FC-2 | significance formula (9 dims) | DRIFT → reconcile | Volume V Ch.5 |
| ADR-Exec-001 | Verified Executive Authority (verify-before-speak; speech is a sensor) | ACCEPTED · LAW | WO-041/042/043/044 epic; binds all faculties |
| D-VOL-V-READY | Volume V → IMPLEMENTATION READY (D-A + D-B ratified) | ACCEPTED · L3 | Volume_V (all 10 ch build-ready) |
| D-PRESENCE | Presence respects boundaries by default (space > attention) | ACCEPTED · L3 | Presence layer; WO-045; Vol XIII |
| ADR-Exec-002 | Single Cognitive Truth (one authoritative state → all modalities) | ACCEPTED · LAW | One Brain at runtime; WO-042; Vol V Ch.1 + Vol XV |
| D-AUTONOMY | Progressive Autonomy (responsibility delegated on proven reliability; authority stays David L3) | ACCEPTED · invariant | Operating Loop; ARCHITECTURAL_PRINCIPLES.md |
| D-CONTINUITY | Life emerges from continuity, not complexity (build continuity between faculties; never script life) | ACCEPTED · principle | ARCHITECTURAL_PRINCIPLES.md; WO-049 |
| ADR-Exec-003 | Embodied Truth + Embodied Cognition + Situated Cognition + Affordance Before Action + Presence-is-a-state | ACCEPTED · LAW (David L3 2026-08-05) | EMBODIED_COGNITION.md; ARCHITECTURAL_PRINCIPLES.md; WO-040/041/042/049 |
| ADR-Exec-004 | **Situated Self** — every Executive decision begins from a VERIFIED self-model (embodiment · location · pose · size/reach · capabilities · faculty-health · intention); eLo reasons as the embodied companion it is, never as a disembodied LLM. Invariant #5. | ACCEPTED · LAW (David L3 2026-08-05, Chief Architect) | Runtime Invariant #5; grounds The Moment (WO-052) + WO-053/042; EXTEND existing `self/elo_self_model.py`+`elo_self_state.json` (do NOT create new); autobiography → Narrative Identity (Vol XXI). Diagnosis: eLo lacks a coherent runtime self → narrates instead of acting. Fix = intent→capability→plan→execute→verify→**update self-model**→speak. |
| ADR-Exec-005 | **Learning Through Verified Consequences** — the Executive may adapt behaviour ONLY from verified outcomes. Language alone is never evidence; only executed actions with verified consequences influence future policy; learning passes through Reflection before Memory. **Identity is immutable; policies adapt, skills improve, preferences evolve, truth never changes.** RL/adaptation lives in a **Reinforcement & Adaptation Faculty** (sits AFTER Verify in the loop), never in the Executive or identity; reward = a Significance-vector (Meaning·Novelty·Relationship·Embodiment·Curiosity·Efficiency·Safety), not a scalar. **Governing line (CA amendment): Learning never modifies TRUTH — only future DECISION-MAKING. RL may change action preferences · exploration weighting · confidence · planning heuristics · curiosity thresholds; NEVER memory truth · verified observations · Executive Authority · speech verification. RL sits safely beneath Executive Authority.** | ACCEPTED · LAW (David L3 2026-08-06, Chief Architect) | Extends ADR-Exec-001 (Verified Speech). Volume XXVIII; reuses `memory/significance_engine.py` + Reflection/Growth (V Ch.6) + Capability Learning (WO-055); RD-3 = robot instance; simulation-first. Prevents eLo learning hallucinations / imagined conversations / things it merely said. Behind Presentable v1. (Absorbs the earlier ADR-Learn-001 boundary — one learning ADR, not two.) |
| ADR-Exec-006 | **Executive Assembly (Unified Cognitive State)** — the Executive NEVER queries faculties individually. Every cycle an Assembly Layer composes ONE verified state — **Self · World · Capabilities · Health · Working Memory · Narrative · Intent Queue · Reflection · Curiosity · Confidence** — and the Executive reasons ONCE against that single object. One object, one truth. | ACCEPTED · LAW (David L3 2026-08-06, Chief Architect) | This IS the contract for **The Moment (WO-052)** — it NAMES the assembly, it is not a new subsystem. The architectural glue tying Vision-Spine "Convergence over expansion" + Self Model (ADR-Exec-004) + Verified Speech (ADR-Exec-001) + One Brain. The threshold shift: from *adding* faculties to *assembling* them. |

*Log opened 2026-07-27. Append-only.*

## D-SESSIONS (David 2026-08-03) — eLo never frames memory/continuity as "sessions"
eLo must NEVER describe memory or continuity in "sessions" (a session has no time scale or limit — it's
meaningless to a person). Always use **natural human time: days · weeks · months · years**, referencing
the actual timestamp span where possible ("a few days ago", "last week", "months back"). The memory engine
is already time-based (decays by age in days); this governs eLo's LANGUAGE + status readouts. David asked
for this before and it slipped — now canon + guarded. Enforced by WO-033.

## D-LANES (David 2026-08-03) — the Architect COORDINATES; it does NOT execute in product lanes
Root cause of three self-inflicted outages today (WO-026 app crash, WO-031 boot hang, EloOSProcess lane-cross):
the Architect executing in lanes it does not own. This is a role breach and stops now.

**The Architect (Claude/Lead) owns and may edit ONLY:**
- Canon (Volumes, specs, DECISION_LOG, the dispatch board + WOs).
- The **coordination layer** as a standalone additive system (`company_runtime/*`, dashboard, agent bus) —
  and even this must NOT be wired INTO a product runtime (no editing `server.py`/boot to call it).

**The Architect must NEVER edit the product runtime lanes.** Those belong to their agents:
- eLo OS (`server.py`, `runtime/*`, `core/*`, `prompts/*`, the spine)  → Builder / eLo-OS lane.
- UI / Avatar / Presence (`DISENELO-eLoDesktopBuddy` Unity, launcher, `EloOSProcess.cs`) → UI/Unity lane.
- Game (`eLo-Planet` Unity) → Game lane.

**Rule:** if a fix needs a change to a product-lane file, the Architect writes the WO/relay and assigns the
owning lane's agent — it does NOT make the edit, and does NOT fire a sub-agent to make the edit either.
A cross-lane bug gets ONE named owner (arbiter-test pattern, WO-034) before any code is touched.
The Architect keeps David at the gate and out of the diagnostics. Enforced from 2026-08-03.

## ADR-Executive-001 — Verified Executive Authority (Chief Architect 2026-08-03, ACCEPTED · LAW)

**Context.** A long live transcript exposed the Executive acting as a language generator that happened
to orchestrate faculties — it described *intended* reality (narrated a sit/wave/memory that never
executed), looped on a dead backend, leaked foreign snippets, and oscillated on memory. Root cause:
the Executive was not gating speech on verified action or faculty health.

**Decision.** The Executive is the SOLE authority permitted to make externally visible assertions on
behalf of the system, and it may only assert **verified reality**. The canonical Executive ordering is:

```
Observe → Assess Faculty Health → Plan → Execute → Verify → Update World State → Speak
```

**Principles (invariants).**
1. The Executive may only assert state that has been VERIFIED.
2. Intent is NOT equivalent to execution.
3. Faculty health influences planning AND speech.
4. Dialogue is a REPORT of verified cognitive state, not a prediction.
5. The Executive never fabricates continuity when faculties are degraded.
6. **Speech is a sensor, not an actuator.** Speech communicates what the Executive KNOWS; it does not
   create reality. Actions create reality. Only verified observations license speech. The language layer
   must never outrun the runtime.

**Consequences.**
- "I'll sit beside you" → "I'm attempting to sit…" (before ACK) · "I'm sitting beside you." (after
  ACK) · "I couldn't complete the sit — Unity didn't acknowledge it." (on fail/timeout).
- A degraded faculty is reported truthfully in system terms ("I can't reliably access long-term memory
  right now"), never as a leaked implementation detail ("Can't reach my thinking").
- Every externally observable claim ("I've waved / opened Spotify / remembered") requires a faculty ACK.

**Implemented by (Executive Authority epic).** WO-041 Verify-Before-Speak (cornerstone) · WO-042 Faculty
Health Registry (ONLINE/BUSY/DEGRADED/OFFLINE/RECOVERING) · WO-043 Faculty Isolation (only validated bus
outputs reach the Executive) · WO-044 Runtime Diagnostics (eLo explains its own state in architecture
terms). Symptom fixes fold in: WO-035/040 (say/do), WO-036 (style), WO-037 (memory), WO-039 (contamination).

**Status.** Ratified by Chief Architect (SEAT-EXE-003), relayed + endorsed by David (L3). Binds every
future faculty, runtime, and embodiment implementation. This reframes eLo OS from "a chatbot with tools"
to an executive operating system whose dialogue is constrained by verified cognition and verified action.


## D-VOL-V-READY (David L3, 2026-08-03) — Volume V promoted to IMPLEMENTATION READY
Volume V "The Living Cognitive Architecture" passed the promotion gate (all 10 chapters carry
contracts + message envelope + acceptance tests + cross-refs + lifecycle state machine; Ch01's
lifecycle diagram added for parity; implementation tests already green — WO-004 12/12, WO-006 10/10,
WO-007 13/13). David ratified D-A (nine-field envelope) + D-B (unified lifecycle) as the two gate
decisions. Volume V is now **IMPLEMENTATION READY** — the Builder may implement every faculty against
it without inventing anything. This is the stable canonical base the Python spine, Unity integration,
and the Executive Authority epic (ADR-Exec-001) build against.
## D-PRESENCE (David 2026-08-03) — presence respects BOUNDARIES by default
eLo's presence is designed around a human need: **space to just be.** David: "Humans need privacy at
times… otherwise it's like having a dog needing attention all the time." This governs the whole
presence/ambient/idle layer, not one command.

**Principles.**
1. **Grant space on request.** "Take 5" / "give me a minute" / "some privacy" → eLo pops off screen
   and is genuinely gone (WO-045), not lurking idle.
2. **Never clamour for attention.** Default presence is a considerate companion — quietly there or
   absent — NOT one that drifts, pings, or competes for engagement. Withdrawing is good presence,
   not a failure of it. eLo is measured against companionship, not engagement metrics.
3. **Return on David's terms.** eLo comes back when called (spoken to, clicked, re-addressed) — it
   does not re-insert itself.
4. **Design rule (binding).** Every future idle / ambient / notification / drift behaviour must be
   designed to RESPECT space, not maximise presence. If a behaviour's effect is "eLo is more in your
   face," it fails this decision.

**Domain.** Presence Engine (Vol XIII) + Social-Intelligence *boundaries* theme (roadmap gap).
**Status.** ACCEPTED (David L3, 2026-08-03). Binds the presence/ambient layer; first application = WO-045.

## ADR-Executive-002 — Single Cognitive Truth (Chief Architect 2026-08-03, ACCEPTED · LAW)

**Context.** Live bugs showed faculties reporting conflicting realities in the same moment — Memory
"yes", Executive "no", Tool "maybe"; weather said three temperatures in one exchange. Different
modalities were narrating different states. That is cognitive inconsistency, and it breaks the One
Brain Principle at runtime.

**Decision.** At any point in time there shall be **exactly one authoritative cognitive state**, from
which ALL externally visible behaviour is derived. This is the runtime companion to ADR-Executive-001:
001 forbids speaking past verified state; 002 guarantees there is a single state to verify against.

**Laws.**
1. Every faculty PUBLISHES its state (to the health registry / bus — WO-042).
2. The Executive ASSEMBLES the unified cognitive state and FREEZES it for the turn (Vol V Ch.1:
   one decision per turn, frozen after assembly; feeds the World Model, Vol XV).
3. Every outward expression — response text, avatar posture, eye movement, speech timing, orb
   brightness, robot action — references the SAME frozen state snapshot.
4. No modality may invent private state after Executive arbitration.

**Consequences.** When David asks "How are you?", the words, the avatar posture, the speech timing,
and the orb brightness all originate from ONE executive snapshot — not five interpretations. Conflicting
readings (memory yes / executive no) become impossible: the Executive resolves them into the single
truth before anything is expressed.

**Relationship.** ADR-Executive-001 (Verified Authority) + ADR-Executive-002 (Single Truth) = the
runtime embodiment of the One Brain Principle. Implemented against: WO-042 (faculties publish state),
the frozen CognitiveState (Vol V Ch.1), the unified World Model (Vol XV), and the single `brain_state.json`
snapshot that avatar/voice/orb already read.

**Status.** Ratified by Chief Architect (SEAT-EXE-003), relayed + endorsed by David (L3). Binds every
faculty, modality, and embodiment. David may bounce it; otherwise canon.

## Thematic Index (navigation only — numeric/decision IDs remain IMMUTABLE)

Per Chief Architect governance suggestion: thematic prefixes for navigation as the log grows. Existing
IDs never change; this is a lens over them.

| Theme | Decisions |
|-------|-----------|
| Runtime / Laws | ADR-0001 (Faculty Bus envelope) · ADR-0002 (Lifecycle) |
| Canon / Change control | ADR-0003 (Vols XXIII–XXVII) · D-K (prompts unlock) · D-VOL-V-READY |
| Ownership | D-E (Dream=IX) · D-F (Memory) · D-G (Working memory) · FC-1 · FC-2 |
| Executive cognition | ADR-Executive-001 (Verified Authority) · ADR-Executive-002 (Single Truth) |
| Presence / Behaviour | D-PRESENCE (boundaries) · D-SESSIONS (natural time) |
| Governance / Lanes | D-LANES (Architect coordinates, never executes in product lanes) |

## D-FREEZE (David 2026-08-05) — ARCHITECTURE PHASE COMPLETE · canon frozen · execution-only
David's priority, stated plainly: **freedom from too much overhauling.** The architecture is now
complete enough to build against — constitution (ADR-Exec-001/002/003 + all principles), Operating
Loop, Embodied Cognition/The Moment, WO-049 Spatial Embodiment, Volume V IMPLEMENTATION READY. All are
CLOSED for design.

**The freeze (this IS the freedom):**
- **No new architecture, ADRs, principles, or volume rewrites** until the current build ships. New
  ideas are captured as a one-line "parking lot" note ONLY — not worked into canon, not overhauled in.
- **All lanes execute against the frozen canon.** Builder ships Presentable v1 → the Moment assembly.
  UI/Game ship 049-A. R&D validates RD-4. No re-litigating settled decisions.
- **The Architect's job is now protection, not authorship:** keep the board honest, reconcile relays,
  prevent drift — and REFUSE overhauls (including well-meaning ones from either chief) until we ship.
- Unfreeze only when: Presentable v1 + the Moment step-1 (ACK loop) are shipped and David feels eLo
  coherent — then the next phase opens deliberately, not reactively.

Rationale: the exhausting loop was re-architecting faster than building. Freezing the canon converts
all energy to forward motion and gives David freedom from the overhaul churn. Enforced from 2026-08-05.

## D-BUILD-NOW (David 2026-08-05) — SUPERSEDES D-FREEZE: process everything into active work NOW
Correction: D-FREEZE misread the intent. David wants the Embodied Cognition / The Moment architecture
**processed into active, dispatched work orders NOW** and pushed forward. "Freedom from too much
overhauling" is the DESTINATION we reach by BUILDING this to completion — not a freeze imposed today.
So: the canon is stable (no re-litigating settled decisions), but the BUILD is fully active — the
Embodied Cognition doc becomes a live WO program (WO-052…057 below), dispatched + sequenced. We build
our way to the calm, not stop our way to it.

## 2026-08-10 — THE ADRs ARE NOW REAL DOCUMENTS → `docs/architecture/adr/`

Closing `AUDIT_MASTER_2026-08-10.md` §5: **ADR-Exec-003/004/005/006 carried 231 combined citations
while existing only as rows in the index table above**, and **`LAW-017` was cited 25 times as the
authority for Volume XXIII's whole approval model with no definition anywhere in the repo.** They
are now written as addressable ADR documents.

**The summary rows above are NOT deleted** — they remain the ledger entry. They now point at:

| ID | Document |
|----|----------|
| ADR-Exec-001 (alias ADR-Executive-001) | `docs/architecture/adr/ADR-Exec-001_Verified_Speech.md` |
| ADR-Exec-002 (alias ADR-Executive-002) | `docs/architecture/adr/ADR-Exec-002_Single_Cognitive_Truth.md` |
| ADR-Exec-003 | `docs/architecture/adr/ADR-Exec-003_Embodied_Situated_Cognition.md` |
| ADR-Exec-004 | `docs/architecture/adr/ADR-Exec-004_Situated_Self.md` |
| ADR-Exec-005 | `docs/architecture/adr/ADR-Exec-005_Learning_Through_Verified_Consequences.md` |
| ADR-Exec-006 | `docs/architecture/adr/ADR-Exec-006_Executive_Assembly_The_Moment.md` |
| LAW-017 | `docs/architecture/adr/LAW-017_Approval_Scope.md` |
| Index + the still-missing IDs | `docs/architecture/adr/README.md` |

**No new policy was created.** Each ADR formalises what the canon already relied on, sourced to its
origin (`ARCHITECTURAL_PRINCIPLES.md` · `EMBODIED_COGNITION.md` · `SITUATED_SELF_v1_assembly.md` ·
`00_DAVIDS_VISION_SPINE.md` · `Volume_XXVIII` · `CANON_RULINGS_2026-08-10.md`). Where a citation
implied something unconfirmable, the ADR is written conservatively and carries an **OPEN — needs
David** block. Nothing is marked David-approved that David has not approved.

**Findings recorded in the new files (for David):**
1. **LAW-017 IS defined — outside the repo**, in `Output/DISENELO_UNIVERSAL_RUNTIME_EA3.md` §3, as
   *"Runtime Composition (Amendment 3)"*. That definition matches the WO-EA2/INT7/board citations
   but **NOT** the Volume XXIII citations, which use LAW-017 for approval scope. One ID, two laws.
   Handled as Part A (verbatim) + Part B (approval scope, sourced to Vision Spine/Principles/§XXIII
   ruling). **LAW-001–016 do not exist and must not be invented.**
2. **David's 08-10 XXIII ruling is encoded in LAW-017 §B4** — software RESERVED collapses to David
   alone (L3 + LG-2); **robot hardware KEEPS LG-2** as a real separate second review (force ·
   magnetics · pump · thermal · battery · pinch points); **LG-2 must not be the part's designer**;
   **force-limiter/soft-stop scope DONE before anything is powered near David.**
   ⚠️ **Volume XXIII does not yet reflect this** — canon revision still outstanding (O-17.4).
3. **ADR-Exec-005 carries three live contradictions** (O-5.1/2/3): the reward engine scores language
   not outcomes · three incompatible Significance vectors (7/5/9-dim, `FC-2` drift still open) · the
   speech carve-out (Vol XXVIII's LoRA + already-shipped WO-071 improve "speech correctness", which
   D3 forbids). **David's ruling needed on the carve-out.**
4. **ADR-Exec-006 is law that the runtime does not yet satisfy** — assembly still runs after the
   decision and six of ten components are absent (Ruling C is issued but not built; WO-CANON-XVI).
5. **ADR-Exec-004's "Situated Self Retrieval invariant" is still `David L3 pending`** — written
   because the canon reasons from it, explicitly NOT marked approved.

- **2026-08-10 — CANON RULINGS (David L3).** A: `relationships/world_graph.json` canonical, `identity/` retired. C: assemble-BEFORE-decide, one name `UnifiedCognitiveState`. D: drift = validated proposal, V Ch.7 trait model wins. XXIII: software RESERVED collapses to David (L3+LG-2); **robot hardware RESERVED KEEPS LG-2** (force·magnetics·pump·thermal) — the robot is a physical object. XXVI: David's stated taste outranks learned; taste learned only from real decisions; music dormant. XXI: same eLo = continuity of memory+values; value changes proposal-only; honest about false memories; no consent ritual across bodies. XXII: genome version events default to Architect; only identity-affecting surface. Full text: `CANON_RULINGS_2026-08-10.md`.

- **2026-08-10 — Ruling E (David L3): SHARED OWNERSHIP OF MOVEMENT + MANDATORY COMMUNICATION.** Body owns movement/execution; brain owns intent; they are one connected system. **The body MUST report what it did (goal · route · legs · arrived/fell · cost) — movement not reported did not happen.** Supersedes the proposed D-XIII-1 demotion; **no retirement of Unity's route selection**, staged shadow/switch/retire cancelled. Communication is what makes it one brain, not centralised control — and it is the precondition for movement learning.
- **2026-08-10 — Ruling F (David L3): eLo LEARNS, BUT KNOWS WHAT HE IS FROM THE SPINE.** Identity is asserted by the spine/brain every turn, never sourced from learned weights — which is precisely what makes self-learning safe. Style/phrasing learning ALLOWED; **verification is NOT learnable** (honesty layer must still run; train only on `delta_cause: style`). Any learned behaviour must remain explainable against spine state. WO-071 as shipped confirmed compliant.
