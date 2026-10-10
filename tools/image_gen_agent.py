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


# Reasons collected during the current generate() call. DREAM-1: the
# caller must be able to say WHY, not just that everything failed.
_LAST_ERRORS: list[str] = []


def _output_path(filename: str | None = None) -> Path:
    """
    Where the next image lands.

    `filename` lets the caller name the file — the dream pipeline needs
    `dream_<dream_id>_scene_<N>.png` (WO-DREAM-ENGINE-001 PHASE 5b).

    Without it the name is a second-resolution timestamp, which collides:
    a 14-scene dream generates well inside one second and every scene
    overwrote the last. Kept for callers that pass nothing, now with a
    uniqueness suffix so it cannot silently clobber.
    """
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filename:
        safe = "".join(c for c in filename if c.isalnum() or c in "-_.") or "image"
        if not safe.endswith(".png"):
            safe += ".png"
        return _OUTPUT_DIR / safe

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    candidate = _OUTPUT_DIR / f"{stamp}.png"
    n = 1
    while candidate.exists():
        candidate = _OUTPUT_DIR / f"{stamp}_{n}.png"
        n += 1
    return candidate


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


# ── OpenAI image call ─────────────────────────────────────────────────────────
#
# eLo has dreamt 166 times and produced zero pictures. Three dreams reached the
# image stage; every scene failed, and the live journal records why:
#
#   DALL-E 3: Error code: 400 - {'error': {'message': "Unknown parameter:
#   'response_format'.", 'type': 'invalid_request_error', ...}}       x6
#   DALL-E 3: No module named 'openai'                                 x4
#
# The second is fixed — openai 3.19.2 is installed. The first is live: newer
# image endpoints reject response_format outright, and the parameter was sent
# unconditionally, so both DALL-E paths 400'd and the chain fell through to a
# local Stable Diffusion that is not running (connection refused). Every route
# failed for a different reason and the dream recorded no art.
#
# Sent first, because older SDKs need it, then dropped and retried when the API
# says it does not know it. Without response_format the response carries a URL
# instead of base64, so both shapes are read.

def _openai_image_bytes(client, model: str, prompt: str, **extra) -> bytes:
    """Generate one image and return its PNG bytes. Raises on failure."""
    kwargs = dict(model=model, prompt=prompt, n=1, size="1024x1024", **extra)
    try:
        resp = client.images.generate(response_format="b64_json", **kwargs)
    except Exception as e:
        if "response_format" not in str(e):
            raise
        resp = client.images.generate(**kwargs)

    item = resp.data[0]

    b64 = getattr(item, "b64_json", None)
    if b64:
        return base64.b64decode(b64)

    url = getattr(item, "url", None)
    if not url:
        raise RuntimeError("image response carried neither b64_json nor url")
    import urllib.request
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


# ── DALL-E 3 ──────────────────────────────────────────────────────────────────

def _dalle3(prompt: str, filename: str | None = None) -> Optional[Path]:
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        out = _output_path(filename)
        # gpt-image-1 is the current model name (formerly dall-e-3, deprecated 2025).
        # Falls back to dall-e-3 in case of model-not-found to support older API keys.
        try:
            out.write_bytes(
                _openai_image_bytes(client, "gpt-image-1", prompt, quality="hd")
            )
        except Exception as _e1:
            if "does not exist" in str(_e1) or "model_not_found" in str(_e1):
                out.write_bytes(
                    _openai_image_bytes(client, "dall-e-3", prompt, quality="hd")
                )
            else:
                raise
        return out
    except Exception as e:
        import logging as _ig_log
        _ig_log.getLogger("elo.image_gen").debug("[image_gen] DALL-E failed: %s", e)
        _LAST_ERRORS.append(f"DALL-E: {e}")
        return None


# ── DALL-E 2 ──────────────────────────────────────────────────────────────────

def _dalle2(prompt: str, filename: str | None = None) -> Optional[Path]:
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        out = _output_path(filename)
        out.write_bytes(_openai_image_bytes(client, "dall-e-2", prompt))
        return out
    except Exception as e:
        print(f"[image_gen] DALL-E 2 failed: {e}")
        _LAST_ERRORS.append(f"DALL-E 2: {e}")
        return None


# ── Stable Diffusion local (A1111 / ComfyUI) ─────────────────────────────────

def _sd_local(prompt: str, filename: str | None = None) -> Optional[Path]:
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
        out = _output_path(filename)
        out.write_bytes(base64.b64decode(img_b64))
        return out
    except Exception as e:
        print(f"[image_gen] SD local failed: {e}")
        _LAST_ERRORS.append(f"SD local: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def generate(
    prompt: str,
    *,
    filename: str | None = None,
    preview: bool = True,
    write_hud: bool = True,
) -> dict:
    """
    Generate an image from prompt. Returns:
        {"ok": True,  "path": "/abs/path.png", "source": "dalle3"|"dalle2"|"sd_local"}
        {"ok": False, "error": "...", "errors": [per-backend reasons]}

    filename  — name the output. The dream pipeline passes
                dream_<dream_id>_scene_<N>.png (PHASE 5b).
    preview   — open the image in Preview.app. Defaults True for a single
                ad-hoc image; the dream pipeline passes False, because a
                14-scene dream would otherwise open 14 Preview windows on
                David's desktop in the middle of the night.
    write_hud — patch hud_image into blender_state.json.

    DREAM-1: on failure the real per-backend reasons come back in `errors`.
    The previous generic "All image generation backends failed." told the
    caller nothing, so the dream path had nothing to log.
    """
    _LAST_ERRORS.clear()

    for fn, label in [(_dalle3, "dalle3"), (_dalle2, "dalle2"), (_sd_local, "sd_local")]:
        path = fn(prompt, filename)
        if path and path.exists():
            if preview:
                _open_preview(path)
            if write_hud:
                _write_hud(path)
            return {"ok": True, "path": str(path), "source": label}

    reasons = list(_LAST_ERRORS)
    return {
        "ok": False,
        "error": "; ".join(reasons) if reasons else "All image generation backends failed.",
        "errors": reasons,
    }


def generate_dream_scene(
    prompt: str,
    *,
    dream_id: str,
    scene_index: int,
    intensity: float = 0.5,
    emotion_vector: "dict | None" = None,
) -> dict:
    """
    WO-DREAM-006 §5b — Generate one dream scene image and apply FX pipeline.

    Saves as dream_<dream_id>_scene_<N>.png.
    Applies CompositionDesigner FX (blob_tracking, datamosh, VCR, summagator)
    scaled by dream intensity and emotion vector.

    Returns:
        {"ok": True, "path": str, "source": str}
        {"ok": False, "error": str}
    """
    filename = f"dream_{dream_id}_scene_{scene_index:02d}.png"
    result = generate(prompt, filename=filename, preview=False, write_hud=False)

    if not result.get("ok"):
        import logging
        logging.getLogger(__name__).warning(
            "[dream] image generation failed: %s", result.get("error", "unknown")
        )
        return result

    # Apply FX pipeline
    try:
        from PIL import Image as _PIL_Image
        from tools.dream_fx import apply_fx
        path = result["path"]
        img = _PIL_Image.open(path).convert("RGBA")
        img = apply_fx(img, intensity, emotion_vector or {})
        img.convert("RGB").save(path, "PNG")
    except Exception as fx_err:
        import logging
        logging.getLogger(__name__).warning(
            "[dream] FX pipeline failed (image still saved): %s", fx_err
        )

    return result
