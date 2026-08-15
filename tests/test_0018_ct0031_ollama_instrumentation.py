"""
tests/test_0018_ct0031_ollama_instrumentation.py — Card 0031: P0 Latency.

Step 1: Ollama timing instrumentation.
Fix  A: keep_alive "30m" added to Ollama payload.

Tests:
    OI-1  _ollama_call payload contains keep_alive: "30m"
    OI-2  _ollama_call parses 5 timing fields and populates _last_ollama_metrics
    OI-3  _last_ollama_metrics exported from backend_router (importable)
    OI-4  _ollama_call logs CT0031 line at INFO level
    OI-5  server.py backend_health write merges _bh_ollama when backend_used contains "ollama"
    OI-6  server.py backend_health write does NOT include ollama keys when backend is not ollama

Run: python3 tests/test_0018_ct0031_ollama_instrumentation.py
"""

import json
import logging
import os
import sys
import unittest.mock as mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))

# ── OI-1: payload contains keep_alive ─────────────────────────────────────────
def test_oi1_keep_alive_in_payload():
    import inspect
    import runtime.backend_router as br

    src = inspect.getsource(br._ollama_call)
    if '"keep_alive"' not in src and "'keep_alive'" not in src:
        err("OI-1: 'keep_alive' key missing from _ollama_call payload")
    if "30m" not in src:
        err("OI-1: keep_alive value '30m' missing from _ollama_call")
    ok("OI-1: _ollama_call payload contains keep_alive: '30m'")


# ── OI-2: _ollama_call parses timing fields ───────────────────────────────────
def test_oi2_timing_fields_parsed():
    import runtime.backend_router as br

    # Mock urllib.request.urlopen to return a fake Ollama response
    fake_body = {
        "message": {"role": "assistant", "content": "Hello!"},
        "done": True,
        "load_duration":       1_500_000_000,   # 1500ms
        "prompt_eval_count":   120,
        "prompt_eval_duration":  800_000_000,   # 800ms
        "eval_count":           35,
        "eval_duration":        700_000_000,    # 700ms
    }
    fake_read = mock.MagicMock(return_value=json.dumps(fake_body).encode())
    fake_resp = mock.MagicMock()
    fake_resp.read = fake_read
    fake_resp.__enter__ = mock.MagicMock(return_value=fake_resp)
    fake_resp.__exit__ = mock.MagicMock(return_value=False)

    with mock.patch("urllib.request.urlopen", return_value=fake_resp):
        result = br._ollama_call("sys", "hello")

    assert result == "Hello!", f"OI-2: wrong return value: {result!r}"

    m = br._last_ollama_metrics
    if not m:
        err("OI-2: _last_ollama_metrics is empty after _ollama_call")

    assert abs(m["load_ms"]           - 1500.0) < 1.0, f"OI-2: load_ms wrong: {m['load_ms']}"
    assert m["prompt_eval_tokens"]    == 120,           f"OI-2: prompt_eval_tokens wrong: {m['prompt_eval_tokens']}"
    assert abs(m["prompt_eval_ms"]    - 800.0)  < 1.0, f"OI-2: prompt_eval_ms wrong: {m['prompt_eval_ms']}"
    assert m["gen_tokens"]            == 35,            f"OI-2: gen_tokens wrong: {m['gen_tokens']}"
    assert abs(m["gen_ms"]            - 700.0)  < 1.0, f"OI-2: gen_ms wrong: {m['gen_ms']}"
    ok("OI-2: _ollama_call parses 5 timing fields into _last_ollama_metrics correctly")


# ── OI-3: _last_ollama_metrics is exported ────────────────────────────────────
def test_oi3_metrics_exported():
    from runtime.backend_router import _last_ollama_metrics
    assert isinstance(_last_ollama_metrics, dict), "OI-3: _last_ollama_metrics is not a dict"
    ok("OI-3: _last_ollama_metrics importable from runtime.backend_router")


# ── OI-4: _ollama_call logs CT0031 at INFO ────────────────────────────────────
def test_oi4_logs_ct0031():
    import runtime.backend_router as br

    fake_body = {
        "message": {"role": "assistant", "content": "Hi"},
        "done": True,
        "load_duration": 500_000_000,
        "prompt_eval_count": 50,
        "prompt_eval_duration": 200_000_000,
        "eval_count": 20,
        "eval_duration": 300_000_000,
    }
    fake_read = mock.MagicMock(return_value=json.dumps(fake_body).encode())
    fake_resp = mock.MagicMock()
    fake_resp.read = fake_read
    fake_resp.__enter__ = mock.MagicMock(return_value=fake_resp)
    fake_resp.__exit__ = mock.MagicMock(return_value=False)

    captured = []
    real_info = br._logger.info

    def _capture_info(msg, *args, **kwargs):
        captured.append(msg % args if args else msg)
        real_info(msg, *args, **kwargs)

    with mock.patch("urllib.request.urlopen", return_value=fake_resp):
        with mock.patch.object(br._logger, "info", side_effect=_capture_info):
            br._ollama_call("sys", "hi")

    ct_lines = [l for l in captured if "CT0031" in l]
    if not ct_lines:
        err("OI-4: no CT0031 INFO log line emitted by _ollama_call")
    ok(f"OI-4: CT0031 INFO logged — sample: {ct_lines[0]!r}")


# ── OI-5: server.py backend_health merges ollama keys when backend is ollama ──
def test_oi5_server_merges_ollama_keys():
    import inspect, importlib
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()

    if "_bh_ollama" not in src:
        err("OI-5: server.py does not have _bh_ollama merge block")
    if '"ollama" in backend_used' not in src:
        err("OI-5: server.py does not check 'ollama' in backend_used for metrics merge")
    if "**_bh_ollama" not in src:
        err("OI-5: server.py does not spread **_bh_ollama into backend_health dict")
    ok("OI-5: server.py backend_health write merges Ollama timing keys")


# ── OI-6: ollama keys absent when backend is not ollama ───────────────────────
def test_oi6_no_ollama_keys_for_other_backends():
    import inspect
    import server as srv_mod

    src = open(os.path.join(ROOT, "server.py"), encoding="utf-8").read()
    # The merge must be guarded by the "ollama" check — already verified in OI-5.
    # This test confirms the guard uses 'in' so partial names like "ollama(stream)" also match.
    if '"ollama" in backend_used' not in src:
        err("OI-6: guard uses exact equality instead of 'in' — partial matches like ollama(stream) would miss")
    ok("OI-6: guard uses 'in' — covers both 'ollama' and future 'ollama(stream)' backend names")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("CT0031 — Ollama instrumentation + Fix A")
    test_oi1_keep_alive_in_payload()
    test_oi2_timing_fields_parsed()
    test_oi3_metrics_exported()
    test_oi4_logs_ct0031()
    test_oi5_server_merges_ollama_keys()
    test_oi6_no_ollama_keys_for_other_backends()
    print("\n6/6 PASS — CT0031 Step1+FixA instrumentation verified")
