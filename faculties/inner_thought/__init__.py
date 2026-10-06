"""
faculties/inner_thought — eLo's inner thought, Builder 2's lane.

early_runner starts the thought at the top of the turn and collects it at
assembly (Board ruling 2026-10-06, Option C). The generation itself lives in
runtime/inner_thought_first.py and the quality standard in
runtime/inner_thought_quality.py; both predate this package and are left where
they are rather than moved, because runtime/server.py already imports the
quality gate and moving a file it imports is a change to Builder 1's file.
"""
from faculties.inner_thought.early_runner import (
    COLLECT_TIMEOUT_S, ThoughtInFlight, collect, start,
)

__all__ = ["start", "collect", "ThoughtInFlight", "COLLECT_TIMEOUT_S"]
