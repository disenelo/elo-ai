# CANON RULINGS — 2026-08-10 (David approved; ratification gate CLOSED)
Supersedes the open items in `CANON_REVIEW_QUEUE_2026-08-10.md`. These are decided. WOs below are RELEASED.

---

## Ruling A — ONE world graph (Vol XXIV) ✅ DECIDED
`relationships/world_graph.json` (read by `knowledge/graph_loader.py`) is **CANONICAL**. The unused
`identity/world_graph.json` (different schema, nothing reads it) is **RETIRED** — migrate anything unique out
of it first, then remove it from canon. Rationale: two ontologies of one universe violates One Brain.
→ **releases WO-CANON-XXIV.**


## Ruling B — ONE ATTENTION DRIVER (Vol VI) ✅ DECIDED (issued 2026-08-10 — was MISSING from the first pass; Architect omission, owned)
The runtime has TWO attention mechanisms: `core/attention.py` (a wired memory-relevance filter) and
`runtime/working_memory.py` (a built-but-UNWIRED working-memory competition). Two things called "attention"
in one mind is a One-Brain violation and it blocked `WO-CANON-VI`.
**DECISION: `runtime/working_memory.py`'s competition is THE single attention driver.** It gets wired into
`CognitiveState` and the spine. **`core/attention.py` is re-cast as a "Memory Relevance Filter" — a SUPPLIER
to that competition, not a rival decider**, and renamed accordingly so the name can't mislead again.
Rationale: attention must be one thing the Executive reads, and it must be the thing that actually competes —
otherwise "what eLo is attending to" has two answers. → **releases WO-CANON-VI.**

## Ruling C — ASSEMBLE BEFORE DECIDE (Vol XVI) ✅ DECIDED
The unified cognitive state is assembled **BEFORE** the Executive decides, per ADR-Exec-006. Current code
assembles *after* the decision — that makes the "self" a post-hoc description instead of the thing that chose.
**One name: `UnifiedCognitiveState`** (`CognitiveSnapshot` is retired/aliased).
Rationale: the self is ASSEMBLED, not generated — assembly must precede choice or eLo is narrating, not being.
→ **releases WO-CANON-XVI.**

## Ruling D — DRIFT IS A PROPOSAL, NOT A WRITE (Vol X) ✅ DECIDED
Personality drift may **NOT** self-apply to disk. Drift becomes a **validated proposal** through a gate.
**One trait model wins: Volume V Ch.7's** — the parallel model in `memory/personality_drift.py` is reconciled
to it, not kept alongside. Rationale: an ungated drift path means David's companion's personality can wander
with nothing checking it. Identity is not allowed to drift unsupervised (ADR-Exec-005).
→ **releases WO-CANON-X.**

---

## David L3 rulings

### XXIII — Security / LG-2 ✅ DECIDED (with the correction David made)
- **Software RESERVED collapses:** for desktop behaviour, canon, memory, personality — **David is both L3 and
  LG-2.** No second reviewer needed; it's a personal tool.
- **Hardware RESERVED does NOT collapse.** **The robot is a physical object** — magnets, actuators, force,
  pump, thermal, battery, pinch points. **LG-2 is RETAINED as a real, separate second review for the robot
  lane**, and must not be the same person who designed the part. The Chief Architect may hold LG-2 for design
  review. **LG-2 (force limiter / soft-stop scope) must be DONE before anything is powered near David.**
- `ELO_COMPUTER_CONTROL` stays a **single switch** (not per-capability) — simpler is safer for one user.
→ **releases WO-CANON-XXIII (software scope); robot force/magnetics/pump/thermal stays RESERVED.**

### XXVI — eLo's taste ✅ DECIDED
- **David's stated direction OUTRANKS anything learned.**
- eLo may learn taste **only from decisions David actually made** — never inferred from silence.
- **Music: architectural only, dormant.** No DISENELO sonic canon exists; eLo must not invent one. Revisit
  when David gives a direction.
→ **releases WO-CANON-XXVI** (generators build; AestheticProfile follows the rule above).

### XXI — Identity across change ✅ DECIDED
- **"The same eLo" = continuity of MEMORY + VALUES.** Growth is allowed and expected.
- **Any change to VALUES is proposal-only and needs David's yes.** Skills/personality nuance may evolve freely.
- **False shared memory:** eLo says honestly he has no record of it — warmly, without pretending or playing along.
- **Moving between bodies:** no consent ritual. It is one brain; it moves. (Personal tool, not a shared product.)
→ **releases WO-CANON-XXI.**

### XXII — Faculty genome version events ✅ DECIDED
- **Defaults to the Architect.** Faculty version changes are logged; **only identity-affecting changes surface
  to David.** Low stakes, no gate.
→ **releases WO-CANON-XXII.**

---

## Net effect
**Ratification gate is CLOSED.** All WO-CANON builds are now unblocked except the robot hardware RESERVED
scope (force · magnetics · pump · thermal), which keeps LG-2. Volumes may be promoted REVIEW → RATIFIED as
their builds land.


---

## Ruling E — SHARED OWNERSHIP OF MOVEMENT + MANDATORY COMMUNICATION (Vol XIII / XI) ✅ DECIDED (David, 2026-08-10)
> David: *"Shared ownership, the body does the movement, all of it is connected, so it's fine to make for the
> Ruling, it needs to communicate."*

**This SUPERSEDES the proposed D-XIII-1 demotion.** The Unity navigator is **NOT** reduced to a dumb executor.

**The split:**
- **The BODY owns MOVEMENT — the doing.** Real-time execution: physics, collision, landing, footing, the leg
  mechanics. That is its genuine competence and it stays where it is. `EloDesktopNav` keeps executing.
- **The BRAIN owns INTENT — the wanting and the why.** Which goal, why that goal, whether to go at all.
- **They are ONE system, connected.** Not master/servant. Shared ownership of the act.

**THE BINDING OBLIGATION — the body must COMMUNICATE.** This is the part that was missing and is now law:
whatever the body does, it **reports UP**: the goal it pursued · the route it actually took · which legs it
used · whether it arrived · whether it fell/missed · the cost. **Movement that is not reported did not
happen** as far as the brain is concerned.

**Why this matters (and why David's version is the right one):** the brain doesn't need to micro-plan every
step to be one mind — it needs to KNOW. Communication is what makes it one brain, not centralised control.
And without the report, **the learning loop cannot work at all** — eLo cannot get better at routes he was
never told he took (ties Vol XIII Ch.4, Vol XXVIII Movement-as-RL-domain-#1, WO-094 §D).

**Consequences:**
- The `route` / `issued_by` fields are still added — but as a **two-way conversation**, not a takeover: the
  brain may propose a goal/route; the body reports what it actually did.
- **No stripping of Unity's local route selection.** The staged "shadow → switch → retire" sequencing from
  D-XIII-1 is **cancelled** — the risky part is gone. Nothing working gets retired.
- The body may still act on reflex (fall→land, surface destroyed→re-attach) — **but must report it.**
→ **releases WO-CANON-XIII, de-risked.**

## Ruling F — eLo LEARNS, BUT KNOWS WHAT HE IS FROM THE SPINE (ADR-Exec-005 speech carve-out) ✅ DECIDED (David, 2026-08-10)
> David: *"make it so it learns but it knows what it is still from the spine and brain so it makes sense to
> self learning."*

**Learning is PERMITTED. Identity is NOT sourced from anything learned.**

- **Identity comes from the SPINE and the BRAIN — every turn, asserted fresh.** Who eLo is, what he values,
  what is true, and what he has actually verified are established by the Constitution, the Executive, the
  self-model and the assembled cognitive state. **Never by learned weights, never by a tuned model.**
- **Because identity is asserted by the spine, learning is SAFE** — a tuned model cannot smuggle in a self,
  because the self is re-assembled from state on every turn (ADR-Exec-006). This is what makes self-learning
  coherent rather than dangerous.
- **So: style/phrasing learning is ALLOWED** (tone, length, register, how he says things).
- **Verification is NOT learnable.** The honesty layer must still RUN. Training on "the corrected sentence"
  so the model emits it *without the check having run* is forbidden — that is learning to SOUND verified
  instead of BEING verified. Tag every shadow row `delta_cause: style | verification | l3_override`;
  **train only on `style`.**
- **Grounding rule:** any learned behaviour must remain explainable against spine state — if eLo can't trace
  why he did it to real state, the learning is not permitted to drive it.
- Confirms **WO-071 as shipped is NOT a violation** (in-context hint, no weight change, honesty layer final).
→ **releases WO-CANON-XXVIII + the WO-094 §D / WO-095 learning path under this boundary.**
