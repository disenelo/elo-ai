"""
scripts/wkg_backfill_interactions.py — WO-0096 WKG BACKFILL

Processes interactions.json into WKG nodes. Facts/knowledge from David's
utterances only (Builder 1 scope). Significance patterns → SPG (Builder 2).

Deduplication: uses timestamp as experience_id prefix so already-processed
turns are skipped on re-runs.

Run: python3 scripts/wkg_backfill_interactions.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys
import argparse
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("wkg_backfill")


def _xid_from_entry(entry: dict) -> str:
    ts = entry.get("timestamp", "")
    # Use timestamp as a stable dedup key, normalised to safe chars
    return "backfill:" + ts.replace(":", "-").replace(".", "-")[:32]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Parse + match patterns but don't write")
    ap.add_argument("--limit", type=int, default=0, help="Max entries to process (0 = all)")
    args = ap.parse_args()

    interactions_path = os.path.join(ROOT, "memory", "interactions.json")
    if not os.path.isfile(interactions_path):
        log.error("interactions.json not found at %s", interactions_path)
        sys.exit(1)

    with open(interactions_path, encoding="utf-8") as f:
        entries = json.load(f)

    if not isinstance(entries, list):
        log.error("interactions.json is not a list")
        sys.exit(1)

    log.info("Loaded %d interactions", len(entries))

    # Build set of already-processed source_ids from existing WKG claims
    from runtime import wkg_faculty as wf
    existing_claims = wf._load("claims")
    processed_xids: set[str] = set()
    for c in existing_claims:
        for sid in (c.get("source_ids") or []):
            processed_xids.add(sid)

    log.info("Existing WKG: %d entities, %d claims, %d unique source_ids",
             len(wf._load("entities")), len(existing_claims), len(processed_xids))

    from runtime.wkg_fact_extractor import extract_and_write

    processed = 0
    skipped_dup = 0
    skipped_empty = 0
    written_claims = 0
    errors = 0

    limit = args.limit or len(entries)

    for entry in entries[:limit]:
        user_msg = (entry.get("user") or "").strip()
        if not user_msg or len(user_msg) < 8:
            skipped_empty += 1
            continue

        # Skip turns where eLo's own world-knowledge injection was prepended —
        # those are not David's raw words and should not be treated as stated facts.
        if user_msg.startswith("[WORLD_KNOWLEDGE") or user_msg.startswith("[REMINDER_SET]"):
            skipped_empty += 1
            continue

        xid = _xid_from_entry(entry)
        if xid in processed_xids:
            skipped_dup += 1
            continue

        project = entry.get("project_tag", "general")

        if args.dry_run:
            # Just match patterns without writing
            from runtime.wkg_fact_extractor import _PATTERNS, _QUESTION_PREFIXES, _MAX_UTTERANCE_LEN
            if user_msg.endswith("?") or _QUESTION_PREFIXES.match(user_msg) or len(user_msg) > _MAX_UTTERANCE_LEN:
                skipped_empty += 1
                continue
            matched = [tmpl.format(**{k: v for k, v in m.groupdict().items() if v})
                       for pat, rel, sig, tmpl in _PATTERNS
                       if (m := pat.search(user_msg))]
            if matched:
                log.info("[DRY-RUN] %s | %s | facts: %s", xid[:20], user_msg[:60], matched)
                processed += 1
        else:
            try:
                claim_ids = extract_and_write(user_msg, experience_id=xid, project=project)
                if claim_ids:
                    written_claims += len(claim_ids)
                    log.debug("Wrote %d claims for %s", len(claim_ids), xid[:20])
                processed += 1
            except Exception as exc:
                log.warning("extract_and_write error for %s: %s", xid[:20], exc)
                errors += 1

    ents_after = wf._load("entities")
    claims_after = wf._load("claims")

    print()
    print("=" * 60)
    print(f"WKG Backfill {'[DRY-RUN] ' if args.dry_run else ''}Complete")
    print(f"  Entries processed : {processed}")
    print(f"  Skipped (dup)     : {skipped_dup}")
    print(f"  Skipped (empty/Q) : {skipped_empty}")
    print(f"  Claims written    : {written_claims if not args.dry_run else 'N/A'}")
    print(f"  Errors            : {errors}")
    print(f"  WKG entities after: {len(ents_after)}")
    print(f"  WKG claims after  : {len(claims_after)}")


if __name__ == "__main__":
    main()
