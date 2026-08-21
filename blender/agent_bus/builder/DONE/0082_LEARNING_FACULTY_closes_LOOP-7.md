# 0082 — LOOP-7 · the Learning Faculty must change a real decision on a real turn

**WO:** WO-CANON-XXVIII / LOOP-7 · **Seat:** builder · **Priority:** 🔴 **P0 — Presentable v1 test 3**
**Reserved?** no · **STATE: AUTHORISED**
**LAYER:** `[DAVID]` — *"SO UNFREEZE it"* (2026-08-21) · *"Learns and asses not adopts, wants to learn
more, and there is a reason to why"* (2026-08-21)

---

## 0 · Where this actually stands

**Built and wired.** `faculties/learning/faculty.py` → `runtime/spine/spine.py:253` →
`plan.learning_advice` → `runtime/executive.py:314`. The counterfactual holds in isolation:
a fitting lesson flips `reflect` → `answer`; a conflicting one loses and raises curiosity instead.

🔴 **It has never run on a real turn, and the diagnosis below says it currently CANNOT.**
**Three separate faults. All found 2026-08-21 by the Architect. Do not treat this as one bug.**

---

## F-1 · ✅ The D1 gate is CORRECT. An earlier report of "no advice" was a malformed test.

`_evidence_is_verified` requires, **inside each evidence entry**: `verified: true` · a non-empty
`session_id` that is **not** pure-numeric · **and** an `action` or `outcome` naming a real executed thing.

A test lesson carrying `outcome` at the *top level* is correctly rejected. **The gate is not the problem.**
🔴 **Do not loosen it to make the card pass.** It mirrors the gate in `build_executive_context` (card `0075`)
and the two must not diverge.

---

## F-2 · 🔴 Every lesson in the live ledger FAILS the gate — on the session-id rule

`self/lessons_ledger.jsonl` — **2 lessons, 0 pass.**

```json
"evidence": [{"episode_ref": "1787263113.984", "verified": true,
              "ts": 1787263195.956118, "session_id": "1787261879"}]
```

**`session_id: "1787261879"` is pure-numeric — a process id, not a session.** Rejected by design.
The entry also carries **no `action` and no `outcome`**, so it fails the second condition too.

🔴 **So LOOP-7 cannot fire today: there is nothing the Executive is permitted to learn from.**
This is the actual blocker, and it is a **write-side** defect, not a faculty defect.

**Fix at the source.** `runtime/reflection_faculty.py:131` creates `"evidence": []` with the comment
*"filled by `lesson_store.record_outcome()` with SPOT codes"*. **Find what writes these entries and make it
emit a real `session_id` plus the executed `action`/`outcome`.**
⚠️ **Do NOT retrofit the two existing rows to make them pass** — that is manufacturing evidence. David:
*"Do not manufacture evidence to make LOOP-7 pass."* Leave them; generate correct ones going forward.

---

## F-3 · 🔴 A valid lesson still can't move a decision — the `_fit` floor

With a **correctly-shaped** lesson the faculty returns `fit=partial`, `confidence=0.0`, `preferences={}`.

Cause: `_fit()` returns `("partial", 0.5)` for any lesson with **no `scope` and no `applies_when`** —
*"A lesson with no stated conditions cannot claim to fit."* The Executive at `executive.py:314` requires
`confidence >= 0.5`. **A lesson without those fields can never reach the threshold.**

🔴 **This is correct behaviour for assessment and a real gap for the loop.** Both are true.
David: *"learns and **asses** not adopts"* — a lesson that doesn't state where it applies **should not**
push. But nothing currently *writes* `scope`/`applies_when`, so no lesson can ever qualify.

**So the write side must also emit `scope` (or `applies_when`) and the lesson's reason.**
`lessons_ledger.jsonl` rows already have a `scope` field and a `reason` field — **they are being left empty.**

---

## F-4 · ⚠️ Robustness — the pre-v1 ledger would crash the turn

`self/lessons_ledger_pre_v1.jsonl` holds **754 lessons whose `evidence` entries are STRINGS, not objects.**
`_evidence_is_verified` calls `ev.get("verified")` and raises `AttributeError: 'str' object has no attribute
'get'`. That file is not loaded today — **if it ever is, every turn dies.**

**Fix:** skip non-dict evidence entries defensively. **Do not migrate or rewrite the 754 rows.**

---

## Order of work

1. **F-2** — fix the write side so new lessons carry a real `session_id` + `action`/`outcome`.
2. **F-3** — same write path emits `scope`/`applies_when` and the `reason`.
3. **F-4** — one-line defensive skip for non-dict evidence.
4. **Then** run a real session, produce one qualifying lesson, and prove the loop.

## Wiring (required)

- **caller:** `runtime/spine/spine.py:253` — already in place
- **trigger:** a real turn where `lesson_store.recall()` returns ≥1 D1-passing lesson
- **observable:** `plan.learning_advice.preferences` non-empty **and** the chosen CAL action differs from
  what the Executive would have chosen without it

## Test — `tests/test_loop7_live.py`, RED when disconnected

1. **The counterfactual, on a real turn:** same input, lesson present vs absent ⇒ **different CAL action.**
   Both branches recorded in the outbox.
2. **Disconnection:** cut `spine.py:253` ⇒ the test goes **RED**. If it still passes, it proves nothing.
3. A lesson with a pure-numeric `session_id` ⇒ **still rejected** after the fix.
4. A lesson that conflicts with the situation ⇒ **loses**, and `curiosity > 0` with a non-empty
   `wants_to_know`.
5. Every emitted preference carries a traceable `reason`. **A preference with no reason is a bias** —
   assert it cannot be produced.
6. 754-row pre-v1 ledger loads without raising.

## Done when
built · **wired** · **exercised on a real turn** · **falsifiable**.
🔴 **Then and only then, Presentable v1 test 3 is met.** If the counterfactual does not hold — **report why,
honestly. `UNKNOWN` with evidence beats a false pass.**

## Result (seat fills this in)
- commit:
- test:
- the two transcripts (lesson present / lesson absent), verbatim:
- the qualifying lesson that was generated, verbatim:
- if it failed — what happened:
