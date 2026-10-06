"""
faculties/inner_thought/early_runner.py — start the thought at the top of the
turn, collect it at assembly.

Board ruling 2026-10-06, Option C: restructure the existing daemon so the
inner thought runs BEFORE response assembly rather than after, keeping the fix
inside Builder 2's lane and out of backend_router.

WHAT WAS WRONG. The daemon ran after the reply was assembled and was handed
that reply as its subject, so every thought was a commentary on a decision
already made. David's log:

    response:      "I don't have that recorded."
    inner_thought: "I am settling into a moment of clarity, acknowledging the
                    reference to Pinkie and the Brain without needing to
                    record it."

The thought knew; the reply denied.

WHY THIS IS CONCURRENT AND NOT MERELY EARLIER. Measured against the live model
with the server up and three seats working:

    long prompt  npredict=96    30707 / 12986 ms   (16 tokens)
    short prompt npredict=40    17847 / 13887 ms   (4-10 tokens)

Four tokens in 17.8 seconds — contention, not generation. Making the reply
WAIT for the thought would put 15-30s on every turn, which is the option the
Board ruled out. So the thought starts the moment David's words are known and
runs alongside the reply's own generation; at assembly it is collected with a
short, bounded wait. Added latency is max(0, thought - reply), usually zero.

WHAT THIS FIXES AND WHAT IT DOES NOT. The thought is generated from what was
ASKED and never sees the reply, so it can no longer be a rationalisation of
it — that is the contradiction closed. It does not condition the reply's
tokens; only a single-pass generation does that, and the Board ruled it out
while three seats are in server.py. Stated plainly so nobody reads more into
this than it does.

Nothing here raises. A thought that does not form is no thought, never a
failed turn.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable

_log = logging.getLogger("elo.inner_thought.early")

# How long assembly will wait if the thought is still in flight. Small on
# purpose: the point is to collect work already done, not to introduce the
# blocking the ruling rejected.
COLLECT_TIMEOUT_S: float = 0.35


class ThoughtInFlight:
    """A thought being formed while the reply is being written."""

    __slots__ = ("_thread", "_result", "_started", "_asked", "_collected")

    def __init__(self, asked: str):
        self._asked = asked
        self._result = ""
        self._started = time.time()
        self._collected = False
        self._thread: threading.Thread | None = None

    # ── internals ────────────────────────────────────────────────────────
    def _run(self, fn: Callable[[], str]) -> None:
        try:
            self._result = str(fn() or "")
        except Exception as e:                     # never surfaces to the turn
            _log.warning("inner thought failed while forming: %s", e)
            self._result = ""

    def _spawn(self, fn: Callable[[], str]) -> None:
        self._thread = threading.Thread(
            target=self._run, args=(fn,), daemon=True,
            name="elo-inner-thought",
        )
        self._thread.start()

    # ── collection ───────────────────────────────────────────────────────
    def collect(self, timeout_s: float | None = None) -> str:
        """
        The thought, if it formed in time. "" otherwise.

        Idempotent: assembly may ask more than once and a late thought is
        never attached to a second turn, because the first collect consumes
        it.
        """
        if self._collected:
            return ""
        wait = COLLECT_TIMEOUT_S if timeout_s is None else float(timeout_s)
        if self._thread is not None:
            self._thread.join(timeout=wait)
            if self._thread.is_alive():
                self._collected = True
                _log.info(
                    "inner thought still forming after %.0fms — turn ships "
                    "without one (asked: %r)",
                    (time.time() - self._started) * 1000, self._asked[:60],
                )
                return ""
        self._collected = True
        if self._result:
            _log.info("inner thought formed in %.0fms",
                      (time.time() - self._started) * 1000)
        return self._result

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self._started) * 1000


def _calm_now() -> bool:
    """
    Is eLo in calm mode this turn?

    Read here rather than passed in, so restoring the calm register costs
    Builder 1's file nothing. Read-only: this never writes blender_state.
    """
    try:
        import json
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            "blender", "blender_state.json",
        )
        with open(path, encoding="utf-8") as f:
            st = json.load(f) or {}
        return bool(st.get("calm_mode")
                    or str((st.get("state") or {}).get("mode", "")) == "calm")
    except Exception:
        return False


def start(asked: str, *, history: str = "", generator: Callable | None = None
          ) -> ThoughtInFlight | None:
    """
    Begin forming the thought. Call this as soon as David's words are known —
    before the reply is generated, which is the entire point.

    Returns None when there is nothing to think about, so the caller can treat
    "no handle" and "no thought" identically.
    """
    asked = str(asked or "").strip()
    if not asked:
        return None

    gen = generator
    if gen is None:
        try:
            from runtime.inner_thought_first import form_thought as _ft
        except Exception as e:                     # pragma: no cover
            _log.warning("inner thought generator unavailable: %s", e)
            return None

        _calm = _calm_now()

        def gen(_a=asked, _h=history, _c=_calm):   # type: ignore[misc]
            # Generous deadline: this is off the critical path, so a slow
            # thought costs nothing. Assembly's own COLLECT_TIMEOUT_S is what
            # protects the turn.
            return _ft(_a, history=_h, calm=_c, deadline_s=20.0)

    handle = ThoughtInFlight(asked)
    handle._spawn(gen)
    return handle


def collect(handle: "ThoughtInFlight | None",
            timeout_s: float | None = None) -> str:
    """Collect from a handle that may be None. Convenience for the call site."""
    if handle is None:
        return ""
    return handle.collect(timeout_s)
