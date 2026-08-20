"""
self_improvement/finetune/tagger.py — WO-104 Step 1.

Compliance: Ruling F requires every shadow row to carry `delta_cause`
before training can run. This module classifies legacy rows that were
written before `record_turn` began emitting the tag.

Classification (derivation only — never guesses):
    raw_gen == final                                    → 'none'
    trace_id has a matching l3_patch record             → 'l3_override'
    row already carries a valid delta_cause             → keep it
    otherwise (raw_gen != final, no other signal)       → 'unknown'

`unknown` rows are excluded from training by the trainer's Rule 1 alarm.
`verification` and `l3_override` rows are also excluded even if present.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from typing import Iterable

VALID_DELTA_CAUSES = ("none", "style", "verification", "l3_override", "unknown")


def _load_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _l3_trace_ids(rows: Iterable[dict]) -> set[str]:
    return {
        r.get("trace_id", "")
        for r in rows
        if r.get("_type") == "l3_patch" and r.get("trace_id")
    }


def classify_row(row: dict, l3_ids: set[str]) -> str:
    """Return the derived delta_cause for a single turn row."""
    if row.get("_type") == "l3_patch":
        return "l3_override"

    existing = row.get("delta_cause")
    if existing in VALID_DELTA_CAUSES:
        return existing

    raw_gen = row.get("elo_raw_gen")
    final = row.get("elo_final")

    if raw_gen == final:
        return "none"

    tid = row.get("trace_id", "")
    if tid and tid in l3_ids:
        return "l3_override"

    return "unknown"


def backfill(path: str, dry_run: bool = False) -> dict:
    """
    Read every row, derive delta_cause where missing, rewrite the file atomically.
    Legacy file is preserved as <path>.pre_delta_cause_backup.
    Returns a tally: {'none': N, 'style': N, 'verification': N, 'l3_override': N, 'unknown': N, 'total': N}.
    """
    rows = _load_rows(path)
    l3_ids = _l3_trace_ids(rows)

    tally = {c: 0 for c in VALID_DELTA_CAUSES}
    tally["total"] = len(rows)
    tagged_rows: list[dict] = []

    for r in rows:
        if r.get("_type") == "l3_patch":
            tagged_rows.append(r)
            tally["l3_override"] += 1
            continue

        cause = classify_row(r, l3_ids)
        r_out = dict(r)
        r_out["delta_cause"] = cause
        tagged_rows.append(r_out)
        tally[cause] += 1

    if dry_run:
        return tally

    if rows:
        backup = path + ".pre_delta_cause_backup"
        if not os.path.exists(backup):
            shutil.copy2(path, backup)

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in tagged_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)

    tally["backfilled_at"] = time.time()
    return tally


def audit(path: str) -> dict:
    """Return the current delta_cause distribution without rewriting the file."""
    rows = _load_rows(path)
    tally = {c: 0 for c in VALID_DELTA_CAUSES}
    tally["untagged"] = 0
    tally["total"] = len(rows)
    for r in rows:
        if r.get("_type") == "l3_patch":
            continue
        c = r.get("delta_cause")
        if c in VALID_DELTA_CAUSES:
            tally[c] += 1
        else:
            tally["untagged"] += 1
    return tally
