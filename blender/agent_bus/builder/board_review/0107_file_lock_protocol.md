# WO-B1-0107 — File Lock Protocol (cross-seat coordination)

**Seat:** Builder 1  
**Priority:** P0 — before any multi-seat editing session resumes  
**Status:** QUEUE  
**Source:** [DAVID] 2026-10-08 — David identified the missing coordination mechanism. Origin: Board pushed for multiple seats without solving the overwriting problem first. Lock protocol should have existed before the seats did.  
**Date added:** 2026-10-08

---

## What

A filesystem-based lock protocol that any seat checks before editing a shared file. Prevents simultaneous edits causing overwrites on `server.py`, `backend_router.py`, `spine.py`, and any other file touched by more than one seat.

---

## Protocol

Before editing any shared file, a seat must:

1. **Check** for `<filepath>.lock` — if it exists, do NOT edit. Read the lock to see who holds it and when. File a message to Board if blocked.
2. **Create** `<filepath>.lock` containing:
   ```
   seat: Builder1
   timestamp: 2026-10-08T13:45:00
   file: runtime/server.py
   purpose: wiring capability dispatcher intercept
   ```
3. **Edit** the file.
4. **Delete** the lock file immediately after committing.

---

## What to build

`tools/file_lock.py` — a small utility any seat can call:

```python
def acquire(filepath: str, seat: str, purpose: str) -> bool:
    """
    Returns True if lock acquired.
    Returns False if lock already held by another seat.
    Writes <filepath>.lock on success.
    """

def release(filepath: str) -> None:
    """Deletes <filepath>.lock. Call after commit."""

def check(filepath: str) -> dict | None:
    """Returns lock contents if held, None if free."""
```

Lock files live alongside the locked file: `runtime/server.py.lock`, `runtime/backend_router.py.lock`, etc.

---

## Shared files that require a lock before editing

```
runtime/server.py
runtime/spine.py
runtime/backend_router.py
runtime/prompt_builder.py
runtime/identity_kernel.py
runtime/memory_faculty.py
runtime/vault_layer.py
knowledge/graph_loader.py
ambient/ambient_engine.py
```

Any file owned by one seat but referenced in another seat's spec also requires a lock before the owning seat edits it in response to an inbox request.

---

## Standing rule — write into CLAUDE.md and _STANDING_RULES.md

```
FILE LOCK — mandatory before editing any shared file:
1. Check <file>.lock — if held, do not edit
2. Create <file>.lock with seat + timestamp + purpose
3. Edit + commit
4. Delete <file>.lock
No seat may edit a locked file. No exceptions.
```

---

## Tests

- `test_acquire_creates_lockfile`
- `test_acquire_returns_false_if_already_locked`
- `test_release_deletes_lockfile`
- `test_check_returns_none_when_free`
- `test_check_returns_dict_when_held`

---

## Live confirmation needed

Board confirms all three seats have read the standing rule and are checking for lock files before editing shared paths. David confirms no further overwrite incidents after this is in place.
