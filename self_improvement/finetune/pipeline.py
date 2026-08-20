"""
self_improvement/finetune/pipeline.py — WO-104 end-to-end orchestrator.

    capture (already live via shadow_capture)  →
    tag (backfill delta_cause where derivable) →
    trainer (refuse untagged; filter to style) →
    adapter (versioned, delete-to-revert)      →
    gate  (honesty, identity, style probes)    →
    activate on 'gated' verdict

Idle/scheduled use only. NEVER called on the response path.

Outbox schema (returned dict AND persisted to Output/finetune_adapters/last_run.json):
    ts, base_model, tally, style_rows_after_tagging, adapter_version,
    adapter_status, notes, recommendation ('ship' | 'hold'), reason
"""
from __future__ import annotations

import json
import os
import time

from . import adapter as _adapter
from . import gate as _gate
from . import tagger as _tagger
from . import trainer as _trainer

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SHADOW_LOG = os.environ.get(
    "ELO_SHADOW_LOG",
    os.path.join(_ROOT, "self", "journals", "understudy_shadow.jsonl"),
)
DEFAULT_BASE_MODEL = os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")
LAST_RUN_PATH = os.path.join(_adapter.ADAPTER_ROOT, "last_run.json")


def run(
    shadow_log_path: str = DEFAULT_SHADOW_LOG,
    base_model: str = DEFAULT_BASE_MODEL,
    force_pipeline_proof: bool = False,
) -> dict:
    started = time.time()
    tally = _tagger.backfill(shadow_log_path)

    train_result = _trainer.train(
        shadow_log_path=shadow_log_path,
        base_model=base_model,
        force_pipeline_proof=force_pipeline_proof,
    )

    eval_report = _gate.evaluate(train_result["version"])

    if eval_report.get("verdict") == "gated":
        recommendation = "ship"
        reason = "eval passed: honesty preserved, no identity drift, style moved as intended"
    elif train_result["status"] == "pipeline_proof":
        recommendation = "hold"
        reason = (
            f"pipeline-proof run: {train_result['style_rows']} usable style rows, "
            f"below the {_trainer.MIN_STYLE_ROWS_FOR_REAL_TRAIN} [ESTIMATE] threshold "
            f"and/or MLX toolchain not installed. Capture more style deltas, then re-run."
        )
    else:
        recommendation = "hold"
        reason = f"train result status={train_result['status']!r}; eval verdict={eval_report.get('verdict')!r}"

    result = {
        "ts":                        started,
        "base_model":                base_model,
        "shadow_source":             shadow_log_path,
        "tally":                     tally,
        "style_rows_after_tagging":  train_result["style_rows"],
        "adapter_version":           train_result["version"],
        "adapter_status":            train_result["status"],
        "adapter_path":              train_result["adapter_path"],
        "excluded":                  train_result["excluded"],
        "eval_report":               eval_report,
        "notes":                     train_result["notes"],
        "recommendation":            recommendation,
        "reason":                    reason,
    }

    os.makedirs(_adapter.ADAPTER_ROOT, exist_ok=True)
    with open(LAST_RUN_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, indent=2))
