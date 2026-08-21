---
volume: VIII
title: "Memory Architecture — Biological Memory, Consolidation & Forgetting"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
source: "Cognitive Plan Architecture (19_*) Layer 4 + Consolidation + live code (memory/*)"
implementation: PARTIAL (tiered vault + facts + consolidation faculty + forgetting curve LIVE via WO-011; single logical Memory Faculty / candidate submission + reinforce-on-retrieval PENDING)
Provenance: [ENGINEERING][CREATIVE]
audit_status: OPEN
canonical_path: docs/architecture/Volume_VIII/
dependencies:
  - Volume V Ch.3 (Memory Architecture — cognitive-layer view; reconciled, not forked — Ch.4 §4.5)
  - Volume V Ch.5 (Significance — what becomes memory), Ch.6 (Reflection/integrate_session)
  - Volume VI (Working Memory — boundary above, Ch.4 §4.4), Volume XV (World State — boundary beside)
  - Volume XXIV (Knowledge — boundary beside), Volume XXI (Autobiographical Thread — derived view)
  - memory/vault_layer.py (one writer + retrieval), memory/consolidation_faculty.py (WO-011),
    memory/obsidian_loader.py (one reader); 17_memory_update.md (STUB — see reconciliation)
priority: "Audit Critical Gaps #3 (Working Memory) & #4 (Consolidation) — HIGH/MEDIUM"
last_review: 2026-08-10
next_review: TBD
---

# Volume VIII — Memory Architecture

Layer 4 (+ Consolidation) of the Cognitive Plan Architecture. The dedicated deep volume
for **how eLo remembers over time**: the biological memory types, storage tiers, the
timed consolidation faculty, and the forgetting curve.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V8-CH01 | Chapter 1 | Biological Memory, Consolidation & Forgetting (model overview) | READY FOR REVIEW |
| ELO-V8-CH02 | Chapter 2 | The Four Memory Types & Their Data Shapes | READY FOR REVIEW |
| ELO-V8-CH03 | Chapter 3 | Consolidation & the Forgetting Curve — What Lasts, What Fades | READY FOR REVIEW |
| ELO-V8-CH04 | Chapter 4 | The Sole-Writer Contract, Retrieval & the Memory/Knowledge/World-State Boundary | READY FOR REVIEW |

## Canon reconciliation (REQUIRES DECISION — D-F)

Memory appears in several places. To prevent divergent implementations, ownership is:

| Doc | Owns |
|---|---|
| **Volume VIII (this)** | The **authoritative memory volume**: biological types + data shapes (Ch.2), tiers, timed consolidation faculty + forgetting curve (Ch.3), sole-writer contract + retrieval + boundaries (Ch.4). |
| Volume V Ch.3 | Memory **as a cognitive-architecture faculty** (the 6-layer view + retrieval role in a turn). Compatible sub-view; this volume is the deep spec it maps onto (Ch.4 §4.5). |
| `17_memory_update.md` | Was to be the **write path** spec — currently a **STUB** (`STATUS: PENDING`). The live write path is `memory/vault_layer.py`; Ch.2 §2.2 grounds there directly. **Recommend: retire the reference and make Vol VIII the sole memory root (D-F direction), or write 17_ as prose pointing at vault_layer.** Flag for CA/David. |
| `03_memory_faculty.md` (stub) | Reserved for **retrieval** detail — now specified in Ch.4 §4.2; the stub retires into this volume. |

**D-F RATIFIED (2026-07-27):** the **Memory Faculty owns** persistence, retrieval,
indexing, forgetting, and consolidation. **No other faculty writes permanent memory
directly** — everything else submits a **Memory Candidate**, and the Memory Faculty
decides. Volume VIII is the memory root; V Ch.3 is its cognitive-layer view; the `03`
stub retires into this volume. **D-G:** Working Memory is Executive-owned (Vol VI) —
distinct from this volume's long-term store.

## Definition of Done

- [x] Four biological memory types defined (Ch.1) + their live data shapes/schemas (Ch.2)
- [x] Storage tiers specified against live code — three-tier vault via `vault_layer.py` (Ch.2 §2.2)
- [x] Spot-code addressing + summary/deep schemas + companion stores (facts, memory pack) (Ch.2)
- [x] Consolidation faculty (timed) specified with LIVE parameters — Audit gap #4 (Ch.3)
- [x] Forgetting curve / decay / reinforcement specified with LIVE constants (Ch.3 §3.3–3.4)
- [x] Sole-writer contract (D-F) + Memory Candidate shape + anti-fabrication (Ch.4 §4.1)
- [x] Retrieval path with confidence+source+status + reader chokepoint (Ch.4 §4.2–4.3)
- [x] Memory↔Working-Memory↔World-State↔Knowledge↔Autobiographical-Thread boundaries (Ch.4 §4.4)
- [x] Vol V Ch.3 six-layer reconciliation (mapped, not forked) (Ch.4 §4.5)
- [x] Faculty contract + lifecycle + acceptance tests (all chapters)
- [ ] Wire the single logical MemoryFaculty (candidate-in/decision-out) — PENDING (Ch.4 §4.1.2)
- [ ] Wire reinforce()-on-retrieval so decay has its counterforce — PENDING (Ch.3 §3.4)
- [ ] Resolve `17_memory_update.md` stub (retire vs write) — decision for CA/David
- [ ] Architecture Agent can implement without inventing (pending REVIEW sign-off)
- [ ] Audit can mark COMPLETE
