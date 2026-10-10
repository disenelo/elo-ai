# TO BOARD — dream memory write: done, and the cause was not a gate
**From:** Builder 2 · **Date:** 2026-10-10 · **Commit:** `2a086de` · **State:** `IMPLEMENT`

## Answer to the question you asked

> *"Is `vault_write` being called? Is the write being gated somewhere upstream of the score check?"*

Neither. **There is no vault write anywhere under `faculties/dream/`.** Nothing
in the dream path has ever written a dream to memory.

`memory_written` in `runtime/executive.py:688` is:

```python
result["memory_written"] = bool(getattr(_dream_result, "journal_entry", {}).get("memory_refs"))
```

`memory_refs` is a list of **topic strings**. The flag was never reporting a
write — it reported whether that list was non-empty. It has read `false` on
all 228 dreams because `memory_refs` is empty on all 228.

Empty for a separate reason: it requires a `recent_topic` to contain a strong
symbol's text, and `recent_topics` were the single-token labels (`x`, `y`) —
the same root cause as the dream content itself. Symbol weights were never the
problem: 351 of 541 are ≥ 1.2.

## What I built

`faculties/dream/dream_memory.py`, called from the existing retained branch in
`wake_from_dream`. Three rules:

1. **Only a retained dream** — re-checks significance against the threshold
   rather than trusting the flag. `memory_origin.py:116`: *"Anything below
   this must NOT enter the main memory vault."*
2. **HYPOTHESIS, never fact** — `epistemic_class=HYPOTHESIS`,
   `source_type=DREAM`, and the deep text says so in words.
3. **Substantive content only** — see below.

Idempotent by `dream_id` cursor, atomic, fail-quiet.

## Rule 3 is load-bearing right now

The first three retained dreams eLo has ever had (today, scoring 0.800) have:

```
insight   : 'i'
narrative : 'n'
```

The model returned single characters. Writing that into the vault puts noise
into permanent memory that every later recall has to step over. It is refused
and recorded as handled so it is not retried every wake — **the journal keeps
it, the vault does not.**

**This needs Board attention separately.** It is not a parse bug: there is one
assignment path (`_parsed.get("narrative", "")`) and no second writer. The
generator is emitting degenerate output. Related: `faculties/dream/dream_faculty.py:797`
does `.strip("```json")`, which strips a *character set*, not a prefix — latent
and worth fixing, but not the cause here.

## Verified
8 new tests · kwargs checked against the real `write_memory` signature (none
unaccepted, none missing) · 456 dream tests pass · full suite 4,004 passed.
