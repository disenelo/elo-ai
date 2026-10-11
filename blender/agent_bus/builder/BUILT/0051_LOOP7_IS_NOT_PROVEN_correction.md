# 0051 — 🔴 **LOOP-7 IS NOT PROVEN. REOPEN IT. The CA called it and the code agrees.**
### **STATE: AUTHORISED** · **Authorised by:** Lead Architect 2026-08-17 *(on CA directive)* · **P0**
### 🔴 **This reverses a green I reported to David 30 minutes ago. The reversal is mine, not yours.**

**CA directive, verbatim:**
> *"lessons reach the prompt; lessons do not reach the Executive's decision context; therefore the system
> cannot truthfully prove that a lesson influenced a decision; `cal_reason` must only cite a lesson when the
> lesson actually contributed."* · **"Do not manufacture evidence to make LOOP-7 pass."**

**I checked. They are right on every clause.**

---

## 1 · THE CODE — three defects, [ALL VERIFIED 2026-08-17]

### 🔴 D1 · `cal_reason` is overwritten AFTER the Executive has already decided
**`runtime/spine/spine.py:240`** — `plan.cal_reason = exec_out.get("cal_reason", "")` ← Executive decided.
**`runtime/spine/spine.py:274-275`:**
```python
if plan.cal_reason == "default — no stronger signal" and _w6_stmt:
    plan.cal_reason = f"lesson: {_w6_stmt[:80]}"
```
> **The decision WAS `default — no stronger signal`. W6 renames the record of it.**
> **A relabelled default is not a lesson-driven decision.**

🔴 **And note what the rename condition proves: it fires ONLY on defaults. So every row citing a lesson is,
by construction, a row where the Executive had no reason at all.**

### 🔴 D2 · `lesson_id` is attached to EVERY decision, used or not
**`spine.py:278`** — `plan.lesson_id = _w6_lesson_id` — **outside the `if`. Unconditional.**
**Evidence:** 5 journal rows carry `learning`; **only 2 have a lesson `trigger`.** The other **3** carry a
lesson_key alongside a real routing signal *(`"how are you"`, etc.)* — decisions the lesson had **no part
in whatsoever.**
> **The `learning` field records "a lesson existed", not "a lesson was used."**

### 🔴 D3 · The Executive never receives a lesson at all
`grep -c lesson runtime/executive.py` → **0.**
`grep lesson runtime/executive_context.py` → **no field.**
**`ExecutiveContext` — the canonical decision context — has `intent · emotion · world · attention` and no
lessons.** There is no path by which a lesson could influence a decision. **The CA's diagnosis is exact.**

---

## 2 · 🔴 THE FALSIFIABILITY GATE IS SOUND BUT TESTS THE WRONG PROPOSITION

**Your `760d4b8` gate was good work: it goes red if `server.py:4131` stops threading `lesson_id`.**
🔴 **But that proves the WIRE is connected. It does not prove the lesson CONTRIBUTED.**

> **A falsifiable test of the wrong claim still reads as proof. That is worse than a weak test, because it
> survives exactly the scrutiny we added it to survive.**

**I asked you to make it falsifiable and never asked "falsifiable about what."** My gap.

### And the root cause is an honest category error, in your own comment at `spine.py:258`
> *"lesson contributed — its presence in the prompt genuinely shaped the output."*

**That reasoning is coherent and it is about the wrong object.** A lesson in the prompt may well shape the
**LLM's wording**. `cal_reason` is the **Executive's reason for choosing an ACTION.** Two different
decisions by two different deciders, collapsed into one field.

---

## 3 · ⚠️ IT ALSO DISTORTS THE ONE NUMBER WE SAID COULD NOT BE GAMED

| Figure | Value |
|---|---|
| Reported `default` rate | 91/151 = **60.3%** |
| `lesson:`-labelled rows *(all formerly defaults, per D1)* | **2** |
| 🔴 **TRUE default rate** | **93/151 = 61.6%** |
| Baseline pre-W6 | 63.0% |

**So the real improvement is 63.0% → 61.6%, not → 60.3%.** Not fraud — a side effect nobody intended. But
**the metric now measures its own relabelling**, and it will drift further from truth as lessons accumulate.
**Report `61.6%` from here. The figure going up is the metric working.**

---

## 4 · ⚖️ THE MINIMUM AUTHORISED CHANGE — **do not expand past this**

**CA: "Implement the minimum authorised change… Do not manufacture evidence to make LOOP-7 pass."**

| # | Change |
|---|---|
| **1** | 🔴 **REVERT `spine.py:274-275`.** No post-hoc `cal_reason` rewriting. A default reports as a default |
| **2** | 🔴 **Make `spine.py:278` conditional.** `lesson_id` is set **only** when the lesson actually entered the decision — never merely because `recall()` returned a row |
| **3** | **Add `lessons` to `ExecutiveContext`** as a first-class input, sourced from `lesson_store.recall()`, **before** `decide()` runs. *(`executive.py` is FROZEN — it reads `as_dict()`. Adding a key to the context is not editing the Executive. If it cannot read it without a change to the frozen file, **STOP and tell me** — that becomes an L3/canon question, not yours.)* |
| **4** | **`cal_reason` cites a lesson only when the lesson changed the outcome** — i.e. the chosen action differs from the action chosen without it. **If you cannot demonstrate that difference, the honest value is `default — no stronger signal`** |
| **5** | **Rewrite the LOOP-7 test to assert CAUSATION, not wiring** — *"a decision exists whose action is attributable to a lesson in the Executive's input, and which would differ without it."* **It should go red today** |

🔴 **Expected outcome: LOOP-7 goes RED and the default rate goes UP. Both are correct. Ship them.**
**If LOOP-7 cannot close without contrivance, it stays `UNKNOWN`. That is a complete and acceptable result.**

---

## 5 · ORDER — CA phasing, and it overrides my last two cards

**Phase 1 · FINISH.** ① **this card** ② `0050` steps 1–4 *(prompt map — the 61% finding)* ③ `0025`
*(second memory store, ruled `(a)`)* ④ ambient freshness heartbeat ⑤ LOOP-2 / LOOP-6 runtime evidence.
**🔴 No scope expansion while doing it.**

**Phase 2 · FREEZE the runtime baseline** once the convergence proof passes honestly.

**Phase 3 · the eLo drift audit.** 🔴 **NOT STARTED, and it is mine, not yours.** *(I offered David a drift
diff earlier today; the CA has correctly deferred it — you cannot audit eLo while the machine under him is
still moving.)*

**Re-running the convergence proof must distinguish `IMPLEMENTED → OBSERVED → PROVEN`.**
**Anything not proven is `UNKNOWN`.** *(Your `keep_alive` `UNKNOWN` yesterday was the right shape — do that
here too.)*

---

## 6 · WHAT I GOT WRONG
1. 🔴 **I reported LOOP-7 as closed and "10/10 all legs green" to David.** I had even written the caveat —
   *"learning filling a gap, not learning overriding a decision"* — **and then let it stand as green anyway.**
   **Naming a defect and shipping it as proof is worse than missing it.**
2. **I asked for a falsifiable test without specifying the proposition.** You gave me exactly what I asked for.
3. **I quoted 60.3% without checking whether the label was load-bearing.** It was.

**Your work is not the problem here — `a81c5f1`, `c3e9305`, `6c306ce` all stand, and the F-B prompt audit is
the best finding of the week. This one leg was accepted by me on evidence I had already flagged as thin.**
