# Volume XXVIII — Adaptive Learning & Reinforcement
### Scaffold · scope-locked · PLANNED. Authored + built BEHIND Presentable v1 (RL/physics phase is already gated — defaults first). Chief Architect proposal, David L3 2026-08-06.

**Does not touch the Presentable finish-line 6.** This is the disciplined home for RL so, when it is
built, it strengthens eLo instead of eroding the personality built over months.

## ⚖ THE CONSTITUTIONAL BOUNDARY (the most important rule here — ADR-Exec-005)
> **Reinforcement Learning may optimise behaviours and skills, but it may NEVER alter identity,
> constitutional principles, Executive Authority, or verified truth.**

RL is **not** allowed to learn: personality · values · ethics · memory truth · identity · Executive
Authority · speech correctness · architectural principles. Those are governed by the Constitution, ADRs,
and the Executive, and stay **deterministic**. (Verified Speech must never become "lying sometimes gives
higher reward" — that's exactly why it's a constitutional invariant.) RL improves *how well* eLo performs
what the Executive already decided to do — never *who eLo is* or *what is true*.

## Where RL lives: a Learning Faculty (preserves One Brain)
Do NOT build "an RL agent." Build a **Learning Faculty** the Executive *asks*, like every other faculty:
```
Executive (deterministic) → Movement Faculty → RL Policy → Action
```
The Learning Faculty: runs simulations · learns policies · evaluates rewards · stores learned policies ·
reports confidence. It **never** rewrites code, the Constitution, or the Executive — it learns *behaviour*.

## The four domains RL fits (and only these, for now)
1. **Movement Faculty ⭐** — instead of scripting parkour, eLo learns traversal (state = window geometry ·
   speed · jump height · ledges · momentum; actions = walk/run/jump/wall-jump/climb/slide/drop/hide;
   reward = smooth · no collisions · interesting · natural pauses · safe landing). This is "run around
   because he *wants* to." Consumes the Spatial Faculty (WO-049) + Affordances (WO-056).
2. **Curiosity Faculty** — learned exploration (don't interrupt David · discover affordances · return
   successfully), not random wander.
3. **Presence timing** — learns *when* to approach / observe / disappear from David's state (coding →
   quiet; idle → approach; focused → vanish). Timing learned, not scripted. (Vol XIII Presence.)
4. **Robot locomotion** — balance · walking · recovery · obstacle avoidance · arm positioning. **This is
   RD-3 (Isaac Lab RL pipeline) — the robot instance of this volume.** Sim-only until L3 + LG-2.

## Reward = a VECTOR, via the EXISTING Significance Engine (not a scalar)
Reuse `memory/significance_engine.py` + Vol V Ch.5 Significance — do NOT invent a reward scalar. The
learning signal is a vector aligned to eLo's values: **Meaning · Novelty · Relationship · Embodiment ·
Curiosity · Efficiency · Safety.** Learning then optimises *toward what matters*, not toward a number.

## Simulation-first (the eLo-flavoured idea)
eLo learns by running **simulated** movement (no real motion): *"I wonder if I can jump from Spotify to
Photoshop" → simulate → fail → learn → retry → confidence 98% → next day, do it for real.* Learned policy
+ confidence stored; the Executive only acts for real above a confidence/safety threshold.

## Self-improving SKILLS, not self-modifying code
The engineering expression of "more alive, not just more capable." Improvements are **measurable and
honest**, not hallucinated: *"I've been practicing landing on narrow window edges — success 68% → 94%"* /
*"I've learned a smoother route between the browser and Spotify."* Ties to Reflection/Growth (Vol V Ch.6)
+ Narrative Identity (Vol XXI). Constitution defines *who*; Executive decides *what*; RL improves *how well*.

## Scope (locked)
Reinforcement Learning · Skill Acquisition · Motor Learning · Reward Functions (Significance-vector) ·
Simulation · Policy Optimisation · Habit Formation · Exploration vs Exploitation · Learned Affordances ·
Safe Online Learning.

## Reconciles with (extend, don't duplicate)
Reflection & Growth (Vol V Ch.6) · Capability Learning (WO-055) · Significance Engine (Vol V Ch.5 /
`memory/significance_engine.py`) · Affordances (WO-056) · Spatial Faculty + Movement (WO-049) · Presence
(Vol XIII) · RD-2/RD-3 (Isaac Lab sim + RL, robot). Governance boundary → ADR-Exec-005 (Decision Log).

## Sequencing
Scaffold + scope now (this doc). Full authoring + build sit **behind Presentable v1**; the robot RL
(RD-3) also behind the RD-4 CAD lock + LG-2. Not started; captured so the direction can't drift.

## The three-layer learning strategy (David 2026-08-07 — reconciled)
One picture, three temporal horizons — captured so the direction holds:
1. **Capture (NOW, passive):** WO-070 shadow-log — extends `capability_learning.py`; logs eLo's runtime
   turns (raw_input · elo_raw_gen · elo_final · backend_used · executed_action · l3_rating). The basket.
2. **Real-time learning (in-context, no weight change):** WO-071 — extends `self_improvement/correction_
   store.py` (WO-027); injects recent slips + L3 overrides into the prompt so eLo corrects on the fly.
3. **Permanent adaptation (POST-Presentable, this Volume):** batch LoRA fine-tune of a local understudy
   (Llama-3.1-8B / Mistral-7B), served through the already-installed Ollama.

## Understudy fine-tune — BLUEPRINT (spec only; the seat writes the code, not the Architect)
The batch fine-tune belongs here. **The Architect does NOT write the `.py`** (lane) — this records the
approach so the owning seat (Builder/R&D) builds it when the gates open.
- **Method:** LoRA / QLoRA (4-bit) via Unsloth or Axolotl; a short targeted SFT pass (skill/style sharpening,
  not a full retrain). Adapter saved locally; served via Ollama.
- **Data:** the WO-070 `understudy_shadow.jsonl`, once a few hundred+ CLEAN, L3-approved turns exist.
- **Training pair (IMPORTANT correction to the proposed script):** target the **final verified style
  directly** — learn to PRODUCE `elo_final` given (`context` + `raw_input`), using `elo_raw_gen`→`elo_final`
  as the delta signal. Do NOT train it to emit a narrated "Draft Thought: … Verified Execution: …" — that
  teaches it to show its working, not to just be right.
- **GATES (all required before a run):** (a) data volume threshold met; (b) a confirmed capable local GPU
  (≈RTX 3060+ / CUDA) — hardware-verify gate, abort otherwise; (c) **ADR-Exec-005 guardrail** — the tuned
  understudy sharpens skill/style ONLY, never identity/truth; it remains a FALLBACK brain that still passes
  the Executive verification + honesty guards (never a second source of truth).
- **Serve:** merged adapter → local model in Ollama → slots into the router's existing `…→ Ollama → Mock`
  tier as eLo's own tuned understudy. Zero cloud cost when it drives.
