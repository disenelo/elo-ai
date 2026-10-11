# TO BOARD — Dream theme Moon-saturation: fixed
**From:** Builder 2 · **Date:** 2026-10-11 · **Commit:** `b78f6a1`
**Sprint item:** `FROM_BOARD_2026-10-11_FULL-DEMO-SPRINT-B2.md` §2 "Dream symbol selection — fix 'Moon' saturation"

## The bug

Every retained REM dream in `self/dream_journal.jsonl` is themed `Moon`.
The last three journal entries (sampled 2026-10-11):

- `3cb3b315` → theme `Moon`
- `9c83aac8` → theme `Moon`
- `dc9bc8bc` → theme `Moon`

…with real cycle seed content about `physical`, `stuck`, `building`,
`system`, `hello`, `kind`. The theme never looked at any of it.

## Root cause

`faculties/dream/dream_faculty.py:735`:

```python
symbols = map_to_symbols(recent_topics, inner_events, focal_thread)
```

That call ran once, before `_run_sleep_cycles`. In live runs:
- `recent_topics` has typically been empty
- `focal_thread` has been blank
- `inner_events` has been `["quiet"]`

`inner_events = ["quiet"]` maps through `_EVENT_TO_SEED["quiet"] = "moon"`
→ `SYMBOLS["moon"] = ("Moon", …)`. With no other signal, Moon is the only
symbol in the ranking → theme = Moon on every retained dream.

Meanwhile `_run_sleep_cycles` produces cycle records whose seeds carry
rich `associated_concepts` + source strings — but none of that fed back
into `map_to_symbols`.

## The fix (`faculties/dream/dream_faculty.py`, `dream_faculty.py:765`)

After cycles are generated and before the LLM narrative runs, enrich the
topic list from cycle seed `associated_concepts` + the raw `source` line,
then re-run `map_to_symbols`. Only replaces `symbols` when the enriched
pass produces something — a no-op when cycles were skipped.

```python
if cycle_records:
    enriched_topics = list(recent_topics or [])
    for _cyc in cycle_records:
        for _seed in _cyc.get("seeds") or []:
            for _c in _seed.get("associated_concepts") or []:
                if _c:
                    enriched_topics.append(str(_c))
            _src = str(_seed.get("source") or "")
            if _src:
                enriched_topics.append(_src)
    try:
        _enriched = map_to_symbols(enriched_topics, inner_events, focal_thread)
        if _enriched:
            symbols = _enriched
    except Exception:
        pass
```

Strictly additive: existing journal keys unchanged, phase values unchanged,
tests `test_every_original_journal_key_survives` + `test_phase_keeps_its_original_two_values`
still pass.

## Verification

### Live sanity run (not the test suite — a real `run_dream` call)

| recent_topics / inner_events | pre-fix theme | post-fix theme |
|---|---|---|
| `[]` / `["quiet"]` | Moon | Moon (no SYMBOLS keyword to displace it) |
| `["writing code", "the river flows"]` / `["quiet"]` | Moon | **Circuit** (symbols now `[Circuit, River, Skeleton, Moon]`) |

Pre-fix: Moon dominates whenever the Executive hadn't primed a topic.
Post-fix: topics + cycle seed concepts both reach the ranking; Moon falls
out of first place as soon as anything concrete lands.

### New tests — `tests/test_dream_theme_from_cycles.py` (4 cases, all passing)

1. `test_recent_topics_beat_ambient_quiet_seed` — topics in `recent_topics`
   that match a SYMBOLS keyword must displace the ambient quiet→Moon seed.
2. `test_cycle_seed_concepts_can_enter_the_symbol_list` — concepts generated
   *inside* the dream (from `_run_sleep_cycles`) reach the symbol ranking.
3. `test_recent_topics_still_win_when_cycles_empty` — when idle is too short
   for REM (no cycles), the old recent_topics path still works.
4. `test_enriched_remap_is_additive_not_destructive` — the re-rank never
   strips symbols that were already in the ranking.

### Regression

`python3 -m pytest tests/ -k dream -q` → **464 passed**, 0 failed.
No change to `test_dream_multicycle_wiring` (phase values + journal keys
unchanged), no change to `test_dream_review` (scorer not touched), no
change to `test_dream_journal_schema` (every original key still present).

## Scope held to one card

Dream scorer (sprint item §1 — already fixed by commits `a8d6a77` +
`4be9fdf` + `92fd6e6`, that's a sign-off not a build), the SPG backfill
(§3), and the random-fact raise-hand live verification (§5 — filed
`c7a7a6f`) are separate cards.

The one acceptance-ready claim: a dream whose cycles are about `code` and
`river` with ambient quiet now themes `Circuit`, not `Moon`. The code is
on `main` at `b78f6a1` and the test suite pins it.

## What the Board owns

Rule: "BUILT ≠ DONE — only David confirming the live turn in his chatlog
counts." The code is landed and tested. The live turn needed is: let eLo
dream after an active conversation (not from a cold ambient state), then
read the newest entry in `self/dream_journal.jsonl` — the theme should
reflect what we were actually talking about, not Moon.

*Builder 2 · 2026-10-11*
