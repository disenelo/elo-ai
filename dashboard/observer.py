"""
dashboard/observer.py — Kernel decision observer.

Subclasses CognitiveDebugger and replaces the module-level instance
so every kernel decision cycle pushes a structured event to the bus.

No kernel source file is modified.
The swap is performed by install() which sets core.kernel._cognitive_debugger.
"""

import core.kernel as _kernel
from core.kernel import CognitiveDebugger
from dashboard.event_bus import build_event, push


class DashboardObserver(CognitiveDebugger):
    """
    Extends CognitiveDebugger to push structured events to the dashboard bus.

    Called automatically by core.kernel.cognitive_debug_snapshot() on every
    kernel decision cycle — no kernel source changes required.
    """

    def emit(
        self,
        user_input:     str,
        classification: dict,
        assembled:      dict,
        mode:           str,
        routing_reason: str,
    ):
        # push structured event — the only output the dashboard needs
        event = build_event(user_input, classification, assembled, mode, routing_reason)
        push(event)
        # parent.emit() intentionally NOT called: formatted stdout block
        # is replaced by the JSON stream. Responses remain clean.


# ── installation ───────────────────────────────────────────────────────────────

_installed = False


def install():
    """
    Replace the kernel's module-level CognitiveDebugger instance with
    DashboardObserver. Idempotent — safe to call multiple times.

    Must be called before the first decide_response() turn.
    Kernel source file is NOT modified.
    """
    global _installed
    if _installed:
        return

    # enable the cognitive debug path so emit() is called on every turn
    _kernel._cognitive_debugger = DashboardObserver()
    _kernel._cognitive_debugger.enabled = True   # always on for dashboard

    _installed = True


def uninstall():
    """Restore the default CognitiveDebugger (disables dashboard observation)."""
    global _installed
    _kernel._cognitive_debugger = CognitiveDebugger()
    _installed = False
