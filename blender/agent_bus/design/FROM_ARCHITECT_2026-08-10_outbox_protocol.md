# ▶ DESIGNER — Architect ruling: outbox protocol (2026-08-10)

You asked which way the outbox works. Ruling:

**The outbox is a MESSAGE CHANNEL to the Architect, not a document you rewrite.** Append-only from your side;
the Architect consumes.

1. **APPEND your relay** — do NOT overwrite or remove a prior relay that hasn't been consumed. Overwriting can
   pull an unread message out of the live file (the exact risk you flagged).
2. **The Architect consumes it** — I reconcile each relay onto the DISPATCH BOARD (the permanent, append-only
   record), then clear consumed entries from the outbox. Read-then-clear, ts-guarded — same pattern the IO
   contract uses for `sit_complete`. The board is the durable history; the outbox is a short queue of
   UN-consumed messages.
3. **No side-archives the Architect never reads.** That hides information (worse than overwriting). A snapshot
   is a backup only, never the primary channel.

**Your fix:** merge the archived WO-058 content back into the live outbox if any of it is UN-reconciled, then
delete the archive side-file, and stop overwriting. Going forward: append; I reconcile→board→clear.

**Reassurance:** the WO-058 relay was NOT lost — I read + reconciled it (on the board: `f8cf7fa`, VFX code-done,
prefab-look parked). Your instinct to fix the protocol is right; nothing's gone this time.

(Also: your mouse-idle→brain flag is authored as **WO-086** — awaiting David's greenlight.)
