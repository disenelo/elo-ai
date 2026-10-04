"""
tests/test_canon_invariant_count.py — the canon must agree with itself.

docs/architecture/00_CANON_INDEX.md said "the 6 Runtime Invariants".
docs/architecture/ARCHITECTURAL_PRINCIPLES.md lists SEVEN, numbered 1–7, and
closes "Everything else evolves around these seven".
docs/architecture/FOUNDATION_VOLUMES_STATUS_2026-08-10.md also says seven.

Two sources against one. The seventh — Memory Ownership, "one
permanent-memory writer" — was added to the constitution after the index
line was written, and the index was never updated.

Nothing was removed to resolve it. The count was corrected UPWARD, to
include an invariant that already existed and is already cited; the old
value is kept inline in the index as a superseded note, per the project's
append-don't-delete rule.

Why it is worth a test rather than a one-word edit: Memory Ownership is the
invariant that says there is ONE permanent-memory writer, and today two
modules were found writing self/journals/action_reliability.json in
incompatible shapes, plus two producers writing SPG nodes. An invariant
that the index does not even count is an invariant nobody is checking. If
an eighth is added, every statement of the number has to move together or
this fails.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_ARCHIVE = pathlib.Path(__file__).resolve().parent.parent / "docs" / "architecture"
_CONSTITUTION = _ARCHIVE / "ARCHITECTURAL_PRINCIPLES.md"

_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def _constitution_invariants() -> list[str]:
    """The numbered invariants under the Runtime Invariants heading."""
    text = _CONSTITUTION.read_text(encoding="utf-8")
    start = text.index("## Runtime Invariants")
    rest = text[start:]
    end = rest.index("\n## ", 1) if "\n## " in rest[1:] else len(rest)
    return re.findall(r"^(\d+)\. \*\*", rest[:end], re.MULTILINE)


def test_the_constitution_numbers_them_contiguously():
    nums = [int(n) for n in _constitution_invariants()]
    assert nums, "no numbered invariants found — the parser or the file moved"
    assert nums == list(range(1, len(nums) + 1)), nums


def test_the_constitutions_own_closing_line_matches_its_list():
    """"Everything else evolves around these seven." """
    count = len(_constitution_invariants())
    text = _CONSTITUTION.read_text(encoding="utf-8")
    m = re.search(r"evolves around these (\w+)", text)
    assert m, "the constitution no longer states a total in words"
    stated = _WORDS.get(m.group(1).lower())
    assert stated == count, f"list has {count}, closing line says {m.group(1)!r}"


def test_every_document_that_states_the_number_agrees():
    """
    The drift that started this: one doc saying 6 while two said 7. Any
    document naming a count must name the constitution's count.
    """
    count = len(_constitution_invariants())
    wrong = []
    for p in sorted(_ARCHIVE.rglob("*.md")):
        for m in re.finditer(r"(\d+|\w+)\s+Runtime Invariants", p.read_text(encoding="utf-8", errors="ignore")):
            tok = m.group(1).lower()
            n = int(tok) if tok.isdigit() else _WORDS.get(tok)
            if n is not None and n != count:
                wrong.append(f"{p.relative_to(_ARCHIVE)}: says {m.group(1)}")
    assert not wrong, f"constitution has {count} invariants; disagreeing: {wrong}"


def test_memory_ownership_is_one_of_them():
    """
    The seventh, and the one the index was omitting. Named explicitly
    because it is the invariant two of today's defects violated.
    """
    text = _CONSTITUTION.read_text(encoding="utf-8")
    assert re.search(r"^\d+\. \*\*Memory Ownership\*\*", text, re.MULTILINE)


def test_nothing_was_removed_to_make_the_counts_agree():
    """
    Resolved upward. The index keeps its old value as a superseded note
    rather than losing the fact that it once said six.
    """
    index = (_ARCHIVE / "00_CANON_INDEX.md").read_text(encoding="utf-8")
    assert "7 Runtime Invariants" in index
    assert "superseded 2026-10-04" in index
