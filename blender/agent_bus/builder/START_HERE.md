# BUILDER — START HERE

---

## 🔴🔴 WAVE 1 EXECUTION — DAVID L3 DIRECTIVE 2026-08-24 — SUPERSEDES PHASE ORDER BELOW

**Authority:** David L3 Execution Directive 2026-08-24 · `docs/architecture/EXECUTION_QUEUE_2026-08-24.md`

These are AUTHORISED and dependency-free. Execute before the Phase 1–4 order below. No further Board review required.

### 🔴 IMMEDIATE — do first

| WO | What it is | Size |
|---|---|---|
| **`WO-NAV-001`** | Add `"movement_report"` to `_ACK_BODY_TYPES` in `server.py` (SP-1) + fix `_PENDING_MOVE` matcher → read `payload["report"]["arrived"]` (SP-2) + `MovementOutcome` typed struct (SP-22) | SP-1+SP-2 = two lines. SP-22 = new dataclass. |

🔴 **SP-1+SP-2 are the single most important items in the programme.** Until they land, every consequence consumer produces false `[MOVE_FAILED]` on every successful navigation turn — ACK break on the whole movement chain.

### 🟠 HIGH — after WO-NAV-001 (parallel, all dependency-safe)

| WO | What it is |
|---|---|
| **`WO-NAV-003`** | Wire `GazeState.win_id` → `world_dict` (SP-6) + navigation intent category in `intent_engine.py` (SP-16) + referent resolver (SP-17) |
| **`WO-NAV-004`** | Read `surface_graph` from `elo_spatial.json` (SP-7) + Y-flip conversion Unity→Python (SP-10) + replace `max_jump_d=75` → `capability_set.jump_px` (SP-8) |
| **`WO-NAV-005`** | `embodiment_scope: frozenset` on `Capability` (SP-35) + `current_embodiment` in `world_dict` (SP-37) + filter `_capability_faculty()` by `embodiment_scope` (SP-36) |
| **`WO-NAV-006`** | `PreviousWorldSummary` per turn (SP-27) + `compute_delta()` schema (SP-28) + `significance_faculty.py` structure (SP-29 schema) + `trigger_source` annotation (SP-30) |
| **`WO-NAV-007`** | `spatial_plan` field in `CognitivePlan` (SP-15) + `goal_win_id` in `move_command` schema (SP-19) |
| **`Unity-WO-B1`** | Unity: emit `body_win_id` in movement_report — Unity seat only |

### 🟠 HIGH — WO-NAV-001 verified · NOW RELEASED (Board signal 2026-08-24)

WO-NAV-001 is DONE (commit `b70916a`, 11/11 PASS). Board has issued WO-NAV-002 and WO-NAV-008. Execute now — both are dependency-safe and can run in parallel.

| WO | What it is |
|---|---|
| **`WO-NAV-002`** | Enrich autobiography entry with full MovementOutcome payload (SP-3) + wire MovementOutcome → ExecutionReport movement fields (SP-23) |
| **`WO-NAV-008`** | Call `route_memory.remember_route()` from movement ACK handler with `ack_id` (SP-4) |

Both WOs build on `MovementOutcome` (SP-22, `runtime/movement_outcome.py`) from WO-NAV-001. Coordinate on `_mout` availability — WO-NAV-002 D-1 constructs it; WO-NAV-008 D-1 uses it in the same block.

---

## 🔴 BUILD DIRECTIVE — ARCHITECTURAL FREEZE (David + CA, 2026-08-22)
**Authority:** `_intake/SOURCE_2026-08-22_CA_recovery_delivery_plan.md`

**Implement the listed Work Orders exactly against the existing canonical contracts.**

Do NOT create:
- new architecture
- new faculties
- new gates
- new review processes
- new audit documents
- new schemas
- replacement designs

Unless an existing contract is technically impossible to implement.

**For every implementation defect:** fix it within the WO's scope → run the stated acceptance tests → report changed files and result → move to the next WO. Do not respond by proposing another audit. Do not reinterpret the architecture. Do not expand scope.

The objective is **implementation**, not further architectural discovery.

### Delivery queue — CA-confirmed order (2026-08-22):

```
RS-GRND-01
     ✅ COMPLETE — 16/16 — DO NOT REBUILD
          │
          ▼
WO-RS-002 ── REVIEW_STATE enforcement         ← BUILD NOW
WO-004    ── Repair test harness              ← BUILD NOW (parallel)
          │
WO-RS-003 ── Identity conflict boundary
WO-RS-004 ── Review contamination
          │
WO-005    ── Integrate GRND-01 into real spine
          │
WO-WKG-001 ── WKG core / read path
WO-WKG-002 ── WKG write / verify
WO-WKG-003 ── WKG write path (separate from verify)
          │
WO-SPG-001 ── 🔴 CANCELLED — SPG NOT ONBOARDED (David L3, 2026-08-22)
WO-SPG-002 ── 🔴 CANCELLED — SPG NOT ONBOARDED
          │
WO-SPINE-001 ── integrate_session()
WO-SPINE-002 ── State envelope (CognitiveState / EmbodimentState / ExecutionReport)
WO-SPINE-003 ── UnifiedLiveWorldState
          │
WO-LCI-001 ── verified-outcome reward (Learning P0-A)
          │
WO-CONV-001 ── One Brain integration test (last — verify, don't redesign)
```

**WO-RS-001 is CLOSED — RS-GRND-01 already passed 16/16. Do not rebuild it.**

All cards are in `QUEUE/`. Source contracts are in `docs/architecture/cards/`.

**SPG — read the contract first, always:**
The canonical SPG contract on disk is the authority. CA's shorthand ("SPG = what matters") was architectural framing, not a new definition. Before implementing WO-SPG-001 or WO-SPG-002: read the existing SPG contract. If it is consistent with the WO — implement. If it contradicts the WO — STOP and report the exact contradiction. Do not invent SPG from CA framing.

**Authority chain:** canonical SPG contract on disk → existing architectural meaning → Builder implementation. Not: CA interpretation → Builder invents SPG.

---

**David, 2026-08-21:** *"I want this done so I can audit correctly or it's pointless."*
*"Only thing that won't be done is the social design as that needs a better setup. But the rest should
be able to follow."*

🔴 **ALL 12 CARDS RUN. Nothing is held. Nothing waits on David.**
He has ruled everything in this queue. If you find yourself wanting a decision — **grep the spec first**
(`Output/` · `docs/architecture/` · `_intake/` · `docs/architecture/adr/`). It is almost certainly already
answered, and asking him twice is the most expensive thing we do to him.

---

## Definition of Done — all four, every card. No exceptions.

| | |
|---|---|
| **built** | the code exists |
| **wired** | something real calls it — name the caller |
| **exercised** | it ran on a real turn / asset / board state |
| **falsifiable** | a test goes **RED** when the wire is cut |

🔴 **`written` · `spec'd` · `scaffolded` · `partial` · `built-unmarked` are NOT progress.**
Report **finished things and blockers.** Nothing in between. If it isn't done, say **BLOCKED** and why.

---

## ORDER — top to bottom. Do not reorder.

### Phase 1 · Presentable v1 — the only thing that changes what David can show someone

| card | |
|---|---|
| **`0082`** | 🔴 **P0. LOOP-7 live.** The Learning Faculty is built and wired (`faculties/learning/faculty.py` → `spine.py:253` → `executive.py:314`). **It has not run on a real turn through the server.** That single verification is **Presentable v1 acceptance test 3** — *"it feels alive because eLo UNDERSTOOD AND ACTED."* Two of three tests pass; this is the third. ⚠️ A spot-check with a hand-made lesson returned no advice — the `ADR-Exec-005 D1` evidence gate rejected its shape. **Determine whether that is the gate working or a shape mismatch. Do not loosen the gate to make it pass.** |
| **`0083`** | WO-117 SELF-INTERPRET — released tonight; deps 21·23·24 verified wired and exercised. |

### Phase 2 · Canon — completes layer B, which the audit needs whole

**These add material. They erase no evidence. Run them freely.**

`0076` remaining canon in order · `0077` Volume XVIII · `0078` XXVI + XXVIII ·
`0081` Volume XI §A/§D (**David L3 ruled — go**) · `0080` L3 queue triage · `0079` the `0060` routing table
+ three orphan rows · `0069` OpenAI 429 permanent latch

### Phase 3 · Runtime, additive

| card | |
|---|---|
| **`0059`** | Router half already built by the Architect (154 insertions) — **verify it, don't rebuild it.** The real remaining work: `prompt_eval` re-reads **~7,200 tokens every turn** despite a correct prefix layout. **The cache is missing. Fix the cache — never the prompt.** |

### Phase 4 · The two that ARE the findings — 🔴 read the box below first

`0060` GROUND jam (§C/§D done; §A/§B from `0079`) · `0068` MoodPalette — add the 9 missing moods

---

## 🔴 `0060` and `0068` — SNAPSHOT BEFORE YOU FIX

**These two cards are the drift findings themselves.** `0060` is `D-1`; `0068` is the MoodPalette
divergence. Repairing them before the audit runs means the audit inspects a runtime where the evidence
has already been quietly removed — **exactly the pattern the audit exists to catch.**

**David's own rule:** *"Audit first. Correction second. No correction is authorised merely because a
discrepancy has been discovered."*

✅ **Already done for you — the snapshot is taken.**
`docs/architecture/findings/_PRE_FIX_EVIDENCE/` @ `b2d1c30`, with `MANIFEST.json`:
`executive.py` `63eef76…` · `prompt_builder.py` `1bc706f…` · `memory_relevance_filter.py` `a7392e2…` ·
`light_engine.py` `f8afb14…` · plus live `routing_trace.json` and `backend_health.json`.

**So: fix them.** The evidence survives at those hashes. **Do not delete or edit that folder.**

---

## Standing rules

- 🔴 **Never buy speed or tidiness with eLo.** *"buy speed by giving eLo less of himself — do not do this at
  all."* No smaller model for his voice, no lower token budget, no trimming context or memory.
  **If measurement says that's the only lever left — stop and report.**
- 🔴 **`FREEZE_V1_LOCK.md` is David's.** 9 CAL actions, 5 voice states, Character DNA. Anything that changes
  *who eLo is* stops at a proposal.
- 🔴 **Read the artefact before judging it.** I called Volume XXVIII a stub from a word count without opening
  it. It was a complete L3-ratified scaffold.
- **Source every change** at the value: `[SPEC]` `[DAVID]` `[VERIFIED]` `[ESTIMATE]` `[PROPOSAL]`.
- **Chat logs outrank passing tests.** Every AT was green while eLo answered David in one register for seven
  turns and invented baseball.
- **The only three legitimate holds:** David's own stated gate · `FREEZE_V1_LOCK` · RESERVED
  (money · legal · safety · robot force). **Nothing else holds anything, ever.**

## Not in this queue

**Social Design Studio `0001`** — deferred by David 2026-08-21: *"needs a better setup."* Not Builder's.
**The Drift Audit** — CLOSED. Evidence recovery is complete; validation is David's.
**Do not touch `docs/architecture/findings/`.**

---

## eLo Multi-Seat Alignment Protocol — installed 2026-08-24
**Protocol:** `docs/architecture/MULTI_SEAT_ALIGNMENT_PROTOCOL_2026-08-24.md`  
**Your overlay:** `docs/architecture/seat_overlays/OVERLAY_BUILDER_2026-08-24.md`  
**Distribution directive:** `docs/architecture/_intake/SOURCE_2026-08-24_DAVID_L3_seat_distribution_directive.md`

**On every session start (or when directed): ALIGN**

ALIGN = Read Governance → Read Recovered Intent → Read Canon → Read Work State → Report Current Position.

**Standard commands:** ALIGN / ONBOARD / READ BOARD / READ ROADMAP / READ RTR / STATUS / BLOCKED / ESCALATE / VERIFY / CONTINUE

**Anti-drift law:** Never silently override canon. Never invent missing evidence. Never resolve another seat's decision. Never implement without authority. Record conflicts rather than choosing.

**BLOCKER SCOPE AMENDMENT — 2026-08-24** (David L3): `docs/architecture/SEAT_PROTOCOL_AMENDMENT_BLOCKER_SCOPE_2026-08-24.md`  
Classify every blocker: ITEM BLOCKED / SEAT BLOCKED / PROGRAMME BLOCKED. Never infer ITEM BLOCKED = PROGRAMME BLOCKED. Never infer SEAT BLOCKED = PROGRAMME BLOCKED. When verification is waiting on your implementation: read Board queue, identify highest-priority authorised item with satisfied dependencies, confirm lane, proceed. Do not alter queue order. Do not bypass a gate. Return control to Board if unclear.

**Compaction survival:** The protocol, your overlay, and this START_HERE are the canonical session entry point. Do not rely on conversation memory where repository evidence exists.
