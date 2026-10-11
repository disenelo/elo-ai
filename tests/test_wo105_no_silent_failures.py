"""
tests/test_wo105_no_silent_failures.py — WO-105 lint enforcement.

Rule 1 (WORKING_STANDARD.md): "Absent and broken must never look the same."

Strategy: per-file violation baseline established 2026-10-11 (461 total).
CI fails if:
  1. Any file's violation count INCREASES above its baseline (new silent failure added).
  2. A NEW file (not in baseline) has any violations (new files must start clean).

Pre-existing violations are tolerated (tracked for incremental cleanup).
The baseline may only DECREASE, never increase.

Run: python3 tests/test_wo105_no_silent_failures.py
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.resolve()

# ── directories / files to lint ───────────────────────────────────────────────
_SCAN_PATHS = [
    _ROOT / "runtime",
    _ROOT / "world",
    _ROOT / "faculties",
    _ROOT / "server.py",
]

# ── per-file violation baseline (2026-10-11) ──────────────────────────────────
# Relative paths from repo root. Count may only DECREASE (tightening the rule).
# To reduce: fix violations in the file and update the count downward.
# Never increase a count — that means a new silent failure was introduced.
_BASELINE: dict[str, int] = {
    "server.py": 273,
    "runtime/backend_router.py": 17,
    "runtime/spine/spine.py": 11,
    "runtime/the_moment.py": 10,
    "runtime/executive_context.py": 9,
    "runtime/elo_daemon.py": 9,
    "runtime/prompt_builder.py": 8,
    "world/live_world_state.py": 7,
    "faculties/dream/dream_faculty.py": 7,
    "faculties/inner_thought/life.py": 6,
    "runtime/response_gate.py": 5,
    "runtime/capability_learning.py": 5,
    "runtime/reflection_faculty.py": 4,
    "runtime/cognitive_snapshot.py": 4,
    "faculties/synthesis/observer.py": 4,
    "faculties/learning/faculty.py": 4,
    "faculties/action_agent.py": 4,
    "runtime/session_events.py": 3,
    "runtime/background_drop_watcher.py": 3,
    "faculties/temporal/faculty.py": 3,
    "faculties/metacognition/metacognition.py": 3,
    "faculties/inner_thought/random_fact.py": 3,
    "faculties/curiosity/curiosity_faculty.py": 3,
    "runtime/wkg_faculty.py": 2,
    "runtime/unity_events_cursor.py": 2,
    "runtime/spine/presence_faculty.py": 2,
    "runtime/social_reflex.py": 2,
    "runtime/self_interpret.py": 2,
    "runtime/router/learning_buffer.py": 2,
    "runtime/inner_thought_first.py": 2,
    "runtime/executive_candidates.py": 2,
    "runtime/directed_look.py": 2,
    "runtime/capability_dispatcher.py": 2,
    "runtime/capabilities/health_producer.py": 2,
    "runtime/body_relay.py": 2,
    "faculties/spatial/spatial_faculty.py": 2,
    "faculties/perception/robot_vision_bridge.py": 2,
    "faculties/dream/dream_memory.py": 2,
    "world/navigation.py": 1,
    "runtime/world_delta.py": 1,
    "runtime/voice_rewrite.py": 1,
    "runtime/significance_faculty.py": 1,
    "runtime/session_id.py": 1,
    "runtime/router/pipeline.py": 1,
    "runtime/identity_state_manager.py": 1,
    "runtime/faculty_health.py": 1,
    "runtime/dream_request.py": 1,
    "runtime/dream_latch.py": 1,
    "runtime/creative_vault.py": 1,
    "runtime/claim_gate.py": 1,
    "faculties/window_event_faculty.py": 1,
    "faculties/thread_keeper.py": 1,
    "faculties/personality/personality_evolution_faculty.py": 1,
    "faculties/perception/perception_faculty.py": 1,
    "faculties/music_memory/journal.py": 1,
    "faculties/music_memory/importers/soundcloud.py": 1,
    "faculties/metacognition/deferred_threads.py": 1,
    "faculties/metacognition/correction_capture.py": 1,
    "faculties/inner_thought/working_memory.py": 1,
    "faculties/inner_thought/preprocess.py": 1,
    "faculties/grounding/conversation_tracker.py": 1,
    "faculties/dream/dream_review.py": 1,
    "faculties/dream/dream_input.py": 1,
    "faculties/base_cognition.py": 1,
}


# ── AST visitor ───────────────────────────────────────────────────────────────

class _SilentFailureFinder(ast.NodeVisitor):
    """Finds bare except+pass and except+debug-only handlers."""

    def __init__(self) -> None:
        self.violations: list[tuple[int, str]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        body = node.body
        # bare pass
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            self.violations.append((node.lineno, "bare except+pass"))
        # debug-only swallow
        elif len(body) == 1 and isinstance(body[0], ast.Expr):
            call = body[0].value
            if isinstance(call, ast.Call):
                func = call.func
                is_debug = False
                if isinstance(func, ast.Attribute) and func.attr == "debug":
                    is_debug = True
                elif isinstance(func, ast.Name) and func.id == "debug":
                    is_debug = True
                if is_debug:
                    self.violations.append((node.lineno, "debug-only swallow"))
        self.generic_visit(node)


def _collect_files() -> list[Path]:
    files: list[Path] = []
    for p in _SCAN_PATHS:
        p = Path(p)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(p.rglob("*.py"))
    return sorted(files)


def _count_violations(fpath: Path) -> int:
    if "__pycache__" in str(fpath):
        return 0
    if fpath.name.startswith("test_"):
        return 0
    try:
        src = fpath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    try:
        tree = ast.parse(src, filename=str(fpath))
    except SyntaxError:
        return 0
    finder = _SilentFailureFinder()
    finder.visit(tree)
    return len(finder.violations)


def run_regression_check() -> list[str]:
    """Returns list of regression messages. Empty = pass."""
    regressions: list[str] = []
    for fpath in _collect_files():
        rel = str(fpath.relative_to(_ROOT))
        count = _count_violations(fpath)
        if count == 0:
            continue
        baseline = _BASELINE.get(rel)
        if baseline is None:
            regressions.append(
                f"NEW FILE has {count} silent failure(s): {rel} "
                "(new files must start clean — fix before merging)"
            )
        elif count > baseline:
            regressions.append(
                f"REGRESSION in {rel}: {count} violations (baseline={baseline}) "
                f"— {count - baseline} new silent failure(s) added"
            )
    return regressions


def test_no_silent_failures() -> None:
    regressions = run_regression_check()
    if not regressions:
        return
    lines = ["WO-105 lint FAILED — new silent failures detected:\n"]
    lines.extend(f"  {r}" for r in regressions)
    lines.append(
        "\nFix: upgrade to _log.warning(...) or raise. "
        "See tests/test_wo105_no_silent_failures.py for the baseline and rules."
    )
    raise AssertionError("\n".join(lines))


if __name__ == "__main__":
    regressions = run_regression_check()
    if regressions:
        for r in regressions:
            print(f"FAIL  {r}")
        sys.exit(1)
    else:
        total = sum(_BASELINE.values())
        print(f"OK — no regressions. ({total} pre-existing violations tolerated; reducing over time)")
        sys.exit(0)
