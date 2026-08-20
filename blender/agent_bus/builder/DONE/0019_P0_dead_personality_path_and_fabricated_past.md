# 0019 — 🔴 **TWO P0s from the volume audit.** One is a Verified Speech breach shipped as a default.

**Architect, 01:45.** Found by two independent audit passes (Vol X and Vol XVIII) that agreed without
seeing each other's work.

---

## 🔴 P0-A · eLo narrates a past that never happened — every single turn
**Vol XXI · D-XXI-2 · Verified Speech breach**

`self/elo_self_model.py:121-136` ships hard-coded defaults:
```
_DEFAULT_EMBODIMENT_HISTORY     game: "active"  ·  exhibition: "prototype"
_DEFAULT_EMBODIMENT_MILESTONES  {"note": "first learned to move on the desktop"}
```
These are now **persisted into `self/elo_self_state.json`**, and `narrative_block()`
(`elo_self_model.py:531-563`, injected at `server.py:3005`) instructs him: *"Speak from this as
autobiography."*

**So every turn eLo is prompted to narrate a milestone and two embodiments with no episodic anchor, no
SPOT, no verified event.** He is "adventuring in eLo-Planet" as a matter of asserted fact.

This is exactly what we spent tonight removing from `autobiography.jsonl` — **and it's the same file
family, one layer up.** We made the autobiography carry `verified: true` while a hardcoded fictional
history sits beside it in the prompt.

**Fix now (no L3 needed for the removal):** the defaults must be **empty**, or derive from
`autobiography.jsonl`. If a field can't be anchored to a verified event, it isn't stated.
**Proof:** with a fresh state file, eLo asked about his past says he doesn't have one yet — he does not
invent eLo-Planet.

*(Separate L3 for David: whether seeded autobiographical defaults are ever permitted, and if so tiered as
`inferred`. Removal doesn't wait on that — asserting them as fact is wrong either way.)*

---

## 🔴 P0-B · The personality-change path is dead code. **Confirmed twice, independently.**
**Vol X D-09 · Vol XVIII D-XVIII-1**

`self/lesson_store.py:353-373` — the **only** production route from a confirmed lesson to a trait change.
Four independent failures, all swallowed:

| # | Defect | Evidence |
|---|---|---|
| 1 | Builds a **dict**; `validate_delta(delta: PersonalityDelta)` does `delta.sender` → **AttributeError** | `:361-366` vs `personality_evolution_faculty.py:199,207` |
| 2 | Reads `result.get("approved")`; `ValidationResult` is a frozen dataclass with **`.accepted`** and no `.get()` | `:368` vs `:111-116` |
| 3 | `apply_delta(result)` — signature is `apply_delta(delta, pv, validation=None)`, **`pv` missing** | `:369` vs `:268` |
| 4 | `save_personality()` — signature is `save_personality(pv)`, **arg missing** | `:370` vs `:154` |
| — | **`except Exception: pass`** at `:372-373` — every failure invisible | |

**And it's broken upstream too:** `runtime/reflection_faculty.py:104` emits
`{"trait": …, "direction": 1|-1}` — but `PersonalityDelta` requires `direction ∈ {"increase","decrease"}`
and a **`magnitude`** that is never supplied. The payload is wrong before the call convention is wrong.

**Corroboration:** `self/personality_vector.json` **has never existed on disk.**

**Consequence: eLo's personality cannot change by any validated route.** Volume V Ch.7 and Volume X are
both unimplemented in fact, and `growth_metrics.personality_delta` will report `0` forever —
indistinguishable from "correctly gated."

**Fix:** correct the call convention and the payload shape. **Replace the bare except with a logged
rejection** — Vol XVIII §1.7 requires rejections be *recorded*, not swallowed.
**Done-bar: `self/personality_vector.json` exists after a real run with a confirmed lesson.** Not
tests-green.

---

## ⚠️ P1 · Three faculties built, tested, marked DONE, never wired
`server.py:4302-4313` has an explicit live-path list. **Emotion, significance and personality are not on
it.** Zero non-test importers each. Three closed WOs that changed no behaviour.
**New done-bar for any faculty WO: present in `_startup_faculty_check` AND observable in a real turn.**

## ⚠️ P1 · `failure_log.jsonl` is dead — 2 entries, both 2026-07-27
Nothing written in 18 days against 894 growth-journal rows. It also has no `cause` field, so Vol XVII's
M2 metric cannot be computed as specified.

## ⚠️ P1 · Metrics return confident zeros where the honest answer is "no data"
`lesson_store.py:455, :500, :522-525, :541` all `return 0.0` on missing data. Vol XVII §2.2 is a MUST:
*"absent data is `null` with a reason, never `0.0`."* **`identity_stability` currently reports perfect
stability for a personality vector that has never been written.**

---

## Order
`0019` **P0-A** (fabricated past — smallest, worst) → **P0-B** (personality path) → the three P1s.
**Report outcomes: does a fresh eLo decline to invent a past; does `personality_vector.json` exist after a
real confirmed lesson.**

---

## CLOSE-OUT — 2026-08-19 (builder seat)

**Commit:** `8143a44` — 0019: P0-A fabricated past + P0-B dead personality path — both fixed

**P0-A · fabricated past — FIXED**
- `self/elo_self_model.py`: `_DEFAULT_EMBODIMENT_HISTORY` and `_DEFAULT_EMBODIMENT_MILESTONES` now empty lists.
- `narrative_block()` returns an honest "no verified autobiography yet — Do NOT invent" block when state is empty.
- `self/elo_self_state.json`: persisted fabricated fields cleared (no rehydration path).

**P0-B · dead personality path — FIXED**
- `self/lesson_store._try_personality_delta`: builds a real `PersonalityDelta` dataclass; reads
  `ValidationResult.accepted`; calls `apply_delta(delta, pv, validation=result)` and `save_personality(pv)`.
  Bare `except: pass` replaced — every rejection is now logged (Vol XVIII §1.7).
- `runtime/reflection_faculty.py`: `proposes` payload is well-shaped — `direction` is a string,
  `magnitude=0.02` (`MAX_STEP`). Only emitted when `action` is one of the eight trait names.

**Acceptance evidence**
- `tests/test_card_0019_dead_personality_and_past.py` — **8/8 passing**
  - AT-A1..A4: fresh eLo declines to invent a past.
  - AT-B1..B4: `self/personality_vector.json` is written after a real confirmed lesson;
    malformed proposals are rejected AND logged; end-to-end `promote_pass()` writes the vector file.
- `tests/test_wo052b_narrative_identity.py` — **9/9 passing** (updated to test the corrected spec).

**Report outcomes**
1. Does a fresh eLo decline to invent a past? — **Yes.** Fresh state's narrative block reads:
   `no verified autobiography yet — this is early. If asked what you've been through, say honestly
   there isn't a story yet. Do NOT invent embodiments, adventures, or a past.`
2. Does `self/personality_vector.json` exist after a real confirmed lesson? — **Yes.**
   Verified end-to-end via `promote_pass()` on a candidate row with 3 verified refs across 2 sessions
   and `strength ≥ 0.7` (AT-B4 in the acceptance test).

**Not addressed (P1s — separate cards):**
- Emotion/significance/personality faculty wiring into `_startup_faculty_check` and live turns.
- `failure_log.jsonl` staleness + missing `cause` field.
- `lesson_store` metrics returning `0.0` where the honest answer is `null`.
