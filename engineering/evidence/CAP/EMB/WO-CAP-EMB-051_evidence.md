# WO-CAP-EMB-051 — eLo should know the difference between simulation and reality

**Filed by:** Builder 2 · 2026-09-27
**Source:** `SOURCE_2026-09-19_eLo_EMBODIMENT_LEARNING_MEMORY.md §51`
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13

---

## VERBATIM SOURCE §51 — line by line

| Source line | Where it is true in the built system |
|---|---|
| `This is non-negotiable.` | — |
| `SIMULATED EXPERIENCE` | `MemoryOrigin.SIMULATED_EXPERIENCE` |
| `PHYSICAL EXPERIENCE` | `MemoryOrigin.PHYSICAL_EXPERIENCE` |
| `eLo can remember both.` | both are `is_auto_storable` → True; neither is erased |
| `But they must be labelled differently.` | `origin_for_embodiment()` labels from the live body |
| `Otherwise:` | — |
| `I already know how this works.` | `can_claim_physical_experience(origin)` |
| `could mean:` | — |
| `I tested it in Unity.` | `origin_for_embodiment("unity")` → `simulated_experience` |
| `when it has never physically done it.` | that origin returns **False** — the claim is unavailable |

---

## THE GAP THIS FOUND

`MemoryOrigin` already separated **dream** from **real**. It did not separate
**simulated body** from **physical body**. An action by the Unity desktop
avatar and an action by the robot were both `REAL_EXPERIENCE`.

So the conflation §51 calls non-negotiable was live: nothing in the memory
layer could tell "eLo moved in Unity" from "eLo physically moved".

The signal already existed — `server.py:7399` writes `embodiment: "desktop"`
and it sits in `blender_state.json` right now — but it never reached memory
labelling.

## WHAT CHANGED

Additive to `runtime/memory_origin.py` (the two existing consumers,
`wkg_faculty.record_claim()` and `dream_review`, neither match
exhaustively, so new members are safe):

- `SIMULATED_EXPERIENCE` / `PHYSICAL_EXPERIENCE`
- `current_embodiment()` — reads the live state. **Observed, not declared.**
- `origin_for_embodiment()` — body → label
- `can_claim_physical_experience()` — the §51 guard

**An unrecognised body fails safe to SIMULATED.** Defaulting the other way
would let a new embodiment silently claim physical experience it has never
had, which is precisely the failure the section forbids.

---

## WIRE-CUT PROOF

Cut: make unknown bodies default to PHYSICAL, and let simulated experience
claim physical capability.

```
WIRE CUT: unknown body claims physical + simulated may claim physical
FAILED test_nothing_else_may_claim_physical_experience[real_experience]
FAILED test_nothing_else_may_claim_physical_experience[dream_simulation]
FAILED test_nothing_else_may_claim_physical_experience[simulated_experience]
FAILED test_a_dream_certainly_cannot_claim_it
FAILED test_missing_state_falls_back_without_claiming_physical
... 14 failed, 22 passed
```

Restored:

```
36 passed in 0.13s
```

---

## REAL RUN — JSONL

```jsonl
{"wo": "WO-CAP-EMB-051", "checkpoint": "live embodiment observed, not declared", "embodiment": "desktop", "origin": "simulated_experience", "can_claim_physical": false}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "unity", "origin": "simulated_experience", "can_claim_physical": false, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "desktop", "origin": "simulated_experience", "can_claim_physical": false, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "terminal", "origin": "simulated_experience", "can_claim_physical": false, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "robot", "origin": "physical_experience", "can_claim_physical": true, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "pi5", "origin": "physical_experience", "can_claim_physical": true, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "body -> label", "body": "hologram", "origin": "simulated_experience", "can_claim_physical": false, "remembered": true}
{"wo": "WO-CAP-EMB-051", "checkpoint": "the line §51 exists to prevent", "scenario": "eLo tested it in Unity and has never physically done it", "origin": "simulated_experience", "may_say_i_already_know_how_this_works": false}
{"wo": "WO-CAP-EMB-051", "checkpoint": "only one origin may claim physical experience", "claimable": ["physical_experience"], "total_origins": 9}
{"wo": "WO-CAP-EMB-051", "checkpoint": "eLo can remember both", "simulated_remembered": true, "physical_remembered": true}
```

The decisive row:

```json
{"scenario": "eLo tested it in Unity and has never physically done it",
 "origin": "simulated_experience",
 "may_say_i_already_know_how_this_works": false}
```

And: of nine origins, exactly one may claim physical experience. Both new
labels are remembered.

## NOT PROVEN

- **Not a live-server exchange.** §51's evidence line asks for one. This is
  a memory-layer boundary with no prompt that exercises it; the rows above
  are the real code reading the real live `embodiment` field. Server-level
  evidence needs a turn where eLo is asked whether it has done something.
- **The guard is available, not yet enforced at the response layer.**
  Nothing currently calls `can_claim_physical_experience()` before eLo
  speaks. The label and the guard exist; wiring them into the response path
  is a separate change and touches identity prompting, which Builder 1 owns.
- **No physical body exists.** `PHYSICAL_EXPERIENCE` has never been produced
  by a real robot — EMB is 56/59 gated on hardware.

## STATUS

`IMPLEMENTED → TESTED`. Labelling live; response-layer enforcement not
wired. Not LIVE VERIFIED. Not declaring PASS.
