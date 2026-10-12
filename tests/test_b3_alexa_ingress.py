"""
B3-ALEXA-INGRESS-001 — capabilities/alexa_ingress.py

Wiring tests (not live evidence): request verification refuses everything that
isn't a correctly signed, current request for our skill; the handler maps Alexa
requests to eLo turns; slow turns are held and delivered on "go on".
"""
import base64
import json
import time
from datetime import datetime, timedelta, timezone

import pytest
import threading

from capabilities import alexa_ingress as ai

@pytest.fixture(autouse=True)
def _echo_not_connected(monkeypatch):
    monkeypatch.setattr(ai, "_echo_is_mouth", lambda: False)
    import tools.echo_speaker as _es_reset
    _es_reset.release_voice()
    monkeypatch.setenv("ALEXA_REPLY", "skill")     # these tests cover the Alexa-speaks mode


SKILL = "amzn1.ask.skill.test-0000"
URL = "https://s3.amazonaws.com/echo.api/echo-api-cert.pem"


def _req(app=SKILL, ts=None, kind="IntentRequest", utterance="hello"):
    ts = ts or datetime.now(timezone.utc)
    return {
        "version": "1.0",
        "session": {"application": {"applicationId": app}},
        "context": {"System": {"application": {"applicationId": app}}},
        "request": {"type": kind, "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "intent": {"name": "TalkIntent", "slots": {"utterance": {"value": utterance}}}},
    }


@pytest.fixture
def signer(monkeypatch):
    """A local RSA key + cert standing in for Amazon's; chain check stubbed so the
    signature step itself is what's exercised."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "echo-api.amazon.com")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1))
            .sign(key, hashes.SHA256()))
    monkeypatch.setattr(ai, "_cert_chain", lambda url: [cert])
    monkeypatch.setattr(ai, "_verify_chain", lambda chain: None)

    def sign(body: bytes) -> str:
        return base64.b64encode(key.sign(body, padding.PKCS1v15(), hashes.SHA256())).decode()
    return sign


def _headers(sig, url=URL):
    return {"SignatureCertChainUrl": url, "Signature-256": sig}


# ── verification ──────────────────────────────────────────────────────────────

def test_correctly_signed_request_passes(signer):
    body = json.dumps(_req()).encode()
    assert ai.verify(_headers(signer(body)), body, SKILL) == (True, "verified")


def test_tampered_body_refused(signer):
    body = json.dumps(_req()).encode()
    sig = signer(body)
    tampered = json.dumps(_req(utterance="open my files")).encode()
    ok, why = ai.verify(_headers(sig), tampered, SKILL)
    assert not ok and "signature" in why


def test_no_skill_id_means_ingress_off(signer):
    body = json.dumps(_req()).encode()
    assert ai.verify(_headers(signer(body)), body, "")[0] is False


def test_wrong_skill_refused(signer):
    body = json.dumps(_req(app="amzn1.ask.skill.someone-else")).encode()
    ok, why = ai.verify(_headers(signer(body)), body, SKILL)
    assert not ok and "applicationId" in why


def test_stale_timestamp_refused(signer):
    body = json.dumps(_req(ts=datetime.now(timezone.utc) - timedelta(seconds=300))).encode()
    ok, why = ai.verify(_headers(signer(body)), body, SKILL)
    assert not ok and "150" in why


def test_missing_headers_refused():
    body = json.dumps(_req()).encode()
    assert ai.verify({}, body, SKILL)[0] is False


@pytest.mark.parametrize("url", [
    "http://s3.amazonaws.com/echo.api/echo-api-cert.pem",          # not https
    "https://s3.amazonaws.evil.com/echo.api/echo-api-cert.pem",    # wrong host
    "https://s3.amazonaws.com/EcHo.aPi/echo-api-cert.pem",         # path case-sensitive
    "https://s3.amazonaws.com/invalid.path/echo-api-cert.pem",     # wrong path
    "https://s3.amazonaws.com/echo.api/../invalid.path/cert.pem",  # traversal
    "https://s3.amazonaws.com:563/echo.api/echo-api-cert.pem",     # wrong port
])
def test_bad_cert_urls_refused(url):
    assert ai._valid_cert_url(url) is False


@pytest.mark.parametrize("url", [
    "https://s3.amazonaws.com/echo.api/echo-api-cert.pem",
    "https://s3.amazonaws.com:443/echo.api/echo-api-cert.pem",
    "https://S3.AMAZONAWS.COM/echo.api/echo-api-cert.pem",
    "https://s3.amazonaws.com/echo.api/../echo.api/echo-api-cert.pem",
])
def test_good_cert_urls_accepted(url):
    assert ai._valid_cert_url(url) is True


def test_self_signed_chain_fails_trust_check():
    """The real chain check refuses a cert that doesn't chain to a trusted root."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "echo-api.amazon.com")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(2)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName("echo-api.amazon.com")]), False)
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1))
            .sign(key, hashes.SHA256()))
    with pytest.raises(Exception):
        ai._verify_chain([cert])


# ── handler ───────────────────────────────────────────────────────────────────

def _say(resp):
    return resp["response"]["outputSpeech"]["text"]


def test_launch_is_answered_by_the_brain_and_stop_is_quiet():
    seen = []
    r = ai.handle(_req(kind="LaunchRequest"), lambda t: seen.append(t) or {"response": "Yo, what's good?"})
    assert seen == [ai.OPEN_UTTERANCE] and _say(r) == "Yo, what's good?"
    stop = {"request": {"type": "IntentRequest", "intent": {"name": "AMAZON.StopIntent"}}}
    r = ai.handle(stop, lambda t: {})
    assert r["response"]["shouldEndSession"] is True and "outputSpeech" not in r["response"]


def test_no_words_is_alexa_system_not_elo():
    fb = {"request": {"type": "IntentRequest", "intent": {"name": "AMAZON.FallbackIntent"}}}
    assert _say(ai.handle(fb, lambda t: pytest.fail("brain must not be called"))) == ai.SYS_MISSED


def test_talk_goes_through_the_turn_and_keeps_session_open():
    seen = []
    r = ai.handle(_req(utterance="how are you"), lambda t: seen.append(t) or {"response": "Good, you?"})
    assert seen == ["how are you"]
    assert _say(r) == "Good, you?" and r["response"]["shouldEndSession"] is False


def test_slow_turn_is_held_then_delivered(monkeypatch):
    monkeypatch.setattr(ai, "_BUDGET_S", 0.2)
    ai._pending.clear()

    def slow(t):
        time.sleep(0.5)
        return {"response": "Here's the long answer."}
    first = _say(ai.handle(_req(utterance="tell me something long"), slow))
    assert first == ai.SYS_SLOW
    assert _say(ai.handle(_req(utterance="go on"), slow)) == ai.SYS_STILL   # not done yet
    time.sleep(0.5)
    assert _say(ai.handle(_req(utterance="go on"), slow)) == "Here's the long answer."
    assert not ai._pending


def test_listener_off_without_skill_id(monkeypatch):
    monkeypatch.delenv("ALEXA_SKILL_ID", raising=False)
    assert ai.serve(lambda t: {}) is None


def test_reply_model_is_the_inner_thought_model(monkeypatch):
    for k in ("ALEXA_OLLAMA_MODEL", "ELO_INNER_THOUGHT_MODEL"):
        monkeypatch.delenv(k, raising=False)
    from runtime import inner_thought_first as itf
    assert ai.reply_model() == itf._MODEL == "mistral-nemo:12b"
    monkeypatch.setenv("ALEXA_OLLAMA_MODEL", "x:1b")
    assert ai.reply_model() == "x:1b"


@pytest.mark.parametrize("where", ["mac", "echo"])
def test_ears_mode_runs_turn_in_background_and_alexa_says_nothing(monkeypatch, where):
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    import tools.echo_speaker as es
    monkeypatch.setattr(es, "voice_output", lambda: where)
    monkeypatch.setattr(ai, "_ADAPT_BUDGET_S", 0.1)
    seen, gate = [], threading.Event()
    def turn(t):
        seen.append(t); time.sleep(0.3); gate.set(); return {"response": "his reply plays on the chosen speaker"}
    r = ai.handle(_req(utterance="how's it going"), turn)
    assert r["response"] == {"shouldEndSession": True}
    assert gate.wait(2) and seen == ["how's it going"]


def test_ears_is_the_default(monkeypatch):
    monkeypatch.delenv("ALEXA_REPLY", raising=False)
    assert ai._reply_mode() == "ears"


# ── WO-B3-0011 · contextual output choice ─────────────────────────────────────

def test_alexa_input_pins_reply_to_echo_overriding_manual_mac_setting(monkeypatch):
    """Input channel wins over David's manual Presence setting (David L3 2026-10-10)."""
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    import tools.echo_speaker as es
    monkeypatch.setattr(es, "device_index", lambda fresh=False: 1)   # Echo connected
    monkeypatch.setattr(es, "voice_output", lambda: "mac")           # David's setting = Mac
    es.stop_wanting()
    assert es.speaking() is False
    monkeypatch.setattr(ai, "_ADAPT_BUDGET_S", 0.1)
    gate = threading.Event()
    ai.handle(_req(utterance="what's on today"), lambda t: time.sleep(0.3) or gate.set() or {"response": "the usual"})
    assert gate.wait(2)
    es.release_voice()
    assert es.speaking() is True, "Alexa-arriving turn must route eLo's voice to the Echo"
    es.stop_wanting()


def test_alexa_input_without_echo_connected_does_not_pin(monkeypatch):
    """Echo disconnected → no pin; voice_engine already falls back to the Mac."""
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    import tools.echo_speaker as es
    monkeypatch.setattr(es, "device_index", lambda fresh=False: None)
    monkeypatch.setattr(es, "voice_output", lambda: "mac")
    es.stop_wanting()
    gate = threading.Event()
    ai.handle(_req(utterance="still there"), lambda t: gate.set() or {"response": "yep"})
    assert gate.wait(2)
    assert es._want["until"] == 0.0, "no want_for pin when the Echo isn't connected"


def _slow(reply="later", secs=0.4):
    """A turn slower than the (shortened) Alexa window: today's ~20 s case."""
    def turn(t):
        time.sleep(secs); return {"response": reply}
    return turn


# ── "heard you" chime (WO-0017 gap 7) ───────────────────────────────────────────

def test_ears_mode_plays_heard_cue_not_words(monkeypatch):
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    monkeypatch.delenv("ALEXA_HEARD_CUE", raising=False)
    monkeypatch.setattr(ai, "_chime_mp3", lambda: b"CHIME")
    monkeypatch.setattr(ai, "_ADAPT_BUDGET_S", 0.1)
    r = ai.handle(_req(utterance="how's it going"), _slow(), base="https://example.ts.net")["response"]
    assert r["shouldEndSession"] is True
    ssml = r["outputSpeech"]["ssml"]
    assert ssml.startswith('<speak><audio src="https://example.ts.net/alexa/audio/') and "how's" not in ssml
    assert ai.audio_clip(ssml.split("example.ts.net", 1)[1].split('"')[0]) == b"CHIME"


def test_heard_cue_can_be_turned_off(monkeypatch):
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    monkeypatch.setenv("ALEXA_HEARD_CUE", "off")
    monkeypatch.setattr(ai, "_ADAPT_BUDGET_S", 0.1)
    r = ai.handle(_req(utterance="hi"), _slow(), base="https://example.ts.net")["response"]
    assert r == {"shouldEndSession": True}



# ── adaptive conversation (B3 2026-10-12): fast reply → Alexa speaks + keeps listening ──

def test_fast_reply_becomes_open_conversation(monkeypatch):
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    r = ai.handle(_req(utterance="what's the weather"), lambda t: {"response": "Grey and drizzly, 12 degrees."})
    assert r["response"]["shouldEndSession"] is False                       # Alexa keeps listening
    assert r["response"]["outputSpeech"]["text"] == "Grey and drizzly, 12 degrees."


def test_fast_reply_is_not_heard_twice(monkeypatch):
    import tools.echo_speaker as es
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    ai.handle(_req(utterance="hi"), lambda t: {"response": "Hey."})
    assert es.speaking() is True                                            # routed to popen_play …
    p = es.popen_play("/tmp/none.mp3")                                       # … which swallows it
    assert p is not None and p.args == ["true"]
    assert es._holding() is False                                           # only once


def test_slow_reply_releases_the_hold(monkeypatch):
    import tools.echo_speaker as es
    monkeypatch.setenv("ALEXA_REPLY", "ears")
    monkeypatch.setattr(ai, "_ADAPT_BUDGET_S", 0.1)
    r = ai.handle(_req(utterance="hi"), _slow())
    assert r["response"]["shouldEndSession"] is True
    assert es._holding() is False                                           # reply will play normally
