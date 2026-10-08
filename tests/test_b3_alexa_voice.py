"""
B3 — eLo's ElevenLabs voice on the Echo: SSML <audio> clip, else Alexa's voice.
Offline: TTS stubbed. Not live evidence.
"""
import time
import pytest
from capabilities import alexa_ingress as ai

BASE = "https://example.trycloudflare.com"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k"); monkeypatch.setenv("ELEVENLABS_VOICE_ID", "v")
    monkeypatch.delenv("ALEXA_VOICE", raising=False)
    monkeypatch.setattr(ai, "_alexa_mp3", lambda text: b"MP3:" + text.encode())
    ai._audio.clear()


def _launch():
    return {"request": {"type": "LaunchRequest"}}


def test_voiced_reply_is_ssml_audio_served_by_listener():
    out = ai.handle(_launch(), lambda t: {}, base=BASE)["response"]["outputSpeech"]
    assert out["type"] == "SSML" and out["ssml"].startswith(f'<speak><audio src="{BASE}/alexa/audio/')
    path = out["ssml"].split(BASE, 1)[1].split('"')[0]
    assert ai.audio_clip(path) == "MP3:Yo — it's eLo. What's up?".encode()


def test_talk_reply_voiced():
    req = {"request": {"type": "IntentRequest", "intent": {"name": "TalkIntent",
           "slots": {"utterance": {"value": "hi"}}}}}
    out = ai.handle(req, lambda t: {"response": "Hey David."}, base=BASE)["response"]["outputSpeech"]
    assert out["type"] == "SSML"


@pytest.mark.parametrize("why", ["no_base", "off", "no_audio", "slow"])
def test_falls_back_to_alexa_voice(why, monkeypatch):
    base = None if why == "no_base" else BASE
    if why == "off": monkeypatch.setenv("ALEXA_VOICE", "off")
    if why == "no_audio": monkeypatch.setattr(ai, "_alexa_mp3", lambda t: None)
    if why == "slow":
        monkeypatch.setattr(ai, "_VOICE_DEADLINE_S", 1.6)
        monkeypatch.setattr(ai, "_alexa_mp3", lambda t: time.sleep(3) or b"x")
    out = ai.handle(_launch(), lambda t: {}, base=base)["response"]["outputSpeech"]
    assert out == {"type": "PlainText", "text": "Yo — it's eLo. What's up?"}


@pytest.mark.parametrize("p", ["/alexa/audio/abc.mp3", "/chat", "/alexa/audio/" + "0" * 32 + ".mp3",
                               "/alexa/audio/../x.mp3", "/"])
def test_only_known_tokens_are_served(p):
    assert ai.audio_clip(p) is None


def test_clips_expire(monkeypatch):
    tok = ai._store(b"x")
    monkeypatch.setattr(ai.time, "time", lambda: 10 ** 12)
    assert ai.audio_clip(f"/alexa/audio/{tok}.mp3") is None
