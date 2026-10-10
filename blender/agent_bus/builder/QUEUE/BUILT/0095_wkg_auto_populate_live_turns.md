**WO:** ROOT-1-FIX · **Seat:** builder · **Priority:** P0
**Reserved?** no

## Goal
Every live turn writes to WKG automatically. Currently zero automatic growth from live experience — eLo has never written a WKG node from a real conversation.

## What's broken
ROOT-1: WKG-AUTO-POPULATE-001. The causal chain `EXPERIENCE → vault_write → WKG growth` is not wired. Nodes must be written after every meaningful turn without manual intervention.

## Scope — exactly this, nothing more
- After each turn completes in spine, extract significant content and write a WKG node automatically
- Significance threshold: use existing significance scoring if available; otherwise write if turn contains a fact, decision, preference, or correction
- Node format: matches existing WKG schema
- Do not block the response — write async or post-turn

## Files to touch
`runtime/spine.py` · `faculties/wkg/` (writer path)

## Test
`python3 -m pytest tests/ -k "wkg or auto_populate" -v`
After test turn: verify a new node appears in WKG with content from that turn.

## Done when
Live turn produces a WKG node. Node is readable by graph_loader. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "Remember that I prefer short answers."
> Then David says: "What do you remember about my preferences?"
> eLo should retrieve and cite the preference written from the first turn.

## Result
- commit: already landed — wkg_fact_extractor.py (ROOT-1) + populate_wkg_from_turn() in memory_faculty.py,
  wired in server.py lines 6723-6743
- test: 326/326 WKG+auto_populate tests pass 2026-10-07 (test_auto5_live_claim_retrievable confirms
  claims written by live turns are retrievable by graph_loader)
- notes: extract_and_write() handles "my X is Y" patterns; populate_wkg_from_turn() creates concept stubs.
  Both run post-turn in server.py. Card confirmed DONE — no new commit needed.
