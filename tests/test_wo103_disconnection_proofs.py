"""
tests/test_wo103_disconnection_proofs.py — WO-103: tests that bite when features disconnect.

AT-103-1: assemble-before-decide at runtime (instrument the live turn, not source text)
AT-103-2: orphan-faculty alarm — any faculty not reachable from live path FAILS this test
          NOTE: faculties.temporal is an orphan today. This test is INTENTIONALLY RED until
          WO-CANON-XXV removes temporal from faculties/. Leave it red — that's the proof.
AT-103-3: _PRESERVE_KEYS round-trip — every key survives a partial write through _write()
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --------------------------------------------------------------------------- #
# AT-103-1: assemble-before-decide on the LIVE turn path (not source text)    #
# --------------------------------------------------------------------------- #

def test_assemble_before_decide_runtime():
    """
    Ruling C invariant: assemble_cognitive_state() must be called BEFORE exec_decide().
    Previous AT-1 read spine.py with readlines() — it would pass even if server.py
    regressed. This test runs the real spine.run() and observes the call sequence.
    """
    import runtime.spine.spine as _spine_mod

    call_order = []
    _real_assemble = _spine_mod.assemble_cognitive_state

    def _recording_assemble(*args, **kwargs):
        call_order.append("assemble")
        try:
            return _real_assemble(*args, **kwargs)
        except Exception:
            return None

    def _mock_decide(attention_in, loop_detected=False, user_input=""):
        call_order.append("decide")
        return {
            "action": "answer", "cal_reason": "AT-103-1", "tone": "DIRECT",
            "max_sentences": 2, "response_goal": "answer",
            "valence": "neutral", "momentum": "stable", "mode": "", "register": "",
        }

    with patch.object(_spine_mod, "assemble_cognitive_state", _recording_assemble), \
         patch("runtime.executive.decide", _mock_decide):
        _spine_mod.run("hello", state={}, attention={})

    assert "assemble" in call_order, \
        "assemble_cognitive_state() was never called on the live spine.run() path"
    assert "decide" in call_order, \
        "exec_decide() was never called on the live spine.run() path"

    ai = call_order.index("assemble")
    di = call_order.index("decide")
    assert ai < di, (
        f"Ruling C violated on live path — assemble (position {ai}) came AFTER "
        f"decide (position {di}). Full order: {call_order}"
    )


# --------------------------------------------------------------------------- #
# AT-103-2: orphan-faculty alarm                                               #
# NOTE: INTENTIONALLY FAILS TODAY — faculties.temporal is an orphan.          #
# This test goes green only when WO-CANON-XXV removes temporal from faculties/ #
# --------------------------------------------------------------------------- #

def _faculty_names() -> set[str]:
    """Return all top-level faculty names from the faculties/ directory."""
    fac_dir = os.path.join(ROOT, "faculties")
    names = set()
    for entry in os.listdir(fac_dir):
        if entry.startswith("_") or entry == "__pycache__":
            continue
        if entry.endswith(".py"):
            names.add(entry[:-3])
        elif os.path.isdir(os.path.join(fac_dir, entry)):
            if os.path.exists(os.path.join(fac_dir, entry, "__init__.py")):
                names.add(entry)
    return names


def _live_path_src() -> str:
    """Return combined source of server.py + spine.py — the real live path."""
    srcs = []
    # ambient_engine added 2026-10-06. It is started by server.py:2286 and
    # ticks every 0.5s — eLo's heartbeat is as live as a turn is, and a
    # faculty consumed only from there was being reported as dead code.
    #
    # The two files below are still where a TURN runs. This widens what counts
    # as reachable; it does not relax the rule. imagination and knowledge
    # remain orphaned after the change, which is the check that it was widened
    # honestly.
    for rel in ("server.py", "runtime/spine/spine.py",
                "ambient/ambient_engine.py"):
        p = os.path.join(ROOT, rel)
        with open(p, encoding="utf-8") as f:
            srcs.append(f.read())
    return "\n".join(srcs)


def test_no_orphan_faculties():
    """
    Every faculty in faculties/ must be imported somewhere in the live path
    (server.py or spine.py). A faculty that isn't imported is dead code and
    any tests it has are false positives.

    CURRENTLY FAILS: faculties.temporal is orphaned. This test is correct in failing.
    It goes green when WO-CANON-XXV removes temporal/ from faculties/.
    """
    live_src = _live_path_src()
    all_faculties = _faculty_names()

    # Match only real import statements — not comments, strings, or table entries.
    # Pattern: line that starts (after whitespace) with "from faculties.<name>"
    # or "import faculties.<name>", on an import line not in a comment.
    _import_re = re.compile(
        r"^\s*(from|import)\s+faculties\.([\w.]+)",
        re.MULTILINE,
    )
    imported_names: set[str] = set()
    for m in _import_re.finditer(live_src):
        top = m.group(2).split(".")[0]
        imported_names.add(top)

    orphans = sorted(all_faculties - imported_names)

    assert not orphans, (
        f"Orphan faculties (registered + tested, never imported by live path): {orphans}\n"
        f"Each orphan's tests are green but the code is unreachable. "
        f"Remove the faculty or wire it into server.py/spine.py."
    )


# --------------------------------------------------------------------------- #
# AT-103-3: _PRESERVE_KEYS round-trip through _write()                        #
# --------------------------------------------------------------------------- #

def test_preserve_keys_survive_partial_write():
    """
    Every key in _PRESERVE_KEYS must survive a _write() call that omits them.
    This is the invariant the gaze bug violated: gaze was emitted, then a
    subsequent _write() without gaze in the payload silently dropped it.
    """
    import blender_bridge.state_writer as _sw

    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()

    real_path = _sw._STATE_PATH
    _sw._STATE_PATH = tmp.name
    try:
        # Step 1: write a state that has all PRESERVE_KEYS populated
        seed = {k: f"preserved_{k}" for k in _sw._PRESERVE_KEYS}
        seed["__other__"] = "ephemeral"
        _sw._write(seed)

        # Step 2: write again with a payload that omits all PRESERVE_KEYS
        _sw._write({"__fresh__": "new_turn"})

        # Step 3: read and assert every PRESERVE_KEY survived
        with open(tmp.name, encoding="utf-8") as f:
            result = json.load(f)

        missing = [k for k in _sw._PRESERVE_KEYS if k not in result]
        wrong = [
            k for k in _sw._PRESERVE_KEYS
            if k in result and result[k] != f"preserved_{k}"
        ]
        assert not missing, (
            f"Keys dropped by partial write — add them to _PRESERVE_KEYS or emit them "
            f"every turn: {missing}"
        )
        assert not wrong, (
            f"Keys present but wrong value after partial write: "
            f"{[(k, result[k]) for k in wrong]}"
        )

        # Step 4: non-preserved keys from step 1 must NOT carry over
        assert "__other__" not in result, \
            "__other__ should not survive a partial write (not in _PRESERVE_KEYS)"
    finally:
        _sw._STATE_PATH = real_path
        os.unlink(tmp.name)
