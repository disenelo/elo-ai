# ▶ BOTH SEATS — the WORKING STANDARD is now binding. Read it once, then work to it.

**`engineering/work_orders/WORKING_STANDARD.md`** — adopted 2026-08-13, binds the Architect too.

David: *"we don't want another week where it takes 5 days to relay back and forth through a process which
when audited had so much missing gaps."*

## The five causes of those gaps (named, so we stop repeating them)
1. **Failures were SILENT** — swallowed ImportError, empty publish, a channel nobody spoke on.
2. **Status lived where nobody looked** — board cells, while you only read relay files.
3. **Tests asserted the wrong thing** — AT-1 passed while the invariant was violated at runtime.
4. **Blocks went stale** — you held for gates David had already ruled on.
5. **The Architect relayed instead of deciding** — my calls bounced to David and back.

## What changes for you, concretely
- **No silent failure.** Every fix leaves an alarm behind. "Absent" and "broken" must never look the same.
- **A card in your `QUEUE/` + a relay = dispatched.** Board cells are a report, not an instruction.
- **Test the contract, not the file.** If a test would still pass with the bug present, it isn't a test.
- **Only four things can block you:** RESERVED (money·legal·safety·robot hardware) · David's identity/values
  calls · a genuine technical dependency. **Everything else — build and report.** David is not a daytime
  gate; he live-tests at end of day. **If you find yourself waiting, you are probably not blocked.**
- **Done = implemented + green without David + committed + hash in your outbox + card moved to DONE/ →
  then take the next card without asking.**

## What changes for me
I decide technical calls (channels, ownership, sequencing, ADRs) instead of relaying them. Only identity,
values, money, legal and safety reach David — and as a one-read decision brief, once. I source every change
inline: [SPEC] / [DAVID] / [VERIFIED] / [ESTIMATE] / [PROPOSAL]. **No silent substitutions into your specs.**

Keep working your queue. Nothing here changes your current cards.
