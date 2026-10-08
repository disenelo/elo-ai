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

from capabilities import alexa_ingress as ai

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
