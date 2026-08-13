# AUTORUN PROTOCOL — work fires on its own (David 2026-08-10)
### The fix for: "I dispatched it on the board and nothing happened."

**Root cause it solves:** dispatch used to live in a board *status cell*. Seat crons scan their *folder*.
So dispatches were invisible and seats sat idle reporting "nothing new."
**New rule: THE FILE IS THE TRIGGER.** If a card file exists in your QUEUE, that is your work. No status
cell, no greenlight, no relay needed.

## Folder structure (per seat: `builder/` · `design/` · `game/`)
```
blender/agent_bus/<seat>/
  QUEUE/    ← work waiting. Files named NN_WO-XXX_slug.md, picked LOWEST NUMBER FIRST.
  DOING/    ← move the card here when you start it (so everyone sees what's in flight)
  DONE/     ← move the card here when committed + test green. Append the commit hash inside.
  outbox.json  ← your report line (append-only)
```

## The seat loop (every cron tick — no human in it)
1. `ls QUEUE/` → if empty, stay silent and stop. If not empty, take the **lowest-numbered** card.
2. `mv` that card `QUEUE/ → DOING/`.
3. Do exactly what the card says — nothing more (no freelancing, stay in lane).
4. Run its test. Must pass **without David**.
5. Commit only your changed files.
6. Append the commit hash + result to the card, `mv` it `DOING/ → DONE/`, append a line to `outbox.json`.
7. Loop: go back to step 1 and take the next card. **Do not stop to ask.**

## Standing rules (David 2026-08-10)
- **Nothing is held.** David is NOT a daytime gate. He runs ONE LIVE TEST AT END OF DAY — that is the review.
- Build → test → commit → next. Only **money · legal · safety** are reserved (those cards are marked
  `RESERVED` in the title and must NOT be auto-run).
- A card in `DOING/` older than a day = that seat probably died → the Architect re-queues it.
- **Architect never edits code.** It writes cards. Seats build. That's the whole contract.

## Architect loop (what I do)
- Turn every need into a **card** in the right seat's `QUEUE/` (not a board cell).
- Read `DONE/` + outboxes → reconcile the board → write the next cards. The board becomes a *report*,
  not the dispatch mechanism.

## Card template
See `_CARD_TEMPLATE.md`. A card is self-contained: goal · exact scope · files to touch · test to run · done-when.
