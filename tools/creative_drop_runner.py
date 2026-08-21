"""
tools/creative_drop_runner.py — folder-drop caller for the Vol XXVI creative loop.

Trigger: a file in Output/DROP/<campaign>/00_inbox/.
Action:  read the drop, invoke the Executive-owned creative loop, write the
         Executive's selected synthesis into 03_ready/ as an observable David
         can look at. Nothing publishes; the loop stops at 03_ready/
         (SOCIAL DESIGN STUDIO rule; 0073 boundary).

RESERVED (money · pricing · funding goals) → not touched here.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

from faculties.creative.creative_imagination import (
    run_creative_loop,
    executive_select,
)

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("_", text.lower()).strip("_") or "drop"


def _extract_seeds(text: str, max_seeds: int = 4) -> list[str]:
    """Pull seed concepts from a drop file. Prefers explicit 'seeds:' line; otherwise
    the first bulleted words; otherwise the top nouns."""
    seeds: list[str] = []
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("seeds:"):
            for tok in low[len("seeds:"):].split(","):
                tok = tok.strip()
                if tok:
                    seeds.append(tok)
        elif line.startswith("- ") and len(seeds) < max_seeds:
            seeds.append(line[2:].strip())
    if not seeds:
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]+", text) if len(w) > 3]
        seeds = words[:max_seeds]
    return seeds[:max_seeds]


def _extract_goal(text: str, filename: str) -> str:
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("goal:"):
            return line.split(":", 1)[1].strip()
    return Path(filename).stem.replace("_", " ")


def process_drop(
    drop_path: Path,
    *,
    campaign_root: Path,
    identity_terms: Optional[list[str]] = None,
    canon_terms: Optional[list[str]] = None,
    aesthetic_profile: Optional[dict] = None,
) -> dict:
    """Run one drop file through the creative loop, writing the observable.

    Returns the loop result plus 'output_path' when the Executive selected a synthesis.
    """
    text = drop_path.read_text(encoding="utf-8")
    goal = _extract_goal(text, drop_path.name)
    seeds = _extract_seeds(text)
    spark = text.strip().splitlines()[0] if text.strip() else drop_path.stem

    result = run_creative_loop(
        spark=spark, goal=goal, seeds=seeds,
        executive_select_fn=executive_select,
        identity_terms=identity_terms,
        canon_terms=canon_terms,
        aesthetic_profile=aesthetic_profile,
    )

    ready_dir = campaign_root / "03_ready"
    ready_dir.mkdir(parents=True, exist_ok=True)
    output_path = None
    if result["selected"] is not None:
        cand = result["selected"]["candidate"]
        sig = result.get("significance") or {}
        out_slug = _slug(f"{goal}_{cand['concept']}")
        output_path = ready_dir / f"{out_slug}.md"
        output_path.write_text(
            f"# {goal}\n\n"
            f"epistemic_status: {cand['epistemic_status']}\n"
            f"domain: {cand['domain']}\n\n"
            f"## Metaphor (Executive-selected)\n{cand['metaphor']}\n\n"
            f"## Rationale\n{cand['rationale']}\n\n"
            f"## Bridge symbols\n" + ", ".join(cand['bridge_symbols']) + "\n\n"
            f"## Significance\noverall: {sig.get('overall', 0):.3f}\n"
            f"memory_ref: {result.get('memory_ref') or 'below_threshold'}\n\n"
            f"## Source drop\n{drop_path.name}\n",
            encoding="utf-8",
        )
        result["output_path"] = str(output_path)

    log_path = campaign_root / "_creative_loop.log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts":       time.time(),
            "drop":     drop_path.name,
            "goal":     goal,
            "seeds":    seeds,
            "selected": bool(result["selected"]),
            "reason":   result.get("reason"),
            "memory_ref": result.get("memory_ref"),
        }, ensure_ascii=False) + "\n")
    return result


def scan_campaign(campaign_root: Path) -> list[dict]:
    """Process every file in 00_inbox/ once. Files stay in place; only 03_ready/ is written."""
    inbox = campaign_root / "00_inbox"
    if not inbox.exists():
        return []
    results = []
    for drop in sorted(inbox.iterdir()):
        if drop.is_file() and not drop.name.startswith("."):
            results.append(process_drop(drop, campaign_root=campaign_root))
    return results


if __name__ == "__main__":  # pragma: no cover
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print(json.dumps({"processed": len(scan_campaign(root))}, indent=2))
