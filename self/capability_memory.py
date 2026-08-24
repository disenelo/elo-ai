"""
self/capability_memory.py — WO-CAP-001: Capability Result Memory

Records capability invocation results as informative world state.
Append-only JSONL store — failures (succeeded=False) are as informative as successes.
MemoryFaculty sole writer through record_capability_result().

JSONL schema (SPEC-CAP-001 S-1):
  ts              float  — Unix timestamp at write
  capability      str    — capability name from registry
  experience_id   str    — current turn's xid
  goal_surface    str    — sanitised user intent, no PII
  result_summary  str    — one-line human-readable result
  result_typed    dict   — structured, capability-specific (see SPEC-CAP-001 S-3)
  succeeded       bool
  failure_reason  str    — "" if succeeded
"""
from __future__ import annotations

import json
import os
import time

_ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CAP_LOG = os.path.join(_ROOT, "self", "capability_memory.jsonl")


def record_capability_result(
    capability: str,
    experience_id: str,
    goal_surface: str,
    result_summary: str,
    result_typed: dict,
    succeeded: bool,
    failure_reason: str = "",
    log_path: str | None = None,
) -> None:
    """
    Append one capability result record to capability_memory.jsonl.
    Called immediately after a capability agent returns a result.
    Always writes — failures (succeeded=False) are informative world state.
    """
    path = log_path or _CAP_LOG
    record = {
        "ts":             time.time(),
        "capability":     capability or "",
        "experience_id":  experience_id or "",
        "goal_surface":   goal_surface or "",
        "result_summary": result_summary or "",
        "result_typed":   result_typed if isinstance(result_typed, dict) else {"value": str(result_typed)},
        "succeeded":      bool(succeeded),
        "failure_reason": failure_reason if not succeeded else "",
    }
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def recent_capability_results(n: int = 3, log_path: str | None = None) -> list[dict]:
    """
    Return the last n capability result records (any capability), newest last.
    Makes capability history readable by the Executive.
    """
    path = log_path or _CAP_LOG
    records: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return []
    except Exception:
        return []
    return records[-n:]
