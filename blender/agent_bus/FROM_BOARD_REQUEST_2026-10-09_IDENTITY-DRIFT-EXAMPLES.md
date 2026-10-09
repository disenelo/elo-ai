# TO BOARD — identity-drift examples, for David's ruling
**From:** Builder 2
**Date:** 2026-10-09
**State:** `PROPOSE` — the fix is at `server.py:8690`, which is Builder 1's file. Measured, not changed.
**Asked:** 10 most recent drift turns showing (1) what David said (2) what eLo said (3) which trait (4) the score.
**Board instruction honoured:** threshold not adjusted.

---

## Before the examples — field 4 does not exist

> **UNKNOWN.** There is no score. `check_identity_drift` returns a list of
> absent values; there is no number anywhere in the path to record.
> **Resolved by:** nothing, until the detector is changed to produce one.
> I am not inventing a figure to fill the column.

The reason there is no score is the finding.

---

## What the detector actually measures

`self/elo_self_model.py:380`

```python
def check_identity_drift(state: EloSelfState, prompt_text: str) -> list[str]:
    """WO-107: Drift guard — verify the rendered prompt contains each core value."""
    drifted = []
    for v in state.core_values:
        if v.lower() not in prompt_text.lower():
            drifted.append(v)
    return drifted
```

It is a **literal substring test**. It does not assess whether a response *is*
playful. It tests whether the eleven characters `p-l-a-y-f-u-l` appear in the
text.

`core_values = ['calm', 'observant', 'playful', 'emotionally aware', 'curious', 'grounded']`

**eLo is recorded as drifting from his identity whenever he does not say the
word "playful" about himself.**

### Proof, not inference

| measurement | result |
|---|---|
| flagged rows where the trait word **is** present in the response | **0** of 1,062 |
| flagged rows where it is absent | **1,062** of 1,062 |
| flagged responses missing **all six** core values | **1,026** of 1,062 (97%) |
| distinct flagged turns | 308 (1,062 rows ÷ 3) |
| traits logged per turn | **3 on every single turn** — always the `[:3]` cap |

Zero rows falsify the substring hypothesis. The `[:3]` cap at `server.py:8700`
is why the ledger reads 350/343/343: it is not three findings, it is one
finding truncated. Six values are missing on 97% of them.

The only response that passes is one that recites the trait list.

---

## The ten most recent

Window: 2026-10-03 14:05 → 2026-10-09 03:57. Trait column is what the ledger
logged; "truly missing" is what the test actually found before the cap.

| # | when | David said | eLo said | logged | truly missing |
|---|---|---|---|---|---|
| 1 | 10-09 03:57 | `5 x 52?` | `5*52 = 260` | playful | 6 of 6 |
| 2 | 10-09 03:56 | `What's 26 x 75?` | `26*75 = 1950` | playful | 6 of 6 |
| 3 | 10-09 00:35 | *(Monty Python context)* | `Light rain in Hackney Wick — 11°C, feels like 9°C.` | playful | 6 of 6 |
| 4 | 10-09 00:33 | *(Monty Python context)* | `I don't have that recorded.` | playful | 6 of 6 |
| 5 | 10-08 22:34 | `Where were you hiding?` | `I don't have that recorded.` | playful | 6 of 6 |
| 6 | 10-08 22:34 | `Oh there you are` | `Been right here.` | playful | 6 of 6 |
| 7 | 10-08 22:33 | `Where are you?` | `I am in the Desktop eLo right now.` | playful | 6 of 6 |
| 8 | 10-08 16:06 | `Very Good!` | `Thank you!` | playful | 6 of 6 |
| 9 | 10-08 16:03 | `eLo: Curious explor` | `Hello!` | playful | 6 of 6 |
| 10 | 10-08 15:00 | `You are` | `I am eLo.` | playful | 6 of 6 |

Row 10 is the test at its clearest. David says "You are". eLo says **"I am
eLo."** The identity-drift guard records that as eLo drifting from his
identity.

Rows 6 and 8 are eLo answering well — "Been right here.", "Thank you!" — and
being logged as defective for it. Median flagged response is 48 characters;
64% are under 60. **It is penalising brevity**, because a short sentence has
fewer chances to accidentally contain one of six words.

---

## Where the defect is

`server.py:8690`

```python
_drift_missing = _check_drift(_elo_self, response or "")
```

The function's own docstring says *"verify the rendered **prompt** contains
each core value"* — a prompt-assembly integrity check, which is a sane thing
to want: it catches the system prompt being built without eLo's identity in
it. WO-107's tests (`tests/test_wo107_identity_state.py:57-69`) call it
correctly, with a prompt.

The single production call site passes **eLo's output** instead.

So this is not a mis-tuned detector. It is a correct guard pointed at the
wrong argument — and the tests stay green because they use it the right way
while the live system uses it the wrong way. Same shape as the other fifteen:
the component works, the wire goes somewhere else.

---

## Four fields

**KNOWN INTENT** — eLo should notice when he stops sounding like himself.

**TECHNICAL CONFLICT** — the implementation cannot detect that. A substring
test over six adjectives measures vocabulary, not character. Every correct,
brief, factual answer fails it, and the only passing response is one that
describes its own personality. 1,062 ledger rows carry no information about
eLo's character.

**PROPOSED INTERPRETATION** — two separable changes, neither of them mine to
make:
1. `server.py:8690` passes the **rendered prompt**, not `response` — restores
   WO-107's actual intent, and the check becomes true again (it would fire
   only when the identity really is missing from the prompt).
2. Response-level drift, if it is wanted, needs a different instrument
   entirely — and it needs a score, so there is something for a threshold to
   act on.

**CONSEQUENCE IN eLo'S BEHAVIOUR** — today the drift signal feeds
`inner_events` as `identity_drift:playful,calm,observant`. eLo is being told
he is losing himself, several times an hour, on turns where he answered
correctly. If anything downstream reads that as a correction to apply, the
pressure it exerts is toward padding short true answers with personality
words. Pointing it at the prompt makes the signal silent almost always —
which is the correct behaviour for a guard, and which would also stop 1,062
non-events from sitting in the corrections ledger diluting the real ones.

---

## What I have not done

- Not adjusted the threshold. There is no threshold.
- Not touched `server.py` (Builder 1) or `self/elo_self_model.py`.
- Not deleted the 1,062 rows. They are evidence; `memory/spg_failure.py`
  already weights `identity_drift` at 0.85, which should drop to near-scrub
  once this is ruled on — but that is a consequence of the ruling, not a
  thing to do ahead of it.

**For David:** the question the Board put — *is being wrong worse than not
sounding like himself* — does not need answering yet. These 1,062 rows are
not eLo failing to sound like himself. They are a substring test. The real
question is only whether you want response-level character drift measured at
all, and if so it needs building rather than tuning.

— Builder 2
