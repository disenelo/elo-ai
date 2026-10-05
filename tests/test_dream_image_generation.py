"""
tests/test_dream_image_generation.py — 166 dreams, zero pictures.

eLo has dreamt 166 times. Not one produced an image. Three dreams reached the
image stage and every scene failed; the live journal records why:

    DALL-E 3: Error code: 400 - {'error': {'message': "Unknown parameter:
    'response_format'.", 'type': 'invalid_request_error', ...}}        x6
    DALL-E 3: No module named 'openai'                                 x4
    SD local: <urlopen error [Errno 111] Connection refused>

The second is already resolved — openai 3.19.2 is installed. The first was
live: newer image endpoints reject response_format outright and it was sent
unconditionally, so both DALL-E paths 400'd and the chain fell through to a
local Stable Diffusion that is not running. Every route failed for a different
reason and the dream recorded no art.

These prompts are what was lost, from the most recent dream:

    "An abandoned robot station, where light moves slower than sound;
     a machine breathing recur throughout. curiosity dominant"
    "a robot folded inward until it holds a room"
    "An abandoned childhood station, where nothing casts a shadow"

No test here calls a real API. They run against doubles that reproduce the
recorded failure exactly.
"""
from __future__ import annotations

import base64

import pytest

import tools.image_gen_agent as iga

PNG = b"\x89PNG\r\n\x1a\n" + b"fake"


class _Item:
    def __init__(self, b64=None, url=None):
        if b64 is not None:
            self.b64_json = b64
        if url is not None:
            self.url = url


class _Resp:
    def __init__(self, item):
        self.data = [item]


class _RejectsResponseFormat:
    """The live failure: 400 Unknown parameter: 'response_format'."""

    def __init__(self):
        self.calls = []
        self.images = self

    def generate(self, **kw):
        self.calls.append(kw)
        if "response_format" in kw:
            raise RuntimeError(
                "Error code: 400 - {'error': {'message': \"Unknown parameter: "
                "'response_format'.\", 'type': 'invalid_request_error'}}"
            )
        return _Resp(_Item(url="https://example.invalid/i.png"))


class _AcceptsResponseFormat:
    """An older SDK, which is why the parameter is still tried first."""

    def __init__(self):
        self.calls = []
        self.images = self

    def generate(self, **kw):
        self.calls.append(kw)
        return _Resp(_Item(b64=base64.b64encode(PNG).decode()))


class _FakeHTTP:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return PNG


def test_the_recorded_400_no_longer_loses_the_image(monkeypatch):
    # Dropping response_format means the API returns a URL instead of base64,
    # so the download is part of the path being tested. Stubbed, not fetched.
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _FakeHTTP())

    c = _RejectsResponseFormat()
    out = iga._openai_image_bytes(c, "dall-e-3", "a machine breathing")

    assert out == PNG
    assert len(c.calls) == 2, "should retry exactly once, without the parameter"
    assert "response_format" in c.calls[0]
    assert "response_format" not in c.calls[1]


def test_an_older_sdk_still_gets_base64_in_one_call():
    c = _AcceptsResponseFormat()
    assert iga._openai_image_bytes(c, "dall-e-2", "a room") == PNG
    assert len(c.calls) == 1, "no pointless retry when the parameter works"


def test_an_unrelated_error_is_not_swallowed_as_a_retry():
    class _Broken:
        def __init__(self):
            self.images = self

        def generate(self, **kw):
            raise RuntimeError("Error code: 401 - invalid api key")

    with pytest.raises(RuntimeError, match="401"):
        iga._openai_image_bytes(_Broken(), "dall-e-3", "x")


def test_a_response_with_neither_shape_fails_loudly():
    class _Empty:
        def __init__(self):
            self.images = self

        def generate(self, **kw):
            return _Resp(_Item())

    with pytest.raises(RuntimeError, match="neither b64_json nor url"):
        iga._openai_image_bytes(_Empty(), "dall-e-3", "x")
