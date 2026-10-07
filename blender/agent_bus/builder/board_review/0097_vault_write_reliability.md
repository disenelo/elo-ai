**WO:** ROOT-5-FIX · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
vault_write succeeds reliably on every turn. Currently writes are unreliable — ROOT-5.

## Scope — exactly this, nothing more
- Audit vault_write call path in spine for silent failures
- Add error logging on any failed write (not silent swallow)
- Ensure write completes before turn closes or runs reliably async
- Verify: after a turn, the vault entry exists

## Files to touch
`runtime/spine.py` · `runtime/memory*/` (vault write path)

## Test
`python3 -m pytest tests/ -k "vault" -v`
Manual: trigger a turn, check vault for the entry.

## Done when
vault_write failures are logged (not silent). Reliability rate measurable. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What did I just tell you?"
> eLo should retrieve from vault what was said in the immediately prior turn.

## Result
- commit: 5c37a34
- test: 67 vault tests green (2026-10-07)
- notes: Silent failure was in tool_router.py exception handler — `_logger.debug` swallowed vault_write
  exceptions at normal log levels. Fix: detect `ag_name == "vault_write"` in the except block,
  escalate to `_logger.error(..., exc_info=True)`. On success path: log now includes vault_write
  return string (saved filename/title) for full observability. vault_writer.py write is synchronous
  (open+write) — no async gap found. Write completes before turn closes.
