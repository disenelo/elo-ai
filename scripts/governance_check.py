#!/usr/bin/env python3
"""
scripts/governance_check.py — WO-CANON-XXVII §B
Four governance checks. Each reads real files and fails on a real condition.

Usage:
    python scripts/governance_check.py              # run all checks, print report
    python scripts/governance_check.py --json       # machine-readable output

Returns exit code 1 if any check fails.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent

# ── paths ─────────────────────────────────────────────────────────────────────
GOVERNED_INDEX = ROOT / "docs" / "architecture" / "Volume_XXVII" / "04_Governed_Index.md"
CANON_INDEX    = ROOT / "docs" / "architecture" / "00_CANON_INDEX.md"
VOLUMES_DIR    = ROOT / "docs" / "architecture"
WO_DIR         = ROOT / "engineering" / "work_orders"
DISPATCH_BOARD = WO_DIR / "DISPATCH_BOARD.md"
COMPLETION_LOG = WO_DIR / "COMPLETION_LOG.md"

# WO shape rule binds from this date (REWRITTEN 2026-08-13)
WO_SHAPE_CUTOFF = "2026-08-13"

_REQUIRED_WO_SECTIONS = (
    "files to touch",
    "files must-not-touch",
    "definition of done",
)


# ── G-1: link integrity in the governed index ─────────────────────────────────

def G1_links(index_path: pathlib.Path = GOVERNED_INDEX) -> list[dict]:
    """Return list of broken links found in the governed index.

    A broken link is a markdown [text](path) where path does not exist on disk.
    Anchors (#section) are allowed if the base file exists.
    Returns [{"link": path_str, "line": n}] for each broken reference.
    """
    if not index_path.exists():
        return [{"link": str(index_path), "line": 0, "error": "governed index not found"}]

    broken: list[dict] = []
    text = index_path.read_text(encoding="utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        for raw in re.findall(r'\[([^\]]*)\]\(([^)]+)\)', line):
            _, href = raw
            if href.startswith("http://") or href.startswith("https://"):
                continue  # external URLs not checked
            # Strip anchor
            base = href.split("#")[0].strip()
            if not base:
                continue
            target = (index_path.parent / base).resolve()
            if not target.exists():
                broken.append({"link": href, "line": n})
    return broken


# ── G-2: index/volume drift ───────────────────────────────────────────────────

def G2_drift(volumes_dir: pathlib.Path = VOLUMES_DIR,
             canon_index: pathlib.Path = CANON_INDEX) -> list[dict]:
    """Return volumes whose 00_Metadata.md `implementation:` field
    disagrees with their status row in 00_CANON_INDEX.md.

    Returns [{"volume": "Volume_XV", "metadata_impl": "PENDING", "index_status": "✅"}] for each mismatch.
    """
    if not canon_index.exists():
        return [{"error": f"00_CANON_INDEX.md not found: {canon_index}"}]

    index_text = canon_index.read_text(encoding="utf-8")
    drift: list[dict] = []

    for meta_path in sorted(volumes_dir.glob("Volume_*/00_Metadata.md")):
        vol_dir = meta_path.parent
        vol_name = vol_dir.name  # e.g. "Volume_XV"
        # Extract the identifier part (roman numeral or alphanumeric)
        m = re.match(r'Volume_([A-Z0-9]+)', vol_name)
        if not m:
            continue
        vol_id = m.group(1)  # e.g. "XV", "III", or "TEST"
        # Human-readable form: roman numerals with spaces; others as-is
        vol_spaced = re.sub(r'_', ' ', vol_name)  # "Volume XV"

        # Extract implementation: field from metadata
        meta_text = meta_path.read_text(encoding="utf-8")
        impl_match = re.search(r'^implementation:\s*(.+)', meta_text, re.MULTILINE | re.IGNORECASE)
        impl_val = impl_match.group(1).strip() if impl_match else None
        if impl_val is None:
            continue

        # Find the volume's row in 00_CANON_INDEX.md
        vol_lines = [
            line for line in index_text.splitlines()
            if f"Volume {vol_id}" in line or f"Volume_{vol_id}" in line
               or vol_spaced in line
        ]

        # Determine what the index implies about status
        index_status: str | None = None
        for line in vol_lines:
            if "✅" in line and ("Live" in line or "live" in line or "COMPLETE" in line or "complete" in line):
                index_status = "✅ Live"
                break
            if "📝" in line or "REVIEW" in line or "PENDING" in line:
                index_status = "📝 PENDING"
                break
            if "🔴" in line and "not started" in line.lower():
                index_status = "🔴 Not started"
                break

        if index_status is None:
            continue  # can't determine — skip

        # Check for disagreement: COMPLETE in metadata vs PENDING/Not-started in index
        impl_upper = impl_val.upper()
        disagreement = False
        if "COMPLETE" in impl_upper and "PENDING" in (index_status.upper() if index_status else ""):
            disagreement = True
        elif "PENDING" in impl_upper and "✅" in (index_status or ""):
            disagreement = True

        if disagreement:
            try:
                meta_rel = str(meta_path.relative_to(ROOT))
            except ValueError:
                meta_rel = str(meta_path)
            drift.append({
                "volume":         vol_name,
                "metadata_impl":  impl_val,
                "index_status":   index_status,
                "metadata_path":  meta_rel,
            })

    return drift


# ── G-3: WO shape lint ───────────────────────────────────────────────────────

def G3_wo_shape(wo_dir: pathlib.Path = WO_DIR,
                cutoff: str = WO_SHAPE_CUTOFF) -> dict:
    """Check WO-*.md files for required sections.

    Post-cutoff WOs (raised on/after cutoff) MUST have all three sections — failures listed.
    Pre-cutoff WOs are counted as backlog but NOT failed.

    Returns {"post_cutoff_failures": [...], "pre_cutoff_backlog": N, "checked": N}.
    """
    failures: list[dict] = []
    backlog = 0
    checked = 0

    date_pattern = re.compile(r'raised\s+(\d{4}-\d{2}-\d{2})', re.IGNORECASE)

    for wo_path in sorted(wo_dir.glob("WO-*.md")):
        checked += 1
        text = wo_path.read_text(encoding="utf-8", errors="replace")
        text_lower = text.lower()

        # Determine if post-cutoff: look for "raised YYYY-MM-DD" in the WO text
        dates_found = date_pattern.findall(text)
        raised_date = min(dates_found) if dates_found else None

        is_post_cutoff = raised_date is not None and raised_date >= cutoff

        # Check required sections
        missing = [
            s for s in _REQUIRED_WO_SECTIONS
            if s not in text_lower
        ]

        if missing:
            if is_post_cutoff:
                failures.append({
                    "file":        wo_path.name,
                    "raised":      raised_date,
                    "missing":     missing,
                })
            else:
                backlog += 1

    return {
        "post_cutoff_failures": failures,
        "pre_cutoff_backlog":   backlog,
        "checked":              checked,
    }


# ── G-4: DONE ownership ───────────────────────────────────────────────────────

def G4_done_ownership(board_path: pathlib.Path = DISPATCH_BOARD,
                      log_path: pathlib.Path = COMPLETION_LOG) -> list[dict]:
    """Return WO IDs marked DONE ✅ on the board with no COMPLETION_LOG.md entry.

    A WO is "owned" if COMPLETION_LOG.md contains its ID (e.g. "### [WO-096B]").
    Returns [{"id": "WO-096B", "board_line": N}] for each unowned DONE.
    """
    if not board_path.exists():
        return [{"error": f"DISPATCH_BOARD.md not found: {board_path}"}]

    board_text = board_path.read_text(encoding="utf-8")
    log_text   = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    unowned: list[dict] = []
    # Find lines with "DONE ✅" or "DONE✅" and extract WO IDs
    wo_id_re = re.compile(r'\b(WO-[A-Z0-9]+(?:-[A-Za-z0-9]+)*|WO-CANON-[IVXLCDM]+)\b')
    done_marker_re = re.compile(r'DONE\s*✅')

    for n, line in enumerate(board_text.splitlines(), 1):
        if not done_marker_re.search(line):
            continue
        ids = wo_id_re.findall(line)
        for wo_id in ids:
            # Check if COMPLETION_LOG.md has an entry for this WO
            # Pattern: "[WO-ID]" in the log
            if f"[{wo_id}]" not in log_text and f"**{wo_id}**" not in log_text:
                unowned.append({"id": wo_id, "board_line": n})

    return unowned


# ── report ─────────────────────────────────────────────────────────────────────

def run_all() -> dict:
    g1 = G1_links()
    g2 = G2_drift()
    g3 = G3_wo_shape()
    g4 = G4_done_ownership()

    return {
        "G1_link_integrity":    {"pass": not g1, "broken": g1},
        "G2_index_drift":       {"pass": not g2, "drift":  g2},
        "G3_wo_shape":          {
            "pass":            not g3["post_cutoff_failures"],
            "failures":        g3["post_cutoff_failures"],
            "pre_cutoff_backlog": g3["pre_cutoff_backlog"],
            "checked":         g3["checked"],
        },
        "G4_done_ownership":    {"pass": not g4, "unowned": g4},
    }


def print_report(results: dict) -> bool:
    """Print human-readable report. Returns True if all checks pass."""
    all_pass = True
    print("\n" + "=" * 64)
    print("Governance checks — WO-CANON-XXVII")
    print("=" * 64 + "\n")

    g1 = results["G1_link_integrity"]
    marker = "✅" if g1["pass"] else "🔴"
    print(f"{marker} G-1 link integrity: ", end="")
    if g1["pass"]:
        print("all governed-index links resolve")
    else:
        print(f"{len(g1['broken'])} broken link(s)")
        for b in g1["broken"][:10]:
            print(f"   line {b['line']}: {b['link']}")
        all_pass = False

    g2 = results["G2_index_drift"]
    marker = "✅" if g2["pass"] else "🔴"
    print(f"{marker} G-2 index/volume drift: ", end="")
    if g2["pass"]:
        print("no disagreements found")
    else:
        print(f"{len(g2['drift'])} volume(s) with status mismatch")
        for d in g2["drift"]:
            print(f"   {d['volume']}: metadata={d['metadata_impl']!r} vs index={d['index_status']!r}")
        all_pass = False

    g3 = results["G3_wo_shape"]
    marker = "✅" if g3["pass"] else "🔴"
    print(f"{marker} G-3 WO shape lint: {g3['checked']} WOs checked, "
          f"pre-cutoff backlog={g3['pre_cutoff_backlog']}, ", end="")
    if g3["pass"]:
        print("no post-cutoff violations")
    else:
        print(f"{len(g3['failures'])} post-cutoff violation(s)")
        for f in g3["failures"]:
            print(f"   {f['file']} (raised {f['raised']}): missing {f['missing']}")
        all_pass = False

    g4 = results["G4_done_ownership"]
    marker = "✅" if g4["pass"] else "🔴"
    print(f"{marker} G-4 DONE ownership: ", end="")
    if g4["pass"]:
        print("every DONE ✅ has a COMPLETION_LOG.md entry")
    else:
        print(f"{len(g4['unowned'])} DONE ✅ line(s) without a COMPLETION_LOG.md entry")
        for u in g4["unowned"][:20]:
            if "error" in u:
                print(f"   ERROR: {u['error']}")
            else:
                print(f"   {u['id']} (board line {u['board_line']})")
        print(f"   NOTE: G-4 failing on the current board is INTENDED — "
              "see WO-CANON-XXVII §B. Architect corrects board lines.")
        all_pass = False

    print()
    return all_pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Governance checks — WO-CANON-XXVII §B")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = run_all()
    if args.json:
        print(json.dumps(results, indent=2, default=str))
        ok = all(v.get("pass", True) for v in results.values())
    else:
        ok = print_report(results)

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
