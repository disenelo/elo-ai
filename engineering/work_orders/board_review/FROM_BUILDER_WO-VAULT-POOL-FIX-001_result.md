# WO-VAULT-POOL-FIX-001 — Result Card

**Status**: COMPLETE — already implemented; verified 2026-10-06
**Lane**: `server.py` (generation layer)
**Date**: 2026-10-06

## What was found

The WO described vault writes using `elo_final` (potentially pool-substituted) instead of `elo_raw_gen`. The fix was already implemented in server.py:6511:

```python
_vault_response = locals().get("_elo_raw") or response
```

This is the correct fix. `_elo_raw` is captured at server.py:6360 immediately after the router call, before any post-generation scrubs (voice_rewrite, _sanitise, mirror scrub, memory scrub — all at 7200+). The vault write at 6511 fires before those scrubs, so `_elo_raw` correctly holds the LLM's actual bytes.

## Execution flow (confirmed)

```
router_route() → response           ← backend output (LLM or mock)
6360: _elo_raw = response            ← captured before scrubs
6511: _vault_response = _elo_raw     ← vault uses raw bytes
...
7200+: _sanitise(), voice_rewrite(), mirror scrub, MCG scrub → response (elo_final)
```

## Acceptance tests (verified)

| AT | Result |
|---|---|
| `tests/test_vault_write_unique.py` | 7/7 PASS |
| `tests/test_wo_vault_epistemic_class_enforce.py` | 6/6 PASS |
| `tests/test_vault_epistemic_filter.py` | 5/5 PASS |

Total: 18/18 related vault tests pass.

## WO-VAULT-WRITE-INVESTIGATE-001 resolved by this

WO-VAULT-WRITE-INVESTIGATE-001 was an investigation WO. Root cause: `_journal_route()` used `response` (elo_final) instead of `_elo_raw`. Fixed by line 6511. Four downstream WOs (COG-008/010/012/017) unblocked.

## Files

| File | Lines |
|---|---|
| `server.py` | 6360 (`_elo_raw` capture), 6508–6511 (vault write fix) |

No code changes made this session — implementation was already present.
