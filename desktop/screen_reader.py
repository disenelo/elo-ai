"""
desktop/screen_reader.py — Screen text extraction via Claude vision.

Not a visual description — a read. Captures the screen silently, passes it
to Claude vision with a text-extraction prompt, and returns structured content:
what's open, what text is visible, what topics are present.

eLo uses this when it needs to understand what David is actually looking at —
beyond just the window title. On-demand only, never continuous polling.

Requires: ANTHROPIC_API_KEY in .env
"""
from __future__ import annotations

import base64
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

_ANTHROPIC_KEY = lambda: os.environ.get("ANTHROPIC_API_KEY", "")
_GOOGLE_KEY    = lambda: os.environ.get("GOOGLE_API_KEY", "")

# Rate limit — minimum seconds between captures to avoid hammering
_LAST_CAPTURE: float = 0
_MIN_INTERVAL: float = 30.0

_TMP_DIR = tempfile.gettempdir()


@dataclass
class ScreenContent:
    raw_text:   str          # all readable text extracted from screen
    topics:     list[str]    # key topics/concepts identified
    app:        str          # active app at capture time
    summary:    str          # one-sentence summary of what's on screen
    captured_at: float = 0.0


def capture() -> Optional[str]:
    """
    Take a silent screenshot and return the path. Returns None on failure.
    Uses -x flag (no sound) and captures the main display only.
    """
    path = os.path.join(_TMP_DIR, f"elo_screen_{int(time.time())}.png")
    try:
        result = subprocess.run(
            ["screencapture", "-x", "-t", "png", path],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0 and os.path.exists(path):
            return path
    except Exception:
        pass
    return None


def _encode(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _cleanup(path: str) -> None:
    try:
        os.unlink(path)
    except Exception:
        pass


def read(force: bool = False) -> Optional[ScreenContent]:
    """
    Capture the screen and extract text content via Claude vision.

    Args:
        force — bypass rate limit (use sparingly)

    Returns:
        ScreenContent or None if rate-limited, capture failed, or API unavailable.
    """
    global _LAST_CAPTURE

    if not force and (time.time() - _LAST_CAPTURE) < _MIN_INTERVAL:
        return None

    # Prefer Anthropic if keyed, fall back to Gemini (already in .env)
    anthropic_key = _ANTHROPIC_KEY()
    google_key    = _GOOGLE_KEY()
    if not anthropic_key and not google_key:
        return None

    path = capture()
    if not path:
        return None

    _LAST_CAPTURE = time.time()

    system_prompt = (
        "You extract readable text from screen captures. "
        "Return only a JSON object — no other text. Format:\n"
        '{"raw_text": "all visible readable text", '
        '"topics": ["keyword1", "keyword2"], '
        '"app": "name of active application if visible", '
        '"summary": "one sentence: what is this person working on right now"}'
        "\n\nRules:\n"
        "- raw_text: extract actual words visible on screen — code, UI labels, document text, URLs\n"
        "- topics: 3-8 concrete keywords, no stopwords\n"
        "- app: if you can see the app name or UI chrome, name it\n"
        "- summary: plain language, what is visible, not what you think they're doing"
    )

    try:
        import httpx, json, re
        encoded = _encode(path)
        _cleanup(path)

        raw_text = ""

        if anthropic_key:
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 600,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": encoded}},
                    ]}],
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            raw_text = resp.json()["content"][0]["text"].strip()

        elif google_key:
            resp = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_key}",
                json={
                    "contents": [{"parts": [
                        {"text": system_prompt},
                        {"inline_data": {"mime_type": "image/png", "data": encoded}},
                    ]}],
                    "generationConfig": {"maxOutputTokens": 600},
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        raw_text = re.sub(r"^```\w*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        data = json.loads(raw_text)

        return ScreenContent(
            raw_text=data.get("raw_text", ""),
            topics=data.get("topics", []),
            app=data.get("app", ""),
            summary=data.get("summary", ""),
            captured_at=_LAST_CAPTURE,
        )

    except Exception as e:
        import sys
        print(f"[screen_reader] error: {e}", file=sys.stderr)
        _cleanup(path)
        return None


def as_signal_text(content: ScreenContent) -> str:
    """Return a compact text representation for injection into synthesis observer."""
    parts = []
    if content.summary:
        parts.append(content.summary)
    if content.topics:
        parts.append("Topics: " + ", ".join(content.topics))
    if content.raw_text:
        parts.append(content.raw_text[:300])
    return "\n".join(parts)
