#!/usr/bin/env python3
"""
tools/board_reconciler.py — WO-RECON / card 0064

Generate the WO status column from evidence.  Never hand-edit.

Evidence sources searched (all four must be checked):
  1. git log --all (commit messages naming the WO)
  2. tests/*.py files containing the WO identifier
  3. blender/agent_bus/builder/DONE/ cards containing the WO identifier
  4. Assets/Scripts/*.cs  (DISENELO-eLoDesktopBuddy Unity project)

Status vocabulary:
  DONE-proven     commit  +  test/card  +  .cs  (all three source types present)
  DONE-evidenced  two of the three source types
  partial         one source type only
  not-started     no evidence anywhere
  BLOCKED         explicitly marked blocked with a stated reason
  BLOCKED-UNEXPLAINED  marked blocked, no reason string in source

Usage:
  python tools/board_reconciler.py                      # report to stdout
  python tools/board_reconciler.py --register <path>    # custom register path
  python tools/board_reconciler.py --json               # machine-readable JSON output
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT        = pathlib.Path(__file__).parent.parent
TESTS_DIR   = ROOT / "tests"
DONE_DIR    = ROOT / "blender" / "agent_bus" / "builder" / "DONE"
CS_DIR      = pathlib.Path("/Users/Disenelo/Desktop/Output/DISENELO-eLoDesktopBuddy/Assets/Scripts")
REGISTER    = ROOT / "engineering" / "work_orders" / "WO_REGISTER_TRUTH_2026-08-20.md"

# WOs explicitly marked BLOCKED in the register (source: WO_REGISTER §BLOCKED rows)
_KNOWN_BLOCKED = {"WO-116", "WO-117", "WO-101"}


# ── identifier extraction ─────────────────────────────────────────────────────

_WO_PATTERN = re.compile(
    r'\b('
    r'WO-CANON-(?:X{0,3}(?:IX|IV|V?I{0,3})|[A-Z]+(?:-[A-Z0-9]+)*)'
    r'|WO-PRIN-[A-Z0-9-]+'
    r'|WO-BRAIN-[A-Z-]+'
    r'|WO-[A-Z0-9]+(?:-[A-Za-z0-9]+)*'
    r'|INT7-[A-Z0-9]+'
    r'|INT-[0-9]+'
    r'|CT4V-[0-9]+'
    r'|EA(?:2-)?[0-9]+[A-Z]?'
    r'|LOOP-[0-9]+'
    r')\b'
)


def extract_ids_from_register(register_path: pathlib.Path) -> list[str]:
    """Extract all WO identifiers from the register file (backtick notation)."""
    text = register_path.read_text(encoding="utf-8")
    # Backtick notation: `WO-001`
    ids = re.findall(r'`([^`]+)`', text)
    # Filter to known WO-style patterns
    result = []
    for ident in ids:
        if _WO_PATTERN.match(ident):
            result.append(ident)
    return sorted(set(result))


# ── evidence search ───────────────────────────────────────────────────────────

def _git_commits_for(ident: str) -> list[str]:
    """Return commit hashes whose message contains the identifier."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--all", "--oneline", "--grep", ident],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        )
        return [line.split()[0] for line in out.strip().splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def _test_files_for(ident: str) -> list[pathlib.Path]:
    """Return test files that contain the identifier."""
    matches = []
    if TESTS_DIR.exists():
        for f in TESTS_DIR.glob("*.py"):
            try:
                if ident.lower() in f.read_text(encoding="utf-8", errors="replace").lower():
                    matches.append(f)
            except OSError:
                pass
    return matches


def _done_cards_for(ident: str) -> list[pathlib.Path]:
    """Return DONE cards that contain the identifier."""
    matches = []
    if DONE_DIR.exists():
        for f in DONE_DIR.iterdir():
            try:
                if ident.lower() in f.read_text(encoding="utf-8", errors="replace").lower():
                    matches.append(f)
            except OSError:
                pass
    return matches


def _cs_files_for(ident: str) -> list[pathlib.Path]:
    """Return .cs files that contain the identifier."""
    matches = []
    if CS_DIR.exists():
        for f in CS_DIR.rglob("*.cs"):
            try:
                if ident.lower() in f.read_text(encoding="utf-8", errors="replace").lower():
                    matches.append(f)
            except OSError:
                pass
    return matches


# ── classification ────────────────────────────────────────────────────────────

def classify(ident: str) -> dict:
    """Gather evidence and return a result dict for this identifier."""
    commits   = _git_commits_for(ident)
    tests     = _test_files_for(ident)
    cards     = _done_cards_for(ident)
    cs_files  = _cs_files_for(ident)

    has_commit = bool(commits)
    has_test   = bool(tests)
    has_card   = bool(cards)
    has_cs     = bool(cs_files)

    source_types = sum([has_commit, has_test or has_card, has_cs])
    any_evidence = has_commit or has_test or has_card or has_cs

    if ident in _KNOWN_BLOCKED:
        # A blocked WO is BLOCKED-UNEXPLAINED unless a reason is findable in a card
        reason_found = False
        for f in DONE_DIR.iterdir() if DONE_DIR.exists() else []:
            try:
                text = f.read_text(encoding="utf-8", errors="replace").lower()
                if ident.lower() in text and ("blocked because" in text or "blocker:" in text or "blocked:" in text):
                    reason_found = True
                    break
            except OSError:
                pass
        status = "BLOCKED" if reason_found else "BLOCKED-UNEXPLAINED"
    elif not any_evidence:
        status = "not-started"
    elif source_types >= 3:
        status = "DONE-proven"
    elif source_types == 2:
        status = "DONE-evidenced"
    elif source_types == 1:
        status = "partial"
    else:
        status = "partial"

    return {
        "id":           ident,
        "status":       status,
        "commits":      commits[:3],     # cap for readability
        "test_files":   [str(f.name) for f in tests],
        "done_cards":   [str(f.name) for f in cards],
        "cs_files":     [str(f.name) for f in cs_files],
        "sources":      {
            "git":   has_commit,
            "test":  has_test,
            "card":  has_card,
            "cs":    has_cs,
        },
    }


# ── report ────────────────────────────────────────────────────────────────────

def run(register_path: pathlib.Path = REGISTER, as_json: bool = False) -> list[dict]:
    """Run the reconciler and return results."""
    ids = extract_ids_from_register(register_path)
    results = [classify(ident) for ident in ids]
    return results


def print_report(results: list[dict]) -> None:
    by_status: dict[str, list[str]] = {}
    for r in results:
        by_status.setdefault(r["status"], []).append(r["id"])

    order = ["DONE-proven", "DONE-evidenced", "partial", "not-started",
             "BLOCKED", "BLOCKED-UNEXPLAINED"]
    labels = {
        "DONE-proven":       "✅ DONE-proven",
        "DONE-evidenced":    "⚠️  DONE-evidenced",
        "partial":           "🟡 partial",
        "not-started":       "🔴 not-started",
        "BLOCKED":           "⛓  BLOCKED",
        "BLOCKED-UNEXPLAINED": "🔴 BLOCKED-UNEXPLAINED (no reason recorded)",
    }

    print(f"\n{'='*64}")
    print(f"Board reconciler — evidence-derived status")
    print(f"Sources searched: git log · tests/*.py · DONE/ cards · .cs files")
    print(f"{'='*64}\n")

    total = len(results)
    for status in order:
        ids = by_status.get(status, [])
        if not ids:
            continue
        label = labels.get(status, status)
        print(f"{label}  ({len(ids)} of {total})")
        for ident in ids:
            r = next(x for x in results if x["id"] == ident)
            src = []
            if r["sources"]["git"]:   src.append("git")
            if r["sources"]["test"]:  src.append("test")
            if r["sources"]["card"]:  src.append("card")
            if r["sources"]["cs"]:    src.append(".cs")
            src_str = f"  [{', '.join(src)}]" if src else ""
            print(f"  {ident}{src_str}")
        print()

    # Discrepancy summary
    unexplained = by_status.get("BLOCKED-UNEXPLAINED", [])
    if unexplained:
        print(f"🔴 BLOCKED with no reason: {', '.join(unexplained)}")
        print("   A blocker with no stated cause is not a blocker — name it or clear it.\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Board reconciler — WO-RECON / card 0064")
    parser.add_argument("--register", default=str(REGISTER), help="WO register path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = run(pathlib.Path(args.register))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
