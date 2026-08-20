"""
tests/test_0038_exception_list_ratified.py — Card 0038 acceptance.

The Exception List is RATIFIED. 31 pre-spine handlers, four verdicts:
  TRANSPORT (3)          — stay outside the loop, must journal
  SAFETY (3)             — stay outside the loop, highest-priority journalling
  EXECUTOR-FAST-PATH (12)— may stay only if it journals
  COGNITIVE (13)         — no ratified ground, must ROUTE through spine

Assertions (card 0038 §Build order, step 4 — pairs with WO-103):

  AT-1  All 31 ratified handlers emit `_bypass_journal(backend=..,
        handler_class=.., line=..)` with the exact (backend, class, line)
        tuple ratified in card 0038.

  AT-2  Every `_bypass_journal` handler_class is one of the four ratified
        classes (TRANSPORT, SAFETY, EXECUTOR-FAST-PATH, COGNITIVE). A new
        class label is unratified and fails the test.

  AT-3  Every `return {` inside `_process_turn` **before** `_spine_run(`
        is preceded (within a small window) by a `_bypass_journal` call
        whose class is in {TRANSPORT, SAFETY, EXECUTOR-FAST-PATH} — i.e.
        one of the 18 ratified grounds. A COGNITIVE-classified early
        return (must-route, but returned) or an unjournalled early return
        fails the test. **This is what stops number 32 appearing.**

Run: python3 tests/test_0038_exception_list_ratified.py
"""
from __future__ import annotations
import os
import re
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

_SERVER_PY = os.path.join(_REPO, "server.py")

# ─── Ratified table (from card 0038) ────────────────────────────────────────
# (backend, handler_class, ratified_line)
RATIFIED: list[tuple[str, str, int]] = [
    # TRANSPORT — 3
    ("guard",           "TRANSPORT",           1586),
    ("direct",          "TRANSPORT",           1610),
    ("direct",          "TRANSPORT",           1640),
    # SAFETY — 3
    ("computer_control","SAFETY",              1631),
    ("direct",          "SAFETY",              1659),
    ("computer_control","SAFETY",              1667),
    # EXECUTOR-FAST-PATH — 12
    ("anim_cmd",        "EXECUTOR-FAST-PATH",  1685),
    ("scale_cmd",       "EXECUTOR-FAST-PATH",  1705),
    ("invade_cmd",      "EXECUTOR-FAST-PATH",  1715),
    ("open_last",       "EXECUTOR-FAST-PATH",  1737),
    ("video_ctrl",      "EXECUTOR-FAST-PATH",  1764),
    ("video_ctrl",      "EXECUTOR-FAST-PATH",  1780),
    ("yt_volume",       "EXECUTOR-FAST-PATH",  1809),
    ("yt_volume",       "EXECUTOR-FAST-PATH",  1827),
    ("yt_app",          "EXECUTOR-FAST-PATH",  1849),
    ("media_open",      "EXECUTOR-FAST-PATH",  1947),
    ("media_open",      "EXECUTOR-FAST-PATH",  1962),
    ("app_switch",      "EXECUTOR-FAST-PATH",  2337),
    # COGNITIVE — 13 (must route: journal + fall through, NO early return)
    ("file_agent",      "COGNITIVE",           1601),
    ("image_gen",       "COGNITIVE",           1877),
    ("model_gen",       "COGNITIVE",           1905),
    ("action_agent",    "COGNITIVE",           1981),
    ("reminder",        "COGNITIVE",           2050),
    ("desktop_list",    "COGNITIVE",           2089),
    ("project_list",    "COGNITIVE",           2116),
    ("app_list",        "COGNITIVE",           2208),
    ("chrome_tabs",     "COGNITIVE",           2289),
    ("tracker_agent",   "COGNITIVE",           2358),
    ("company_state",   "COGNITIVE",           2377),
    ("cultural_facts",  "COGNITIVE",           2393),
    ("decision_journal","COGNITIVE",           2404),
]

RATIFIED_CLASSES = frozenset({"TRANSPORT", "SAFETY", "EXECUTOR-FAST-PATH", "COGNITIVE"})
RATIFIED_GROUNDS = frozenset({"TRANSPORT", "SAFETY", "EXECUTOR-FAST-PATH"})  # the 18 that may return early

# `_bypass_journal(...)` invocation — matches either single- or multi-line calls
_BJ_RE = re.compile(
    r'_bypass_journal\s*\([^)]*?'
    r'backend\s*=\s*"([^"]+)"[^)]*?'
    r'handler_class\s*=\s*"([^"]+)"[^)]*?'
    r'line\s*=\s*(\d+)',
    re.DOTALL,
)


_passed = _failed = 0


def ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, detail: str = "") -> None:
    global _failed
    _failed += 1
    print(f"  ❌ {label}")
    if detail:
        for line in detail.splitlines():
            print(f"       {line}")


def _read_server() -> tuple[str, list[str]]:
    with open(_SERVER_PY, encoding="utf-8") as f:
        src = f.read()
    return src, src.splitlines()


def _extract_bypass_calls(src: str) -> list[tuple[int, str, str, int]]:
    """Return list of (source_line, backend, class, ratified_line) for every
    `_bypass_journal(...)` call in server.py (excluding the def itself)."""
    calls: list[tuple[int, str, str, int]] = []
    for m in _BJ_RE.finditer(src):
        src_line = src.count("\n", 0, m.start()) + 1
        calls.append((src_line, m.group(1), m.group(2), int(m.group(3))))
    return calls


def _find_line(lines: list[str], needle: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1  # 1-based
    return -1


# ────────────────────────────────────────────────────────────────────────────
# AT-1 — the 31 ratified handlers journal with the ratified tuple
# ────────────────────────────────────────────────────────────────────────────
def at1_ratified_journalled(src: str) -> None:
    calls = _extract_bypass_calls(src)
    tuples = {(b, c, ln) for (_sl, b, c, ln) in calls}
    missing = [t for t in RATIFIED if t not in tuples]
    if missing:
        detail = "\n".join(f"  {b:20s} class={c:20s} line={ln}" for (b, c, ln) in missing)
        fail(f"AT-1 all 31 ratified handlers journalled ({len(RATIFIED)-len(missing)}/{len(RATIFIED)})",
             f"missing:\n{detail}")
        return
    ok(f"AT-1 all {len(RATIFIED)} ratified handlers journalled at their ratified tuple")


# ────────────────────────────────────────────────────────────────────────────
# AT-2 — every _bypass_journal handler_class is one of the four ratified classes
# ────────────────────────────────────────────────────────────────────────────
def at2_only_ratified_classes(src: str) -> None:
    calls = _extract_bypass_calls(src)
    bad = [(sl, b, c, ln) for (sl, b, c, ln) in calls if c not in RATIFIED_CLASSES]
    if bad:
        detail = "\n".join(f"  server.py:{sl}  backend={b}  class={c}  (unratified class label)"
                           for (sl, b, c, _ln) in bad)
        fail(f"AT-2 every _bypass_journal uses a ratified class ({len(calls)-len(bad)}/{len(calls)} clean)",
             detail)
        return
    ok(f"AT-2 all {len(calls)} _bypass_journal calls use a ratified class label")


# ────────────────────────────────────────────────────────────────────────────
# AT-3 — no unratified pre-spine early return in _process_turn
#
# For every `return {` between `def _process_turn(` and the first
# `_spine_run(` call, walk backward up to `_LOOKBACK` non-blank code lines
# looking for a `_bypass_journal(...)` call. Assert:
#   (a) a bypass_journal is present, AND
#   (b) its handler_class is in RATIFIED_GROUNDS (i.e. one of the 18) — a
#       COGNITIVE-classified early return is a routing violation.
# ────────────────────────────────────────────────────────────────────────────
_LOOKBACK = 25  # lines to search backward from a `return` for its bypass_journal

def at3_no_unratified_early_return(src: str, lines: list[str]) -> None:
    fn_start = _find_line(lines, "def _process_turn(", start=0)
    if fn_start < 0:
        fail("AT-3 locate _process_turn", "def _process_turn( not found in server.py")
        return
    spine_line = _find_line(lines, "_spine_run(", start=fn_start)
    if spine_line < 0:
        fail("AT-3 locate _spine_run call", "_spine_run( not found after _process_turn")
        return

    # 1-based line numbers; scan (fn_start, spine_line)
    violations: list[str] = []
    early_returns_checked = 0
    for i in range(fn_start, spine_line - 1):
        line = lines[i]
        if "return {" not in line:
            continue
        early_returns_checked += 1
        # walk back up to _LOOKBACK lines
        found_backend = found_class = None
        found_at = -1
        window_start = max(fn_start - 1, i - _LOOKBACK)
        # accumulate a text window so we can regex multi-line calls
        window_src = "\n".join(lines[window_start:i])
        matches = list(_BJ_RE.finditer(window_src))
        if not matches:
            violations.append(
                f"server.py:{i+1}  return without preceding _bypass_journal within {_LOOKBACK} lines: "
                f"{line.strip()[:90]}"
            )
            continue
        # nearest match (last one in the window)
        last = matches[-1]
        found_backend = last.group(1)
        found_class = last.group(2)
        # offset from window_start
        offset_in_window = window_src.count("\n", 0, last.start())
        found_at = window_start + offset_in_window + 1
        if found_class not in RATIFIED_GROUNDS:
            violations.append(
                f"server.py:{i+1}  return under class={found_class} backend={found_backend} "
                f"(journalled at :{found_at}) — COGNITIVE must ROUTE through spine, not return. "
                f"Reclassify to TRANSPORT/SAFETY/EXECUTOR-FAST-PATH or remove the early return."
            )

    if violations:
        fail(f"AT-3 no unratified pre-spine early return "
             f"({early_returns_checked - len(violations)}/{early_returns_checked} clean)",
             "\n".join(violations))
        return
    ok(f"AT-3 all {early_returns_checked} pre-spine early returns carry a ratified ground "
       f"({sorted(RATIFIED_GROUNDS)})")


# ────────────────────────────────────────────────────────────────────────────
def main() -> int:
    src, lines = _read_server()
    print("Card 0038 — Exception List Ratified · acceptance test")
    print(f"  server.py: {_SERVER_PY}")
    print(f"  ratified handlers: {len(RATIFIED)}  (TRANSPORT 3 + SAFETY 3 + EXECUTOR-FAST-PATH 12 + COGNITIVE 13)")
    print()
    at1_ratified_journalled(src)
    at2_only_ratified_classes(src)
    at3_no_unratified_early_return(src, lines)
    print()
    print(f"Card 0038: {_passed} passed, {_failed} failed")
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
