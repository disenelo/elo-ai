"""B3: pre_ack (B1 3332caf) fires before slow ops — documents, Spotify play — and never for devices. Offline."""
import pytest
import runtime.pre_ack as pa


@pytest.fixture
def acks(monkeypatch):
    seen = []
    monkeypatch.setattr(pa, "emit", lambda cap, text="", *a, **k: seen.append(cap))
    return seen


def test_document_acks_before_writing(acks, monkeypatch, tmp_path):
    import tools.document_writer as dw, tools.tool_router as tr
    monkeypatch.setattr(dw, "_DIR", str(tmp_path))
    order = []
    monkeypatch.setattr(dw, "_generate", lambda s, u: order.append(("write", list(acks))) or "# List\n- a")
    tr._direct_intercepts("make me a list of fabrics")
    assert order and order[0][1] == ["document_write"]          # ack happened before the write


@pytest.mark.parametrize("q", ["put on jazz", "play some music"])
def test_spotify_play_acks(acks, monkeypatch, q):
    import tools.spotify_play as sp
    monkeypatch.setattr(sp, "play", lambda t: "Playing.")
    monkeypatch.setattr(sp, "play_music", lambda: ("play", "Playing."))
    sp._handle_line(q)
    assert acks == ["spotify_play"]


def test_pause_does_not_ack(acks, monkeypatch):
    import tools.spotify_play as sp
    monkeypatch.setattr(sp, "control", lambda a: "Paused.")
    sp._handle_line("pause the music")
    assert acks == []


def test_device_spoken_route_never_acks(acks, monkeypatch, tmp_path):
    import tools.device_control as dc
    monkeypatch.delenv("ELO_DEVICE_ROUTE", raising=False)
    monkeypatch.setattr(dc, "_say_on_mac", lambda t: True)
    monkeypatch.setattr(dc.time, "sleep", lambda s: None)
    monkeypatch.setattr(dc, "_ALLOW_FILE", str(tmp_path / "x.json"))
    dc.run("Lights Out")
    assert acks == []          # an ack would talk over "Alexa … turn off the lights"
