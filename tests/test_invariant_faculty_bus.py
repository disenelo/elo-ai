"""
tests/test_invariant_faculty_bus.py — Runtime Invariant 6, measured.

docs/architecture/ARCHITECTURAL_PRINCIPLES.md, the constitution:

    6. Faculty Bus — all inter-faculty traffic passes the canonical
       envelope; no faculty injects arbitrary content into another.
       (ADR-0001)

ADR-0001 is marked LAW. core/faculty_bus.py implements it properly: required
id/sender/receiver/priority/payload.type, rejection at the boundary rather
than silent processing, confidence that may only be lowered, an append-only
trace, and a _dropped audit trail. It works.

It has TWO production users — runtime/shadow_capture.py and
runtime/spine/spine.py.

Meanwhile sixteen faculties put content into the shared system prompt by
string concatenation, nowhere near the envelope:

    curiosity_questions · expectation_tracker · intentions · long_term_reader
    novelty_detector · relationship_evolution · spg_observer
    capability_learning · cognitive_authorship · faculty_conflict_detector
    habit_tracker · initiative_faculty · silence_faculty
    relationship_faculty · temporal_state · correction_history

That is inter-faculty traffic. runtime/faculty_conflict_detector.py exists
BECAUSE of it — its docstring says "if two faculties give contradictory
directives into the system prompt simultaneously, and nothing flags the
contradiction... one faculty silently overrides". A conflict detector is the
symptom of an unenforced envelope, not a substitute for one.

The same shape as every other finding in this stack: the component is
correct, and the seam around it is empty. The bus is a working,
law-enforcing envelope that almost nothing passes through.

ROUTING SIXTEEN FACULTIES ONTO THE BUS IS NOT A BUILDER DECISION — it is an
architectural change against a LAW-marked ADR, and it belongs to Board. What
is in scope is making the violation countable and stopping it growing: a
seventeenth bypass now fails here instead of appearing silently.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SERVER = (_ROOT / "server.py").read_text(encoding="utf-8")

# Measured 2026-10-04. May shrink. May not grow.
KNOWN_DIRECT_INJECTORS = 16

_BUS_USERS = ("runtime/shadow_capture.py", "runtime/spine/spine.py")


def _direct_injectors() -> set[str]:
    """Faculties that concatenate a block into the system prompt themselves."""
    return set(re.findall(r"from\s+([a-z_.]+)\s+import\s+[a-z_]+_prompt_block", _SERVER))


# ── The envelope enforces its own law ───────────────────────────────────────

def test_the_bus_rejects_a_confidence_increase():
    """"confidence may only be LOWERED downstream (raised → rejected)"."""
    from core.faculty_bus import make_envelope
    env = make_envelope(sender="a", receiver="b", payload_type="test",
                        body={}, confidence=0.5)
    lowered = env.lower_confidence(0.2)
    assert lowered.confidence == pytest.approx(0.2)
    with pytest.raises(ValueError):
        env.lower_confidence(0.9)


def test_the_bus_keeps_an_audit_trail_of_what_it_dropped():
    """"Missing = rejected at boundary, never silently processed"."""
    from core.faculty_bus import get_bus
    bus = get_bus()
    assert hasattr(bus, "publish")
    assert callable(getattr(bus, "dropped", None)) or hasattr(bus, "_dropped")


# ── The violation, counted ──────────────────────────────────────────────────

def test_the_number_of_faculties_bypassing_the_envelope_does_not_grow():
    """
    The ratchet. A seventeenth faculty may not start injecting into the
    shared prompt without someone deciding that it should.
    """
    found = _direct_injectors()
    assert len(found) <= KNOWN_DIRECT_INJECTORS, (
        f"faculties bypassing the Faculty Bus went from {KNOWN_DIRECT_INJECTORS} "
        f"to {len(found)}: {sorted(found)}"
    )


def test_the_baseline_is_not_fiction():
    """A register that over-counts ratchets nothing."""
    found = _direct_injectors()
    assert len(found) >= 1, "no injectors found — the detector has drifted, not the code"
    assert abs(len(found) - KNOWN_DIRECT_INJECTORS) <= 2, (
        f"baseline {KNOWN_DIRECT_INJECTORS} vs measured {len(found)} — re-measure"
    )


def test_the_bus_still_has_its_production_users():
    """
    If this drops to zero the envelope is dead code and Invariant 6 is
    unimplemented rather than merely unenforced — a different and worse
    finding, which should not arrive quietly.
    """
    alive = [u for u in _BUS_USERS
             if "faculty_bus" in (_ROOT / u).read_text(encoding="utf-8")]
    assert alive, f"nothing uses core.faculty_bus any more (checked {_BUS_USERS})"


def test_the_conflict_detector_is_still_needed_and_still_wired():
    """
    It is the symptom. While sixteen faculties share a prompt with no
    envelope, something has to notice when two of them contradict — so if
    this ever disappears while the bypass count stays up, conflicts go back
    to being invisible.
    """
    assert "faculty_conflict_detector" in _SERVER
