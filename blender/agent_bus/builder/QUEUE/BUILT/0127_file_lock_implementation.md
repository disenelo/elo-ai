# WO-B1-0127 — file_lock.py implementation
**Seat:** Builder 1  
**Priority:** P0 — multi-seat safety  
**Date:** 2026-10-12  
**Source:** FILE LOCK section in CLAUDE.md [DAVID 2026-10-08]

---

## What

`tools/file_lock.py` — referenced in CLAUDE.md as P0, never built. Without it, seats can collide on shared files (server.py, spine.py, etc.) with no protection.

## What it does

1. `acquire(seat, filepath, purpose)` — checks for `<filepath>.lock`, creates it if clear, errors if held
2. `release(filepath)` — deletes the lock file
3. `check(filepath)` — returns who holds the lock or None

Shared files requiring a lock: `server.py`, `spine.py`, `backend_router.py`, `prompt_builder.py`, `identity_kernel.py`, `memory_faculty.py`, `vault_layer.py`, `graph_loader.py`, `ambient_engine.py`.

## Done when

Two seats attempt to acquire the same file simultaneously → second seat gets a clear error and does not edit. File to Board: demonstration of collision prevention.

*Board · Lead Architect · 2026-10-12*
