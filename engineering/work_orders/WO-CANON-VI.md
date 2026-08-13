# WO-CANON-VI — Working Memory & Attention: wire the WM object + resolve the two-attention design

**Owner:** Builder (eLo OS — `runtime/working_memory.py` + `runtime/spine/` + `runtime/executive.py`).
**Priority:** P2 — Horizon-2 (post-Presentable v1), Tier A. **Status:** QUEUED — **gated on alignment ruling B**
(CANON_REVIEW_QUEUE 2026-08-10, item 2). Cannot dispatch the Ch.4 wiring until ruling B lands. **Closes:** Audit gap #3.

**Canon refs:** Volume VI — Ch.1 `01_Working_Memory_and_Attention.md`, Ch.2 `02_Working_Memory_Lifecycle.md`,
Ch.3 `03_Attention_and_Salience.md`, Ch.4 `04_Wiring_Working_Memory_Into_The_Turn.md`. Decision Log D-G (Executive owns
Working Memory). Reconcile with Vol V Ch.1 §4/§5 (FC-2: live Significance scores 9 dimensions, not the 5-term draft).

## Problem / Goal
`runtime/working_memory.py` (WO-008) already implements the typed WM object + attention competition
(`seed_working_memory`, `update_working_memory` with inline evict, `run_attention_competition`, `AttentionState`,
`AttentionCandidate`, `_score`, `_budget_to_mode`, `_summarise_evicted`) — but it is **imported nowhere**. And two
attention mechanisms coexist: `core/attention.py` (a wired memory-relevance filter) vs the WM competition (built,
unwired). Goal: make the WM competition the single attention driver, wire the WM object into the turn +
CognitiveState + Executive, and implement session-close CARRY.

## Scope to DoD (grounded in Ch.1–Ch.4)
- **Resolve two-attention design (ruling B / D-VI-1) — build side:** once ruling B ratifies the WM competition as the
  **single attention driver**, re-cast `core/attention.py::compute()` as the **"Memory Relevance Filter"** — a supplier
  of candidates + emotional/urgency signal, NOT a second attention authority. Until ratified, treat `core/attention.py`
  as candidate/signal supplier only. This decision determines which slot the Executive trusts and **blocks Ch.4 wiring**.
- **Wire the WM object into the turn (`runtime/spine/spine.py`):** run WM UPDATE + attention competition at the TOP of
  the turn, before faculty activation and before the Executive; then FREEZE into CognitiveState; never touched again
  that turn. Mode may gate faculty activation (fewer faculties in `peripheral`).
- **CognitiveState slot (`runtime/contracts.py::CognitiveState`):** add `working_memory: WorkingMemory` and
  `attention_state: AttentionState` (attach via `runtime/cognitive_snapshot.py` `build_snapshot`, WO-052). Do NOT remove
  legacy fields (`attention_scores`, `emotional_context`, `momentum`, `valence`) in the same step — migrate incrementally
  with parity asserts; make `momentum`/`valence`/`emotional_context` inputs to the competition. De-duplicate
  `open_threads`: `CognitiveState.open_threads` and `WorkingMemory.open_threads` become the same list, WM authoritative.
- **Attention as explicit competing weights (keep WO-008 math):** `score = w1·novelty + w2·importance + w3·urgency`
  (defaults 0.35/0.40/0.25, sum 1.0). Budget→mode: `<0.15` peripheral / `0.15–0.60` reactive / `≥0.60` deliberative.
  Ties within ε=0.01 held (`tied=True`), not collapsed. Distress candidate wins regardless of score and forces
  `deliberative` (bypass, not a high score; not tunable). Attention authors nothing — reads novelty (`core/pattern_observer.py`),
  importance (`memory/significance_engine.py` pin + goal tier + relevance bucket), urgency (World State time/deadlines +
  emotional_context + interruptions).
- **Lifecycle SEED/UPDATE/EVICT/CARRY:** SEED once at session start from `continuity/` (cold start = empty window +
  neutral AttentionState, no fabricated prior session). UPDATE appends exactly one frame/turn, returns a **new frozen**
  WorkingMemory (no in-place mutation). EVICT inline when `len(frames) > capacity` (12), oldest **unpinned** first, gist
  ≤60 chars into `rolling_summary`; all-pinned → transient overflow (pinned safety). **Build CARRY (not yet implemented):**
  at session close hand `open_threads` + `rolling_summary` (+ active `current_task`) to `continuity/` only. **WM never
  writes LTM** — consolidation to Vol VIII runs via Significance/Reflection.
- **Executive contract (`runtime/executive.py`, D-G):** reads WM + `attention_state`, decides once; goal/task revisions
  apply to NEXT turn's SEED/UPDATE, never mutate the current frozen object; a held tie surfaces as genuine ambiguity.
  Weight tuning only in the integration window (Reflection, V Ch.6), re-normalised to ≈1.0, behind the identity-continuity
  guard; distress override not tunable.

## Definition of Done
- WM UPDATE + single attention competition run at top-of-turn, freeze into CognitiveState, Executive decides once from
  the frozen slice; `core/attention.py` demoted to relevance-filter supplier (per ruling B).
- WM bounded at 12, evicts oldest unpinned into rolling_summary, pinned survive; ties held; distress overrides.
- CARRY hands threads/summary to continuity at session close; WM never writes LTM.
- Audit can mark Vol VI COMPLETE.

## Tests to write (`tests/test_canon_vi_working_memory.py`)
- Ch.1: bounded WM (evict oldest unpinned), attention competition (highest score wins), budget→mode (0.1→peripheral),
  distress overrides, ties held, typed not free-form (reject arbitrary key), WM+attention→Executive frozen.
- Ch.2: seed from continuity, cold-start seed (no fabricated prior), append one frame/turn (new frozen), evict oldest
  unpinned, pinned safety, rolling summary lossy ≤60 chars, no LTM write, carry→next seed.
- Ch.3: highest score wins, weights sum to one, budget→mode, ties held, distress overrides, attention authors nothing,
  **IT-1 one driver not two [gated on ruling B]**, peripheral→quiet.
- Ch.4: WM before Executive, one slice read many (no re-run), slot present, no downstream re-decide, threads not
  duplicated, world-in/focus-out, LTM boundary (CARRY→continuity only), mode gates activation.

## Dependencies + blocked-by
- **Blocked by:** **alignment ruling B** (two attention mechanisms) — CA call; gates all Ch.4 wiring. Also runs behind
  Presentable v1 and behind WO-CANON-XV (World State supplies candidates/urgency).
- Cross-volume: Vol V Ch.1 §4/§5, Ch.4 (distress), Ch.5 (significance/pinning — reconcile FC-2 9-dimension score);
  Vol VIII (LTM boundary WM never crosses); Vol XII (perception candidates). D-G RATIFIED (Executive owns WM).
- **Gate:** ruling B on the CANON_REVIEW_QUEUE (CA). Not David L3.

## Lane
Builder (Python — wiring `runtime/working_memory.py` into spine/contracts/executive + CARRY; recast `core/attention.py`).
Architect coordinates + relays ruling B when it lands.
