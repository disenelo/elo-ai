---
chapter: 1
title: "The Dream Faculty — Offline Symbolic Recombination"
volume: IX
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Architecture Agent)
source: "ChatGPT brain/dream chat 2026-07-26 + faculties/dream/dream_faculty.py"
implementation: PARTIAL (cycle live; phases + image pending)
audit_status: OPEN
dependencies:
  - Volume V/CONTRACTS.md; Ch.5 Significance; Ch.6 Reflection; Ch.7 Personality
  - Volume VIII Memory Architecture (source memories + consolidation target)
---

# Chapter 1: The Dream Faculty

## 1.0 Purpose

The Dream Faculty performs **offline cognitive recombination**. When the Executive is
idle, eLo replays high-value memories, unfinished goals, strong emotions, and recurring
symbols, recombines them into a short **symbolic narrative**, extracts one **insight**,
and integrates that insight back into self-state and memory.

> The dream isn't the image. The image is only the visual output. The actual dream is the
> **association graph** — memory → symbol → narrative → insight. (Design source: the
> brain/dream chat.)

This is **not** the ambient engine. Ambient decides speak/emotion/move in the moment;
the Dream Faculty synthesises meaning offline. It runs in the integration window, never
the response path — dreaming is a learning act (`17_cognitive_principles.md`:
*reflection produces growth*).

Live in `faculties/dream/dream_faculty.py`. This chapter documents it as-built and binds
it to the canon contracts.

## 1.1 The Dream Cycle (as built)

```
1. Trigger check   idle ≥ DREAM_IDLE_THRESHOLD (600s) AND cooldown ≥ DREAM_COOLDOWN (3600s)
                   AND Executive load low  (should_dream(elo_self, idle_seconds, energy_history))
        ↓
2. Symbol mapping  memories + inner events → archetypes   (symbol_engine.map_to_symbols — Ch.2)
        ↓
3. Narrative       LLM: 2–3 symbolic sentences from the weighted symbol set
        ↓
4. Insight         one-line integration → feeds back into EloSelfState
        ↓
5. Journal         append to self/dream_journal.jsonl
        ↓
6. Wake            EloSelfState updated with rest + insight; mode → idle
```

Unity coupling: `server.py` writes `state.mode="dreaming"` before the cycle and
`"idle"` after; the Unity/Avatar agent reads `state.mode` to trigger the sleep animation.
This module only writes the signal (respects the embodiment boundary — `CO_WORKING_GUIDE.md §4`).

## 1.2 DreamResult

```
DreamResult:
  symbols:       [ {name, meaning, weight} ]   # from the symbol engine
  narrative:     str        # 2–3 symbolic sentences
  insight:       str        # one-line integration
  journal_entry: dict       # persisted record (see §1.4)
  timestamp:     float
```

## 1.3 Trigger Discipline

```
should_dream(elo_self, idle_seconds, energy_history) is True only when:
  - cooldown elapsed (≥ 3600s since last dream)
  - idle_seconds ≥ 600
  - Executive load is low (no active turn; energy_history indicates rest)
```

**Rules (MUST):** dreaming never preempts a turn; if input arrives mid-cycle, the cycle
yields and `mode` returns to idle. Dreaming is opportunistic, bounded, and rate-limited.

## 1.4 Dream Journal

Append-only `self/dream_journal.jsonl`. Each entry (design-enriched, per the chat):

```
{ "dream_id", "timestamp", "theme", "symbols":[...], "narrative", "insight",
  "memory_refs":[...], "personality_delta_proposed": null | {trait, direction},
  "image_ref": null | path }        # image_ref filled once DeepDream pipeline lands (Ch.2)
```

## 1.5 Faculty Contract

```
Faculty:
  name:            DreamFaculty
  version:         1.0.0
  purpose:         Recombine high-value memories/emotions/goals into symbolic narratives
                   and integrate the insight — offline, at low Executive load.
  contributes_to:  ExecutionReport-adjacent (writes self-state + memory via integration)
  runs_in:         integration-window (idle) — NEVER response-path

Inputs:
  - type: elo_self_state    source: self/elo_self_model.py            required: true
  - type: idle_signal       source: server.py idle timer              required: true
  - type: high_value_memories source: Memory (Vol VIII) + Significance (Ch.5)   required: true
  - type: recurring_symbols source: symbol_engine (Ch.2)              required: true

Outputs:
  - type: dream_result      destination: self/dream_journal.jsonl + EloSelfState
  - type: dream_insight     destination: Consolidation (Vol VIII) + Personality (Ch.7, proposal)
  - type: sleep_signal      destination: blender_state.json state.mode="dreaming" (via server.py)

Dependencies:
  - faculty: MemoryArchitecture (Vol VIII, hard — source + consolidation), SignificanceEngine (Ch.5, hard),
             PersonalityEvolution (Ch.7, hard for any trait-affecting insight — validated)

Failure Modes:
  - condition: LLM narrative unavailable   fallback: store symbol graph only; skip narrative; still journal.
  - condition: input arrives mid-cycle     fallback: abort cycle, mode→idle, no partial journal.
  - condition: insight would change personality   fallback: emit a proposal to Ch.7 (validated); never self-apply.
  - condition: no high-value memories       fallback: do not dream (nothing to recombine).
```

## 1.6 Faculty Lifecycle

Universal lifecycle (CONTRACTS.md §3), integration-window centred: `ACTIVE` (idle-watching)
→ trigger → `PROCESSING` (symbols→narrative→insight) → `LEARNING` (journal + self-state) →
`VALIDATION_REQUIRED` (any personality delta → Ch.7) → `UPDATING` → `STABLE` → `ACTIVE`.
An incoming turn always preempts back to `ACTIVE` (dreaming yields to presence).

## 1.7 Message Envelope Binding

Per CONTRACTS.md §2. `sender: DreamFaculty`; `priority: low` (never preempts); `payload.type:
dream_result | dream_insight`; a personality-affecting insight is addressed to
`PersonalityEvolution` and MUST NOT self-apply (identity-continuity gate, Ch.7).

## 1.8 Acceptance Tests

```
FT-1  Trigger discipline     Given idle 600s + cooldown elapsed + low load, Then a cycle runs; else it does not.
FT-2  Association graph       Given today's memories, Then symbols are mapped and a 2–3 sentence narrative is produced.
FT-3  Journal append          Given a completed cycle, Then one entry appends to dream_journal.jsonl with insight.
ST-1  Yields to presence       Given input mid-cycle, Then the cycle aborts, mode→idle, no partial journal.
ST-2  No unvalidated identity  Given a personality-affecting insight, Then it routes to Ch.7 validation; never self-applied.
ST-3  Rate-limited             Given a dream just ran, Then no new dream within DREAM_COOLDOWN.
IT-1  Dream → consolidation    Dream insight → Consolidation (Vol VIII) strengthens the reinforced memory; self-state gains rest+insight.
```

## 1.9 References
- `faculties/dream/dream_faculty.py`, `faculties/dream/symbol_engine.py`, `self/dream_journal.jsonl`.
- Chapter 2 (Symbol Engine, phases, DeepDream). Vol VIII (Memory/consolidation), V Ch.5/6/7.
- `ARCHITECTURE_AUDIT.md` Vol IX (image-gen + phases gaps).

---
**Status: READY FOR REVIEW** — as-built cycle + contract/lifecycle/envelope/tests. (Canonicalised from the brain/dream chat.)