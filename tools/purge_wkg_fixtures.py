"""
tools/purge_wkg_fixtures.py — WKG-FACT-QUALITY-001 fixture purge

Removes test_label_* entities and their associated claims from live WKG memory.
Backs up both files before touching them.

Run ONCE, from the elo-ai root:
    python tools/purge_wkg_fixtures.py

Board-approved 2026-10-10 (WKG-FACT-QUALITY-001).
"""
import json
import shutil
import time
from pathlib import Path

ENTITIES_PATH = Path("memory/wkg/entities.json")
CLAIMS_PATH   = Path("memory/wkg/claims.json")


def main() -> None:
    ts = int(time.time())

    # Backup
    shutil.copy(ENTITIES_PATH, f"{ENTITIES_PATH}.bak_{ts}")
    shutil.copy(CLAIMS_PATH,   f"{CLAIMS_PATH}.bak_{ts}")
    print(f"Backed up to .bak_{ts}")

    entities = json.loads(ENTITIES_PATH.read_text())
    claims   = json.loads(CLAIMS_PATH.read_text())

    test_eids = {e["entity_id"] for e in entities if str(e.get("label", "")).startswith("test_label_")}
    print(f"test_label entities: {len(test_eids)}")

    entities_clean = [e for e in entities if e["entity_id"] not in test_eids]
    claims_clean   = [c for c in claims
                      if c.get("object_entity_id") not in test_eids
                      and c.get("subject_entity_id") not in test_eids]

    print(f"Entities: {len(entities)} → {len(entities_clean)} (removed {len(entities) - len(entities_clean)})")
    print(f"Claims:   {len(claims)} → {len(claims_clean)} (removed {len(claims) - len(claims_clean)})")

    ENTITIES_PATH.write_text(json.dumps(entities_clean, indent=2))
    CLAIMS_PATH.write_text(json.dumps(claims_clean, indent=2))
    print("Purge complete.")


if __name__ == "__main__":
    main()
