#!/usr/bin/env python3
"""
scripts/wkg_backfill_interactions.py — WKG historical backfill from interactions.json

WO-WKG-BUILD-NOW Job 3 (David L3 2026-10-06):
    Read interactions.json → extract entities/concepts → write to WKG.
    All claims tagged provenance: "interactions_backfill_2026-10-06".

Run from ~/elo-ai/: python scripts/wkg_backfill_interactions.py

Dry-run mode (no writes):
    python scripts/wkg_backfill_interactions.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

# ── resolve project root ───────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
_log = logging.getLogger("wkg_backfill")

_INTERACTIONS_PATH = os.path.join(_ROOT, "memory", "interactions.json")
_DAVID_ENTITY_ID   = "6de402af-8b5a-4238-950f-79bb1a00ab58"
_PROVENANCE        = "interactions_backfill_2026-10-06"
_BATCH_SIZE        = 100    # log progress every N entries
_MAX_CLAIMS        = 2000   # safety cap — stop before hammering the store


def _load_interactions() -> list[dict]:
    with open(_INTERACTIONS_PATH) as f:
        data = json.load(f)
    _log.info("Loaded %d interactions", len(data))
    return data if isinstance(data, list) else []


def _extract_topics(entry: dict) -> list[str]:
    """Return candidate topic labels from an interaction entry."""
    topics: list[str] = []
    # explicit concepts field
    for c in (entry.get("concepts") or []):
        if isinstance(c, str) and len(c) >= 3:
            topics.append(c.strip())
    # first meaningful phrase from user message
    user = (entry.get("user") or "").strip()
    if user and len(user) >= 4:
        # take first 60 chars, strip trailing partial words
        snip = user[:60].rsplit(" ", 1)[0] if " " in user[:60] else user[:60]
        if snip and snip not in topics:
            topics.append(snip)
    return topics[:5]  # max 5 topics per entry


def run(dry_run: bool = False) -> None:
    from runtime.wkg_faculty import search_entities, create_entity, record_claim

    interactions = _load_interactions()
    n_claims = 0
    n_skipped = 0
    n_entities_created = 0
    n_entries = 0

    for i, entry in enumerate(interactions):
        if n_claims >= _MAX_CLAIMS:
            _log.info("Reached max claim cap (%d) — stopping", _MAX_CLAIMS)
            break

        topics = _extract_topics(entry)
        if not topics:
            n_skipped += 1
            continue

        n_entries += 1

        for topic in topics:
            if n_claims >= _MAX_CLAIMS:
                break
            try:
                hits = search_entities(topic[:60])
                if hits:
                    obj_id = hits[0]["entity_id"]
                    entity_created = False
                else:
                    if not dry_run:
                        obj = create_entity(
                            entity_type="CONCEPT",
                            label=topic[:80],
                            description=f"Backfill entity from interactions.json ({_PROVENANCE})",
                            source_ids=[_PROVENANCE],
                        )
                        obj_id = obj["entity_id"]
                    else:
                        obj_id = f"dry-run-{topic[:20]}"
                    entity_created = True
                    n_entities_created += 1

                if not dry_run:
                    record_claim(
                        subject_entity_id=_DAVID_ENTITY_ID,
                        relationship_type="ASSOCIATED_WITH",
                        object_entity_id=obj_id,
                        epistemic_class="SOURCE_ATTRIBUTED",
                        source_id=_PROVENANCE,
                        confidence=0.55,
                    )
                n_claims += 1
            except Exception as e:
                _log.debug("Skipping topic %r: %s", topic, e)
                continue

        if i % _BATCH_SIZE == 0:
            _log.info(
                "Progress: %d/%d entries | %d claims | %d entities created",
                i + 1, len(interactions), n_claims, n_entities_created,
            )

    _log.info(
        "Backfill %s — entries processed: %d | entries skipped: %d | "
        "claims written: %d | entities created: %d",
        "DRY RUN" if dry_run else "COMPLETE",
        n_entries, n_skipped, n_claims, n_entities_created,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WKG backfill from interactions.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
