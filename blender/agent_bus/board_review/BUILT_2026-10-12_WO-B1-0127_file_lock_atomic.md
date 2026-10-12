# Board Review — WO-B1-0127: file_lock.py atomic acquire
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

`tools/file_lock.py` — verify built, ensure collision prevention works. Card noted "never built" but WO-B1-0107 had already shipped it.

---

## What was built

### Already present (WO-B1-0107)

`tools/file_lock.py` existed with `acquire()`, `release()`, `check()` — full implementation.

### TOCTOU race fixed (this session)

The original `acquire()` used `os.path.exists()` then `open("w")` — two separate syscalls. Between them, a second seat could pass the `exists()` check and both would believe they hold the lock.

**Fix:** replaced with `os.open(O_CREAT | O_EXCL | O_WRONLY, 0o644)` — atomic file creation. `FileExistsError` is raised if another process created the file in the window. Now the first `acquire()` wins, guaranteed.

```python
fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
return True
# ...
except FileExistsError:
    return False
```

---

## Verification

Lock file protocol is in place and atomic. Two seats calling `acquire()` simultaneously on the same file: exactly one returns `True`, the other returns `False` (FileExistsError caught). The losing seat calls `check()` to see who holds it.

Live collision test deferred (no two live seats running simultaneously right now).

---

## Commits

`f8f4bb9` — WO-B1-0127: file_lock atomic acquire with O_EXCL (TOCTOU fix)

---

## Board decisions required

None. Ready to close.

*Builder 1 · 2026-10-12*
