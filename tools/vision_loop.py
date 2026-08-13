"""
tools/vision_loop.py — Background vision loop for eLo OS.

Runs every 2s (backs off to 6s when nothing is happening).
Asks the vision model for structured attention data and writes
blender_state.json["vision"] so Unity eLo can react.

Output block:
    {
        "active":    bool,          # something worth observing on screen
        "attention": float 0–1,     # how intently → scales observe/dwell/tilt
        "focus":     {"x": float, "y": float},  # viewport 0–1, mouse-position proxy
        "app":       str            # frontmost app name
    }

Start from server.py:
    from tools import vision_loop; vision_loop.start()
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import tempfile
import threading
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# All blender_state.json writes go through the coordinator — never direct file writes.
from blender_bridge.state_writer import patch as _patch_state

_FAST_INTERVAL = 2.0   # seconds when attention is meaningful
_SLOW_INTERVAL = 6.0   # back-off when attention stays low
_LOW_THRESHOLD = 0.1   # attention value considered "nothing happening"
_SLOW_AFTER    = 3     # consecutive low-attention reads before back-off

_stop_event: threading.Event  = threading.Event()
_thread: threading.Thread | None = None

_QUOTA_BACKOFF = 60.0   # seconds to pause an API after a 429
_quota_until: dict[str, float] = {"gemini": 0.0, "openai": 0.0}

_VISION_PROMPT = (
    "You are eLo's peripheral vision. Analyse the screenshot.\n"
    "Return JSON only — no prose, no markdown, no explanation:\n"
    '{"active": <bool>, "attention": <0.0-1.0>, "app": "<frontmost app name>", "description": "<5 words max>"}\n\n'
    "active=true  → something worth eLo noticing: code being written, art, video, motion, bright content\n"
    "active=false → idle desktop, black screen, screensaver, nothing happening\n"
    "attention    → 0.0 resting, 1.0 fully drawn in (creative work, fast motion, etc.)\n"
    "app          → macOS frontmost application, e.g. \"Blender\", \"VS Code\", \"Safari\", \"Spotify\"\n"
    "description  → 5 words max describing the primary activity visible, e.g. \"rigging robot arm mesh\", \"writing journal entry\", \"browsing GitHub issues\""
)


# ── screenshot ────────────────────────────────────────────────────────────────

def _has_screen_permission() -> bool:
    """Check Screen Recording permission without triggering the macOS prompt."""
    try:
        from Quartz import CGPreflightScreenCaptureAccess
        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        return False  # Quartz unavailable — don't call screencapture; install pyobjc-framework-Quartz


def _screenshot() -> bytes | None:
    # Guard: don't call screencapture if Screen Recording isn't granted.
    # CGPreflightScreenCaptureAccess checks silently — no prompt.
    if not _has_screen_permission():
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        subprocess.run(
            ["screencapture", "-x", "-t", "png", path],
            check=True, timeout=5.0, capture_output=True,
        )
        with open(path, "rb") as f:
            data = f.read()
        os.unlink(path)
        return data
    except Exception:
        return None


# ── mouse position → viewport focus ──────────────────────────────────────────

def _mouse_focus() -> dict:
    """Return {x, y} in viewport 0–1 (top-left origin). Falls back to {0.5, 0.5}."""
    try:
        from Quartz import CGEventCreate, CGEventGetLocation, kCGEventNull
        from AppKit import NSScreen
        loc    = CGEventGetLocation(CGEventCreate(None))
        frame  = NSScreen.mainScreen().frame()
        x = loc.x / frame.size.width
        y = 1.0 - (loc.y / frame.size.height)  # AppKit origin is bottom-left
        return {"x": round(max(0.0, min(1.0, x)), 3),
                "y": round(max(0.0, min(1.0, y)), 3)}
    except Exception:
        return {"x": 0.5, "y": 0.5}


# ── vision model call ─────────────────────────────────────────────────────────

def _analyse(image_bytes: bytes) -> dict | None:
    """Call Gemini or OpenAI with the structured prompt. Returns parsed dict or None."""
    now = time.time()
    b64 = base64.b64encode(image_bytes).decode()

    # Gemini first
    gkey = os.environ.get("GOOGLE_API_KEY", "")
    if gkey and now >= _quota_until["gemini"]:
        result = _call_gemini(gkey, b64)
        if result is not None:
            return result

    # OpenAI fallback
    okey = os.environ.get("OPENAI_API_KEY", "")
    if okey and now >= _quota_until["openai"]:
        result = _call_openai(okey, b64)
        if result is not None:
            return result

    return None


def _parse_json_response(text: str) -> dict | None:
    """Extract the first JSON object from model output."""
    m = re.search(r'\{[^{}]+\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return {
            "active":      bool(data.get("active", False)),
            "attention":   float(max(0.0, min(1.0, data.get("attention", 0.0)))),
            "app":         str(data.get("app", "")),
            "description": str(data.get("description", "")),
        }
    except Exception:
        return None


def _call_gemini(gkey: str, b64: str) -> dict | None:
    try:
        import httpx
        model = os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
        url   = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body  = {
            "contents": [{"parts": [
                {"text": _VISION_PROMPT},
                {"inline_data": {"mime_type": "image/png", "data": b64}},
            ]}],
            "generationConfig": {"maxOutputTokens": 80, "temperature": 0.1},
        }
        resp = httpx.post(f"{url}?key={gkey}", json=body, timeout=15.0)
        if resp.status_code == 200:
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_json_response(text)
        if resp.status_code == 429:
            _quota_until["gemini"] = time.time() + _QUOTA_BACKOFF
            print(f"[eLo vision] Gemini quota hit — backing off {_QUOTA_BACKOFF}s")
        return None
    except Exception:
        return None


def _call_openai(okey: str, b64: str) -> dict | None:
    try:
        import httpx
        model = os.environ.get("ELO_OPENAI_MODEL", "gpt-4o-mini")
        body  = {
            "model": model,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": _VISION_PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"}},
            ]}],
            "max_tokens": 80,
            "temperature": 0.1,
        }
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {okey}", "Content-Type": "application/json"},
            timeout=15.0,
        )
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"]
            return _parse_json_response(text)
        if resp.status_code == 429:
            _quota_until["openai"] = time.time() + _QUOTA_BACKOFF
            print(f"[eLo vision] OpenAI quota hit — backing off {_QUOTA_BACKOFF}s")
        return None
    except Exception:
        return None


# ── state write ───────────────────────────────────────────────────────────────

def _write_vision(active: bool, attention: float, focus: dict, app: str, description: str = "") -> None:
    _patch_state({"vision": {
        "active":      active,
        "attention":   round(attention, 3),
        "focus":       focus,
        "app":         app,
        "description": description,
    }})


# ── background loop ───────────────────────────────────────────────────────────

def _any_api_ready() -> bool:
    """Return True only if at least one vision API has a key AND is not in quota back-off."""
    now = time.time()
    gemini_ok = bool(os.environ.get("GOOGLE_API_KEY", "")) and now >= _quota_until["gemini"]
    openai_ok = bool(os.environ.get("OPENAI_API_KEY", "")) and now >= _quota_until["openai"]
    return gemini_ok or openai_ok


def _loop() -> None:
    low_count = 0

    while not _stop_event.is_set():
        # Only capture the screen when an API is actually ready to process it.
        # Screencapture triggers the macOS Screen Recording permission prompt even
        # when the result is immediately thrown away — don't capture for nothing.
        if _any_api_ready():
            img = _screenshot()
            if img:
                result = _analyse(img)
                if result:
                    focus = _mouse_focus()
                    _write_vision(
                        active=result["active"],
                        attention=result["attention"],
                        focus=focus,
                        app=result["app"],
                        description=result.get("description", ""),
                    )
                    if result["attention"] < _LOW_THRESHOLD:
                        low_count += 1
                    else:
                        low_count = 0
            else:
                # Screenshot failed (permission revoked, blank frame, etc.) — clear active
                # so the status reflects reality rather than holding the last successful state.
                _write_vision(active=False, attention=0.0,
                              focus={"x": 0.5, "y": 0.5}, app="")

        interval = _SLOW_INTERVAL if low_count >= _SLOW_AFTER else _FAST_INTERVAL
        _stop_event.wait(interval)


# ── public API ────────────────────────────────────────────────────────────────

def is_available() -> bool:
    return bool(
        os.environ.get("GOOGLE_API_KEY", "") or
        os.environ.get("OPENAI_API_KEY", "")
    )


def start() -> None:
    """Start the background vision loop. Safe to call multiple times."""
    global _thread
    if _thread and _thread.is_alive():
        return
    if not is_available():
        print("[eLo vision loop] no vision API key — set GOOGLE_API_KEY or OPENAI_API_KEY")
        return
    _stop_event.clear()
    _write_vision(active=False, attention=0.0, focus={"x": 0.5, "y": 0.5}, app="")
    _thread = threading.Thread(target=_loop, daemon=True, name="vision-loop")
    _thread.start()
    print("[eLo vision loop] started")


def stop() -> None:
    _stop_event.set()
