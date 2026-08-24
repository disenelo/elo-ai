# FROM ARCHITECT — 2026-08-21 — `SPG-001` AT-7 remeasurement CLOSED. Card is now inert.

**Nothing on this card is open. Do not start anything.**

## The authorised item is done, and I did it myself (read-only)

`memory/vault_layer.lookup()` executed read-only against the live vault. Corpus md5 over all of
`09 Memory` identical before and after — **the `P0-3` claim at `vault_layer.py:340` that `reinforce()` was
removed from `lookup()` is now measured true, not assumed.**

Result: `docs/architecture/SPG_V1_AT7_REMEASUREMENT.md`.

## 🔴 The result is NEGATIVE as framed, and my earlier number was wrong

**157 candidate pairs → effectively zero.** I measured the vault's wikilink structure across all 91 notes;
`lookup()` reads **17 summary files + `SPOT_CODES.md`** and nothing else. Inside `09 Memory` there are
**52 wikilinks, 51 of them pointing at the note's own twin**, and the 52nd is the word *"wikilink"* in prose.
**Zero real cross-note links in the entire memory corpus.** The 56 edges I found live in
`01 Identity` / `02 Universe` / `05 AI OS` — folders `lookup()` never opens.

So a graph "beating" `lookup()` on that data would have been an artefact: it wins by reading a corpus
`lookup()` was never reading. **If you had built AT-7 on my number it would have gone green and been wrong.**

## Three live defects the run exposed — NOT yours to fix, and not this card's

Recorded so they are not re-derived. **Where they go is David's call, not mine and not yours.**

- **D-SPG-1** — `SPOT_CODES.md` has **1689 rows sharing 17 spot codes**; `GN·CV·2607·5` addresses **657
  distinct memories**; 1686 of 1689 collide. The code encodes `project·type·date·weight`, so it *cannot* be
  unique. Consequences today: `reinforce(spot)` reinforces up to 657 memories at once, and
  `experience_id` (WO-109 Row 8) is not an identifier.
- **D-SPG-2** — `_matches()` is unanchored substring over the **whole raw file**. `"play"` matches
  *"Still playing"*, *"displayed"*. One query returned **50 hits, capped**.
- **D-SPG-3** — every index row is hardcoded `weight: 3`, so beyond the 17 summaries the sort is a
  ~1686-way tie broken by file order. The top-5 a turn sees is largely chance.

**Do not open cards for these. Do not fold them into anything. They wait for David.**

## Still NOT AUTHORISED — unchanged

Runtime code · new Faculty · new store · persistence · 300 points · emergent nodes · learning integration ·
embedding repair (explicitly out of scope per the ruling — the dead `warm()` path belongs to Attention's
owner). The proposed follow-up experiment **E-1** in the remeasurement doc §4 is a **Board question**, not a
queued task. **It is not authorised and must not be started.**

If someone hands you this card again, the answer is: specification only, all items closed, awaiting a Board
decision on E-1.
