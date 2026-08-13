# WO-CANON-X — Personality Engine: put drift behind a validation gate + reconcile the trait model with V Ch.7

**Owner:** Builder (eLo OS — `self/`, `memory/personality_drift.py`, `runtime/spine/`). **Priority:** P2 — Horizon-2
(post-Presentable v1), Tier A. **Status:** QUEUED — **gated on alignment ruling D** (CANON_REVIEW_QUEUE 2026-08-10,
item 4) and the RESERVED trait-model decisions D-X3-1/2/3 (**David L3 + CA**, identity-adjacent). **Closes:** Audit gap #6.

**Canon refs:** Volume X — Ch.1 `01_SelfState_Trait_Unification.md`, Ch.2 `02_The_SelfState_Model.md`, Ch.3
`03_Drift_Management_vs_Healthy_Growth.md`, Ch.4 `04_Personality_In_The_Moment.md`. **Authoritative for traits:**
Vol V Ch.7 (`PersonalityVector`, §7.5 validation gate, §7.6 versioning + `identity_hash`) — Vol X does NOT restate it.
ADRs: Exec-006 (The Moment), Exec-005 (learning from consequences), Exec-004 (Situated Self), Exec-002/001.

## Problem / Goal
Two LIVE personality systems run unaware of each other: `self/elo_self_model.py` (fast affective layer:
mood/curiosity/satisfaction/inner_events) and `memory/personality_drift.py` (slow drift: `tone_profile`/
`interaction_bias`, which **self-applies to `memory/personality_state.json` with no identity-continuity validation
and no Reflection gate**) — Audit gap #6. And the drift model is a different trait model than V Ch.7's canonical
`PersonalityVector`. Goal: unify under one `PersonalityEngine`, put drift behind the V Ch.7 validation path, and
reconcile to one trait model.

## Scope to DoD (grounded in Ch.1–Ch.4; extend existing, do not rewrite)
- **Gap-#6 fix — no self-apply (Ch.3, the core build):** replace `memory/personality_drift.py`'s `save()` self-apply
  with **emitting a `DriftObservation`** (a candidate, not a write) to Reflection (V Ch.6) and stopping. Only Reflection
  promotes an observation to a `PersonalityDelta`, only from a confirmed, evidenced lesson; then V Ch.7 §7.5 validation
  + §7.6 versioning apply. Fail closed: Reflection unavailable → log candidate, apply NOTHING. Keep the drift math
  (band, clamp `[0.2,0.9]`, `drift_rate` 0.02 / stability-lock 0.01); do NOT build a second evolution path — application
  stays in V Ch.7 (single applier). Build a read-only `DriftMonitor` (generalise `_detect_instability()`): band /
  velocity / `identity_hash` / divergence checks; raises alarms, never applies/reverts; `identity_hash` mismatch =
  CRITICAL (freeze evolution, alarm, roll back).
- **Trait-model reconciliation (ruling D / D-X3-1):** map `tone_profile`/`interaction_bias` onto the canonical
  `PersonalityVector` (curiosity, patience, confidence, empathy, discipline, wonder, playfulness, directness) +
  preferences, or deprecate — the mapping is a RESERVED decision, NOT to be invented in code. Do not proceed on the
  code mapping until ruling D + D-X3-1 land.
- **Unify under one `PersonalityEngine` (Ch.1):** one faculty holds both layers (`SelfStateModel` / `DriftManager` /
  `PersonalityComposition`); the fast layer NEVER writes the slow layer directly — trait change only via the V Ch.7
  validated path. Fast values stay free within a session.
- **Self-State model (Ch.2):** keep `self/elo_self_model.py` math; clamp every affective float `[0.0,1.0]`;
  `inner_events` values only from the closed §2.3 vocabulary (out-of-vocab → reset affective slice, preserve situated);
  `session_turns` resets to 0 on load. **The one substantive change:** wire the decay target from the constants
  `0.5 / 0.55` to the **V Ch.7 trait baseline** (`trait.baseline`) — the "first fruit of unification"; until built,
  mark degraded and decay to constant (honest gap). Preserve the WO-052A round-trip (do not drop co-resident situated
  fields owned by ADR-Exec-004). Surfacing stays a deterministic seed (`prompt_block`/`self_inquiry_voice`), no LLM, no
  fabricated mood on cold start.
- **Personality in the Moment (Ch.4):** build `PersonalityComposition` as a **read-only** step — read Ch.2 self-state +
  V Ch.7 trait vector, freeze a `PersonalitySlice`, contribute to CognitiveState, copy into `self/state/the_moment.json`
  with epistemic tiers (self-state tier "inferred/private", never "verified"). Composition NEVER writes self-state or a
  trait. Trait vector read-only + identical every turn of a session; only self-state moves intra-session. Derive the
  V Ch.4 affect baseline here. Wire at top-of-turn in the spine, beside the World State assembly (WO-CANON-XV / XVI).

## Definition of Done
- Drift proposes (`DriftObservation`), never self-applies; every trait change passes V Ch.7 §7.5 + is versioned; a
  `DriftMonitor` alarms without acting; `identity_hash` mismatch freezes evolution.
- One trait model (per ruling D); decay target = trait baseline; fast layer never writes the slow layer.
- `PersonalitySlice` assembled read-only into The Moment each turn; composition writes nothing; personality colours
  expression only, never overrides verified truth.
- Audit can mark Vol X COMPLETE.

## Tests to write (`tests/test_canon_x_personality.py`)
- Ch.1: two speeds, eLo ≠ David, baseline relaxation, no direct trait write, identity protected, self-state→affect+evolution.
- Ch.2: eLo ≠ David, fast movement bounded (no ratchet), session read derived not invented (no LLM), situated fields
  round-trip (WO-052A), no trait write from fast layer, cold start doesn't fabricate feeling, corruption resets safely,
  decay target = trait baseline.
- Ch.3: drift proposes never applies, unconfirmed signal changes nothing, confirmed lesson grows slowly (identity_hash
  unchanged), bounded-but-ungated is still drift, identity cannot move under any drift, monitor alarms doesn't act,
  drift→Reflection→validated growth (whole gap-#6 loop), chronic divergence earns a hearing not a bypass.
- Ch.4: assembled not generated, stable who / fluctuating feeling, one read all faculties agree, composition never
  writes, personality never overrides truth, degraded self-state doesn't fabricate feeling, three-volume seam holds,
  "who are you?" answered from state.

## Dependencies + blocked-by
- **Blocked by:** **alignment ruling D** (drift-gate + trait-model, CA + David nod) and **D-X3-1/2/3** (RESERVED,
  David L3 / CA — trait-model unification, drift-rate reconciliation, conversational-signal legitimacy) and the Ch.2
  §2.6 file-layout decision (David L3, identity-adjacent). Runs behind Presentable v1; wires beside WO-CANON-XV / XVI.
- Cross-volume: Vol V Ch.7 (authoritative traits), V Ch.6 (Reflection = sole delta source), V Ch.4 (affect baseline),
  Vol XXI (narrative-layer drift-vs-growth — do not duplicate), `18_identity_kernel.md` (immutable boundary).
- **Gate:** ruling D + David L3 (identity/values). Architect promotes Vol X only after these clear.

## Lane
Builder (Python — drift-observation redirect, DriftMonitor, decay-target wiring, PersonalityComposition, Moment wiring).
Architect coordinates + relays ruling D / David L3 decisions. Trait-model mapping stays out of code until ruled.
