---
chapter: 2
title: "The Working-Memory Lifecycle — Seed, Update, Evict, Carry"
volume: VI
status: READY FOR REVIEW
version: 0.1.0
owner: David Charles
architect: Claude (Lead Architect)
implementation: PENDING
audit_status: OPEN
dependencies:
  - Volume_VI/01_Working_Memory_and_Attention.md (the typed WM object — this is its lifecycle)
  - Volume_V/01_Cognitive_Core.md §4 (the in-turn frame buffer — D-G reconciliation)
  - Volume_V/CONTRACTS.md §3 (universal faculty lifecycle)
  - Volume_VIII/01_Memory_Architecture.md (Long-Term Memory — the boundary WM never crosses)
  - Volume_V/01 §5 (significance → pinning)
---

# Chapter 2: The Working-Memory Lifecycle

## 2.0 Purpose

Chapter 1 defines *what* Working Memory is — the typed, bounded object eLo holds in
mind (`WorkingMemory` with `frames`, `active_goals`, `interruptions`, `open_threads`,
`pinned`, `rolling_summary`, `attention`). This chapter defines its **life**: how it
comes into being at the start of a session, how it changes across a turn and across
turns, how it stays bounded without losing what matters, and where it *ends* — the
line it never crosses into Long-Term Memory (Vol VIII).

Working Memory is not a store; it is a **moving window**. Its correctness is a
question of lifecycle, not of shape. A typed object with a broken lifecycle still
drifts. This chapter is the discipline that keeps the window honest.

## 2.1 Principle

- **Working Memory has a birth, a life, and a boundary.** It is seeded (birth),
  updated and evicted every turn (life), and it never writes itself into permanent
  memory (boundary — that is Vol VIII's job through the Significance Engine).
- **Bounded means the oldest *unpinned* frame leaves, never the most important.**
  Eviction is by age among unpinned frames only; pinned frames (Significance ≥ HIGH,
  V Ch.5) are protected. Overflow compresses into `rolling_summary`; it never grows
  the window.
- **Continuity is seeded, not remembered.** Turn 1 of a session does not "recall" —
  it is *handed* a continuity summary and open threads from the last session. WM
  starts warm because continuity fills it, not because WM persists.
- **Executive-owned (D-G).** The lifecycle is executive state. Faculties propose
  candidates (percepts, goals, interruptions); the Executive holds the WM object and
  the transitions below apply to *its* state, not to any faculty's private store.

## 2.2 The Lifecycle States

Working Memory moves through four operations per session. These are operations on the
object, distinct from (and running inside) the faculty's universal lifecycle
(CONTRACTS.md §3).

```
SEED      once per session start / turn 1
   │        seed_working_memory(current_task, continuity_summary, open_threads)
   ▼
UPDATE    once per turn (top of turn, before the Executive reasons)
   │        update_working_memory(wm, new_frame)  → append the turn's frame
   ▼
EVICT     inline within UPDATE, only when len(frames) > capacity
   │        drop oldest UNPINNED frame → fold its gist into rolling_summary
   ▼
CARRY     at session close
            surviving open_threads + rolling_summary → continuity/ (Vol VIII handles LTM)
```

**Note (grounded):** `runtime/working_memory.py` (WO-008) already implements
`seed_working_memory()`, `update_working_memory()` (with inline eviction), and
`run_attention_competition()`. The module exists but is **imported nowhere** — SEED,
UPDATE, and EVICT are built; the wiring into the turn (Ch.4) is PENDING; CARRY is not
yet implemented.

## 2.3 SEED — Continuity Fills the Window

```
seed_working_memory(current_task="", continuity_summary="", open_threads=[], capacity=12)
  → WorkingMemory(
        current_task,
        frames = (seed_frame,) if continuity_summary else (),   # one frame carrying "last time…"
        open_threads = tuple(open_threads),
        attention = AttentionState(budget=0.5, mode="reactive"),
        capacity)
```

**Rules (MUST):**

- Seeding is the **only** way continuity enters WM. WM does not persist between
  sessions; the continuity summary and the surviving `open_threads` from CARRY (§2.6)
  are what make turn 1 feel like a continuation ("last time we were…").
- The seed frame is `significance = 0.5`, `pinned = False` — continuity is context, not
  a protected fact. If it matters permanently it is already in Long-Term Memory
  (Vol VIII) and will be re-surfaced there, not held in WM.
- Cold start (no continuity available) seeds an **empty** window with a neutral
  `AttentionState`. WM never fabricates a prior session (aligns with Truth-before-fluency
  and the anti-fabrication discipline).

## 2.4 UPDATE — One Frame Per Turn

Each turn appends exactly one `CognitiveFrame` (the turn's thought/observation) to
`frames`, at the top of the turn, before the Executive reasons.

```
update_working_memory(wm, new_frame) -> WorkingMemory (new, frozen):
    frames' = wm.frames + (new_frame,)
    pinned' = wm.pinned + (new_frame.frame_id if new_frame.pinned)
    while len(frames') > capacity:   → EVICT (§2.5)
    return WorkingMemory(... frames', pinned', rolling_summary' ...)
```

**Rules (MUST):**

- **Append-only within a turn; the result is a new frozen object.** WM is not mutated
  in place — each UPDATE returns a fresh frozen `WorkingMemory`, matching the
  frozen-after-assembly contract (V Ch.1 Contract 2). Interpretation reads; reasoning
  produces the next object.
- A frame's `pinned` flag is set by the Significance Engine (V Ch.5): `significance ≥
  HIGH → pinned = True`. WM does not decide significance; it *honours* it.
- `current_task`, `active_goals`, and `interruptions` are carried forward unchanged by
  UPDATE unless the Executive revises them. WM tracks them; it does not author goals
  (Agency — V Ch.10 — proposes goals; the Executive commits them).

## 2.5 EVICT — Compress, Never Grow

When `len(frames) > capacity` (default 12):

```
evict_idx = first index whose frame_id ∉ pinned          # oldest UNPINNED
if evict_idx is None:  break            # all pinned → allow transient overflow (pinned safety)
evicted = frames.pop(evict_idx)
rolling_summary += " | " + gist(evicted)                 # compressed to ≤ 60 chars/frame
```

**Rules (MUST):**

- Only **unpinned** frames are evictable. Eviction is oldest-first among them.
- If every frame is pinned, the window is **allowed to overflow transiently** rather
  than drop a protected frame ("pinned safety"). This is a deliberate bias: losing a
  Significance-HIGH frame is worse than a briefly oversized window. (Open question
  §2.8: cap on transient overflow before forcing summarisation of the oldest pinned.)
- The evicted frame's gist folds into `rolling_summary` — the window's compressed
  memory of what left. `rolling_summary` is a lossy gist, **not** a retrieval index;
  anything needing recall belongs in Long-Term Memory (Vol VIII), not here.

## 2.6 CARRY — The Boundary to Long-Term Memory

At session close, WM does **not** write to Long-Term Memory. It hands two things to the
continuity layer:

```
session_close(wm):
    unresolved = [t for t in wm.open_threads]      # topics still open
    gist       = wm.rolling_summary                # window's compressed trace
    → continuity/ (next-session SEED input)
    # Long-Term consolidation is SEPARATE: the Significance Engine + Reflection
    #   (Vol V Ch.5/Ch.6) decide what of this session becomes LTM (Vol VIII).
    #   WM never calls the LTM writer. (D-F, D-G.)
```

**Rules (MUST):**

- **WM never writes Long-Term Memory.** The only permanent-memory writer is the Memory
  Faculty via the Significance Engine (Memory Ownership invariant; D-F). WM's CARRY
  feeds *continuity seeding* only.
- What survives to the next session's SEED is: unresolved `open_threads` + the
  `rolling_summary` gist + `current_task` if still active. Everything else is dropped —
  a session's working set is meant to be forgotten unless it earned LTM through
  Significance.

## 2.7 Faculty Lifecycle Binding

Universal lifecycle (CONTRACTS.md §3). Mapping to the four WM operations:

```
INITIALISE → register WM readers; attach to continuity + Significance
READY      → subscribed, holding the current frozen WorkingMemory
ACTIVE     → per turn: UPDATE (append frame) → EVICT if over cap → run attention
             competition (Ch.1 §1.3) → freeze into CognitiveState
   └─ fault ─► ERROR → RECOVERY (through READY): re-SEED from continuity; if none,
             cold-start neutral window; never crash the turn
WAITING/SLEEPING → CARRY at session close; weight-tuning (Ch.3) in integration window
```

- SEED corresponds to INITIALISE / first ACTIVE; UPDATE+EVICT to each ACTIVE turn;
  CARRY to SLEEPING (session close). Weight-tuning of the attention competition
  (novelty/importance/urgency) is integration-window work (Ch.3, driven by Reflection
  V Ch.6) — **never** on the response path.

## 2.8 Acceptance Tests

```
FT-1  Seed from continuity        Given a continuity summary, When SEED runs, Then WM has one seed frame (sig 0.5, unpinned) and the carried open_threads.
FT-2  Cold-start seed             Given no continuity, When SEED runs, Then WM has zero frames and a neutral AttentionState; no fabricated prior session.
FT-3  Append one frame per turn   Given a turn, When UPDATE runs, Then exactly one frame is appended and a NEW frozen WorkingMemory is returned (old not mutated).
FT-4  Evict oldest unpinned       Given capacity 12 and a 13th unpinned frame, Then the oldest unpinned frame is evicted into rolling_summary; pinned frames untouched.
ST-1  Pinned safety               Given all 12 frames pinned and a 13th arrives, Then the window overflows transiently rather than drop a pinned frame.
ST-2  Rolling summary is lossy     Given evicted frames, Then rolling_summary holds a gist (≤60 chars/frame), not a retrievable copy.
ST-3  No LTM write from WM         Given session close, Then WM writes only to continuity; it never calls the Long-Term Memory writer (Vol VIII / D-F).
IT-1  Carry → next seed            Given unresolved open_threads at close, When the next session seeds, Then those threads reappear in the new WM (continuity closes the loop).
```

## 2.9 Wiring to Live Anchors

- `runtime/working_memory.py` — `seed_working_memory()` (SEED), `update_working_memory()`
  (UPDATE + inline EVICT), `_summarise_evicted()` (gist), `CognitiveFrame.pinned`
  (Significance protection). **Built; imported nowhere — CARRY and turn-wiring PENDING.**
- `continuity/` — SEED input source and CARRY output sink (session-to-session handoff).
- `memory/significance_engine.py` — sets `pinned` (Significance ≥ HIGH). Note FC-2:
  the live engine scores **9 dimensions**, not the 5-term draft (reconcile at V Ch.5).
- Long-Term consolidation path (Vol VIII / D-F) — **separate** from WM; WM never calls it.

## 2.10 Open Questions (for CA / David)

```
REQUIRES DECISION
  Q2-a  Transient-overflow cap: how many pinned-only overflow frames before the oldest
        pinned is force-summarised? (Ch.1 currently allows unbounded pinned overflow.)  [INVENTED — flag]
  Q2-b  rolling_summary compression: fixed 60-char gist (current code) vs a model-summarised
        gist at session close. Fixed is deterministic; model gist is richer but non-verified.
  Q2-c  CARRY vs consolidation timing: does CARRY run before or after the Significance/Reflection
        integration window at session close? (Ordering affects what open_threads survive.)
```

---
**Status: READY FOR REVIEW** — the WM object's full lifecycle (SEED · UPDATE · EVICT · CARRY),
bounded to Vol VIII at the LTM boundary and to V Ch.1 §4 as its in-turn view (D-G). Grounded in
`runtime/working_memory.py`; wiring and CARRY marked PENDING. Three open questions flagged.
