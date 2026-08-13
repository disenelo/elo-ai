"""
tools/image_gen_agent.py — Image generation for eLo OS.

Fallback chain:
    1. DALL-E 3 (hd, 1024x1024)
    2. DALL-E 2 (if DALL-E 3 quota / rate-limit)
    3. Stable Diffusion local (http://localhost:7860 — A1111 / ComfyUI)

Output: ~/Desktop/eLo Generated/images/<timestamp>.png
        opened in Preview + hud_image written to blender_state.json
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

_OUTPUT_DIR = Path.home() / "Desktop" / "eLo Generated" / "images"
_SD_URL     = os.environ.get("ELO_SD_URL", "http://localhost:7860")


def _output_path() -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return _OUTPUT_DIR / f"{stamp}.png"


def _open_preview(path: Path) -> None:
    try:
        subprocess.Popen(["open", "-a", "Preview", str(path)])
    except Exception:
        pass


def _write_hud(path: Path) -> None:
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch({"hud_image": str(path)})
    except Exception:
        pass


# ── DALL-E 3 ──────────────────────────────────────────────────────────────────

def _dalle3(prompt: str) -> Optional[Path]:
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        resp = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="hd",
            response_format="b64_json",
        )
        data = resp.data[0].b64_json
        out  = _output_path()
        out.write_bytes(base64.b64decode(data))
        return out
    except Exception as e:
        print(f"[image_gen] DALL-E 3 failed: {e}")
        return None


# ── DALL-E 2 ──────────────────────────────────────────────────────────────────

def _dalle2(prompt: str) -> Optional[Path]:
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        resp = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="b64_json",
        )
        data = resp.data[0].b64_json
        out  = _output_path()
        out.write_bytes(base64.b64decode(data))
        return out
    except Exception as e:
        print(f"[image_gen] DALL-E 2 failed: {e}")
        return None


# ── Stable Diffusion local (A1111 / ComfyUI) ─────────────────────────────────

def _sd_local(prompt: str) -> Optional[Path]:
    try:
        import urllib.request
        payload = json.dumps({
            "prompt":          prompt,
            "negative_prompt": "blurry, low quality, distorted",
            "steps":           25,
            "width":           1024,
            "height":          1024,
            "cfg_scale":       7,
        }).encode()
        req  = urllib.request.Request(
            f"{_SD_URL}/sdapi/v1/txt2img",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read())
        img_b64 = body["images"][0]
        out = _output_path()
        out.write_bytes(base64.b64decode(img_b64))
        return out
    except Exception as e:
        print(f"[image_gen] SD local failed: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def generate(prompt: str) -> dict:
    """
    Generate an image from prompt. Returns:
        {"ok": True,  "path": "/abs/path.png", "source": "dalle3"|"dalle2"|"sd_local"}
        {"ok": False, "error": "..."}
    """
    for fn, label in [(_dalle3, "dalle3"), (_dalle2, "dalle2"), (_sd_local, "sd_local")]:
        path = fn(prompt)
        if path and path.exists():
            _open_preview(path)
            _write_hud(path)
            return {"ok": True, "path": str(path), "source": label}

    return {"ok": False, "error": "All image generation backends failed."}
