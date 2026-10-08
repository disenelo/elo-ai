# Builder — Standing Rules (all seats, every session)

Read this file before acting. These are hard rules, not guidelines.

---

## RULE 1 — CHECK BEFORE BUILD

Before building ANYTHING on a Work Order:
1. Search for what already exists related to it.
2. A Work Order EXTENDS the existing thing by default — do NOT create a parallel version.
3. If it exists → extend it in place.
4. If unsure → relay the question before writing code.

Source: `STANDING_RULE_check_before_build.md` (full text)

---

## RULE 2 — FILE LOCK — mandatory before editing any shared file (WO-B1-0107, 2026-10-08)

```python
from tools.file_lock import acquire, release, check
```

Before editing any of these files:
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

**Protocol:**
1. `check(filepath)` — if lock held, do NOT edit. Read who holds it. File a message to Board if blocked.
2. `acquire(filepath, seat="Builder1", purpose="<what you are doing>")` — creates `<filepath>.lock`.
3. Edit the file and commit.
4. `release(filepath)` — deletes the lock immediately after commit.

No seat may edit a locked file. No exceptions.

Origin: David identified the missing coordination mechanism 2026-10-08. Board pushed for multiple seats without solving the overwriting problem first.
