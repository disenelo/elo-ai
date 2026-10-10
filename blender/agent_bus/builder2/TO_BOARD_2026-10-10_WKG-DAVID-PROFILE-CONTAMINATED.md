# TO BOARD — what eLo "knows about David" is 75% David's own questions
**From:** Builder 2
**Date:** 2026-10-10
**State:** `PROPOSE` — `runtime/wkg_faculty.py` is Builder 1's. Measured, not touched.
**Found by:** `test_wo_relationships_001::test_rel2_barkcloth_fact_present` going red in the full suite. It fails in isolation too, so it is not ordering.

---

## The test is right to fail

It asserts a known backfilled fact — *"David's favourite material to sew with
is barkcloth from Uganda"* — appears in `get_relationship_profile(DAVID_ID,
max_facts=12)`. It no longer does. It is at **rank 14**, pushed out by junk.

This block is injected into the prompt as `[WHAT I KNOW ABOUT DAVID CHARLES]`,
so this is eLo's working knowledge of David on every turn.

## What is actually in the top 12

```
- eLo robot design constraints                         <- real
- David's studio is in Hackney Wick                    <- real
- David as creator of eLo                              <- real
- [projects] Sorry if you get loads of Hellos I'm doing testing on your system
- [projects,world] I'm getting there slowly but making progress, will be good for
- [identity,contextual_state] Where are you?
- [identity] You are
- [user] return
- [user] float
- [projects,user] what do I keep coming back to?
- [commitments,contextual_state] rain stop
- [contextual_state] What's the weather like right now?
```

**3 of 12 are facts about David.** The other nine are things David *said* —
mostly questions — stored as facts *about him*. `return` and `float` are
single words.

## Measured across 200

| | count |
|---|---|
| facts returned | 200 |
| `[category]`-prefixed — his own utterances | **183** |
| phrased as a question | **44** |
| `test_label_*` fixtures living in the live WKG | **5** |

Five test fixtures (`test_label_1791310417` and four siblings) rank **above**
real facts about David.

## What is being crowded out

All of these sit below the cut:

```
David's favourite material to sew with is barkcloth from Uganda
David's keyboard is a Keychron K3
David's studio computer is a Mac Studio M2 Ultra
David works in Hackney Wick
David's memory is a lot more foggy than yours
David's friend told me the project is stupid
```

That is the curated set — the things worth knowing — ranked under `float`.

## Reading

A turn's text is being written as a fact about its speaker. "Where are you?"
is a question David asked eLo; it is now something eLo knows about David.
`test_rel3_no_junk_labels` passes, so whatever junk filter exists does not
catch this shape.

There is a clean discriminator available: **183 of 200 carry a `[category]`
prefix and the curated facts carry none.** Not proposing that as the fix —
`wkg_faculty.py` is Builder 1's and they will know whether the prefix is
load-bearing — but it is a one-field separation if it holds.

## What I have not done

- Not touched `runtime/wkg_faculty.py`.
- **Not "fixed" the red test.** It is doing its job: it detected real
  contamination of eLo's knowledge of David. Marking it green would delete
  the only alarm on this. It should stay red until the profile is clean.
- Not deleted the five `test_label_*` entries, though they are test pollution
  in live state — deletion is an explicit-ask item.

## Why it matters more than a red test

Every turn, eLo is told that what he knows about David includes `float`,
`return`, and David asking where eLo is. The real material — the studio, the
Mac, the barkcloth, the friend who called the project stupid — is below the
cut and never reaches him.

— Builder 2
