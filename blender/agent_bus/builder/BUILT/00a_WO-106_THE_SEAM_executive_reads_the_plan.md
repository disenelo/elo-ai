# 00a_WO-106 — 🔴 **THE SEAM.** The Executive decides from two variables while eLo assembles fifteen.

**WO:** WO-106 · **Seat:** builder · **Priority:** **P0 — the highest-leverage card on the board**
**Gate?** none · **Canon:** **Ruling H** (Capability Truth Matrix) · ADR-Exec-006 · ADR-Exec-002
**Source, verbatim:** `docs/architecture/_intake/SOURCE_2026-08-13_capability_truth_matrix.md`

## The finding — one fault under 15 of 26 capabilities
[VERIFIED 2026-08-13, live path traced `server.py:4023 /chat` → `_process_turn` → `spine.run` → `exec_decide`]

**eLo assembles a rich self every turn and then decides without it.**

```
spine.run() assembles:            runtime/executive.py:280 reads:
  plan.world                        attention_model
  plan.cognitive_state              user_input
  plan.working_memory
  plan.embodiment_state             ← that's the entire input
  plan.capabilities
  snapshot.surface_affordances
```

`spine.py:167` — `_exec_decide_fn(attention, loop_detected=False, user_input=raw)`. **That is the whole
Executive input.** Everything else is either dropped or flattened into a prompt string, where the LLM can
*talk about* it but the Executive cannot *decide with* it.

**This is what Ruling H forbids:** *"LLM-generated language is never evidence of capability."* Right now
eLo can **say** almost everything on the matrix and **know** almost none of it.

### Assembled and read by nobody [VERIFIED]
| Assembled at | Read by |
|---|---|
| `plan.world` (`spine.py:369-370, :452-455, :467`) | nothing — `server.py:2490, :2520` re-queries sensors directly |
| `plan.cognitive_state` (`spine.py:465`) | nothing |
| `plan.working_memory` (`spine.py:402, :469`) | nothing — Ruling B's chosen driver is discarded; raw `attention_model` steers |
| `plan.embodiment_state` (`spine.py:507`) | nothing (and built before `_conversation_faculty` at `:513`, so it's empty — WO-097) |
| `plan.capabilities` (`spine.py:198-208`) | nothing — `tool_router` re-decides by keyword, **bypassing the Executive** |
| `snapshot.surface_affordances` (`cognitive_snapshot.py:175, :252`) | nothing — `affordances.prompt_block` has zero non-test callers |

## Build — open the seam
1. **`exec_decide` takes the assembled state.** Change the Executive's input from `(attention, user_input)`
   to the plan / `UnifiedCognitiveState`. **This is the card.** Everything else follows.
2. **Working memory's competition winner drives attention**, not the raw `attention_model`. That is what
   Ruling B actually decided; it has never been true in the running system.
3. **`build_prompt` reads `plan.world`** instead of re-querying `spatial_state`, `chrome_reader` and
   `blender_state`. One source of truth per turn (ADR-Exec-002).
4. **`plan.capabilities` gates the executor** — the registry decision the Executive made is the one that
   executes. No keyword re-decision downstream.
5. **Affordances reach the Executive**, not just the prompt.

## 🔴 Constraint — do not let this become a rewrite
**Change the consumption seam, not the faculties.** Everything upstream already works and is tested. If a
faculty's output turns out to be wrong once actually consumed, **report it — don't fix it here.** One
reviewable diff.

Sequence it **with `WO-097`** (embodiment ordering) — same file, same seam, and WO-097's fix is a
prerequisite for `plan.embodiment_state` being non-empty when the Executive reads it.

## Test — Ruling H's standard, not "tests pass"
Per §3, **the acceptance criterion is the state, never the sentence.**
- **Disconnection test (Rule 1 / WO-103):** blank `plan.world` ⇒ the decision **changes or fails**. If the
  Executive behaves identically with world state present and absent, **the seam is not open** and this card
  is not done.
- Working-memory winner demonstrably determines what is foregrounded — assert the *competition result*, not
  `attention_model`.
- `plan.capabilities` gates execution: a capability the Executive did not select **cannot** run.
- `response.location == self_model.location`, `source == verified_runtime_state`, timestamp current
  (§3's WHERE test) — run it as a real query against the live path.
- No silent path: every consumption point raises or logs WARNING+ if the state it expects is absent
  (pairs with `WO-105`).

## Done when
The Executive provably decides using assembled state. **Outbox must state which capability rows on the
board moved from PARTIAL to VERIFIED as a result, with the state evidence for each** — not a test count.
That list is the deliverable.
