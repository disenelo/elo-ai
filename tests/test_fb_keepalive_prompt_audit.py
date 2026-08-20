"""
tests/test_fb_keepalive_prompt_audit.py — Card 0047 F-B.

Proves:
    FB-1  runtime.backend_router._ollama_call         → keep_alive="30m" in dict
    FB-2  runtime.backend_router._ollama_stream       → keep_alive="30m" in payload
    FB-3  backends.ollama_backend.OllamaBackend._call → keep_alive="30m" in payload
    FB-4  prompt_builder.build() populates _last_prompt_audit with per-block breakdown
    FB-5  audit blocks carry {name, chars, est_tokens, pct_tokens}, totals reconcile
    FB-6  server.py backend_health write includes the prompt_audit block

Run: python3 tests/test_fb_keepalive_prompt_audit.py
"""
import inspect
import json
import os
import sys
import unittest.mock as mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── FB-1: _ollama_call payload contains keep_alive="30m" (actual dict, falsifiable) ──
def test_fb1_ollama_call_keep_alive():
    import runtime.backend_router as br

    captured = {}
    fake_body = json.dumps({
        "message": {"role": "assistant", "content": "ok"},
        "done": True, "load_duration": 0, "prompt_eval_count": 1,
        "prompt_eval_duration": 0, "eval_count": 1, "eval_duration": 0,
    }).encode()

    class _Ctx:
        def read(self): return fake_body
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def _capture(req, timeout=60):
        captured["payload"] = json.loads(req.data.decode())
        return _Ctx()

    with mock.patch("urllib.request.urlopen", _capture):
        try: br._ollama_call("sys", "user")
        except Exception: pass

    p = captured.get("payload")
    if not p:
        err("FB-1: mock did not intercept urlopen — dict not captured")
    if p.get("keep_alive") != "30m":
        err(f"FB-1: FALSIFIED — _ollama_call keep_alive={p.get('keep_alive')!r} (expected '30m')")
    ok("FB-1: _ollama_call sends keep_alive='30m' in the actual dict")


# ── FB-2: _ollama_stream payload contains keep_alive="30m" ──────────────────────
def test_fb2_ollama_stream_keep_alive():
    import runtime.backend_router as br

    captured = {}
    # Stream response — a single JSON line with done=True
    fake_line = (json.dumps({
        "message": {"content": "ok"}, "done": True,
        "load_duration": 0, "prompt_eval_count": 1,
        "prompt_eval_duration": 0, "eval_count": 1, "eval_duration": 0,
    }) + "\n").encode()

    class _Resp:
        def __iter__(self): return iter([fake_line])
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def _capture(req, timeout=120):
        captured["payload"] = json.loads(req.data.decode())
        return _Resp()

    with mock.patch("urllib.request.urlopen", _capture):
        try: br._ollama_stream("sys", "user")
        except Exception: pass

    p = captured.get("payload")
    if not p:
        err("FB-2: mock did not intercept urlopen for stream call")
    if p.get("keep_alive") != "30m":
        err(f"FB-2: FALSIFIED — _ollama_stream keep_alive={p.get('keep_alive')!r}")
    ok("FB-2: _ollama_stream sends keep_alive='30m' in the actual dict")


# ── FB-3: backends/ollama_backend.py — every call path guarded ─────────────────
def test_fb3_ollama_backend_keep_alive():
    # This backend is not on the live path today, but the card says "every call path".
    # A source-level check is enough: it uses `requests` which we don't stub here.
    from backends import ollama_backend
    src = inspect.getsource(ollama_backend.OllamaBackend._call)
    if '"keep_alive"' not in src and "'keep_alive'" not in src:
        err("FB-3: backends/ollama_backend.py._call missing keep_alive — orphaned path still off-guard")
    if "30m" not in src:
        err("FB-3: keep_alive present but not '30m' in backends/ollama_backend.py._call")
    ok("FB-3: backends/ollama_backend.py._call carries keep_alive='30m'")


# ── FB-4: prompt_builder.build() populates _last_prompt_audit ───────────────────
def test_fb4_prompt_audit_populated():
    from runtime.prompt_builder import build, _last_prompt_audit
    _last_prompt_audit.clear()
    prompt = build(
        "hello",
        attention={"high_priority_memory": ["h1"], "medium_priority_memory": [],
                   "emotional_context": {}, "intent": "chat"},
        vault_context="world stuff",
        personality_block="[PERSONA] test",
        exec_decision={"tone": "DIRECT", "max_sentences": 2, "action": "answer"},
    )
    if not _last_prompt_audit:
        err("FB-4: _last_prompt_audit not populated after build()")
    blocks = _last_prompt_audit.get("blocks", [])
    if not blocks:
        err("FB-4: audit has no blocks")
    names = {b["name"] for b in blocks}
    for required in ("living_presence_spec", "personality_block", "active_memory",
                     "world_knowledge", "executive_directive"):
        if required not in names:
            err(f"FB-4: audit missing block {required!r} — present: {sorted(names)}")
    ok(f"FB-4: audit populated with {len(blocks)} blocks: {sorted(names)}")


# ── FB-5: audit shape — {name, chars, est_tokens, pct_tokens}; totals reconcile ─
def test_fb5_audit_shape_and_totals():
    from runtime.prompt_builder import build, _last_prompt_audit
    _last_prompt_audit.clear()
    _ = build("x", attention={"high_priority_memory": [], "medium_priority_memory": [],
                              "emotional_context": {}, "intent": "chat"})
    for b in _last_prompt_audit["blocks"]:
        for key in ("name", "chars", "est_tokens", "pct_tokens"):
            if key not in b:
                err(f"FB-5: block {b.get('name')!r} missing key {key!r}")
        if b["chars"] <= 0 or b["est_tokens"] <= 0:
            err(f"FB-5: block {b['name']!r} has non-positive size: {b}")
    # totals reconcile against the sum
    summed_chars  = sum(b["chars"]      for b in _last_prompt_audit["blocks"])
    summed_tokens = sum(b["est_tokens"] for b in _last_prompt_audit["blocks"])
    if summed_chars != _last_prompt_audit["total_chars"]:
        err(f"FB-5: total_chars {_last_prompt_audit['total_chars']} != summed {summed_chars}")
    if summed_tokens != _last_prompt_audit["total_est_tokens"]:
        err(f"FB-5: total_est_tokens {_last_prompt_audit['total_est_tokens']} != summed {summed_tokens}")
    # pct sums to ~100 (±0.5 for rounding)
    pct_sum = round(sum(b["pct_tokens"] for b in _last_prompt_audit["blocks"]), 1)
    if abs(pct_sum - 100.0) > 0.6:
        err(f"FB-5: pct_tokens summing to {pct_sum}, expected ~100")
    ok(f"FB-5: audit shape valid; totals reconcile; pct sum = {pct_sum}")


# ── FB-6: server.py backend_health write includes prompt_audit ──────────────────
def test_fb6_server_writes_prompt_audit():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    if "_last_prompt_audit" not in src:
        err("FB-6: server.py does not read _last_prompt_audit from prompt_builder")
    if "**_bh_prompt" not in src and "'prompt_audit'" not in src and '"prompt_audit"' not in src:
        err("FB-6: server.py does not merge prompt_audit into backend_health.json")
    ok("FB-6: server.py backend_health write includes prompt_audit block")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("F-B — Ollama keep_alive on every path + per-block prompt audit (card 0047)")
    print()
    test_fb1_ollama_call_keep_alive()
    test_fb2_ollama_stream_keep_alive()
    test_fb3_ollama_backend_keep_alive()
    test_fb4_prompt_audit_populated()
    test_fb5_audit_shape_and_totals()
    test_fb6_server_writes_prompt_audit()
    print()
    print("6/6 PASS — F-B: keep_alive present on every Ollama call path;")
    print("            per-block prompt audit exposed via backend_health.json.")
    print()
    print("PROVEN when: every Ollama payload carries keep_alive='30m' (so a stray")
    print("call cannot silently shorten the model residency timer to the 5-min default);")
    print("and prompt_audit reveals where the 7,281 prompt_eval_tokens go, block by block.")
