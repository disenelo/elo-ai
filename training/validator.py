"""
training/validator.py — training readiness gate.

Reads all JSONL from datasets/organic/ and datasets/synthetic/.
Runs quality, balance, and coherence checks.
Outputs PASS or BLOCK. Training is gated behind PASS.

Usage:
    python -m training.validator
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_MIN_RECORDS   = 1000
_TARGET_RECORDS = 1500
_MAX_DUP_PCT   = 15.0
_MIN_ACTION_PCT = 8.0
_MAX_TONE_PCT   = 40.0
_TOP_PHRASE_PCT = 10.0

_ALL_ACTIONS = ["answer", "build", "connect", "celebrate", "reflect",
                "ground", "challenge", "witness", "silence"]

_GENERIC_PHRASES = [
    "that's worth exploring", "that is worth exploring",
    "tell me more", "what does that mean",
    "where does that lead", "interesting",
    "i understand", "i see", "noted",
    "good question", "great question",
    "i'm here", "i am here",
    "we can sit with that", "take your time",
    "what is underneath that",
    "how does that make you feel",
]

_LOOP_PHRASES = [
    "tell me more", "what else", "keep going",
    "can you elaborate", "what does that feel like",
    "what comes up for you",
]

_FALLBACK_SIGNALS = [
    "i'm sorry", "i am sorry", "i apologise", "i apologize",
    "i don't know", "i do not know",
    "as an ai", "as a language model",
    "i cannot", "i can't do that",
]


# ── loaders ───────────────────────────────────────────────────────────────────

def _load_dir(directory: str) -> list:
    records = []
    if not os.path.isdir(directory):
        return records
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".jsonl"):
            path = os.path.join(directory, fname)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return records


def load_all(base_dir: Optional[str] = None) -> list:
    base_dir = base_dir or os.path.join(_ROOT, "datasets")
    records  = []
    records += _load_dir(os.path.join(base_dir, "organic"))
    records += _load_dir(os.path.join(base_dir, "synthetic"))
    return records


# ── checks ────────────────────────────────────────────────────────────────────

def _check_size(records: list) -> dict:
    n = len(records)
    status = "PASS" if n >= _MIN_RECORDS else "BLOCK"
    return {
        "check":   "dataset_size",
        "status":  status,
        "value":   n,
        "minimum": _MIN_RECORDS,
        "target":  _TARGET_RECORDS,
        "note":    f"{n} records (min {_MIN_RECORDS}, target {_TARGET_RECORDS})",
    }


def _check_duplicates(records: list) -> dict:
    seen: set = set()
    dupes = 0
    for r in records:
        key = f"{r.get('user_input', r.get('input', ''))}|{r.get('response', '')}"
        if key in seen:
            dupes += 1
        seen.add(key)
    total  = len(records) or 1
    pct    = round(dupes / total * 100, 1)
    status = "PASS" if pct < _MAX_DUP_PCT else "BLOCK"
    return {
        "check":   "duplicates",
        "status":  status,
        "value":   pct,
        "maximum": _MAX_DUP_PCT,
        "note":    f"{dupes} duplicates ({pct}%, max {_MAX_DUP_PCT}%)",
    }


def _check_action_balance(records: list) -> dict:
    counts = Counter(r.get("action", "") for r in records)
    total  = len(records) or 1
    low    = []
    for action in _ALL_ACTIONS:
        pct = round(counts.get(action, 0) / total * 100, 1)
        if pct < _MIN_ACTION_PCT:
            low.append(f"{action}({pct}%)")
    status = "PASS" if not low else "BLOCK"
    return {
        "check":    "action_balance",
        "status":   status,
        "minimum":  _MIN_ACTION_PCT,
        "low_actions": low,
        "distribution": {a: round(counts.get(a, 0) / total * 100, 1) for a in _ALL_ACTIONS},
        "note":     f"{'All balanced' if not low else 'Under-represented: ' + ', '.join(low)}",
    }


def _check_tone_balance(records: list) -> dict:
    counts = Counter(r.get("tone", "") for r in records)
    total  = len(records) or 1
    heavy  = []
    for tone, count in counts.items():
        pct = round(count / total * 100, 1)
        if pct > _MAX_TONE_PCT:
            heavy.append(f"{tone}({pct}%)")
    status = "PASS" if not heavy else "BLOCK"
    return {
        "check":         "tone_balance",
        "status":        status,
        "maximum":       _MAX_TONE_PCT,
        "heavy_tones":   heavy,
        "distribution":  {t: round(c / total * 100, 1) for t, c in counts.most_common()},
        "note":          f"{'All balanced' if not heavy else 'Overweight: ' + ', '.join(heavy)}",
    }


def _check_repetition(records: list) -> dict:
    """Top-50 response phrases must not dominate."""
    phrase_counts: Counter = Counter()
    for r in records:
        resp = r.get("response", "").lower()
        # extract 3-5 word phrases
        words = re.findall(r"\b\w+\b", resp)
        for j in range(len(words) - 2):
            phrase_counts[" ".join(words[j:j+3])] += 1

    top50 = sum(c for _, c in phrase_counts.most_common(50))
    total = sum(phrase_counts.values()) or 1
    pct   = round(top50 / total * 100, 1)
    status = "PASS" if pct < _TOP_PHRASE_PCT * 5 else "BLOCK"  # 50% threshold for phrase dominance
    return {
        "check":   "repetition",
        "status":  status,
        "top50_pct": pct,
        "top_phrase": phrase_counts.most_common(1)[0] if phrase_counts else ("", 0),
        "note":    f"Top-50 phrases = {pct}% of all phrases",
    }


def _check_response_quality(records: list) -> dict:
    generic_hits   = []
    loop_hits      = []
    fallback_hits  = []
    short_hits     = []

    for r in records:
        resp  = r.get("response", "").lower()
        inp   = r.get("user_input", r.get("input", ""))[:40]
        if len(resp.strip()) < 10:
            short_hits.append(inp)
        if any(p in resp for p in _GENERIC_PHRASES):
            generic_hits.append(inp)
        if any(p in resp for p in _LOOP_PHRASES):
            loop_hits.append(inp)
        if any(p in resp for p in _FALLBACK_SIGNALS):
            fallback_hits.append(inp)

    issues = []
    if len(generic_hits) > len(records) * 0.05:
        issues.append(f"generic_phrases:{len(generic_hits)}")
    if len(loop_hits) > len(records) * 0.05:
        issues.append(f"loop_phrases:{len(loop_hits)}")
    if fallback_hits:
        issues.append(f"fallback_language:{len(fallback_hits)}")
    if len(short_hits) > len(records) * 0.03:
        issues.append(f"too_short:{len(short_hits)}")

    status = "PASS" if not issues else "BLOCK"
    return {
        "check":    "response_quality",
        "status":   status,
        "issues":   issues,
        "samples":  {
            "generic":  generic_hits[:3],
            "loop":     loop_hits[:3],
            "fallback": fallback_hits[:3],
        },
        "note": f"{'Clean' if not issues else 'Issues: ' + ', '.join(issues)}",
    }


def _check_block_conditions(records: list) -> dict:
    """
    Block if dataset is too repetitive, emotional, passive, grounding, or short.
    Measures whether any single characteristic dominates above a threshold.
    """
    action_counts = Counter(r.get("action", "") for r in records)
    total = len(records) or 1

    blocks = []
    thresholds = {
        "too_repetitive": ("reflect",   35),
        "too_emotional":  ("witness",   25),
        "too_passive":    ("silence",   20),
        "too_grounding":  ("ground",    25),
    }
    for label, (action, max_pct) in thresholds.items():
        pct = round(action_counts.get(action, 0) / total * 100, 1)
        if pct > max_pct:
            blocks.append(f"{label}({action}={pct}%)")

    # too_short: >10% responses under 20 chars
    short = sum(1 for r in records if len(r.get("response", "")) < 20)
    if short / total > 0.10:
        blocks.append(f"too_short({short})")

    status = "PASS" if not blocks else "BLOCK"
    return {
        "check":   "block_conditions",
        "status":  status,
        "blocks":  blocks,
        "note":    f"{'No dominant failures' if not blocks else ', '.join(blocks)}",
    }


# ── main ──────────────────────────────────────────────────────────────────────

def validate(base_dir: Optional[str] = None) -> dict:
    """
    Run all checks. Returns result dict with overall PASS/BLOCK verdict.
    """
    records = load_all(base_dir)
    checks  = [
        _check_size(records),
        _check_duplicates(records),
        _check_action_balance(records),
        _check_tone_balance(records),
        _check_repetition(records),
        _check_response_quality(records),
        _check_block_conditions(records),
    ]

    verdict = "PASS" if all(c["status"] == "PASS" for c in checks) else "BLOCK"
    return {
        "verdict": verdict,
        "total":   len(records),
        "checks":  checks,
    }


def print_result(result: dict) -> None:
    print(f"\n{'═'*55}")
    print(f"  TRAINING VALIDATOR — {result['verdict']}  ({result['total']} records)")
    print(f"{'═'*55}")
    for c in result["checks"]:
        icon = "✅" if c["status"] == "PASS" else "🔴"
        print(f"  {icon}  {c['check']:<22}  {c['note']}")
    print(f"{'═'*55}")
    if result["verdict"] == "PASS":
        print("  Training is unlocked.\n")
    else:
        blocked = [c["check"] for c in result["checks"] if c["status"] == "BLOCK"]
        print(f"  BLOCKED on: {', '.join(blocked)}")
        print("  Resolve all BLOCK conditions before fine-tuning.\n")


if __name__ == "__main__":
    result = validate()
    print_result(result)
    sys.exit(0 if result["verdict"] == "PASS" else 1)
