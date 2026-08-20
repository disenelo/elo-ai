"""
tests/test_canon_iv_ordering_invariants.py — WO-CANON-IV (Card 08)

Make the turn order a CONTRACT, not a comment.

The ordering guarantees Volumes XII, XV, VI and ADR-Exec-006 depend on
existed only as comments in spine.py — no canon, no test. Two invariants
were found VIOLATED (I-3, I-6) SILENTLY. This suite tests each invariant
listed in Volume_IV/02_Ordering_Guarantees_and_Invariants.md so that a
future reorder can't drift again unnoticed.

Trap avoided: source-order checks scoped to one module cannot detect a
cross-module ordering violation (that's what let I-3 hide). I-3 and I-4
below are asserted against BOTH server.py and runtime/spine/spine.py.

Each ordering test is proven sensitive to reordering by a matching
_swap_ self-test: it mutates a COPY of the source (swaps the two lines
under test) and re-runs the same check on the mutated copy, asserting
the check now FAILS. A test that would still pass under a swap is
worthless — it isn't testing the sequence, only the presence.

Invariants covered:
  I-1  perception before world-state       (Vol XII → XV)
  I-2  world-state before attention/WM     (Vol XV → VI) and both before first faculty
  I-3  assembly before decision            (ADR-Exec-006 / Ruling C — process-level)
  I-4  memory read before / write after    (Vol VII §2.1.4 / Vol XXVIII)
  I-5  ACK before belief                   (Ruling E — pending state → assembly → belief)
  I-6  expression after utterance          (build_embodiment_state after _conversation_faculty)

Run: python3 tests/test_canon_iv_ordering_invariants.py
"""
from __future__ import annotations
import ast
import os
import py_compile
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SPINE_PATH = os.path.join(_BASE, "runtime", "spine", "spine.py")
_SERVER_PATH = os.path.join(_BASE, "server.py")
_MOMENT_PATH = os.path.join(_BASE, "runtime", "the_moment.py")

_passed = _failed = 0


def ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err) -> None:
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — line-scanning primitives. Match on call sites, not line numbers.
# Volume IV §2.8: "Match on call sites, not line numbers. Line numbers drift;
# order does not."
# ─────────────────────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _line_of(src: str, marker: str, start_idx: int = 0) -> int | None:
    """First line index (0-based) at or after start_idx containing marker."""
    lines = src.splitlines()
    for i in range(start_idx, len(lines)):
        if marker in lines[i]:
            return i
    return None


def _all_lines(src: str, marker: str) -> list[int]:
    return [i for i, ln in enumerate(src.splitlines()) if marker in ln]


def _run_body_start(spine_src: str) -> int:
    """Line index of `def run(` in spine.py — the entrypoint whose body we scan."""
    idx = _line_of(spine_src, "def run(")
    if idx is None:
        raise AssertionError("spine.py: `def run(` not found")
    return idx


def _swap_two_lines(src: str, a_idx: int, b_idx: int) -> str:
    """Return a copy of src with lines a_idx and b_idx swapped."""
    lines = src.splitlines(keepends=True)
    lines[a_idx], lines[b_idx] = lines[b_idx], lines[a_idx]
    return "".join(lines)


def _assert_swap_fails(check_fn, src: str, a_idx: int, b_idx: int, label: str) -> None:
    """Mutate the source by swapping two lines and assert the checker now fails.

    A checker is a callable(src) -> None that raises AssertionError iff the
    ordering is wrong. If swapping the two lines under test doesn't make the
    checker fail, the test isn't actually testing sequence — it's testing
    presence, which is the trap I-8 exists to prevent.
    """
    mutated = _swap_two_lines(src, a_idx, b_idx)
    try:
        check_fn(mutated)
    except AssertionError:
        return  # good: mutation was detected
    raise AssertionError(
        f"{label}: swapping the two lines under test did NOT make the check fail. "
        f"The test is not sensitive to reordering — it is testing presence, not sequence."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Load sources once — every test reads from these
# ─────────────────────────────────────────────────────────────────────────────
try:
    _SPINE  = _read(_SPINE_PATH)
    _SERVER = _read(_SERVER_PATH)
    _MOMENT = _read(_MOMENT_PATH)
except Exception as e:
    print(f"  ❌ setup: could not read sources: {e}")
    sys.exit(1)


# =============================================================================
# I-1  PERCEPTION BEFORE WORLD STATE           (Vol IV §2.1)
# =============================================================================

# Effect-line markers — the LINE OF EFFECT, not the import. The import may be
# aliased (`from … import perceive_from_live_state as _perceive`); the effect
# is `_perception = _perceive()`. Ordering lives in effects, not imports.
_PERC_MARKER = "_perception = _perceive("
_WORLD_MARKER = "_world = _assemble_world("


def _check_I1a(spine_src: str) -> None:
    body_start = _run_body_start(spine_src)
    perc = _line_of(spine_src, _PERC_MARKER,  start_idx=body_start)
    worl = _line_of(spine_src, _WORLD_MARKER, start_idx=body_start)
    assert perc is not None, f"perception effect line ({_PERC_MARKER!r}) not found in spine.run()"
    assert worl is not None, f"world effect line ({_WORLD_MARKER!r}) not found in spine.run()"
    assert perc < worl, (
        f"I-1 VIOLATED: perception (L{perc+1}) does not precede world assembly "
        f"(L{worl+1}) — the world would have nothing sensed to copy."
    )


try:
    _check_I1a(_SPINE)
    ok("FT-IV-1a  I-1  _perception = _perceive() < _world = _assemble_world(...) in spine.run()")

    body_start = _run_body_start(_SPINE)
    perc_line = _line_of(_SPINE, _PERC_MARKER,  start_idx=body_start)
    worl_line = _line_of(_SPINE, _WORLD_MARKER, start_idx=body_start)
    _assert_swap_fails(_check_I1a, _SPINE, perc_line, worl_line, "FT-IV-1a")
    ok("FT-IV-1a·swap  swapping perception/world effect lines makes the check fail (test is sensitive)")
except AssertionError as e:
    fail("FT-IV-1a", e)


# I-1b — structural dependency: world reads perception via a passed argument,
# not by re-sensing. If someone "simplifies" by having the world sense for
# itself, this check catches it.
try:
    body_start = _run_body_start(_SPINE)
    lines = _SPINE.splitlines()
    worl_line = _line_of(_SPINE, _WORLD_MARKER, start_idx=body_start)
    assert worl_line is not None, "world assembly effect line not found"
    call_span = "\n".join(lines[worl_line:worl_line + 4])
    assert "perception=" in call_span, (
        "I-1 STRUCTURAL: world assembly is not invoked with perception=<value>. "
        "The world is re-sensing rather than reading — violates Vol XV §1.4 and §1.2.2."
    )
    ok("FT-IV-1b  I-1  world assembly called with perception= (structural dep, not positional)")
except AssertionError as e:
    fail("FT-IV-1b", e)


# =============================================================================
# I-2  WORLD → ATTENTION/WM → FIRST FACULTY    (Vol IV §2.2)
# =============================================================================

_ATTN_MARKER = "_attn_state = _wm_attn("
_LANG_MARKER = "language = _language_faculty("


def _check_I2a(spine_src: str) -> None:
    body_start = _run_body_start(spine_src)
    worl = _line_of(spine_src, _WORLD_MARKER, start_idx=body_start)
    attn = _line_of(spine_src, _ATTN_MARKER,  start_idx=body_start)
    lang = _line_of(spine_src, _LANG_MARKER,  start_idx=body_start)
    assert worl is not None, "world assembly effect not in spine.run()"
    assert attn is not None, "attention competition effect (_wm_attn) not in spine.run()"
    assert lang is not None, "first-faculty call (language = _language_faculty) not in spine.run()"
    assert worl < attn < lang, (
        f"I-2 VIOLATED: expected world (L{worl+1}) < WM/attention (L{attn+1}) < "
        f"first faculty (L{lang+1}). Got world={worl+1}, attn={attn+1}, lang={lang+1}."
    )


try:
    _check_I2a(_SPINE)
    ok("FT-IV-2a  I-2  world < attention/WM < first faculty (language) in spine.run()")

    body_start = _run_body_start(_SPINE)
    worl_line = _line_of(_SPINE, _WORLD_MARKER, start_idx=body_start)
    lang_line = _line_of(_SPINE, _LANG_MARKER,  start_idx=body_start)
    _assert_swap_fails(_check_I2a, _SPINE, worl_line, lang_line, "FT-IV-2a")
    ok("FT-IV-2a·swap  hoisting language above world makes the check fail")
except AssertionError as e:
    fail("FT-IV-2a", e)


# I-2c — exactly one attention competition per turn (Ruling B: supplier, not
# rival decider).
try:
    body_start = _run_body_start(_SPINE)
    attn_calls = [
        i for i, ln in enumerate(_SPINE.splitlines()[body_start:], start=body_start)
        if "_wm_attn(" in ln
    ]
    assert len(attn_calls) == 1, (
        f"I-2 VIOLATED (Ruling B): expected exactly 1 run_attention_competition call "
        f"in spine.run(), found {len(attn_calls)} at lines {[i+1 for i in attn_calls]}."
    )
    ok(f"FT-IV-2c  I-2  exactly one run_attention_competition() in spine.run() (Ruling B: one winner)")
except AssertionError as e:
    fail("FT-IV-2c", e)


# =============================================================================
# I-3  ASSEMBLY BEFORE DECISION                (Vol IV §2.3 · Ruling C · ADR-Exec-006)
# THE trap: a source-order check scoped to spine.py alone is TRUE while the
# invariant is VIOLATED. We assert across BOTH files.
# =============================================================================

# I-3a — inside spine.run(), assemble_cognitive_state precedes the invocation
# of _executive_faculty (which is where the decision is taken). Note that the
# decide *call* itself lives inside `_executive_faculty` (defined above run()
# in the file), so a naïve full-file line comparison would give the WRONG
# answer — precisely the trap Vol IV §2.3 called out. We check run-flow order.
_ASM_MARKER = "_cognitive_state = assemble_cognitive_state("
_EXEC_CALL_MARKER = "plan = _executive_faculty("


def _check_I3a(spine_src: str) -> None:
    body_start = _run_body_start(spine_src)
    asm  = _line_of(spine_src, _ASM_MARKER,       start_idx=body_start)
    exec_call = _line_of(spine_src, _EXEC_CALL_MARKER, start_idx=body_start)
    assert asm is not None,       "_cognitive_state = assemble_cognitive_state( not in spine.run()"
    assert exec_call is not None, "plan = _executive_faculty( not in spine.run()"
    assert asm < exec_call, (
        f"I-3 VIOLATED (run-flow): assemble_cognitive_state (L{asm+1}) does not precede "
        f"_executive_faculty invocation (L{exec_call+1}) — the Executive would decide "
        f"without the assembled state on its input. This is the Ruling C flow-order clause."
    )


try:
    _check_I3a(_SPINE)
    ok("FT-IV-3a  I-3  assemble_cognitive_state( < _executive_faculty( in spine.run()")

    body_start = _run_body_start(_SPINE)
    asm_line = _line_of(_SPINE, _ASM_MARKER, start_idx=body_start)
    exec_line = _line_of(_SPINE, _EXEC_CALL_MARKER, start_idx=body_start)
    _assert_swap_fails(_check_I3a, _SPINE, asm_line, exec_line, "FT-IV-3a")
    ok("FT-IV-3a·swap  swapping assemble and _executive_faculty call makes the check fail")
except AssertionError as e:
    fail("FT-IV-3a", e)


# I-3a·nested — assembly is NOT re-done inside the Executive. If it were, the
# decision would be the assembler, and Ruling C would be violated even though
# the run-flow check passed. This closes the "false positive" gap.
def _fn_body_calls(module_src: str, fn_name: str) -> set[str]:
    """Return the set of qualified function names called inside `fn_name`.

    Uses ast to walk the FunctionDef body (skipping signature and docstring).
    Comments never enter the ast, so a mention of `assemble_cognitive_state()`
    in a signature comment cannot pollute the result.
    """
    tree = ast.parse(module_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            calls: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    fn = sub.func
                    if isinstance(fn, ast.Name):
                        calls.add(fn.id)
                    elif isinstance(fn, ast.Attribute):
                        calls.add(fn.attr)
            return calls
    raise AssertionError(f"def {fn_name}(...) not found in module")


try:
    ef_calls = _fn_body_calls(_SPINE, "_executive_faculty")
    assert "assemble_cognitive_state" not in ef_calls, (
        "I-3 VIOLATED: _executive_faculty() invokes assemble_cognitive_state() — the decider "
        "is doing the assembling, exactly the shape of the original violation."
    )
    ok("FT-IV-3a·nested  _executive_faculty does NOT call assemble_cognitive_state (assembly not re-done at decision time)")
except AssertionError as e:
    fail("FT-IV-3a·nested", e)


# I-3b — server.py has no top-of-turn exec_decide call ahead of spine.run().
# This is the cross-module clause that closes the trap.
try:
    srv_lines = _SERVER.splitlines()
    exec_calls = [
        (i, ln) for i, ln in enumerate(srv_lines)
        if "exec_decide(" in ln and "import" not in ln and "= exec_decide" in ln
    ]
    # The Ruling C closure permits at most ONE remaining exec_decide( call: the
    # fallback in the `else:` branch when _plan is None. That call MUST come
    # AFTER the _spine_run( call site.
    spine_run_line = _line_of(_SERVER, "= _spine_run(")
    if spine_run_line is None:
        spine_run_line = _line_of(_SERVER, "_spine_run(")
    assert spine_run_line is not None, "server.py does not call _spine_run( — the turn is bypassing the spine"
    assert len(exec_calls) <= 1, (
        f"I-3 VIOLATED (cross-module): server.py contains {len(exec_calls)} "
        f"exec_decide calls at lines {[i+1 for i,_ in exec_calls]} — Ruling C permits "
        f"at most one (fallback else-branch)."
    )
    if exec_calls:
        i, ln = exec_calls[0]
        assert i > spine_run_line, (
            f"I-3 VIOLATED (cross-module): server.py:{i+1} calls exec_decide BEFORE "
            f"_spine_run at L{spine_run_line+1}. Decision precedes assembly across the process — "
            f"exactly the shape of the original violation."
        )
    ok(f"FT-IV-3b  I-3  server.py has ≤1 exec_decide call, and it follows _spine_run (Ruling C closed)")
except AssertionError as e:
    fail("FT-IV-3b", e)


# I-3c — no _exec_decision transport through the attention channel. This is the
# tell David called out: a decision riding inside an attention dict has no
# legitimate seat in the turn order.
try:
    assert "_exec_decision" not in _SPINE, (
        "I-3 VIOLATED: spine.py still references \"_exec_decision\" — the pre-assembly "
        "transport channel that let the decision arrive on the attention dict."
    )
    # server.py: the string may legitimately appear in comments explaining
    # WHY it was retired. What must NOT appear is an assignment that injects
    # _exec_decision into an attention dict.
    forbidden = re.search(
        r'attention\w*\["_exec_decision"\]\s*=|_attention_with_exec\["_exec_decision"\]\s*=',
        _SERVER,
    )
    assert forbidden is None, (
        f"I-3 VIOLATED: server.py still injects a decision into the attention channel: "
        f"{forbidden.group(0)!r}. Ruling C forbids this transport."
    )
    ok("FT-IV-3c  I-3  no _exec_decision transport in spine.py or server.py (attention channel clean)")
except AssertionError as e:
    fail("FT-IV-3c", e)


# I-3d — exactly one decider in the spine. Invariant #2: no committee.
try:
    dec_calls = [
        i for i, ln in enumerate(_SPINE.splitlines())
        if "_exec_decide_fn(" in ln and "import" not in ln
    ]
    assert len(dec_calls) == 1, (
        f"I-3 VIOLATED (Invariant #2): expected exactly 1 exec_decide call site in "
        f"spine.py, found {len(dec_calls)} at lines {[i+1 for i in dec_calls]}."
    )
    ef_calls = [
        i for i, ln in enumerate(_SPINE.splitlines())
        if "_executive_faculty(" in ln
        and "def _executive_faculty" not in ln
        and "import" not in ln
    ]
    # Expect exactly one call to _executive_faculty from spine.run().
    assert len(ef_calls) == 1, (
        f"I-3 VIOLATED: expected exactly 1 _executive_faculty( call in spine.run(), "
        f"found {len(ef_calls)} at lines {[i+1 for i in ef_calls]}."
    )
    ok("FT-IV-3d  I-3  exactly one decider — 1 exec_decide call, 1 _executive_faculty call in spine.py")
except AssertionError as e:
    fail("FT-IV-3d", e)


# =============================================================================
# I-4  MEMORY READ BEFORE, MEMORY WRITE AFTER   (Vol IV §2.4)
# =============================================================================

# I-4a — the spine performs no memory read of its own; memory arrives via
# the memory_pack parameter.
try:
    body_start = _run_body_start(_SPINE)
    # The run() body extends to EOF (module functions after `def run(` follow it).
    # To scope the "no memory import" check to run() only, we bound it at the
    # next top-level `def ` after run(.
    lines = _SPINE.splitlines()
    body_end = len(lines)
    for i in range(body_start + 1, len(lines)):
        # Top-level def (no leading whitespace) closes run's body.
        if re.match(r"^def [A-Za-z_]", lines[i]):
            body_end = i
            break
    run_body = "\n".join(lines[body_start:body_end])

    # A memory-module read inside run() would look like an import of anything
    # under `memory.` or from a memory-store module. Legitimate: memory_pack
    # is a parameter, not a read.
    banned = re.search(r"^\s*from\s+memory[\.\s]|^\s*import\s+memory[\.\s]", run_body, re.MULTILINE)
    assert banned is None, (
        f"I-4 VIOLATED: spine.run() imports a memory module inline: {banned.group(0)!r}. "
        f"Memory must arrive via the memory_pack parameter — no mid-turn memory reads."
    )
    # Also the run signature must expose memory_pack as a parameter.
    sig_line = lines[body_start]
    # Signature can span lines: check the run() header block for the param name.
    sig_span = "\n".join(lines[body_start:body_start + 8])
    assert "memory_pack" in sig_span, (
        "I-4 VIOLATED: spine.run() signature does not declare memory_pack — memory "
        "would have to be sourced from somewhere else inside the spine."
    )
    ok("FT-IV-4a  I-4  spine.run() has NO memory imports and accepts memory_pack= as a parameter")
except AssertionError as e:
    fail("FT-IV-4a", e)


# I-4b — memory write happens AFTER the response exists. Cross-module: check
# server.py's call to _spine_update() sits after the _spine_run() line.
try:
    write_line = _line_of(_SERVER, "_spine_update(raw, response)")
    spine_run_line = _line_of(_SERVER, "= _spine_run(")
    if spine_run_line is None:
        spine_run_line = _line_of(_SERVER, "_spine_run(")
    assert write_line is not None, (
        "I-4 VIOLATED: server.py contains no `_spine_update(raw, response)` call — "
        "the memory writer for the turn is missing."
    )
    assert spine_run_line is not None, "server.py does not call _spine_run("
    assert write_line > spine_run_line, (
        f"I-4 VIOLATED: _spine_update at L{write_line+1} does not follow _spine_run at "
        f"L{spine_run_line+1} — a mid-turn write becomes a mid-turn learn (ADR-Exec-005)."
    )
    ok(f"FT-IV-4b  I-4  server.py writes memory (_spine_update L{write_line+1}) AFTER _spine_run L{spine_run_line+1}")

    # Sensitivity proof: swap the two lines and re-check.
    def _check_I4b(src: str) -> None:
        wl = _line_of(src, "_spine_update(raw, response)")
        sl = _line_of(src, "= _spine_run(") or _line_of(src, "_spine_run(")
        assert wl is not None and sl is not None and wl > sl, "I-4 order broken"

    _assert_swap_fails(_check_I4b, _SERVER, spine_run_line, write_line, "FT-IV-4b")
    ok("FT-IV-4b·swap  swapping _spine_run and _spine_update makes the check fail")
except AssertionError as e:
    fail("FT-IV-4b", e)


# =============================================================================
# I-5  ACK BEFORE BELIEF                        (Vol IV §2.5 · Ruling E)
# The invariant has two sub-rules. I-5a: pending state enters the assembly
# (not a side door). I-5b: belief is written from the ACK, not the command.
# =============================================================================

# I-5a — pending_sit is threaded from server.py into spine.run() and consumed
# by build_snapshot (i.e. it enters through the ASSEMBLY channel, not by a
# late injection into the frozen state).
try:
    body_start = _run_body_start(_SPINE)
    lines = _SPINE.splitlines()
    sig_span = "\n".join(lines[body_start:body_start + 8])
    assert "pending_sit" in sig_span, (
        "I-5 VIOLATED: spine.run() signature no longer accepts pending_sit — the body's "
        "pending state has no legitimate way into the assembly."
    )
    snap_line = _line_of(_SPINE, "_build_snap(", start_idx=body_start)
    assert snap_line is not None, "build_snapshot ( _build_snap( ) not called in spine.run()"
    call_span = "\n".join(lines[snap_line:snap_line + 3])
    assert "pending_sit=pending_sit" in call_span, (
        "I-5 VIOLATED: build_snapshot is called without pending_sit=pending_sit — the "
        "pending body state is dropped before the frozen snapshot is built."
    )
    ok("FT-IV-5a  I-5  pending_sit threaded into run() signature and into build_snapshot (assembly channel)")
except AssertionError as e:
    fail("FT-IV-5a", e)


# I-5b — belief is written from the ACK. the_moment.py promotes pose_tier to
# "observed"/"verified" iff pose_acked is true; otherwise "last-known". A
# commanded state that is not ACKed is pending, never true.
try:
    m = re.search(r'"pose_tier"\s*:\s*"observed"\s+if\s+pose_acked\s+else\s+"last-known"', _MOMENT)
    assert m is not None, (
        "I-5 VIOLATED: runtime/the_moment.py no longer promotes pose_tier from pose_acked — "
        "belief could now be written at command time (Vol XI §1.1.3 breach)."
    )
    ok("FT-IV-5b  I-5  runtime/the_moment.py: pose_tier is 'observed' iff pose_acked else 'last-known'")
except AssertionError as e:
    fail("FT-IV-5b", e)


# =============================================================================
# I-6  EXPRESSION AFTER UTTERANCE               (Vol IV §2.6)
# _conversation_faculty( sets plan.direct_response; build_embodiment_state
# copies it into response_text / display_text / tts_text. If the order is
# reversed, every direct-response turn publishes an empty utterance.
# =============================================================================

def _check_I6a(spine_src: str) -> None:
    body_start = _run_body_start(spine_src)
    # The call site — not the `def _conversation_faculty` header earlier in the file.
    conv = _line_of(spine_src, "plan = _conversation_faculty(plan)", start_idx=body_start)
    # build_embodiment_state( on the RHS of an assignment in the run body.
    emb  = _line_of(spine_src, "plan.embodiment_state = build_embodiment_state(", start_idx=body_start)
    assert conv is not None, "plan = _conversation_faculty(plan) not found in spine.run()"
    assert emb  is not None, "plan.embodiment_state = build_embodiment_state( not found in spine.run()"
    assert conv < emb, (
        f"I-6 VIOLATED: _conversation_faculty (L{conv+1}) does not precede "
        f"build_embodiment_state (L{emb+1}). Every direct-response turn publishes an empty utterance."
    )


try:
    _check_I6a(_SPINE)
    ok("FT-IV-6a  I-6  _conversation_faculty( < build_embodiment_state( in spine.run()")

    body_start = _run_body_start(_SPINE)
    conv_line = _line_of(_SPINE, "plan = _conversation_faculty(plan)", start_idx=body_start)
    emb_line  = _line_of(_SPINE, "plan.embodiment_state = build_embodiment_state(", start_idx=body_start)
    _assert_swap_fails(_check_I6a, _SPINE, conv_line, emb_line, "FT-IV-6a")
    ok("FT-IV-6a·swap  swapping _conversation_faculty and build_embodiment_state makes the check fail")
except AssertionError as e:
    fail("FT-IV-6a", e)


# I-6b — build_embodiment_state carries the utterance into the published
# EmbodimentState. If it doesn't, "expression after utterance" is decorative:
# the order is right but no utterance survives.
try:
    m = re.search(
        r"def build_embodiment_state\([^)]*\)[^:]*:(?P<body>.*?)(?=\n\ndef |\Z)",
        _SPINE, re.DOTALL,
    )
    assert m is not None, "def build_embodiment_state( block not located"
    body = m.group("body")
    assert "getattr(plan, \"direct_response\"" in body or "plan.direct_response" in body, (
        "I-6 VIOLATED: build_embodiment_state does not read plan.direct_response — the "
        "utterance produced by _conversation_faculty is not carried into EmbodimentState."
    )
    assert "response_text=" in body and "tts_text=" in body and "display_text=" in body, (
        "I-6 VIOLATED: EmbodimentState is not constructed with response_text/display_text/tts_text "
        "populated from the plan's direct_response — subscribers (Voice, Unity, Island) will read empty."
    )
    # The three text fields must all bind to the resp variable derived from
    # plan.direct_response (not empty strings or other sources).
    assert re.search(r"resp\s*=\s*getattr\(plan,\s*\"direct_response\"", body) or \
           re.search(r"resp\s*=\s*plan\.direct_response", body), (
        "I-6 VIOLATED: EmbodimentState.response_text is not derived from plan.direct_response."
    )
    ok("FT-IV-6b  I-6  build_embodiment_state carries direct_response into response_text/display_text/tts_text")
except AssertionError as e:
    fail("FT-IV-6b", e)


# =============================================================================
# Compile check — spine.py and server.py must be syntactically clean.
# =============================================================================
try:
    py_compile.compile(_SPINE_PATH,  doraise=True)
    py_compile.compile(_SERVER_PATH, doraise=True)
    py_compile.compile(_MOMENT_PATH, doraise=True)
    ok("py_compile clean on spine.py, server.py, the_moment.py")
except py_compile.PyCompileError as e:
    fail("py_compile", e)
except Exception as e:
    fail("py_compile", e)


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 74)
print(f"Vol IV ordering invariants (WO-CANON-IV)    {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
