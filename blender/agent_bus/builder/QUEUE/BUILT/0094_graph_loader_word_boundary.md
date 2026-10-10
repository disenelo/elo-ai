**WO:** ROOT-3-FIX · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Fix graph_loader retrieval so it stops injecting wrong context into live sessions.

## What's broken
`k in t` substring match — e.g. searching "art" matches "Camberwell College of Arts" and injects it into David's session. Word-boundary-free substring matching is polluting every retrieval with false positives.

## Scope — exactly this, nothing more
- In `graph_loader.py`: replace substring `k in t` match with word-boundary regex (`\b{k}\b`) or equivalent whole-word match
- Re-run retrieval on a known query and verify only relevant nodes return
- Do not touch WKG structure, vault, or spine

## Files to touch
`graph_loader.py`

## Test
`python3 -m pytest tests/ -k "graph_loader or retrieval" -v`
Manual spot-check: query "David" should not return nodes about unrelated proper nouns containing "david" as substring.

## Done when
Word-boundary retrieval in place. No false-positive injections. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What do you remember about DISENELO?"
> eLo should respond with actual DISENELO facts, not unrelated injected context.

## Result
- commit: already landed — B3-BOARD-RULINGS 2026-10-06 fix in graph_loader.py:181
- test: 31/31 graph_loader+retrieval tests pass 2026-10-07
- notes: _kw_match() and _wkg_word_scores() both use re.search(r"\b"+re.escape(k)+r"\b").
  No raw substring match remains. Card confirmed DONE — no new commit needed.
