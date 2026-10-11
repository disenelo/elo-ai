"""
runtime/elo_daemon.py — WO-B1-0106

eLo Persistent Daemon — load once, stay alive, respond to events.

Current architecture:
    start Python → load eLo → process → exit

Target:
    eLo daemon (stays alive)
      ├── Kernel            (identity_kernel — immutable singleton)
      ├── State             (AWAKE / RESTING / SLEEP)
      ├── Memory cache      (working_memory, WKG)
      ├── Faculty registry  (capability_dispatcher, system_primitives)
      ├── System adapters   (blender_state.json reader)
      └── Event bus         (tick events, request events)

David's request is an event occurring inside eLo's life — not the thing that
creates eLo's existence. [SPEC SOURCE_ELO-CONTINUOUS-IDENTITY_2026-10-08.md]

LIFE LOOP states:
  AWAKE   — David is present (active conversation)
  RESTING — No active conversation; inner_thought ticking slowly
  SLEEP   — Extended idle; dreaming/consolidation

THRESHOLDS — confirmed [DAVID 2026-10-09]:
  AWAKE → RESTING : 5 minutes since last request
  RESTING → SLEEP : 20 minutes in RESTING state
"""
from __future__ import annotations

import logging
import signal
import threading
import time
from enum import Enum
from typing import Any, Callable

_log = logging.getLogger(__name__)

# ── LIFE LOOP state ────────────────────────────────────────────────────────────

class LifeState(str, Enum):
    AWAKE   = "AWAKE"
    RESTING = "RESTING"
    SLEEP   = "SLEEP"


# Confirmed [DAVID 2026-10-09]
_RESTING_AFTER_S: float = 5 * 60    # seconds idle before AWAKE → RESTING
_SLEEP_AFTER_S: float   = 20 * 60   # seconds in RESTING before → SLEEP

# Inner-thought tick intervals by state (slower when resting/sleeping)
_TICK_INTERVAL: dict[LifeState, float] = {
    LifeState.AWAKE:   30.0,   # tick every 30s while David is present
    LifeState.RESTING: 120.0,  # tick every 2 min while resting
    LifeState.SLEEP:   300.0,  # tick every 5 min while sleeping
}


# ── Faculty registry ───────────────────────────────────────────────────────────

class FacultyRegistry:
    """
    Loaded once at daemon startup. Holds references to all faculty modules.
    The same object is used across every request — no reload, no reconstruction.
    """
    def __init__(self) -> None:
        self._loaded_at   = time.time()
        self._capability_dispatcher = None
        self._system_primitives     = None
        self._working_memory        = None

    def load(self) -> "FacultyRegistry":
        try:
            from runtime import capability_dispatcher as _cd
            self._capability_dispatcher = _cd
        except ImportError:
            _log.warning("capability_dispatcher not available")

        try:
            from tools import system_primitives as _sp
            self._system_primitives = _sp
        except ImportError:
            pass  # B3-0007 not yet delivered — graceful

        try:
            from runtime.working_memory import WorkingMemory as _WM
            self._working_memory = _WM()
        except Exception:
            pass  # B2-0010 not yet delivered — graceful

        return self

    @property
    def capability_dispatcher(self):
        return self._capability_dispatcher

    @property
    def system_primitives(self):
        return self._system_primitives

    @property
    def working_memory(self):
        return self._working_memory


# ── Daemon ─────────────────────────────────────────────────────────────────────

class EloDaemon:
    """
    Long-running eLo process host.

    Startup:
        daemon = EloDaemon()
        daemon.start()

    Request handling (replaces per-request reload):
        result = daemon.handle_request(raw_user_message)

    Shutdown (SIGTERM or explicit):
        daemon.stop()

    The daemon never suspends the LIFE loop during request handling (INVARIANT 3).
    """

    def __init__(
        self,
        on_inner_tick: Callable[[LifeState, float], None] | None = None,
    ) -> None:
        """
        Args:
            on_inner_tick: optional callback for each LIFE loop tick.
                           Receives (current_state, time_since_last_request).
                           Used by tests and by ambient_engine integration.
        """
        self._state             = LifeState.AWAKE
        self._last_request_ts   = time.time()
        self._resting_since_ts  = 0.0
        self._on_inner_tick     = on_inner_tick
        self._registry          = FacultyRegistry()
        self._running           = False
        self._life_thread: threading.Thread | None = None
        self._lock              = threading.Lock()
        self._tick_count        = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self) -> "EloDaemon":
        """Load faculties, wire signal handler, start LIFE loop."""
        _log.info("eLo daemon starting — loading faculties")
        self._registry.load()

        # Wire SIGTERM for graceful shutdown
        try:
            signal.signal(signal.SIGTERM, self._handle_sigterm)
        except (OSError, ValueError):
            pass  # non-main-thread context (tests) — skip signal

        self._running = True
        self._life_thread = threading.Thread(
            target=self._life_loop,
            name="eLo-life-loop",
            daemon=True,
        )
        self._life_thread.start()
        _log.info("eLo daemon ready — LIFE loop running")
        return self

    def stop(self, *, reason: str = "explicit stop") -> None:
        """Flush pending writes, checkpoint state, stop LIFE loop."""
        _log.info("eLo daemon stopping: %s", reason)
        self._running = False
        self._flush_vault_writes()
        self._checkpoint_state()
        if self._life_thread and self._life_thread.is_alive():
            self._life_thread.join(timeout=2.0)
        _log.info("eLo daemon stopped cleanly")

    def handle_request(self, raw_message: str) -> dict[str, Any]:
        """
        Route a user message through the capability_dispatcher without reloading.

        INVARIANT 3: The LIFE loop continues in its background thread throughout
        this call. We do not pause or join the life thread here.

        Returns a result dict with at minimum {"response": str, "state": LifeState}.
        """
        self._mark_awake()

        cd = self._registry.capability_dispatcher
        if cd is None:
            return {"response": "", "state": self._state, "backend": "unavailable"}

        try:
            tier = cd.classify(raw_message)

            if tier == cd.TIER_FACT:
                fact = cd.dispatch_fact(raw_message)
                if fact and fact.get("value") is not None:
                    return {
                        "response": str(fact["value"]),
                        "state":    self._state,
                        "tier":     tier,
                        "backend":  "capability_dispatcher",
                        "authority": fact.get("authority", "definitive"),
                    }

            if tier == cd.TIER_STATE:
                state_result = cd.dispatch_state(raw_message)
                if state_result and state_result.get("value") is not None:
                    return {
                        "response": str(state_result["value"]),
                        "state":    self._state,
                        "tier":     tier,
                        "backend":  "capability_dispatcher",
                        "authority": state_result.get("authority", "recorded"),
                    }
        except Exception as exc:
            _log.debug("capability_dispatcher error: %s", exc)

        # Fall through — return UNKNOWN for executive to handle
        return {
            "response": None,
            "state":    self._state,
            "tier":     "UNKNOWN",
            "backend":  "executive",
        }

    # ── State management ───────────────────────────────────────────────────────

    @property
    def state(self) -> LifeState:
        return self._state

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def registry(self) -> FacultyRegistry:
        return self._registry

    def status(self) -> dict[str, Any]:
        # Snapshot for callers that need to gate behaviour on idle time —
        # notably ambient_engine's dream-intent trigger, which must not fire
        # while David is actively in conversation.
        with self._lock:
            return {
                "state":            self._state.value,
                "last_request_ts":  self._last_request_ts,
                "resting_since_ts": self._resting_since_ts,
                "tick_count":       self._tick_count,
                "running":          self._running,
            }

    def _mark_awake(self) -> None:
        with self._lock:
            prev_state = self._state
            self._last_request_ts = time.time()
            if self._state == LifeState.SLEEP:
                # STIRRING beat [DAVID 2026-10-09]: ease back via RESTING, not instant jump.
                # Fire one inner_thought tick at RESTING rate before transitioning to AWAKE.
                _log.info("eLo life state → STIRRING (SLEEP → RESTING → AWAKE)")
                self._state = LifeState.RESTING
                self._resting_since_ts = 0.0
                threading.Thread(
                    target=self._stirring_beat,
                    name="eLo-stirring",
                    daemon=True,
                ).start()
            elif self._state != LifeState.AWAKE:
                _log.info("eLo life state → AWAKE (request received from %s)", prev_state.value)
                self._state = LifeState.AWAKE
                self._resting_since_ts = 0.0

    def _stirring_beat(self) -> None:
        """STIRRING beat: fire one life_tick at RESTING pace, then ease to AWAKE."""
        try:
            from faculties.inner_thought import life_tick as _life_tick, RESTING as _RESTING
            _life_tick(_RESTING)
        except Exception:
            pass
        finally:
            with self._lock:
                if self._state == LifeState.RESTING:
                    _log.info("eLo life state → AWAKE (STIRRING complete)")
                    self._state = LifeState.AWAKE
                    self._resting_since_ts = 0.0

    def _compute_next_state(self, now: float) -> LifeState:
        idle = now - self._last_request_ts
        if idle < _RESTING_AFTER_S:
            return LifeState.AWAKE
        if self._resting_since_ts == 0.0:
            return LifeState.RESTING
        resting_for = now - self._resting_since_ts
        if resting_for >= _SLEEP_AFTER_S:
            return LifeState.SLEEP
        return LifeState.RESTING

    # ── LIFE loop ──────────────────────────────────────────────────────────────

    def _life_loop(self) -> None:
        """Background thread — ticks inner_thought at intervals tuned by state."""
        _log.debug("LIFE loop started")
        while self._running:
            now       = time.time()
            new_state = self._compute_next_state(now)
            with self._lock:
                if new_state != self._state:
                    _log.info("eLo life state → %s", new_state.value)
                    if new_state == LifeState.RESTING and self._state == LifeState.AWAKE:
                        self._resting_since_ts = now
                    elif new_state == LifeState.AWAKE:
                        self._resting_since_ts = 0.0
                    self._state = new_state

            self._tick(new_state, now - self._last_request_ts)
            time.sleep(_TICK_INTERVAL.get(new_state, 60.0))

        _log.debug("LIFE loop exited")

    def _tick(self, state: LifeState, idle_seconds: float) -> None:
        """One LIFE loop tick — fire inner_thought if available, call on_inner_tick."""
        self._tick_count += 1
        _log.debug("LIFE tick #%d state=%s idle=%.0fs", self._tick_count, state.value, idle_seconds)

        # inner_thought tick — B2-0010 (life_tick contract: never raises, returns {state,ok,actions,elapsed_ms})
        try:
            from faculties.inner_thought import life_tick as _life_tick
            _life_tick(state.value)
        except Exception:
            pass  # B2-0010 not yet delivered — silent

        if self._on_inner_tick:
            try:
                self._on_inner_tick(state, idle_seconds)
            except Exception:
                pass

    # ── Graceful shutdown ──────────────────────────────────────────────────────

    def _handle_sigterm(self, signum, frame) -> None:
        _log.info("SIGTERM received — initiating graceful shutdown")
        self.stop(reason="SIGTERM")

    def _flush_vault_writes(self) -> None:
        """Flush any pending vault/WKG writes before exit."""
        try:
            from memory.vault_layer import flush_pending as _flush
            _flush()
        except Exception:
            pass

    def _checkpoint_state(self) -> None:
        """Checkpoint life state to disk for warm restart."""
        try:
            import json, os
            checkpoint = {
                "life_state":       self._state.value,
                "last_request_ts":  self._last_request_ts,
                "resting_since_ts": self._resting_since_ts,
                "tick_count":       self._tick_count,
                "ts":               time.time(),
            }
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "blender", "elo_daemon_checkpoint.json",
            )
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)
            os.replace(tmp, path)
            _log.info("daemon checkpoint written to %s", path)
        except Exception as exc:
            _log.debug("checkpoint write failed: %s", exc)


# ── Module singleton ───────────────────────────────────────────────────────────
# Callers can use the shared daemon if running inside the same process,
# or instantiate their own for tests.

_daemon: EloDaemon | None = None


def get_daemon() -> EloDaemon:
    """Return the module-level daemon singleton (creates + starts if needed)."""
    global _daemon
    if _daemon is None:
        _daemon = EloDaemon()
        _daemon.start()
    return _daemon
