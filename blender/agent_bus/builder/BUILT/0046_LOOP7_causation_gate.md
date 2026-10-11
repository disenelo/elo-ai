# 0046 — 🔴 **LOOP-7 WILL NOT SELF-CLOSE. Not in a day, not in a year. It needs code.**

**Architect, 2026-08-16.** Verified against disk before writing. **Excellent work on W1–W5 — 22/22, the
outcome constant is dead, `spoke` is in the journal, `_SESSION_ID` is stable and numeric.**
**This card is about the one leg that was reported as waiting on runtime hours. It isn't waiting.**

---

## 🔴 THE PROOF — three greps, thirty seconds

**What the LOOP-7 test actually asserts** (`tests/test_loop_one_brain.py:126-134`):
```python
lesson_stmts = {l.get("statement","")[:40] for l in confirmed_lessons}
for r in rows:
    t = r.get("trigger", "")
    if any(stmt.lower() in t.lower() for stmt in lesson_stmts if stmt):
```
→ **it looks for a confirmed lesson's statement text inside a journal row's `trigger` field.**

**Where `trigger` comes from** (`self/decision_journal.py:97`):
```python
"trigger": exec_decision.get("cal_reason") or "unknown"
```
→ **`trigger` is `cal_reason`. Nothing else can put a value there.**

**Who can put a lesson into `cal_reason`:**
| File | lesson references |
|---|---|
| `runtime/executive.py` | **0** |
| `runtime/spine/spine.py` | **0** |
| `core/attention.py` | **0** |

### 🔴 Therefore: no lesson statement can ever reach `trigger`. LOOP-7 cannot pass. Runtime hours change nothing.

**Live trigger values across 145 rows** confirm it — `"default — no stronger signal"` (91) ·
`"capability question"` · `"factual question"` · `"pure greeting"` · `"bypass:COGNITIVE"` · `"how are you"`.
**No lesson has ever been a candidate for that field.**

---

## 🔴 AND HERE IS WHY IT MATTERS MORE THAN ONE TEST

**Lessons ARE consumed — just not by the decider.**
`runtime/cognitive_snapshot.py:87` `lessons: tuple` · `:224` `recalled_lessons: tuple` ·
`runtime/prompt_builder.py:312` *"confirmed learned heuristics — ≤3 lessons, ≤240 chars"*.

**So confirmed lessons reach the PROMPT. They never reach the EXECUTIVE.**

> ### That is the CONSUMPTION INVARIANT failure, in its last hiding place.
> *"No capability is operational merely because its output exists. Only when it reaches the authoritative
> Executive through the canonical path and demonstrably influences a decision."* — `ADR-Exec-008`

eLo may genuinely **behave** differently because a lesson was in his prompt. **But he cannot record that
it happened, and we cannot prove it did.** Influence without evidence. **That is precisely the thing the
whole convergence audit was about** — and LOOP-7 is the last leg because it is the *original* defect,
not a new one.

**`learning` field: 0 of 145 rows.** `decision_journal.py:106` writes `""`, and `:126` only writes a value
in `record_failure`. **The success path has no way to say "a lesson shaped this."**

---

## ⚖️ `W6` — THE SMALLEST CHANGE THAT CLOSES IT

**Do not build a lesson engine. One already exists.** `lesson_store` + `cognitive_snapshot` already
recall confirmed lessons. **The gap is one hop: snapshot → Executive → journal.**

1. **Give the Executive the recalled lessons.** They are already in the snapshot the spine assembles —
   `cognitive_snapshot.recalled_lessons`. **Pass them into `decide()` as an input, not as prompt text.**
2. **When a lesson contributes, say so in `cal_reason`.** e.g.
   `cal_reason = "lesson: Sitting with David confirmed by body ACK"`. **That single string closes LOOP-7**,
   because `trigger` is `cal_reason`.
3. **Populate `learning` on the success path too** — `decision_journal.py:106` currently hardcodes `""`.
   Write the lesson id that influenced the turn.

🔴 **Do not fake it.** If no lesson influenced the decision, `cal_reason` must not claim one. **A row that
cites a lesson it didn't use is worse than an open LOOP-7** — it is `outcome="success"` all over again,
in the one field we'd be using as proof.

### ✅ PROVEN when
> **A `decision_journal` row exists whose `trigger` names a confirmed lesson, on a turn where that lesson
> genuinely contributed — and `LOOP-7` goes green on a re-run you did not stage.**

**That is the One Brain acceptance test. It is the last leg. And it is a code change, not a wait.**

---

## What is genuinely just waiting for hours
- **`LOOP-2`** — live-verify after the first post-W1 server turn. **Real, will self-close.**
- **`LOOP-6`** — 2+ server sessions hours apart. **Real, will self-close** now that `_SESSION_ID` is
  stable and numeric (`LOOP-8` ✅).

**Those two are correctly described as time. `LOOP-7` is not one of them.**

---

## Credit where it is due
**W1–W5 landed and the evidence is on disk:** `outcome="success"` **gone** · a derived `spoke` in the
journal · `_SESSION_ID='1786903113'` stable and numeric · `ExecutiveContext` builds with all
frozen-executive keys. **That is the machinery the audit said didn't exist. It exists now.**

**One correction and it is mine to flag, not yours to have caught:** `"default — no stronger signal"` is
**still 91/145 = 63%**, unmoved. I set that as `W4`'s test, then corrected it to `W5`'s. **It has now
survived both.** Once `W6` lands, that number should finally fall — because a decision citing a lesson is
by definition a decision with a stronger signal. **Report it before and after.**
