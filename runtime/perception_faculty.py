"""
runtime/perception_faculty.py — WO-PERCEPTION-001

Environment perception: reads blender_state.json once per turn, diffs against the
previous turn's snapshot, and returns a PerceptionResult with the delta.

CognitiveState.environment_delta and .perception_changed are populated from this.
OBSERVATION vault events are triggered by server.py when perception_changed is True
and the delta contains meaningful environment changes.

Thread safety: single-threaded server; module-level prev-state is safe.
"""

from __future__ import annotations

import json
import os

# ── Observed fields (what eLo can perceive) ───────────────────────────────────

_OBSERVED_KEYS: tuple[tuple, ...] = (
    # (keypath_tuple, label, significance)
    (("state", "mode"),          "presence_mode",   "high"),
    (("state", "emotion"),       "emotion",         "medium"),
    (("state", "energy"),        "energy",          "low"),
    (("asleep",),                "asleep",          "high"),
    (("dream_phase",),           "dream_phase",     "high"),
    (("elo_battery",),           "elo_battery",     "low"),
    (("activity_recent",),       "activity_recent", "medium"),
    (("weather",),               "weather",         "low"),
)

_HIGH_SIG_KEYS = frozenset(
    label for _, label, sig in _OBSERVED_KEYS if sig == "high"
)

# ── Module-level previous snapshot (persists across turns within one session) ──

_prev_snapshot: dict = {}
_prev_path_mtime: float = 0.0
_last_result: dict = {}   # last perceive() result — readable by server.py


# ── Public API ────────────────────────────────────────────────────────────────

def perceive(blender_state_path: str) -> dict:
    """
    Read blender_state.json and compute what changed since last call.

    Returns:
        {
          "snapshot":         {label: value, ...},  # current values
          "delta":            {label: (old, new)},  # changed fields
          "changed_fields":   [label, ...],         # list of changed field names
          "perception_changed": bool,               # True if anything notable changed
          "high_sig_change":  bool,                 # True if a high-significance field changed
          "error":            str | None,           # if blender_state.json was unreadable
        }
    """
    global _prev_snapshot, _prev_path_mtime

    # ── Read blender_state.json ───────────────────────────────────────────────
    try:
        mtime = os.path.getmtime(blender_state_path)
        with open(blender_state_path, encoding="utf-8") as f:
            raw = json.load(f)
        _prev_path_mtime = mtime
    except Exception as exc:
        return {
            "snapshot": {},
            "delta": {},
            "changed_fields": [],
            "perception_changed": False,
            "high_sig_change": False,
            "error": str(exc),
        }

    # ── Extract snapshot ──────────────────────────────────────────────────────
    snapshot: dict = {}
    for keypath, label, _ in _OBSERVED_KEYS:
        val = raw
        try:
            for k in keypath:
                val = val[k]
        except (KeyError, TypeError):
            val = None
        snapshot[label] = val

    # ── Compute delta ─────────────────────────────────────────────────────────
    delta: dict = {}
    if _prev_snapshot:  # skip diff on first call — no baseline to compare against
        for label, current in snapshot.items():
            prev = _prev_snapshot.get(label)
            if prev != current:
                # Ignore low-significance float drift (battery jitter)
                if isinstance(current, float) and isinstance(prev, float):
                    if abs(current - (prev or 0.0)) < 0.05:
                        continue
                delta[label] = (prev, current)

    changed_fields = list(delta.keys())
    high_sig = any(f in _HIGH_SIG_KEYS for f in changed_fields)
    perception_changed = bool(changed_fields)

    # ── Advance snapshot ──────────────────────────────────────────────────────
    _prev_snapshot = dict(snapshot)

    # WO-B1-0139: novelty signal — any field with a None→value transition is NOVEL
    novelty_fields = [
        label for label, (old, new) in delta.items()
        if old is None and new is not None
    ]
    novel = bool(novelty_fields)

    # WO-B1-0139: epistemic tagging — direct reads are OBSERVED; no inference path yet
    snapshot_tagged = {
        label: {"value": val, "source": "OBSERVED"}
        for label, val in snapshot.items()
    }

    result = {
        "snapshot": snapshot,
        "snapshot_tagged": snapshot_tagged,      # WO-B1-0139: epistemic-tagged version
        "delta": delta,
        "environment_delta": delta,              # WO-B1-0139: alias for spine.py compat
        "changed_fields": changed_fields,
        "perception_changed": perception_changed,
        "high_sig_change": high_sig,
        "novel": novel,                          # WO-B1-0139: new field never seen before
        "novelty_fields": novelty_fields,
        "error": None,
    }
    _last_result = result
    return result


def get_last_result() -> dict:
    """Return the most recent perceive() result without triggering a file read."""
    return dict(_last_result)


def reset() -> None:
    """Clear prev snapshot at session start."""
    global _prev_snapshot, _prev_path_mtime
    _prev_snapshot = {}
    _prev_path_mtime = 0.0


def format_delta_for_vault(delta: dict) -> str:
    """Format delta dict as a human-readable OBSERVATION note body."""
    if not delta:
        return ""
    lines = ["Environment changed this turn:"]
    for label, (old, new) in delta.items():
        lines.append(f"  {label}: {old!r} → {new!r}")
    return "\n".join(lines)
