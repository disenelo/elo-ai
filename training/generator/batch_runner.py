"""
training/generator/batch_runner.py — synthetic dataset generation.

Runs all prompts in prompt_library through the full eLo OS pipeline,
captures routing and responses, saves to datasets/synthetic/.

Requires a live backend (Claude or Groq) for useful training data.
With --allow-mock, runs against the mock backend for structure testing only.

Usage:
    python -m training.generator.batch_runner
    python -m training.generator.batch_runner --allow-mock
    python -m training.generator.batch_runner --limit 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

# ── path setup ────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Load .env before any other imports
def _load_dotenv():
    env_path = os.path.join(_ROOT, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip(); val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_dotenv()

# ── pipeline imports ──────────────────────────────────────────────────────────
from memory import state_manager
from memory.memory_pack_builder import build as build_memory_pack
from memory.obsidian_loader import get_context_block
from core import attention as attn
from runtime.executive import decide as exec_decide
from runtime import state_machine as sm
from runtime.prompt_builder import build as build_prompt
from runtime.backend_router import route as router_route
from knowledge.graph_loader import build_context as graph_context
from backends.mock_backend import MockBackend as _MockBackend
from avatar.presence_engine import compute as _presence_compute, reset as _presence_reset
from core.continuity import context_block as _continuity_block

from training.generator.prompt_library import PROMPTS, summary as lib_summary
from training.generator.coverage_tracker import report, print_report

_SYSTEM_VERSION = "2.1"
_DISCARD_BACKENDS = {"mock", "fallback"}


def _write_jsonl(path: str, records: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def run(
    limit:       int  = 0,
    allow_mock:  bool = False,
    verbose:     bool = False,
) -> list:
    """
    Run all prompts through the pipeline.
    Returns list of saved records.
    """
    state      = state_manager.load()
    mem_pack   = build_memory_pack(state)
    vault_ctx  = get_context_block(max_chars=1200)
    rt_state   = sm.fresh()
    fallback   = _MockBackend()
    _presence_reset()

    prompts = PROMPTS[:limit] if limit else PROMPTS
    saved: list   = []
    skipped: int  = 0
    seen: set     = set()

    lib = lib_summary()
    print(f"\n  Prompt library: {lib['total']} total — "
          f"{', '.join(f'{k}:{v}' for k,v in lib['by_category'].items())}")
    print(f"  Running {len(prompts)} prompts ...\n")

    for i, prompt in enumerate(prompts):
        raw = prompt["input"]

        attention_model = attn.compute(raw, mem_pack, state, loop_detected=False)
        exec_decision   = exec_decide(attention_model, loop_detected=False, user_input=raw)
        rt_state        = sm.update(rt_state, attention_model, exec_decision, loop_signal=False)

        g_ctx = graph_context(raw)
        _cont = _continuity_block()
        if _cont:
            g_ctx = f"{g_ctx}\n{_cont}" if g_ctx else _cont

        system = build_prompt(
            raw,
            vault_context=vault_ctx,
            state_context=state_manager.as_context_string(state),
            attention=attention_model,
            exec_decision=exec_decision,
            graph_context=g_ctx,
        )

        action = exec_decision.get("action", "")
        tone   = exec_decision.get("tone", "")
        cal_r  = exec_decision.get("cal_reason", "")
        max_s  = exec_decision.get("max_sentences", 4)
        emo    = attention_model.get("emotional_context", {})

        # Direct bypass pool entries (same as main.py)
        _raw_l = raw.lower().rstrip("!.,")
        _PURE_G = {"hey", "hello", "hi", "hiya", "yo", "hey there", "hi there",
                   "hello there", "heya", "sup", "helo"}
        _SOCIAL = ["nice to see you", "good to see you", "great to see you",
                   "hi again", "hello again", "good to be back"]
        _SELF_REF = ("how do you work", "how does elo work", "how are you built",
                     "what are you exactly", "how do you remember", "how do you think")

        backend_name = "direct"
        if _raw_l in _PURE_G or cal_r == "pure greeting":
            response = "Hey."
        elif any(p in raw.lower() for p in _SOCIAL) or cal_r == "social greeting":
            response = "Good to see you."
        elif any(p in raw.lower() for p in _SELF_REF):
            response = ("I run a loop each turn: read what matters, decide what to do, respond. "
                        "Each session connects to the last.")
        else:
            try:
                response, backend_name = router_route(system, raw, max_sentences=max_s, action=action)
            except Exception:
                response     = fallback.generate_response(raw, action, {}, {}, {}, {})["response_text"]
                backend_name = "mock"

        # Quality filter
        if len(response.strip()) < 3:
            skipped += 1
            continue
        if not allow_mock and backend_name in _DISCARD_BACKENDS:
            skipped += 1
            continue

        _hash = hash(f"{raw}|{response}")
        if _hash in seen:
            skipped += 1
            continue
        seen.add(_hash)

        presence = {}
        try:
            presence = _presence_compute(attention_model, exec_decision)
        except Exception:
            pass

        record = {
            "input":            raw,
            "response":         response,
            "action":           action,
            "tone":             tone,
            "confidence":       round(exec_decision.get("max_sentences", 3) / 4, 2),
            "presence":         _safe_presence(presence),
            "emotional_valence": prompt.get("valence", "neutral"),
            "collection_type":  "synthetic",
            "category":         prompt.get("category", ""),
            "cal_reason":       cal_r,
        }
        saved.append(record)

        if verbose or (i + 1) % 50 == 0:
            print(f"  [{i+1:>3}/{len(prompts)}] {action:<10} {backend_name:<6}  {raw[:55]}")

    # Write output
    date_str  = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path  = os.path.join(_ROOT, "datasets", "synthetic", f"synthetic_{date_str}.jsonl")
    _write_jsonl(out_path, saved)

    cov_path = os.path.join(_ROOT, "datasets", "synthetic", f"coverage_{date_str}.csv")
    result   = report(saved, output_path=cov_path)
    print_report(result)

    print(f"  Saved:   {len(saved)} records → {out_path}")
    print(f"  Skipped: {skipped} (mock/duplicate/too short)")
    print(f"  Coverage report → {cov_path}\n")

    return saved


def _safe_presence(presence: dict) -> dict:
    keep = {"animation", "intensity", "energy", "duration", "mood"}
    return {k: v for k, v in presence.items() if k in keep} if presence else {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eLo OS batch dataset generator")
    parser.add_argument("--limit",      type=int,  default=0,     help="Limit to N prompts (0 = all)")
    parser.add_argument("--allow-mock", action="store_true",       help="Allow mock backend responses")
    parser.add_argument("--verbose",    action="store_true",       help="Print every record")
    args = parser.parse_args()
    run(limit=args.limit, allow_mock=args.allow_mock, verbose=args.verbose)
