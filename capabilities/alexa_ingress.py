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


# Only the brain speaks as eLo (David, 2026-10-08: "the responses to Alexa aren't
# eLo's — they're generically written"). eLo's voice carries brain text only.
# The few things the brain can't answer (Alexa didn't pass words on, the turn is
# still running) are Alexa's own system prompts: worded as Alexa, spoken in
# Alexa's voice, never as eLo.
SYS_SLOW = "eLo's working on that. Say 'go on' to hear him."
SYS_STILL = "eLo's still thinking. Say 'go on' in a moment."
SYS_MISSED = "I didn't catch that for eLo. Say it again?"
SYS_EMPTY = "eLo didn't answer that one. Try again?"
SYS_HELP = "You're talking to eLo. Just speak normally, and say stop when you're done."
OPEN_UTTERANCE = "hey eLo"   # opening the skill is David greeting eLo; the brain answers it


def _text(result: dict | None) -> tuple[str, bool]:
    t = ((result or {}).get("response") or "").strip()
    return (t, True) if t else (SYS_EMPTY, False)


def talk(utterance: str, turn_fn) -> tuple[str, bool]:
    """(reply, from_brain) for one Alexa utterance, within the time budget."""
    with _pending_lock:
        p = _pending.get("slot")
        if p is not None:
            if p["done"].is_set():
                _pending.clear()
                return _text(p["result"])
            return SYS_STILL, False
        slot = _run(turn_fn, utterance)
        if slot["done"].wait(_BUDGET_S):
            return _text(slot["result"])
        _pending["slot"] = slot
        return SYS_SLOW, False


def reply_model() -> str:
    """Ollama model for Alexa turns (David, 2026-10-08): the inner-thought model, so
    the inner thought and the reply share one loaded model — no 12B↔14B swap, which
    cost ~20–30 s a turn. eLo's main model (ELO_OLLAMA_MODEL) stays for everything
    else ("eLo isn't a simple chat model"). Override with ALEXA_OLLAMA_MODEL."""
    return (os.environ.get("ALEXA_OLLAMA_MODEL")
            or os.environ.get("ELO_INNER_THOUGHT_MODEL")
            or "mistral-nemo:12b")      # runtime/inner_thought_first.py default


# ── 2b · eLo's own voice on the Echo (ElevenLabs → SSML <audio>) ───────────────
# Alexa plays an <audio> clip only from a public HTTPS URL, as MP3 48 kbps at
# 16/22.05/24 kHz. The clip is made with eLo's ElevenLabs voice (the same call
# voice/voice_engine.py makes), converted with ffmpeg, kept in memory under an
# unguessable token for 10 min, and served by this listener at
# /alexa/audio/<token>.mp3 through the same tunnel. Any failure, or not enough
# of Alexa's 8 s left → Alexa's own voice reads the text (never silence).
# ALEXA_VOICE=off turns it off.

import secrets as _secrets
import subprocess as _subprocess

_VOICE_DEADLINE_S = 7.3     # whole reply incl. TTS must land inside Alexa's 8 s
_AUDIO_TTL_S = 600
_audio: dict[str, tuple[float, bytes]] = {}
_audio_lock = threading.Lock()
_TOKEN_RE = re.compile(r"^/alexa/audio/([0-9a-f]{32})\.mp3$")


def _voice_on() -> bool:
    return os.environ.get("ALEXA_VOICE", "elevenlabs").lower() != "off" \
        and bool(os.environ.get("ELEVENLABS_API_KEY")) and bool(os.environ.get("ELEVENLABS_VOICE_ID"))


def _alexa_mp3(text: str) -> bytes | None:
    """eLo's ElevenLabs voice for text, re-encoded for Alexa. None on any failure."""
    from voice.voice_engine import _fetch_elevenlabs_audio, _clean_for_tts
    raw = _fetch_elevenlabs_audio(_clean_for_tts(text))
    if not raw:
        return None
    out = _subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
                           "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "48k", "-ar", "24000",
                           "-f", "mp3", "pipe:1"], input=raw, capture_output=True, timeout=4)
    return out.stdout if out.returncode == 0 and out.stdout else None


def _store(mp3: bytes) -> str:
    tok = _secrets.token_hex(16)
    now = time.time()
    with _audio_lock:
        for k in [k for k, (ts, _) in _audio.items() if now - ts > _AUDIO_TTL_S]:
            _audio.pop(k, None)
        _audio[tok] = (now, mp3)
    return tok


def audio_clip(path: str) -> bytes | None:
    m = _TOKEN_RE.match(path or "")
    if not m:
        return None
    with _audio_lock:
        hit = _audio.get(m.group(1))
    return hit[1] if hit and time.time() - hit[0] <= _AUDIO_TTL_S else None


def _voiced(text: str, base: str | None, t0: float) -> dict | None:
    """SSML outputSpeech in eLo's voice, or None (caller falls back to text)."""
    if not base or not _voice_on():
        return None
    left = _VOICE_DEADLINE_S - (time.monotonic() - t0)
    if left < 1.5:
        return None
    box: dict = {}
    th = threading.Thread(target=lambda: box.setdefault("mp3", _alexa_mp3(text)), daemon=True)
    th.start()
    th.join(left)
    mp3 = box.get("mp3")
    if not mp3:
        print(f"[alexa] voice: fell back to Alexa's voice ({'timeout' if th.is_alive() else 'no audio'})", flush=True)
        return None
    url = f"{base}/alexa/audio/{_store(mp3)}.mp3"
    return {"type": "SSML", "ssml": f'<speak><audio src="{url}"/></speak>'}


# ── 3 · Alexa request → Alexa response ────────────────────────────────────────

def _speech(text: str, end: bool = False, elo: bool = False,
            base: str | None = None, t0: float | None = None) -> dict:
    """elo=True: brain text, in eLo's voice when possible. elo=False: Alexa system prompt."""
    out = _voiced(text, base, t0 if t0 is not None else time.monotonic()) if elo else None
    resp: dict = {"outputSpeech": out or {"type": "PlainText", "text": text[:7900]}, "shouldEndSession": end}
    print(f"[alexa] → {'eLo' if elo else 'Alexa system'}"
          f"{' (eLo voice)' if out else ''}: {text[:100]!r}", flush=True)
    return {"version": "1.0", "response": resp}


def _brain(utterance: str, turn_fn, base, t0) -> dict:
    reply, from_brain = talk(utterance, turn_fn)
    return _speech(reply, elo=from_brain, base=base, t0=t0)


def handle(req: dict, turn_fn, base: str | None = None) -> dict:
    """base = public https origin of the tunnel (eLo's voice); None → Alexa's voice."""
    t0 = time.monotonic()
    r = req.get("request") or {}
    kind = r.get("type", "")
    if kind == "LaunchRequest":
        print(f"[alexa] opened → brain: {OPEN_UTTERANCE!r}", flush=True)
        return _brain(OPEN_UTTERANCE, turn_fn, base, t0)
    if kind == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}
    if kind != "IntentRequest":
        return _speech(SYS_MISSED)
    intent = (r.get("intent") or {})
    name = intent.get("name", "")
    utterance = (((intent.get("slots") or {}).get("utterance") or {}).get("value") or "").strip()
    print(f"[alexa] intent={name} heard={utterance!r}", flush=True)
    if name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
        return {"version": "1.0", "response": {"shouldEndSession": True}}   # ends quietly
    if name == "AMAZON.HelpIntent":
        return _speech(SYS_HELP)
    if name == "TalkIntent" and utterance:
        return _brain(utterance, turn_fn, base, t0)
    return _speech(SYS_MISSED)          # FallbackIntent / no words: eLo heard nothing


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
            host = (self.headers.get("Host") or "").strip()
            base = f"https://{host}" if re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", host) else None
            self._send(200, handle(req, turn_fn, base=base))

        def do_GET(self):
            clip = audio_clip(self.path)
            if clip is None:
                self._send(404, {"error": "not found"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(clip)))
            self.end_headers()
            self.wfile.write(clip)

    srv = ThreadingHTTPServer(("127.0.0.1", port), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[alexa] ingress listening on 127.0.0.1:{port}/alexa", flush=True)
    return srv
