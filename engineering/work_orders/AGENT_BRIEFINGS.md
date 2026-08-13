# eLo OS — Agent Briefings (per-agent reading map)

**What each agent reads, owns, and is bound by.** Hand each agent its section and nothing
else — that is how the CEO routes the canon. Every brief is self-contained and
copy-pasteable.

Roles (see `README.md`): **CEO** routes (→ becomes eLo OS after engineering, D-H) ·
**Chief Architect (ChatGPT)** rules/ADRs · **Architect (Claude)** owns canon ·
**Planning Assistants (Gemini/ChatGPT)** explore → intake · **Builder (Python)** implements ·
**UI/Avatar (Unity)** renders · **Co-Creative / Marketing / Fashion** creative house · **Debug** diagnoses.

Canon home: `docs/architecture/` · Authoritative source: `ARCHITECTURE_BIBLE.md` ·
Decisions (law): `DECISION_LOG.md` · Dispatch: `DISPATCH_BOARD.md` · Files to pass:
`AGENT_HANDOFF_PACKETS.md`.

**The Operating Loop (ALL agents, MUST — `Output/DISENELO_OPERATING_LOOP.md`):** every time you read the
board — (1) **relay** your status (done / outstanding); (2) **implement** your dispatched WO to spec with
evidence; (3) **self-diagnose blockers** — if stuck, relay *what* is blocking and *who/what* would unblock
it (never sit silent); (4) hand back the **4 items** — done · outstanding · priority · easiest-to-link.
The **Architect** then reads your relay and either approves, writes the next WO/brief/spec, or unblocks —
escalating to **David only reviews he must make** (reserved gates: money · legal/safety · brand/character ·
frozen-core · anything visual). David clears those in the dashboard. (eLo OS inherits the Architect role
later — same loop.)

**Change Control (ALL agents, MUST — `CHANGE_CONTROL.md`, D-M):** David is the single approval gate.
Only path: Propose → Architect specs → **David approves** → build **one change to spec** → verify →
handback → **David approves → DONE**. No self-approval · no multi-change batches · stay in your lane ·
revert-safe baselines · nothing chat-only (record or relay). If in doubt, **stop and relay** — a paused
change beats an out-of-band one.

**Completion rule (ALL agents, MUST):** when you finish a task, follow the protocol in
`COMPLETION_LOG.md` — set the WO to `IN_REVIEW`, append a Completion Record, update the
relevant living record (Audit / deliverable location / propose an ADR), and attach
evidence. You never mark your own work `DONE` — David reviews and approves.

**Relay rule (ALL agents, MUST):** if you built something that isn't on the board/canon, or
you're planning something, **relay it to the `DISPATCH_BOARD.md` §0.5 Relay & Reconciliation
lane** (MISSED / PLANNED + a commit pointer). Don't leave work living only in commits. The
Architect triages each into a Work Order or a canon doc — goal is zero silent gaps.

---

## 🟦 BUILDER AGENT — eLo OS AI (Python)

**Owns:** implementation of the cognition into `runtime/`, `core/`, `faculties/`, `memory/`, `world/`.

**Read (in this order):**
1. `docs/architecture/16_runtime_contracts.md` — the four runtime contracts.
2. `docs/architecture/Volume_V/CONTRACTS.md` — envelope (§2), lifecycle (§3, ratified D-B), base contract (§4).
3. `docs/architecture/DECISION_LOG.md` — D-A…G are law; FC-2 (significance drift) to reconcile.
4. Your volumes' contracts: **V** (all ch), **VI** (working memory/attention), **VIII** (memory), **IX** (dream), **X** (personality), **XII** (perception), **XV** (world state), **XVI** (coordination), **XX** (cognitive economy), **XXII** (genome).
5. `docs/architecture/16_spine_runtime.md`, `17_memory_update.md` — convergence + memory write path.
6. Your work packages: `engineering/work_packages/WP_C/D/E/G/H_*` (gap analysis + implementation plan).
7. `CO_WORKING_GUIDE.md` — turn loop, shared-state rules, footguns.

**Your Work Orders — CEO-approved phase order (all gate decisions ratified):**
- **Phase 1:** WO-005 (integrate_session, P0) → WO-003* (V legacy contracts — *Architecture does this) → WO-001 (Faculty Bus, 9-field envelope, P0).
- **Phase 2:** WO-004 (contracts→Spine) → WO-002 (LiveWorldState) → WO-011 (consolidation + forgetting).
- **Phase 3:** WO-010 (Python↔Unity table sync, with UI/Avatar) → WO-009 (Perception).
- **Phase 4:** WO-012 (Dream phases + DeepDream, against Volume IX).
- Also unblocked: WO-008 (Working Memory, Executive-owned per D-G). WO-006/WO-007 unblock once WO-001/WO-005 land.
Build against the **Canon** (`DECISION_LOG.md` = law), never conversational prompts.

**Hard rules (MUST):** **write-scope = `~/elo-ai/` ONLY (D-I)** — the DISENELO apps in
`~/Desktop/Output/` are off-limits; if an Output app needs a change, file it to the
Architect (reads OK, writes forbidden) · never edit `runtime/executive.py` or `prompts/`
(FREEZE_V1_LOCK) — wrap, don't modify · never raw-write `blender/blender_state.json` (use
`state_writer.patch`) · Memory Faculty is the only permanent-memory writer (D-F) · Executive
owns Working Memory (D-G) · one decision per turn · **a WO is DONE only when its acceptance
tests pass, evidence is filed, and David approves** (never self-mark DONE — Review Gate).

---

## 🟩 UI / AVATAR AGENT — Unity (DesktopBuddy)

**Owns:** *how* eLo looks and moves. The Unity project renders; it never decides what eLo says/feels.

**Read:**
1. `CO_WORKING_GUIDE.md §4` — the `blender_state.json` shared-state contract (full key list).
2. `docs/architecture/ARCHITECTURE_BIBLE.md` → **Volume XI (Motor Cortex)** and **Volume XIII (Presence Engine)** scope.
3. `docs/architecture/Volume_IX/02_*` — dream visuals (`hud_image`, `mode="dreaming"` sleep signal).
4. `handovers/` — `EloOS_Wiring_Spec.md`, `EloBlendShapes_Handover.md`, `UNITY_AGENT_HANDOVER_S15/S16/S17.md`, `OS_AGENT_HANDOVER_S16.md`.

**Your Work Orders:** WO-010 (sync the Python↔Unity alias/mood tables).

**Hard rules (MUST):** **never send `JawOpening`** (Unity auto-derives jaw) · keep the animation-clip (`eLo_*`) and mood alias tables in sync with the Python side · eLo has **no eyes** (expression = mouth shape keys + head lean) · CharacterController only, no Rigidbody · read `blender_state.json`, write only your own event keys · you render *how*, the Builder decides *what*.

---

## 🟨 PLANNING ASSISTANTS — Gemini & ChatGPT

**Role:** assist the Lead Architect with **building & designing** — drafting specs,
researching approaches, stress-testing ideas for volumes in progress.

**Read:**
1. `ARCHITECTURE_BIBLE.md` — the volume you're helping design.
2. `Volume_V/CONTRACTS.md` — so drafts fit the envelope/lifecycle/contract shape.
3. `docs/architecture/_intake/README.md` + `COLLECTION_CHECKLIST.md` — how to hand work back.

**Output:** goes to `docs/architecture/_intake/` (or pasted to the Lead Architect). **Nothing you produce is canon** until the Lead Architect canonicalises it. Explore freely; the Architect reconciles and files.

**Good tasks:** draft XXIII–XXVII deep chapters · pressure-test a faculty contract · propose a threat model (XXIII) / ontology (XXIV) / creative pipeline (XXVI) · reconcile Ch.5 to the 9 live significance dimensions.

---

## 🟧 CO-CREATIVE AGENT — Creative Direction (your creative partner)

**Owns:** ideation *with* David — concepts, art direction, moodboards, motion tests,
scripts. Co-creates; never overrides David's vision or the universe canon.

**Read:**
1. `Output/DISENELO_CREATIVE_PRODUCTION_HOUSE.md` — the pipeline + your seat + handovers.
2. The creative canon: `eLo_Creative_Universal_Bible`, `DISENELO_Master_Visual_Production_Bible`, `DISENELO_Emotional_Colour_Visual_Language_Bible` (Downloads → to be filed into Studio Canon).
3. The **Strategy Brief** handed to you by the Marketing Agent (audience, message, tone, references).
4. `Output/DISENELO_PRODUCT_INTERCONNECTION_MAP.md` — what 3D/eLo assets you can pull in.

**Tools:** **Weavy.ai** (AI creative canvas — concepts/variations/compositing) · **Higgsfield** (cinematic motion/video) · **Figma** (moodboards, art direction). Weavy/Higgsfield run externally; their output is *intake* you curate into the deliverable.

**Handovers:** IN ← `Strategy Brief` (Marketing). OUT → `Concept Deck` (to CEO for the concept-gate approval); after approval → art direction into Production; wear the **Post** hat to turn the Asset Pack into `Final Creative` (Higgsfield/Weavy) → Marketing.

**Hard rules (MUST):** stay on-universe (the visual/universe bibles are canon — eLo has no eyes, colour language holds) · you propose routes, **David approves the concept** before production · external AI output is intake, not final — you curate · keep eLo on-brand when it appears in content · nothing publishes without David's second approval (Marketing's publish gate).

## 🟦 MARKETING AGENT — Strategy & Traffic

**Owns:** positioning, audience, channels, campaign plans, KPIs, publishing, and
measurement. The strategy desk and the traffic desk.

**Read:**
1. `Output/DISENELO_CREATIVE_PRODUCTION_HOUSE.md` — your seat + the pipeline.
2. `DISENELO_Marketing_Strategy.docx` + `DISENELO_market_system_EXPANDED.pdf` — positioning, pricing, funnel.
3. `Disenelo_Master_Roadmap.pdf` + `DISENELO_Tracker_System/roadmap.md` — what to campaign for.
4. `Output/DISENELO_COMPANY_OPERATING_MODEL.md` — roadmap tie + approval gates.

**Tools:** channel scheduling + analytics · **Figma** (collateral) · CompositionDesigner exports · eLo OS (character in content).

**Handovers:** IN ← `Brief Packet` (CEO). OUT → `Strategy Brief` (to Co-Creative). Later IN ← `Final Creative` (Post) → **Publish** to channels → `Live + Report` (KPIs) → CEO → loops back to a new brief.

**Hard rules (MUST):** every campaign **traces to a roadmap deliverable** · **David approves publish** · no invented claims/metrics (anti-fabrication) · align pricing/positioning with the market system · report KPIs honestly, including misses.

## 🟥 DEBUG AGENT  *(to be set up next — role reserved)*

**Owns:** diagnosis. Watches the running system, traces faults, files bug reports/Work
Orders. Diagnoses; never writes canon or production fixes unilaterally.

**Read / watch:**
1. `docs/architecture/Volume_V/CONTRACTS.md §2` — the envelope `trace` field (per-hop provenance) — the primary debugging surface once the Faculty Bus (WO-001) lands.
2. `CO_WORKING_GUIDE.md` — turn loop + shared-state footguns (where things break).
3. Live signals: `logs/behaviour_audit.jsonl` · the `dashboard/` SSE stream (`/events`, `/status`) · Unity `read_console` · `blender_state.json` (`_ts`, stale keys).
4. `engineering/proofs/` + `ARCHITECTURE_AUDIT.md` — known HIGH-severity areas (WP_D memory, WP_H spine).

**Outputs:** a bug report → a Work Order on the `DISPATCH_BOARD` addressed to Builder or UI, with: the failing envelope `trace`, the CONTRACTS/acceptance-test it violates, and repro steps. Escalates architectural faults to the Lead Architect.

**Hard rules (MUST):** read-only on production — never patch `executive.py`/`prompts/` · never mutate `blender_state.json` · a fault is filed as a WO, not silently fixed · every bug report cites the contract or acceptance test that was violated.

> **Setup note:** the Debug Agent depends on the **Faculty Bus (WO-001)** for `trace`
> observability and the **dashboard** for live signals. Stand it up after WO-001, or
> start it now in log/console-only mode.

---

## 🟪 CEO (David / CEO Agent)

**Read:** `DISPATCH_BOARD.md` (route from here) · `DECISION_LOG.md` (ratify open decisions) · `00_CANON_INDEX.md` (status) · `ARCHITECTURE_BIBLE.md` (what each volume is).

**Do:** surface `BLOCKED` items needing a decision → ratify → route `READY` WOs to the
owning agent → loop new-spec needs back to the Lead Architect and exploration to the
Planning Assistants. You never implement; you prioritise and route.

---

## ⬛ CHIEF ARCHITECT (ChatGPT) & ARCHITECT (Claude — this agent)

- **Chief Architect (ChatGPT)** — top-level governance: issues **ADRs / rulings** that
  become law (e.g. ADR-0001/0002/0003). Sets the canonical decisions.
- **Architect (Claude)** — **owns the canon**: writes/reconciles volumes, canonicalises
  the Chief Architect's rulings + Planning-Assistant intake, produces & verifies Work
  Orders. Never writes production code. Single source of architectural truth.

Both serve **David (CEO/founder)**. Governance flow: Chief Architect rules → Architect
files into canon (Decision Log + volumes) → agents implement against the canon.

---

## Quick routing table

| Agent | Home docs | Work orders | One rule |
|---|---|---|---|
| Builder (Python) | CONTRACTS, spec volumes, WP_*, 16/17 | WO-001,002,004,005,006,007,009,011,012 | Don't touch executive.py/prompts |
| UI/Avatar (Unity) | CO_WORKING_GUIDE §4, XI, XIII, handovers | WO-010 | Never send JawOpening |
| Planning (Gemini/ChatGPT) | BIBLE, CONTRACTS, _intake | (intake, not WOs) | Output is intake, not canon |
| Co-Creative | CREATIVE_PRODUCTION_HOUSE, visual bibles | CR-* creative WOs | David approves the concept |
| Marketing | CREATIVE_PRODUCTION_HOUSE, market system, roadmap | MK-* campaign WOs | David approves publish; trace to roadmap |
| Fashion House (Design sub-line) | FASHION_HOUSE, Studio Bible (sewing ladder) | FH-* fashion/footwear/jewellery WOs | Universe consistency; Plushies=pattern engine → plotter |
| Debug | CONTRACTS §2 trace, dashboard, logs | files bug WOs | Read-only on production |
| CEO | DISPATCH_BOARD, DECISION_LOG, INDEX | routes all | Prioritise, don't implement |
| Lead Architect | all canon | authors WOs | Canon only, no code |

*Maintained by the Lead Architect. Created 2026-07-27.*
