"""
tools/file_lock.py — cross-seat file lock protocol (WO-B1-0107)

Usage before editing any shared file:
    from tools.file_lock import acquire, release, check

    if not acquire("runtime/server.py", seat="Builder1", purpose="wiring capability intercept"):
        info = check("runtime/server.py")
        raise RuntimeError(f"File locked by {info}")
    try:
        # ... edit the file ...
    finally:
        release("runtime/server.py")

Lock files live alongside the locked file: runtime/server.py.lock
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path


def acquire(filepath: str, seat: str, purpose: str) -> bool:
    """
    Acquire a lock on filepath.
    Returns True if lock acquired; False if already held by another seat.
    Writes <filepath>.lock on success. Uses O_EXCL for atomic creation.
    """
    lock_path = _lock_path(filepath)
    payload = {
        "seat": seat,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file": filepath,
        "purpose": purpose,
    }
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except FileExistsError:
        return False
    except OSError:
        return False


def release(filepath: str) -> None:
    """Delete <filepath>.lock. Call after commit."""
    lock_path = _lock_path(filepath)
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def check(filepath: str) -> dict | None:
    """Return lock contents dict if held, None if free."""
    lock_path = _lock_path(filepath)
    if not os.path.exists(lock_path):
        return None
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _lock_path(filepath: str) -> str:
    return filepath + ".lock"
