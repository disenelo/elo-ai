"""
capabilities/alexa_ingress.py — Alexa ingress: David talks to eLo through an Echo.

Source: blender/agent_bus/builder3/START_HERE.md Job 4 — "Alexa currently has
outbound push only (alexa_agent.py local TTS). No Alexa request handler, no
utterance ingress. eLo cannot hear Alexa — only shout at it. Build the ingress
path so David can talk to eLo through Alexa and get a real response back."

Flow:  Echo → Alexa custom skill → HTTPS (tunnel) → this module's own listener
       (default 127.0.0.1:5051, POST /alexa only) → verify → the same turn
       pipeline as /chat → eLo's reply as Alexa speech.

Two constraints from Amazon's custom-skill contract:
  1. A self-hosted HTTPS endpoint must verify every request: signature-cert
     URL, cert chain + SAN echo-api.amazon.com, Signature-256 over the raw
     body, timestamp within 150 s. Also checked here: applicationId ==
     ALEXA_SKILL_ID. Unverified requests are refused — the endpoint must never
     let an outsider drive eLo (Spotify, files, …). The listener serves
     nothing but /alexa, so /chat is never exposed through the tunnel.
  2. Alexa abandons a reply after 8 s; an eLo turn can take ~13 s. A turn not
     finished by _BUDGET_S is kept: eLo says he's on it, and the finished
     answer is given on David's next utterance ("go on").
"""
from __future__ import annotations

import base64
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from posixpath import normpath

_BUDGET_S = 6.5            # leave margin under Alexa's 8 s
_MAX_SKEW_S = 150          # Amazon: reject requests older/newer than 150 s
_CERT_SAN = "echo-api.amazon.com"
_cert_cache: dict[str, tuple[float, list]] = {}


# ── 1 · request verification ──────────────────────────────────────────────────

def _valid_cert_url(url: str) -> bool:
    try:
        u = urlparse(url)
    except Exception:
        return False
    if (u.scheme or "").lower() != "https" or (u.hostname or "").lower() != "s3.amazonaws.com":
        return False
    if u.port not in (None, 443):
        return False
    return normpath(u.path or "/").startswith("/echo.api/")


def _cert_chain(url: str) -> list:
    from cryptography import x509
    hit = _cert_cache.get(url)
    if hit and time.time() - hit[0] < 3600:
        return hit[1]
    import httpx
    pem = httpx.get(url, timeout=5.0).content
    chain = x509.load_pem_x509_certificates(pem)
    _cert_cache[url] = (time.time(), chain)
    return chain


_roots: list = []


def _trusted_roots() -> list:
    """certifi's roots, one at a time: a malformed root (certifi currently ships
    one with a non-positive serial) is skipped instead of failing every check."""
    global _roots
    if not _roots:
        import certifi
        import warnings
        from cryptography import x509
        pem = open(certifi.where(), "rb").read()
        for block in re.findall(rb"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----", pem, re.S):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    _roots.append(x509.load_pem_x509_certificate(block))
            except Exception:
                continue
    return _roots


def _verify_chain(chain: list) -> None:
    """Leaf valid now, issued for echo-api.amazon.com, chaining to a trusted root."""
    from cryptography import x509
    from cryptography.x509.verification import PolicyBuilder, Store
    roots = _trusted_roots()
    verifier = (PolicyBuilder().store(Store(roots)).time(datetime.now(timezone.utc))
                .build_server_verifier(x509.DNSName(_CERT_SAN)))
    verifier.verify(chain[0], chain[1:])


def verify(headers: dict, body: bytes, skill_id: str | None = None) -> tuple[bool, str]:
    """(ok, reason). Every check must pass; any failure refuses the request."""
    skill_id = skill_id if skill_id is not None else os.environ.get("ALEXA_SKILL_ID", "")
    if not skill_id:
        return False, "ALEXA_SKILL_ID not set — ingress disabled"
    h = {k.lower(): v for k, v in headers.items()}
    url = h.get("signaturecertchainurl", "")
    sig = h.get("signature-256", "")
    if not url or not sig:
        return False, "missing signature headers"
    if not _valid_cert_url(url):
        return False, "signature cert URL not an Amazon echo.api URL"
    try:
        req = json.loads(body.decode("utf-8"))
    except Exception:
        return False, "body is not JSON"
    app = ((req.get("context") or {}).get("System") or {}).get("application", {}).get("applicationId") \
        or ((req.get("session") or {}).get("application") or {}).get("applicationId", "")
    if app != skill_id:
        return False, "applicationId does not match ALEXA_SKILL_ID"
    try:
        ts = datetime.fromisoformat(req["request"]["timestamp"].replace("Z", "+00:00"))
        if abs((datetime.now(timezone.utc) - ts).total_seconds()) > _MAX_SKEW_S:
            return False, "timestamp outside 150 s"
    except Exception:
        return False, "missing/invalid timestamp"
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        chain = _cert_chain(url)
        _verify_chain(chain)
        chain[0].public_key().verify(base64.b64decode(sig), body, padding.PKCS1v15(), hashes.SHA256())
    except Exception as e:
        return False, f"signature/certificate check failed: {type(e).__name__}"
    return True, "verified"


# ── 2 · turns, inside Alexa's time limit ──────────────────────────────────────

_pending: dict = {}          # {"utterance", "thread", "result", "done": Event}
_pending_lock = threading.Lock()
_GO_ON_RE = re.compile(r"^(?:go on|and|well|so|what|what is it|tell me|carry on|yes|yeah|ok(?:ay)?|ready|and\??)$", re.I)


def _run(turn_fn, utterance: str) -> dict:
    slot = {"utterance": utterance, "result": None, "done": threading.Event()}

    def work():
        try:
            slot["result"] = turn_fn(utterance)
        except Exception as e:
            slot["result"] = {"response": "", "error": str(e)}
        finally:
            slot["done"].set()

    threading.Thread(target=work, daemon=True).start()
    return slot


def _text(result: dict | None) -> str:
    t = ((result or {}).get("response") or "").strip()
    return t or "I lost that one — say it again?"


def talk(utterance: str, turn_fn) -> str:
    """eLo's spoken reply to one Alexa utterance, within the time budget."""
    with _pending_lock:
        p = _pending.get("slot")
        if p is not None:
            if p["done"].is_set():
                _pending.clear()
                prefix = "" if _GO_ON_RE.match(utterance.strip()) else "On what you asked before — "
                return prefix + _text(p["result"])
            return "Still on your last one — say 'go on' in a moment."
        slot = _run(turn_fn, utterance)
        if slot["done"].wait(_BUDGET_S):
            return _text(slot["result"])
        _pending["slot"] = slot
        return "Give me a sec on that — say 'go on' and I'll tell you."


# ── 3 · Alexa request → Alexa response ────────────────────────────────────────

def _speech(text: str, end: bool = False, reprompt: str | None = "Anything else?") -> dict:
    resp: dict = {"outputSpeech": {"type": "PlainText", "text": text[:7900]}, "shouldEndSession": end}
    if reprompt and not end:
        resp["reprompt"] = {"outputSpeech": {"type": "PlainText", "text": reprompt}}
    return {"version": "1.0", "response": resp}


def handle(req: dict, turn_fn) -> dict:
    r = req.get("request") or {}
    kind = r.get("type", "")
    if kind == "LaunchRequest":
        return _speech("Yo — it's eLo. What's up?", reprompt="I'm here — what's up?")
    if kind == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}
    if kind != "IntentRequest":
        return _speech("Didn't catch that — say it again?")
    intent = (r.get("intent") or {})
    name = intent.get("name", "")
    if name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
        return _speech("Later.", end=True)
    if name == "AMAZON.HelpIntent":
        return _speech("Just talk to me like normal — I'm the same eLo as on your Mac.")
    if name == "TalkIntent":
        utterance = (((intent.get("slots") or {}).get("utterance") or {}).get("value") or "").strip()
        if not utterance:
            return _speech("Didn't catch that — say it again?")
        return _speech(talk(utterance, turn_fn))
    return _speech("Didn't catch that — say it again?")


# ── 4 · the dedicated listener ────────────────────────────────────────────────

def serve(turn_fn, port: int | None = None) -> object | None:
    """Start the /alexa-only listener on 127.0.0.1 when ALEXA_SKILL_ID is set.
    The tunnel (e.g. cloudflared) points here, never at the main server."""
    if not os.environ.get("ALEXA_SKILL_ID"):
        return None
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    port = port or int(os.environ.get("ALEXA_PORT", "5051"))

    class _H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code: int, payload: dict) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json;charset=UTF-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path.rstrip("/") != "/alexa":
                self._send(404, {"error": "not found"})
                return
            body = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
            ok, why = verify(dict(self.headers), body)
            if not ok:
                print(f"[alexa] refused: {why}", flush=True)
                self._send(400, {"error": "request verification failed"})
                return
            req = json.loads(body.decode("utf-8"))
            print(f"[alexa] {req.get('request', {}).get('type')} accepted", flush=True)
            self._send(200, handle(req, turn_fn))

        def do_GET(self):
            self._send(404, {"error": "not found"})

    srv = ThreadingHTTPServer(("127.0.0.1", port), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[alexa] ingress listening on 127.0.0.1:{port}/alexa", flush=True)
    return srv
