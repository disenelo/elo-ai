"""
WO-B3-0009 — eLo writes documents into ~/Documents/eLo. Offline: the model is
stubbed and files go to a temp folder (never David's real Documents).
"""
import os
import pytest
import tools.document_writer as dw


@pytest.mark.parametrize("q", ["Make me a list of things to pack for the studio", "make a checklist for the kickstarter",
                               "Write that up", "can you write this up for me", "create a doc with the M-65 measurements",
                               "write me a summary of what we decided", "save that as a document",
                               "put that into a plan", "draft a brief for the eLo book cover"])
def test_document_requests(q):
    assert dw.is_document_request(q)


@pytest.mark.parametrize("q", ["make a note: buy milk", "remind me to call mum", "what's on my list today",
                               "I made a list yesterday", "write back to Sam", "tell me about the plan",
                               "what's the weather like"])
def test_not_document_requests(q):
    assert not dw.is_document_request(q)


@pytest.fixture
def _docs(tmp_path, monkeypatch):
    monkeypatch.setattr(dw, "_DIR", str(tmp_path / "eLo"))
    return tmp_path / "eLo"


def test_writes_markdown_file_and_says_where(_docs, monkeypatch):
    seen = {}
    def fake(system, user):
        seen["system"], seen["user"] = system, user
        return "# Studio packing list\n\n- Heat press\n- Silicone\n"
    monkeypatch.setattr(dw, "_generate", fake)
    r = dw.write_document("Make me a list of things to pack for the studio")
    assert r["success"] is True
    path = r["result"]["path"]
    assert path.startswith(str(_docs)) and path.endswith("-studio-packing-list.md")
    assert open(path).read().startswith("# Studio packing list")
    assert "Studio packing list" in r["result"]["line"] and os.path.basename(path) in r["result"]["line"]
    assert "Markdown" in seen["system"]


def test_plain_text_when_asked_and_no_overwrite(_docs, monkeypatch):
    monkeypatch.setattr(dw, "_generate", lambda s, u: "Ideas\nOne\nTwo")
    a = dw.write_document("create a text file with ideas")["result"]["path"]
    b = dw.write_document("create a text file with ideas")["result"]["path"]
    assert a.endswith(".txt") and b.endswith("-2.txt") and a != b


def test_write_that_up_includes_recent_conversation(_docs, monkeypatch):
    seen = {}
    monkeypatch.setattr(dw, "_recent_conversation", lambda limit=5: "David: we pick ngrok\neLo: good call")
    monkeypatch.setattr(dw, "_generate", lambda s, u: seen.setdefault("u", u) and "# Decision\nngrok")
    dw.write_document("write that up")
    assert "we pick ngrok" in seen["u"]


def test_failure_is_honest_and_writes_nothing(_docs, monkeypatch):
    def boom(s, u): raise TimeoutError("no model")
    monkeypatch.setattr(dw, "_generate", boom)
    r = dw.write_document("make me a list of fabrics")
    assert r["success"] is False and "couldn't write" in r["result"]["line"]
    assert not _docs.exists() or not any(_docs.iterdir())


def test_local_model_first_then_cloud(monkeypatch):
    calls = []
    monkeypatch.setattr(dw, "_ollama", lambda s, u, timeout=120: calls.append("local") or "")
    import tools.draft_agent as da
    monkeypatch.setattr(da, "_call_llm", lambda s, u, max_tokens=600: calls.append("cloud") or "x")
    assert dw._generate("s", "u") == "x" and calls == ["local", "cloud"]


def test_router_returns_the_line_directly(_docs, monkeypatch):
    import tools.tool_router as tr
    monkeypatch.setattr(dw, "_generate", lambda s, u: "# Fabric list\n- canvas")
    out = tr._direct_intercepts("make me a list of fabrics")
    assert out[1] == "create_document" and out[0].startswith("Done — I wrote it up")
    assert tr.get_direct_result() == out[0]
