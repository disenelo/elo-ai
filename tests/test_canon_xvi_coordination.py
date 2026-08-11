"""
tests/test_canon_xvi_coordination.py — WO-CANON-XVI: Assemble Before Decide

Assertions (per ADR-Exec-006 / Ruling C 2026-08-10):
  AT-0: UnifiedCognitiveState alias exported from runtime.cognitive_snapshot
  AT-1: assembly happens BEFORE executive in spine.py source (line order)
  AT-2: only one _executive_faculty call per turn in spine.py (no voting)
  AT-3: faculty_bus.get_messages() returns envelopes in priority order
         (critical → high → normal → low) not FIFO insertion order

Run: python3 tests/test_canon_xvi_coordination.py
"""
from __future__ import annotations
import sys, os, uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── AT-0: UnifiedCognitiveState is exported ───────────────────────────────────
try:
    from runtime.cognitive_snapshot import UnifiedCognitiveState, CognitiveSnapshot
    assert UnifiedCognitiveState is CognitiveSnapshot, \
        "UnifiedCognitiveState must alias CognitiveSnapshot"
    # Can instantiate with defaults
    ucs = UnifiedCognitiveState()
    assert hasattr(ucs, "assembled_ts"), "missing assembled_ts field"
    ok("AT-0: UnifiedCognitiveState exported and aliases CognitiveSnapshot")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: assembly line is BEFORE executive line in spine.py source ───────────
try:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _spine_path = os.path.join(_base, "runtime", "spine", "spine.py")
    with open(_spine_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Find first occurrence of assemble_cognitive_state call (not def)
    assembly_line = next(
        (i for i, ln in enumerate(lines, 1)
         if "assemble_cognitive_state(" in ln and "def " not in ln),
        None,
    )
    # Find _executive_faculty call (not def)
    exec_line = next(
        (i for i, ln in enumerate(lines, 1)
         if "_executive_faculty(" in ln and "def " not in ln),
        None,
    )
    assert assembly_line is not None, "assemble_cognitive_state call not found in spine.py"
    assert exec_line is not None,     "_executive_faculty call not found in spine.py"
    assert assembly_line < exec_line, (
        f"assembly (line {assembly_line}) must come BEFORE executive (line {exec_line})"
    )
    ok(f"AT-1: assembly (line {assembly_line}) < executive (line {exec_line}) — ADR-Exec-006 satisfied")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: exactly one _executive_faculty call per turn in spine.py ────────────
try:
    with open(_spine_path, encoding="utf-8") as f:
        src = f.read()
    # Count calls (not definition, not comments)
    call_lines = [
        ln.strip() for ln in src.splitlines()
        if "_executive_faculty(" in ln
        and not ln.strip().startswith("#")
        and "def _executive_faculty" not in ln
    ]
    assert len(call_lines) == 1, (
        f"expected 1 _executive_faculty call, found {len(call_lines)}: {call_lines}"
    )
    ok("AT-2: exactly one _executive_faculty call — no voting")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: faculty_bus.get_messages() delivers in priority order ───────────────
try:
    from core.faculty_bus import FacultyBus, Envelope

    bus = FacultyBus()
    bus.subscribe("test_faculty", None)

    def _env(priority: str) -> Envelope:
        return Envelope(
            id=str(uuid.uuid4()),
            sender="test",
            receiver="test_faculty",
            priority=priority,
            context={"conversation_id": "x", "significance": 0.5,
                     "relationship_state": "neutral",
                     "memory_instruction": {"store": False, "priority": "peripheral"}},
            payload={"type": "test", "data": priority},
            confidence=1.0,
            expires=None,
        )

    # Publish in reverse-priority order so FIFO would deliver low→high
    for p in ("low", "normal", "high", "critical"):
        bus.publish(_env(p))

    msgs = bus.get_messages("test_faculty")
    assert len(msgs) == 4, f"expected 4 messages, got {len(msgs)}"
    priorities = [m.priority for m in msgs]
    assert priorities == ["critical", "high", "normal", "low"], (
        f"wrong delivery order: {priorities}"
    )
    ok("AT-3: get_messages() delivers critical → high → normal → low")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-CANON-XVI coordination   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
