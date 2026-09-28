# WO-CAP-EMB-002 — Every embodiment needs an "I can..." model

**Date:** 2026-09-28
**Seat:** Builder 2
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13 · pytest 9.1.1
**Commit:** `bfd49d4`
**Source:** `SOURCE_2026-09-19_eLo_EMBODIMENT_LEARNING_MEMORY.md` §2
**Supersedes the FAIL in:** `WO-CAP-EMB-EVIDENCE-2026-09-20.md`

**STATUS: TESTED.** Not LIVE VERIFIED — see LIVE EVIDENCE. Prior status was
TESTED ❌ FAIL.

---

## THE PRIOR FAILURE, AND WHY IT HAPPENED

2026-09-20 recorded two failures:

| Input | Output | Verdict then |
|---|---|---|
| `what can you do right now through this terminal` | "You explored emotion, identity with a neutral tone, and that's something to consider." | ❌ pattern observer leaking into a capability question |
| `what cant you do right now in this body` | "I can't do things like control your computer directly" | ⚠️ false — eLo *can* open apps, set reminders, control lights |

Both have one cause: **there was no ground truth to answer from.** A
capability question reached the language model with nothing authoritative to
say, so the nearest available state — the conversation pattern observer —
filled the gap, and the denial was improvised.

A hardcoded Can/Cannot table fixes the first failure and reproduces the
second the moment the registry moves. So every claim in this build is checked
against `runtime.capability_registry.CAPABILITY_REGISTRY` — what is actually
dispatchable right now, observed rather than declared.

## OBSERVED

```
§2 — five bodies, as built

Terminal eLo (terminal)
  Can:            read/write text, inspect files, run commands, research, reason, talk
  Cannot:         physically walk, see the room unless given vision, manipulate physical objects

Desktop eLo (desktop)
  Can:            perceive screen state, move around desktop surfaces, observe windows, interact with UI, speak, animate, react, move around its environment
  Cannot:         §2 does not say — cannot() returns None, not False

Unity eLo (unity)
  Can:            walk, run, jump, wall-jump, parkour, fight, observe, interact with game objects, navigate 3D/2.5D space, express emotion physically
  Cannot:         §2 does not say — cannot() returns None, not False

Robot eLo (robot)
  Can eventually: see, hear, move, touch, manipulate, navigate, sense orientation, sense position, perceive physical space, interact with humans, manipulate objects
    -> can() answers False for every one of these today
  Cannot:         §2 does not say — cannot() returns None, not False

Alexa/voice embodiment (alexa)
  Can:            hear, speak, converse, trigger capabilities, exist without a visible body
  Cannot:         §2 does not say — cannot() returns None, not False


the 2026-09-20 FAIL, re-run against the model
  "I can't do things like control your computer directly" FALSE — disproved by WORLD_MEDIA_CONTROL, WORLD_LIGHTS_CONTROL
  "I can't set reminders"                              FALSE — disproved by WORLD_REMINDERS_WRITE
  "I can't search the web"                             FALSE — disproved by WORLD_WEB_RESEARCH
  "I can't physically walk"                            true — not contradicted


drift check — §2 lines with no live registry backing
  terminal  none
  desktop   none
  unity     none
  robot     none
  alexa     none
```

## THREE DECISIONS

**The robot's list is future tense.** §2 writes "Robot eLo / Can eventually:"
— the only body given one. It lives in its own table and `can()` answers
False for every entry. A body that has not been built can do nothing yet.
This is the same call EMB-051 makes when it fails an unknown body safe to
simulated, and for the same reason: an unbuilt body must never claim.

**Absent is not empty.** §2 spells out Cannot for the terminal only.
`cannot()` returns `None` for the other four, not `False`, because False
reads as "so it can" — which is how eLo came to assert things about bodies
the source never described. The build carries no invented denials.

**One embodiment signal.** `current_body()` reads EMB-051's
`current_embodiment()` rather than adding a second source of truth.

## BOARD CROSS-CHECK, EXECUTABLE

`test_every_source_line_is_represented` parses §2's VERBATIM SOURCE block out
of the work order — body by body, Can / Cannot / Can eventually — and
compares it against the build. It goes red if source and build drift. Board
does not have to take the tables on trust.

Rule 4b is pinned: `test_manipulate_appears_twice_for_the_robot` holds both
"manipulate" and "manipulate objects", which the source lists separately.

## TEST RESULTS

```
tests/test_cap_emb_002_i_can_model.py     24 passed
regression (emb · capab · origin · embodiment · cognitive · dream ·
            battery · calm)              645 passed
```

## WIRE-CUT

| cut | result |
|---|---|
| drop the registry check from `denial_is_false` (reinstates the 2026-09-20 denial) | 6 failed |
| let the robot claim present-tense ability | 6 failed |
| answer `False` where §2 gives no Cannot list | 1 failed |
| restored | 24 passed |

## LIVE EVIDENCE

**NONE.** The WO asks for a real-server exchange, and the running server does
not carry this commit. The two 2026-09-20 inputs have not been re-run against
a live server.

## KNOWN, NOT DONE — AND IT IS THE HALF THAT WAS TESTED

The prior FAIL was a **response-layer** failure: the wrong subsystem answered.
This commit builds the ground truth that was missing and proves it is
correct, but **nothing calls it before eLo speaks.** `capability_answer()` is
available; the capability question still reaches the language model the same
way it did on 2026-09-20.

Wiring it in means touching the response path — `runtime/claim_gate.py` and
the prompt builder — which is Builder 1's active lane. Same half-closure as
EMB-051's `can_claim_physical_experience()`, stated rather than quietly
omitted.

**So: the model is right and the leak is not yet closed.** Re-running the two
2026-09-20 inputs today would very likely still fail. That is the honest
position, and it is a Board routing decision, not a Builder 2 one.

## BUILDER STATUS

**TESTED.** Not declaring PASS — Board crosschecks.
