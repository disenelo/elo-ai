"""
creative/drop_loop.py — The DROP loop for the social_design_studio seat.

Polls 01_INBOX for new files. Catalogues each one, proposes derivatives,
surfaces choices to David. Never renames files. Never ships without approval.

Usage (one-pass scan):
    python creative/drop_loop.py --once

Usage (continuous poll every 60s):
    python creative/drop_loop.py --poll 60

WO: social_design_studio/QUEUE/0001_STAND_UP_THE_DROP_LOOP.md
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from creative.catalogue import (
    INBOX, CATALOGUED, FOR_DAVID,
    classify,
    write_sidecar,
    write_question_card,
    write_proposal_card,
    write_approval_gate,
)

_log = logging.getLogger("drop_loop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_PROCESSED_LOG = CATALOGUED / "_processed.log"


def _already_processed(path: Path) -> bool:
    """Returns True if this file has already been catalogued this run."""
    if not _PROCESSED_LOG.exists():
        return False
    return path.name in _PROCESSED_LOG.read_text(encoding="utf-8")


def _mark_processed(path: Path) -> None:
    with _PROCESSED_LOG.open("a", encoding="utf-8") as f:
        f.write(path.name + "\n")


def _is_skip_file(path: Path) -> bool:
    """Skip hidden files, sidecars, log files, and _-prefixed placeholder files."""
    name = path.name
    return (
        name.startswith(".")
        or name.startswith("_")
        or name.endswith(".catalogue.md")
        or name.endswith(".proposal.md")
        or name.endswith(".question.md")
        or name.endswith(".approval.md")
        or name.endswith(".log")
        or not path.is_file()
    )


def process_file(path: Path) -> dict:
    """Process one file from INBOX. Returns a result dict."""
    if _is_skip_file(path):
        return {"file": path.name, "action": "skipped"}

    if _already_processed(path):
        return {"file": path.name, "action": "already_processed"}

    entry = classify(path)
    result = {"file": path.name, "project": entry.project, "confidence": entry.confidence}

    # Always write catalogue sidecar (project known or not)
    sidecar = write_sidecar(entry)
    result["sidecar"] = str(sidecar)

    if entry.project is None:
        # Uncertain → question card in 04_FOR_DAVID, no proposal
        q_card = write_question_card(entry)
        result["action"] = "question"
        result["question_card"] = str(q_card)
        _log.info("QUESTION  %-40s → project uncertain → %s", path.name, q_card.name)
    else:
        # Clear project → proposal + approval gate
        proposal = write_proposal_card(entry)
        approval = write_approval_gate(entry, proposal)
        result["action"] = "proposed"
        result["proposal"] = str(proposal)
        result["approval_gate"] = str(approval)
        _log.info(
            "CATALOGUED %-40s → project=%s (conf=%s) → %s",
            path.name, entry.project, entry.confidence, approval.name,
        )

    _mark_processed(path)
    return result


def scan_once(inbox: Path = INBOX) -> list[dict]:
    """One pass over INBOX. Returns list of result dicts."""
    if not inbox.exists():
        _log.warning("INBOX does not exist: %s", inbox)
        return []

    results = []
    for path in sorted(inbox.iterdir()):
        r = process_file(path)
        if r.get("action") not in ("skipped", "already_processed"):
            results.append(r)
    return results


def loop(interval_s: int = 60, inbox: Path = INBOX) -> None:
    _log.info("DROP loop starting — polling %s every %ds", inbox, interval_s)
    while True:
        results = scan_once(inbox)
        if results:
            _log.info("Processed %d file(s) this pass", len(results))
        time.sleep(interval_s)


def main() -> None:
    parser = argparse.ArgumentParser(description="DROP loop — creative seat")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true", help="Single pass, then exit")
    group.add_argument("--poll", type=int, metavar="SECONDS", help="Poll continuously")
    args = parser.parse_args()

    if args.poll:
        loop(interval_s=args.poll)
    else:
        results = scan_once()
        _log.info("Scan complete — %d item(s) processed", len(results))
        for r in results:
            print(f"  {r.get('action','?'):12} {r['file']}")


if __name__ == "__main__":
    main()
