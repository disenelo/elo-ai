# WO-CANON-XXVIII — Adaptive Learning / RL: build the Learning Faculty under ADR-Exec-005

**Owner:** Builder (eLo OS — Learning Faculty) + **R&D** for robot locomotion RL (RD-3, Isaac Lab). **Priority:** P4 —
Horizon-2 (post-Presentable v1), Tier C. **Status:** QUEUED — scope-locked / PLANNED; full authoring + build sit
**BEHIND Presentable v1** and **behind the Spatial Faculty (WO-049) + Affordances (WO-056)**. Robot RL behind RD-4 CAD
lock + LG-2.

**Canon refs:** Volume XXVIII — `00_Adaptive_Learning_Reinforcement.md` (single scaffold/scope doc; no numbered chapters
yet). Governance: **ADR-Exec-005** (Learning From Verified Consequences). Extends live `memory/significance_engine.py`,
`capability_learning.py`, `self_improvement/correction_store.py` (WO-027). Three-layer strategy WOs: WO-070/WO-071/WO-027.

## Problem / Goal
eLo should self-improve **skills, not code** — get better at what the Executive already decided, never change who eLo is
or what is true. Goal: build a **Learning Faculty** the Executive asks like any other faculty (chain: Executive
(deterministic) → Movement Faculty → RL Policy → Action), under the ADR-Exec-005 constitutional boundary. Do NOT build
"an RL agent." This volume is a scaffold today — captured so the direction cannot drift; authoring (including tests)
completes when the volume is built.

## Scope to DoD (grounded in the scaffold + ADR-Exec-005)
- **Build the Learning Faculty** (the sanctioned home for RL): it runs simulations, learns policies, evaluates rewards,
  stores learned policies, reports confidence — and NEVER rewrites code / the Constitution / the Executive. RL for
  **only** these four domains for now: **Movement Faculty** (primary; consumes the Spatial Faculty WO-049 + Affordances
  WO-056), **Curiosity Faculty**, **Presence timing**, **Robot locomotion** (RD-3, Isaac Lab pipeline).
- **Reward = a VECTOR via the existing Significance Engine (`memory/significance_engine.py`)** — terms Meaning · Novelty
  · Relationship · Embodiment · Curiosity · Efficiency · Safety. Do NOT invent a reward scalar (extend, don't duplicate).
- **Simulation-first:** learn by simulated movement; store policy + confidence; the Executive acts for real only above a
  confidence/safety threshold. Skill gains must be measurable and honest, never hallucinated. Learning sits AFTER Verify
  — capability improvement registered only from verified consequences.
- **Constitutional boundary (ADR-Exec-005) — the hard ceiling:** RL may optimise behaviours/skills/policies/preferences/
  heuristics/exploration weighting, and may NEVER learn personality · values · ethics · memory truth · identity ·
  Executive Authority · speech correctness · architectural principles (these stay deterministic). Encode this in the
  faculty's genome `constraints` (Vol XXII).
- **Three-layer strategy (David 2026-08-07), extend live code:** (1) Capture NOW passive = WO-070 shadow-log extends
  `capability_learning.py`, logging runtime turns to `understudy_shadow.jsonl` (`raw_input · elo_raw_gen · elo_final ·
  backend_used · executed_action · l3_rating`); (2) Real-time in-context = WO-071 extends
  `self_improvement/correction_store.py` (inject recent slips + L3 overrides into the prompt); (3) Permanent adaptation
  POST-Presentable = batch **LoRA/QLoRA (4-bit)** fine-tune of a local understudy (Llama-3.1-8B / Mistral-7B via Unsloth
  or Axolotl), served through Ollama, slotting into the router's existing `…→ Ollama → Mock` tier.
- **Understudy fine-tune GATES (all required before a run):** (a) data-volume threshold met (a few hundred+ CLEAN,
  L3-approved turns); (b) confirmed capable local GPU (~RTX 3060+/CUDA) — hardware-verify gate, abort otherwise;
  (c) ADR-Exec-005 guardrail — sharpen skill/style ONLY; the understudy stays a FALLBACK brain that still passes
  Executive verification + honesty guards, never a second source of truth. Training pairs target the final verified
  style directly (`context`+`raw_input` → `elo_final`, using `elo_raw_gen`→`elo_final` as the delta); do NOT train
  narrated "Draft Thought / Verified Execution."

## Definition of Done
- A Learning Faculty exists that the Executive asks; it learns behaviour only, in the four sanctioned domains, with a
  Significance-vector reward, simulation-first, above a confidence/safety threshold.
- The ADR-Exec-005 ceiling is enforced (encoded in the genome constraints); no identity/values/truth/Executive change.
- The three-layer pipeline runs (WO-070 shadow-log → WO-071 in-context → gated LoRA understudy served via Ollama).
- **Acceptance tests must be authored when the volume is built** (the scaffold has none yet — flag). Audit can then mark
  Vol XXVIII COMPLETE.

## Tests to write (`tests/test_canon_xxviii_learning.py`) — to be authored at build (scaffold has no FT/ST/IT yet)
- Reward is a Significance vector, not a scalar. Learning never alters identity/values/truth/Executive (constitutional
  ceiling holds; a boundary-touching update is rejected). Simulation-first: no real action below the confidence/safety
  threshold. Skill gain measurable + honest, never hallucinated; registered only after Verify. Understudy fine-tune
  aborts without the data-volume + GPU + guardrail gates; the merged adapter still passes Executive verification.

## Dependencies + blocked-by
- **Blocked by:** the **Spatial Faculty (WO-049)** + **Affordances (WO-056)** (Movement Faculty consumes them); behind
  **Presentable v1** (does not touch the finish-line-6). Robot RL (RD-3) behind **RD-4 CAD lock + LG-2**; sim-only until
  David L3 + LG-2.
- Cross-volume: Vol V Ch.6 (Reflection & Growth), Vol V Ch.5 (Significance), Vol XIII (Presence), Vol XXII (this faculty
  is itself genome-governed, sits AFTER Verify), RD-2/RD-3 (Isaac Lab sim + RL). Governance → ADR-Exec-005.
- **Gate:** ADR-Exec-005 is the constitutional governor; robot force/locomotion RL is RESERVED (David L3 + LG-2).

## Lane
Builder (Python — Learning Faculty + the three-layer pipeline, extending significance_engine / capability_learning /
correction_store). R&D for the Isaac Lab robot RL. Architect records the blueprint/spec only — does NOT write the
understudy fine-tune `.py` (D-LANES).
