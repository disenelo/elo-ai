# CANON BUILD PROGRAM — implement the 28-volume Bible to DoD (David 2026-08-10: "build WOs, write it all, align it all, add it to the board")

**Owner:** Architect authors + sequences (Markdown); **Builder** implements eLo-OS volumes; **Designer** the embodiment ones. David = L3 + the RESERVED gates. **Status:** all volumes now WRITTEN (spec) — this program tracks BUILDING them.
**Rule (DoD):** a volume is DONE only when its faculty/contract is implemented, wired into the turn loop, tested WITHOUT David, and the Audit can mark it COMPLETE — never "chapter written." Volume V is the reference bar.
**Sequencing law:** this program runs **BEHIND Presentable v1** (the finish-line-6 comes first). Nothing here pulls Builder/Designer off the milestone. Several volumes are PARTIALLY built already (the specs cite live code) — those WOs are "complete + wire + verify," not "build from zero."

## Gate before ratify — the alignment rulings (see `docs/architecture/CANON_REVIEW_QUEUE_2026-08-10.md`)
**✅ ALL RULED 2026-08-10 — gate CLOSED.** Rulings A·B·C·D decided, plus **E** (shared ownership of movement + mandatory communication) and **F** (eLo learns; identity asserted by the spine, never from learned weights). See `docs/architecture/CANON_RULINGS_2026-08-10.md`. Original four:
- **A · Two world-graphs** (`relationships/world_graph.json` vs `identity/world_graph.json`) — Vol XXIV. Ruling → then XXIV.
- **B · Two attention mechanisms** (`core/attention.py` vs `runtime/working_memory.py`, latter unwired) — Vol VI. Ruling → then VI.
- **C · Assemble-after-decide + name clash** (`CognitiveSnapshot` vs `UnifiedCognitiveState`; assembly runs AFTER the decision, ADR-Exec-006 says BEFORE) — Vol XVI. Ruling → then XVI.
- **D · Drift self-applies with no gate + trait model ≠ V Ch.7** (Audit gap #6) — Vol X. Ruling → then X.

## The build WOs — one per volume (status of the SPEC in parentheses)

### Tier A — Core brain, unblocks the most (Builder) — build first, post-Presentable
| WO | Volume | Build scope (to DoD) | Blocked by |
|----|--------|----------------------|-----------|
| WO-CANON-XV | XV World Model | Wire the unified LiveWorldState; faculties read it once (stop direct-sensor drift) | — (Priority #2) |
| WO-CANON-XII | XII Perception | Wire perceive()→World-State copy; promote fidelity guard to structured flags (all modalities) | XV · ruling A? no |
| WO-CANON-VI | VI Working Memory & Attention | Wire `runtime/working_memory.py` into CognitiveState + spine; resolve the two-attention design | **ruling B** |
| WO-CANON-VIII | VIII Memory Architecture | Wire the single logical MemoryFaculty (candidate-in/decision-out); call `reinforce()` on retrieval | — |
| WO-CANON-XVI | XVI Multi-Faculty Coordination | Assemble UnifiedCognitiveState BEFORE the decision; priority scheduling on the bus | **ruling C** |
| WO-CANON-X | X Personality Engine | Put drift behind a validation gate; reconcile trait model with V Ch.7 | **ruling D** |

### Tier B — Cognition support (Builder) — after Tier A
| WO | Volume | Build scope | Blocked by |
|----|--------|-------------|-----------|
| WO-CANON-XXIV | XXIV Knowledge | Add confidence+evidence+ranked retrieval; single canonical graph | **ruling A** |
| WO-CANON-XX | XX Cognitive Economy | Make the router a cognitive-tier selector w/ value-gated escalation + cost telemetry | — |
| WO-CANON-XXV | XXV Temporal Cognition | Time-perception + circadian + planning-horizon faculty | XV · XXI |
| WO-CANON-XXI | XXI Narrative Identity | Autobiography journal (WO-078) + coherence/verified-autobiography guard | VIII · XXVII gate |
| WO-CANON-XXII | XXII Faculty Genome | Genome descriptor + registry + validation gate | XVI |

### Tier C — Governance & expansion (mixed) — lowest urgency, mostly formalisation
| WO | Volume | Build scope | Blocked by |
|----|--------|-------------|-----------|
| WO-CANON-XXIII | XXIII Security & Trust | Formalise gate/approval/secret discipline; define LG-2 | David L3 (LG-2) |
| WO-CANON-XXVII | XXVII Eng Standards & Canon Gov | Consolidate `engineering/` governance; ADR-numbering + Governance-DoD ruling | David/CA rulings |
| WO-CANON-XXVI | XXVI Creative Intelligence | Domain generators; needs the AestheticProfile call | David L3 (taste) |
| WO-CANON-XXVIII | XXVIII Adaptive Learning/RL | Learning Faculty under ADR-Exec-005 | Spatial Faculty · already gated |
| WO-CANON-XIX | XIX Consciousness Research | Research programme → findings become ADRs only | — |

### Already live/ratified (verify-only at Audit): I, II, III, IV, V (ratified), XIV, IX (engine live).
> **⚠ CORRECTED 2026-08-10:** **VII, XI, XIII were wrongly listed here as "verify-only" — they had NO CANON AT ALL.**
> That exemption is why they were never written. Now written (`Volume_VII/`, `Volume_XI/`, `Volume_XIII/`) and
> given build orders WO-CANON-VII / -XI / -XIII. **UPDATE (later 2026-08-10): I, II, III, IV, XIV are NOW WRITTEN TOO** — every volume I–XXVIII has canon. Build orders: WO-CANON-I/II/III/IV/XIV + XVII/XVIII on the board.

**Next Architect step on approval:** promote each spec REVIEW→RATIFIED as David + the Chief Architect clear the review queue, then dispatch the Tier-A WOs to the Builder in order once Presentable v1 lands.
