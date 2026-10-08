"""
ALEXA-MODEL-OVERRIDE (B3 fix of 392f9d3, David's OK 2026-10-08): the Alexa model
reaches the streaming reply even though the turn runs on another thread.
Offline: Ollama HTTP stubbed.
"""
import io, json, threading
from runtime import backend_router as br


def _fake_urlopen(seen):
    def f(req, timeout=None):
        seen.append(json.loads(req.data.decode())["model"])
        body = json.dumps({"message": {"content": "hi"}, "done": True}).encode() + b"\n"
        r = io.BytesIO(body); r.status = 200
        r.__enter__ = lambda *a: r; r.__exit__ = lambda *a: False
        return r
    return f


def _stream_model(monkeypatch):
    seen = []
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(seen))
    try:
        br._ollama_stream("sys", "hello")
    except Exception:
        pass
    return seen[0] if seen else None


def test_stream_uses_turn_model_set_on_another_thread(monkeypatch):
    monkeypatch.setenv("ELO_OLLAMA_MODEL", "qwen2.5-coder:14b")
    t = threading.Thread(target=lambda: setattr(br._per_turn, "ollama_model", "mistral-nemo:12b"))
    t.start(); t.join()                          # set on the worker, read on this thread
    try:
        assert _stream_model(monkeypatch) == "mistral-nemo:12b"
    finally:
        br._per_turn.ollama_model = None


def test_stream_default_when_no_turn_model(monkeypatch):
    monkeypatch.setenv("ELO_OLLAMA_MODEL", "qwen2.5-coder:14b")
    br._per_turn.ollama_model = None
    assert _stream_model(monkeypatch) == "qwen2.5-coder:14b"
