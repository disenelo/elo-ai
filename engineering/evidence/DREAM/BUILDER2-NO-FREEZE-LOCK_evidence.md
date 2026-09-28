# BUILDER2-NO-FREEZE-LOCK — dream insights can now reach the Executive

**Filed by:** Builder 2 · 2026-09-28
**Directive:** `FROM_ARCHITECT_2026-09-27_BUILDER2-NO-FREEZE-LOCK.md`
**Authority:** David L3 — "I do not want to see FREEZE LOCK."

---

## WHAT I FOUND WHEN I OPENED THE FILE

The directive asks me to remove `FREEZE_V1_LOCK` from the Executive's
speak/emit path for dream insights.

**There is no such lock.** `FREEZE_V1_LOCK` appears three times in
`runtime/executive.py` and every one is a comment:

- line 367 — `§5 — the nine, verbatim`: the nine CAL actions are a frozen
  set. A learned preference may select among them and may never extend them.
- line 424 — records David's earlier ruling `"SO UNFREEZE it"`, already
  applied so the Executive may ask the Learning Faculty.
- line 430 — repeats that a lesson may shift *which* of the nine is
  preferred, never introduce a tenth.

It is a documented invariant about the CAL action set. It is not a runtime
switch, and it was not what stopped a dream insight being acted on.

Removing it would have deleted a real constraint and fixed nothing.

## WHAT WAS ACTUALLY STOPPING IT

`server.py:1094`:

```python
_top_intent: dict = dict(_intents[0])
```

**One intent is consumed, and it was chosen by list position.** Precedence
was a side effect of the order proposers happen to be written in
`internal_intents()`.

A dream requires >= 600s idle. `exploration` fires at >= 300s and is written
first. So whenever a dream insight existed, `exploration` was already ahead
of it — the retained insight was proposed and then **silently discarded,
every time.**

### I need to correct my own earlier evidence

`WO-DREAM-ENGINE-001_PHASE8_executive_routing_evidence.md` says the dream
"reaches the arbiter". That was wrong. It reached the proposer's output
list. It never reached the Executive, because the consumer dropped it one
line later. I did not trace past `internal_intents()` and I should have.

## THE FIX

Salience. Every intent now carries one, and the consumer selects the
maximum rather than the first.

| intent | salience |
|---|---|
| `dream_insight` | 0.75 |
| `exploration` | 0.60 |
| `return_to_thread` | 0.50 |
| `micro_goal` | 0.30 |

Defaults **descend in the previous list order**, so this is
behaviour-preserving for the existing intents — exploration still beats
return_to_thread still beats micro_goal, exactly as before.

`dream_insight` sits just above exploration. Not to bypass it: it is the one
intent here that had to clear a gate to exist at all (0.72). Routine idle
curiosity fires on any five quiet minutes; a retained dream does not. The
margin is 0.15, it is still `priority: low`, and it is still below 1.0 — it
competes, and a future higher-salience proposer will beat it.

## WHAT STAYS UNCHANGED, PER THE DIRECTIVE

- `internal_intents()` remains the sole proposer (WO-INGRESS-32)
- `surfaces_directly: false` on the faculty — the faculty does not speak
- the 0.72 gate still decides whether a dream proposes at all
- low priority — dream insights compete, they do not bypass
- the nine CAL actions remain frozen; I removed no invariant

---

## WIRE-CUT PROOF

Cut: revert the consumer to `_intents[0]`.

```
WIRE CUT: consumer back to _intents[0]
FAILED test_server_selects_by_salience_not_list_position
1 failed, 18 passed
```

Restored:

```
19 passed in 0.09s
```

---

## REAL RUN — both branches

```
UNRETAINED dream (below 0.72)
   exploration      salience=0.6   priority=low  <-- selected
   return_to_thread salience=0.5   priority=low
   reaches Executive: exploration

RETAINED dream (>= 0.72)
   exploration      salience=0.6   priority=low
   return_to_thread salience=0.5   priority=low
   dream_insight    salience=0.75  priority=low  <-- selected
   reaches Executive: dream_insight
   trigger: woke from dream — the arm stalls at the same angle

BEFORE this change the consumer took _intents[0] — exploration, always.
A dream needs >=600s idle; exploration fires at >=300s, so it was always first.
```

## REGRESSION

`self/emergent_cognition.py` is shared. Every consumer re-run:
`test_ingress32_ambient_retirement`, `test_wo114_self_choose`,
`test_wo125_self_interpret`, `test_0013_wave5_reflect_history_look_selfchoose`,
`test_wo115_reflect_and_autobiography`, `test_000b_five_surgical_fixes` —
all PASS.

## NOT PROVEN — and this is the directive's own test

The directive names the test that matters:

> A retained dream fires in production on the live server. The Executive
> receives it, decides to surface it, and eLo expresses something from it.

That has **not** happened. What is proven is that a retained dream now wins
selection and is handed to the Executive. Whether the Executive chooses to
speak it, and what eLo then says, is the Executive's own logic running on a
live turn.

No dream has yet fired on the live server. The journal's newest real-looking
entries are still test-written.

## STATUS

`IMPLEMENTED → WIRED → TESTED`. Not LIVE VERIFIED. Not declaring PASS.
