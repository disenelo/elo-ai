"""
scripts/wkg_backfill.py — WO-WKG-GRAPH-001 Job 3

Historical backfill: process memory/interactions.json → WKG claims.

REQUIRES BOARD SIGN-OFF BEFORE RUNNING.
Will write claims to memory/wkg/claims.json and entities.json.

Usage:
  python scripts/wkg_backfill.py --dry-run     # show what would be written
  python scripts/wkg_backfill.py               # write (requires --confirm)
  python scripts/wkg_backfill.py --confirm     # actually write claims

Output: provenance "interactions_backfill_2026-10-06" on every claim written.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_INTERACTIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "memory", "interactions.json"
)
_PROVENANCE = "interactions_backfill_2026-10-06"
_DAVID_ENTITY_ID = "6de402af-8b5a-4238-950f-79bb1a00ab58"


def _load_interactions() -> list:
    with open(_INTERACTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _build_summary(entry: dict) -> str:
    user = (entry.get("user") or "").strip()[:120]
    concepts = entry.get("concepts") or []
    tags = ",".join(concepts[:4]) if concepts else ""
    if tags:
        return f"[{tags}] {user}"
    return user


def run(dry_run: bool = True):
    from runtime.wkg_faculty import (
        search_entities, create_entity, record_claim, _load,
    )
    from runtime.memory_origin import MemoryOrigin

    interactions = _load_interactions()
    print(f"Loaded {len(interactions)} interactions from interactions.json")

    # Filter: entries with concepts (category tags) and non-trivial user text
    candidates = [
        e for e in interactions
        if e.get("concepts")
        and len((e.get("user") or "").strip()) >= 15
        and "[eLo AI" not in (e.get("response") or "")  # skip placeholder-mode entries
    ]
    print(f"Eligible (has concepts, non-placeholder): {len(candidates)}")

    # Deduplicate by summary label (avoid flooding identical topics)
    seen_labels: set[str] = set()
    written = 0
    skipped_dup = 0
    skipped_existing = 0

    for entry in candidates:
        summary = _build_summary(entry)
        label = summary[:80]
        if label in seen_labels:
            skipped_dup += 1
            continue
        seen_labels.add(label)

        if dry_run:
            print(f"  DRY-RUN: would write — {label}")
            written += 1
            continue

        # Find or create concept entity
        hits = search_entities(label[:60])
        if hits:
            obj_id = hits[0]["entity_id"]
            skipped_existing += 1
        else:
            obj_ent = create_entity(
                entity_type="CONCEPT",
                label=label,
                description=(
                    f"Auto-backfilled from interactions.json "
                    f"({entry.get('project_tag','')}, "
                    f"{entry.get('timestamp','')[:10]}). "
                    f"Concepts: {', '.join(entry.get('concepts', []))}."
                ),
                source_ids=[_PROVENANCE],
                domain="Concepts",
            )
            if obj_ent.get("rejected"):
                skipped_existing += 1
                continue
            obj_id = obj_ent["entity_id"]

        record_claim(
            subject_entity_id=_DAVID_ENTITY_ID,
            relationship_type="ASSOCIATED_WITH",
            object_entity_id=obj_id,
            epistemic_class="SOURCE_ATTRIBUTED",
            source_id=_PROVENANCE,
            confidence=0.65,
            memory_type="episodic",
            memory_origin=MemoryOrigin.REAL_EXPERIENCE.value,
            context_action=entry.get("mode", ""),
        )
        written += 1

        if written % 50 == 0:
            print(f"  Written {written}...")

    print(f"\n--- Summary ---")
    print(f"Written: {written}")
    print(f"Skipped (duplicate label): {skipped_dup}")
    print(f"Skipped (entity already existed): {skipped_existing}")
    if dry_run:
        print("\nDRY RUN — nothing was written. Run with --confirm to write.")
    else:
        print(f"\nBackfill complete. All claims carry provenance={_PROVENANCE!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WKG backfill from interactions.json")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Show what would be written without writing (default)")
    parser.add_argument("--confirm", action="store_true",
                        help="Actually write claims (Board sign-off required)")
    args = parser.parse_args()

    if args.confirm:
        print("RUNNING WITH --confirm: claims will be written to the live WKG store.\n")
        run(dry_run=False)
    else:
        print("DRY RUN mode (use --confirm to actually write).\n")
        run(dry_run=True)
