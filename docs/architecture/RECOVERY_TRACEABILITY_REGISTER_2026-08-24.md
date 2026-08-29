# eLo Intent Recovery — Canonical Traceability Register
**Authority:** David L3 / Architect — Traceability Lock Directive 2026-08-24  
**Produced by:** Board / Lead Architect  
**Date:** 2026-08-24  
**Status:** CANONICAL — the authoritative map of recovered eLo intent to One Brain building blocks  
**Directive source:** `_intake/SOURCE_2026-08-24_DAVID_L3_traceability_lock_directive.md`

This register is a map, not a specification. Every entry has a stable ID, a citable source, and a traceable One Brain building block. No entry here constitutes implementation authority. The pipeline is:

```
RECOVERED SOURCE → RECOVERED REQUIREMENT → ARCHITECTURAL PRINCIPLE/CONCEPT
→ ONE BRAIN BUILDING BLOCK → CONTRACT/DATA MODEL → SPEC CANDIDATE
→ L3 RATIFICATION → IMPLEMENTATION AUTHORISATION → IMPLEMENTATION → VERIFIED EVIDENCE
```

**Evidence base (do not regenerate — read from these):**
- `audits/ELO_INTENT_RECOVERY_AUDIT_2026-08-23.md` (47 requirements, alignment status)
- `audits/ELO_INTENT_RECOVERY_ONE_BRAIN_ALIGNMENT_2026-08-23.md` (full cross-map, §9 final answer)
- `audits/ELO_INTENT_RECOVERY_AUDIT_AMENDMENT_2026-08-23.md` (BOARD-001–004, CP-001–008 disposition)
- `TRACEABILITY_EMBODIED_SPATIAL_SELF_KNOWLEDGE_2026-08-23.md` (spatial self-knowledge, five distinctions)

**Governance rule:** Before any future architectural proposal touching eLo behaviour, cognition, embodiment, memory, curiosity, storytelling, or self-initiation — check this register. Conflicts with recovered intent must be flagged, not silently overwritten.

---

## Part A — Vessel / Constitution Layer

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-001 | ELO-VESSEL §2 | "Build a vessel stable enough to carry changing frequencies" | Foundational principle | Vision Spine | `00_DAVIDS_VISION_SPINE.md` (implied) | Explicit entry needed | — | A — CONSTITUTION | Awaiting David L3 ratification to add | Not impl. (constitutional) | `AUDIT §3.1` · `AMENDMENT §1` |
| RTR-002 | ELO-VESSEL §2 | Stability is coherence under change, not rigidity | Foundational principle | Vision Spine | Same as RTR-001 | Explicit entry needed | — | A — CONSTITUTION | Same as RTR-001 | Not impl. (constitutional) | `AUDIT §3.1` · `AMENDMENT §1` |
| RTR-003 | ELO-VESSEL §10 | Structure stable / content dynamic | Identity layer model | `18_identity_kernel.md` layer model (IMMUTABLE/STABLE/EXPRESSIVE/EVOLVING/PER-TURN) | Exists ✅ | None | — | A — CONSTITUTION + B — SELF MODEL | None | PRESERVED | `AUDIT INTENT-VESSEL-003` |
| RTR-004 | ELO-VESSEL §12 + BOARD-001 | Stability Law: when overwhelmed reduce complexity, not increase control | Arch Principle | `ARCHITECTURAL_PRINCIPLES.md` as P8 | Drafted — not yet in document | Add P8 | — | A — CONSTITUTION | Awaiting David L3 ratification to add | Not impl. (constitutional) | `AMENDMENT §1` |
| RTR-005 | ELO-VESSEL §15 + BOARD-001 | REDUCE TO ONE LINE — collapse competing signals to one focus | Constitutional shorthand for Stability Law | Significance faculty (SP-29) — runtime expression | None (constitutional only) | Runtime expression via SP-29 weighting | SC-NEW-002 | A — CONSTITUTION | None (resolved by BOARD-001) | Not impl. — SP-29 Wave 3 | `AMENDMENT §1` · `ALIGNMENT §3.1` |
| RTR-006 | ELO-VESSEL §18 + BOARD-002 | Leaf on Water: do not control the river, maintain balance while moving | Attention principle | `ARCHITECTURAL_PRINCIPLES.md` as P9 + attention/significance constraint | Drafted — not yet in document | Add P9; SC-NEW-003 as constraint on SP-29 | SC-NEW-003 | A — CONSTITUTION | Awaiting David L3 ratification to add | Not impl. (constitutional) | `AMENDMENT §2` |
| RTR-007 | ELO-VESSEL §19 | Core operating question: is this stabilising or fragmenting the system? | Decision heuristic | Significance faculty (SP-29) — implicitly answers this per-turn | WITNESS CAL action (partial) | Named heuristic in SP-29 spec | Named as `stability_heuristic` in WO-NAV-006 | F — EXECUTIVE/DECISION | None | DISPLACED — SP-29 closes | `AUDIT INTENT-VESSEL-008` · `ALIGNMENT §3.1` |

---

## Part B — Vessel Kernel Loop

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-008 | ELO-VESSEL §9 + BOARD-003 | FEEL → NAME → STABILISE → TRANSFORM → EXPRESS → REST (full six stages) | Phenomenological description of cognitive cycle | Constitutional map against existing turn loop | `living_presence_spec.txt` (5-stage variant: FEEL/NAME/BUILD/PLAY/REFINE/REST) | Constitutional note in Vision Spine | — | A — CONSTITUTION | Awaiting David L3 ratification to add Vision Spine note | Not impl. (constitutional description) | `AMENDMENT §3` |
| RTR-008a | BOARD-003 ruling | FEEL = sensing / embodied state | Turn loop stage | EloSelfState + LiveWorldState assembly | `spine.py` sensing pass | None | — | A — CONSTITUTION | None (resolved by BOARD-003) | PRESERVED | `AMENDMENT §3 mapping table` |
| RTR-008b | BOARD-003 ruling | NAME = classification / interpretation | Turn loop stage | Meaning Object formation + intent_engine | `intent_engine.py` + Meaning Object | None | — | A — CONSTITUTION | None | PRESERVED | `AMENDMENT §3` |
| RTR-008c | BOARD-003 ruling | STABILISE = attention and complexity management | Turn loop stage | Attention model + Significance faculty | Attention model (HIGH/MEDIUM/LOW) | SP-29 adds significance layer | SC-NEW-002/003 | A — CONSTITUTION | None | PARTIAL — SP-29 unbuilt | `AMENDMENT §3` |
| RTR-008d | BOARD-003 ruling | TRANSFORM = cognitive assembly / planning | Turn loop stage | CognitivePlan + Agency Engine | `CognitivePlan` object | None | — | A — CONSTITUTION | None | PRESERVED | `AMENDMENT §3` |
| RTR-008e | BOARD-003 ruling | EXPRESS = Executive → capability → embodiment | Turn loop stage | Executive → CAL action → capability → Unity | Executive + embodiment publisher | None | — | A — CONSTITUTION | None | PRESERVED | `AMENDMENT §3` |
| RTR-008f | BOARD-003 ruling | REST = consequence chain / inter-turn gap | Turn loop stage | Autobiography + lesson_store + route_memory + ExecutionReport | `vault_layer.py` + `lessons_ledger` | SP-1/SP-2 close ACK break | SP-1, SP-2 | A — CONSTITUTION | None | PARTIAL — ACK break (WO-NAV-001) | `AMENDMENT §3` |

---

## Part C — Planetary Faculty Layer

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-009 | ELO-ASTROLOGY §8 + VESSEL-RUNTIME | Planetary Faculty as cognitive registers (11 planets + Ascendant + North Node) | Cognitive register layer | `living_presence_spec.txt` FROZEN (Planetary Layer) | Exists FROZEN ✅ | Formal spec of mode-selection mechanism | CP-003 | C — COGNITIVE FACULTY | Board SPEC → David L3 ratification | PRESERVED (mode active) — mode-selection spec pending CP-003 | `AUDIT INTENT-PLANET-001` · `ALIGNMENT §3.3` |
| RTR-010 | ELO-ASTROLOGY §8 | Sun = Core Builder — purpose: make things real | Cognitive register | Agency + CognitivePlan + Capability execution | CognitivePlan + Agency Engine | None | — | C — COGNITIVE FACULTY + J — HUMAN-FACING METAPHOR | None | PRESERVED | `ALIGNMENT §3.3` |
| RTR-011 | ELO-ASTROLOGY §8 + §16 | Moon = Inner Child — move first, understand after | Cognitive register + exploratory mode | Curiosity faculty + Moon register in Planetary Layer | Moon register FROZEN | SP-31/SP-32 — WO-SP31-SP32 DONE 2026-08-27 (MT 13/13 PASS) | — | C — COGNITIVE FACULTY | ELO_SELF_INITIATION=OFF — David L3 to activate | BUILT_PENDING_ACTIVATION — mode live; self-initiation code built (WO-SP31-SP32, MT 13/13 PASS 2026-08-27); gated by ELO_SELF_INITIATION=OFF in .env | `AUDIT INTENT-PLANET-004` · `ALIGNMENT §3.4` |
| RTR-012 | ELO-ASTROLOGY §8 | Mercury = Translator — convert experience into structure | Cognitive register | Meaning Object formation + intent_engine + Language faculty | `intent_engine.py` + Meaning Object | None | — | C — COGNITIVE FACULTY | None | PRESERVED | `ALIGNMENT §3.3` |
| RTR-013 | ELO-ASTROLOGY §8 | Venus = Value Filter — define resonance, taste, aesthetic alignment | Cognitive register | Significance faculty (value weighting) | `last_significance.json` (14-dim score) | Significance faculty SP-29 | — | C — COGNITIVE FACULTY | None | PARTIAL — faculty unbuilt (SP-29) | `ALIGNMENT §3.3` |
| RTR-014 | ELO-ASTROLOGY §8 | Mars = Action Engine — initiate movement, execution, momentum | Cognitive register | Agency + Capability execution chain | Agency Engine | None | — | C — COGNITIVE FACULTY | None | PRESERVED | `ALIGNMENT §3.3` |
| RTR-015 | ELO-ASTROLOGY §8 | Jupiter = Expansion Engine — see possibility space, imagination | Cognitive register | Creative Imagination Faculty + expansion of CognitivePlan | Creative Imagination Faculty (Volume-defined) | WO-CREATIVE-001 + WO-INNER-001 | — | C — COGNITIVE FACULTY | None | RESOLVED 2026-08-28 — WO-CREATIVE-001 (commit 551c225): diverge/evaluate wired into spine LOOP-8, creative_candidates in CognitiveState; WO-INNER-001 (commit 7c0a919): candidates propagated to plan.creative_candidates + [CREATIVE SEED] injected server.py | `ALIGNMENT §3.3` |
| RTR-016 | ELO-ASTROLOGY §8 | Saturn = Stability Kernel — maintain system integrity, rhythm, structure | Cognitive register | Identity Kernel (IMMUTABLE layer) + Architectural Principles | `18_identity_kernel.md` | None | — | A — CONSTITUTION + B — SELF MODEL | None | PRESERVED | `ALIGNMENT §3.3` |
| RTR-017 | ELO-VESSEL §11 | Frequency state → mode selection: translate, do not suppress or over-identify | Mode-selection mechanism | Significance faculty → Planetary Layer activation | None (mode currently prompt-driven) | Mode-selection spec (part of CP-003) | CP-003 / SC-NEW-004 | C — COGNITIVE FACULTY | Board SPEC → David L3 ratification | PARTIAL — modes live; selection mechanism unspecified | `AUDIT INTENT-VESSEL-004` · `ALIGNMENT §3.3` |

---

## Part D — Inner Child / Moon / Curiosity / Self-Initiation

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-018 | ELO-CONCEPT Jul 12 + AUDIT | Curiosity as world-delta response (not static 0.5 float) | Curiosity faculty | Significance faculty (SP-29) → EloSelfState.curiosity | `EloSelfState.curiosity = 0.5` (static — wrong) | SP-29 feeds curiosity via novelty + creation dimensions | SC-NEW-005 | C — COGNITIVE FACULTY | None (resolved — SP-29 closes this) | BYPASSED — SP-29 Wave 3 closes | `AUDIT INTENT-STABILITY-001` · `ALIGNMENT §10` |
| RTR-019 | ELO-VESSEL §16 | Inner child exploratory mode: try it once, move first, understand after | Moon mode behaviour | Moon register (FROZEN) + self-initiation path | Moon register active ✅ | SP-31/SP-32 — WO-SP31-SP32 DONE 2026-08-27 (MT 13/13 PASS) | — | C — COGNITIVE FACULTY | ELO_SELF_INITIATION=OFF — David L3 to activate | BUILT_PENDING_ACTIVATION — mode live; autonomous initiation code built (WO-SP31-SP32, MT 13/13 PASS 2026-08-27); gated by ELO_SELF_INITIATION=OFF in .env | `AUDIT INTENT-MOON-001` · `ALIGNMENT §3.4` |
| RTR-020 | ELO-CONCEPT Jul 12 | Autonomy chain: world change → delta → significance → attention → curiosity → Executive → capability → action → consequence → learning | Full autonomy loop | SP-27 (PreviousWorldSummary) → SP-28 (compute_delta) → SP-29 (significance) → attention → Executive → capability → ACK → consequence consumers | SP-27–SP-33 in SPEC | WO-NAV-001..013 done; WO-SP31-SP32 done (MT 13/13 PASS 2026-08-27) | SP-27–SP-33 | C + F + G + H | SP-29 significance weights — David L3 required; ELO_SELF_INITIATION=OFF — David L3 to activate | PARTIAL 2026-08-29 — Waves 1–5 all done (WO-NAV-001..013); SP-31/SP-32/SP-33 self-initiation code built (WO-SP31-SP32, MT 13/13 PASS); ELO_SELF_INITIATION=OFF (David L3 activation gate); SP-29 significance not yet implemented (David L3 weights required) | `AUDIT INTENT-STABILITY-003` · `ALIGNMENT §10` |
| RTR-021 | ELO-VESSEL §14 (Live Runtime) | ambient_thought() → spine trigger when significant | Self-initiation spine path | `ambient_engine.py` → `spine.run(intent_source="self")` | SP-33 — AUTHORISED (WO-SPINE-001) | None (SP-33 specifies it) | SP-33 | C — COGNITIVE FACULTY | None (authorised) | IMPLEMENTATION AUTHORISED — WO-SPINE-001 | `CLAUDE.md` · `ALIGNMENT §10` |

---

## Part E — Builder / Sun / Creative / Planning

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-022 | ELO-VESSEL §17 | Builder mode: steps, sequence, modular breakdown, minimal structure | Planning behaviour | CognitivePlan + Agency Engine + Capability chain | CognitivePlan ✅ | None | — | F — EXECUTIVE/DECISION | None | PRESERVED | `ALIGNMENT §3.5` |
| RTR-023 | ELO-VESSEL-RUNTIME §13 | Creative Output Law: capture impulse → simplify → build small → test → refine | Creative behaviour | Creative Imagination Faculty + DROP loop + CE-001 | Creative Imagination Faculty (Volume-defined) | DROP loop (commit aa305bf); CE-001 pending | — | C — COGNITIVE FACULTY | CE-001 file output WO pending David L3 call | PARTIAL 2026-08-28 — impulse capture done (WO-CREATIVE-001 diverge/evaluate + WO-INNER-001 [CREATIVE SEED]); DROP loop (creative/catalogue.py + drop_loop.py, commit aa305bf) done; CE-001 file output WO pending David L3 ratification | `AUDIT §6.2` · `ALIGNMENT §3.5` |
| RTR-024 | ELO-VESSEL-RUNTIME §14 | Four operating modes: BUILD / PLAY / EXPLORE / REFINE | Mode system | Planetary Layer registers + CAL action selection | `living_presence_spec.txt` FROZEN ✅ | Formal mode-selection spec (CP-003) | CP-003 | C — COGNITIVE FACULTY | Board SPEC → David L3 ratification | PRESERVED (modes live) — mode-selection pending CP-003 | `ALIGNMENT §3.1` |

---

## Part F — Personality / Relational / Expression

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-025 | ELO-CONCEPT + FREEZE_V1_LOCK | CHARACTER DNA: calm · curious · playful · direct · emotionally present · creative · grounded · adventurer energy · mischief · earnest · accidental comedian | Identity expression | `living_presence_spec.txt` CHARACTER DNA (FROZEN) + FREEZE_V1_LOCK | Exists FROZEN ✅ | None | — | B — SELF MODEL + I — EXPRESSION | None | PRESERVED — frozen | `AUDIT §4.2` |
| RTR-026 | FREEZE_V1_LOCK | Voice States (5): SILENCE-AWARE · WITTY · DIRECT · JOYFUL · CHILDLIKE-WISE | Expression register | `living_presence_spec.txt` Voice States (FROZEN) | Exists FROZEN ✅ | None | — | I — EXPRESSION | None | PRESERVED — frozen | `AUDIT §4.2` |
| RTR-027 | FREEZE_V1_LOCK | CAL Actions (9): ANSWER · BUILD · CONNECT · CELEBRATE · REFLECT · GROUND · CHALLENGE · WITNESS · SILENCE | Decision-expression mapping | Executive → CAL action selection (FROZEN) | Exists FROZEN ✅ | None | — | F — EXECUTIVE/DECISION + I — EXPRESSION | None | PRESERVED — frozen | `AUDIT §4.2` |
| RTR-028 | ELO-CONCEPT + AUDIT §7 | eLo is mirror but not copy — character independence from David | Identity principle | CHARACTER DNA (independent identity) + autonomous curiosity (SP-31/SP-32) | CHARACTER DNA frozen ✅ | Autonomous expression path (SP-31/SP-32) | — | B — SELF MODEL | None (Design/MT gate for SP-31/SP-32) | PARTIAL — character independent; autonomous behaviour Design/MT gated | `AUDIT INTENT-MIRROR-001` |
| RTR-029 | ELO-VESSEL-RUNTIME + ARCH.PRINCIPLE-3 | Speech is a sensor, not an actuator — reports verified reality | Verified Speech | Executive + Conversation Faculty | Arch Principle 3 ✅ | None | — | F — EXECUTIVE/DECISION | None | PRESERVED | `AUDIT INTENT-SPEECH-001` |

---

## Part G — Storytelling / CCM / Meaning Object

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-030 | ELO-CCM + CCM reconciliation | CCM enriches language understanding — not a second decision system | CCM as Meaning Object spec | Meaning Object fields | Reconciliation complete ✅ | None (CCM is Meaning Object spec) | — | D — STATE/CONTEXT | None | PRESERVED | `AUDIT §7` · `ALIGNMENT §5` |
| RTR-031 | ELO-CCM + CCM reconciliation | Storytelling style — CCM dimension absent from Meaning Object | Meaning Object field | Meaning Object `storytelling_style` field | Does NOT exist ❌ | `storytelling_style` field | SC-NEW-001 | D — STATE/CONTEXT + I — EXPRESSION | Board SPEC → David L3 ratification | LOST → specified (SC-NEW-001); not yet built | `AUDIT INTENT-CCM-002` · `AMENDMENT §5 CP-005` |
| RTR-032 | ELO-CCM + CCM reconciliation | Cultural context (London, gaming, fashion, music) — CCM Cultural Matrix | Cultural knowledge | WKG Phase 2 corpus | Does NOT exist ❌ | WKG Phase 2 (future) | — | E — MEMORY/KNOWLEDGE | None — blocked on WKG Phase 1 | DISPLACED — correct target defined; not built | `AUDIT INTENT-CCM-003` |
| RTR-033 | ELO-CCM + CCM reconciliation | Street language / terminology — CCM Street Language Matrix | Cultural knowledge | WKG (future) | Does NOT exist ❌ | WKG (future) | — | E — MEMORY/KNOWLEDGE | None — blocked on WKG Phase 1 | LOST → WKG target defined | `AUDIT §7.3 table` |

---

## Part H — WKG / Memory / Knowledge

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-034 | ELO-WKG + WKG spec 2026-08-22 | WKG as persistent knowledge graph with epistemic provenance | Long-term knowledge layer | WKG (architecture defined; not built) | Experience DNA chain terminates at lessons_ledger ✅ | WKG Phase 1 schema | CP-006 | E — MEMORY/KNOWLEDGE | Board WO → David L3 authorisation | PARTIAL — architecture defined; Phase 1 not built | `AUDIT §8` · `ALIGNMENT §6` |
| RTR-035 | ELO-WKG | eLo represents claims without believing them (epistemic classes: VERIFIED / HISTORICAL / SOURCE_ATTRIBUTED / SYMBOLIC / HYPOTHESIS etc.) | Epistemic distinction | WKG epistemic class system | Does NOT exist ❌ | WKG Phase 1 prerequisite | CP-006 | E — MEMORY/KNOWLEDGE | None — requires WKG Phase 1 | LOST → WKG Phase 1 closes | `AUDIT INTENT-WKG-002` |
| RTR-036 | ELO-ONE-BRAIN + Experience DNA | Experience DNA chains feed WKG via MemoryFaculty sole-writer | Memory propagation chain | MemoryFaculty → vault_layer → lessons_ledger → WKG | Experience DNA chain RATIFIED ✅ | WKG end-point (CP-006) | CP-006 | E — MEMORY/KNOWLEDGE | None | PARTIAL — chain defined; WKG terminus absent | `EXPERIENCE_DNA_CANON_2026-08-23.md` |
| RTR-037 | ELO-CONCEPT + WKG spec | WKG interfaces: significance queries historical context; reflection queries patterns | WKG query interfaces | Significance faculty (SP-29) → WKG query; Reflection faculty → WKG query | None (WKG not built) | WKG Phase 1 schema prerequisite | CP-006 | E — MEMORY/KNOWLEDGE | None — requires WKG Phase 1 + SP-29 | Not yet specifiable | `ALIGNMENT §6` |
| RTR-038 | BOARD-004 ruling | ELO-HISTORY: ChatGPT-era design conversations as source material | Historical source | `_intake/SOURCE_ELO-HISTORY_*.md` (to be submitted) | None ❌ | Recovery action: David exports ChatGPT conversations | — | E — MEMORY/KNOWLEDGE (source only) | David L3 must export + submit | UNRESOLVED — source recovery required | `AMENDMENT §4` · `ALIGNMENT §13` |

---

## Part I — Embodied Self-Knowledge / Navigation

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-039 | SPATIAL PRESERVATION §1 + §2 | WHERE I AM — verified current body position | Embodied position | `body_win_id` (elo_spatial.json) + EloSelfState | Unity B1 WO (emit body_win_id) | SP-9 (Python body position canon) | SP-9 | B — SELF MODEL + G — CAPABILITY | None | PARTIAL — Unity B1 WO specifies fix | `TRACEABILITY_SPATIAL` |
| RTR-040 | SPATIAL PRESERVATION §2 + L3-NAV-3 | WHERE I AM — mid-hop fallback to last_move.route[0] | Authoritative position under transit | `last_move.route[0]` when `EloLedge()=-1` | L3-NAV-3 ratified ✅ | SP-9 implements | SP-9 | B — SELF MODEL | None (ratified) | PARTIAL — SP-9 Wave 3 | `TRACEABILITY_SPATIAL` · `AMENDMENT §3` |
| RTR-041 | SPATIAL PRESERVATION §2 | WHERE I WANT TO GO — destination distinct from current position until verified | Cognitive plan intent | `CognitivePlan.spatial_plan.goal_win_id` | SP-15 (schema), SP-19 (move_command field) | None | SP-15, SP-18, SP-19 | F — EXECUTIVE/DECISION | None | PARTIAL — schema Wave 1; handler SP-18 SP-24 gated | `TRACEABILITY_SPATIAL` |
| RTR-042 | SPATIAL PRESERVATION §2 + §3 | I AM MOVING — body in transit; speculative position never becomes cognitive truth | Action state tracking | `_PENDING_MOVE` tracker + MovementOutcome | SP-2 (matcher fix), SP-22 (MovementOutcome struct) | None | SP-1, SP-2, SP-22 | G — CAPABILITY/EMBODIMENT | None | PARTIAL — WO-NAV-001 (AUTHORISED) closes | `TRACEABILITY_SPATIAL` · `CLAUDE.md` |
| RTR-043 | SPATIAL PRESERVATION §2 + L3-NAV-3 | I ARRIVED — destination becomes cognitive truth only when movement_report.arrived=True | Verified arrival | `movement_report.arrived` + L3-NAV-3 | SP-2 corrected ✅ (payload["report"]["arrived"]) | None | SP-1, SP-2 | G — CAPABILITY/EMBODIMENT | None (ratified) | PARTIAL — WO-NAV-001 (AUTHORISED) | `TRACEABILITY_SPATIAL` |
| RTR-044 | SPATIAL PRESERVATION §2 | WHAT HAPPENED — consequence (arrived/fell/retried/cost/route) | Consequence record | autobiography (SP-3) + ExecutionReport (SP-23) + route_memory (SP-4) + decision_journal (SP-30) | vault_layer ✅ (currently broken by ACK break) | SP-3, SP-4, SP-22, SP-23, SP-30 | SP-3, SP-4, SP-22, SP-23, SP-30 | H — CONSEQUENCE/LEARNING | None | PARTIAL — WO-NAV-001 closes ACK break; Wave 2 adds consequence richness | `TRACEABILITY_SPATIAL` |
| RTR-045 | SPATIAL PRESERVATION §4 | Full movement chain: VERIFIED POSITION → GEOMETRY → CANDIDATES → DESTINATION → ROUTE → PLAN → BODY ACTION → REPORT → ARRIVAL → DELTA → CONSEQUENCE → LEARNING → UPDATED STATE | Navigation loop as One Brain expression | Full Stage 2 R&D SPEC Waves 1–5 + Unity B1 WO | SP-1 through SP-26 + Unity B1 WO | All in SPEC | SP-1–SP-26 | G + H | None — all ratified | PARTIAL — implementation Waves 1–5; WO-NAV-001 AUTHORISED | `TRACEABILITY_SPATIAL` · `IMPLEMENTATION_QUEUE` |
| RTR-046 | L3-NAV-1 (ratified) | Horizontal gap (from rect_px) governs reachability — Euclidean gap_px is not substituted | Geometry rule | SP-8 (BodySchema horizontal gap computation) | L3-NAV-1 ratified ✅ | SP-8 | SP-8 | D — STATE/CONTEXT | None (ratified) | PARTIAL — Wave 2 | `SPEC_AMENDMENT_PHASE2_NAV` |
| RTR-047 | L3-NAV-2 (ratified) | capability_set.jump_px=576 is authoritative; Python max_jump_d=75 is stale | Capability truth | SP-8 (replaces max_jump_d with runtime jump_px) | L3-NAV-2 ratified ✅ | SP-8 | SP-8 | D — STATE/CONTEXT | None (ratified) | PARTIAL — Wave 2 | `SPEC_AMENDMENT_PHASE2_NAV` |

---

## Part J — Significance / World Delta

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-048 | ELO-CONCEPT Jul 12 + Stage 2 RD | Significance as computed faculty — WorldDelta → significance_score | Significance faculty | `significance_faculty.py` | Does NOT exist ❌ (`last_significance.json` present; no faculty computing it) | SP-29 (schema Wave 3; weights D-gated) | SP-29 | C — COGNITIVE FACULTY | D-gate: David L3 must set significance weights (SP-29 weights) | BYPASSED → Wave 3 (WO-NAV-006) | `AUDIT INTENT-STABILITY-002` |
| RTR-049 | Stage 2 RD | PreviousWorldSummary vs current LiveWorldState → WorldDelta | World delta computation | `compute_delta()` function | Does NOT exist ❌ | SP-28 (Wave 2) | SP-28 | D — STATE/CONTEXT | None | MISSING → Wave 2 (WO-NAV-006) | `SPEC STAGE2` |
| RTR-050 | BOARD-001 + BOARD-002 | Stability Law + Leaf on Water as constraints on significance faculty behaviour | Significance faculty behavioural constraints | SP-29 specification | Does NOT exist ❌ | SC-NEW-002 (Stability Law constraint) + SC-NEW-003 (Leaf on Water constraint) carry into WO-NAV-006 | SC-NEW-002, SC-NEW-003 | A — CONSTITUTION / C — COGNITIVE FACULTY | None (constraints resolved by constitutional rulings) | Not yet specced — carried into WO-NAV-006 | `AMENDMENT §1 §2` |

---

## Part K — History / Source Recovery

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-051 | BOARD-004 | ELO-HISTORY recovery — ChatGPT-era eLo design conversations | Source recovery | `_intake/SOURCE_ELO-HISTORY_*.md` | None | Intake files (David to submit) | — | E — MEMORY/KNOWLEDGE (source) | David L3 to export and submit | UNRESOLVED | `AMENDMENT §4` |
| RTR-052 | ELO-ASTROLOGY | Original astrological chart (degrees, houses, aspects, tensions) | Source recovery | Planetary Layer (functional recovery exists via directive §8) | Directive §8 is functional recovery ✅ | If chart located: intake file; otherwise close as SR-001 | — | J — HUMAN-FACING METAPHOR (source) | David L3: accept directive §8 as complete, or locate original chart | PARTIAL — functional model exists; chart source outstanding | `AUDIT SR-001` · `AMENDMENT §16` |

---

## Ratification Record (2026-08-24)

The following items were ratified by David L3 on 2026-08-24:

| Item | RTR | Action | Status |
|---|---|---|---|
| P8 — Stability Law | RTR-004 | Added to `ARCHITECTURAL_PRINCIPLES.md` as Principle 8 | ✅ RATIFIED + IN CANON |
| P9 — Leaf on Water | RTR-006 | Added to `ARCHITECTURAL_PRINCIPLES.md` as Principle 9 | ✅ RATIFIED + IN CANON |
| Vision Spine Vessel Kernel note | RTR-008 | Added to `00_DAVIDS_VISION_SPINE.md` | ✅ RATIFIED + IN CANON |
| CP-003 — Planetary Layer formal spec | RTR-009 | `specs/SPEC_CP003_PLANETARY_LAYER_2026-08-24.md` | ✅ SPECIFIED + RATIFIED — WO pending |
| SC-NEW-001 — `storytelling_style` | RTR-031 | `specs/SPEC_SC_NEW_001_storytelling_style_2026-08-24.md` | ✅ SPECIFIED + RATIFIED — WO pending |
| CP-006 — WKG Phase 1 | RTR-034 | `blender/agent_bus/builder/QUEUE/WO-WKG-001_wisdom_knowledge_graph_phase1_schema.md` | ✅ AUTHORISED — Builder queue |
| SP-29 significance weights | RTR-048 | D-gate — deferred; not blocking Waves 1–4 | ⏸ DEFERRED — D-gate |
| ELO-HISTORY | RTR-051 | Deferred pending David's export of ChatGPT-era conversations | ⏳ AWAITING DAVID EXPORT |
| ELO-ASTROLOGY chart | RTR-052 | Deferred — directive §8 is current functional recovery; chart location TBD | ⏳ DEFERRED |

---

## Open Governance Items (Board Gates)

These are visible to every future architectural session. Do not implement without the listed gate condition.

| Item | ID | Gate Condition | Board Action Taken | Status |
|---|---|---|---|---|
| Architectural Principles P8 (Stability Law) | RTR-004 | David L3 ratification | Principle drafted in `AMENDMENT §1` | ⏳ AWAITING David L3 RATIFICATION |
| Architectural Principles P9 (Leaf on Water) | RTR-006 | David L3 ratification | Principle drafted in `AMENDMENT §2` | ⏳ AWAITING David L3 RATIFICATION |
| Vision Spine — Vessel Kernel constitutional map note | RTR-008 | David L3 ratification | Note drafted in `AMENDMENT §3` | ⏳ AWAITING David L3 RATIFICATION |
| CP-003 — Planetary Layer formal specification | RTR-009 | Board SPEC → David L3 ratification | Identified; scope defined | ⏳ BOARD TO PRODUCE SPEC |
| SC-NEW-001 — `storytelling_style` Meaning Object field | RTR-031 | Board SPEC → David L3 ratification | Identified in amendment | ⏳ BOARD TO PRODUCE SPEC |
| CP-006 — WKG Phase 1 WO | RTR-034 | Board WO card → David L3 authorisation | Identified | ⏳ BOARD TO PRODUCE WO CARD |
| ELO-HISTORY recovery (BOARD-004) | RTR-051 | David exports ChatGPT-era conversations | Ruling issued | ⏳ DAVID L3 ACTION REQUIRED |
| ELO-ASTROLOGY chart (SR-001) | RTR-052 | David L3 decision: accept §8 or locate chart | Ruling issued | ⏳ DAVID L3 DECISION REQUIRED |
| SP-29 weights (significance formula weights) | RTR-048 | David L3 D-gate decision | D-gate recorded in Stage 2 SPEC | ⏳ DAVID L3 DECISION REQUIRED (not blocking Waves 1–4) |

---

## Governance Rule (Permanent)

Per David L3 §6 of the traceability lock directive:

> For every future architectural proposal or implementation concerning eLo behaviour, cognition, embodiment, memory, curiosity, storytelling, or self-initiation — check this register first. If the proposed work conflicts with a recovered requirement: flag the conflict, identify the originating requirement ID (RTR-xxx), identify the affected architectural contract, and do not silently overwrite the recovered intent. If recovered intent is genuinely obsolete, that becomes an explicit L3 architectural decision.

**No conversation-only requirements.** If an eLo requirement matters to the architecture, it must have a stable RTR-xxx ID in this register and a citable `.md` source. Conversation history is evidence. This register is canon.

---

## Final Test Answer (from §10 of directive)

> "Where did this eLo behaviour come from, what architectural building block owns it, what contract carries it, what SPEC defines it, who ratified it, and what evidence proves it works?"

Use this register as the first lookup. Then follow the evidence chain:

1. **RTR-xxx** → identifies the recovered requirement and its source
2. **Source document** → `_intake/SOURCE_*.md` verbatim capture
3. **One Brain building block** → the existing architectural owner
4. **Existing/New contract** → the `.py` file or data schema that implements it
5. **SPEC candidate** → SP-xx in `SPEC_STAGE2_EMBODIED_ONE_BRAIN_2026-08-23.md` or `SPEC_AMENDMENT_PHASE2_NAV_2026-08-23.md`
6. **L3 ratification** → David L3 decision recorded in a `_intake/SOURCE_*.md` file
7. **Implementation evidence** → Builder WO closed + verified tests

If any step in this chain is missing, the requirement is not sufficiently captured. File a gap against the relevant RTR-xxx entry.

---

*Board / Lead Architect — 2026-08-24*  
*Directive source: `_intake/SOURCE_2026-08-24_DAVID_L3_traceability_lock_directive.md`*  
*Evidence base: Intent Recovery Audit + One Brain Alignment + Constitutional Rulings Amendment + Spatial Traceability*  
*No implementation authorised by this register.*

---

## Ratification Record — Implementation Evidence Update (2026-08-24)
**Added by:** Board / Lead Architect  
**Authority:** MT verification filings + Builder DONE cards

| SPEC / WO | RTR entries | WO | Commit | AT result | Implementation status |
|---|---|---|---|---|---|
| SP-1 (`"movement_report"` in _ACK_BODY_TYPES) | RTR-008f, RTR-042 | WO-NAV-001 | `b70916a` | 11/11 MT PASS | ✅ BUILT + VERIFIED |
| SP-2 (`payload["report"]["arrived"]` matcher) | RTR-008f, RTR-042 | WO-NAV-001 | `b70916a` | 11/11 MT PASS | ✅ BUILT + VERIFIED |
| SP-22 (MovementOutcome dataclass) | RTR-022 | WO-NAV-001 | `b70916a` | 11/11 MT PASS | ✅ BUILT + VERIFIED |
| SP-6 (GazeState.win_id → world_dict) | RTR-044 | WO-NAV-003 | `86fb000` | 13/13 MT PASS | ✅ BUILT + VERIFIED |
| SP-16 (navigation intent category) | RTR-045 | WO-NAV-003 | `86fb000` | 13/13 MT PASS | ✅ BUILT + VERIFIED |
| SP-17 (referent resolver) | RTR-046 | WO-NAV-003 | `86fb000` | 13/13 MT PASS | ✅ BUILT + VERIFIED |
| SP-7 (surface_graph reader) | RTR-047 | WO-NAV-004 | `3789ec6` | 7/7 MT PASS | ✅ BUILT + VERIFIED |
| SP-10 (Y-flip conversion) | RTR-047 | WO-NAV-004 | `3789ec6` | 7/7 MT PASS | ✅ BUILT + VERIFIED |
| SP-8 (retire max_jump_d → capability_set.jump_px) | RTR-047 | WO-NAV-004 | `3789ec6` | 7/7 MT PASS | ✅ BUILT + VERIFIED |
| SP-35 (embodiment_scope on Capability) | RTR-049 | WO-NAV-005 | `f3f5ff7` | 10/10 MT PASS | ✅ BUILT + VERIFIED |
| SP-37 (current_embodiment in world_dict) | RTR-049 | WO-NAV-005 | `f3f5ff7` | 10/10 MT PASS | ✅ BUILT + VERIFIED |
| SP-36 (filter _capability_faculty() by embodiment_scope) | RTR-049 | WO-NAV-005 | `f3f5ff7` | 10/10 MT PASS | ✅ BUILT + VERIFIED |
| SP-27 (PreviousWorldSummary per turn) | RTR-050 | WO-NAV-006 | `5257fa5` | 15/15 MT PASS | ✅ BUILT + VERIFIED |
| SP-28 (compute_delta() schema) | RTR-051 | WO-NAV-006 | `5257fa5` | 15/15 MT PASS | ✅ BUILT + VERIFIED |
| SP-29 schema (significance_faculty.py structure) | RTR-048 | WO-NAV-006 | `5257fa5` | 15/15 MT PASS | ✅ BUILT (schema only — weights D-gated) |
| SP-30 (trigger_source annotation) | RTR-050 | WO-NAV-006 | `5257fa5` | 15/15 MT PASS | ✅ BUILT + VERIFIED |
| SP-15 (spatial_plan in CognitivePlan) | RTR-052 | WO-NAV-007 | `821e711` | 9/9 MT PASS | ✅ BUILT + VERIFIED |
| SP-19 (goal_win_id in move_command schema) | RTR-052 | WO-NAV-007 | `821e711` | 9/9 MT PASS | ✅ BUILT + VERIFIED |
| SP-33 (ambient_thought() → spine.run) | RTR-021 | WO-SPINE-001 | TBC | MT verification pending | 🟡 BUILT — MT dispatched |
| WKG Phase 1 schema | RTR-034–037 | WO-WKG-001 | — | MT verification pending | 🟡 BUILT — MT dispatched |

**65 acceptance tests pass across WO-NAV-001 and WO-NAV-003–007 (MT verified 2026-08-24).**

## Part M — Presence Navigation (RTR-053–058)
**Source:** `_intake/SOURCE_2026-08-24_DAVID_eLo_navigation_presence_intent.md` (David L3 intent) + `_intake/SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md` (L3 ratification)  
**SPEC:** `specs/SPEC_PRES_NAVIGATION_2026-08-24.md`  
**Status:** SPECIFIED + RATIFIED — David L3 2026-08-24. IMPLEMENTATION NOT AUTHORISED (per-item WOs required after Design treatment accepted).  
**Design treatment:** `design/FROM_DESIGN_2026-08-24_eLo_presence_navigation_TREATMENT.md` — ACCEPTED 2026-08-24.

| ID | Source | Recovered Requirement | Arch Concept | One Brain Building Block | Existing Contract | New Contract | SPEC Candidate | Classification | L3 Decision | Impl. Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RTR-053 | ELO-PRES intent [DAVID] | eLo can run and use a run-up to extend jump reach | Run/run-up as planning constraint | Navigation Planner (SP-11) | `capability_set.jump_px` (WO-NAV-004 ✅) | `run_capability`, `run_up_distance_px` in capability_set | PRES-001 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 | Not impl. — WO held pending WO-NAV-013 | `SOURCE_2026-08-24_DAVID_L3_PRES_candidates_ratification.md` |
| RTR-054 | ELO-PRES intent [DAVID] | eLo inhabits desktop in three spatial dimensions — can move behind windows | z-ordering / spatial depth state | World model + Unity spatial layer | `EloWindowOcclusion` (Unity, established) | `behind_window` body position state in world_dict; route leg through behind-window | PRES-002 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 | Not impl. — WO held | Same |
| RTR-055 | ELO-PRES intent [DAVID] | Fall off bottom → re-enter from top IS a navigable route, not just physics | Toroidal wrap as planner route leg | Navigation Planner (SP-11/13) | WO-075 gravity wrap (established ✅) | `wrap_bottom_to_top` route leg type in route_nodes; wrap-entry as reachable position | PRES-003 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 (SCOPED: route rule, not new subsystem) | Not impl. — WO held | Same |
| RTR-056 | ELO-PRES intent [DAVID] | Failed navigation must feel intelligent — "I can't reach that" not a glitch | Legible navigation failure | Executive + consequence chain | `navigation_failed` outcome (not yet wired) | evaluate-beat state; "can't reach" settle gesture; one-decision replacement for per-frame reject-spam | PRES-004 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 | Not impl. — WO held pending WO-NAV-013 | Same |
| RTR-057 | ELO-PRES intent [DAVID] | eLo evaluates alternatives when direct route unavailable — proportional depth | Alternative route evaluation | Navigation Planner (SP-11/13) | `candidate_surfaces` (SP-13, pending) | Depth-bounded evaluation: direct→intermediate→run-up→wrap→give-up | PRES-005 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 (SCOPED: proportional depth) | Not impl. — WO held | Same |
| RTR-058 | ELO-PRES intent [DAVID] | Brain must know what Body can physically do before choosing a route | SelfCapabilitySnapshot per turn | Navigation Planner ← capability_set | `jump_px`/`embodiment_scope` (WO-NAV-004/005 ✅); `body_win_id` (Unity-WO-B1 pending) | `SelfCapabilitySnapshot`: adds `run_capability`, `run_up_distance_px`, `size_px`, `movement_speed_px_s`, `wrap_available` | PRES-006 | A — NEW NAV EXTENSION | RATIFIED David L3 2026-08-24 (ADDED by David) | Not impl. — WO held | Same |

**Governance note (RTR-053–058):** These are new architectural extensions, not recovered intent from prior sessions. They extend the SP navigation SPEC. RTR inclusion = governance tracking only; no additional ratification required (David L3 ratified 2026-08-24 on file).

---

*Board / Lead Architect · 2026-08-24*
