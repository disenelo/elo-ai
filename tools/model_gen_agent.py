"""
tools/model_gen_agent.py — 3D model generation for eLo OS.

Fallback chain:
    1. Hyper3D / Rodin  (RODIN_API_KEY in .env — async poll)
    2. Meshy            (MESHY_API_KEY in .env — async poll)
    3. Tripo3D          (TRIPO_API_KEY in .env — async poll)
    4. Shap-E           (local — requires shap-e pip install + torch)

Output: ~/Desktop/eLo Generated/models/<timestamp>.glb
        opened in Quick Look + hud_model written to blender_state.json
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional

_OUTPUT_DIR  = Path.home() / "Desktop" / "eLo Generated" / "models"
_POLL_EVERY  = 3      # seconds between status polls
_POLL_MAX    = 120    # max seconds to wait per backend


def _output_path(ext: str = "glb") -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return _OUTPUT_DIR / f"{stamp}.{ext}"


def _open_quicklook(path: Path) -> None:
    try:
        subprocess.Popen(["qlmanage", "-p", str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            subprocess.Popen(["open", str(path)])
        except Exception:
            pass


def _write_hud(path: Path) -> None:
    try:
        from blender_bridge.state_writer import patch as _patch
        _patch({"hud_model": str(path)})
    except Exception:
        pass


def _http_json(url: str, payload: dict | None = None,
               headers: dict | None = None, method: str | None = None) -> dict:
    body = json.dumps(payload).encode() if payload else None
    req  = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method or ("POST" if body else "GET"),
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── Hyper3D / Rodin ────────────────────────────────────────────────────────────

def _hyper3d(prompt: str) -> Optional[Path]:
    api_key = os.environ.get("RODIN_API_KEY") or os.environ.get("HYPER3D_API_KEY")
    if not api_key:
        print("[model_gen] Hyper3D: no RODIN_API_KEY/HYPER3D_API_KEY")
        return None
    try:
        # Submit job
        resp = _http_json(
            "https://hyperhuman.deemos.com/api/v2/rodin",
            payload={"prompt": prompt, "condition_mode": "concat",
                     "geometry_file_format": "glb", "quality": "high"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        job_id = resp.get("uuid") or resp.get("job_uuid") or resp.get("job_id")
        if not job_id:
            print(f"[model_gen] Hyper3D: unexpected response {resp}")
            return None

        # Poll
        deadline = time.time() + _POLL_MAX
        while time.time() < deadline:
            time.sleep(_POLL_EVERY)
            status = _http_json(
                f"https://hyperhuman.deemos.com/api/v2/status/{job_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            state = status.get("status", "").lower()
            if state in ("done", "succeeded", "completed"):
                glb_url = (status.get("jobs") or [{}])[0].get("model_url") or status.get("model_url")
                if glb_url:
                    out = _output_path("glb")
                    urllib.request.urlretrieve(glb_url, out)
                    return out
                break
            if state in ("failed", "error"):
                print(f"[model_gen] Hyper3D job failed: {status}")
                return None
        print("[model_gen] Hyper3D: timed out")
        return None
    except Exception as e:
        print(f"[model_gen] Hyper3D error: {e}")
        return None


# ── Meshy ──────────────────────────────────────────────────────────────────────

def _meshy(prompt: str) -> Optional[Path]:
    api_key = os.environ.get("MESHY_API_KEY")
    if not api_key:
        print("[model_gen] Meshy: no MESHY_API_KEY")
        return None
    try:
        # Submit
        resp = _http_json(
            "https://api.meshy.ai/v2/text-to-3d",
            payload={"mode": "preview", "prompt": prompt,
                     "art_style": "realistic", "negative_prompt": "low quality"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        task_id = resp.get("result")
        if not task_id:
            print(f"[model_gen] Meshy: unexpected response {resp}")
            return None

        # Poll
        deadline = time.time() + _POLL_MAX
        while time.time() < deadline:
            time.sleep(_POLL_EVERY)
            status = _http_json(
                f"https://api.meshy.ai/v2/text-to-3d/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            state = status.get("status", "").lower()
            if state == "succeeded":
                glb_url = (status.get("model_urls") or {}).get("glb")
                if glb_url:
                    out = _output_path("glb")
                    urllib.request.urlretrieve(glb_url, out)
                    return out
                break
            if state == "failed":
                print(f"[model_gen] Meshy job failed: {status}")
                return None
        print("[model_gen] Meshy: timed out")
        return None
    except Exception as e:
        print(f"[model_gen] Meshy error: {e}")
        return None


# ── Tripo3D ────────────────────────────────────────────────────────────────────

def _tripo(prompt: str) -> Optional[Path]:
    api_key = os.environ.get("TRIPO_API_KEY")
    if not api_key:
        print("[model_gen] Tripo: no TRIPO_API_KEY")
        return None
    try:
        resp = _http_json(
            "https://api.tripo3d.ai/v2/openapi/task",
            payload={"type": "text_to_model", "prompt": prompt},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        task_id = (resp.get("data") or {}).get("task_id")
        if not task_id:
            print(f"[model_gen] Tripo: unexpected response {resp}")
            return None

        deadline = time.time() + _POLL_MAX
        while time.time() < deadline:
            time.sleep(_POLL_EVERY)
            status = _http_json(
                f"https://api.tripo3d.ai/v2/openapi/task/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            state = (status.get("data") or {}).get("status", "").lower()
            if state == "success":
                glb_url = ((status.get("data") or {}).get("output") or {}).get("model")
                if glb_url:
                    out = _output_path("glb")
                    urllib.request.urlretrieve(glb_url, out)
                    return out
                break
            if state in ("failed", "cancelled"):
                print(f"[model_gen] Tripo job failed: {status}")
                return None
        print("[model_gen] Tripo: timed out")
        return None
    except Exception as e:
        print(f"[model_gen] Tripo error: {e}")
        return None


# ── Shap-E (local) ────────────────────────────────────────────────────────────

def _shape_e(prompt: str) -> Optional[Path]:
    try:
        import torch
        from shap_e.diffusion.sample import sample_latents
        from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
        from shap_e.models.download import load_model, load_config
        from shap_e.util.notebooks import decode_latent_mesh

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        xm      = load_model("transmitter", device=device)
        model   = load_model("text300M", device=device)
        diffusion = diffusion_from_config(load_config("diffusion"))

        latents = sample_latents(
            batch_size=1, model=model, diffusion=diffusion,
            guidance_scale=15.0, model_kwargs={"texts": [prompt]},
            progress=True, clip_denoised=True, use_fp16=True, use_karras=True,
            karras_steps=64, sigma_min=1e-3, sigma_max=160, s_churn=0,
        )
        out = _output_path("obj")
        with open(out, "w") as f:
            decode_latent_mesh(xm, latents[0]).tri_mesh().write_obj(f)
        return out
    except ImportError:
        print("[model_gen] Shap-E: not installed (pip install shap-e)")
        return None
    except Exception as e:
        print(f"[model_gen] Shap-E error: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def generate(prompt: str) -> dict:
    """
    Generate a 3D model from prompt. Returns:
        {"ok": True,  "path": "/abs/path.glb", "source": "hyper3d"|"meshy"|"tripo"|"shape_e"}
        {"ok": False, "error": "..."}
    """
    for fn, label in [
        (_hyper3d, "hyper3d"),
        (_meshy,   "meshy"),
        (_tripo,   "tripo"),
        (_shape_e, "shape_e"),
    ]:
        path = fn(prompt)
        if path and path.exists():
            _open_quicklook(path)
            _write_hud(path)
            return {"ok": True, "path": str(path), "source": label}

    return {"ok": False, "error": "All 3D model generation backends failed."}
