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


# ── Repo-wide: no module may call route with the backend name ─────────────

# Known and NOT fixed: runtime/executive.py's run_dream_window closure has the
# identical defect. Its own comment says it uses the real router so the dream
# produces "genuine narrative and insight, not an empty stub that degrades to
# the minimal fallback" — and the call guarantees that stub.
#
# executive.py is frozen at the TEST layer: test_d3_lesson_reaches_executive
# hashes it and the last SHA bump is annotated "David-authorized via Board".
# Editing it is a governance decision, not a plumbing one. Recorded here so it
# is visible and so a FOURTH copy cannot appear quietly.
KNOWN_UNFIXED = {"runtime/executive.py"}


def _route_aliases(tree: ast.AST) -> set[str]:
    """
    Names that `route` was imported under in this file.

    Matching on identifiers containing "route" is not enough — these are
    aliased imports (`route as _rt`, `route as _rt_b`), which is exactly the
    blind spot that let the executive.py copy through the first version of
    this test and made a wire-cut on it pass.
    """
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and "backend_router" in (node.module or ""):
            for a in node.names:
                if a.name == "route":
                    names.add(a.asname or a.name)
    return names


def _offenders() -> list[str]:
    root = pathlib.Path(__file__).resolve().parent.parent
    out = []
    for path in root.rglob("*.py"):
        sp = str(path)
        if "/tests/" in sp or "__pycache__" in sp or "/.git/" in sp:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        aliases = _route_aliases(tree)
        if not aliases:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Name) and fn.id in aliases):
                continue
            first = node.args[0]
            if isinstance(first, ast.Call):
                inner = first.func
                iname = inner.id if isinstance(inner, ast.Name) else getattr(inner, "attr", "")
                if "active_backend" in iname or iname.startswith("_ab"):
                    out.append(str(path.relative_to(root)))
    return out


def test_no_new_module_passes_the_backend_name_as_the_prompt():
    """
    A ratchet. server.py had two of these and runtime/executive.py has a
    third; the shape is copy-pasted between dream closures, so a fourth would
    fail exactly as silently as the first three did.
    """
    found = set(_offenders())
    assert found <= KNOWN_UNFIXED, f"new call site(s) passing the backend name: {sorted(found - KNOWN_UNFIXED)}"


def test_the_known_unfixed_one_is_still_really_broken():
    """
    The register must describe reality. If executive.py gets fixed or the
    closure moves, this fails and KNOWN_UNFIXED needs correcting — a stale
    exemption is how a defect becomes invisible again.
    """
    assert set(_offenders()) == KNOWN_UNFIXED, (
        f"KNOWN_UNFIXED is out of date: actually {sorted(_offenders())}"
    )
