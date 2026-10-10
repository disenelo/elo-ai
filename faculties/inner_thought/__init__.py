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
from faculties.inner_thought.life import AWAKE, RESTING, SLEEP, life_tick
from faculties.inner_thought.preprocess import (
    INJECT_KEY, is_complex, pre_thought,
)
from faculties.inner_thought.random_fact import (
    clear_pending, is_pending, maybe_signal,
)
from faculties.inner_thought.working_memory import (
    WorkingMemory, add_event, as_context, current_project, get_working_memory,
)

__all__ = [
    "start", "collect", "ThoughtInFlight", "COLLECT_TIMEOUT_S",
    # card 0010A — the STATE tier Builder 1's dispatcher reads
    "WorkingMemory", "get_working_memory", "add_event", "as_context",
    "current_project",
    # card 0010B — the beat Builder 1's daemon calls
    "life_tick", "AWAKE", "RESTING", "SLEEP",
    # 2026-10-10 — the pre-processor Builder 1 injects BEFORE generation
    "pre_thought", "is_complex", "INJECT_KEY",
    # WO-B1-0110 — the hand eLo raises; Builder 1 selects and speaks
    "is_pending", "clear_pending", "maybe_signal",
]
