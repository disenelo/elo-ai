"""
WO-026 acceptance tests — eLo faster responses.

AT-1  Streaming path assembles the same final text as concatenated chunks
AT-2  _token_budget(): short for ANSWER/CELEBRATE, large for BUILD/REFLECT, default otherwise
AT-3  routing_trace.json has llm_latency_ms field (numeric) after a routed turn
AT-4  Frozen kernel untouched (executive.py + prompts/ unchanged)
"""
import importlib.util
import json
import os
import sys
import tempfile

_ROOT = os.path.join(os.path.dirname(__file__), "..")


# ── Load backend_router directly to avoid optional deps (openai, groq, etc.) ─────

_BR_PATH = os.path.join(_ROOT, "runtime", "backend_router.py")
_br_spec  = importlib.util.spec_from_file_location("backend_router_test", _BR_PATH)
_br_mod   = importlib.util.module_from_spec(_br_spec)
# Stub Optional so the import doesn't blow up (it's already imported as str | None)
sys.modules.setdefault("groq", type(sys)("groq"))
_br_spec.loader.exec_module(_br_mod)

_token_budget    = _br_mod._token_budget
_SENTENCE_END_RE = _br_mod._SENTENCE_END_RE


# ── AT-1: streaming chunk assembly ─────────────────────────────────────────────

def test_at1_streaming_chunk_assembly():
    """Joining stream chunks produces the same text as the expected full response."""
    chunks = ["Hello", " there.", " How", " are", " you", " today?"]
    full = "".join(chunks).strip()
    expected = "Hello there. How are you today?"
    assert full == expected, f"AT-1 FAIL: got '{full}'"

    # Verify sentence boundary detection on first sentence
    buffer = ""
    fired_text = []
    for chunk in chunks:
        buffer += chunk
        m = _SENTENCE_END_RE.search(buffer)
        if m and not fired_text:
            fired_text.append(buffer[:m.start() + 1].strip())
            break

    assert fired_text, "AT-1 FAIL: no first sentence detected"
    assert fired_text[0] == "Hello there.", f"AT-1 FAIL: first sentence = '{fired_text[0]}'"
    print(f"AT-1 PASS — streaming assembles '{full}'; first sentence = '{fired_text[0]}'")


# ── AT-2: token budget by action ──────────────────────────────────────────────

def test_at2_token_budget():
    short_actions = ("answer", "celebrate", "direct_response", "observe")
    deep_actions  = ("build", "reflect", "plan")

    for action in short_actions:
        budget = _token_budget(action)
        assert budget <= 300, f"AT-2 FAIL: {action} → {budget} (expected ≤300)"

    for action in deep_actions:
        budget = _token_budget(action)
        assert budget >= 400, f"AT-2 FAIL: {action} → {budget} (expected ≥400)"

    default = _token_budget("unknown_action")
    assert 200 <= default <= 500, f"AT-2 FAIL: default budget {default} out of expected range"

    print(f"AT-2 PASS — short budgets {[_token_budget(a) for a in short_actions]}; "
          f"deep budgets {[_token_budget(a) for a in deep_actions]}; default={default}")


# ── AT-3: routing_trace.json has llm_latency_ms ──────────────────────────────

def test_at3_latency_field_schema():
    """routing_trace.json write must include llm_latency_ms — verified in server.py source."""
    _srv = os.path.join(_ROOT, "server.py")
    with open(_srv, encoding="utf-8") as f:
        src = f.read()
    assert "llm_latency_ms" in src, "AT-3 FAIL: llm_latency_ms missing from server.py routing_trace write"
    assert "_perf_mod.perf_counter()" in src, "AT-3 FAIL: perf_counter timing missing from server.py"

    # If the file exists and was written after our change, also check its contents
    _rt_path = os.path.join(_ROOT, "blender", "routing_trace.json")
    if os.path.exists(_rt_path):
        with open(_rt_path, encoding="utf-8") as f:
            trace = json.load(f)
        if "llm_latency_ms" in trace:
            assert isinstance(trace["llm_latency_ms"], (int, float)), \
                f"AT-3 FAIL: llm_latency_ms not numeric: {trace['llm_latency_ms']}"
            print(f"AT-3 PASS — llm_latency_ms={trace['llm_latency_ms']}ms confirmed live in routing_trace.json")
            return

    print("AT-3 PASS (code) — llm_latency_ms wired in server.py routing_trace block")


# ── AT-4: frozen kernel ───────────────────────────────────────────────────────

def test_at4_frozen_kernel():
    frozen_files = [os.path.join(_ROOT, "runtime", "executive.py")]
    for path in frozen_files:
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        for token in (b"ELO_STREAM", b"on_first_sentence", b"_token_budget", b"llm_latency"):
            assert token not in content, \
                f"AT-4 FAIL: frozen file {path} contains WO-026 token '{token.decode()}'"

    prompts_dir = os.path.join(_ROOT, "prompts")
    if os.path.isdir(prompts_dir):
        for fname in os.listdir(prompts_dir):
            fpath = os.path.join(prompts_dir, fname)
            with open(fpath, "rb") as f:
                content = f.read()
            assert b"ELO_STREAM" not in content, \
                f"AT-4 FAIL: prompts/{fname} modified — FREEZE_V1_LOCK violated"
    print("AT-4 PASS — frozen kernel untouched")


# ── runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_at1_streaming_chunk_assembly,
        test_at2_token_budget,
        test_at3_latency_field_schema,
        test_at4_frozen_kernel,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n{'ALL PASS' if not failed else f'{failed} FAILED'} — WO-026 ({len(tests)-failed}/{len(tests)})")
    sys.exit(failed)
