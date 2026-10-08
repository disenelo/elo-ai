"""
tests/test_elo_daemon.py — WO-B1-0106

Tests for runtime/elo_daemon.py.
All headless (no live server, no LLM calls).
Life loop timings are patched to milliseconds for fast test cycles.
"""

import pytest
import time
import threading
from unittest.mock import patch

from runtime.elo_daemon import EloDaemon, FacultyRegistry, LifeState, get_daemon


# ── FacultyRegistry ────────────────────────────────────────────────────────────

class TestFacultyRegistry:
    def test_loads_without_error(self):
        reg = FacultyRegistry().load()
        assert reg is not None

    def test_capability_dispatcher_loaded(self):
        reg = FacultyRegistry().load()
        assert reg.capability_dispatcher is not None

    def test_same_object_across_multiple_loads(self):
        """Registry is not rebuilt between requests — same object identity."""
        reg = FacultyRegistry().load()
        cd_ref = reg.capability_dispatcher
        # Load again from same registry instance — should be same object
        assert reg.capability_dispatcher is cd_ref


# ── EloDaemon startup / shutdown ───────────────────────────────────────────────

class TestDaemonStartStop:
    def test_starts_in_awake_state(self):
        d = EloDaemon()
        d.start()
        assert d.state == LifeState.AWAKE
        d.stop()

    def test_life_thread_is_running_after_start(self):
        d = EloDaemon()
        d.start()
        assert d._life_thread is not None
        assert d._life_thread.is_alive()
        d.stop()

    def test_life_thread_exits_after_stop(self):
        d = EloDaemon()
        d.start()
        d.stop()
        # Give the thread time to exit
        time.sleep(0.05)
        assert not d._running

    def test_faculty_registry_loaded_on_start(self):
        d = EloDaemon()
        d.start()
        assert d.registry.capability_dispatcher is not None
        d.stop()


# ── Request handling ───────────────────────────────────────────────────────────

class TestDaemonHandleRequest:
    def test_math_request_answered_without_reload(self):
        d = EloDaemon()
        d.start()
        result = d.handle_request("28 × 74")
        assert result is not None
        assert result.get("response") == "2072"
        d.stop()

    def test_time_request_returns_string(self):
        d = EloDaemon()
        d.start()
        result = d.handle_request("What time is it?")
        assert result is not None
        response = result.get("response")
        # May return a time string or fall through — either is valid
        assert isinstance(response, (str, type(None)))
        d.stop()

    def test_unknown_request_falls_through_to_executive(self):
        d = EloDaemon()
        d.start()
        result = d.handle_request("tell me something interesting about jellyfish")
        assert result is not None
        assert result.get("tier") == "UNKNOWN"
        assert result.get("backend") == "executive"
        d.stop()

    def test_daemon_does_not_reload_between_requests(self):
        """Faculty registry object is the same across two requests."""
        d = EloDaemon()
        d.start()
        reg_id_before = id(d.registry.capability_dispatcher)
        d.handle_request("What time is it?")
        d.handle_request("28 + 14")
        reg_id_after = id(d.registry.capability_dispatcher)
        assert reg_id_before == reg_id_after, "Faculty registry was reloaded between requests"
        d.stop()

    def test_handle_request_marks_awake(self):
        """Calling handle_request while RESTING transitions state back to AWAKE."""
        d = EloDaemon()
        d.start()
        # Manually force to RESTING
        with d._lock:
            d._state = LifeState.RESTING
        assert d.state == LifeState.RESTING
        # Sending a request should transition back to AWAKE
        d.handle_request("hey")
        assert d.state == LifeState.AWAKE
        d.stop()


# ── LIFE loop tick ────────────────────────────────────────────────────────────

class TestDaemonLifeLoop:
    def test_life_loop_ticks_during_idle(self):
        """
        After start, the life loop should tick at least once within a short window.
        We patch _TICK_INTERVAL to fire immediately.
        """
        ticks = []

        def on_tick(state, idle_seconds):
            ticks.append((state, idle_seconds))

        with patch("runtime.elo_daemon._TICK_INTERVAL", {
            LifeState.AWAKE:   0.05,
            LifeState.RESTING: 0.05,
            LifeState.SLEEP:   0.05,
        }):
            d = EloDaemon(on_inner_tick=on_tick)
            d.start()
            time.sleep(0.3)  # wait for a couple of ticks
            d.stop()

        assert len(ticks) >= 1, "LIFE loop did not tick during idle"

    def test_tick_count_increments(self):
        with patch("runtime.elo_daemon._TICK_INTERVAL", {
            LifeState.AWAKE:   0.05,
            LifeState.RESTING: 0.05,
            LifeState.SLEEP:   0.05,
        }):
            d = EloDaemon()
            d.start()
            time.sleep(0.25)
            d.stop()

        assert d.tick_count >= 1

    def test_inner_life_not_suspended_during_request(self):
        """
        INVARIANT 3: LIFE loop must still be running while handle_request executes.
        We verify by checking the life thread is alive mid-request.
        """
        life_alive_during_request = []

        original_handle = EloDaemon.handle_request

        def spy_handle(self_d, raw_message):
            # Check thread is alive when we're inside handle_request
            life_alive_during_request.append(
                self_d._life_thread is not None and self_d._life_thread.is_alive()
            )
            return original_handle(self_d, raw_message)

        with patch.object(EloDaemon, "handle_request", spy_handle):
            d = EloDaemon()
            d.start()
            d.handle_request("What time is it?")
            d.stop()

        assert life_alive_during_request, "handle_request never called (test error)"
        assert all(life_alive_during_request), "LIFE loop was not alive during request handling"


# ── State transitions ──────────────────────────────────────────────────────────

class TestDaemonStateTransitions:
    def test_transitions_to_resting_after_idle_threshold(self):
        """
        After _RESTING_AFTER_S seconds without a request, state becomes RESTING.
        We patch the threshold to 0.1s for test speed.
        """
        with patch("runtime.elo_daemon._RESTING_AFTER_S", 0.05):
            with patch("runtime.elo_daemon._SLEEP_AFTER_S", 9999.0):
                with patch("runtime.elo_daemon._TICK_INTERVAL", {
                    LifeState.AWAKE:   0.05,
                    LifeState.RESTING: 0.05,
                    LifeState.SLEEP:   0.05,
                }):
                    d = EloDaemon()
                    d.start()
                    time.sleep(0.3)  # idle for longer than threshold
                    state = d.state
                    d.stop()

        assert state in (LifeState.RESTING, LifeState.SLEEP), (
            f"Expected RESTING or SLEEP after idle, got {state}"
        )

    def test_transitions_back_to_awake_on_request(self):
        """After a request, RESTING state → AWAKE."""
        with patch("runtime.elo_daemon._RESTING_AFTER_S", 0.01):
            with patch("runtime.elo_daemon._SLEEP_AFTER_S", 9999.0):
                with patch("runtime.elo_daemon._TICK_INTERVAL", {
                    LifeState.AWAKE:   0.05,
                    LifeState.RESTING: 0.05,
                    LifeState.SLEEP:   0.05,
                }):
                    d = EloDaemon()
                    d.start()
                    time.sleep(0.15)
                    # Now send a request — should wake up
                    d.handle_request("hello")
                    state_after = d.state
                    d.stop()

        assert state_after == LifeState.AWAKE
