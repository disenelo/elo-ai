---
volume: IX
title: "Dream Architecture — Offline Symbolic Recombination"
status: REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
source: "Canonicalised from ChatGPT brain/dream design chat (2026-07-26) + live code"
implementation: PARTIAL (faculties/dream/ live: cycle, symbol engine, phases, trigger, wake, journal; DeepDream image + consolidation-reinforce wire + creative-spark emit + Executive-invoked entry PENDING)
audit_status: OPEN
canonical_path: docs/architecture/Volume_IX/
dependencies:
  - Volume V (CONTRACTS.md; Ch.4 Emotion, Ch.5 Significance, Ch.6 Reflection, Ch.7 Personality, Ch.9 Creative Imagination)
  - Volume VIII (Memory Architecture — Ch.3 Consolidation/forgetting: dreams reinforce verified records)
  - Volume XXVI (Creative Intelligence — Ch.3 Dream Integration: two-way creative bridge, shared symbol vocabulary)
  - Volume III (runtime contracts — dream runs at low Executive load)
priority: "Audit gap #7 (LOW) — dream image generation; + dream phases + imagined-speech firewall"
last_review: 2026-08-10
next_review: TBD
---

# Volume IX — Dream Architecture

Offline cognitive recombination: when the Executive is idle, eLo replays important
memories, unfinished goals, strong emotions, and recurring symbols into symbolic dream
narratives — then integrates the insight back into memory and personality. Dreaming is
part of the learning loop, not a decorative image generator.

## Chapter Build Queue

| ID | Chapter | Title | Status |
|----|---------|-------|--------|
| ELO-V9-CH01 | Chapter 1 | The Dream Faculty (cycle, as-built) | READY FOR REVIEW |
| ELO-V9-CH02 | Chapter 2 | Symbol Engine, Dream Phases & DeepDream Pipeline | READY FOR REVIEW |
| ELO-V9-CH03 | Chapter 3 | The Circadian Trigger & Wake Integration | READY FOR REVIEW |
| ELO-V9-CH04 | Chapter 4 | Dream Integration & the Imagined-Speech Firewall | READY FOR REVIEW |

The volume is complete at four chapters: the **cycle** (Ch.1), the **symbolic + visual
machinery** (Ch.2), the **rhythm** — when eLo dreams and how it wakes (Ch.3), and the
**outbound integration + epistemic firewall** — how dreams feed Memory and Creativity
without ever being asserted as fact (Ch.4). No further chapters are implied by the scope.

## Implementation status (from Audit + code)

- **Live:** `faculties/dream/dream_faculty.py` (6-step cycle; `should_dream` 3-signal trigger;
  NREM/REM phase gating by idle window; `wake_from_dream` self-state restoration; NREM
  `memory_refs` + `_extract_personality_proposal`; enriched journal),
  `faculties/dream/symbol_engine.py` (symbol library, source-weighting).
  `self/dream_journal.jsonl` (append target, created on first dream). Unity sleep signal via
  `state.mode="dreaming"` (`blender_bridge/state_writer.py`). `tools/image_gen_agent.py`
  (`generate` → writes `hud_image`) present.
- **Gaps this volume specs (PENDING):** (1) **DeepDream/image pipeline** wired end-to-end —
  Audit gap #7 (Ch.2); (2) **consolidation `reinforce()` edge** — dream `memory_refs` not yet
  strengthening vault records (Ch.4 §4.3, mirrors Vol VIII §3.4); (3) **`creative_spark` emit**
  — REM insight not yet emitted to the Creative faculty (Ch.4 §4.4); (4) **Executive-invoked
  dream entry** — trigger still called by the idle path, not the Executive's low-load decision
  (Ch.3 §3.1.1).

## Invariants this volume holds

- **One Brain** — Dream is one faculty of one mind; it is *invoked* at low Executive load, never
  a rogue background daemon that seizes control (Ch.3 §3.1.1).
- **Every faculty is asked by the Executive** — the trigger grants *permission*; the Executive
  decides to dream. Dreaming always yields to presence (Ch.3 §3.1.3).
- **Verified Speech — dreams are imagined, flagged as such.** A dream is `imagined` end-to-end;
  eLo may assert the *occurrence* ("I dreamed…") but never the *content* as fact about the world,
  a memory of a real event, or an applied change to itself (Ch.4 §4.1, the imagined-speech
  firewall). Dreams reinforce already-verified memory and emit *proposals/sparks* that downstream
  gates must still accept — eLo can never learn a thing it merely imagined (Ch.4 §4.2).

## Numbering note (REQUIRES DECISION — D-E)

The live code headers cite **"Architecture Bible Volume IV: Dream Faculty."** The
Architecture Audit and `00_CANON_INDEX.md` map Dream to **Volume IX**. This volume follows
the Audit/index (**IX**). Reconcile the code header vs the Bible numbering, or confirm
which is canonical.

## Definition of Done

- [x] Dream cycle documented as-built (trigger → symbols → narrative → insight → journal → wake)
- [x] Symbol engine + weighting specified
- [x] Dream phases specified (new)
- [x] DeepDream image pipeline specified (new — Audit gap #7)
- [x] Consolidation + personality coupling specified
- [x] Circadian trigger (3-signal) + idle-window phase gating + wake integration specified (Ch.3)
- [x] Imagined-speech firewall specified — dreams feed Memory + Creativity + Personality without being asserted as fact (Ch.4)
- [x] Faculty contract + lifecycle + envelope + acceptance tests (all four chapters)
- [ ] Architecture Agent can implement the gaps without inventing (pending REVIEW)
- [ ] Audit can mark COMPLETE
