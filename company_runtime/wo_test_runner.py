#!/usr/bin/env python3
"""
wo_test_runner.py — line up EVERY work order, run its tests, show full detail,
and sort each WO into an action tier by TYPE:

  • AUTO    — pure engineering / cognitive / kernel / runtime WOs with a runnable
              test. Green tests == done → safe to AUTO-CLOSE (flip board to DONE).
  • CONFIRM — live-behaviour eLo felt by David (voice / routing / memory / movement).
              Tests verify the mechanics, but David likes to feel it → tests green =
              PROPOSE-CLOSE (one-click confirm), not silent auto-close.
  • REVIEW  — needs David's eye or a reserved gate: Design/visual look, money (BO-*),
              legal (LG-*), safety (RD-CAD / robot). NEVER auto-closed.

Default is DRY-RUN: runs tests + prints the report, changes nothing.
Pass --apply to actually flip AUTO-tier green WOs to DONE on the board (reversible;
one edit per WO; leaves CONFIRM/REVIEW for David).

Usage:
  python3 -m company_runtime.wo_test_runner                 # dry-run, all WOs
  python3 -m company_runtime.wo_test_runner --wo WO-019     # one WO
  python3 -m company_runtime.wo_test_runner --tier AUTO     # only a tier
  python3 -m company_runtime.wo_test_runner --apply         # auto-close AUTO greens
  python3 -m company_runtime.wo_test_runner --json out.json # also write machine report
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time, glob

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repo root
TESTS  = os.path.join(ROOT, "tests")
BOARD  = os.path.join(ROOT, "engineering", "work_orders", "DISPATCH_BOARD.md")

# ── Policy: importance tier per WO (shared source of truth) ───────────────────
from company_runtime import wo_policy

TIERS = ("AUTO", "CONFIRM", "DAVID", "RESERVED")   # auto-close only on AUTO+green

def tier_for(wo: str, board_status: str, title: str = "") -> str:
    return wo_policy.classify(wo, title, board_status or "")["importance"]

# ── Map a test file → its WO id ───────────────────────────────────────────────
def wo_from_testfile(fn: str) -> str | None:
    b = os.path.basename(fn)
    m = re.match(r"test_wo([0-9]+)([a-z]?)_", b)      # test_wo019_ / test_wo004a_
    if m: return f"WO-{int(m.group(1)):03d}{m.group(2)}"
    m = re.match(r"test_int([0-9]+)_", b)
    if m: return "INT-" + m.group(1)
    m = re.match(r"test_ea([0-9])_([0-9]+)_", b)
    if m: return f"EA{m.group(1)}-{m.group(2)}"
    return None

def discover() -> dict[str, str]:
    """WO id -> test file path."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(TESTS, "test_*.py"))):
        wo = wo_from_testfile(fn)
        if wo:
            out[wo] = fn
    return out

# ── Pull each WO's current board status cell (for tiering + skip-if-done) ──────
def board_status() -> dict[str, str]:
    st = {}
    if not os.path.exists(BOARD): return st
    for l in open(BOARD, encoding="utf-8"):
        if not l.startswith("|") or l.count("|") < 6: continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) < 5: continue
        wo = re.sub(r"\*\*", "", c[0]).strip()
        st.setdefault(wo, c[4])
    return st

# ── Run one test file, capture full detail ────────────────────────────────────
# DISENELO tests are self-running scripts: `python3 tests/test_xxx.py` prints its
# own "Result: N/M passed, K failed" and ✅/❌ markers. We run them directly
# (pytest can't collect them) and parse that self-report. Falls back to pytest
# only if the file defines pytest-style test_ functions and prints no self-report.
def run_test(path: str) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, path], cwd=ROOT,
                           capture_output=True, text=True, timeout=300)
        out = (p.stdout or "") + ("\n" + p.stderr if (p.stderr or "").strip() else "")
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return {"rc": 124, "passed": 0, "failed": 0, "errors": 1,
                "summary": "TIMEOUT (>300s)", "detail": "timed out", "secs": 300.0}
    except Exception as e:
        return {"rc": 1, "passed": 0, "failed": 0, "errors": 1,
                "summary": f"RUNNER ERROR: {e}", "detail": str(e), "secs": 0.0}

    # primary: the "Result: N/M passed, K failed" self-report (last one wins)
    passed = failed = 0
    summary = ""
    ms = re.findall(r"(\d+)\s*/\s*(\d+)\s*passed,\s*(\d+)\s*failed", out)
    if ms:
        passed = int(ms[-1][0]); failed = int(ms[-1][2])
        summary = f"{passed} passed, {failed} failed (self-report)"
    else:
        # fallback: count ✅ / ❌ markers, or a traceback
        passed = out.count("✅") + len(re.findall(r"\bPASS(ED)?\b", out))
        failed = out.count("❌") + len(re.findall(r"\bFAIL(ED)?\b", out))
        if "Traceback (most recent call last)" in out and passed == 0:
            summary = "import/runtime error (traceback)"
        else:
            summary = f"{passed} passed, {failed} failed (marker-count)"
    errors = 1 if (rc != 0 and passed == 0) else 0
    return {"rc": rc, "passed": passed, "failed": failed, "errors": errors,
            "summary": summary, "detail": out, "secs": round(time.time() - t0, 1)}

# Green = the script's own tally shows all-pass (rc may be nonzero if a test uses a
# custom exit code, so we trust the parsed tally: passed>0 and failed==0 and no fatal error).
GREEN = lambda r: r["passed"] > 0 and r["failed"] == 0 and r["errors"] == 0

# ── Flip a board row to DONE (AUTO auto-close) ────────────────────────────────
def auto_close(wo: str, note: str) -> bool:
    src = open(BOARD, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    tag = f"| **{wo}** |"
    tag2 = f"| {wo} |"
    changed = False
    for i, l in enumerate(lines):
        if l.startswith(tag) or l.startswith(tag2):
            c = l.rstrip("\n").split("|")
            if len(c) < 6: continue
            if "DONE" in c[5]: return False  # already done
            c[5] = f" **DONE ✅ auto-verified ({note})** " + c[5].strip() + " "
            lines[i] = "|".join(c) + "\n"
            changed = True
            break
    if changed:
        open(BOARD, "w", encoding="utf-8").write("".join(lines))
    return changed

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wo", help="run one WO id, e.g. WO-019")
    ap.add_argument("--tier", choices=["AUTO", "CONFIRM", "REVIEW"], help="filter to a tier")
    ap.add_argument("--apply", action="store_true", help="auto-close AUTO-tier green WOs on the board")
    ap.add_argument("--full", action="store_true", help="print full pytest detail per WO")
    ap.add_argument("--json", help="write machine-readable report to this path")
    a = ap.parse_args()

    mapping = discover()
    bstat = board_status()
    items = []
    for wo, path in mapping.items():
        if a.wo and wo.upper() != a.wo.upper(): continue
        tier = tier_for(wo, bstat.get(wo, ""))
        if a.tier and tier != a.tier: continue
        items.append((wo, path, tier))
    order = {"AUTO": 0, "CONFIRM": 1, "DAVID": 2, "RESERVED": 3}
    items.sort(key=lambda x: (order.get(x[2], 9), x[0]))

    print(f"\n╔══ WO TEST RUNNER · {len(items)} work orders · {'APPLY' if a.apply else 'DRY-RUN'} ══╗\n")
    report, closed = [], []
    for wo, path, tier in items:
        r = run_test(path)
        ok = GREEN(r)
        icon = "🟢" if ok else "🔴"
        action = "—"
        if ok and tier == "AUTO":
            action = "AUTO-CLOSE" + (" → applied" if a.apply else " (dry-run)")
        elif ok and tier == "CONFIRM":
            action = "PROPOSE-CLOSE → David 1-click"
        elif ok and tier in ("DAVID", "RESERVED"):
            action = "HOLD → David (your call)" if tier == "DAVID" else "HOLD → David L3"
        elif not ok:
            action = "STAYS OPEN (not green)"
        print(f"{icon} {wo:9} [{tier:7}] {r['passed']}p/{r['failed']}f/{r['errors']}e "
              f"{r['secs']:>5}s  {r['summary'][:46]:46}  → {action}")
        if a.full or not ok:
            print("   " + "-" * 72)
            for ln in r["detail"].splitlines():
                print("   " + ln)
            print("   " + "-" * 72)
        if a.apply and ok and tier == "AUTO":
            if auto_close(wo, os.path.basename(path)):
                closed.append(wo)
        report.append({"wo": wo, "tier": tier, "test": os.path.relpath(path, ROOT),
                       "green": ok, **{k: r[k] for k in ("passed", "failed", "errors", "rc", "summary", "secs")}})

    # roll-up
    def n(t): return sum(1 for x in report if x["tier"] == t)
    def g(t): return sum(1 for x in report if x["tier"] == t and x["green"])
    print("\n╠══ ROLL-UP (importance) ══╗")
    for t in TIERS:
        if n(t): print(f"  {wo_policy.BADGE[t]} {t:9} : {g(t)}/{n(t)} green — {wo_policy.LABEL[t]}")
    if a.apply and closed:
        print(f"\n  ✅ AUTO-CLOSED on board: {', '.join(closed)}")
    elif not a.apply:
        auto_green = [x['wo'] for x in report if x['tier']=='AUTO' and x['green']]
        if auto_green:
            print(f"\n  → would AUTO-CLOSE (run with --apply): {', '.join(auto_green)}")
    confirm_green = [x['wo'] for x in report if x['tier']=='CONFIRM' and x['green']]
    if confirm_green:
        print(f"  → PROPOSE-CLOSE (David 1-click): {', '.join(confirm_green)}")

    if a.json:
        json.dump({"generated": time.time(), "apply": a.apply, "closed": closed, "items": report},
                  open(a.json, "w"), indent=2)
        print(f"\n  report → {a.json}")

if __name__ == "__main__":
    main()
