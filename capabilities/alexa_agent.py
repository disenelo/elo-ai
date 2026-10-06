"""
capabilities/alexa_agent.py — WORLD_ALEXA_SPEAK capability

WO-BA17-ALEXA-001

Two-step voice path:
  Step A — TTS to local system audio via tts_output.speak()
            Controlled by ELO_TTS_BACKEND env var (default: "print")
  Step B — Alexa Proactive Events API notification (silent no-op if creds absent)

Returns {spoken: bool, backend: str, alexa_notified: bool}.
Never journals as a user memory turn.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_ALEXA_SKILL_ID = os.environ.get("ALEXA_SKILL_ID", "")
_ALEXA_ACCESS_TOKEN = os.environ.get("ALEXA_ACCESS_TOKEN", "")
_ALEXA_USER_ID = os.environ.get("ALEXA_USER_ID", "")


def speak(text: str, emotion: str = "neutral") -> dict:
    """
    Speak text through TTS and optionally notify via Alexa.

    Args:
        text:    The text to speak.
        emotion: Emotion hint for TTS voice parameters (maps to tts_output emotion presets).

    Returns:
        {spoken: bool, backend: str, alexa_notified: bool}
    """
    result: dict = {
        "spoken": False,
        "backend": os.environ.get("ELO_TTS_BACKEND", "print"),
        "alexa_notified": False,
    }

    # ── Step A: TTS to local audio ────────────────────────────────────────────
    try:
        from plugins.voice.tts_output import speak as _tts_speak
        emotion_snapshot = {"emotion": emotion} if emotion and emotion != "neutral" else None
        _tts_speak(text, emotion_snapshot=emotion_snapshot)
        result["spoken"] = True
    except Exception as exc:
        logger.error("[alexa_agent] TTS step A failed: %s", exc)
        result["spoken"] = False

    # ── Step B: Alexa Proactive Events (silent if creds absent) ───────────────
    if _ALEXA_SKILL_ID and _ALEXA_ACCESS_TOKEN and _ALEXA_USER_ID:
        result["alexa_notified"] = _notify_alexa(text)
    else:
        logger.debug("[alexa_agent] Alexa creds absent — Step B skipped")

    # B3 result standard (additive — existing keys unchanged).
    result["success"] = bool(result["spoken"])
    result["error"] = None if result["spoken"] else "local TTS failed"
    try:
        from tools.capability_status import record_result
        record_result("alexa_speak", {"success": result["success"], "result": dict(result),
                                      "error": result["error"]})
    except Exception:
        pass
    return result


def _notify_alexa(text: str) -> bool:
    """
    POST a Proactive Event to the Alexa Skill Messaging API.
    Returns True on HTTP 202, False on any error.
    Silent failure — Step A already spoke; Alexa is a bonus surface.
    """
    try:
        import urllib.request
        import urllib.error
        import json

        endpoint = (
            "https://api.amazonalexa.com/v1/proactiveEvents/stages/development"
            if os.environ.get("ALEXA_ENV", "prod") == "dev"
            else "https://api.amazonalexa.com/v1/proactiveEvents"
        )

        payload = json.dumps({
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "referenceId": f"elo-speak-{__import__('time').time_ns()}",
            "expiryTime": __import__("datetime").datetime.utcnow().replace(
                year=__import__("datetime").datetime.utcnow().year + 1
            ).isoformat() + "Z",
            "event": {
                "name": "AMAZON.MessageAlert.Activated",
                "payload": {
                    "messageGroup": {
                        "creator": {"name": "eLo"},
                        "count": 1,
                        "urgency": "URGENT",
                    },
                    "state": {"status": "UNREAD"},
                },
            },
            "localizedAttributes": [
                {"locale": "en-US", "creatorName": "eLo"},
            ],
            "relevantAudience": {
                "type": "Unicast",
                "payload": {"user": _ALEXA_USER_ID},
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {_ALEXA_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "X-Amzn-RequestId": f"elo-{__import__('time').time_ns()}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 202
    except Exception as exc:
        logger.warning("[alexa_agent] Alexa Step B notification failed (non-fatal): %s", exc)
        return False
