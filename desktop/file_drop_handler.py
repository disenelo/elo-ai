"""
desktop/file_drop_handler.py — File-drop event reader for eLo OS.

Polls unity_events.json for {"type":"file_drop","path":"...","_ts":...} events
written by EloFileDrop.cs (Unity Presence) and routes by file extension:

    Image (.png / .jpg / .jpeg / .gif / .webp / .bmp)
        → GPT-4o vision analysis → eLo describes it aloud

    PDF (.pdf)
        → text extraction → LLM summary → eLo summarises it

    3D model (.glb / .obj / .fbx / .stl)
        → Quick Look preview + write hud_model path

    Text / Markdown (.txt / .md / .rtf)
        → read + eLo summarises / displays content

    Anything else
        → open with macOS default app

Background thread — started from server.py alongside the Spotify / vision polls.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path

_EVENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "blender", "unity_events.json",
)
_POLL_INTERVAL = 0.5   # seconds
_last_ts: float = 0.0
_last_seq: int = -1   # seq cursor; -1 = nothing consumed yet
_lock = threading.Lock()
# Module-level queue — populated by _process(), drained by pop_pending_drops()
# so server.py can inject file drop context into the next turn without a circular import.
_pending_drops: list[dict] = []

# ── Extension sets ────────────────────────────────────────────────────────────

_IMAGE_EXT  = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
_PDF_EXT    = {".pdf"}
_MODEL_EXT  = {".glb", ".obj", ".fbx", ".stl", ".usdz"}
_TEXT_EXT   = {".txt", ".md", ".rtf", ".csv", ".json", ".yaml", ".yml"}


# ── Handlers ──────────────────────────────────────────────────────────────────

def _handle_image(path: Path) -> str:
    try:
        from tools.vision_agent import _describe_openai  # type: ignore
        raw = path.read_bytes()
        result = _describe_openai(raw, "Describe this image concisely — what's in it, key details, mood or style if relevant.")
        return result or "I can see the image but couldn't read it clearly."
    except Exception as e:
        print(f"[file_drop] image analysis error: {e}")
        return "Got the image — couldn't analyse it right now."


def _handle_pdf(path: Path) -> str:
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            pages = pdf.pages[:8]
            text = "\n".join(p.extract_text() or "" for p in pages).strip()
    except ImportError:
        try:
            r = subprocess.run(
                ["pdftotext", str(path), "-"],
                capture_output=True, text=True, timeout=15,
            )
            text = r.stdout.strip()
        except Exception:
            pass

    if not text:
        return f"Dropped {path.name} — couldn't extract text from it."

    snippet = text[:3000]
    try:
        import openai, os as _os
        client = openai.OpenAI(api_key=_os.environ.get("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are eLo. Summarise this document in 2-3 sentences — key topic, main point, and any important detail worth flagging."},
                {"role": "user", "content": snippet},
            ],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[file_drop] PDF summarise error: {e}")
        return f"{path.name} — {len(text.split())} words. Couldn't summarise right now."


def _handle_model(path: Path) -> str:
    try:
        subprocess.Popen(
            ["qlmanage", "-p", str(path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        subprocess.Popen(["open", str(path)])
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch({"hud_model": str(path)})
    except Exception:
        pass
    return f"3D file — opening {path.name} in the viewer."


def _handle_text(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return f"Couldn't read {path.name}."

    if len(content) < 600:
        return f"{path.name}:\n{content}"

    snippet = content[:3000]
    try:
        import openai, os as _os
        client = openai.OpenAI(api_key=_os.environ.get("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Summarise this in 2-3 sentences — main topic and key points."},
                {"role": "user", "content": snippet},
            ],
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return content[:400] + ("…" if len(content) > 400 else "")


def _handle_other(path: Path) -> str:
    try:
        subprocess.Popen(["open", str(path)])
    except Exception:
        pass
    return f"Opened {path.name}."


# ── Router ────────────────────────────────────────────────────────────────────

def _route(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in _IMAGE_EXT:
        return _handle_image(path)
    if ext in _PDF_EXT:
        return _handle_pdf(path)
    if ext in _MODEL_EXT:
        return _handle_model(path)
    if ext in _TEXT_EXT:
        return _handle_text(path)
    return _handle_other(path)


def _process(event: dict) -> None:
    global _pending_drops
    raw_path = event.get("path", "")
    if not raw_path:
        return
    path = Path(raw_path)
    if not path.exists():
        print(f"[file_drop] dropped file not found: {raw_path}")
        return

    print(f"[file_drop] processing: {path.name}")
    response = _route(path)

    # Speak directly — voice engine, no circular import through server.py
    try:
        from voice.voice_engine import speak as _speak
        _speak(response)
    except Exception as _e:
        print(f"[file_drop] speak error: {_e}")

    # Queue for context injection on next turn (drained by pop_pending_drops())
    with _lock:
        _pending_drops = (_pending_drops[-4:] +
                          [{"file": path.name, "summary": response[:300]}])


# ── Poll loop ─────────────────────────────────────────────────────────────────

def _poll_loop() -> None:
    # INT-8 Bug 1: read NDJSON line-by-line; seq cursor; path from payload.path
    global _last_ts, _last_seq
    while True:
        time.sleep(_POLL_INTERVAL)
        try:
            with open(_EVENTS_FILE, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            ev_type = event.get("type", "") or event.get("event", "")
            if ev_type != "file_drop":
                continue
            # Seq-based dedup preferred; ts fallback for events without seq field
            ev_seq = event.get("seq")
            if ev_seq is not None:
                with _lock:
                    if ev_seq <= _last_seq:
                        continue
                    _last_seq = ev_seq
            else:
                ts = float(event.get("_ts") or 0) or os.path.getmtime(_EVENTS_FILE)
                with _lock:
                    if ts <= _last_ts:
                        continue
                    _last_ts = ts
            # Path: payload.path first (append-log schema), fall back to top-level path
            raw_path = (event.get("payload") or {}).get("path") or event.get("path", "")
            if raw_path:
                threading.Thread(
                    target=_process,
                    args=({"path": raw_path},),
                    daemon=True,
                ).start()


def start(interval: float = _POLL_INTERVAL) -> None:
    """Start the background poll thread. Safe to call multiple times — idempotent."""
    global _POLL_INTERVAL
    _POLL_INTERVAL = interval
    t = threading.Thread(target=_poll_loop, daemon=True, name="file_drop_poll")
    t.start()
    print("[file_drop] poll started")


def pop_pending_drops() -> list:
    """
    Drain and return all pending file drop results. Called by server.py each turn
    to inject file drop context into the system prompt. Thread-safe.
    """
    global _pending_drops
    with _lock:
        drops, _pending_drops = list(_pending_drops), []
    return drops
