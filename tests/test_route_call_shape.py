"""
tests/test_route_call_shape.py — two call sites used route() wrongly in three ways at once.

runtime.backend_router.route is:

    route(system_prompt: str, user_input: str, ...) -> tuple[str, str]

26 of its 27 return statements return a tuple. Two call sites in server.py
called it as `_rt(_ab(), msgs)`:

  1. the BACKEND NAME passed where the system prompt goes
  2. a message LIST passed where a string is expected
  3. the (text, backend) tuple used as if it were text

Measured, not inferred — the dream's llm closure called exactly as server.py
defined it:

    AttributeError: 'list' object has no attribute 'lower'

raised inside _detect_model_override(user_input). dream_faculty documents
llm_fn as "callable(messages: list[dict]) -> str" and wraps the call in
`except Exception`, so the failure was swallowed and the dream fell through
to its deterministic fallback:

    "eLo drifts through something that feels like moon..."

EVERY dream has been the stub. Never once the LLM. The same closure shape
sat in the ambient brain-utterance path, inside a try spanning lines
1004-1490, so it failed the same way and just as quietly.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

import runtime.backend_router as br

_SERVER = (pathlib.Path(__file__).resolve().parent.parent / "server.py").read_text(encoding="utf-8")


def _code_only() -> str:
    return "\n".join(l for l in _SERVER.splitlines() if not l.strip().startswith("#"))


# ── The contract ───────────────────────────────────────────────────────────

def test_route_takes_two_strings_and_returns_a_pair():
    params = list(inspect.signature(br.route).parameters)
    assert params[:2] == ["system_prompt", "user_input"]


def test_route_really_returns_a_tuple():
    """26 of 27 returns. A caller treating it as text gets a tuple."""
    tree = ast.parse(pathlib.Path(br.__file__).read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "route")
    rets = [r for r in ast.walk(fn) if isinstance(r, ast.Return) and r.value]
    tuples = [r for r in rets if isinstance(r.value, ast.Tuple)]
    assert len(tuples) > len(rets) * 0.8, (len(tuples), len(rets))


# ── No call site may pass the backend name as the prompt ──────────────────

def test_no_call_site_passes_active_backend_as_the_system_prompt():
    code = _code_only()
    assert "_rt(_ab()" not in code.replace(" ", ""), (
        "a call site still passes the backend name where the system prompt goes"
    )


def test_every_route_call_unpacks_the_pair():
    """
    A bare `x = _rt(...)` leaves a tuple in x. Each call must unpack, so the
    tuple cannot be handed on as if it were text.
    """
    bad = []
    for node in ast.walk(ast.parse(_SERVER)):
        if not isinstance(node, ast.Assign):
            continue
        v = node.value
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "_rt":
            if not isinstance(node.targets[0], ast.Tuple):
                bad.append(node.lineno)
    assert not bad, f"route() result not unpacked at line(s) {bad}"


# ── The dream closure honours its documented contract ─────────────────────

def test_the_dream_closure_returns_text_not_a_tuple():
    code = _code_only()
    start = code.index("def _dream_llm(")
    body = code[start:start + 700]
    assert "_rt(_d_sys, _d_usr)" in body, body[:200]
    assert "return _d_txt" in body


def test_the_dream_closure_pulls_both_roles_out_of_the_messages():
    code = _code_only()
    body = code[code.index("def _dream_llm("):][:700]
    assert '"system"' in body and '"user"' in body


def test_dream_faculty_still_documents_llm_fn_as_returning_a_string():
    """If this contract changes, the closure above must change with it."""
    src = pathlib.Path(
        pathlib.Path(__file__).resolve().parent.parent / "faculties" / "dream" / "dream_faculty.py"
    ).read_text(encoding="utf-8")
    assert "callable(messages: list[dict]) → str" in src or \
           "callable(messages: list[dict]) -> str" in src


# ── The failure was silent, which is why it lasted ────────────────────────

def test_the_dream_swallows_llm_failure_by_design():
    """
    Not a defect on its own — a dream must survive a dead backend. It is why a
    broken closure produced stub dreams for as long as it did instead of an
    error, so the closure is what has to be right.

    Checked on the parsed tree: an earlier version measured character distance
    from the call to the handler and failed on a long f-string in between,
    which is a proximity heuristic, not the property.
    """
    path = (pathlib.Path(__file__).resolve().parent.parent
            / "faculties" / "dream" / "dream_faculty.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    guarded = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        calls_llm = any(
            isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "llm_fn"
            for c in ast.walk(node)
        )
        broad = any(
            h.type is None or (isinstance(h.type, ast.Name) and h.type.id == "Exception")
            for h in node.handlers
        )
        if calls_llm and broad:
            guarded = True
            break
    assert guarded, "llm_fn is no longer wrapped — a dead backend would now break the dream"
