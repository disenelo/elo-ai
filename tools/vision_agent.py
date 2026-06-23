"""
tools/vision_agent.py — Screen capture + Gemini Flash visual description.

Takes a screenshot (macOS screencapture), encodes it, sends to Gemini Flash
as a multimodal prompt. GOOGLE_API_KEY must be set in .env.

Returns a one-line summary for the LLM to speak about.
"""
from __future__ import annotations

import base64
import os
import subprocess
import tempfile

_GKEY  = os.environ.get("GOOGLE_API_KEY", "")
_MODEL = os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent"


def _screenshot() -> bytes | None:
    """Capture the screen to a temp PNG and return raw bytes."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        subprocess.run(
            ["screencapture", "-x", "-t", "png", path],
            check=True, timeout=5.0,
        )
        with open(path, "rb") as f:
            data = f.read()
        os.unlink(path)
        return data
    except Exception as e:
        print(f"[eLo vision] screenshot error: {e}")
        return None


def _describe(image_bytes: bytes, question: str) -> str | None:
    if not _GKEY:
        return None
    try:
        import httpx
        b64 = base64.b64encode(image_bytes).decode()
        body = {
            "contents": [{
                "parts": [
                    {"text": f"You are eLo's vision — describe what you see on screen briefly. {question}"},
                    {"inline_data": {"mime_type": "image/png", "data": b64}},
                ]
            }],
            "generationConfig": {"maxOutputTokens": 120, "temperature": 0.3},
        }
        resp = httpx.post(f"{_URL}?key={_GKEY}", json=body, timeout=20.0)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return None
    except Exception as e:
        print(f"[eLo vision] Gemini error: {e}")
        return None


def agent(query: str) -> str:
    """Capture screen and describe it via Gemini Flash."""
    if not _GKEY:
        return "VISION: GOOGLE_API_KEY not set — add it to .env"

    img = _screenshot()
    if not img:
        return "VISION: could not capture screen"

    # Formulate a focused question from the user query
    question = query if len(query) > 10 else "What's on screen right now?"
    description = _describe(img, question)

    if description:
        return f"VISION: {description[:300]}"
    return "VISION: could not analyse screen"
