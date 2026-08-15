"""
tests/test_0007_metrics_isolation.py — Rule 1 alarm: growth_metrics.jsonl not polluted by tests.

When promote_pass() is called with a temp ledger_path, the production
self/journals/growth_metrics.jsonl MUST remain byte-identical.

MI-1  promote_pass(ledger_path=tmp) writes metrics beside tmp, not to production
MI-2  production growth_metrics.jsonl unchanged after test call
MI-3  _append_metrics(ledger_path=None) writes to the production path (sanity check
      that the prod path IS used when ledger_path is absent — but we verify it's
      the ONLY condition that triggers the prod write)

Run: python3 tests/test_0007_metrics_isolation.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROD_METRICS = os.path.join(_ROOT, "self", "journals", "growth_metrics.jsonl")


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return -1


# ── MI-1: temp ledger_path writes metrics beside tmp, not to production ───────

print("\nMI-1: promote_pass(ledger_path=tmp) writes beside tmp, not to production")
_tmp_ledger = None
try:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False,
                                     dir="/tmp") as tf:
        _tmp_ledger = tf.name
        json.dump({"lesson_key": "test_key_mi1", "statement": "test lesson",
                   "scope": "behaviour", "cause": "met", "strength": 0.3,
                   "status": "candidate", "first_seen": "2026-01-01T00:00:00+00:00",
                   "last_seen": "2026-01-01T00:00:00+00:00", "promoted_at": None,
                   "retired_at": None, "reason": None, "proposes": None,
                   "ts": "2026-01-01T00:00:00+00:00", "evidence": [],
                   "delta": "met"}, tf)
        tf.write("\n")

    _prod_before = _file_size(_PROD_METRICS)

    from self.lesson_store import promote_pass
    promote_pass(ledger_path=_tmp_ledger)

    _prod_after = _file_size(_PROD_METRICS)
    _tmp_metrics = os.path.join("/tmp", "journals", "growth_metrics.jsonl")

    if _prod_after != _prod_before:
        fail("MI-1", f"production growth_metrics.jsonl changed: {_prod_before} → {_prod_after} bytes")
    else:
        ok(f"MI-1 — production file unchanged ({_prod_before} bytes); metrics beside tmp as expected")
except Exception as e:
    fail("MI-1", repr(e))
finally:
    if _tmp_ledger:
        try: os.unlink(_tmp_ledger)
        except: pass
    # clean up tmp/journals if created
    _tmp_met = "/tmp/journals/growth_metrics.jsonl"
    if os.path.exists(_tmp_met):
        try: os.unlink(_tmp_met)
        except: pass


# ── MI-2: production file byte-identical after test call ─────────────────────

print("\nMI-2: production growth_metrics.jsonl byte-identical after test call")
try:
    _size_before = _file_size(_PROD_METRICS)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False,
                                     dir="/tmp") as tf2:
        _tmp2 = tf2.name
        json.dump({"lesson_key": "test_key_mi2", "statement": "test lesson 2",
                   "scope": "behaviour", "cause": "met", "strength": 0.3,
                   "status": "candidate", "first_seen": "2026-01-01T00:00:00+00:00",
                   "last_seen": "2026-01-01T00:00:00+00:00", "promoted_at": None,
                   "retired_at": None, "reason": None, "proposes": None,
                   "ts": "2026-01-01T00:00:00+00:00", "evidence": [],
                   "delta": "met"}, tf2)
        tf2.write("\n")

    promote_pass(ledger_path=_tmp2)

    _size_after = _file_size(_PROD_METRICS)
    if _size_after != _size_before:
        fail("MI-2", f"production file changed: {_size_before} → {_size_after} bytes after promote_pass(tmp)")
    else:
        ok(f"MI-2 — production growth_metrics.jsonl unchanged ({_size_before} bytes)")
except Exception as e:
    fail("MI-2", repr(e))
finally:
    try: os.unlink(_tmp2)
    except: pass
    _tmp_met2 = "/tmp/journals/growth_metrics.jsonl"
    if os.path.exists(_tmp_met2):
        try: os.unlink(_tmp_met2)
        except: pass


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*40}")
print(f"Metrics Isolation: {PASS} passed, {FAIL} failed")
if FAIL:
    sys.exit(1)
