"""
self_improvement/finetune/adapter.py — WO-104 versioned adapter registry.

An "adapter" here is a directory under Output/finetune_adapters/ containing:
    manifest.json      — {version, created_at, base_model, source_rows,
                          row_count_style, training_config, hash, status}
    training_set.jsonl — the exact style rows used (audit trail)
    weights/           — actual LoRA weights when MLX is available; empty
                         directory when this is a pipeline-proof run

Safety mechanism (card requirement, non-negotiable):
    - never overwrite the base model
    - deleting the adapter directory instantly reverts to baseline behaviour
    - `active` symlink points at the adapter currently served; removing it
      reverts to baseline. `deactivate()` removes the symlink only.

Adapter status:
    'pipeline_proof' → structure created, no real weights (MLX unavailable
                       or row count too low). Not servable.
    'trained'        → real weights present, eval not yet run.
    'gated'          → real weights present, eval passed.
    'rejected'       → eval failed. Kept for audit; will not be served.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from typing import Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ADAPTER_ROOT = os.environ.get(
    "ELO_ADAPTER_ROOT",
    os.path.join(_ROOT, "Output", "finetune_adapters"),
)
ACTIVE_LINK = os.path.join(ADAPTER_ROOT, "active")


def _sha256_of_rows(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def new_version_tag(base_model: str, prefix: str = "elo-style") -> str:
    ts = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return f"{prefix}-{base_model.replace(':', '_')}-{ts}"


def create_adapter(
    version: str,
    base_model: str,
    style_rows: list[dict],
    training_config: dict,
    status: str = "pipeline_proof",
    weights_bytes: Optional[bytes] = None,
) -> str:
    """
    Materialise a versioned adapter directory. Returns the adapter path.
    weights_bytes is written to weights/adapter.safetensors when supplied;
    otherwise weights/ is left empty and status defaults to 'pipeline_proof'.
    """
    os.makedirs(ADAPTER_ROOT, exist_ok=True)
    adir = os.path.join(ADAPTER_ROOT, version)
    os.makedirs(adir, exist_ok=True)
    os.makedirs(os.path.join(adir, "weights"), exist_ok=True)

    with open(os.path.join(adir, "training_set.jsonl"), "w", encoding="utf-8") as f:
        for r in style_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if weights_bytes is not None:
        with open(os.path.join(adir, "weights", "adapter.safetensors"), "wb") as f:
            f.write(weights_bytes)

    manifest = {
        "version":          version,
        "created_at":       time.time(),
        "base_model":       base_model,
        "row_count_style":  len(style_rows),
        "training_config":  training_config,
        "source_hash":      _sha256_of_rows(style_rows),
        "status":           status,
        "has_weights":      weights_bytes is not None,
    }
    with open(os.path.join(adir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return adir


def read_manifest(version: str) -> dict:
    with open(os.path.join(ADAPTER_ROOT, version, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def update_status(version: str, status: str, eval_report: Optional[dict] = None) -> dict:
    m = read_manifest(version)
    m["status"] = status
    m["status_updated_at"] = time.time()
    if eval_report is not None:
        m["eval_report"] = eval_report
    with open(os.path.join(ADAPTER_ROOT, version, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    return m


def list_adapters() -> list[dict]:
    if not os.path.exists(ADAPTER_ROOT):
        return []
    out = []
    for name in sorted(os.listdir(ADAPTER_ROOT)):
        p = os.path.join(ADAPTER_ROOT, name)
        mf = os.path.join(p, "manifest.json")
        if os.path.isdir(p) and os.path.exists(mf):
            try:
                out.append(read_manifest(name))
            except Exception:
                pass
    return out


def activate(version: str) -> str:
    """Symlink Output/finetune_adapters/active → <version>. Never overwrites weights."""
    m = read_manifest(version)
    if m.get("status") != "gated":
        raise RuntimeError(
            f"refuse to activate adapter {version}: status={m.get('status')}, "
            f"only 'gated' adapters may be served"
        )
    if os.path.islink(ACTIVE_LINK) or os.path.exists(ACTIVE_LINK):
        os.remove(ACTIVE_LINK)
    os.symlink(version, ACTIVE_LINK)
    return ACTIVE_LINK


def deactivate() -> None:
    """Remove the active symlink. Baseline behaviour restored instantly."""
    if os.path.islink(ACTIVE_LINK) or os.path.exists(ACTIVE_LINK):
        os.remove(ACTIVE_LINK)


def active_version() -> Optional[str]:
    if os.path.islink(ACTIVE_LINK):
        return os.readlink(ACTIVE_LINK)
    return None


def delete_adapter(version: str) -> bool:
    """Full revert: remove an adapter directory. Base model is untouched."""
    p = os.path.join(ADAPTER_ROOT, version)
    if not os.path.isdir(p):
        return False
    if active_version() == version:
        deactivate()
    shutil.rmtree(p)
    return True
