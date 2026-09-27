# WO-DREAM-ENGINE-001 PHASE 8 — routed to the Executive (final half)

**Filed by:** Builder 2 · 2026-09-27
**Runtime:** `/Users/Disenelo/miniconda3/bin/python3` 3.13.13

---

## STATE BEFORE

PHASE 8's gate ran and its outputs were written to the journal (`39dec98`),
but **nothing downstream read them.** A dream could clear the retention gate
and waking cognition would never learn of it. The journal was a dead end.

## WHAT CHANGED — and what I deliberately did NOT build

The WO says: *"Executive decides what surfaces to waking cognition. Dream
Faculty does not speak directly."*

The obvious implementation is a dream→Executive channel. **That would have
been wrong.** WO-INGRESS-32 makes `internal_intents()` the *sole proposer*,
and `server.py:1004` says so in a comment. A second channel would quietly
retire that rule.

So the dream proposes through the existing proposer, at low priority, like
every other intent, and the Executive arbitrates exactly as it already does:

| File | Change |
|---|---|
| `faculties/dream/dream_faculty.py` | `wake_from_dream()` appends a `dream_insight` inner event **only when the dream cleared retention** |
| `self/emergent_cognition.py` | `internal_intents()` proposes a `dream_insight` intent when that marker and the dream read are both present |

No bypass. No new channel. The faculty still has no `speak`/`emit`/`say`,
and `for_executive()` still declares `surfaces_directly: false`.

## THE GATE DECIDES WHETHER ANYTHING SURFACES

An unretained dream leaves no marker. It stays in the journal and never
reaches the proposer. That is the PHASE 8 semantic made mechanical — the
0.72 threshold is not advisory bookkeeping, it is what decides whether eLo
can bring a dream into waking thought at all.

---

## WIRE-CUT PROOF

Cut: remove the retention gate so every dream proposes.

```
WIRE CUT: retention gate removed — every dream proposes
FAILED test_an_unretained_dream_proposes_nothing
FAILED test_a_dream_with_no_journal_entry_does_not_propose
FAILED test_the_marker_alone_is_not_enough_without_the_insight
FAILED test_the_marker_ages_out_of_the_event_window
4 failed, 8 passed
```

Restored:

```
12 passed in 0.09s
```

---

## REAL RUN — both branches on the real path

```
retention threshold: 0.72

UNRETAINED (significance 0.1)
   retained            : False
   inner_events         : ['creative_spark', 'connection']
   intents proposed     : ['exploration']
   dream reached Executive: False

RETAINED (significance 0.95)
   retained            : True
   inner_events         : ['creative_spark', 'connection', 'dream_insight']
   intents proposed     : ['exploration', 'dream_insight']
   dream reached Executive: True
   proposal             : priority=low source=dream_review
   trigger              : woke from dream — the arm stalls at the same angle

```

Reading it:
- Significance 0.10 → not retained → no marker → **the dream does not reach
  the Executive.** `exploration` still fires; the dream simply is not there.
- Significance 0.95 → retained → marker → proposed at `priority=low`,
  `source=dream_review`, carrying the insight as its trigger.
- The dream joins the intent list. It does not replace or outrank anything.

## REGRESSION

`self/emergent_cognition.py` is shared, so every consumer was re-run:
`test_ingress32_ambient_retirement`, `test_0017_autobiography_provenance`,
`test_wo114_self_choose`, `test_0013_wave5_reflect_history_look_selfchoose`,
`test_wo115_reflect_and_autobiography`, `test_wo125_self_interpret` — all
PASS, plus 17 passed under pytest.

## NOT PROVEN

- **Not live.** No dream has fired on the running server (PID 9577, up 5h+,
  pre-`ff98065`). Both branches above ran out of process.
- **The Executive's decision is not exercised here.** This proves the dream
  *reaches* the arbiter. Whether the Executive chooses to speak it is the
  Executive's own logic, under FREEZE_V1_LOCK, and untouched.

## STATUS

PHASE 8: `IMPLEMENTED → WIRED → TESTED`, both halves — journal and routing.
Not LIVE VERIFIED. Not declaring PASS.
