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
- commit: 3f4dcb0
- test: 68/68 vault tests PASS. Direct vault write: {"action":"write","spot":"GN·CV·2610·1·383c8"}.
- notes: |
    4 silent except-pass blocks in server.py turn-close path now log at WARNING (runtime.vault_write).
    Covers: interaction (6884), topic_change (7060), perception (7096), world_interaction (7130).
    memory_faculty.submit() already calls _mark_vault_offline on exception — server.py now surfaces
    those failures so they appear in server logs. vault_write test: action=write confirmed.
    Reliability rate is now measurable via log grep: grep "ROOT-5:" elo_server.log | wc -l
    Scope note: memory_faculty.py:158 already has error path with _mark_vault_offline, NOT pass.
    The silent drops were in server.py's outer wrappers only.
