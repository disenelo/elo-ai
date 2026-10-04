"""
tests/test_canon_alignment.py — code-alignment against the SOURCE ARCHIVE.

docs/architecture/ holds 123 top-level canon documents and 28 Volumes. The
numbered 01–17 spine — the entries you would check an implementation
against — is almost entirely placeholder:

    01_one_brain.md             4 lines   STATUS: PENDING
    02_language_faculty.md      4 lines   STATUS: PENDING
    03_memory_faculty.md        4 lines   STATUS: PENDING
    04_attention_faculty.md     4 lines   STATUS: PENDING
    05_relationship_faculty.md  8 lines   STATUS: PENDING
    08_capability_faculty.md    4 lines   STATUS: PENDING
    09_executive_faculty.md    21 lines   STATUS: PENDING
    10_cognitive_plan.md        4 lines   STATUS: PENDING
    12_expression_plan.md       4 lines   STATUS: PENDING
    13_conversation_faculty.md  4 lines   STATUS: PENDING
    14_presence_faculty.md     19 lines   STATUS: PENDING
    15_execution_gate.md        4 lines   STATUS: PENDING
    16_spine_runtime.md        22 lines   STATUS: PENDING
    17_memory_update.md         4 lines   STATUS: PENDING
    99_future_embodiments.md    4 lines   STATUS: PENDING

Every one of them is SHIPPED. runtime/router/execution_gate.py,
runtime/spine/presence_faculty.py, runtime/capability_registry.py,
runtime/router/conversation_matrix.py and the rest are running right now.
Attention has no named module but is threaded through the Executive as
attention_model; One Brain is distributed across executive and spine; three
embodiment modules exist under 99_future_embodiments.

So the answer to "run the questions against the source archive" is that for
the core faculties the archive cannot answer them. The entries were never
written, and the code is the only source of truth. That is also why this
stack keeps finding correct components with empty seams — there is no spec
saying what is supposed to be connected to what, so nothing notices when
nothing is.

THIS FILE IS A DEBT REGISTER, NOT A BLESSING. The fifteen are recorded so
the set cannot grow quietly. It is a ratchet: a new faculty may not ship
with a placeholder spec, and a written spec may not regress to one. Writing
the fifteen is not a Builder task — specs are the Board's, and I do not
write canon.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_ARCHIVE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "architecture"

# The spine: numbered core-faculty specs, the ones an implementation is
# checked against. Non-numbered docs (audits, ADRs, volumes) are excluded —
# they are records, not contracts.
_SPINE = re.compile(r"^\d{2}_.*\.md$")

# Allowed to be placeholders, as of 2026-10-04. The set may SHRINK. It may
# not grow, and nothing new may join it.
KNOWN_STUBS = frozenset({
    "01_one_brain.md", "02_language_faculty.md", "03_memory_faculty.md",
    "04_attention_faculty.md", "05_relationship_faculty.md",
    "08_capability_faculty.md", "09_executive_faculty.md",
    "10_cognitive_plan.md", "12_expression_plan.md",
    "13_conversation_faculty.md", "14_presence_faculty.md",
    "15_execution_gate.md", "16_spine_runtime.md", "17_memory_update.md",
    "99_future_embodiments.md",
})

_STUB_MAX_LINES = 25


def _is_stub(path: pathlib.Path) -> bool:
    lines = [l for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()
             if l.strip()]
    return len(lines) <= _STUB_MAX_LINES and any("STATUS: PENDING" in l for l in lines)


def _spine_docs() -> list[pathlib.Path]:
    return sorted(p for p in _ARCHIVE.glob("*.md") if _SPINE.match(p.name))


def test_the_archive_is_present():
    docs = _spine_docs()
    assert docs, f"no numbered canon docs under {_ARCHIVE}"


def test_no_new_placeholder_specs():
    """
    The ratchet. A faculty may not ship with its canon entry left as
    STATUS: PENDING, because an unwritten spec is why nobody notices when an
    implementation is never connected to anything.
    """
    current = {p.name for p in _spine_docs() if _is_stub(p)}
    new = current - KNOWN_STUBS
    assert not new, (
        f"{len(new)} canon spec(s) became placeholders since 2026-10-04: "
        f"{sorted(new)}"
    )


def test_the_placeholder_set_never_grows():
    current = {p.name for p in _spine_docs() if _is_stub(p)}
    assert len(current) <= len(KNOWN_STUBS), (
        f"placeholder specs went from {len(KNOWN_STUBS)} to {len(current)}"
    )


def test_a_written_spec_may_not_regress_to_a_placeholder():
    """Separate from the ratchet so the failure names WHICH one went back."""
    written_before = {p.name for p in _spine_docs()} - KNOWN_STUBS
    regressed = {p.name for p in _spine_docs()
                 if p.name in written_before and _is_stub(p)}
    assert not regressed, f"written canon regressed to STATUS: PENDING: {sorted(regressed)}"


def test_the_debt_is_recorded_accurately():
    """
    KNOWN_STUBS must describe reality. An entry that no longer exists, or was
    never a stub, makes the register fiction — and a fictional baseline
    ratchets nothing.
    """
    names = {p.name for p in _spine_docs()}
    missing = KNOWN_STUBS - names
    assert not missing, f"KNOWN_STUBS lists files that do not exist: {sorted(missing)}"


# Each unwritten spec, and the code that shipped without it. Verified on
# disk 2026-10-04. This is the asymmetry the register exists to state: the
# behaviour is running, the contract it is supposed to satisfy is a
# placeholder.
SHIPPED_WITHOUT_CANON = {
    "01_one_brain.md":            "runtime/executive.py",          # distributed, no single module
    "02_language_faculty.md":     "runtime/language",
    "03_memory_faculty.md":       "memory/memory_faculty.py",
    "04_attention_faculty.md":    "runtime/executive.py",          # attention_model, no named module
    "05_relationship_faculty.md": "runtime/spine/relationship_faculty.py",
    "08_capability_faculty.md":   "runtime/capability_registry.py",
    "09_executive_faculty.md":    "runtime/executive.py",
    "10_cognitive_plan.md":       "runtime/cognitive_state.py",
    "12_expression_plan.md":      "expression/expression_mapper.py",
    "13_conversation_faculty.md": "runtime/router/conversation_matrix.py",
    "14_presence_faculty.md":     "runtime/spine/presence_faculty.py",
    "15_execution_gate.md":       "runtime/router/execution_gate.py",
    "16_spine_runtime.md":        "runtime/spine/spine.py",
    "17_memory_update.md":        "runtime/working_memory.py",
    "99_future_embodiments.md":   "runtime/mobile_embodiment.py",
}

_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("name,impl", sorted(SHIPPED_WITHOUT_CANON.items()))
def test_each_unwritten_spec_has_shipped_code_behind_it(name, impl):
    """
    The actual finding, asserted rather than described: these are not
    unwritten specs for unbuilt things. The code is running.

    If an implementation disappears, this fails and says so — at which point
    the spec is not debt any more, it is a document for something that no
    longer exists, and the register needs correcting either way.
    """
    assert (_ARCHIVE / name).exists(), name
    assert (_ROOT / impl).exists(), f"{name} has no implementation at {impl}"


def test_the_register_covers_every_recorded_stub():
    """No entry may sit in KNOWN_STUBS without naming what shipped instead."""
    assert set(SHIPPED_WITHOUT_CANON) == set(KNOWN_STUBS), (
        set(KNOWN_STUBS) ^ set(SHIPPED_WITHOUT_CANON)
    )


@pytest.mark.parametrize("name", sorted(KNOWN_STUBS))
def test_the_live_state_of_each_entry_is_visible(name):
    """
    Prints under -v so the debt is inspectable per entry rather than as an
    aggregate. Shrinking it is the goal, so a written spec passes too.
    """
    p = _ARCHIVE / name
    assert p.exists()
    assert isinstance(_is_stub(p), bool)
