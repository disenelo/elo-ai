"""
blender_bridge/exit_state.py — Shared exit-sequence suppression flag.

When eLo runs off-screen (exit_event written to blender_state.json), the
ambient engine must not fire new speech, smiles, emotion flickers, or
animation wanders until the full Unity ExitSequence has completed.

Timeline covered (from ExitSequence in DesktopBuddy.cs):
    speech-wait    ≤ 8s
    gun-check      ≤ 1.2s
    run-off        ≤ 8s
    dormant wait   ≤ 8s (until mouse-move triggers return)
    return run-in  ~ 3s
    ─────────────────
    total max      ~ 30s  →  flag held for _DURATION = 35s

Public API:
    mark_exiting()   — set flag (call immediately after writing exit_event)
    is_exiting()     — True while exit sequence is considered active
    clear_exit()     — explicit early clear (e.g., Unity signals return done)
"""
from __future__ import annotations

import time
import threading

_DURATION = 35.0  # seconds — full sequence including return

_lock:    threading.Lock = threading.Lock()
_exit_ts: float          = 0.0


def mark_exiting() -> None:
    """Start the exit-sequence suppression window."""
    global _exit_ts
    with _lock:
        _exit_ts = time.time()


def is_exiting() -> bool:
    """Return True if eLo is currently in exit sequence."""
    with _lock:
        return _exit_ts > 0.0 and (time.time() - _exit_ts) < _DURATION


def clear_exit() -> None:
    """Manually end the suppression window early."""
    global _exit_ts
    with _lock:
        _exit_ts = 0.0
