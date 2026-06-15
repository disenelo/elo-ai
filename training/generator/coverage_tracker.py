"""
training/generator/coverage_tracker.py — action/tone coverage reporting.

Reads a JSONL dataset, measures distribution per action and tone,
and writes coverage.csv to the same directory.

Target: ≥40 examples per action.
"""
import csv
import json
import os
from collections import Counter
from typing import Optional

_TARGET_PER_ACTION = 40
_ALL_ACTIONS = ["answer", "build", "connect", "celebrate", "reflect",
                "ground", "challenge", "witness", "silence"]


def load_jsonl(path: str) -> list:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_dir(directory: str) -> list:
    """Load all .jsonl files from a directory."""
    records = []
    if not os.path.isdir(directory):
        return records
    for fname in os.listdir(directory):
        if fname.endswith(".jsonl"):
            records.extend(load_jsonl(os.path.join(directory, fname)))
    return records


def report(records: list, output_path: Optional[str] = None) -> dict:
    """
    Compute coverage report from a list of records.

    Returns dict with per-action coverage %, tone distribution,
    total count, and gap list (actions below target).
    """
    action_counts = Counter(r.get("action", "") for r in records)
    tone_counts   = Counter(r.get("tone", "")   for r in records)
    total         = len(records)

    coverage = {}
    for action in _ALL_ACTIONS:
        count = action_counts.get(action, 0)
        pct   = min(100, round(count / _TARGET_PER_ACTION * 100, 1)) if count else 0.0
        coverage[action] = {"count": count, "coverage_pct": pct, "target": _TARGET_PER_ACTION}

    tone_total = sum(tone_counts.values()) or 1
    tones = {t: {"count": c, "pct": round(c / tone_total * 100, 1)}
             for t, c in tone_counts.items()}

    gaps = [a for a in _ALL_ACTIONS if coverage[a]["coverage_pct"] < 100]

    result = {
        "total_records": total,
        "actions":       coverage,
        "tones":         tones,
        "gaps":          gaps,
        "ready":         total >= 1000 and len(gaps) == 0,
    }

    if output_path:
        _write_csv(result, output_path)

    return result


def _write_csv(result: dict, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["action", "count", "coverage_pct", "target", "status"])
        for action, data in result["actions"].items():
            status = "OK" if data["coverage_pct"] >= 100 else "NEEDS_MORE"
            writer.writerow([action, data["count"], f"{data['coverage_pct']}%",
                             data["target"], status])
        writer.writerow([])
        writer.writerow(["tone", "count", "pct"])
        for tone, data in result["tones"].items():
            writer.writerow([tone, data["count"], f"{data['pct']}%"])
        writer.writerow([])
        writer.writerow(["total_records", result["total_records"]])
        writer.writerow(["ready_for_training", result["ready"]])


def print_report(result: dict) -> None:
    print(f"\n{'─'*50}")
    print(f"  COVERAGE REPORT  ({result['total_records']} records)")
    print(f"{'─'*50}")
    for action, data in result["actions"].items():
        bar   = "█" * int(data["coverage_pct"] / 10)
        gap   = "░" * (10 - len(bar))
        flag  = "✅" if data["coverage_pct"] >= 100 else "⚠️ "
        print(f"  {flag} {action:<12} {bar}{gap}  {data['coverage_pct']:5.1f}%  ({data['count']}/{data['target']})")
    print()
    if result["gaps"]:
        print(f"  Gaps: {', '.join(result['gaps'])}")
    else:
        print("  All actions covered.")
    print(f"  Ready for training: {'YES' if result['ready'] else 'NO'}")
    print(f"{'─'*50}\n")
