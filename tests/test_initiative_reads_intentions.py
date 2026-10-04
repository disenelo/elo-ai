"""
tests/test_initiative_reads_intentions.py — two modules, one concept, two files.

IS ELO: — Intentions & Continuity / One Brain?
    "a system capable of retaining unfinished threads?"
    "can two different systems write contradictory state?"

memory/intentions.py OWNS intentions: data/intentions.json, a JSON array of
records, five statuses (ACTIVE, DEFERRED, RESUMED, COMPLETED, ABANDONED),
and the API hold/defer/resume/complete/abandon/open_intentions.

runtime/initiative_faculty.py read self/intentions.jsonl instead, with its
own JSONL parser. Three mismatches, not one:

  path     self/intentions.jsonl   vs   data/intentions.json
  format   one JSON object a line  vs   a JSON array
  status   checks "PAUSED", which is not one of the five, and never checks
           RESUMED — so an intention eLo picked back up was invisible

Neither file exists, so both read nothing and the disagreement never
surfaced. It would have surfaced the moment anything wrote one.

Fixed by reading through the owning module. Same shape as routing
spg_faculty's claims read through wkg_faculty.all_claims(): one accessor,
one answer, and the format and status vocabulary come free because the
owner handles them.

SEPARATELY, AND NOT FIXED HERE: memory.intentions.hold() — the only writer
— has ZERO production callers. Nothing in the running system ever holds an
intention, which is why no store exists. Deciding WHEN eLo should hold one
is Executive policy and belongs to Board, not to a plumbing fix.
"""
from __future__ import annotations

import pytest

import memory.intentions as intentions
import runtime.initiative_faculty as inf


@pytest.fixture
def _store(tmp_path, monkeypatch):
    monkeypatch.setattr(intentions, "_STORE", tmp_path / "intentions.json")
    return tmp_path


# ── One accessor ────────────────────────────────────────────────────────────

def test_an_active_intention_reaches_the_initiative_faculty(_store):
    intentions.hold("finish the seam audit", context="work")
    active, deferred = inf._read_intentions_safe()
    assert "finish the seam audit" in active
    assert deferred == []


def test_a_deferred_intention_is_read_as_deferred(_store):
    i = intentions.hold("call the supplier")
    intentions.defer(i.intention_id, reason="waiting on David")
    active, deferred = inf._read_intentions_safe()
    assert "call the supplier" in deferred
    assert active == []


def test_a_resumed_intention_is_active_again(_store):
    """
    RESUMED was invisible: the old reader checked only ACTIVE, DEFERRED and
    "PAUSED". An intention eLo had deliberately picked back up counted as
    nothing.
    """
    i = intentions.hold("rewire the dream trigger")
    intentions.defer(i.intention_id, reason="blocked")
    intentions.resume(i.intention_id)
    active, deferred = inf._read_intentions_safe()
    assert "rewire the dream trigger" in active, (active, deferred)


@pytest.mark.parametrize("finish", ["complete", "abandon"])
def test_a_closed_intention_is_neither_active_nor_deferred(_store, finish):
    i = intentions.hold("ship the addon")
    getattr(intentions, finish)(i.intention_id)
    active, deferred = inf._read_intentions_safe()
    assert "ship the addon" not in active + deferred


def test_an_empty_store_is_simply_empty(_store):
    assert inf._read_intentions_safe() == ([], [])


# ── No second path ──────────────────────────────────────────────────────────

def _code_only(module) -> str:
    """
    Module source with comments AND docstrings removed.

    Stripping only `#` lines is not enough: the docstring here EXPLAINS the
    old path and the bogus "PAUSED" status, and a substring scan reads that
    prose as the behaviour. Third time that has caught me today, so this
    goes through the AST rather than line filtering.
    """
    import ast
    from pathlib import Path
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def test_the_faculty_keeps_no_intentions_path_of_its_own():
    code = _code_only(inf)
    assert "intentions.jsonl" not in code, "a second intentions path survives"
    assert "memory.intentions" in code


def test_it_uses_the_owners_status_vocabulary():
    """"PAUSED" is not one of the five statuses and never was."""
    assert "PAUSED" not in _code_only(inf)


# ── Causal ──────────────────────────────────────────────────────────────────

def test_holding_an_intention_changes_what_initiative_sees(_store):
    before = inf._read_intentions_safe()
    intentions.hold("build the scoring function")
    after = inf._read_intentions_safe()
    assert before == ([], []) and after != before
