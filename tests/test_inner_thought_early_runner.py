"""
tests/test_inner_thought_early_runner.py — Board ruling 2026-10-06, Option C.

The thought must start before the reply exists and be collected at assembly,
so it can no longer be a rationalisation of a reply already written.

Measured first, because it decided the shape: with the live server up and
three seats working, the generator takes 13-30s for 4-17 tokens. Making the
reply WAIT for that is the option the Board ruled out, so the thought runs
alongside the reply and assembly collects whatever is ready.

No test here touches a live model.
"""
from __future__ import annotations

import threading
import time

import pytest

from faculties.inner_thought import early_runner as er


def _gen(text, *, delay=0.0):
    def _g():
        if delay:
            time.sleep(delay)
        return text
    return _g


# ── it starts before there is a reply ───────────────────────────────────────

def test_start_needs_only_what_was_asked():
    """
    The signature is the fix. There is no reply parameter because at the
    moment this runs there is no reply — which is why the thought cannot
    rationalise one.
    """
    import inspect
    params = set(inspect.signature(er.start).parameters)
    assert params == {"asked", "history", "generator"}
    assert "reply" not in params and "response" not in params


def test_nothing_asked_means_no_handle():
    assert er.start("", generator=_gen("x")) is None
    assert er.start("   ", generator=_gen("x")) is None


# ── it does not block the reply ─────────────────────────────────────────────

def test_a_slow_thought_does_not_hold_the_turn():
    h = er.start("do you remember pinkie and the brain",
                 generator=_gen("too slow", delay=2.0))
    t0 = time.time()
    out = h.collect(timeout_s=0.05)
    waited = time.time() - t0

    assert out == ""
    assert waited < 0.5, (
        f"assembly blocked {waited:.2f}s on a thought — the Board ruled out "
        "adding latency to every turn"
    )


def test_work_done_in_parallel_is_still_collected():
    """The whole point: the thought was forming while the reply was written."""
    h = er.start("hello", generator=_gen("i noticed the hesitation", delay=0.05))
    time.sleep(0.15)                       # the reply takes longer than this
    assert h.collect(timeout_s=0.05) == "i noticed the hesitation"


def test_a_ready_thought_needs_no_wait_at_all():
    h = er.start("hello", generator=_gen("already here"))
    time.sleep(0.05)
    t0 = time.time()
    assert h.collect(timeout_s=0.3) == "already here"
    assert time.time() - t0 < 0.1


# ── a late thought never lands on the next turn ─────────────────────────────

def test_collect_consumes_so_a_late_thought_cannot_reappear():
    h = er.start("hello", generator=_gen("late", delay=0.4))
    assert h.collect(timeout_s=0.01) == ""
    time.sleep(0.5)                        # it finishes after the turn shipped
    assert h.collect(timeout_s=0.3) == "", (
        "a thought that missed its turn was attached to a later one"
    )


def test_collecting_twice_does_not_repeat_the_thought():
    h = er.start("hello", generator=_gen("once"))
    time.sleep(0.05)
    assert h.collect(timeout_s=0.3) == "once"
    assert h.collect(timeout_s=0.3) == ""


# ── failures are never the turn's problem ───────────────────────────────────

def test_a_raising_generator_is_absorbed():
    def _boom():
        raise RuntimeError("ollama down")
    h = er.start("hello", generator=_boom)
    time.sleep(0.05)
    assert h.collect(timeout_s=0.3) == ""


def test_collect_tolerates_no_handle():
    assert er.collect(None) == ""


def test_the_thread_is_a_daemon_so_it_cannot_hold_shutdown():
    h = er.start("hello", generator=_gen("x", delay=5.0))
    assert h._thread is not None and h._thread.daemon


def test_nothing_leaks_into_the_main_thread():
    before = threading.active_count()
    h = er.start("hello", generator=_gen("x"))
    h.collect(timeout_s=0.3)
    time.sleep(0.05)
    assert threading.active_count() <= before + 1
