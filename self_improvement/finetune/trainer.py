"""
self_improvement/finetune/trainer.py — WO-104 style-only LoRA trainer.

Hard rules (Ruling F + Rule 1 alarm):
    - REFUSES to run if ANY input row lacks a valid `delta_cause`. Not skip. Refuse.
    - EXCLUDES every row tagged `verification`, `l3_override`, `unknown`, or `none`.
    - Only `style` rows are eligible for training.
    - Never overwrites the base model. Produces an adapter file only.

Toolchain [PROPOSAL]:
    On Apple Silicon: MLX LoRA (`mlx_lm.lora`). Optional — probed at runtime.
    If MLX is not installed the trainer still runs end-to-end and produces a
    'pipeline_proof' adapter (manifest + audit trail, no weights). This is
    a valid pass per the card: "Expect the first run to be a pipeline proof."
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import time
from typing import Optional

from . import adapter as _adapter
from .tagger import VALID_DELTA_CAUSES

MIN_STYLE_ROWS_FOR_REAL_TRAIN = 200  # [ESTIMATE — my figure, unverified.
                                      #             Card §2 says "several hundred to a few thousand".]


class UntaggedRowError(RuntimeError):
    """Rule 1 alarm — trainer must refuse untagged input, loudly."""


class InsufficientStyleRowsError(RuntimeError):
    """Not enough style rows to train real weights. Pipeline-proof mode is still valid."""


def _load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def assert_all_rows_tagged(rows: list[dict]) -> None:
    """Rule 1 alarm — raises UntaggedRowError if any turn row lacks a valid delta_cause."""
    for i, r in enumerate(rows):
        if r.get("_type") == "l3_patch":
            continue
        c = r.get("delta_cause")
        if c not in VALID_DELTA_CAUSES:
            raise UntaggedRowError(
                f"row {i} (trace_id={r.get('trace_id')!r}) has delta_cause={c!r}; "
                f"trainer refuses to run on untagged data (Ruling F, Rule 1 alarm)"
            )


def filter_to_style(rows: list[dict]) -> list[dict]:
    """
    Drop l3_patch, verification, l3_override, unknown, none.
    Only keep rows tagged 'style'. Assumes assert_all_rows_tagged already passed.
    """
    keep = []
    for r in rows:
        if r.get("_type") == "l3_patch":
            continue
        if r.get("delta_cause") == "style":
            keep.append(r)
    return keep


def _mlx_available() -> bool:
    return importlib.util.find_spec("mlx_lm") is not None


def _write_mlx_dataset(rows: list[dict], out_path: str) -> None:
    """
    MLX LoRA expects a JSONL with {"text": "..."} or {"prompt": "...", "completion": "..."}.
    We use the completion form: prompt = raw_input, completion = elo_final (the style-target).
    """
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            item = {
                "prompt": r.get("raw_input") or "",
                "completion": r.get("elo_final") or "",
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def train(
    shadow_log_path: str,
    base_model: str,
    adapter_prefix: str = "elo-style",
    force_pipeline_proof: bool = False,
) -> dict:
    """
    Full train pass. Returns {version, adapter_path, status, style_rows,
    total_rows, excluded, weights_present, notes}.

    Raises UntaggedRowError if any row is untagged (Rule 1 alarm).
    """
    rows = _load_jsonl(shadow_log_path)
    assert_all_rows_tagged(rows)

    style_rows = filter_to_style(rows)
    excluded = {
        c: 0 for c in ("none", "verification", "l3_override", "unknown")
    }
    for r in rows:
        if r.get("_type") == "l3_patch":
            continue
        c = r.get("delta_cause")
        if c in excluded:
            excluded[c] += 1

    version = _adapter.new_version_tag(base_model, prefix=adapter_prefix)
    training_config = {
        "adapter_type":   "lora",
        "min_rows":       MIN_STYLE_ROWS_FOR_REAL_TRAIN,
        "started_at":     time.time(),
        "shadow_source":  shadow_log_path,
    }

    can_train_real = (
        _mlx_available()
        and len(style_rows) >= MIN_STYLE_ROWS_FOR_REAL_TRAIN
        and not force_pipeline_proof
    )
    notes: list[str] = []

    if not can_train_real:
        if force_pipeline_proof:
            notes.append("force_pipeline_proof=True")
        if not _mlx_available():
            notes.append(
                "mlx_lm not importable; on macOS install with `pip install mlx-lm` "
                "and re-run. Pipeline-proof adapter created instead."
            )
        if len(style_rows) < MIN_STYLE_ROWS_FOR_REAL_TRAIN:
            notes.append(
                f"only {len(style_rows)} style rows; need ≥{MIN_STYLE_ROWS_FOR_REAL_TRAIN} "
                f"[ESTIMATE] before a real train is worthwhile."
            )
        adapter_path = _adapter.create_adapter(
            version=version,
            base_model=base_model,
            style_rows=style_rows,
            training_config=training_config,
            status="pipeline_proof",
            weights_bytes=None,
        )
        return {
            "version":          version,
            "adapter_path":     adapter_path,
            "status":           "pipeline_proof",
            "style_rows":       len(style_rows),
            "total_rows":       len(rows),
            "excluded":         excluded,
            "weights_present":  False,
            "notes":            notes,
        }

    # Real train path — MLX available AND we have enough rows.
    dataset_path = os.path.join(_adapter.ADAPTER_ROOT, f"{version}.dataset.jsonl")
    _write_mlx_dataset(style_rows, dataset_path)

    weights_out = os.path.join(_adapter.ADAPTER_ROOT, f"{version}.weights.safetensors")
    training_config["mlx_command"] = [
        "python3", "-m", "mlx_lm.lora",
        "--model", base_model,
        "--train",
        "--data", dataset_path,
        "--adapter-path", weights_out,
    ]

    try:
        subprocess.run(training_config["mlx_command"], check=True)
        with open(weights_out, "rb") as f:
            weights_bytes = f.read()
    except Exception as e:
        notes.append(f"mlx_lm.lora invocation failed: {e}. Falling back to pipeline_proof.")
        adapter_path = _adapter.create_adapter(
            version=version,
            base_model=base_model,
            style_rows=style_rows,
            training_config=training_config,
            status="pipeline_proof",
            weights_bytes=None,
        )
        return {
            "version":          version,
            "adapter_path":     adapter_path,
            "status":           "pipeline_proof",
            "style_rows":       len(style_rows),
            "total_rows":       len(rows),
            "excluded":         excluded,
            "weights_present":  False,
            "notes":            notes,
        }

    adapter_path = _adapter.create_adapter(
        version=version,
        base_model=base_model,
        style_rows=style_rows,
        training_config=training_config,
        status="trained",
        weights_bytes=weights_bytes,
    )
    return {
        "version":          version,
        "adapter_path":     adapter_path,
        "status":           "trained",
        "style_rows":       len(style_rows),
        "total_rows":       len(rows),
        "excluded":         excluded,
        "weights_present":  True,
        "notes":            notes,
    }
