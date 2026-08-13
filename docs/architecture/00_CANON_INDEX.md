---
document: "eLo OS Engineering Canon — Master Index"
status: LIVING (update after every volume/chapter promotion)
version: 0.1.0
owner: David Charles
architects: Claude (Architecture Agent) · ChatGPT (Chief Architecture Officer)
build_team: Builder Agent (Claude Code) · UI/Avatar Agent
canon_home: docs/architecture/
audit_reference: docs/architecture/ARCHITECTURE_AUDIT.md
last_updated: 2026-08-10
---

> **▶ 2026-08-10 — FULL CANON WRITE-UP (David: "write it all, align it all").** Every volume now has a
> written spec. The previously thin/unwritten volumes were completed to full, code-grounded chapter sets and
> moved to **REVIEW**: **XXI** (Narrative Identity, new) · **VI · VIII · X · XII · XVI · XX · XXII** (core
> brain, now 4 chapters each) · **XXIII–XXVII** (governance deep chapters). **XV** + **XXVIII** were already
> spec-complete. Builds are tracked in `engineering/work_orders/CANON_BUILD_PROGRAM.md` (sequenced BEHIND
> Presentable v1). Ratification is gated on `CANON_REVIEW_QUEUE_2026-08-10.md` — four cross-volume One-Brain
> rulings (world-graph · attention · assemble-order · drift-gate) + David's RESERVED calls. Status cells below
> may lag; the two program docs are the current truth until the next full index cell-pass.

# eLo OS Engineering Canon — Master Index

The Architecture Bible is **27 volumes**. This index is the single map of all of
them: what each volume is, whether it exists in the live system, its priority, and
where its canonical spec lives. It turns "build 27 volumes" into a tracked program.

**Rule:** a volume is not "done" because it was described. It is done only when it
meets the **Definition of Done** (see §Definition of Done) and the Audit can mark it
COMPLETE. Volume V is the reference template for that bar.

> **Read first:** `ARCHITECTURAL_PRINCIPLES.md` — the one-page constitution (enduring principles +
> the 6 Runtime Invariants that should almost never change). Everything below evolves around it.

Status legend: ✅ Live · ⚠️ Partial · 🔴 Future/Not started · 📝 Spec drafted (canon written, implementation pending)


> **⚠ CORRECTION 2026-08-10 (audit):** the "✅ Live (code)" marks on **VII · XI · XIII** were MISLEADING —
> those volumes had **no canon written at all**, and the Build Program exempted them as "verify-only", so
> nothing would ever have caused them to exist. **Now written:** `Volume_VII/` (Executive Cortex, 6 ch) ·
> `Volume_XI/` (Motor Cortex, 2 ch) · `Volume_XIII/` (Presence & Embodied Spatial Intelligence, 5 ch).
> **XVII and XVIII still have no home** — they live inside `Volume_V/06_*` and `07_*` only. **I–IV and XIV
> are stubs.** ADRs are now REAL documents in `docs/architecture/adr/`.


> **✅ 2026-08-10 (later) — ALL VOLUMES NOW WRITTEN.** The remaining stubs were completed: **Volume_I**
> (Philosophy) · **Volume_II** (Cognitive Principles) · **Volume_III** (System Architecture) ·
> **Volume_IV** (The Cognitive Spine — the live turn order finally canonised with file+line citations,
> after months marked "✅ Live" with no canon) · **Volume_XIV** (Plugin Architecture).
> Earlier the same day: VII · XI · XIII · XVII · XVIII. **Every volume I–XXVIII now has written canon.**
> **Two LIVE DEFECTS were found by the audits and are now P0 Builder cards:** WO-096 (desktop perception
> silently dead — swallowed ImportError) and WO-097 (EmbodimentState publishes EMPTY on every
> direct-response turn — spine ordering). Both were invisible because the failures were silent.

---

## The 27 Volumes

### Tier 1 — Foundation (I–III)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| I | Philosophy | ✅ | `prompts/living_presence_spec.txt`, `VISION.md` | One Brain, One Personality |
| II | Cognitive Principles | ✅ | `17_cognitive_principles.md` | How eLo reasons |
| III | System Architecture | ✅ | `16_runtime_contracts.md` | The four runtime contracts + loop |

### Tier 2 — Brain (IV–VII)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| IV | Cognitive Spine | ✅ | `runtime/spine/spine.py` (code) | Faculties in sequence → CognitiveState |
| V | Faculty Contracts & Runtime APIs | ✅📝 | `Volume_V/` (10 ch + CONTRACTS.md) | **IMPLEMENTATION READY — L3 RATIFIED 2026-08-03.** All 10 ch verified; tests green (WO-004/006/007); D-A + D-B accepted. Build-ready. |
| VI | Working Memory & Attention | 📝 | `Volume_VI/` (1 ch) | **Spec'd** — typed WM object + attention competition (gap #3). Reconciles V Ch.1 (D-G) |
| VII | Executive Cortex | ✅ | `runtime/executive.py` (FREEZE_V1_LOCK) | One CognitivePlan per turn |

### Tier 3 — Learning (VIII–X)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| VIII | Memory Architecture | 📝 | `Volume_VIII/` (1 ch) | **Spec'd** — 4 memory types, timed consolidation, forgetting curve (gaps #3/#4). Reconciles V Ch.3 (D-F) |
| IX | Dream Architecture | 📝 | `Volume_IX/` (2 ch) + `faculties/dream/` (code) | **Spec'd** — cycle+symbol engine live; DeepDream + phases spec'd (gap #7) |
| X | Personality Engine | 📝 | `Volume_X/` (1 ch) + `Volume_V/07_*` | **Spec'd** — self-state + unifies self_model/drift (gap #6); traits owned by V Ch.7 |

### Tier 4 — Embodiment (XI–XIII)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| XI | Motor Cortex | ✅ | `avatar/` (code) | Unity bridge, animation, robot signal — UI/Avatar Agent |
| XII | Perception System | 📝 | `Volume_XII/` (1 ch) | **Spec'd** — Perception Faculty (sensation→context), feeds World State (gap #5) |
| XIII | Presence Engine → *Presence & Embodied Spatial Intelligence* (planned evolution) | ✅→📝 | `presence/`, `ambient/` (code) | Idle/silence NOW; evolves to home the Spatial Faculty + embodied-presence philosophy (WO-049 Track B, post-Presentable). Reconciles the CA's 'new Vol XIII' — NOT a new number. |

### Tier 5 — Expansion (XIV–XVI)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| XIV | Plugin Architecture | ✅ | `plugins/` (code) | Registry, dynamic load |
| XV | World Model | ⚠️ | — (needs volume) | **Priority #2** — unified World State, one object all faculties read |
| XVI | Multi-Faculty Coordination | 📝 | `Volume_XVI/` (1 ch) | **Spec'd** — One Brain coordination under one Executive |

### Tier 6 — Research (XVII–XIX)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| XVII | Reflection Engine | 📝 | `Volume_V/06_*` (spec) | Journals/lessons/metrics specced in Vol V Ch.6 |
| XVIII | Self-Evolution | 📝 | `Volume_V/06_*`, `07_*` (spec) | Improvement cycle + versioning specced in Vol V |
| XIX | Artificial Consciousness Research | 📝 | `Volume_XIX/` (1 ch) | **Spec'd** — research programme; findings → ADRs only |

### Tier 7 — Extensions (XX–XXII)

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| XX | Cognitive Economy | 📝 | `Volume_XX/` (1 ch) | **Spec'd** — budgets, tiers 0–3, value-gated escalation |
| XXI | Narrative Identity Engine | ⚠️ | — (draftable from `continuity/`) | Continuous autobiographical thread across sessions |
| XXII | Faculty Genome | 📝 | `Volume_XXII/` (1 ch) | **Spec'd** — genome schema, evolution, 6 laws |

### Tier 8 — Governance (XXIII–XXVII) — named from the Bible

| Vol | Title | Impl. | Canon spec | Notes |
|-----|-------|-------|-----------|-------|
| XXIII | Security & Trust Architecture | 🧩 scaffold | `Volume_XXIII/` | Scope locked (auth, sandboxing, approval gates, threat model) |
| XXIV | Knowledge Architecture | 🧩 scaffold | `Volume_XXIV/` | Scope locked (ontology, KG, retrieval, evidence/citation) |
| XXV | Temporal Cognition | 🧩 scaffold | `Volume_XXV/` | Scope locked (time perception, circadian, planning horizons) |
| XXVI | Creative Intelligence Architecture | 🧩 scaffold | `Volume_XXVI/` | Scope locked (creative domains + Dream integration) |
| XXVII | Engineering Standards & Canon Governance | 🧩 scaffold | `Volume_XXVII/` | Scope locked; mostly consolidates existing `engineering/` |
| XXVIII | Adaptive Learning & Reinforcement | 🧩 scaffold | `Volume_XXVIII/` | Scope locked (RL · skill/motor learning · Significance-vector reward · simulation · policy optimisation · learned affordances · safe online learning). Boundary = ADR-Exec-005 Learning Through Verified Consequences (RL never alters identity/Constitution/Executive/truth; learns only from verified outcomes). Reinforcement & Adaptation Faculty (after Verify); RD-3 = robot instance. Behind Presentable v1. |

> ✅ All 27 volumes are now named and filed. Titles + scope are authoritative from
> `ARCHITECTURE_BIBLE.md` (captured 2026-07-27). XXIII–XXVII are scaffolds (scope locked,
> deep chapters pending).

---

## Roadmap Reconciliation — David's 2026-08-03 plan → canonical volumes

David's Phase-2 roadmap numbers topics **differently** from the canonical 27-volume scheme.
Before assigning any NEW volume number, this maps each roadmap topic onto what already
exists, so we index rather than rewrite. **Most of the "unfinished" list already exists
under another name.**

| Roadmap item (David's #) | Already exists as | State | Verdict |
|--------------------------|-------------------|-------|---------|
| VI · Conversation & Language | *no dedicated volume* — dialogue lives in `prompts/`, `runtime/router/` | code only | 🔴 **GENUINE GAP** — worth a canonical volume |
| VII · Embodiment & Physical Robot | XI Motor Cortex (avatar) + XII Perception + `Output/RD-CAD/` (URDF/STEP) | partial — avatar yes, *hardware layer* not canon | 🟠 **PARTIAL GAP** — physical-robot (motors/nav/safety) under-specified |
| VIII · Unity Presence Runtime | XI Motor Cortex + XIII Presence + `20_one_brain_visualiser.md` + Presence tracker | live (code) | ✅ covered — distributed, not a single volume |
| IX · Memory Runtime | **VIII Memory Architecture** + V Ch.3 + V Ch.5 Significance + `memory/` | spec + partial code | ✅ covered |
| X · Executive Planning | **VII Executive Cortex** + XVI Coordination + V Ch.10 Agency + WO/board + `company_runtime/` | live + spec | ✅ covered |
| XI · Learning System | XVII Reflection + XVIII Self-Evolution (both in **V Ch.6/7**) + XXII Faculty Genome | spec | ✅ covered |
| XII · World Model | **XV The World Model** (Unified Live World State) + XII Perception | spec (priority #2) | ✅ covered |
| XIII · Social Intelligence | **V Ch.8 Intent & Relationship** + `relationship_faculty` + XXIII trust/boundaries | spec + code | 🟠 **PARTIAL** — exists, not consolidated into one volume |

### Genuine gaps (the ONLY net-new authorship the roadmap implies)

1. 🔴 **Conversation & Language Runtime** — no canonical home; dialogue/turn-taking/repair
   currently live implicitly in prompts + router. This is the one clear missing volume.
2. 🟠 **Physical-Robot Embodiment** — avatar motor cortex (XI) is canon; the *hardware* body
   (actuators, navigation, safety interlocks) is only in RD-CAD engineering docs, not a volume.
3. 🟠 **Social Intelligence** — real but scattered (V Ch.8 + relationship code + XXIII); could
   be consolidated into a standalone volume if it earns one.

**Everything else on the roadmap already exists — it needs indexing, not writing.**
Recommendation stands: promote V, keep this index current, author only the gaps above.

---

## Whole-Canon Build Queue (by Audit priority)

The Architecture Audit gives the critical-gap priority order. Translated to volume builds:

```
DONE (canon drafted):
  [x] Volume V   — Faculty Contracts & Runtime APIs   (Faculty Bus / envelope = Audit gap #1)
                   → also drafts X (personality), XVII (reflection), XVIII (self-evolution)

NEXT (priority order from Audit gaps):
  [ ] Volume XV  — World Model / Unified World State    (Audit gap #2)
  [ ] Volume VI  — Working Memory & Attention           (Audit gap #3)
  [ ] Volume VIII— Memory Architecture (consolidation)  (Audit gap #4)
  [ ] Volume XII — Perception System                    (Audit gap #5)
  [ ] Volume X   — Personality Engine (ratify Vol V Ch.7 into standalone volume, gap #6)

THEN (future / research / extensions):
  [ ] Volume XVI  — Multi-Agent Coordination
  [ ] Volume XXI  — Narrative Identity Engine
  [ ] Volume XXII — Faculty Genome
  [ ] Volume XX   — Cognitive Economy
  [ ] Volume XIX  — Artificial Consciousness Research
  [ ] Volumes XXIII–XXVII — pending titles/scope

ALREADY LIVE (canon = code; write spec only if formalisation needed):
  I, II, III, IV, VII, IX, XI, XIII, XIV
```

**One volume = one build cycle.** Each new volume follows Volume V's discipline:
research the live system → draft chapters → each chapter gets contract + state
machine + envelope + acceptance tests → REVIEW → IMPLEMENTATION READY → build.

---

## Definition of Done (applies to EVERY volume)

Inherited from `Volume_V/00_Metadata.md`. A volume advances DRAFT → REVIEW →
IMPLEMENTATION READY → COMPLETE only when:

- [ ] Every chapter received and filed
- [ ] Every faculty contract defined (typed inputs / outputs / confidence / failure modes)
- [ ] Every state machine defined (universal lifecycle per `Volume_V/CONTRACTS.md` §3)
- [ ] Every API / message envelope defined (nine-field wire format per `CONTRACTS.md` §2)
- [ ] Every failure mode documented (graceful degradation)
- [ ] Acceptance tests written for each chapter (functional / stability / integration)
- [ ] The Builder Agent can implement without inventing anything
- [ ] The Audit can mark COMPLETE

---

## Status Roll-up

```
✅ Live (canon = working code):        9  volumes  (I, II, III, IV, VII, IX, XI, XIII, XIV)
📝 Spec drafted (canon written):       11 volumes  (V, VI, VIII, IX, X, XII, XV, XVI, XIX, XX, XXII) [+ XVII, XVIII inside V Ch.6]
🧩 Scaffold (scope locked, chapters pending): 5 (XXIII, XXIV, XXV, XXVI, XXVII)
⚠️ Partial (draftable next):           1  volume   (XXI — from continuity/)
   Authoritative source:               ARCHITECTURE_BIBLE.md (v1.0, all 27 volumes) · master map: 19_cognitive_plan_architecture.md
   Embodiment/observability:           20_one_brain_visualiser.md (the live "brain display" — captured from commits 2026-07-27)
──────────────────────────────────────────────────────
All 27 volumes named & filed. Governance: DECISION_LOG.md (D-A…G ratified), CONTRACTS.md, work_orders/DISPATCH_BOARD.md.
──────────────────────────────────────────────────────
Total:                                 27 volumes
```

---

```
Master Canon Index
Status: LIVING
Files: 00_CANON_INDEX.md
Covers: all 27 volumes (I–XXII mapped from Audit; XXIII–XXVII pending titles)
Next build: Volume XV — Unified World State (Audit priority #2)
Open: 5 unnamed volumes need titles/scope
```

READY FOR REVIEW

> **Planned faculty:** Spatial Faculty (desktop/world navigation, body-fit, path planning; Executive asks "how do I get there?") — agreed architecture for WO-049 Track B; authored as a Volume-V faculty chapter when scheduled (post-Presentable v1). — 2026-08-04
